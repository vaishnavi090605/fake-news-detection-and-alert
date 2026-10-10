"""
ML Service — loads all trained models ONCE at startup and exposes a
single classify() function used by the /predict endpoint.

Loads:
    models/tfidf_vectorizer.joblib      (Day 3)
    models/fake_news_model.joblib       (Day 4)
    models/label_encoder.joblib         (Day 4)
    models/category_vectorizer.joblib   (Day 5)
    models/category_classifier.joblib   (Day 5)
"""

from pathlib import Path

import joblib

from app.text_cleaning import clean_text

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"


class MLService:
    def __init__(self):
        missing = [
            f for f in [
                "tfidf_vectorizer.joblib",
                "fake_news_model.joblib",
                "label_encoder.joblib",
                "category_vectorizer.joblib",
                "category_classifier.joblib",
            ]
            if not (MODELS_DIR / f).exists()
        ]
        if missing:
            raise FileNotFoundError(
                "Missing model files: " + ", ".join(missing) +
                ". Run model_training.py (Day 4) and category_classifier.py (Day 5) first."
            )

        self.vectorizer = joblib.load(MODELS_DIR / "tfidf_vectorizer.joblib")
        self.model = joblib.load(MODELS_DIR / "fake_news_model.joblib")
        self.label_encoder = joblib.load(MODELS_DIR / "label_encoder.joblib")
        self.category_vectorizer = joblib.load(MODELS_DIR / "category_vectorizer.joblib")
        self.category_classifier = joblib.load(MODELS_DIR / "category_classifier.joblib")

        # classes_ is ordered [not-fake, fake] per model_training.py's encode_labels()
        # Dataset encoding:
        # 0 = Fake
        # 1 = Genuine
        self.fake_index = 0

    def classify(self, raw_text: str) -> dict:
        """
        Returns:
            {
                "clean_text": ...,
                "prediction": "Fake" | "Genuine",
                "confidence": 0.0-1.0,   # confidence in the PREDICTED class
                "category": "Politics" | "Health" | ...
            }
        """
        cleaned = clean_text(raw_text)

        vec = self.vectorizer.transform([cleaned])

        proba = self.model.predict_proba(vec)[0]  # [P(fake), P(genuine)]
        pred_index = int(proba.argmax())
        confidence = float(proba[pred_index])

        # If model probability is near 50% (between 45% and 58%), flag as Inconclusive
        if 0.45 <= proba[self.fake_index] <= 0.58:
            prediction = "Inconclusive"
        else:
            prediction = "Fake" if pred_index == self.fake_index else "Genuine"

        cat_vec = self.category_vectorizer.transform([cleaned])
        category = self.category_classifier.predict(cat_vec)[0]

        return {
            "clean_text": cleaned,
            "prediction": prediction,
            "confidence": round(confidence, 4),
            "category": category,
        }



# Singleton — loaded once when the FastAPI app starts, reused across requests
ml_service = MLService()