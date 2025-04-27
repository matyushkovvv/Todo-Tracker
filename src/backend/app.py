from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth
from db.mongo import register_user, authenticate_user, add_task, get_user_tasks

app = Flask(__name__)
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(nickname, password):
    return authenticate_user(nickname, password)

# Регистрация
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    user_id = register_user(data['username'], data['nickname'], data['password'])
    if not user_id:
        return jsonify({"error": "User already exists"}), 400
    return jsonify({"user_id": user_id}), 201

# Добавление задачи (требует авторизации)
@app.route('/tasks', methods=['POST'])
@auth.login_required
def create_task():
    user_id = auth.current_user()
    task_id = add_task(user_id, request.json['text'], request.json['date'])
    return jsonify({"task_id": str(task_id)}), 201

# Получение задач (требует авторизации)
@app.route('/tasks', methods=['GET'])
@auth.login_required
def get_tasks():
    user_id = auth.current_user()
    tasks = get_user_tasks(user_id, request.json['date'])
    return jsonify({"tasks": tasks})

if __name__ == '__main__':
    app.run(debug=True)