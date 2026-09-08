import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer


# Load cleaned dataset
data = pd.read_csv("data/processed/news_cleaned.csv")

print("Dataset shape:", data.shape)


# Input and target
X = data["clean_text"]
y = data["label"]


# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("\n========== TRAIN TEST SPLIT ==========")
print("Training samples:", len(X_train))
print("Testing samples:", len(X_test))


# Create TF-IDF vectorizer
vectorizer = TfidfVectorizer(
    max_features=50000,
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.95
)


# Learn vocabulary from training data
X_train_tfidf = vectorizer.fit_transform(X_train)

# Transform test data using the same vocabulary
X_test_tfidf = vectorizer.transform(X_test)


print("\n========== TF-IDF ==========")
print("Training matrix shape:", X_train_tfidf.shape)
print("Testing matrix shape:", X_test_tfidf.shape)
print("Vocabulary size:", len(vectorizer.vocabulary_))


# Save vectorizer
joblib.dump(
    vectorizer,
    "models/tfidf_vectorizer.joblib"
)

print("\nTF-IDF vectorizer saved successfully!")