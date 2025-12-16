/**
 * Careerflow Resume Optimizer - Frontend Application
 * Enhanced with model selection, evaluation, and results panels
 */

const API_BASE = '/api';

// State
const state = {
    conversationId: null,
    resumeId: null,
    resumeData: null,
    isProcessing: false,
    currentVersion: 1,
    versions: [],
    selectedModel: 'llama-3.3-70b-versatile',
    settings: {
        temperature: 0.7,
        maxTokens: 2048,
        exportFormat: 'pdf',
        showReasoning: true,
        autoExpand: true
    },
    evaluation: {
        overall: 0,
        keywords: 0,
        format: 0,
        impact: 0
    }
};

// DOM Elements
const elements = {
    // Chat
    chatContainer: document.getElementById('chat-container'),
    messages: document.getElementById('messages'),
    messageInput: document.getElementById('message-input'),
    sendBtn: document.getElementById('send-btn'),
    welcomeMessage: document.getElementById('welcome-message'),
    clearChat: document.getElementById('clear-chat'),
    charCount: document.getElementById('char-count'),
    
    // Resume
    resumeUpload: document.getElementById('resume-upload'),
    resumeStatus: document.getElementById('resume-status'),
    attachBtn: document.getElementById('attach-btn'),
    
    // Model
    modelSelect: document.getElementById('model-select'),
    modelStatus: document.getElementById('model-status'),
    currentModel: document.getElementById('current-model'),
    connectionStatus: document.getElementById('connection-status'),
    
    // Panels
    resultsPanel: document.getElementById('results-panel'),
    closePanel: document.getElementById('close-panel'),
    panelTabs: document.querySelectorAll('.panel-tab'),
    
    // Tabs content
    previewTab: document.getElementById('preview-tab'),
    changesTab: document.getElementById('changes-tab'),
    analysisTab: document.getElementById('analysis-tab'),
    previewEmpty: document.getElementById('preview-empty'),
    changesEmpty: document.getElementById('changes-empty'),
    analysisEmpty: document.getElementById('analysis-empty'),
    resumePreview: document.getElementById('resume-preview'),
    changesList: document.getElementById('changes-list'),
    analysisContent: document.getElementById('analysis-content'),
    
    // Score
    scoreSection: document.getElementById('score-section'),
    scoreCircle: document.getElementById('score-circle'),
    scoreValue: document.getElementById('score-value'),
    scoreBreakdown: document.getElementById('score-breakdown'),
    
    // Versions
    versionsSection: document.getElementById('versions-section'),
    versionsList: document.getElementById('versions-list'),
    
    // Modals
    settingsModal: document.getElementById('settings-modal'),
    settingsBtn: document.getElementById('settings-btn'),
    closeSettings: document.getElementById('close-settings'),
    evalModal: document.getElementById('eval-modal'),
    evalBtn: document.getElementById('eval-btn'),
    closeEval: document.getElementById('close-eval'),
    
    // Settings controls
    temperatureSlider: document.getElementById('temperature'),
    tempValue: document.getElementById('temp-value'),
    maxTokensSlider: document.getElementById('max-tokens'),
    tokensValue: document.getElementById('tokens-value'),
    exportFormat: document.getElementById('export-format'),
    showReasoning: document.getElementById('show-reasoning'),
    autoExpand: document.getElementById('auto-expand'),
    saveSettings: document.getElementById('save-settings'),
    resetSettings: document.getElementById('reset-settings'),
    
    // Actions
    exportBtn: document.getElementById('export-btn'),
    menuToggle: document.getElementById('menu-toggle'),
    sidebar: document.querySelector('.sidebar'),
    
    // Loading
    loadingOverlay: document.getElementById('loading-overlay'),
    
    // Example prompts
    examplePrompts: document.querySelectorAll('.example-prompt'),
    agentItems: document.querySelectorAll('.agent-item')
};

// Initialize
document.addEventListener('DOMContentLoaded', init);

function init() {
    setupEventListeners();
    loadSettings();
    checkHealth();
    updateCharCount();
}

function setupEventListeners() {
    // Message input
    elements.messageInput.addEventListener('input', handleInputChange);
    elements.messageInput.addEventListener('keydown', handleKeyDown);
    elements.sendBtn.addEventListener('click', sendMessage);

    // File upload
    elements.resumeUpload.addEventListener('change', handleFileUpload);
    elements.attachBtn?.addEventListener('click', () => elements.resumeUpload.click());

    // Model selection
    elements.modelSelect.addEventListener('change', handleModelChange);

    // Example prompts
    elements.examplePrompts.forEach(btn => {
        btn.addEventListener('click', () => {
            const prompt = btn.dataset.prompt;
            elements.messageInput.value = prompt;
            handleInputChange();
            elements.messageInput.focus();
        });
    });

    // Agent items
    elements.agentItems.forEach(item => {
        item.addEventListener('click', () => {
            const agent = item.dataset.agent;
            highlightAgent(agent);
        });
    });

    // Panel tabs
    elements.panelTabs.forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // Close panel
    elements.closePanel?.addEventListener('click', () => {
        elements.resultsPanel.classList.add('collapsed');
    });

    // Clear chat
    elements.clearChat.addEventListener('click', clearChat);

    // Settings modal
    elements.settingsBtn?.addEventListener('click', () => openModal('settings-modal'));
    elements.closeSettings?.addEventListener('click', () => closeModal('settings-modal'));
    
    // Eval modal
    elements.evalBtn?.addEventListener('click', () => openModal('eval-modal'));
    elements.closeEval?.addEventListener('click', () => closeModal('eval-modal'));

    // Settings controls
    elements.temperatureSlider?.addEventListener('input', (e) => {
        const value = (e.target.value / 100).toFixed(1);
        elements.tempValue.textContent = value;
    });
    
    elements.maxTokensSlider?.addEventListener('input', (e) => {
        elements.tokensValue.textContent = e.target.value;
    });
    
    elements.saveSettings?.addEventListener('click', saveSettings);
    elements.resetSettings?.addEventListener('click', resetSettings);

    // Export
    elements.exportBtn?.addEventListener('click', handleExport);

    // Mobile menu toggle
    elements.menuToggle?.addEventListener('click', () => {
        elements.sidebar.classList.toggle('open');
    });

    // Close modals on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.classList.remove('active');
            }
        });
    });

    // Auto-resize textarea
    elements.messageInput.addEventListener('input', autoResize);
}

// ========================================
// API Functions
// ========================================

async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        updateConnectionStatus(true, data.model);
        
        // Update model select to match server
        if (data.model && elements.modelSelect) {
            const option = Array.from(elements.modelSelect.options).find(opt => 
                opt.value === data.model || opt.text.toLowerCase().includes(data.model.toLowerCase())
            );
            if (option) {
                elements.modelSelect.value = option.value;
            }
        }
    } catch (error) {
        updateConnectionStatus(false);
        console.error('Health check failed:', error);
    }
}

async function uploadResume(file) {
    showLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/resume/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        const data = await response.json();
        state.resumeId = data.resume_id;
        state.resumeData = data;

        updateResumeStatus(data);
        await loadResumeContent(data.resume_id);
        await loadVersions(data.resume_id);

        // Show results panel
        if (state.settings.autoExpand) {
            elements.resultsPanel.classList.remove('collapsed');
            switchTab('preview');
        }

        addSystemMessage(`✅ Resume uploaded successfully! Found ${data.sections_detected.length} sections: ${data.sections_detected.join(', ')}`);

    } catch (error) {
        addSystemMessage(`❌ Error uploading resume: ${error.message}`);
        console.error('Upload error:', error);
    } finally {
        showLoading(false);
    }
}

async function sendChatMessage(message) {
    if (state.isProcessing) return;

    state.isProcessing = true;
    elements.sendBtn.disabled = true;

    // Hide welcome message
    elements.welcomeMessage.classList.add('hidden');

    // Add user message
    addMessage('user', message);

    // Show typing indicator
    const typingId = showTypingIndicator();

    try {
        const response = await fetch(`${API_BASE}/chat/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                conversation_id: state.conversationId,
                resume_id: state.resumeId,
                context: {
                    model: state.selectedModel,
                    temperature: state.settings.temperature,
                    max_tokens: state.settings.maxTokens
                }
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Request failed');
        }

        const data = await response.json();

        // Update state
        state.conversationId = data.conversation_id;
        state.currentVersion = data.current_resume_version;

        // Remove typing indicator
        removeTypingIndicator(typingId);

        // Add assistant message
        addAssistantMessage(data);

        // Update versions if changed
        if (state.resumeId && data.resume_changes && data.resume_changes.length > 0) {
            await loadVersions(state.resumeId);
            await loadResumeContent(state.resumeId);
            updateChangesPanel(data.resume_changes);
            
            if (state.settings.autoExpand) {
                elements.resultsPanel.classList.remove('collapsed');
                switchTab('changes');
            }
        }

        // Update evaluation if available
        if (data.evaluation) {
            updateEvaluation(data.evaluation);
        }

        // Highlight active agent
        if (data.agent_type) {
            highlightAgent(data.agent_type);
        }

        // Update analysis if available
        if (data.analysis) {
            updateAnalysis(data.analysis);
        }

    } catch (error) {
        removeTypingIndicator(typingId);
        addSystemMessage(`❌ Error: ${error.message}`);
        console.error('Chat error:', error);
    } finally {
        state.isProcessing = false;
        handleInputChange();
    }
}

async function loadResumeContent(resumeId) {
    try {
        const response = await fetch(`${API_BASE}/resume/${resumeId}`);
        if (!response.ok) return;

        const data = await response.json();
        renderResumePreview(data.sections);

    } catch (error) {
        console.error('Failed to load resume content:', error);
    }
}

async function loadVersions(resumeId) {
    try {
        const response = await fetch(`${API_BASE}/resume/${resumeId}/versions`);
        if (!response.ok) return;

        const data = await response.json();
        state.versions = data.versions;
        renderVersions(data.versions);

    } catch (error) {
        console.error('Failed to load versions:', error);
    }
}

async function revertToVersion(versionNumber) {
    if (!state.resumeId) return;

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE}/resume/${state.resumeId}/revert/${versionNumber}`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error('Revert failed');
        }

        const data = await response.json();
        state.currentVersion = data.new_version_number;

        await loadVersions(state.resumeId);
        await loadResumeContent(state.resumeId);

        addSystemMessage(`↩️ Reverted to version ${versionNumber}`);

    } catch (error) {
        addSystemMessage(`❌ Error reverting: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

// ========================================
// UI Functions
// ========================================

function handleInputChange() {
    const hasText = elements.messageInput.value.trim().length > 0;
    elements.sendBtn.disabled = !hasText || state.isProcessing;
    updateCharCount();
}

function updateCharCount() {
    const count = elements.messageInput.value.length;
    elements.charCount.textContent = `${count} / 4000`;
    
    if (count > 3800) {
        elements.charCount.style.color = 'var(--warning)';
    } else if (count > 3950) {
        elements.charCount.style.color = 'var(--error)';
    } else {
        elements.charCount.style.color = 'var(--text-dim)';
    }
}

function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function autoResize() {
    const textarea = elements.messageInput;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
}

function sendMessage() {
    const message = elements.messageInput.value.trim();
    if (!message || state.isProcessing) return;

    elements.messageInput.value = '';
    autoResize();
    updateCharCount();
    sendChatMessage(message);
}

function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    uploadResume(file);
    e.target.value = '';
}

function handleModelChange(e) {
    state.selectedModel = e.target.value;
    elements.currentModel.textContent = e.target.value;
    
    // Optionally notify backend of model change
    addSystemMessage(`🔄 Switched to model: ${getModelDisplayName(e.target.value)}`);
}

function getModelDisplayName(modelId) {
    const names = {
        'llama-3.3-70b-versatile': 'Llama 3.3 70B',
        'llama-3.1-8b-instant': 'Llama 3.1 8B',
        'mixtral-8x7b-32768': 'Mixtral 8x7B',
        'gemma2-9b-it': 'Gemma 2 9B'
    };
    return names[modelId] || modelId;
}

function addMessage(role, content) {
    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;

    const avatar = role === 'user' ? '👤' : '🤖';

    messageEl.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-text">${formatMessageContent(content)}</div>
        </div>
    `;

    elements.messages.appendChild(messageEl);
    scrollToBottom();
}

function addAssistantMessage(data) {
    const messageEl = document.createElement('div');
    messageEl.className = 'message assistant';

    let changesHtml = '';
    if (data.resume_changes && data.resume_changes.length > 0) {
        changesHtml = `
            <div class="changes-container">
                <div class="changes-header">📝 Changes Made</div>
                ${data.resume_changes.map(change => `
                    <div class="change-item">
                        <span class="change-type ${change.change_type}">${change.change_type}</span>
                        <strong>${change.section}</strong>
                    </div>
                `).join('')}
            </div>
        `;
    }

    const agentBadge = data.agent_type ? `
        <span class="agent-badge">
            ${getAgentIcon(data.agent_type)} ${formatAgentName(data.agent_type)}
        </span>
    ` : '';

    messageEl.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="message-text">${formatMessageContent(data.message)}</div>
            ${changesHtml}
            <div class="message-meta">
                ${agentBadge}
                <span>v${data.current_resume_version}</span>
            </div>
        </div>
    `;

    elements.messages.appendChild(messageEl);
    scrollToBottom();
}

function addSystemMessage(content) {
    const messageEl = document.createElement('div');
    messageEl.className = 'message assistant';

    messageEl.innerHTML = `
        <div class="message-avatar">ℹ️</div>
        <div class="message-content">
            <div class="message-text">${content}</div>
        </div>
    `;

    elements.messages.appendChild(messageEl);
    scrollToBottom();
}

function showTypingIndicator() {
    const id = 'typing-' + Date.now();
    const typingEl = document.createElement('div');
    typingEl.id = id;
    typingEl.className = 'message assistant';

    typingEl.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    elements.messages.appendChild(typingEl);
    scrollToBottom();
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function updateResumeStatus(data) {
    elements.resumeStatus.classList.add('uploaded');
    elements.resumeStatus.innerHTML = `
        <div class="status-icon">✅</div>
        <div class="status-text">
            <span class="status-label">${data.filename}</span>
            <span class="status-detail">${data.sections_detected.length} sections detected</span>
        </div>
    `;
}

function updateConnectionStatus(connected, model = '') {
    const statusEl = elements.connectionStatus;
    if (connected) {
        statusEl.innerHTML = `<span class="status-dot"></span> <span id="current-model">${model || 'Connected'}</span>`;
        statusEl.querySelector('.status-dot').style.background = 'var(--success)';
        elements.modelStatus.innerHTML = `<span class="pulse-dot"></span> Connected`;
    } else {
        statusEl.innerHTML = `<span class="status-dot"></span> Disconnected`;
        statusEl.querySelector('.status-dot').style.background = 'var(--error)';
        elements.modelStatus.innerHTML = `<span class="pulse-dot" style="background: var(--error)"></span> Disconnected`;
    }
}

function renderResumePreview(sections) {
    if (!sections || sections.length === 0) {
        elements.previewEmpty.style.display = 'flex';
        elements.resumePreview.classList.remove('has-content');
        return;
    }

    elements.previewEmpty.style.display = 'none';
    elements.resumePreview.classList.add('has-content');
    elements.resumePreview.innerHTML = sections.map(section => `
        <div class="resume-section">
            <h4>${section.title}</h4>
            <p>${escapeHtml(section.content)}</p>
        </div>
    `).join('');
}

function renderVersions(versions) {
    if (!versions || versions.length === 0) {
        elements.versionsSection.style.display = 'none';
        return;
    }

    elements.versionsSection.style.display = 'block';
    elements.versionsList.innerHTML = versions.slice().reverse().map(v => `
        <div class="version-item ${v.version_number === state.currentVersion ? 'current' : ''}" 
             onclick="revertToVersion(${v.version_number})">
            <span>v${v.version_number}</span>
            <span>${v.agent_used || 'manual'}</span>
        </div>
    `).join('');
}

function updateChangesPanel(changes) {
    if (!changes || changes.length === 0) {
        elements.changesEmpty.style.display = 'flex';
        elements.changesList.classList.remove('has-content');
        return;
    }

    elements.changesEmpty.style.display = 'none';
    elements.changesList.classList.add('has-content');
    elements.changesList.innerHTML = changes.map(change => `
        <div class="change-card">
            <div class="change-card-header">
                <span class="change-card-section">${change.section}</span>
                <span class="change-type ${change.change_type}">${change.change_type}</span>
            </div>
            <div class="change-card-content">${change.description || 'Content updated'}</div>
        </div>
    `).join('');
}

function updateAnalysis(analysis) {
    if (!analysis) {
        elements.analysisEmpty.style.display = 'flex';
        elements.analysisContent.classList.remove('has-content');
        return;
    }

    elements.analysisEmpty.style.display = 'none';
    elements.analysisContent.classList.add('has-content');
    
    let html = '';
    if (analysis.strengths) {
        html += `
            <div class="analysis-item">
                <h5>💪 Strengths</h5>
                <p>${analysis.strengths.join('<br>')}</p>
            </div>
        `;
    }
    if (analysis.improvements) {
        html += `
            <div class="analysis-item">
                <h5>📈 Suggested Improvements</h5>
                <p>${analysis.improvements.join('<br>')}</p>
            </div>
        `;
    }
    if (analysis.keywords) {
        html += `
            <div class="analysis-item">
                <h5>🔑 Key Skills Detected</h5>
                <p>${analysis.keywords.join(', ')}</p>
            </div>
        `;
    }
    
    elements.analysisContent.innerHTML = html;
}

function updateEvaluation(evaluation) {
    state.evaluation = evaluation;
    
    // Update score circle
    const score = evaluation.overall || 0;
    const circumference = 283; // 2 * PI * 45
    const offset = circumference - (score / 100) * circumference;
    
    elements.scoreCircle.style.strokeDashoffset = offset;
    elements.scoreValue.textContent = `${score}%`;
    
    // Show score section
    elements.scoreSection.style.display = 'block';
    
    // Update breakdown
    elements.scoreBreakdown.innerHTML = `
        <div class="score-item">
            <span class="score-item-label">Keywords</span>
            <span class="score-item-value">${evaluation.keywords || 0}%</span>
        </div>
        <div class="score-item">
            <span class="score-item-label">Format</span>
            <span class="score-item-value">${evaluation.format || 0}%</span>
        </div>
        <div class="score-item">
            <span class="score-item-label">Impact</span>
            <span class="score-item-value">${evaluation.impact || 0}%</span>
        </div>
    `;
    
    // Update eval modal
    document.getElementById('eval-overall').textContent = `${evaluation.overall || 0}%`;
    document.getElementById('eval-keywords').textContent = `${evaluation.keywords || 0}%`;
    document.getElementById('eval-format').textContent = `${evaluation.format || 0}%`;
    document.getElementById('eval-impact').textContent = `${evaluation.impact || 0}%`;
    
    document.getElementById('overall-bar').style.width = `${evaluation.overall || 0}%`;
    document.getElementById('keywords-bar').style.width = `${evaluation.keywords || 0}%`;
    document.getElementById('format-bar').style.width = `${evaluation.format || 0}%`;
    document.getElementById('impact-bar').style.width = `${evaluation.impact || 0}%`;
}

function highlightAgent(agentType) {
    elements.agentItems.forEach(item => {
        item.classList.toggle('active', item.dataset.agent === agentType);
    });
}

function switchTab(tabName) {
    // Update tab buttons
    elements.panelTabs.forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

function clearChat() {
    elements.messages.innerHTML = '';
    elements.welcomeMessage.classList.remove('hidden');
    state.conversationId = null;
}

function showLoading(show) {
    elements.loadingOverlay.classList.toggle('active', show);
}

function scrollToBottom() {
    elements.chatContainer.scrollTop = elements.chatContainer.scrollHeight;
}

// ========================================
// Modal Functions
// ========================================

function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// ========================================
// Settings Functions
// ========================================

function loadSettings() {
    const saved = localStorage.getItem('careerflow_settings');
    if (saved) {
        try {
            state.settings = { ...state.settings, ...JSON.parse(saved) };
            applySettings();
        } catch (e) {
            console.error('Failed to load settings:', e);
        }
    }
}

function applySettings() {
    if (elements.temperatureSlider) {
        elements.temperatureSlider.value = state.settings.temperature * 100;
        elements.tempValue.textContent = state.settings.temperature.toFixed(1);
    }
    if (elements.maxTokensSlider) {
        elements.maxTokensSlider.value = state.settings.maxTokens;
        elements.tokensValue.textContent = state.settings.maxTokens;
    }
    if (elements.exportFormat) {
        elements.exportFormat.value = state.settings.exportFormat;
    }
    if (elements.showReasoning) {
        elements.showReasoning.checked = state.settings.showReasoning;
    }
    if (elements.autoExpand) {
        elements.autoExpand.checked = state.settings.autoExpand;
    }
}

function saveSettings() {
    state.settings = {
        temperature: parseFloat(elements.temperatureSlider.value) / 100,
        maxTokens: parseInt(elements.maxTokensSlider.value),
        exportFormat: elements.exportFormat.value,
        showReasoning: elements.showReasoning.checked,
        autoExpand: elements.autoExpand.checked
    };
    
    localStorage.setItem('careerflow_settings', JSON.stringify(state.settings));
    closeModal('settings-modal');
    addSystemMessage('✅ Settings saved successfully');
}

function resetSettings() {
    state.settings = {
        temperature: 0.7,
        maxTokens: 2048,
        exportFormat: 'pdf',
        showReasoning: true,
        autoExpand: true
    };
    applySettings();
    localStorage.removeItem('careerflow_settings');
    addSystemMessage('🔄 Settings reset to defaults');
}

// ========================================
// Export Function
// ========================================

function handleExport() {
    if (!state.resumeId) {
        addSystemMessage('⚠️ Please upload a resume first');
        return;
    }
    
    addSystemMessage(`📥 Exporting resume as ${state.settings.exportFormat.toUpperCase()}...`);
    // In a real implementation, this would call the backend to generate the export
}

// ========================================
// Utility Functions
// ========================================

function formatMessageContent(content) {
    // Convert markdown-like formatting
    let formatted = escapeHtml(content);

    // Bold
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Line breaks
    formatted = formatted.replace(/\n/g, '<br>');

    // Bullet points
    formatted = formatted.replace(/^• (.+)$/gm, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>)+/g, '<ul>$&</ul>');

    return formatted;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getAgentIcon(agentType) {
    const icons = {
        company_research: '🏢',
        job_matching: '🎯',
        translation: '🌍',
        router: '🔀'
    };
    return icons[agentType] || '🤖';
}

function formatAgentName(agentType) {
    const names = {
        company_research: 'Company Research',
        job_matching: 'Job Matching',
        translation: 'Translation',
        router: 'Router'
    };
    return names[agentType] || agentType;
}

// Make revertToVersion available globally
window.revertToVersion = revertToVersion;
