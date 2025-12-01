# AI Knowledge Assistant 🤖

An AI-powered document assistant that allows users to upload PDF and DOCX files, process them, and ask questions about their content. Built with FastAPI backend, vanilla JavaScript frontend, and deployed with Docker.

![Python](https://img.shields.io/badge/python-3.10-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)![Docker](https://img.shields.io/badge/Docker-ready-blue)

## ✨ Features

- 🔐 **User Authentication** - Secure user registration and login with JWT tokens
- 📄 **Document Processing** - Upload and process PDF and DOCX files
- 🔍 **Vector Search** - Elasticsearch-powered semantic search
- 💬 **AI Chat Interface** - Ask questions about your uploaded documents
- ⚡ **Real-time Processing** - Celery-based asynchronous document processing
- 💾 **Caching** - Redis caching for faster query responses
- 🎨 **Modern UI** - Clean, responsive frontend interface

## 🏗️ Architecture

```
┌─────────────┐
│   Nginx     │  ← Frontend (HTML/CSS/JS)
└──────┬──────┘
       │
┌──────▼──────┐
│   FastAPI   │  ← Backend API
└──────┬──────┘
       │
       ├────► PostgreSQL  (User Data)
       ├────► Redis       (Caching)
       ├────► RabbitMQ    (Task Queue)
       └────► Elasticsearch (Vector Search)
              ↑
        ┌─────┴─────┐
        │   Celery  │  ← Background Workers
        │   Worker  │
        └───────────┘
```

## 📋 Prerequisites

### For Local Development
- Python 3.10+
- PostgreSQL 15+
- Redis
- RabbitMQ
- Elasticsearch 8.11+
- Node.js (optional, for serving frontend)

### For Docker Deployment
- Docker
- Docker Compose

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/AI-Knowledge-Assistant.git
   cd AI-Knowledge-Assistant
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and update the values (especially `JWT_SECRET_KEY` for production):
   ```env
   POSTGRES_PASSWORD=your_secure_password
   JWT_SECRET_KEY=your_super_secret_key_here
   ```

3. **Build and start all services**
   ```bash
   docker compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - RabbitMQ Management: http://localhost:15672 (guest/guest)

### Option 2: Local Development

1. **Install PostgreSQL, Redis, RabbitMQ, and Elasticsearch**

2. **Clone and setup**
   ```bash
   git clone https://github.com/yourusername/AI-Knowledge-Assistant.git
   cd AI-Knowledge-Assistant
   ```

3. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

6. **Start the backend**
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Start Celery worker** (in a new terminal)
   ```bash
   celery -A backend.celery_worker worker --loglevel=info
   ```

8. **Serve the frontend** (in a new terminal)
   ```bash
   # Using Python's HTTP server
   python -m http.server 3000
   ```

9. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs

## 📖 Usage

### First Time Setup

1. **Register an account**
   - Open the application in your browser
   - Click "Register" on the login modal
   - Fill in your details (username, email, full name, password)
   - You'll be automatically logged in after registration

2. **Upload documents**
   - Click "Browse Files" or drag & drop PDF/DOCX files
   - Wait for the upload and processing to complete
   - Files will show "Ingested" status when ready

3. **Ask questions**
   - Type your question in the chat input
   - Press Enter or click the send button
   - The AI will respond based on your uploaded documents

### API Endpoints

#### Authentication
- `POST /register` - Register a new user
- `POST /token` - Login and get access token
- `GET /users/me` - Get current user info

#### Documents
- `POST /ingest` - Upload and process documents
- `POST /query` - Query the knowledge base

#### Health Check
- `GET /health` - Check API health status

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_HOST` | PostgreSQL host | localhost |
| `POSTGRES_PORT` | PostgreSQL port | 5432 |
| `POSTGRES_DB` | Database name | ai_knowledge_assistant |
| `POSTGRES_USER` | Database user | postgres |
| `POSTGRES_PASSWORD` | Database password | changeme123 |
| `REDIS_HOST` | Redis host | localhost |
| `REDIS_PORT` | Redis port | 6379 |
| `RABBITMQ_HOST` | RabbitMQ host | localhost |
| `RABBITMQ_USER` | RabbitMQ user | guest |
| `RABBITMQ_PASS` | RabbitMQ password | guest |
| `ELASTICSEARCH_HOST` | Elasticsearch URL | http://localhost:9200 |
| `JWT_SECRET_KEY` | JWT secret key | your-secret-key-change-this-in-production |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | 30 |

> ⚠️ **Security Warning**: Change `JWT_SECRET_KEY` and `POSTGRES_PASSWORD` before deploying to production!

## 📁 Project Structure

```
AI-Knowledge-Assistant/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── auth.py              # Authentication logic
│   ├── models.py            # Database models
│   ├── database.py          # Database connections
│   ├── search.py            # Elasticsearch integration
│   ├── llm.py              # LLM integration
│   ├── celery_worker.py    # Celery tasks
│   └── Dockerfile          # Backend Docker image
├── index.html              # Frontend HTML
├── styles.css              # Frontend styles
├── script.js               # Frontend JavaScript
├── config.js               # Frontend configuration
├── nginx.conf              # Nginx configuration
├── docker-compose.yml      # Docker services configuration
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## 🔒 Security Notes

### For Production Deployment

1. **Change default credentials**
   ```env
   JWT_SECRET_KEY=generate-a-strong-random-key
   POSTGRES_PASSWORD=use-a-strong-password
   RABBITMQ_USER=custom-user
   RABBITMQ_PASS=strong-password
   ```

2. **Use HTTPS**
   - Configure SSL/TLS certificates
   - Update nginx configuration for HTTPS

3. **Restrict CORS**
   - Update `backend/main.py` to specify allowed origins
   ```python
   allow_origins=["https://yourdomain.com"]
   ```

4. **Set up firewall rules**
   - Only expose ports 80 and 443
   - Keep database and message queue ports internal

5. **Regular updates**
   - Keep Docker images and dependencies updated
   - Monitor security advisories

## 🐛 Troubleshooting

### Docker Issues

**Problem**: Services fail to start
```bash
# Check service logs
docker compose logs app
docker compose logs postgres

# Rebuild from scratch
docker compose down -v
docker compose up --build
```

**Problem**: Database connection errors
```bash
# Check if PostgreSQL is ready
docker compose ps postgres

# Reset database
docker compose down -v
docker compose up -d postgres
# Wait 10 seconds
docker compose up app
```

### Local Development Issues

**Problem**: Module not found errors
```bash
# Make sure you're in the virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Problem**: Elasticsearch connection failed
```bash
# Check if Elasticsearch is running
curl http://localhost:9200

# If not, start Elasticsearch service
```

**Problem**: Celery worker not processing tasks
```bash
# Check RabbitMQ is running
# Check Celery worker logs for errors
# Restart the worker
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- UI styled with custom CSS and [Font Awesome](https://fontawesome.com/)
- Document processing with PyPDF2 and python-docx
- Vector search powered by Elasticsearch

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the troubleshooting section

---

Made with ❤️ for the AI Knowledge Assistant Project
