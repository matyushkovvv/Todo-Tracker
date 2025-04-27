from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB
from auth import hash_password, check_password

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

def register_user(username, nickname, password):
    if db.users.find_one({"$or": [{"username": username}, {"nickname": nickname}]}):
        return None
    user_id = db.users.insert_one({
        "username": username,
        "nickname": nickname,
        "password": hash_password(password)
    }).inserted_id
    return str(user_id)

def authenticate_user(nickname, password):
    user = db.users.find_one({"nickname": nickname})
    if user and check_password(user["password"], password):
        return str(user["_id"])
    return None

def add_task(user_id, text, date):
    task = {
        "user_id": user_id,
        "text": text,
        "date": date,
        "done": False
    }
    return db.tasks.insert_one(task).inserted_id

def get_user_tasks(user_id, date):
    return list(db.tasks.find({"user_id": user_id, "date": date}, {"_id": 0}))