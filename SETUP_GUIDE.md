# Quick Setup Guide 🚀

## Getting Your API Key

### Option 1: Google Gemini (Recommended - FREE!)

1. **Get API Key** (Free!)
   - Go to [Google AI Studio](https://ai.google.dev/)
   - Click "Get API Key"
   - Sign in with your Google account
   - Click "Create API Key"
   - Copy your API key

2. **Create `.env` file**
   ```bash
   # Copy the example file
   cp .env.example .env
   ```

3. **Add your API key to `.env`**
   ```env
   # Open .env and replace this line:
   GOOGLE_API_KEY=your-google-api-key-here
   
   # With your actual key:
   GOOGLE_API_KEY=AIzaSyC...your-actual-key...
   
   # Keep these as-is:
   LLM_PROVIDER=gemini
   LLM_MODEL=gemini-1.5-flash
   ```

### Option 2: OpenAI (Paid)

1. **Get API Key**
   - Go to [OpenAI Platform](https://platform.openai.com/)
   - Sign up and add payment method
   - Go to API Keys section
   - Create new secret key

2. **Update `.env`**
   ```env
   # Comment out Gemini, add OpenAI:
   # GOOGLE_API_KEY=your-google-api-key-here
   OPENAI_API_KEY=sk-...your-key...
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4-turbo-preview
   ```

---

## Running the Application

### Using Docker (Easiest)

```bash
# 1. Make sure .env is configured with your API key
# 2. Start everything
docker compose up --build

# 3. Open browser
# Frontend: http://localhost
# API: http://localhost:8000/docs
```

### Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start services (PostgreSQL, Redis, RabbitMQ, Elasticsearch)
# You can use Docker for just the services:
docker compose up postgres redis rabbitmq elasticsearch

# 3. Start backend
uvicorn backend.main:app --reload --port 8000

# 4. Start Celery worker (new terminal)
celery -A backend.celery_worker worker --loglevel=info

# 5. Serve frontend (new terminal)
python -m http.server 3000

# 6. Open http://localhost:3000
```

---

## Testing Without API Key

If you don't have an API key yet, the application will still work but will return mock responses. You'll see messages like:

> "Mock Response - Configure GOOGLE_API_KEY in .env to get real AI responses"

---

## First Time Usage

1. **Register** - Create your account
2. **Upload** - Add a PDF or DOCX file
3. **Ask** - Type a question about your document
4. **Get Answer** - AI will respond based on your documents!

---

## Troubleshooting

### "Error generating answer"
- Check if your API key is correct in `.env`
- Make sure you copied the entire key
- Restart the application after changing `.env`

### "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### "Port already in use"
```bash
# Stop conflicting services or change ports in docker-compose.yml
docker compose down
```

---

## Cost Information

**Google Gemini:**
- ✅ **FREE** tier available
- 60 requests per minute
- Perfect for testing and small projects

**OpenAI:**
- 💰 Paid only
- ~$0.01 per 1000 tokens (GPT-4 Turbo)
- More expensive but very powerful

---

**Need help?** Check the main [README.md](README.md) for detailed documentation.
