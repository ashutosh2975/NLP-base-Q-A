import numpy as np
import pandas as pd
import re
from sentence_transformers import SentenceTransformer, util
from keybert import KeyBERT

# =========================
# LOAD NLP DATA (YOUR DATA)
# =========================

# Load processed & ranked dataset
df = pd.read_csv(
    "D:/Projects/nlp_qa_platform/data/processed/final_dataset_ranked.csv",
    encoding="latin1",
    low_memory=False
)

# Load SBERT embeddings
embeddings = np.load(
    "D:/Projects/nlp_qa_platform/data/embeddings/question_embeddings.npy"
)

# =========================
# LOAD MODELS (ONCE)
# =========================

sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
kw_model = KeyBERT(model=sbert_model)

# =========================
# COMMON PROGRAMMING TAGS (FOR BETTER CATEGORIZATION)
# =========================

COMMON_TAGS = {
    "python": ["python", "py", "django", "flask", "async", "asyncio"],
    "javascript": ["javascript", "js", "nodejs", "node.js", "react", "vue", "angular"],
    "java": ["java", "spring", "maven", "gradle"],
    "csharp": ["csharp", "c#", "dotnet", ".net", "asp.net", "linq"],
    "sql": ["sql", "mysql", "postgresql", "database", "oracle"],
    "database": ["database", "sql", "mongodb", "redis", "cassandra"],
    "api": ["api", "rest", "graphql", "soap", "http"],
    "web": ["web", "html", "css", "frontend", "backend"],
    "testing": ["testing", "unittest", "pytest", "jest", "mocha"],
    "docker": ["docker", "kubernetes", "devops", "container"],
    "git": ["git", "github", "gitlab", "version-control"],
    "machine-learning": ["machine learning", "ml", "tensorflow", "pytorch", "sklearn"],
}

# =========================
# HELPER FUNCTIONS
# =========================

def parse_tags(tag_str):
    """
    Extract tags from string like:
    ['python' 'pandas' 'csv']
    """
    if pd.isna(tag_str):
        return []
    return re.findall(r"'([^']+)'", tag_str)


def extract_keywords_improved(text, top_n=8):
    """
    Improved keyword extraction with multiple strategies
    """
    # Try KeyBERT extraction
    try:
        keywords = kw_model.extract_keywords(
            text,
            top_n=top_n,
            stop_words="english",
            language="english"
        )
        tags = [kw[0].lower() for kw in keywords if kw[1] > 0.3]
    except:
        tags = []
    
    # Add manual pattern matching for common programming concepts
    text_lower = text.lower()
    for category, patterns in COMMON_TAGS.items():
        for pattern in patterns:
            if pattern in text_lower:
                if category not in tags:
                    tags.append(category)
                break
    
    # Remove duplicates and limit to top_n
    return list(dict.fromkeys(tags))[:top_n]


def calculate_advanced_rank_score(
    similarity_score,
    answer_count=0,
    view_count=0,
    tag_relevance=0.5
):
    """
    Calculate rank score with multiple parameters:
    - Semantic similarity (40%)
    - Tag relevance (30%)
    - Answer count (15%)
    - Recency/popularity (15%)
    """
    
    # Normalize values
    answer_score = min(answer_count / 10, 1.0) * 0.15  # Up to 10 answers
    popularity_score = min(view_count / 100, 1.0) * 0.15  # Up to 100 views
    
    # Combined score
    final_score = (
        similarity_score * 0.40 +
        tag_relevance * 0.30 +
        answer_score +
        popularity_score
    )
    
    return min(final_score, 1.0)  # Cap at 1.0


# =========================
# ANALYZE QUESTION (SEARCH)
# =========================

def analyze_question(user_question, top_k=5):
    """
    Used for searching similar questions with improved tagging
    """
    query_embedding = sbert_model.encode(user_question)

    scores = util.cos_sim(query_embedding, embeddings)[0]
    top_indices = scores.argsort(descending=True)[:top_k]

    results = []
    for idx in top_indices:
        row = df.iloc[int(idx)]
        results.append({
            "question": row["Processed_Text"][:200],
            "similarity": float(scores[idx]),
            "rank_score": float(row["final_rank_score"]),
            "tags": parse_tags(row["Tags_List"])
        })

    # Use improved keyword extraction
    auto_tags = extract_keywords_improved(user_question, top_n=8)

    return {
        "auto_tags": auto_tags,
        "similar_questions": results
    }


# =========================
# PROCESS NEW QUESTION
# (USED WHEN USER ASKS)
# =========================

def process_new_question(question_text):
    """
    Called when a user posts a new question
    with improved tagging and ranking
    """
    query_embedding = sbert_model.encode(question_text)

    scores = util.cos_sim(query_embedding, embeddings)[0]
    top_indices = scores.argsort(descending=True)[:5]

    similar_questions = []
    tag_frequency = {}
    
    for idx in top_indices:
        row = df.iloc[int(idx)]
        tags = parse_tags(row["Tags_List"])
        
        # Count tag frequency to calculate tag relevance
        for tag in tags:
            tag_frequency[tag] = tag_frequency.get(tag, 0) + 1
        
        similar_questions.append({
            "question": row["Processed_Text"][:200],
            "similarity": float(scores[idx]),
            "tags": tags
        })

    # Use improved keyword extraction
    auto_tags = extract_keywords_improved(question_text, top_n=8)
    
    # Calculate tag relevance score based on how many similar questions have these tags
    tag_relevance = 0.5
    if auto_tags and tag_frequency:
        matches = sum(1 for tag in auto_tags if tag in tag_frequency)
        tag_relevance = 0.5 + (matches / len(auto_tags)) * 0.5

    # Use advanced ranking with multiple parameters
    base_similarity = float(scores[top_indices[0]]) if len(top_indices) > 0 else 0.0
    rank_score = calculate_advanced_rank_score(
        similarity_score=base_similarity,
        answer_count=2,  # Will be updated when answers are posted
        view_count=1,
        tag_relevance=tag_relevance
    )

    return {
        "auto_tags": auto_tags,
        "similar_questions": similar_questions,
        "rank_score": min(rank_score, 1.0)
    }
