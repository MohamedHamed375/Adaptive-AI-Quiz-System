# Adaptive AI-Based Quiz System (Reinforcement Learning & RAG)

An intelligent, adaptive educational quiz platform designed to personalize learning experiences. Built as a core project for the **AIE 314 AI-Based Programming** course at **Galala University** (supervised by **Dr. Safaa El-Askary**). 

The platform dynamically adjusts question difficulty in real-time based on student performance using Reinforcement Learning, while utilizing Retrieval-Augmented Generation (RAG) to generate context-rich, non-repetitive questions from domain textbooks.

---

##  System Architecture & Core Mechanics

The system bridges two powerful paradigms to create an interactive learning loop:

1. **Reinforcement Learning (Q-Learning) Engine:**
   * **State Space:** Represents the student's current proficiency level and cumulative score.
   * **Action Space:** Dynamically shifts difficulty metrics (`Easy`, `Medium`, `Hard`).
   * **Reward Function:** Heavily rewards sustained accuracy on high-difficulty questions and penalizes consecutive failures, dynamically updating a custom $Q\text{-table}$ to optimize the personal learning path.

2. **Context-Aware Question Generation (RAG):**
   * Eliminates the need for massive, static hardcoded question banks.
   * Dynamically retrieves specific domain knowledge from course lecture documents and processes them through an LLM to generate unique, factually-grounded questions calibrated to the chosen difficulty layer.

3. **Explainable AI Reasoning:**
   * Includes comprehensive analytics for both instructors and students, showcasing why the RL agent adjusted difficulty levels alongside detailed answer feedback.

---

##  Tech Stack

* **Reinforcement Learning:** Custom Q-Learning Implementation ($Q\text{-table}$ persistence).
* **NLP & Generative AI:** Retrieval-Augmented Generation (RAG) pipeline.
* **Frontend/Backend Interface:** Python-driven environment.

---

##  Getting Started

1. Clone the repository:
   ```bash
   git clone [https://github.com/MohamedHamed375/Adaptive-AI-Quiz-System.git](https://github.com/MohamedHamed375/Adaptive-AI-Quiz-System.git)
