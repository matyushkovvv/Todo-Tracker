from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_AUTH

driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

def suggest_friends_from_neo4j(user_id):
    with driver.session() as session:
        # Если в графе нет данных, возвращаем mock
        result = session.run(
            "MATCH (u:User {id: $user_id})-[:FRIENDS_WITH]-(f) RETURN f.name LIMIT 3",
            user_id=user_id
        )
        friends = [record["f.name"] for record in result]
        
        if not friends:
            return ["Аня", "Борис", "Сергей"]  # Mock-данные
        return friends