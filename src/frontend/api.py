import requests
from config import BASE_URL

def create_user(username):
    """Получаем или создаем пользователя по имени"""
    try:
        response = requests.post(
            f"{BASE_URL}/register",
            json={"username": username}
        )
        return response.json() if response.ok else None
    except requests.exceptions.RequestException as e:
        print(f"User error: {e}")
        return None
    
def get_all_users():
    """Получение всех пользователей из API"""
    try:
        response = requests.get(f"{BASE_URL}/users")
        if response.ok:
            # Преобразуем данные в нужный формат
            users = response.json()
            if isinstance(users, list):
                return users
            elif isinstance(users, dict) and 'users' in users:
                return users['users']
            return []
        return None
    except requests.exceptions.RequestException as e:
        print(f"User error: {e}")
        return None


def add_friend_api(user_id, friend_id):
    """Добавление друга через API"""
    try:
        response = requests.post(
            f"{BASE_URL}/friends",
            json={"user_id": user_id, "friend_id": friend_id}
        )
        return response.ok
    except requests.exceptions.RequestException as e:
        print(f"Add friend error: {e}")
        return False


def get_tasks(username, date):
    """Получение задач пользователя на конкретную дату"""
    try:
        response = requests.get(
            f"{BASE_URL}/tasks",
            params={"username": username, "date": date}
        )
        return response.json() if response.ok else {}
    except requests.exceptions.RequestException as e:
        print(f"Get tasks error: {e}")
        return {}

def add_task(username, date, text):
    """Добавление новой задачи"""
    try:
        response = requests.post(
            f"{BASE_URL}/tasks",
            json={"username": username, "date": date, "text": text}
        )
        return response.ok
    except requests.exceptions.RequestException as e:
        print(f"Add task error: {e}")
        return False

def update_task(task_id, status):
    """Обновление статуса задачи"""
    try:
        response = requests.put(
            f"{BASE_URL}/tasks/{task_id}",
            json={"status": status}
        )
        return response.ok
    except requests.exceptions.RequestException as e:
        print(f"Update task error: {e}")
        return False

def delete_task(task_id):
    """Удаление задачи"""
    try:
        response = requests.delete(f"{BASE_URL}/tasks/{task_id}")
        return response.ok
    except requests.exceptions.RequestException as e:
        print(f"Delete task error: {e}")
        return False
    

def get_friends_api(user_id: str):
    """Получение списка друзей пользователя"""
    try:
        response = requests.get(
            f"{BASE_URL}/friends/{user_id}"
        )
        if response.ok:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        print(f"Get friends error: {e}")
        return None

def remove_friend_api(user_id: str, friend_id: str) -> bool:
    """Удаление друга"""
    try:
        response = requests.delete(
            f"{BASE_URL}/friends",
            json={
                "user_id": user_id,
                "friend_id": friend_id
            }
        )
        return response.ok
    except requests.exceptions.RequestException as e:
        print(f"Remove friend error: {e}")
        return False
    

def get_friend_recommendations_api(user_id: str):
    """Получение рекомендаций друзей с бэкенда"""
    try:
        response = requests.get(
            f"{BASE_URL}/friends/{user_id}/recommendations"
        )
        if response.ok:
            data = response.json()
            # Дополняем данные из MongoDB если нужно
            return data.get('recommendations', [])
        return None
    except requests.exceptions.RequestException as e:
        print(f"Get recommendations error: {e}")
        return None