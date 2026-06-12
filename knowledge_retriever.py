import os

class KnowledgeRetriever:
    def __init__(self, knowledge_dir="knowledge"):
        self.knowledge_dir = knowledge_dir

    def retrieve(self, topic):
        """
        Simple retrieval:
        - Reads the file matching the topic
        - Returns its content as text
        """
        filename = f"{topic.lower()}.txt"
        path = os.path.join(self.knowledge_dir, filename)

        if not os.path.exists(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()

        return text if text else None
