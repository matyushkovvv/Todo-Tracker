from flask import Flask, request, jsonify
from datetime import datetime
from db.redis import get_all_stats, get_stat, increment_stat
from db.mongo import (
    delete_task_from_db, get_tasks_by_workspace_and_date, get_user_workspaces, register_user, get_users,
    create_workspace, get_user_role_in_workspace,
    add_member_to_workspace, remove_member_from_workspace,
    get_workspace_members,
    create_task, update_task_status_by_id
)
from db.neo4j import (
    add_friend, get_user_friends, remove_friend_relation,
    get_friend_recommendations
)

app = Flask(__name__)


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

@app.route('/users/<user_id>/workspaces', methods=['GET'])
def list_user_workspaces(user_id):
    workspaces = get_user_workspaces(user_id)
    return jsonify({"workspaces": workspaces, "count": len(workspaces)}), 200


@app.route('/stats/increment', methods=['POST'])
def increment_stat_route():
    """Увеличивает счетчик статистики"""
    data = request.get_json()
    if not data or 'key' not in data:
        return jsonify({"error": "Key is required"}), 400
    
    try:
        increment_stat(data['key'])
        return jsonify({"status": "success", "key": data['key']}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats/get', methods=['GET'])
def get_stat_route():
    """Получает значение конкретной статистики"""
    key = request.args.get('key')
    if not key:
        return jsonify({"error": "Key parameter is required"}), 400
    
    try:
        value = get_stat(key)
        return jsonify({"key": key, "value": value}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats/workspace/<workspace_id>', methods=['GET'])
def get_workspace_stats_route(workspace_id):
    """Получает всю статистику для конкретной рабочей области"""
    try:
        # Ищем все ключи, начинающиеся с ws:{workspace_id}:
        pattern = f"ws:{workspace_id}:*"
        stats = {}
        
        # Используем ваш существующий метод get_all_stats()
        all_stats = get_all_stats()
        
        # Фильтруем только нужные ключи
        for key_bytes, value_bytes in all_stats.items():
            key = key_bytes.decode('utf-8')
            if key.startswith(f"ws:{workspace_id}:"):
                stat_name = key.split(':')[-1]  # Извлекаем название метрики
                stats[stat_name] = int(value_bytes.decode('utf-8'))
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats/all', methods=['GET'])
def get_all_stats_route():
    """Получает всю статистику (административный)"""
    try:
        # Используем ваш существующий метод
        stats = get_all_stats()
        # Декодируем бинарные данные из Redis
        decoded_stats = {k.decode('utf-8'): int(v.decode('utf-8')) 
                        for k, v in stats.items()}
        return jsonify(decoded_stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/register', methods=['POST'])
def register():
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


@app.route('/workspaces/<workspace_id>/tasks/<task_id>', methods=['DELETE'])
def delete_task_route(workspace_id, task_id):
    """Удаляет задачу из рабочей области"""
    data = request.get_json()
    user_id = data.get("user_id")
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    # Проверяем права (только admin может удалять)
    if get_user_role_in_workspace(workspace_id, user_id) != "admin":
        return jsonify({"error": "Only admin can delete tasks"}), 403
    
    if delete_task_from_db(workspace_id, task_id):
        return jsonify({"message": "Task deleted"}), 200
    else:
        return jsonify({"error": "Task not found"}), 404

@app.route('/workspaces', methods=['POST'])
def create_workspace_route():
    data = request.get_json()
    name = data.get("name")
    user_id = data.get("user_id")

    if not all([name, user_id]):
        return jsonify({"error": "name and user_id required"}), 400

    workspace_id = create_workspace(name, user_id)
    return jsonify({"workspace_id": workspace_id, "message": "Workspace created"}), 201


@app.route('/workspaces/<workspace_id>/members', methods=['GET'])
def list_workspace_members(workspace_id):
    members = get_workspace_members(workspace_id)
    return jsonify({"members": members, "count": len(members)}), 200


@app.route('/workspaces/<workspace_id>/members', methods=['POST'])
def add_member(workspace_id):
    data = request.get_json()
    admin_id = data.get("admin_id")
    user_id = data.get("user_id")
    role = data.get("role")

    if not all([admin_id, user_id, role]):
        return jsonify({"error": "admin_id, user_id and role are required"}), 400

    if get_user_role_in_workspace(workspace_id, admin_id) != "admin":
        return jsonify({"error": "Only admin can add members"}), 403

    success = add_member_to_workspace(workspace_id, user_id, role)
    if not success:
        return jsonify({"error": "User already in workspace"}), 400

    return jsonify({"message": "Member added"}), 200


@app.route('/workspaces/<workspace_id>/members', methods=['DELETE'])
def remove_member(workspace_id):
    data = request.get_json()
    requester_id = data.get("requester_id")
    target_id = data.get("target_id")

    if get_user_role_in_workspace(workspace_id, requester_id) != "admin":
        return jsonify({"error": "Only admin can remove members"}), 403

    if requester_id == target_id:
        return jsonify({"error": "Admin cannot remove themselves"}), 400

    success = remove_member_from_workspace(workspace_id, target_id)
    if not success:
        return jsonify({"error": "User not found in workspace"}), 404

    return jsonify({"message": "Member removed"}), 200


@app.route('/workspaces/<workspace_id>/tasks', methods=['POST'])
def create_task_route(workspace_id):
    data = request.get_json()
    user_id = data.get("user_id")
    text = data.get("text")
    date = data.get("date")

    if not all([user_id, text, date]):
        return jsonify({"error": "user_id, text and date are required"}), 400

    if get_user_role_in_workspace(workspace_id, user_id) not in ["admin", "editor"]:
        return jsonify({"error": "No permission to add task"}), 403

    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    task_id = create_task(workspace_id, text, date)
    return jsonify({"task_id": task_id, "message": "Task created"}), 201


@app.route('/workspaces/<workspace_id>/tasks/<task_id>', methods=['PUT'])
def update_task_status(workspace_id, task_id):
    data = request.get_json()
    user_id = data.get("user_id")
    status = data.get("is_done")

    if not all([user_id, status is not None]):
        return jsonify({"error": "user_id and status required"}), 400

    if get_user_role_in_workspace(workspace_id, user_id) not in ["admin", "editor"]:
        return jsonify({"error": "No permission to update task"}), 403

    updated = update_task_status_by_id(task_id, bool(status))
    if not updated:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"message": "Task updated"}), 200


@app.route('/workspaces/<workspace_id>/tasks', methods=['GET'])
def get_tasks(workspace_id):
    date = request.args.get("date")

    if not date:
        return jsonify({"error": "date required"}), 400

    tasks = get_tasks_by_workspace_and_date(workspace_id, date)
    return jsonify({"tasks": tasks, "count": len(tasks)}), 200


@app.route('/friends', methods=['POST'])
def add_friend_route():
    data = request.get_json()
    user_id = data.get("user_id")
    friend_id = data.get("friend_id")

    if not all([user_id, friend_id]):
        return jsonify({"error": "user_id and friend_id are required"}), 400

    if user_id == friend_id:
        return jsonify({"error": "Cannot add yourself as friend"}), 400

    success = add_friend(user_id, friend_id)
    return (jsonify({"message": "Friend added"}), 200) if success else (jsonify({"error": "Failed to add"}), 500)

@app.route('/friends', methods=['DELETE'])
def remove_friend_route():
    data = request.get_json()
    user_id = data.get("user_id")
    friend_id = data.get("friend_id")

    if not all([user_id, friend_id]):
        return jsonify({"error": "user_id and friend_id are required"}), 400

    success = remove_friend_relation(user_id, friend_id)
    return (jsonify({"message": "Friend removed"}), 200) if success else (jsonify({"error": "Failed to remove"}), 500)


@app.route('/friends/<user_id>', methods=['GET'])
def list_friends(user_id):
    friends = get_user_friends(user_id)
    users = get_users()
    friends_data = [
        {"user_id": fid, "username": next((u["username"] for u in users if u["_id"] == fid), "Unknown")}
        for fid in friends
    ]
    return jsonify({"friends": friends_data, "count": len(friends_data)}), 200


@app.route('/friends/<user_id>/recommendations', methods=['GET'])
def recommend_friends(user_id):
    recommendations = get_friend_recommendations(user_id)
    return jsonify({"recommendations": recommendations, "count": len(recommendations)}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
