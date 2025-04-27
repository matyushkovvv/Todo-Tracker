import redis
from config import REDIS_URI

redis_db = redis.Redis.from_url(REDIS_URI)

def increment_task_counter(date):
    redis_db.incr(f"tasks:{date}")

def get_daily_task_count(date):
    count = redis_db.get(f"tasks:{date}")
    return int(count) if count else 0