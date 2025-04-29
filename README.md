# Todo-Tracker

pip install -r requirements.txt


## Run backend
-docker run -p 6379:6379 redis
-docker run --name myneo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=none neo4j:latest
-docker run -p 27017:27017 mongo
./src/backend> python app.py

## Run frontend
./src/frontend> python app.py