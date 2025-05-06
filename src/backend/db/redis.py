import redis
from config import REDIS_URI

redis_db = redis.Redis.from_url(REDIS_URI)

def increment_stat(key: str):
    redis_db.incr(key)

def get_stat(key: str) -> int:
    return int(redis_db.get(key) or 0)

def get_all_stats() -> dict:
    keys = redis_db.keys('*')
    return {k: redis_db.get(k) for k in keys}
