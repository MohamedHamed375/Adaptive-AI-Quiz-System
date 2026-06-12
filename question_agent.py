import random
import uuid
import os
from question_templates import TEMPLATES


class QuestionAgent:
    def __init__(self):
        self.letters = ["A", "B", "C", "D"]
        self.knowledge_path = os.path.join(
            os.path.dirname(__file__),
            "knowledge"
        )

    def retrieve_context(self, topic):
        """
        Simple RAG retrieval:
        Reads a topic-specific knowledge file
        and returns ONE relevant sentence
        """
        fname = topic.lower() + ".txt"
        path = os.path.join(self.knowledge_path, fname)

        if not os.path.exists(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

        return random.choice(lines) if lines else None

    def generate(self, topic, difficulty):
        # ========= 1) RAG Retrieval =========
        context = self.retrieve_context(topic)

        # ========= 2) Template Selection =========
        pool = TEMPLATES[topic][difficulty]
        temp = random.choice(pool)

        # ========= 3) Question Construction =========
        if context:
            question_text = (
                f"Based on the following concept:\n"
                f"\"{context}\"\n\n"
                f"{temp['question']}"
            )
        else:
            question_text = temp["question"]

        # ========= 4) Options =========
        options = temp["wrong"] + [temp["correct"]]
        random.shuffle(options)

        correct_letter = self.letters[options.index(temp["correct"])]

        qid = uuid.uuid4().hex[:8]

        return {
            "question_id": qid,
            "question": question_text,
            "A": options[0],
            "B": options[1],
            "C": options[2],
            "D": options[3],
            "correct": correct_letter,
            "difficulty": difficulty,
            "topic": topic,
            "context": context 
        }
