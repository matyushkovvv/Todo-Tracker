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
    
def remove_friend_relation(user_id: str, friend_id: str) -> bool:
    """Удаление дружеской связи между пользователями (альтернативная версия)"""
    try:
        with driver.session() as session:
            # Удаляем связи без возврата количества
            session.run("""
                MATCH (u1:User {id: $user_id})-[r:FRIENDS_WITH]-(u2:User {id: $friend_id})
                DELETE r
            """, user_id=user_id, friend_id=friend_id)
            return True
    except Exception as e:
        print(f"Error removing friend relation: {e}")
        return False
    

def get_friend_recommendations(user_id: str, limit: int = 5):
    """Получение рекомендаций друзей на основе общих друзей"""
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (me:User {id: $user_id})-[:FRIENDS_WITH]->(common:User)-[:FRIENDS_WITH]->(recommended:User)
                WHERE NOT (me)-[:FRIENDS_WITH]->(recommended) AND me <> recommended
                WITH recommended, count(common) AS common_friends
                RETURN recommended.id AS user_id, common_friends
                ORDER BY common_friends DESC
                LIMIT $limit
            """, user_id=user_id, limit=limit)
            
            return [{"user_id": record["user_id"], "common_friends": record["common_friends"]} 
                   for record in result]
    except Exception as e:
        print(f"Error getting friend recommendations: {e}")
        return []