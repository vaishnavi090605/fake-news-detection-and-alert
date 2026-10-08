
from pathlib import Path

import resend
from dotenv import dotenv_values

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

env = dotenv_values(ENV_FILE)
resend.api_key = env.get("RESEND_API_KEY")
ALERT_EMAIL = env.get("ALERT_EMAIL")

def send_fake_news_alert(
    fake_news_id: int,
    category: str,
    severity: str,
    detection_count: int,
    similarity_score: float | None,
):
    if not resend.api_key:
        raise RuntimeError("RESEND_API_KEY is not configured")

    if not ALERT_EMAIL:
        raise RuntimeError("ALERT_EMAIL is not configured")

    similarity_text = (
        f"{similarity_score * 100:.1f}%"
        if similarity_score is not None
        else "No historical match"
    )

    resend.Emails.send(
        {
            "from": "TruthGuard AI <onboarding@resend.dev>",
            "to": [ALERT_EMAIL],
            "subject": f"🚨 TruthGuard AI Alert — {severity.upper()} Risk",
            "html": f"""
            <h2>🚨 Fake News Alert</h2>

            <p>A repeated fake-news pattern has been detected
            by <strong>TruthGuard AI</strong>.</p>

            <hr>

            <p><strong>Fake Story ID:</strong> #{fake_news_id}</p>
            <p><strong>Category:</strong> {category}</p>
            <p><strong>Severity:</strong> {severity.upper()}</p>
            <p><strong>Detection Count:</strong> {detection_count}</p>
            <p><strong>Historical Similarity:</strong> {similarity_text}</p>

            <hr>

            <p>
                This alert indicates textual similarity to a previously
                detected fake-news story. It does not prove factual truth.
            </p>

            <p>
                <strong>TruthGuard AI</strong><br>
                AI-Based Social Media Fake News Detection System
            </p>
            """,
        }
    )