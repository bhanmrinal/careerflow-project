"""
Conversation Router.

Intelligently routes user messages to the appropriate specialized agent
using LLM-based intent classification for robust, flexible routing.
"""

import json
from typing import Any

from app.agents.base import AgentResult, BaseAgent
from app.agents.company_research import CompanyResearchAgent
from app.agents.job_matching import JobMatchingAgent
from app.agents.translation import TranslationAgent
from app.core.llm import get_llm
from app.models.conversation import AgentType, Conversation
from app.models.resume import Resume


class ConversationRouter:
    """
    Routes conversations to appropriate specialized agents using LLM-based classification.

    Uses intelligent LLM routing instead of brittle regex patterns to:
    - Handle natural language variations and edge cases
    - Understand context and nuance in user requests
    - Extract relevant parameters (company names, languages, etc.)
    - Adapt to any company, language, or job description format
    """

    ROUTING_SYSTEM_PROMPT = """You are an intelligent router for a resume optimization system. Your job is to analyze user messages and determine which specialized agent should handle the request.

## Available Agents

1. **JOB_MATCHING** - Use when the user:
   - Provides or references a job description, job posting, or JD
   - Asks to match/compare their resume against a specific role
   - Wants to know how well they fit a position
   - Asks about skill gaps for a specific job
   - Mentions ATS optimization for a job posting
   - Pastes text that looks like a job listing (has requirements, responsibilities, qualifications)

2. **COMPANY_RESEARCH** - Use when the user:
   - Wants to optimize their resume for a specific company (by name)
   - Asks about tailoring resume to company culture/values
   - Mentions applying to or targeting a specific organization
   - Wants company-specific optimization WITHOUT a job description
   - Examples: "optimize for Google", "tailor for Amazon", "I'm applying to Stripe"

3. **TRANSLATION** - Use when the user:
   - Wants to translate their resume to another language
   - Mentions a specific country/region's job market
   - Asks about localization or adapting for international markets
   - Mentions any language or country name in context of translation/adaptation

4. **GENERAL** - Use when:
   - The request doesn't clearly fit the above categories
   - The user is asking a general question about the system
   - The intent is ambiguous and needs clarification

## Decision Rules
- If user provides BOTH a company name AND a job description, choose JOB_MATCHING (the JD is more specific)
- If user mentions translation/language AND a company, choose TRANSLATION (translation is the primary ask)
- When in doubt between agents, prefer the more specific one (JOB_MATCHING > COMPANY_RESEARCH > GENERAL)

## Response Format
Respond with ONLY a valid JSON object (no markdown, no explanation):
{
    "agent": "JOB_MATCHING" | "COMPANY_RESEARCH" | "TRANSLATION" | "GENERAL",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "extracted_params": {
        "company_name": "string or null",
        "target_language": "string or null", 
        "target_region": "string or null",
        "has_job_description": true/false
    }
}"""

    def __init__(self):
        self._llm = None
        self._routing_llm = None
        self._agents: dict[AgentType, BaseAgent] = {}

    @property
    def llm(self):
        """Lazy initialization of LLM for agent processing."""
        if self._llm is None:
            self._llm = get_llm(temperature=0.7)
        return self._llm

    @property
    def routing_llm(self):
        """Lazy initialization of LLM for routing (low temperature for consistency)."""
        if self._routing_llm is None:
            self._routing_llm = get_llm(temperature=0.1)
        return self._routing_llm

    def _get_agent(self, agent_type: AgentType) -> BaseAgent:
        """Get or create an agent instance."""
        if agent_type not in self._agents:
            agent_map = {
                AgentType.COMPANY_RESEARCH: CompanyResearchAgent,
                AgentType.JOB_MATCHING: JobMatchingAgent,
                AgentType.TRANSLATION: TranslationAgent,
            }
            agent_class = agent_map.get(agent_type)
            if agent_class:
                self._agents[agent_type] = agent_class()
        return self._agents.get(agent_type)

    async def route(
        self,
        user_message: str,
        resume: Resume | None,
        conversation: Conversation,
        context: dict[str, Any],
    ) -> AgentResult:
        """
        Route a user message to the appropriate agent.

        Args:
            user_message: The user's message.
            resume: The current resume (if any).
            conversation: The conversation context.
            context: Additional context.

        Returns:
            AgentResult from the selected agent.
        """
        if not resume:
            return AgentResult(
                success=False,
                message="Please upload a resume first before I can help you optimize it. You can upload a PDF or DOCX file.",
                reasoning="No resume uploaded",
                metadata={"agent_type": AgentType.ROUTER.value},
            )

        agent_type, extracted_params = await self._classify_intent(
            user_message, conversation, context
        )

        # Merge extracted params with existing context
        updated_context = {**context, **extracted_params}

        # Handle general/unclear queries
        if agent_type is None:
            return await self._handle_general_query(user_message, resume, conversation)

        agent = self._get_agent(agent_type)
        if not agent:
            return await self._handle_general_query(user_message, resume, conversation)

        try:
            result = await agent.process(
                user_message=user_message,
                resume=resume,
                conversation=conversation,
                context=updated_context,
            )
            # Inject agent_type into result metadata for tracking
            result.metadata["agent_type"] = agent_type.value
            return result
        except Exception as e:
            return AgentResult(
                success=False,
                message=f"I encountered an error while processing your request: {str(e)}. Please try again or rephrase your request.",
                reasoning=f"Agent error: {str(e)}",
                metadata={"agent_type": agent_type.value},
            )

    async def _classify_intent(
        self, user_message: str, conversation: Conversation, context: dict[str, Any]
    ) -> tuple[AgentType, dict[str, Any]]:
        """
        Classify the user's intent using LLM-based routing.

        Uses an LLM to understand the user's intent naturally, handling:
        - Any company name (not just hardcoded ones)
        - Any language or region
        - Various ways of expressing the same intent
        - Context from conversation history

        Args:
            user_message: The user's message.
            conversation: Conversation context.
            context: Additional context.

        Returns:
            Tuple of (AgentType, extracted_params dict).
        """
        recent_messages = conversation.get_history(limit=3)
        history_context = ""
        if recent_messages:
            history_context = "Recent conversation:\n" + "\n".join(
                f"- {msg.role.value}: {msg.content[:150]}..." for msg in recent_messages
            )

        # Truncate very long messages (like job descriptions) for routing
        message_preview = (
            user_message[:1500] + "..." if len(user_message) > 1500 else user_message
        )

        routing_prompt = f"""{self.ROUTING_SYSTEM_PROMPT}

{history_context}

Current user message:
\"\"\"
{message_preview}
\"\"\"

Analyze this message and respond with the JSON classification."""

        try:
            response = await self.routing_llm.ainvoke(routing_prompt)
            result = self._parse_routing_response(response.content)
            return result
        except Exception as e:
            # Fallback: if LLM routing fails, default to company research
            return AgentType.COMPANY_RESEARCH, {"error": str(e)}

    def _parse_routing_response(
        self, response_text: str
    ) -> tuple[AgentType, dict[str, Any]]:
        """Parse the LLM routing response and extract agent type and parameters."""
        # Clean up the response - remove markdown code blocks if present
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            # Remove markdown code block
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re

            json_match = re.search(r"\{[^{}]*\}", response_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    return AgentType.COMPANY_RESEARCH, {"parse_error": True}
            else:
                return AgentType.COMPANY_RESEARCH, {"parse_error": True}

        # Map agent string to AgentType
        agent_mapping = {
            "JOB_MATCHING": AgentType.JOB_MATCHING,
            "COMPANY_RESEARCH": AgentType.COMPANY_RESEARCH,
            "TRANSLATION": AgentType.TRANSLATION,
            "GENERAL": None,  # Will trigger general handler
        }

        agent_str = data.get("agent", "GENERAL").upper()
        agent_type = agent_mapping.get(agent_str)

        # Extract parameters
        extracted_params = data.get("extracted_params", {})
        extracted_params["confidence"] = data.get("confidence", 0.5)
        extracted_params["reasoning"] = data.get("reasoning", "")

        return agent_type, extracted_params

    async def _handle_general_query(
        self, user_message: str, resume: Resume, conversation: Conversation
    ) -> AgentResult:
        """Handle general queries that don't fit specific agents."""
        prompt = f"""You are a helpful career assistant. The user has uploaded their resume and is asking:

"{user_message}"

Available capabilities:
1. **Company Research & Optimization**: I can research specific companies and optimize your resume to match their culture and values. Example: "Optimize my resume for Google"

2. **Job Description Matching**: I can analyze job descriptions, calculate match scores, identify skill gaps, and optimize your resume for specific positions. Example: "Match my resume to this job description: [paste JD]"

3. **Translation & Localization**: I can translate your resume to different languages and adapt it for specific regional markets. Example: "Translate my resume to Spanish for the Mexican market"

Please help the user understand how to use these features or clarify their request."""

        response = await self.llm.ainvoke(prompt)

        return AgentResult(
            success=True,
            message=response.content,
            reasoning="General query - provided guidance on available features",
            metadata={"agent_type": AgentType.ROUTER.value},
        )

    def get_available_agents(self) -> list[dict[str, str]]:
        """Get information about available agents."""
        return [
            {
                "type": AgentType.COMPANY_RESEARCH.value,
                "name": "Company Research & Optimization",
                "description": "Research companies and optimize your resume to match their culture and values",
                "example": "Optimize my resume for Google",
            },
            {
                "type": AgentType.JOB_MATCHING.value,
                "name": "Job Description Matching",
                "description": "Analyze job descriptions, calculate match scores, and identify skill gaps",
                "example": "Match my resume to this job description: [paste JD]",
            },
            {
                "type": AgentType.TRANSLATION.value,
                "name": "Translation & Localization",
                "description": "Translate and localize your resume for different markets",
                "example": "Translate my resume to Spanish for Mexico",
            },
        ]
