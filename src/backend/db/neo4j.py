from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_AUTH

driver = GraphDatabase.driver(NEO4J_URI, auth=None)

def add_friend(user_id: str, friend_id: str) -> bool:
    """Создание двусторонней дружеской связи в Neo4j"""
    try:
        with driver.session() as session:
            # Создаем двунаправленную связь за один запрос
            result = session.run("""
                // Находим или создаем обоих пользователей
                MERGE (u1:User {id: $user_id})
                MERGE (u2:User {id: $friend_id})
                
                // Создаем связи в обоих направлениях
                MERGE (u1)-[r1:FRIENDS_WITH]->(u2)
                MERGE (u1)<-[r2:FRIENDS_WITH]-(u2)
                
                // Возвращаем результат для проверки
                RETURN r1, r2
            """, user_id=user_id, friend_id=friend_id)
            
            # Если есть обе связи, считаем операцию успешной
            return len(result.data()) > 0
    except Exception as e:
        print(f"Error creating friendship: {str(e)}")
        return False

def get_user_friends(user_id: str):
    """Получение списка ID друзей пользователя из Neo4j"""
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})-[:FRIENDS_WITH]->(friend:User)
                RETURN friend.id AS friend_id
            """, user_id=user_id)
            
            return [record["friend_id"] for record in result]
    except Exception as e:
        print(f"Error getting friends: {e}")
        return []