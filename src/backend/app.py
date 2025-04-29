from flask import Flask, request, jsonify
from db.mongo import (register_user, get_user_id, 
                      add_task, update_task_status, 
                      get_user_tasks, get_users)

from db.neo4j import (add_friend, get_user_friends)

from bson.objectid import ObjectId
from datetime import datetime
from typing import Dict, List, Union

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register() -> Dict:
    """Регистрация нового пользователя"""
    # Получаем данные из формы (form-data) или JSON
    if request.is_json:
        username = request.json.get('username')
    else:
        username = request.form.get('username')
    
    if not username:
        return jsonify({"error": "Username is required"}), 400
    
    user_id = register_user(username)
    if not user_id:
        return jsonify({"error": "User registration failed"}), 400
        
    return jsonify({
        "user_id": user_id,
        "message": "User registered successfully"
    }), 201


@app.route('/friends', methods=['POST'])
def add_friend_api() -> Dict:
    """Добавление пользователя в друзья"""
    # Получаем данные из JSON или form-data
    if request.is_json:
        current_user_id = request.json.get('current_user_id')
        friend_id = request.json.get('friend_id')
    else:
        current_user_id = request.form.get('current_user_id')
        friend_id = request.form.get('friend_id')
    
    # Проверяем обязательные поля
    if not current_user_id or not friend_id:
        return jsonify({"error": "Both user IDs are required"}), 400
    
    # Проверяем, что пользователь не пытается добавить сам себя
    if current_user_id == friend_id:
        return jsonify({"error": "Cannot add yourself as friend"}), 400
    
    try:
        # Получаем всех пользователей один раз
        all_users = get_users()
        
        # Проверяем существование пользователей
        current_user = next((u for u in all_users if u["_id"] == current_user_id), None)
        friend_user = next((u for u in all_users if u["_id"] == friend_id), None)
        
        if not current_user or not friend_user:
            return jsonify({"error": "One or both users not found"}), 404
        
        # Добавляем связь в Neo4j
        success = add_friend(current_user_id, friend_id)
        
        if not success:
            return jsonify({"error": "Failed to create friend relation"}), 500
            
        return jsonify({
            "message": "Friend added successfully",
            "current_user_id": current_user_id,
            "friend_id": friend_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/friends/<user_id>', methods=['GET'])
def get_friends(user_id: str) -> Dict:
    """Получение списка друзей пользователя"""
    try:
        # Получаем ID друзей из Neo4j
        friend_ids = get_user_friends(user_id)
        
        if not friend_ids:
            return jsonify({"friends": [], "message": "No friends found"}), 200
        
        # Получаем данные друзей из MongoDB
        friends_data = []
        users = get_users()
        for friend_id in friend_ids:
            friend_user = next((u for u in users if u["_id"] == friend_id), None)
            if friend_user:
                friends_data.append({
                    "user_id": friend_user["_id"],
                    "username": friend_user["username"]
                })
        
        return jsonify({
            "friends": friends_data,
            "count": len(friends_data)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/users', methods=['GET'])
def get_all_users():
    try:
        users = get_users()         
        return jsonify({
            "users": users,
            "count": len(users)
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tasks', methods=['POST'])
def create_task() -> Dict:
    """Создание новой задачи"""

    if request.is_json:
        data = request.json
    else:
        data = request.form
    
    username = data.get('username')
    text = data.get('text')
    date = data.get('date')
    
    if not all([username, text, date]):
        return jsonify({"error": "All fields (username, text, date) are required"}), 400
    
    # Валидация даты
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    user_id = get_user_id(username)
    if not user_id:
        return jsonify({"error": "User not found"}), 404
    
    task_id = add_task(user_id, text, date)
    if not task_id:
        return jsonify({"error": "Failed to create task"}), 400
        
    return jsonify({
        "task_id": str(task_id),
        "message": "Task created successfully"
    }), 201

@app.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id: str) -> Dict:
    """Обновление статуса задачи"""
    if not ObjectId.is_valid(task_id):
        return jsonify({"error": "Invalid task ID format"}), 400
    
    if request.is_json:
        data = request.json
    else:
        data = request.form
    
    status = data.get('status')
    
    if status is None:
        return jsonify({"error": "Status is required (true/false)"}), 400
    
    try:
        success = update_task_status(task_id, bool(status))
        if not success:
            return jsonify({"error": "Task not found or not modified"}), 404
            
        return jsonify({"message": "Task updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tasks', methods=['GET'])
def get_tasks() -> Dict:
    """Получение задач пользователя"""

    username = request.args.get('username')
    date = request.args.get('date')
    
    if not username:
        return jsonify({"error": "Username is required"}), 400
    if not date:
        return jsonify({"error": "Date is required (YYYY-MM-DD)"}), 400
    
    
    user_id = get_user_id(username)
    if not user_id:
        return jsonify({"error": "User not found"}), 404
    
    try:
        tasks = get_user_tasks(user_id, date)            
        return jsonify({
            "tasks": tasks,
            "count": len(tasks)
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)