import os
import logging
from typing import List

logger = logging.getLogger(__name__)

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Initialize LLM based on provider
if LLM_PROVIDER == "gemini":
    try:
        import google.generativeai as genai
        from google.api_core.exceptions import ResourceExhausted
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        if GOOGLE_API_KEY:
            genai.configure(api_key=GOOGLE_API_KEY)
            gemini_model = genai.GenerativeModel(LLM_MODEL)
            logger.info(f"✓ Google Gemini initialized with model: {LLM_MODEL}")
        else:
            logger.warning("⚠ GOOGLE_API_KEY not set. Using mock responses.")
            gemini_model = None
    except ImportError:
        logger.warning("⚠ google-generativeai not installed. Using mock responses.")
        gemini_model = None
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
try:
    from sentence_transformers import SentenceTransformer
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    logger.info(f"✓ Embedding model initialized: {EMBEDDING_MODEL}")
except ImportError:
    logger.warning("⚠ sentence-transformers not installed. Using random embeddings.")
    embedding_model = None


def generate_answer(context: str, query: str) -> str:
    """
    Generate an answer to the query based on the provided context.
    
    Args:
        context: The relevant document content
        query: The user's question
    
    Returns:
        The generated answer
    """
    logger.info(f"generate_answer called - LLM_PROVIDER: {LLM_PROVIDER}, gemini_model: {gemini_model is not None}")
    
    if LLM_PROVIDER == "gemini" and gemini_model:
        try:
            logger.info("Calling Gemini API to generate answer...")
            prompt = f"""Based on the following context, please answer the question. If the answer cannot be found in the context, say "I don't have enough information to answer that question."

Context:
{context}

Question: {query}

Answer:"""
            
            logger.info(f"Calling Gemini with query: {query[:100]}")
            response = gemini_model.generate_content(prompt)
<<<<<<< Updated upstream
            logger.info(f"Gemini response received: {response.text[:100]}")
=======
            logger.info(f"Gemini API call successful. Response length: {len(response.text)}")
>>>>>>> Stashed changes
            return response.text
        except ResourceExhausted:
            logger.warning("Gemini quota exceeded (ResourceExhausted)")
            return "I'm currently overloaded (Gemini quota exceeded). Please try again in a minute."
        except Exception as e:
            logger.error(f"Error generating answer with Gemini: {e}", exc_info=True)
<<<<<<< Updated upstream
            return f"I encountered an error while processing your question. Please try again."
=======
            return f"I encountered an error while processing your question: {str(e)}"
>>>>>>> Stashed changes
    
    elif LLM_PROVIDER == "openai":
        try:
            import openai
            response = openai.ChatCompletion.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context. If the answer cannot be found in the context, say you don't have enough information."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating answer with OpenAI: {e}")
            return f"I encountered an error while processing your question. Please try again."
    
    else:
        # Mock response for testing without API key
        logger.info("Using mock response (no LLM configured)")
        return f"""Based on the context provided, here's what I found regarding your question: "{query}"

[Mock Response - Configure GOOGLE_API_KEY or OPENAI_API_KEY in .env to get real AI responses]

Context summary: {context[:200]}...

To enable real AI responses:
1. Get a free API key from https://ai.google.dev/ (Gemini) or https://platform.openai.com/ (OpenAI)
2. Add it to your .env file as GOOGLE_API_KEY or OPENAI_API_KEY
3. Restart the application"""


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
            # Generate embedding using sentence-transformers
            embedding = embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Fall back to random embedding
            import random
            return [random.random() for _ in range(384)]
    else:
        # Mock embedding for testing (384 dimensions)
        logger.info("Using mock embedding (sentence-transformers not configured)")
        import random
        return [random.random() for _ in range(384)]
