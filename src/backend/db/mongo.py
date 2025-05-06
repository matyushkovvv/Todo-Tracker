from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
from config import MONGO_URI, MONGO_DB
from typing import Optional, Dict, List, Union

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

users_collection = db.users
tasks_collection = db.tasks
workspaces_collection = db.workspaces


def register_user(username: str):
    existing_user = users_collection.find_one({"username": username})
    if existing_user:
        return str(existing_user["_id"])
    result = users_collection.insert_one({"username": username})
    return str(result.inserted_id)


def delete_task_from_db(workspace_id: str, task_id: str) -> bool:
    """Удаляет задачу по ID и проверяет принадлежность рабочей области"""
    try:
        result = tasks_collection.delete_one({
            "_id": ObjectId(task_id),
            "workspace_id": ObjectId(workspace_id)
        })
        return result.deleted_count > 0
    except Exception:
        return False


def get_user_id(username: str):
    user = users_collection.find_one({"username": username})
    return str(user["_id"]) if user else None


def get_users():
    return [{"_id": str(u["_id"]), "username": u["username"]} for u in users_collection.find()]


def get_user_by_id(user_id: str):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    return {"_id": str(user["_id"]), "username": user["username"]} if user else None


def create_workspace(name: str, creator_id: str):
    result = workspaces_collection.insert_one({
        "name": name,
        "members": [
            {"user_id": creator_id, "role": "admin"}
        ]
    })
    return str(result.inserted_id)


def get_workspace_by_id(workspace_id: str):
    return workspaces_collection.find_one({"_id": ObjectId(workspace_id)})


def get_user_role_in_workspace(workspace_id: str, user_id: str):
    workspace = get_workspace_by_id(workspace_id)
    if not workspace:
        return None
    for member in workspace["members"]:
        if member["user_id"] == user_id:
            return member["role"]
    return None


def get_workspace_members(workspace_id: str):
    workspace = get_workspace_by_id(workspace_id)
    if not workspace:
        return []
    members_info = []
    for m in workspace["members"]:
        user = get_user_by_id(m["user_id"])
        if user:
            members_info.append({
                "user_id": user["_id"],
                "username": user["username"],
                "role": m["role"]
            })
    return members_info


def add_member_to_workspace(workspace_id: str, user_id: str, role: str):
    workspace = get_workspace_by_id(workspace_id)
    if not workspace:
        return False
    if any(member["user_id"] == user_id for member in workspace["members"]):
        return False
    result = workspaces_collection.update_one(
        {"_id": ObjectId(workspace_id)},
        {"$push": {"members": {"user_id": user_id, "role": role}}}
    )
    return result.modified_count > 0


def remove_member_from_workspace(workspace_id: str, user_id: str):
    result = workspaces_collection.update_one(
        {"_id": ObjectId(workspace_id)},
        {"$pull": {"members": {"user_id": user_id}}}
    )
    return result.modified_count > 0


def create_task(workspace_id, text, date):
    task = {
        "workspace_id": ObjectId(workspace_id),
        "text": text,
        "date": date,
        "is_done": False,
        "created_at": datetime.utcnow()
    }
    result = tasks_collection.insert_one(task)
    return str(result.inserted_id)


def update_task_status_by_id(task_id: str, is_done: bool) -> bool:
    try:
        obj_id = ObjectId(task_id)
    except Exception:
        return False  # Невалидный формат ID

    result = tasks_collection.update_one(
        {"_id": obj_id},
        {"$set": {"is_done": is_done}}
    )
    return result.modified_count > 0



def get_tasks_by_workspace_and_date(workspace_id, date):
    tasks = tasks_collection.find({
        "workspace_id": ObjectId(workspace_id),
        "date": date
    })
    return [
        {
            "task_id": str(task["_id"]),
            "text": task["text"],
            "date": task["date"],
            "is_done": task["is_done"]
        }
        for task in tasks
    ]

def get_user_workspaces(user_id: str) -> List[Dict]:
    workspaces = workspaces_collection.find({
        "members": {
            "$elemMatch": {
                "user_id": user_id
            }
        }
    })
    return [
        {
            "_id": str(ws["_id"]),
            "name": ws["name"],
            "members": ws["members"]
        }
        for ws in workspaces
    ]