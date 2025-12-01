from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
import uuid
import io
import logging

# PDF and DOCX parsing
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("Warning: PyPDF2 not installed. PDF parsing disabled.")

try:
    import docx
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False
    print("Warning: python-docx not installed. DOCX parsing disabled.")

from .auth import (Token, User, UserCreate, authenticate_user, 
                   create_access_token, get_current_user, 
                   create_user, get_user_by_username, get_user_by_email,
                   ACCESS_TOKEN_EXPIRE_MINUTES)
from .models import get_db, init_db
from .database import get_redis_client
from .search import create_index, search_documents
from .llm import generate_answer, get_embedding
from .celery_worker import process_document

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Knowledge Assistant",
    description="AI-powered document assistant with authentication",
    version="1.0.0"
)

# CORS - Allow all origins for development (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup Event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up application...")
    init_db()
    create_index()
    logger.info("✓ Application started successfully")

# Health Check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "pdf_support": PDF_SUPPORT,
        "docx_support": DOCX_SUPPORT
    }

# --- Auth Endpoints ---

@app.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if username already exists
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = create_user(db, user)
    logger.info(f"New user registered: {user.username}")
    return new_user

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login to get access token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    logger.info(f"User logged in: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

# --- Document Processing Functions ---

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    if not PDF_SUPPORT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF parsing not supported. Install PyPDF2."
        )
    
    try:
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error parsing PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse PDF: {str(e)}"
        )

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file"""
    if not DOCX_SUPPORT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DOCX parsing not supported. Install python-docx."
        )
    
    try:
        docx_file = io.BytesIO(file_content)
        doc = docx.Document(docx_file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    except Exception as e:
        logger.error(f"Error parsing DOCX: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse DOCX: {str(e)}"
        )

# --- Ingestion Endpoint ---

@app.post("/ingest")
async def ingest_documents(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload and process documents"""
    results = []
    
    for file in files:
        try:
            content = await file.read()
            
            # Extract text based on file type
            if file.filename.lower().endswith('.pdf'):
                text_content = extract_text_from_pdf(content)
            elif file.filename.lower().endswith('.docx'):
                text_content = extract_text_from_docx(content)
            else:
                # Try UTF-8 decode for text files
                try:
                    text_content = content.decode("utf-8")
                except:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unsupported file type: {file.filename}"
                    )
            
            if not text_content or len(text_content.strip()) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No text content found in {file.filename}"
                )
            
            doc_id = str(uuid.uuid4())
            
            # Trigger Celery Task
            task = process_document.delay(doc_id, text_content, file.filename)
            results.append({
                "filename": file.filename,
                "doc_id": doc_id,
                "task_id": task.id,
                "status": "Processing"
            })
            logger.info(f"Document uploaded: {file.filename} by {current_user.username}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing {file.filename}: {e}")
            results.append({
                "filename": file.filename,
                "status": "Failed",
                "error": str(e)
            })
    
    return {"message": "Files uploaded and processing started", "files": results}

# --- Query Endpoint ---

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def query_knowledge_base(
    request: QueryRequest,
    current_user: User = Depends(get_current_user)
):
    """Query the knowledge base"""
    redis_client = get_redis_client()
    
    # 1. Check Cache
    if redis_client:
        try:
            cached_response = redis_client.get(request.query)
            if cached_response:
                logger.info(f"Cache hit for query: {request.query[:50]}...")
                return {"response": cached_response, "source": "cache"}
        except Exception as e:
            logger.warning(f"Redis error: {e}")
    
    # 2. Vector Search
    query_embedding = get_embedding(request.query)
    retrieved_docs = search_documents(query_embedding)
    
    # 3. Generate Answer
    if retrieved_docs:
        context = "\n\n".join([doc.get("content", "") for doc in retrieved_docs])
        answer = generate_answer(context, request.query)
    else:
        answer = "I don't have enough information to answer that question. Please upload relevant documents first."
    
    # 4. Cache Response
    if redis_client:
        try:
            redis_client.setex(request.query, 3600, answer)  # Cache for 1 hour
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")
    
    logger.info(f"Query processed for user: {current_user.username}")
    return {"response": answer, "source": "llm", "context": retrieved_docs}

