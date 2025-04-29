from pymongo import MongoClient
from bson.objectid import ObjectId
from config import MONGO_URI, MONGO_DB
from typing import Optional, Dict, List

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

def register_user(username: str) -> Optional[str]:
    """Регистрирует нового пользователя или возвращает существующего"""
    if not username or not isinstance(username, str):
        return None
    
    existing_user = db.users.find_one({"username": username})
    if existing_user:
        return str(existing_user["_id"])
    
    user_data = {
        "username": username,
    }
    
    result = db.users.insert_one(user_data)
    return str(result.inserted_id)

def get_users(query=None):
    if query is None:
        query = {}

    users = []
    for user in db.users.find(query):
        user["_id"] = str(user["_id"])
        users.append(user)
    return users

def get_user_id(username: str) -> Optional[str]:
    """Возвращает ID пользователя по имени"""
    if not username:
        return None
        
    user = db.users.find_one({"username": username})
    return str(user["_id"]) if user else None

def add_task(user_id: str, text: str, date: str) -> Optional[str]:
    """Добавляет новую задачу"""
    if not all([user_id, text, date]):
        return None
        
    task_data = {
        "user_id": user_id,
        "text": text,
        "date": date,
        "status": False
    }
    
    try:
        result = db.tasks.insert_one(task_data)
        return str(result.inserted_id)
    except Exception:
        return None

def update_task_status(task_id: str, status: bool) -> bool:
    """Обновляет статус задачи"""
    if not task_id:
        return False
        
    try:
        result = db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"status": status}}
        )
        return result.modified_count > 0
    except Exception:
        return False

def get_user_tasks(user_id: str, date: str) -> List[Dict]:
    """Возвращает задачи пользователя на указанную дату"""
    if not all([user_id, date]):
        return []
        
    try:
        tasks = []
        for task in db.tasks.find({"user_id": user_id, "date": date}):
            task["task_id"] = str(task.pop("_id"))
            tasks.append(task)
        return tasks
    except Exception:
        return []