import redis
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

def get_redis_client():
    """Get Redis client for caching"""
    try:
        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
        # Test connection
        client.ping()
        return client
    except redis.ConnectionError as e:
        print(f"Warning: Could not connect to Redis at {REDIS_HOST}:{REDIS_PORT}: {e}")
        return None
