from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

def add_task_to_mongo(text, date):
    task = {"text": text, "date": date, "done": False}
    result = db.tasks.insert_one(task)
    return result.inserted_id

def get_tasks_from_mongo(date=None):
    return list(db.tasks.find({"date": date}, {"_id": 0}))