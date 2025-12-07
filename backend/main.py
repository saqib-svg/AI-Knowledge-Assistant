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
from .models import get_db, init_db, ChatModel, DocumentModel, ChatDocumentModel, MessageModel
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

# CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
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
    doc_ids: List[str] = None  # Optional: filter by specific document IDs

@app.post("/query")
async def query_knowledge_base(
    request: QueryRequest,
    current_user: User = Depends(get_current_user)
):
    """Query the knowledge base"""
    redis_client = get_redis_client()
    
    # Create cache key including doc_ids for proper caching
    cache_key = f"{request.query}:{','.join(request.doc_ids) if request.doc_ids else 'all'}"
    
    # 1. Check Cache
    if redis_client:
        try:
            cached_response = redis_client.get(cache_key)
            if cached_response:
                logger.info(f"Cache hit for query: {request.query[:50]}...")
                return {"response": cached_response, "source": "cache"}
        except Exception as e:
            logger.warning(f"Redis error: {e}")
    
    # 2. Vector Search (with optional doc_ids filter)
    query_embedding = get_embedding(request.query)
<<<<<<< Updated upstream
    logger.info(f"Query embedding generated, shape: {len(query_embedding) if query_embedding else 0}")
    retrieved_docs = search_documents(query_embedding)
    logger.info(f"Vector search returned {len(retrieved_docs) if retrieved_docs else 0} documents")
=======
    retrieved_docs = search_documents(query_embedding, doc_ids=request.doc_ids)
>>>>>>> Stashed changes
    
    # 3. Generate Answer
    if retrieved_docs:
        context = "\n\n".join([doc.get("content", "") for doc in retrieved_docs])
        answer = generate_answer(context, request.query)
    else:
        answer = "I don't have enough information to answer that question. Please upload relevant documents first."
    
    # 4. Cache Response
    if redis_client:
        try:
            redis_client.setex(cache_key, 3600, answer)  # Cache for 1 hour
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")
    
    logger.info(f"Query processed for user: {current_user.username}")
    return {"response": answer, "source": "llm", "context": retrieved_docs}


# --- Chat and Document Management ---

class ChatCreate(BaseModel):
    title: str

class ChatOut(BaseModel):
    id: int
    title: str
    created_at: str = None

    class Config:
        from_attributes = True
    
    @staticmethod
    def from_orm(obj):
        return ChatOut(
            id=obj.id,
            title=obj.title,
            created_at=obj.created_at.isoformat() if obj.created_at else None
        )

@app.post("/chats", response_model=ChatOut, status_code=201)
async def create_chat(chat: ChatCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_chat = ChatModel(user_id=current_user.id, title=chat.title)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    logger.info(f"Chat created: {new_chat.id} by {current_user.username}")
    return ChatOut.from_orm(new_chat)

@app.get("/chats", response_model=List[ChatOut])
async def list_chats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chats = db.query(ChatModel).filter(ChatModel.user_id == current_user.id).order_by(ChatModel.created_at.desc()).all()
    return [ChatOut.from_orm(c) for c in chats]

@app.delete("/chats/{chat_id}")
async def delete_chat(chat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        chat = db.query(ChatModel).filter(ChatModel.id == chat_id, ChatModel.user_id == current_user.id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        # Manually delete related records (simulating CASCADE)
        db.query(MessageModel).filter(MessageModel.chat_id == chat_id).delete()
        db.query(ChatDocumentModel).filter(ChatDocumentModel.chat_id == chat_id).delete()
        
        db.delete(chat)
        db.commit()
        logger.info(f"Chat deleted: {chat_id} by {current_user.username}")
        return {"message": "Chat deleted"}
    except Exception as e:
        logger.error(f"Error deleting chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete chat: {str(e)}")


@app.post("/chats/{chat_id}/documents")
async def upload_documents_to_chat(chat_id: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = db.query(ChatModel).filter(ChatModel.id == chat_id, ChatModel.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    results = []
    for file in files:
        try:
            content = await file.read()
            # extract text
            if file.filename.lower().endswith('.pdf'):
                text_content = extract_text_from_pdf(content)
            elif file.filename.lower().endswith('.docx'):
                text_content = extract_text_from_docx(content)
            else:
                try:
                    text_content = content.decode('utf-8')
                except:
                    raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")

            if not text_content or len(text_content.strip()) == 0:
                raise HTTPException(status_code=400, detail=f"No text content found in {file.filename}")

            es_id = str(uuid.uuid4())
            
            # Synchronously create DB records
            doc = DocumentModel(
                es_id=es_id, 
                filename=file.filename, 
                uploaded_by=current_user.id, 
                preview=(text_content[:1000] if text_content else None)
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            
            link = ChatDocumentModel(chat_id=chat_id, document_id=doc.id)
            db.add(link)
            db.commit()
            
            # Trigger Celery Task for Indexing ONLY
            logger.info(f"Triggering Celery task for {file.filename} (es_id: {es_id})")
            try:
                task = process_document.delay(es_id, text_content, file.filename)
                logger.info(f"Celery task triggered: {task.id}")
            except Exception as celery_error:
                logger.error(f"Failed to trigger Celery task: {celery_error}")
                raise celery_error
            
            # Set initial status in Redis
            redis_client = get_redis_client()
            if redis_client:
                try:
                    redis_client.setex(f"doc_status:{es_id}", 3600, "processing")
                    logger.info(f"Set Redis status to processing for {es_id}")
                except Exception as e:
                    logger.warning(f"Redis error setting status: {e}")
            else:
                logger.warning("Redis client not available for setting status")
            
            results.append({"filename": file.filename, "es_id": es_id, "task_id": task.id, "status": "Processing"})
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading {file.filename}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            results.append({"filename": file.filename, "status": "Failed", "error": str(e)})

    return {"message": "Files uploaded and processing started", "files": results}


@app.get("/chats/{chat_id}/documents")
async def list_chat_documents(chat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = db.query(ChatModel).filter(ChatModel.id == chat_id, ChatModel.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    links = db.query(ChatDocumentModel).filter(ChatDocumentModel.chat_id == chat_id).all()
    docs = [db.query(DocumentModel).get(link.document_id) for link in links]
    
    redis_client = get_redis_client()
    results = []
    for d in docs:
        if not d: continue
        status = "unknown"
        if redis_client:
            try:
                status = redis_client.get(f"doc_status:{d.es_id}") or "ready" # Default to ready if key expired/missing (assuming old docs are done)
            except:
                pass
        results.append({
            "id": d.id, 
            "es_id": d.es_id, 
            "filename": d.filename, 
            "preview": d.preview,
            "status": status
        })
        
    return results


@app.delete("/chats/{chat_id}/documents/{doc_id}")
async def remove_document_from_chat(chat_id: int, doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = db.query(ChatModel).filter(ChatModel.id == chat_id, ChatModel.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    link = db.query(ChatDocumentModel).filter(ChatDocumentModel.chat_id == chat_id, ChatDocumentModel.document_id == doc_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Document not found in chat")
    db.delete(link)
    db.commit()
    return {"message": "Document removed from chat"}


@app.get("/chats/{chat_id}/messages")
async def get_chat_messages(chat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = db.query(ChatModel).filter(ChatModel.id == chat_id, ChatModel.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    messages = db.query(MessageModel).filter(MessageModel.chat_id == chat_id).order_by(MessageModel.created_at.asc()).all()
    return [{"id": m.id, "sender": m.sender, "content": m.content, "created_at": m.created_at.isoformat()} for m in messages]


class MessageCreate(BaseModel):
    content: str

@app.post("/chats/{chat_id}/messages")
async def create_chat_message(chat_id: int, msg: MessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    1. Save user message
    2. Run RAG/LLM
    3. Save AI message
    4. Return AI message
    """
    chat = db.query(ChatModel).filter(ChatModel.id == chat_id, ChatModel.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # 1. Save User Message
    user_message = MessageModel(chat_id=chat_id, sender='user', content=msg.content)
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # 2. Run RAG/LLM Logic
    
    # Collect ES ids for docs linked to this chat
    links = db.query(ChatDocumentModel).filter(ChatDocumentModel.chat_id == chat_id).all()
    es_ids = []
    for link in links:
        doc = db.query(DocumentModel).get(link.document_id)
        if doc and doc.es_id:
            es_ids.append(doc.es_id)
            
    # Check Document Status
    redis_client = get_redis_client()
    if es_ids and redis_client:
        processing_docs = []
        for es_id in es_ids:
            try:
                status = redis_client.get(f"doc_status:{es_id}")
                if status == "processing":
                    processing_docs.append(es_id)
            except:
                pass
        
        if processing_docs:
            answer = "I am still processing the uploaded documents. Please wait a moment and try again."
            # Save AI Message immediately and return
            ai_message = MessageModel(chat_id=chat_id, sender='ai', content=answer)
            db.add(ai_message)
            db.commit()
            db.refresh(ai_message)
            return {
                "user_message": {
                    "id": user_message.id, 
                    "content": user_message.content, 
                    "created_at": user_message.created_at.isoformat()
                },
                "message": answer,
                "ai_message": {
                     "id": ai_message.id,
                     "content": ai_message.content,
                     "created_at": ai_message.created_at.isoformat()
                },
                "context": []
            }

    # Check Cache
    redis_client = get_redis_client()
    cached_answer = None
    
    # Create a cache key that includes the document context
    # This ensures that if documents change (or are added), the cache is invalidated/bypassed for the same query
    docs_hash = "nodocs"
    if es_ids:
        es_ids.sort()
        import hashlib
        docs_hash = hashlib.md5("".join(es_ids).encode()).hexdigest()
    
    cache_key = f"{msg.content}:{docs_hash}"
    
    if redis_client:
        try:
            cached_answer = redis_client.get(cache_key)
        except Exception as e:
            logger.warning(f"Redis error: {e}")
            
    answer = ""
    retrieved_docs = []
    
    if cached_answer:
        answer = cached_answer
        logger.info(f"Cache hit for query: {msg.content[:20]}... (Key: {cache_key})")
    else:
        # Vector Search
        if es_ids:
            logger.info(f"Searching with {len(es_ids)} document(s) context: {es_ids}")
            try:
                query_embedding = get_embedding(msg.content)
                logger.info(f"Generated embedding for query: {msg.content[:20]}...")
                retrieved_docs = search_documents(query_embedding, allowed_ids=es_ids)
                logger.info(f"Retrieved {len(retrieved_docs)} documents from ES")
                
                if retrieved_docs:
                    context = "\n\n".join([doc.get("content", "") for doc in retrieved_docs])
                    answer = generate_answer(context, msg.content)
                else:
                    logger.info("No documents found in ES matching allowed_ids")
                    answer = "I couldn't find any relevant information in the uploaded documents."
            except Exception as e:
                logger.error(f"Error during RAG pipeline: {e}")
                import traceback
                logger.error(traceback.format_exc())
                answer = "I encountered an error while processing your question. Please try again."
        else:
             # No documents attached, just use LLM directly or generic response
             # For this app, let's assume we want to be helpful even without docs, or strictly require them.
             # Given the prompt "AI-based document chat", let's try to answer generally or ask for docs.
             answer = "Please upload documents to this chat so I can answer your questions based on them."

        # Cache Response
        if redis_client and answer:
            try:
                redis_client.setex(cache_key, 3600, answer)
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")

    # 3. Save AI Message
    ai_message = MessageModel(chat_id=chat_id, sender='ai', content=answer)
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)
    
    return {
        "user_message": {
            "id": user_message.id, 
            "content": user_message.content, 
            "created_at": user_message.created_at.isoformat()
        },
        "message": answer, # For frontend compatibility
        "ai_message": {
             "id": ai_message.id,
             "content": ai_message.content,
             "created_at": ai_message.created_at.isoformat()
        },
        "context": retrieved_docs
    }

