from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_AUTH

driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

def add_friend(user_id, friend_id):
    with driver.session() as session:
        session.run("""
            MERGE (u1:User {id: $user_id})
            MERGE (u2:User {id: $friend_id})
            MERGE (u1)-[:FRIENDS_WITH]->(u2)
        """, user_id=user_id, friend_id=friend_id)

def get_friends(user_id):
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {id: $user_id})-[:FRIENDS_WITH]->(friend)
            RETURN friend.id
        """, user_id=user_id)
        return [record["friend.id"] for record in result]