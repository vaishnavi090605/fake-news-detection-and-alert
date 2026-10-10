"""
Day 4 — Model Training
-----------------------
Trains a Logistic Regression classifier on the TF-IDF features produced
in Day 3.

IMPORTANT: your Day 3 tfidf_features.py only saves the fitted vectorizer
to disk (models/tfidf_vectorizer.joblib) — it does NOT save the train/test
split or the transformed TF-IDF matrices. So this script reproduces the
exact same split (same random_state=42 + stratify=y as tfidf_features.py)
from data/processed/news_cleaned.csv, then transforms it with your
already-fitted vectorizer. Because the split is deterministic, X_train
here will be identical to the X_train that vectorizer was originally
fit on.

Expects:
    data/processed/news_cleaned.csv    (from preprocessing.py)
    models/tfidf_vectorizer.joblib     (from tfidf_features.py)

Produces:
    models/fake_news_model.joblib     -> trained Logistic Regression model
    models/metrics.json               -> evaluation metrics (for dashboard use)
    models/confusion_matrix.png       -> visual confusion matrix
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def load_day3_artifacts():
    print("Reproducing Day 3 split + loading fitted vectorizer...")

    cleaned_path = PROCESSED_DIR / "news_cleaned.csv"
    vectorizer_path = MODELS_DIR / "tfidf_vectorizer.joblib"

    if not cleaned_path.exists():
        raise FileNotFoundError(
            f"Expected file not found: {cleaned_path}\n"
            "Run preprocessing.py first to produce news_cleaned.csv."
        )
    if not vectorizer_path.exists():
        raise FileNotFoundError(
            f"Expected file not found: {vectorizer_path}\n"
            "Run tfidf_features.py first to produce tfidf_vectorizer.joblib."
        )

    data = pd.read_csv(cleaned_path)

    X = data["clean_text"]
    y = data["label"]

    # Same split parameters as tfidf_features.py — reproduces identical
    # X_train / X_test rows deterministically.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    vectorizer = joblib.load(vectorizer_path)

    # Transform (not fit) — the vectorizer's vocabulary was already learned
    # from this exact X_train in tfidf_features.py.
    X_train_tfidf = vectorizer.transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    print(f"  X_train shape: {X_train_tfidf.shape}")
    print(f"  X_test shape:  {X_test_tfidf.shape}")

    return X_train_tfidf, X_test_tfidf, y_train, y_test, vectorizer


# VERIFIED against the real dataset: the article confirmed to be from
# Fake.csv ("Trump ... Happy New Year ... fake news media") has raw
# label 0 in news_cleaned.csv. So in THIS dataset: 0 = Fake, 1 = Genuine.
# This was checked empirically, not assumed — see the conversation history
# for how it was verified. If you ever regenerate news_dataset.csv from
# scratch with a different label convention, re-verify this the same way:
#   df = pd.read_csv('data/processed/news_cleaned.csv')
#   df[df['clean_text'].str.contains('<a snippet guaranteed to be from Fake.csv>')]['label']
VERIFIED_FAKE_LABEL = 0


def encode_labels(y_train, y_test):
    encoder = LabelEncoder()
    fake_label = VERIFIED_FAKE_LABEL
    encoder.classes_ = np.array(["Fake", "Genuine"])

    y_train_enc = np.where(y_train == fake_label, 0, 1)
    y_test_enc = np.where(y_test == fake_label, 0, 1)

    mapping = {"Fake": 0, "Genuine": 1}
    print(f"\nLabel mapping in use: {mapping} (0 = Fake, verified against real data)")

    return y_train_enc, y_test_enc, encoder


def train_model(X_train, y_train):
    print("\nTraining Logistic Regression classifier...")
    model = LogisticRegression(
        max_iter=1000,
        C=1.0,
        class_weight="balanced",  # handles fake/genuine imbalance
        random_state=42,
    )
    model.fit(X_train, y_train)
    return model


def evaluate_model(model, X_test, y_test, label_encoder):
    print("\nEvaluating on held-out test set...")
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, pos_label=0, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, pos_label=0, zero_division=0), 4),
        "f1_score": round(f1_score(y_test, y_pred, pos_label=0, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, y_proba), 4),
    }

    print("\n=== Metrics ===")
    for k, v in metrics.items():
        print(f"  {k:10s}: {v}")

    # target_names ordered by encoded value (0, 1, ...) so labels always
    # match what the encoder actually produced — not a hardcoded guess.
    target_names = [str(c) for c in label_encoder.classes_]
    print("\n=== Classification Report ===")
    report = classification_report(y_test, y_pred, target_names=target_names)
    print(report)

    cm = confusion_matrix(y_test, y_pred)
    return metrics, report, cm, target_names


def save_confusion_matrix(cm, out_path: Path, labels):
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix")
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                     color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.colorbar(im)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"\nSaved confusion matrix plot -> {out_path}")


def main():
    X_train, X_test, y_train, y_test, vectorizer = load_day3_artifacts()
    y_train, y_test, label_encoder = encode_labels(y_train, y_test)

    model = train_model(X_train, y_train)
    metrics, report, cm, target_names = evaluate_model(model, X_test, y_test, label_encoder)

    model_path = MODELS_DIR / "fake_news_model.joblib"
    joblib.dump(model, model_path)
    print(f"\nSaved trained model -> {model_path}")

    encoder_path = MODELS_DIR / "label_encoder.joblib"
    joblib.dump(label_encoder, encoder_path)
    print(f"Saved label encoder -> {encoder_path}")

    metrics_path = MODELS_DIR / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved metrics -> {metrics_path}")

    save_confusion_matrix(cm, MODELS_DIR / "confusion_matrix.png", target_names)

    print("\nDay 4 complete. Model + metrics are ready for the FastAPI backend (Day 6).")


if __name__ == "__main__":
    main()