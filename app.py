from flask import Flask, request, jsonify
from flask_cors import CORS

import hashlib
import random
import string

# Database
from database import get_db
from models import init_db

# NLP logic
from model_utils import (
    analyze_question,
    process_new_question,
    extract_keywords_improved,
    calculate_advanced_rank_score,
    sbert_model,
    util
)

app = Flask(__name__)
CORS(app)

# =========================
# INIT DATABASE (RUN ONCE)
# =========================
init_db()


# =========================
# UTILS
# =========================
def generate_anon_id():
    return "Anon_" + "".join(
        random.choices(string.ascii_uppercase + string.digits, k=5)
    )


# =========================
# AUTH: SIGNUP
# =========================
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    hashed = hashlib.sha256(password.encode()).hexdigest()
    anon_id = generate_anon_id()

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (email, password, anon_id)
            VALUES (?, ?, ?)
        """, (email, hashed, anon_id))
        db.commit()
        user_id = cursor.lastrowid
    except Exception:
        db.close()
        return jsonify({"error": "User already exists"}), 400

    db.close()
    return jsonify({
        "message": "Signup successful",
        "user_id": user_id,
        "anon_id": anon_id
    })


# =========================
# AUTH: LOGIN
# =========================
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    hashed = hashlib.sha256(password.encode()).hexdigest()

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, anon_id
        FROM users
        WHERE email = ? AND password = ?
    """, (email, hashed))

    user = cursor.fetchone()
    db.close()

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({
        "message": "Login successful",
        "user_id": user["id"],
        "anon_id": user["anon_id"]
    })


# =========================
# HEALTH CHECK
# =========================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "NLP-powered Anonymous Q&A Backend is running"
    })


# =========================
# ANALYZE / SEARCH QUESTION
# =========================
@app.route("/analyze-question", methods=["POST"])
def analyze():
    data = request.json
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Question is required"}), 400

    result = analyze_question(question)
    return jsonify(result)


# =========================
# ASK QUESTION (WITH USER)
# =========================
@app.route("/ask-question", methods=["POST"])
def ask_question():
    data = request.json

    question_text = data.get("question", "").strip()
    user_id = data.get("user_id")  # ← NEW

    if not question_text:
        return jsonify({"error": "Question text is required"}), 400

    # NLP processing
    nlp_result = process_new_question(question_text)

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO questions (question_text, auto_tags, rank_score, user_id)
        VALUES (?, ?, ?, ?)
    """, (
        question_text,
        ",".join(nlp_result["auto_tags"]),
        nlp_result["rank_score"],
        user_id
    ))

    question_id = cursor.lastrowid
    db.commit()
    db.close()

    return jsonify({
        "message": "Question posted successfully",
        "question_id": question_id,
        "auto_tags": nlp_result["auto_tags"],
        "similar_questions": nlp_result["similar_questions"]
    })


# =========================
# GET ALL QUESTIONS (HOME)
# =========================
@app.route("/questions", methods=["GET"])
def get_questions():
    db = get_db()
    cursor = db.cursor()

    # Get questions with answer counts for better ranking
    cursor.execute("""
        SELECT q.id, q.question_text, q.auto_tags, q.rank_score, q.created_at,
               COUNT(a.id) as answer_count
        FROM questions q
        LEFT JOIN answers a ON q.id = a.question_id
        GROUP BY q.id
        ORDER BY q.rank_score DESC, q.created_at DESC
    """)

    questions = []
    for row in cursor.fetchall():
        q_dict = dict(row)
        # Re-calculate with answer count for more accurate ranking
        q_dict["rank_score"] = calculate_advanced_rank_score(
            similarity_score=q_dict["rank_score"],
            answer_count=q_dict["answer_count"] or 0,
            view_count=1,
            tag_relevance=0.5
        )
        questions.append(q_dict)
    
    # Sort by improved rank score
    questions.sort(key=lambda x: x["rank_score"], reverse=True)
    
    db.close()

    return jsonify(questions)


# =========================
# POST ANSWER (WITH USER)
# =========================
@app.route("/answer-question", methods=["POST"])
def answer_question():
    data = request.json

    question_id = data.get("question_id")
    answer_text = data.get("answer", "").strip()
    user_id = data.get("user_id")  # ← NEW

    if not question_id or not answer_text:
        return jsonify({"error": "Question ID and answer are required"}), 400

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO answers (question_id, answer_text, user_id)
        VALUES (?, ?, ?)
    """, (question_id, answer_text, user_id))

    db.commit()
    db.close()

    return jsonify({
        "message": "Answer posted successfully"
    })


# =========================
# GET QUESTION + ANSWERS
# =========================
@app.route("/questions/<int:question_id>", methods=["GET"])
def get_question_detail(question_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT * FROM questions WHERE id = ?
    """, (question_id,))
    question = cursor.fetchone()

    if not question:
        db.close()
        return jsonify({"error": "Question not found"}), 404

    cursor.execute("""
        SELECT answer_text, created_at, user_id
        FROM answers
        WHERE question_id = ?
        ORDER BY created_at ASC
    """, (question_id,))
    answers = cursor.fetchall()

    db.close()

    return jsonify({
        "question": dict(question),
        "answers": [dict(a) for a in answers]
    })


# =========================
# USER PREFERENCES: SAVE TAGS
# =========================
@app.route("/user/preferences", methods=["POST"])
def save_user_preferences():
    data = request.json
    user_id = data.get("user_id")
    tags = data.get("tags", [])

    if not user_id or not tags:
        return jsonify({"error": "User ID and tags are required"}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            INSERT INTO user_preferences (user_id, tags)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET tags = excluded.tags, updated_at = CURRENT_TIMESTAMP
        """, (user_id, ",".join(tags)))
        db.commit()
    except Exception as e:
        db.close()
        return jsonify({"error": str(e)}), 400

    db.close()
    return jsonify({"message": "Preferences saved successfully"})


# =========================
# USER PREFERENCES: GET TAGS
# =========================
@app.route("/user/preferences/<int:user_id>", methods=["GET"])
def get_user_preferences(user_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT tags FROM user_preferences WHERE user_id = ?
    """, (user_id,))
    result = cursor.fetchone()
    db.close()

    if result:
        tags = result["tags"].split(",")
        return jsonify({"tags": tags})
    else:
        return jsonify({"tags": []})


# =========================
# GET QUESTIONS FILTERED BY USER PREFERENCES
# =========================
@app.route("/questions/filtered/<int:user_id>", methods=["GET"])
def get_filtered_questions(user_id):
    db = get_db()
    cursor = db.cursor()

    # Get user preferences
    cursor.execute("""
        SELECT tags FROM user_preferences WHERE user_id = ?
    """, (user_id,))
    pref_result = cursor.fetchone()
    
    if not pref_result:
        # No preferences set, return all questions
        cursor.execute("""
            SELECT id, question_text, auto_tags, rank_score, created_at
            FROM questions
            ORDER BY rank_score DESC, created_at DESC
        """)
        questions = [dict(row) for row in cursor.fetchall()]
        db.close()
        return jsonify(questions)
    
    user_tags = set(pref_result["tags"].lower().split(","))
    
    # Get all questions with answer counts
    cursor.execute("""
        SELECT q.id, q.question_text, q.auto_tags, q.rank_score, q.created_at,
               COUNT(a.id) as answer_count
        FROM questions q
        LEFT JOIN answers a ON q.id = a.question_id
        GROUP BY q.id
        ORDER BY q.rank_score DESC, q.created_at DESC
    """)
    
    all_questions = cursor.fetchall()
    db.close()

    # Filter and re-rank questions based on user tags
    filtered = []
    for q in all_questions:
        if q["auto_tags"]:
            question_tags = set(tag.strip().lower() for tag in q["auto_tags"].split(","))
            # Check if any user tag matches question tags
            if user_tags & question_tags:  # intersection
                # Recalculate rank score with answer count
                improved_score = calculate_advanced_rank_score(
                    similarity_score=q["rank_score"],
                    answer_count=q["answer_count"] or 0,
                    view_count=1,
                    tag_relevance=0.6
                )
                q_dict = dict(q)
                q_dict["rank_score"] = improved_score
                filtered.append(q_dict)
    
    # Sort by improved rank score
    filtered.sort(key=lambda x: x["rank_score"], reverse=True)
    
    return jsonify(filtered if filtered else all_questions[:10])


# =========================
# GET SIMILAR QUESTIONS (CLUSTERING)
# =========================
@app.route("/questions/similar/<int:question_id>", methods=["GET"])
def get_similar_questions(question_id):
    """
    Returns questions similar to the specified question
    Used for clustering/related questions display
    """
    db = get_db()
    cursor = db.cursor()

    # Get the target question
    cursor.execute("""
        SELECT id, question_text, auto_tags
        FROM questions
        WHERE id = ?
    """, (question_id,))
    
    target_q = cursor.fetchone()
    if not target_q:
        db.close()
        return jsonify({"error": "Question not found"}), 404

    # Get all other questions
    cursor.execute("""
        SELECT q.id, q.question_text, q.auto_tags, q.rank_score, q.created_at,
               COUNT(a.id) as answer_count
        FROM questions q
        LEFT JOIN answers a ON q.id = a.question_id
        WHERE q.id != ?
        GROUP BY q.id
    """, (question_id,))
    
    all_questions = cursor.fetchall()
    db.close()

    # Calculate similarity scores using SBERT embeddings
    target_embedding = sbert_model.encode(target_q["question_text"])
    
    similar = []
    for q in all_questions:
        q_embedding = sbert_model.encode(q["question_text"])
        similarity = float(util.cos_sim(target_embedding, q_embedding)[0][0])
        
        # Only include questions with >0.3 similarity
        if similarity > 0.3:
            # Re-rank with advanced scoring
            final_score = calculate_advanced_rank_score(
                similarity_score=similarity,
                answer_count=q["answer_count"] or 0,
                view_count=1,
                tag_relevance=0.5
            )
            
            similar.append({
                "id": q["id"],
                "question": q["question_text"],
                "tags": q["auto_tags"],
                "similarity": similarity,
                "rank_score": final_score,
                "answer_count": q["answer_count"] or 0
            })
    
    # Sort by final score
    similar.sort(key=lambda x: x["rank_score"], reverse=True)
    
    return jsonify({
        "original_question": target_q["question_text"],
        "similar_questions": similar[:10]  # Top 10 similar
    })


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    app.run(debug=True)
