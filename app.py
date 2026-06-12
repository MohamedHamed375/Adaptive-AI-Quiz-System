from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import random
from q_agent import QAgent
from flask import redirect
from question_agent import QuestionAgent
question_agent = QuestionAgent()


app = Flask(__name__)



LEVELS = ["Easy", "Medium", "Hard"]
TOPICS = ["RL", "GameTheory", "GAN"]

# =========================================================
# 2) AGENTS: Q-table per topic (strongest academic feature)
# =========================================================
agents = {
    t: QAgent(alpha=0.12, gamma=0.9, epsilon=1.0, epsilon_min=0.05, epsilon_decay=0.995)
    for t in TOPICS
}



# =========================================================
# 4) SESSION STATE (single-user demo)
# =========================================================
session = {
    "active": False,
    "n_questions": 10,
    "idx": 0,
    "state": 0,               # student level state: 0..2
    "correct": 0,

    # logs
    "history": [],            # detailed per-question log
    "level_trace": [],
    "acc_trace": [],
    "difficulty_actions": [],
    "reward_trace": [],
    "epsilon_trace": [],
    "topic_trace": [],
    "reasoning_log": [],


    # control
    "current": None,          # current question on server
    "used_question_ids": set(),
    "selected_topics": TOPICS[:],

    # stop condition info
    "stop_reason": None
}

# =========================================================
# 5) RESET SESSION
# =========================================================
def reset_session(n_questions: int, selected_topics=None):
    session["active"] = True
    session["n_questions"] = int(n_questions)
    session["idx"] = 0
    session["state"] = 0
    session["correct"] = 0

    session["history"] = []
    session["level_trace"] = []
    session["acc_trace"] = []
    session["difficulty_actions"] = []
    session["reward_trace"] = []
    session["epsilon_trace"] = []
    session["topic_trace"] = []
    session["reasoning_log"] = []


    session["current"] = None
    session["used_question_ids"] = set()
    session["stop_reason"] = None

    if selected_topics and isinstance(selected_topics, list) and len(selected_topics) > 0:
        # sanitize topics
        clean = [t for t in selected_topics if t in TOPICS]
        session["selected_topics"] = clean if len(clean) > 0 else TOPICS[:]
    else:
        session["selected_topics"] = TOPICS[:]

# =========================================================
# 6) REWARD FUNCTION (weighted by difficulty + level transitions)
# =========================================================
diff_reward = {0: 1.0, 1: 1.5, 2: 2.0}   # correct reward weight
diff_penalty = {0: 2.0, 1: 1.5, 2: 1.0}  # wrong penalty weight

def compute_reward(is_correct: bool, action: int, old_state: int, new_state: int):
    # base
    r = diff_reward[action] if is_correct else -diff_penalty[action]
    # transition shaping
    if new_state > old_state:
        r += 1.0
    elif new_state < old_state:
        r -= 1.0
    return float(r)

# =========================================================
# 7) STOP CONDITIONS (mastery / fatigue / limit)
# =========================================================
def check_stop_condition():
    """
    Returns:
      None if continue
      "mastery" if mastery reached
      "fatigue" if fatigue detected
      "limit" if question limit reached
    """
    # 1) limit
    if session["idx"] >= session["n_questions"]:
        return "limit"

    # 2) mastery: last 5 accuracy average > 0.85 AND state mostly Hard
    if len(session["acc_trace"]) >= 5:
        last5 = session["acc_trace"][-5:]
        if float(np.mean(last5)) > 0.85:
            # add a small extra check: last 5 states contain >=3 Hard
            last5_states = session["level_trace"][-5:]
            hard_count = sum(1 for s in last5_states if s == 2)
            if hard_count >= 3:
                return "mastery"

    # 3) fatigue: last 3 rewards are negative (student struggling)
    if len(session["reward_trace"]) >= 3:
        last3 = session["reward_trace"][-3:]
        if all(r < 0 for r in last3):
            return "fatigue"

    return None

# =========================================================
# 8) METRICS (overall + per topic)
# =========================================================
def compute_overall_metrics():
    n = max(1, session["idx"])
    acc = session["correct"] / n

    actions = session["difficulty_actions"]
    avg_diff = float(np.mean(actions)) if actions else 0.0

    time_in = {
        "Easy": int(sum(1 for s in session["level_trace"] if s == 0)),
        "Medium": int(sum(1 for s in session["level_trace"] if s == 1)),
        "Hard": int(sum(1 for s in session["level_trace"] if s == 2)),
    }
    time_in_pct = {
        k: round(v / max(1, len(session["level_trace"])) * 100, 2)
        for k, v in time_in.items()
    }

    # max hard streak
    max_streak = 0
    streak = 0
    for s in session["level_trace"]:
        if s == 2:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0

    # recovery count: down then up
    recoveries = 0
    went_down = False
    for i in range(1, len(session["level_trace"])):
        if session["level_trace"][i] < session["level_trace"][i - 1]:
            went_down = True
        if went_down and session["level_trace"][i] > session["level_trace"][i - 1]:
            recoveries += 1
            went_down = False

    return {
        "final_accuracy": round(acc, 4),
        "avg_chosen_difficulty": round(avg_diff, 3),
        "time_in_levels_pct": time_in_pct,
        "max_hard_streak": int(max_streak),
        "recovery_count": int(recoveries),
    }

def compute_per_topic_metrics():
    """
    Builds per-topic metrics from session["history"].
    history rows include:
      topic, action, is_correct, reward, state_before/after, etc.
    """
    per = {}
    for h in session["history"]:
        t = h["topic"]
        if t not in per:
            per[t] = {
                "total": 0,
                "correct": 0,
                "actions": [],
                "rewards": [],
                "states_before": [],
                "states_after": []
            }
        per[t]["total"] += 1
        per[t]["correct"] += int(h["is_correct"])
        per[t]["actions"].append(h["action"])
        per[t]["rewards"].append(h["reward"])
        per[t]["states_before"].append(h["state_before_num"])
        per[t]["states_after"].append(h["state_after_num"])

    # finalize
    out = {}
    for t, d in per.items():
        total = max(1, d["total"])
        out[t] = {
            "total": int(d["total"]),
            "accuracy": round(d["correct"] / total, 4),
            "avg_difficulty": round(float(np.mean(d["actions"])) if d["actions"] else 0.0, 3),
            "avg_reward": round(float(np.mean(d["rewards"])) if d["rewards"] else 0.0, 3),
            "time_in_hard_pct": round(
                100 * (sum(1 for s in d["states_before"] if s == 2) / max(1, len(d["states_before"]))),
                2
            ),
        }
    return out

# =========================================================
# 9) AI FEEDBACK (textual report)
# =========================================================
def generate_ai_feedback(overall, per_topic):
    lines = []

    # overall summary
    acc = overall.get("final_accuracy", 0.0)
    avgd = overall.get("avg_chosen_difficulty", 0.0)
    hard_pct = overall.get("time_in_levels_pct", {}).get("Hard", 0.0)

    if acc >= 0.85:
        lines.append("Overall performance is excellent with high accuracy.")
    elif acc >= 0.65:
        lines.append("Overall performance is good, with room for improvement.")
    else:
        lines.append("Overall performance indicates the student needs more practice.")

    lines.append(f"The system applied adaptive difficulty (avg difficulty ≈ {avgd}).")
    lines.append(f"Time spent in Hard level ≈ {hard_pct}%.")

    # topic summary
    if per_topic:
        best_t = max(per_topic.items(), key=lambda x: x[1]["accuracy"])[0]
        worst_t = min(per_topic.items(), key=lambda x: x[1]["accuracy"])[0]
        lines.append(f"Best topic: {best_t}.")
        lines.append(f"Needs more practice: {worst_t}.")

        # recommendations
        for t, m in per_topic.items():
            if m["accuracy"] >= 0.8:
                lines.append(f"✅ Strong understanding in {t}.")
            elif m["accuracy"] <= 0.5:
                lines.append(f"⚠️ Weak understanding in {t}. Consider revising core concepts.")
            else:
                lines.append(f"➖ Moderate understanding in {t}. More practice recommended.")
    else:
        lines.append("No topic-level breakdown available (no questions answered).")

    # stop reason
    if session.get("stop_reason"):
        sr = session["stop_reason"]
        if sr == "mastery":
            lines.append("Session ended early due to mastery condition.")
        elif sr == "fatigue":
            lines.append("Session ended early due to fatigue (multiple recent wrong answers).")
        elif sr == "limit":
            lines.append("Session ended after reaching the configured question limit.")

    return " ".join(lines)


@app.before_request
def ensure_session_started():
    if request.endpoint in ["quiz_page", "api_next"]:
        if not session.get("active", False):
            reset_session(10)

# =========================================================
# 10) PAGES (templates)
# =========================================================
@app.route("/")
def setup_page():
    return render_template("setup.html")

@app.route("/quiz")
def quiz_page():
    if not session.get("active", False):
        return redirect("/")
    return render_template("quiz.html")


@app.route("/results")
def results_page():
    return render_template("results.html")

# =========================================================
# 11) API: START SESSION (optionally with selected topics)
# =========================================================
@app.route("/api/start", methods=["POST"])
def api_start():
    data = request.get_json() or {}
    n_questions = int(data.get("n_questions", 10))
    n_questions = max(5, min(50, n_questions))

    selected_topics = data.get("topics", None)  # e.g. ["RL","GAN"]
    reset_session(n_questions, selected_topics=selected_topics)

    return jsonify({"ok": True, "n_questions": n_questions, "topics": session["selected_topics"]})

# =========================================================
# 12) API: GET NEXT QUESTION
# =========================================================
@app.route("/api/next", methods=["GET"])
def api_next():
    if not session.get("active", False):
        return jsonify({"done": True}), 200

    # stop condition already triggered
    if session.get("stop_reason") is not None:
        return jsonify({"done": True, "stop_reason": session["stop_reason"]}), 200

    # reached question limit
    if session["idx"] >= session["n_questions"]:
        session["stop_reason"] = "limit"
        return jsonify({"done": True, "stop_reason": "limit"}), 200

    # =========================
    # 1) Choose topic
    # =========================
    topic = random.choice(session["selected_topics"])

    # =========================
    # 2) RL Agent chooses difficulty
    # =========================
    agent = agents[topic]
    state = session["state"]
    action = agent.choose_action(state)
    diff = LEVELS[action]

    # =========================
    # 3) Generate question (RAG + Templates)
    # =========================
    q = question_agent.generate(topic, diff)

    # =========================
    # 4) TOOL REASONING LOG
    # =========================
    reasoning = {
        "step": session["idx"] + 1,
        "topic": topic,
        "state_before": LEVELS[state],
        "chosen_difficulty": diff,
        "tool_used": "QuestionGenerator + RAG",
        "retrieved_context": q.get("context"),
        "decision_reason": f"Difficulty chosen using Q-learning from state {LEVELS[state]}"
    }
    session["reasoning_log"].append(reasoning)

    # =========================
    # 5) Store current question
    # =========================
    session["used_question_ids"].add(q["question_id"])

    session["current"] = {
        "question_id": q["question_id"],
        "topic": topic,
        "action": action,
        "state_before": state,
        "correct": q["correct"],
        "difficulty": diff
    }

    print(f"[DEBUG NEXT] idx={session['idx']} topic={topic} diff={diff}")

    # =========================
    # 6) Send to frontend
    # =========================
    return jsonify({
        "done": False,
        "question_number": session["idx"] + 1,
        "total_questions": session["n_questions"],
        "student_level": LEVELS[state],
        "ai_chosen_difficulty": diff,
        "topic": topic,
        "question_id": q["question_id"],
        "question": q["question"],
        "A": q["A"],
        "B": q["B"],
        "C": q["C"],
        "D": q["D"],
        "epsilon": round(agent.epsilon, 4),
        "retrieved_knowledge": q.get("context")
    })



# =========================================================
# 13) API: SUBMIT ANSWER
# =========================================================
@app.route("/api/submit", methods=["POST"])
def api_submit():
    if not session["active"] or not session["current"]:
        return jsonify({"error": "No active question"}), 400

    data = request.get_json() or {}
    user_ans = (data.get("answer", "") or "").strip().upper()

    cur = session["current"]
    topic = cur["topic"]
    agent = agents[topic]  # topic-specific agent

    correct_opt = cur["correct"]
    is_correct = (user_ans == correct_opt)

    old_state = cur["state_before"]
    action = cur["action"]

    # -------------------------
    # State transition
    # -------------------------
    new_state = old_state
    if is_correct and old_state < 2:
        new_state += 1
    elif (not is_correct) and old_state > 0:
        new_state -= 1

    # -------------------------
    # Reward
    # -------------------------
    r = compute_reward(is_correct, action, old_state, new_state)

    # -------------------------
    # Update agent
    # -------------------------
    agent.update(old_state, action, r, new_state)

    # -------------------------
    # Traces (for charts)
    # -------------------------
    session["level_trace"].append(old_state)
    session["acc_trace"].append(1 if is_correct else 0)
    session["difficulty_actions"].append(action)
    session["reward_trace"].append(r)
    session["epsilon_trace"].append(agent.epsilon)
    session["topic_trace"].append(topic)

    # -------------------------
    # History log
    # -------------------------
    session["history"].append({
        "qnum": session["idx"] + 1,
        "question_id": cur["question_id"],
        "topic": topic,
        "difficulty": LEVELS[action],
        "action": action,
        "state_before": LEVELS[old_state],
        "state_before_num": old_state,
        "answer": user_ans,
        "correct_option": correct_opt,
        "is_correct": bool(is_correct),
        "reward": float(r),
        "state_after": LEVELS[new_state],
        "state_after_num": new_state,
        "epsilon": float(agent.epsilon),
    })

    # -------------------------
    # Counters
    # -------------------------
    session["idx"] += 1
    if is_correct:
        session["correct"] += 1
    session["state"] = new_state
    session["current"] = None

    # -------------------------
    # Stop condition (NO closing session)
    # -------------------------
    stop_reason = check_stop_condition()
    if stop_reason is not None:
        session["stop_reason"] = stop_reason

    done = (stop_reason is not None) or (session["idx"] >= session["n_questions"])

    return jsonify({
        "correct": bool(is_correct),
        "correct_option": correct_opt,
        "reward": float(r),
        "new_state": LEVELS[new_state],
        "done": bool(done),
        "stop_reason": session.get("stop_reason")
    })


# =========================================================
# 14) API: SUMMARY (overall + per-topic + Q-tables + traces)
# =========================================================
@app.route("/api/summary", methods=["GET"])
def api_summary():
    overall = compute_overall_metrics()
    per_topic = compute_per_topic_metrics()
    feedback = generate_ai_feedback(overall, per_topic)

    # Q-tables per topic
    qtables = {t: agents[t].Q.tolist() for t in agents}

    return jsonify({
        "stop_reason": session["stop_reason"],
        "overall_metrics": overall,
        "per_topic_metrics": per_topic,
        "ai_feedback": feedback,
        "reasoning": session["reasoning_log"],


        # traces for charts
        "traces": {
            "levels": session["level_trace"],
            "acc": session["acc_trace"],
            "rewards": session["reward_trace"],
            "actions": session["difficulty_actions"],
            "eps": session["epsilon_trace"],
            "topics": session["topic_trace"],
        },

        # detailed log
        "history": session["history"],

        # Q-tables
        "Q_tables": qtables,
         "reasoning": session["reasoning_log"]
    })

# =========================================================
# 15) RUN
# =========================================================
if __name__ == "__main__":
    app.run(debug=True)
