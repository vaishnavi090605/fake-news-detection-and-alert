import pickle
import sys
from pathlib import Path

import joblib
import numpy as np
from scipy.sparse import vstack
from sklearn.metrics.pairwise import cosine_similarity

# Make sibling module db_setup.py importable regardless of caller's cwd
sys.path.append(str(Path(__file__).resolve().parent))
from db_setup import get_connection, init_db  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
VECTORIZER_PATH = BASE_DIR / "models" / "tfidf_vectorizer.joblib"

REPEAT_THRESHOLD = 0.60
ALERT_AFTER = 2

_vectorizer = None


def calculate_severity(prediction, similarity_score, detection_count):
    """
    Calculates misinformation severity.

    LOW:
        New fake news with no historical match.

    MEDIUM:
        Repeated fake news or moderate/high similarity.

    HIGH:
        Very high similarity combined with multiple detections.

    Genuine news:
        No misinformation severity.
    """

    if prediction != "Fake":
        return "none"

    # First time seeing this fake story
    if similarity_score is None:
        return "low"

    # Very similar + repeatedly detected
    if similarity_score >= 0.85 and detection_count >= 3:
        return "high"

    # Historical match / repeated fake news
    if similarity_score >= 0.60 or detection_count >= 2:
        return "medium"

    return "low"


def get_vectorizer():
    """Loads the TF-IDF vectorizer once and caches it for reuse."""
    global _vectorizer

    if _vectorizer is None:
        if not VECTORIZER_PATH.exists():
            raise FileNotFoundError(
                f"Vectorizer not found at {VECTORIZER_PATH}. "
                "Run tfidf_features.py (Day 3) first."
            )

        _vectorizer = joblib.load(VECTORIZER_PATH)

    return _vectorizer


def vector_to_blob(sparse_vector) -> bytes:
    return pickle.dumps(sparse_vector)


def blob_to_vector(blob: bytes):
    return pickle.loads(blob)


def add_fake_news(
    conn,
    original_text,
    clean_text,
    category="Other",
    source=None
):
    """Stores a brand-new fake news story."""

    vectorizer = get_vectorizer()
    vector = vectorizer.transform([clean_text])

    cursor = conn.execute(
        """
        INSERT INTO fake_news_db
        (original_text, clean_text, tfidf_vector, category, source)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            original_text,
            clean_text,
            vector_to_blob(vector),
            category,
            source,
        ),
    )

    conn.commit()

    return cursor.lastrowid


def find_repeated(conn, clean_text, threshold=REPEAT_THRESHOLD):
    """
    Compares clean_text against every stored fake-news vector.

    Returns the closest historical match if similarity >= threshold.
    """

    rows = conn.execute(
        """
        SELECT id, tfidf_vector, category, detection_count
        FROM fake_news_db
        """
    ).fetchall()

    if not rows:
        return None

    vectorizer = get_vectorizer()
    new_vector = vectorizer.transform([clean_text])

    stored_vectors = vstack(
        [
            blob_to_vector(row["tfidf_vector"])
            for row in rows
        ]
    )

    similarities = cosine_similarity(
        new_vector,
        stored_vectors
    )[0]

    best_idx = int(np.argmax(similarities))
    best_score = float(similarities[best_idx])

    if best_score >= threshold:
        best_row = rows[best_idx]

        return {
            "fake_news_id": best_row["id"],
            "similarity": round(best_score, 4),
            "category": best_row["category"],
            "detection_count": best_row["detection_count"],
        }

    return None


def bump_fake_news(conn, fake_news_id):
    """Increments detection_count and last_seen_at."""

    conn.execute(
        """
        UPDATE fake_news_db
        SET detection_count = detection_count + 1,
            last_seen_at = datetime('now')
        WHERE id = ?
        """,
        (fake_news_id,),
    )

    conn.commit()

    row = conn.execute(
        """
        SELECT detection_count
        FROM fake_news_db
        WHERE id = ?
        """,
        (fake_news_id,),
    ).fetchone()

    return row["detection_count"]


def raise_alert_if_needed(
    conn,
    fake_news_id,
    detection_count,
    category,
    severity
):
    """
    Creates a database alert when repeated fake news reaches
    the configured detection threshold.
    """

    if detection_count < ALERT_AFTER:
        return None

    # Avoid duplicate open alerts
    existing = conn.execute(
        """
        SELECT id
        FROM alerts
        WHERE fake_news_id = ?
        AND status = 'new'
        """,
        (fake_news_id,),
    ).fetchone()

    if existing:
        return None

    message = (
        f"Fake news story #{fake_news_id} detected "
        f"{detection_count} times. "
        f"Category: {category}. "
        f"Severity: {severity.upper()}. "
        f"Historical repetition detected."
    )

    cursor = conn.execute(
        """
        INSERT INTO alerts
        (fake_news_id, alert_type, message, severity)
        VALUES (?, 'repeated_detection', ?, ?)
        """,
        (
            fake_news_id,
            message,
            severity,
        ),
    )

    conn.commit()

    print(
        f"ALERT raised "
        f"(severity={severity.upper()}): {message}"
    )

    return cursor.lastrowid


def record_check(
    conn,
    user_id,
    original_text,
    clean_text,
    prediction,
    confidence,
    category="Other"
):
    """
    Main entry point called by the FastAPI backend.

    Handles:
    - Fake/Genuine result
    - repeated fake detection
    - similarity calculation
    - detection count
    - severity calculation
    - database alert
    - history logging
    """

    is_repeated = 0
    matched_fake_news_id = None
    similarity_score = None
    detection_count = 1
    alert_id = None

    # Calculate initial severity.
    # If this is a new fake, similarity_score is None,
    # therefore severity becomes LOW.
    severity = calculate_severity(
        prediction,
        similarity_score,
        detection_count
    )

    if prediction == "Fake":

        match = find_repeated(
            conn,
            clean_text
        )

        if match:

            # Existing similar fake news found
            is_repeated = 1

            matched_fake_news_id = match["fake_news_id"]

            similarity_score = match["similarity"]

            # Increase historical detection count
            detection_count = bump_fake_news(
                conn,
                matched_fake_news_id
            )

            # Recalculate severity using actual match information
            severity = calculate_severity(
                prediction,
                similarity_score,
                detection_count
            )

            # Create database alert if threshold reached
            alert_id = raise_alert_if_needed(
                conn,
                matched_fake_news_id,
                detection_count,
                match["category"],
                severity
            )

        else:

            # Completely new fake story
            matched_fake_news_id = add_fake_news(
                conn,
                original_text,
                clean_text,
                category=category
            )

            detection_count = 1

            severity = calculate_severity(
                prediction,
                None,
                detection_count
            )

    # Store every submission in history
    conn.execute(
        """
        INSERT INTO news_history
        (
            user_id,
            original_text,
            clean_text,
            prediction,
            confidence,
            category,
            is_repeated,
            matched_fake_news_id,
            similarity_score
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            original_text,
            clean_text,
            prediction,
            confidence,
            category,
            is_repeated,
            matched_fake_news_id,
            similarity_score,
        ),
    )

    conn.commit()

    return {
        "prediction": prediction,
        "confidence": confidence,
        "category": category,
        "is_repeated": bool(is_repeated),
        "matched_fake_news_id": matched_fake_news_id,
        "similarity_score": similarity_score,
        "detection_count": detection_count,
        "severity": severity,
        "alert_raised": alert_id is not None,
    }


if __name__ == "__main__":

    init_db()
    conn = get_connection()

    print("\n--- Submission 1: new fake story ---")

    r1 = record_check(
        conn,
        user_id=None,
        original_text="Government secretly hides shocking truth about economy",
        clean_text="government secretly hides shocking truth about economy",
        prediction="Fake",
        confidence=0.92,
        category="Politics",
    )

    print(r1)

    print("\n--- Submission 2: same story, reworded slightly ---")

    r2 = record_check(
        conn,
        user_id=None,
        original_text="Govt secretly hides shocking truth about the economy!!",
        clean_text="govt secretly hides shocking truth about the economy",
        prediction="Fake",
        confidence=0.89,
        category="Politics",
    )

    print(r2)

    print("\n--- Submission 3: unrelated genuine story ---")

    r3 = record_check(
        conn,
        user_id=None,
        original_text="Central bank releases quarterly economic growth report",
        clean_text="central bank releases quarterly economic growth report",
        prediction="Genuine",
        confidence=0.95,
        category="Politics",
    )

    print(r3)

    conn.close()

    print("\nDay 5 self-test complete.")