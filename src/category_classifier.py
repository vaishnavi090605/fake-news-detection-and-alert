"""
Day 5 — Category Classification
---------------------------------
Assigns every checked article a category: Politics, Health, Education,
Crime, Sports, or Other.

IMPORTANT LIMITATION (mention this in your report):
Your real dataset (Fake.csv / True.csv, ISOT-style) is almost entirely
political/world news — it has no genuine labeled examples of Health,
Education, or Sports articles. A classifier trained directly on it would
essentially only ever predict "Politics" or "Other".

To get a real ML classifier instead of pure keyword-matching, this script:
    1. Weak-labels your real news_cleaned.csv using keyword rules
       (a heuristic, not ground truth).
    2. Adds a small set of hand-written seed examples for the
       under-represented categories (Health, Education, Sports, Crime)
       so the classifier has something to learn from for those classes.
    3. Trains a Logistic Regression classifier (its own TF-IDF vectorizer,
       separate from the fake/genuine one) on the combined set.

This is a reasonable approach for a demo/college project, but the
Health/Education/Sports predictions will be weaker than Politics/Other
since they're learned mostly from the small seed set. Swap in a real
labeled category dataset later for production use.

Produces:
    models/category_vectorizer.joblib
    models/category_classifier.joblib
"""

import re
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = ["Politics", "Health", "Education", "Crime", "Sports", "Other"]

# Keyword rules used only to weak-label the real dataset (heuristic, not ground truth)
CATEGORY_KEYWORDS = {
    "Politics": [
        "election", "government", "president", "minister", "parliament",
        "senate", "policy", "vote", "congress", "political party", "prime minister",
        "democrat", "republican", "campaign", "legislation", "diplomat", "embassy",
    ],
    "Health": [
        "hospital", "doctor", "disease", "virus", "vaccine", "medicine",
        "health", "covid", "patient", "treatment", "surgery", "outbreak",
        "pandemic", "clinic", "nurse", "diagnosis", "medical",
    ],
    "Education": [
        "school", "university", "student", "exam", "teacher", "education",
        "college", "curriculum", "scholarship", "classroom", "professor",
        "campus", "admission", "syllabus",
    ],
    "Crime": [
        "murder", "police", "arrest", "crime", "theft", "robbery", "court",
        "criminal", "investigation", "shooting", "assault", "fraud",
        "kidnap", "smuggling", "jail", "prison", "lawsuit",
    ],
    "Sports": [
        "match", "tournament", "player", "team", "football", "cricket",
        "championship", "score", "goal", "olympic", "coach", "stadium",
        "athlete", "league", "medal", "world cup",
    ],
}

# Small hand-written seed set so Health/Education/Sports/Crime have real
# examples to learn from (your real dataset barely has any).
SEED_EXAMPLES = [
    ("doctors warn new virus outbreak could overwhelm hospitals across the region", "Health"),
    ("health ministry announces free vaccination drive for children under five", "Health"),
    ("researchers publish study linking diet to heart disease risk", "Health"),
    ("hospital reports shortage of ICU beds during flu season", "Health"),
    ("new cancer treatment shows promising results in clinical trial", "Health"),
    ("university announces new scholarship program for engineering students", "Education"),
    ("schools to reopen next week after winter break announcement", "Education"),
    ("students protest against increase in college tuition fees", "Education"),
    ("education board releases exam results for high school students", "Education"),
    ("teacher recognized nationally for innovative classroom methods", "Education"),
    ("police arrest suspect in connection with downtown robbery case", "Crime"),
    ("court sentences man to ten years for fraud and embezzlement", "Crime"),
    ("investigation launched after string of burglaries in the neighborhood", "Crime"),
    ("authorities detain suspects in major drug smuggling operation", "Crime"),
    ("victim testifies in high profile murder trial this week", "Crime"),
    ("national football team wins championship after dramatic final match", "Sports"),
    ("cricket star breaks record for most runs in a single tournament", "Sports"),
    ("olympic committee announces host city for upcoming summer games", "Sports"),
    ("coach praises team performance after hard fought victory", "Sports"),
    ("athlete wins gold medal in record breaking performance at championship", "Sports"),
    ("local bakery wins award for best pastry in the regional food festival", "Other"),
    ("weather department forecasts heavy rainfall across the coastal region", "Other"),
    ("new smartphone model launched with upgraded camera and battery life", "Other"),
    ("city council approves plan to build new public park downtown", "Other"),
    ("traffic disrupted after road construction begins on main highway", "Other"),
]


def weak_label(text: str) -> str:
    """Keyword-based heuristic labeling for bootstrapping training data."""
    text = str(text).lower()
    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", text):
                scores[cat] += 1
    best_cat = max(scores, key=scores.get)
    return best_cat if scores[best_cat] > 0 else "Other"


def build_training_set(sample_size=6000):
    """
    Weak-labels a sample of the real cleaned dataset, then adds the
    hand-written seed examples for under-represented categories.
    """
    cleaned_path = PROCESSED_DIR / "news_cleaned.csv"
    if not cleaned_path.exists():
        raise FileNotFoundError(
            f"{cleaned_path} not found. Run preprocessing.py (Day 2) first."
        )

    print(f"Loading {cleaned_path} for weak-labeling...")
    data = pd.read_csv(cleaned_path)

    # Sample to keep this fast — weak-labeling the full 44k+ rows isn't
    # necessary, a representative sample is enough for Politics/Other.
    if len(data) > sample_size:
        data = data.sample(n=sample_size, random_state=42)

    print("Applying keyword weak-labels to real data (heuristic, not ground truth)...")
    data["category"] = data["clean_text"].apply(weak_label)

    print("\nWeak-label distribution on real data sample:")
    print(data["category"].value_counts())

    seed_df = pd.DataFrame(SEED_EXAMPLES, columns=["clean_text", "category"])
    # Repeat seed examples so they carry enough weight against thousands
    # of real (mostly Politics/Other) rows.
    seed_df = pd.concat([seed_df] * 40, ignore_index=True)

    combined = pd.concat(
        [data[["clean_text", "category"]], seed_df], ignore_index=True
    )
    combined = combined.dropna(subset=["clean_text"])
    combined = combined[combined["clean_text"].str.strip() != ""]

    print("\nFinal training set distribution (real weak-labels + seed examples):")
    print(combined["category"].value_counts())

    return combined


def train_category_classifier(combined_df):
    X = combined_df["clean_text"]
    y = combined_df["category"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    vectorizer = TfidfVectorizer(max_features=20000, ngram_range=(1, 2), min_df=2)
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    print("\nTraining category classifier (Logistic Regression, multi-class)...")
    clf = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    clf.fit(X_train_tfidf, y_train)

    y_pred = clf.predict(X_test_tfidf)
    print(f"\nCategory classifier accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print("\nClassification report:")
    print(classification_report(y_test, y_pred))

    return vectorizer, clf


def predict_category(text: str, vectorizer=None, clf=None) -> str:
    """Used later by the FastAPI backend (Day 6) to tag incoming submissions."""
    if vectorizer is None or clf is None:
        vectorizer = joblib.load(MODELS_DIR / "category_vectorizer.joblib")
        clf = joblib.load(MODELS_DIR / "category_classifier.joblib")
    vec = vectorizer.transform([text])
    return clf.predict(vec)[0]


def main():
    combined = build_training_set()
    vectorizer, clf = train_category_classifier(combined)

    joblib.dump(vectorizer, MODELS_DIR / "category_vectorizer.joblib")
    joblib.dump(clf, MODELS_DIR / "category_classifier.joblib")
    print(f"\nSaved category vectorizer -> {MODELS_DIR / 'category_vectorizer.joblib'}")
    print(f"Saved category classifier -> {MODELS_DIR / 'category_classifier.joblib'}")

    print("\n--- Quick sanity check ---")
    samples = [
        "hospital reports rise in flu cases as vaccine rollout begins",
        "national team wins the championship final in a dramatic finish",
        "university announces new scholarships for first year students",
        "police investigate robbery at downtown jewelry store",
        "president meets world leaders to discuss new trade policy",
        "new restaurant opens downtown offering local cuisine",
    ]
    for s in samples:
        print(f"  '{s[:60]}...' -> {predict_category(s, vectorizer, clf)}")


if __name__ == "__main__":
    main()