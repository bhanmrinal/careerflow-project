# Environment File Setup

## Why Two .env Locations?

The code currently looks for `.env` files in two locations:
1. **Project root** (`../.env` from backend/) - **RECOMMENDED**
2. **Backend directory** (`backend/.env`) - Fallback

This was done because:
- When `run.py` was moved to `backend/`, we needed to support both locations
- For Railway deployment, environment variables are set in the dashboard (no .env file needed)
- For local development, you can use either location

## Recommended Setup

**Use a single `.env` file in the project root** (same level as `backend/`, `frontend/`, `tests/`):

```
careerflow-project/
├── .env                    ← Put your .env file here
├── backend/
│   └── app/
├── frontend/
└── tests/
```

## .env File Template

Create `.env` in the project root with:

```env
# Groq API (Required)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Application
APP_ENV=development
APP_DEBUG=true
SECRET_KEY=your-secret-key-change-in-production

# Server
HOST=0.0.0.0
PORT=8000

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Firebase (Optional - for persistent storage)
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY_ID=your_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your_client_id
FIREBASE_CLIENT_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/...

# File Upload
MAX_FILE_SIZE_MB=10
UPLOAD_DIRECTORY=./uploads

# ChromaDB
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

## Cleaning Up

If you have a `.env` file in `backend/`, you can:
1. Move it to the project root
2. Delete the one in `backend/`
3. The code will automatically find it in the project root

## Railway Deployment

For Railway, you don't need a `.env` file. Just add all variables in the Railway dashboard. See `RAILWAY_DEPLOYMENT.md` for details.

