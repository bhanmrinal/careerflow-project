# Railway Deployment Guide

## Image Size Optimization

The deployment has been optimized to stay under Railway's 4GB image limit:

### Changes Made:
1. **Removed sentence-transformers + PyTorch** (~2GB+ savings)
   - Now using ChromaDB's built-in embedding function (all-MiniLM-L6-v2 via onnxruntime)
   - Same embedding quality, much smaller footprint

2. **Removed langchain-chroma** (not needed, using chromadb directly)

3. **Added .dockerignore** to exclude:
   - Virtual environments
   - Test files
   - Local data directories
   - Documentation

4. **Split requirements**:
   - `requirements.txt` - Production only
   - `requirements-dev.txt` - Development (includes tests)

### Expected Image Size: ~1.5-2GB (down from 8.8GB)

## Environment Variables

Add these environment variables in your Railway project settings:

### Required Variables

```env
# Groq API (Required)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Application
APP_ENV=production
APP_DEBUG=false
SECRET_KEY=your_secure_secret_key_here

# Server (PORT is automatically provided by Railway)
HOST=0.0.0.0
```

### Optional Variables (Firebase)

```env
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY_ID=your_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your_client_id
```

## Corrected JSON for Railway

```json
{
  "APP_ENV": "production",
  "APP_DEBUG": "false",
  "SECRET_KEY": "your_secure_secret_key_here",
  "GROQ_API_KEY": "gsk_your_key_here",
  "GROQ_MODEL": "llama-3.3-70b-versatile",
  "HOST": "0.0.0.0",
  "MAX_FILE_SIZE_MB": "10",
  "UPLOAD_DIRECTORY": "./uploads",
  "CHROMA_PERSIST_DIRECTORY": "./chroma_db",
  "FIREBASE_PROJECT_ID": "your_project_id",
  "FIREBASE_CLIENT_EMAIL": "firebase-adminsdk@your-project.iam.gserviceaccount.com",
  "FIREBASE_CLIENT_ID": "your_client_id",
  "FIREBASE_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
}
```

## Important Notes

1. **PORT Variable**: Railway automatically provides the `PORT` environment variable. Do NOT set it manually.

2. **APP_DEBUG**: Must be `false` in production (not `true`).

3. **Firebase Private Key**: Keep the `\\n` escape sequences as-is.

4. **Embeddings**: ChromaDB now handles embeddings internally using onnxruntime. No separate embedding model configuration needed.

## Deployment Steps

1. Push your code to GitHub
2. Connect your GitHub repository to Railway
3. Add all environment variables in Railway dashboard
4. Railway will automatically detect `railway.json` and `nixpacks.toml`
5. The app will be available at your Railway-provided URL

## Troubleshooting

### If build still fails with image size error:
1. Check that `.dockerignore` is being used
2. Verify `requirements.txt` doesn't include `sentence-transformers` or `torch`
3. Try clearing Railway's build cache (in project settings)

### If embeddings don't work:
- ChromaDB's DefaultEmbeddingFunction uses `onnxruntime` which should be installed automatically
- Check logs for any onnxruntime errors
