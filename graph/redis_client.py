"""Shared Redis connection for all Cowork modules."""
import redis as redis_lib

_client = None

def get_redis():
    global _client
    if _client is None:
        _client = redis_lib.Redis(host='localhost', port=6379, decode_responses=True)
    return _client
