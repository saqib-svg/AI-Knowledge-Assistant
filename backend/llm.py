import os
import logging
from typing import List
import traceback

logger = logging.getLogger(__name__)

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash-latest")  # Updated default
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Initialize LLM based on provider
gemini_model = None
if LLM_PROVIDER == "gemini":
    try:
        import google.generativeai as genai
        from google.api_core.exceptions import ResourceExhausted, InvalidArgument
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        if GOOGLE_API_KEY:
            genai.configure(api_key=GOOGLE_API_KEY)
            
            # Fix model name if using old format
            model_name = LLM_MODEL
            if model_name == "gemini-1.5-flash" or model_name == "gemini-1.5-pro":
                model_name = f"{model_name}-latest"
                logger.warning(f"⚠ Updated model name from {LLM_MODEL} to {model_name}")
            
            gemini_model = genai.GenerativeModel(model_name)
            logger.info(f"✓ Google Gemini initialized with model: {model_name}")
        else:
            logger.warning("⚠ GOOGLE_API_KEY not set. Using mock responses.")
    except ImportError as e:
        logger.warning(f"⚠ google-generativeai not installed: {e}")
    except Exception as e:
        logger.error(f"✗ Error initializing Gemini: {e}")
        logger.error(traceback.format_exc())
        
elif LLM_PROVIDER == "openai":
    try:
        import openai
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if OPENAI_API_KEY:
            openai.api_key = OPENAI_API_KEY
            logger.info(f"✓ OpenAI initialized with model: {LLM_MODEL}")
        else:
            logger.warning("⚠ OPENAI_API_KEY not set. Using mock responses.")
    except ImportError:
        logger.warning("⚠ openai not installed. Using mock responses.")
else:
    logger.warning(f"⚠ Unknown LLM_PROVIDER: {LLM_PROVIDER}. Using mock responses.")

# Initialize embedding model
embedding_model = None
try:
    from sentence_transformers import SentenceTransformer
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    logger.info(f"✓ Embedding model initialized: {EMBEDDING_MODEL}")
except ImportError:
    logger.warning("⚠ sentence-transformers not installed. Using random embeddings.")
except Exception as e:
    logger.error(f"✗ Error loading embedding model: {e}")
    logger.error(traceback.format_exc())


def generate_answer(context: str, query: str) -> str:
    """
    Generate an answer to the query based on the provided context.
    
    Args:
        context: The relevant document content
        query: The user's question
    
    Returns:
        The generated answer
    """
    if LLM_PROVIDER == "gemini" and gemini_model:
        try:
            # Truncate context to avoid token limits (Gemini has ~30k token limit)
            max_context_chars = 15000  # Roughly 4000 tokens
            if len(context) > max_context_chars:
                context = context[:max_context_chars] + "\n\n[Context truncated for length...]"
                logger.info(f"Context truncated to {max_context_chars} characters")
            
            prompt = f"""Based on the following context from documents, please answer the question. 
If the answer cannot be found in the context, say "I don't have enough information to answer that question."
Be concise and specific in your answer.

Context:
{context}

Question: {query}

Answer:"""
            
            logger.info(f"Calling Gemini API with query: {query[:100]}")
            logger.info(f"Context length: {len(context)} characters")
            
            response = gemini_model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.7,
                    'top_p': 0.95,
                    'top_k': 40,
                    'max_output_tokens': 2048,
                },
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE",
                    },
                ]
            )
            
            if not response or not response.text:
                logger.error("Gemini returned empty response")
                return "I received an empty response from the AI. Please try again."
            
            logger.info(f"✓ Gemini response received: {response.text[:100]}...")
            return response.text
            
        except Exception as gemini_error:
            # Check for specific Gemini errors
            error_str = str(gemini_error)
            logger.error(f"✗ Gemini API error: {error_str}")
            logger.error(traceback.format_exc())
            
            if "quota" in error_str.lower() or "resource_exhausted" in error_str.lower():
                return "I'm currently overloaded (API quota exceeded). Please try again in a minute."
            elif "not found" in error_str.lower() or "404" in error_str:
                return f"""The Gemini model configuration is incorrect. 

The model name '{LLM_MODEL}' is not valid. Please update your .env file:

For Gemini 1.5 Flash:
LLM_MODEL=gemini-1.5-flash-latest

Or for Gemini 1.5 Pro:
LLM_MODEL=gemini-1.5-pro-latest

Then restart the services:
docker compose restart app celery_worker"""
            elif "invalid" in error_str.lower():
                return "There was an issue with the request format. Please try rephrasing your question."
            else:
                return f"I encountered an error: {error_str[:300]}. Please try again."
    
    elif LLM_PROVIDER == "openai":
        try:
            import openai
            logger.info(f"Calling OpenAI with query: {query[:100]}")
            
            # Truncate context if too long
            max_context_chars = 12000
            if len(context) > max_context_chars:
                context = context[:max_context_chars]
            
            response = openai.ChatCompletion.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context. If the answer cannot be found in the context, say you don't have enough information."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            logger.info(f"✓ OpenAI response received: {answer[:100]}...")
            return answer
            
        except Exception as e:
            logger.error(f"✗ OpenAI error: {e}")
            logger.error(traceback.format_exc())
            return f"I encountered an error while processing your question: {str(e)[:200]}. Please try again."
    
    else:
        # Mock response for testing without API key
        logger.info("Using mock response (no LLM configured)")
        return f"""Based on the context provided, here's what I found regarding your question: "{query}"

[Mock Response - Configure GOOGLE_API_KEY or OPENAI_API_KEY in .env to get real AI responses]

Context summary: {context[:200]}...

To enable real AI responses:
1. Get a free API key from https://ai.google.dev/ (Gemini) or https://platform.openai.com/ (OpenAI)
2. Add it to your .env file as GOOGLE_API_KEY or OPENAI_API_KEY
3. Set LLM_MODEL=gemini-1.5-flash-latest (for Gemini)
4. Restart the application"""


def get_embedding(text: str) -> List[float]:
    """
    Generate embeddings for the given text.
    
    Args:
        text: The text to embed
    
    Returns:
        A list of floats representing the embedding
    """
    if embedding_model:
        try:
            logger.info(f"Generating embedding for text: {text[:100]}...")
            
            # Truncate text if too long (BERT models have token limits)
            max_length = 512
            if len(text) > max_length * 4:  # Rough estimate: 4 chars per token
                text = text[:max_length * 4]
                logger.info(f"Text truncated to {len(text)} characters")
            
            # Generate embedding using sentence-transformers
            embedding = embedding_model.encode(text, convert_to_numpy=True)
            embedding_list = embedding.tolist()
            
            logger.info(f"✓ Embedding generated, dimension: {len(embedding_list)}")
            
            # Validate embedding dimension
            if len(embedding_list) != 384:
                logger.error(f"Unexpected embedding dimension: {len(embedding_list)}, expected 384")
                raise ValueError(f"Embedding dimension mismatch: {len(embedding_list)} != 384")
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"✗ Error generating embedding: {e}")
            logger.error(traceback.format_exc())
            
            # Fall back to random embedding
            logger.warning("Falling back to random embedding")
            import random
            return [random.random() for _ in range(384)]
    else:
        # Mock embedding for testing (384 dimensions)
        logger.warning("Embedding model not configured, using random embedding")
        import random
        return [random.random() for _ in range(384)]


def test_llm_connection():
    """Test if LLM is properly configured"""
    try:
        test_response = generate_answer("This is a test context.", "What is this?")
        logger.info(f"LLM test successful: {test_response[:100]}")
        return True
    except Exception as e:
        logger.error(f"LLM test failed: {e}")
        return False


def test_embedding_model():
    """Test if embedding model is working"""
    try:
        test_embedding = get_embedding("This is a test sentence.")
        if len(test_embedding) == 384:
            logger.info("✓ Embedding model test successful")
            return True
        else:
            logger.error(f"Embedding test failed: wrong dimension {len(test_embedding)}")
            return False
    except Exception as e:
        logger.error(f"Embedding model test failed: {e}")
        return False