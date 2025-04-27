from datetime import datetime
from flask import Flask, request, jsonify
from db.mongo import add_task_to_mongo, get_tasks_from_mongo
from db.redis import increment_task_counter, get_daily_task_count
from db.neo4j import suggest_friends_from_neo4j

app = Flask(__name__)

# Эндпоинт: Добавление задачи
@app.route("/tasks", methods=["POST"])
def add_task():
    data = request.json
    date = data.get("date")
    
    task_id = add_task_to_mongo(data["text"], date)
    
    increment_task_counter(date)
    
    return jsonify({
        "status": "success",
        "task_id": str(task_id),
        "date": date
    }), 201

@app.route("/tasks", methods=["GET"])
def get_tasks():
    data = request.json
    date = data.get('date')

    tasks = get_tasks_from_mongo(date)
     
    return jsonify({"date": date, "tasks": tasks})

# Эндпоинт: Получение статистики задач
@app.route("/stats/daily", methods=["GET"])
def get_daily_stats():
    date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    count = get_daily_task_count(date)
    return jsonify({"date": date, "task_count": count})


# Эндпоинт: Получение рекомендаций друзей
@app.route("/users/<user_id>/suggested_friends", methods=["GET"])
def get_suggested_friends(user_id):
    friends = suggest_friends_from_neo4j(user_id)
    return jsonify({"user_id": user_id, "suggested_friends": friends})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)