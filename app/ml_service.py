"""
ML Service — loads all trained models ONCE at startup and exposes a
single classify() function used by the /predict endpoint.

Loads:
    models/tfidf_vectorizer.joblib      (Day 3)
    models/fake_news_model.joblib       (Day 4)
    models/label_encoder.joblib         (Day 4)
    models/category_vectorizer.joblib   (Day 5)
    models/category_classifier.joblib   (Day 5)

NOTE ON MODEL METRICS:
    The trained model reports perfect metrics (1.0) which indicates data leakage
    during the train/test split. The model is used as a heuristic guide only.
    Final predictions are strictly binary: Fake or Genuine.
    Logistic Regression is a binary classifier — argmax always produces a winner.
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
                "category": "Politics" | "Health" | "Crime" | ...,
                "reasons": list[str]     # human-readable explanation of why
            }
        """
        import re

        cleaned = clean_text(raw_text)
        lower_raw = raw_text.lower()
        reasons = []

        # ──────────────────────────────────────────────────────
        # 1. High-Precision Heuristic Detection
        #    Lottery Scams, Phishing, Bank Fraud & Health Hoaxes
        # ──────────────────────────────────────────────────────
        lottery_match = bool(re.search(r"\b(?:won|winner|win|claim)\b.*\b(?:lottery|jackpot|cash prize|prize|draw|crore|lakh|million)\b", lower_raw))
        no_ticket_match = bool(re.search(r"\b(?:never|without)\b.*\b(?:purchased|bought|buying|got|had)\b.*\b(?:ticket|entry|coupon)\b", lower_raw))
        congrats_match = bool(re.search(r"\b(?:congratulations|congrats)\b.*\b(?:won|claim|prize|lottery|selected)\b", lower_raw))
        bank_details_match = bool(re.search(r"\b(?:send|share|provide|enter|submit|reply with)\b.*\b(?:bank details|account number|account details|card details|debit card|credit card|cvv|otp|pin|password)\b", lower_raw))
        kyc_phishing_match = bool(re.search(r"\b(?:kyc|pan card|aadhaar|bank account)\b.*(?:suspended|blocked|deactivated|expire|update immediately)", lower_raw))
        miracle_cure_match = bool(re.search(r"\b(?:miracle|secret|guaranteed|100%)\b.*\b(?:cure|treatment|remedy)\b", lower_raw))
        cure_all_match = bool(re.search(r"\b(?:kills|cures)\b.*(?:all (?:virus|viruses|diseases?|infections?|cancer)).*(?:in \d+|guaranteed|instantly|minutes|hours)", lower_raw))
        vaccine_microchip_match = bool(re.search(r"\bvaccine.*(?:microchip|magnetic|control (?:mind|humans?))", lower_raw))
        gov_giveaway_match = bool(re.search(r"\b(?:modi|pm|government|cm)\b.*(?:giving|providing|announces?)\b.*(?:free (?:recharge|laptop|smartphone|electricity|money|cash))\b.*(?:click|link|register)", lower_raw))

        is_scam = (
            (lottery_match and (no_ticket_match or bank_details_match or congrats_match)) or
            (bank_details_match and (lottery_match or congrats_match or "prize" in lower_raw or "lottery" in lower_raw)) or
            (no_ticket_match and (lottery_match or congrats_match)) or
            kyc_phishing_match or
            miracle_cure_match or cure_all_match or vaccine_microchip_match or
            gov_giveaway_match
        )

        if is_scam:
            # Build human-readable reasons for the scam detection
            if lottery_match or congrats_match:
                reasons.append("Contains unsolicited prize/lottery claim language — classic financial scam pattern.")
            if no_ticket_match:
                reasons.append("Claims prize was won without any prior ticket purchase — a hallmark of lottery fraud.")
            if bank_details_match:
                reasons.append("Solicits bank account / OTP / card details — credential harvesting phishing attempt.")
            if kyc_phishing_match:
                reasons.append("Falsely claims KYC, Aadhaar or bank account is blocked to pressure urgent action — phishing tactic.")
            if miracle_cure_match or cure_all_match:
                reasons.append("Claims a guaranteed or miraculous medical cure — contradicted by established medical consensus.")
            if vaccine_microchip_match:
                reasons.append("Contains vaccine microchip/mind-control claim — a widely debunked conspiracy theory.")
            if gov_giveaway_match:
                reasons.append("Falsely attributes free giveaway scheme to a government official and asks to click a link.")

            category = "Crime" if (bank_details_match or lottery_match or kyc_phishing_match or gov_giveaway_match) else "Health"
            return {
                "clean_text": cleaned,
                "prediction": "Fake",
                "confidence": 0.985,
                "category": category,
                "reasons": reasons,
            }

        # ──────────────────────────────────────────────────────
        # 2. Machine Learning TF-IDF Classifier for general news
        # ──────────────────────────────────────────────────────
        vec = self.vectorizer.transform([cleaned])
        proba = self.model.predict_proba(vec)[0]  # [P(fake), P(genuine)]
        pred_index = int(proba.argmax())
        confidence = float(proba[pred_index])

        p_fake = float(proba[self.fake_index])
        p_genuine = float(proba[1 - self.fake_index])

        # Binary classification: always Fake or Genuine based on model's argmax
        # Logistic Regression is a binary classifier — there is always a winner.
        if pred_index == self.fake_index:
            prediction = "Fake"
            confidence = p_fake
            reasons.append(
                f"TF-IDF + Logistic Regression model assigned {p_fake*100:.1f}% probability of being fake news. "
                "The linguistic patterns in this text closely match known misinformation in the training corpus."
            )
            reasons.append(
                "NOTE: This is an ML-based prediction, not a verified fact-check. "
                "No external source was consulted. Treat as a flag for further review."
            )
        else:
            prediction = "Genuine"
            confidence = p_genuine
            reasons.append(
                f"TF-IDF + Logistic Regression model assigned {p_genuine*100:.1f}% probability of being genuine. "
                "The linguistic patterns appear consistent with factual reporting."
            )
            reasons.append(
                "NOTE: 'Genuine' here means the ML model did not detect misinformation patterns — "
                "it does NOT constitute independent verification. Always verify with trusted sources."
            )

        cat_vec = self.category_vectorizer.transform([cleaned])
        category = self.category_classifier.predict(cat_vec)[0]

        return {
            "clean_text": cleaned,
            "prediction": prediction,
            "confidence": round(confidence, 4),
            "category": category,
            "reasons": reasons,
        }


# Singleton — loaded once when the FastAPI app starts, reused across requests
ml_service = MLService()