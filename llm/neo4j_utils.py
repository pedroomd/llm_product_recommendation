# neo4j_utils.py
from neo4j import GraphDatabase
import os

class Neo4jDriverManager:
    _instance = None

    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER")
        self.password = os.getenv("NEO4J_PASSWORD")
        
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Neo4j driver: {e}")


    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def get_session(self):
        return self.driver.session()

    def close(self):
        self.driver.close()