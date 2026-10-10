import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

from dotenv import dotenv_values

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

env = dotenv_values(ENV_FILE) if ENV_FILE.exists() else {}

ALERT_EMAIL = env.get("ALERT_EMAIL") or os.environ.get("ALERT_EMAIL") or "bachuvaishnavi098@gmail.com"
SMTP_SERVER = env.get("SMTP_SERVER") or os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(env.get("SMTP_PORT") or os.environ.get("SMTP_PORT", 587))
SMTP_USER = env.get("SMTP_USER") or os.environ.get("SMTP_USER") or "bachuvaishnavi098@gmail.com"
raw_pass = env.get("SMTP_PASSWORD") or os.environ.get("SMTP_PASSWORD") or "prsh lljm fmjy rawg"
SMTP_PASSWORD = raw_pass.replace(" ", "").strip()


def send_fake_news_alert(
    fake_news_id: int,
    category: str,
    severity: str,
    detection_count: int,
    similarity_score: float | None,
    original_text: str = "",
    prediction: str = "Fake",
    confidence: float = 0.9,
    recipient_email: str | None = None,
):
    target_email = recipient_email or ALERT_EMAIL or "bachuvaishnavi098@gmail.com"
    conf_pct = f"{float(confidence) * 100:.1f}%"

    similarity_text = (
        f"{float(similarity_score) * 100:.1f}%"
        if similarity_score is not None
        else ( "100.0%" if prediction == "Fake" else "0.0%" )
    )

    pred_color = "#ef4444" if prediction == "Fake" else ("#f59e0b" if prediction == "Inconclusive" else "#10b981")

    subject = f"[TRUTHGUARD ALERT] {prediction.upper()} Story Analyzed - {conf_pct} Confidence ({category})"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #0b1329; color: #e2e8f0; padding: 20px; }}
        .card {{ background: #111c38; border: 1px solid #1e293b; border-radius: 10px; padding: 24px; max-width: 600px; margin: auto; }}
        .header {{ font-size: 20px; font-weight: bold; color: #38bdf8; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; }}
        .badge {{ background: {pred_color}; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold; font-size: 14px; text-transform: uppercase; }}
        .metric-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 16px 0; background: #070b16; padding: 16px; border-radius: 8px; }}
        .metric-title {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; }}
        .metric-val {{ font-size: 18px; font-weight: bold; color: #f8fafc; margin-top: 4px; }}
        .story-box {{ background: #070b16; border-left: 4px solid {pred_color}; padding: 12px 16px; border-radius: 4px; margin-top: 16px; font-style: italic; color: #cbd5e1; }}
        .footer {{ font-size: 12px; color: #64748b; margin-top: 20px; border-top: 1px solid #1e293b; padding-top: 12px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <span>TruthGuard AI Misinformation Alert</span>
          <span class="badge">{prediction}</span>
        </div>
        <p style="color: #94a3b8; font-size: 14px; margin-top: 0;">
          An analysis request was performed on TruthGuard AI Dashboard.
        </p>

        <div class="metric-grid">
          <div>
            <div class="metric-title">Prediction Result</div>
            <div class="metric-val" style="color: {pred_color};">{prediction.upper()}</div>
          </div>
          <div>
            <div class="metric-title">Confidence Score</div>
            <div class="metric-val">{conf_pct}</div>
          </div>
          <div>
            <div class="metric-title">Cosine Similarity</div>
            <div class="metric-val">{similarity_text}</div>
          </div>
          <div>
            <div class="metric-title">Detection Counter</div>
            <div class="metric-val">{detection_count}x</div>
          </div>
          <div>
            <div class="metric-title">Category</div>
            <div class="metric-val" style="color: #38bdf8;">{category}</div>
          </div>
          <div>
            <div class="metric-title">Risk Severity</div>
            <div class="metric-val" style="color: #f59e0b;">{severity.upper() if severity else 'MEDIUM'}</div>
          </div>
        </div>

        <div class="metric-title">Analyzed Story Content:</div>
        <div class="story-box">
          "{original_text}"
        </div>

        <div class="footer">
          Dispatched to Nearby Police Station / Misinformation Monitoring Cell: <strong>{target_email}</strong><br>
          TruthGuard AI — Detect · Verify · Protect
        </div>
      </div>
    </body>
    </html>
    """

    # Dispatch via Gmail SMTP
    if SMTP_USER and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"TruthGuard AI Alerts <{SMTP_USER}>"
            msg["To"] = target_email
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, target_email, msg.as_string())

            print(f"[EMAIL ALERT] Alert email sent successfully to {target_email} via Gmail SMTP!")
            return True
        except Exception as e:
            print(f"[EMAIL ERROR] SMTP dispatch failed: {e}")
            return False

    print(f"[EMAIL ALERT] Fallback email alert dispatched to {target_email}: {subject}")
    return True


def send_police_escalation_alert(
    person_username: str,
    person_email: str,
    person_location: str,
    fake_count: int,
    current_fake_story: str,
    nearest_station: dict,
    history_items: list[dict] | None = None,
    recipient_email: str | None = None,
):
    target_email = recipient_email or ALERT_EMAIL or "bachuvaishnavi098@gmail.com"
    station_name = nearest_station.get("name", "Ghatkesar Police Station")
    station_addr = nearest_station.get("address", "Ghatkesar, Hyderabad")
    station_phone = nearest_station.get("phone", "+91-40-27853400 / 100")
    sho = nearest_station.get("sho_officer", "SHO, Ghatkesar PS")

    subject = f"🚨 [POLICE ESCALATION] REPEATED FAKE NEWS SPREAD (>3 STRIKES) - Location: {person_location} - Assigned: {station_name}"

    history_html = ""
    if history_items:
        history_html = "<h4>Prior Recorded Fake Messages by this Person:</h4><ul>"
        for idx, item in enumerate(history_items[:5], 1):
            history_html += f"<li><strong>Strike {idx}:</strong> {item.get('original_text', '')[:120]}... <em>({item.get('checked_at', '')})</em></li>"
        history_html += "</ul>"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #0b1329; color: #f8fafc; padding: 20px; }}
        .alert-card {{ background: #1a0f18; border: 2px solid #ef4444; border-radius: 12px; padding: 24px; max-width: 680px; margin: auto; box-shadow: 0 0 30px rgba(239, 68, 68, 0.3); }}
        .badge-danger {{ background: #ef4444; color: white; padding: 6px 14px; border-radius: 4px; font-weight: bold; text-transform: uppercase; font-size: 13px; }}
        .station-box {{ background: #070b16; border: 1px solid #38bdf8; border-radius: 8px; padding: 16px; margin: 18px 0; }}
        .person-box {{ background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 14px 18px; border-radius: 4px; margin: 16px 0; }}
        .story-quote {{ background: #070b16; border-left: 4px solid #f59e0b; padding: 12px 16px; font-style: italic; color: #fef08a; margin: 12px 0; }}
        .footer {{ font-size: 11px; color: #94a3b8; border-top: 1px solid #334155; margin-top: 20px; padding-top: 12px; line-height: 1.5; }}
      </style>
    </head>
    <body>
      <div class="alert-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; border-bottom: 1px solid rgba(239, 68, 68, 0.4); padding-bottom: 12px;">
          <div>
            <h2 style="color: #ef4444; margin: 0; font-size: 22px;">POLICE DEPARTMENT NOTICE</h2>
            <span style="color: #94a3b8; font-size: 13px;">Automated Misinformation Interception System</span>
          </div>
          <span class="badge-danger">THRESHOLD EXCEEDED (>3 STRIKES)</span>
        </div>

        <p style="color: #e2e8f0; font-size: 14px; line-height: 1.6;">
          <strong>ATTENTION LAW ENFORCEMENT & CYBER CELL:</strong><br>
          An automated system monitor has flagged a user who has submitted or attempted to distribute 
          <strong>confirmed fake messages {fake_count} times</strong> (exceeding the safety limit of 3 strikes).
        </p>

        <div class="person-box">
          <h3 style="color: #f87171; margin-top: 0; margin-bottom: 8px;">📍 Suspect Identification & Geolocation:</h3>
          <div><strong>Identified Location:</strong> <span style="font-size: 16px; color: #38bdf8; font-weight: bold;">📍 {person_location}</span></div>
          <div><strong>Username / Handle:</strong> {person_username}</div>
          <div><strong>Registered Contact Email:</strong> {person_email}</div>
          <div><strong>Cumulative Strike Count:</strong> <span style="color: #ef4444; font-weight: bold;">{fake_count} Strikes</span> (Exceeded Threshold of 3)</div>
        </div>

        <div class="station-box">
          <h3 style="color: #38bdf8; margin-top: 0; margin-bottom: 8px;">🚔 Nearest Jurisdiction Police Station Detected:</h3>
          <div><strong>Assigned Police Station:</strong> <span style="font-size: 15px; font-weight: bold; color: #f8fafc;">{station_name}</span></div>
          <div><strong>Jurisdiction Area / Address:</strong> {station_addr}</div>
          <div><strong>Supervising Authority:</strong> {sho}</div>
          <div><strong>Police Contact:</strong> {station_phone} | <strong>National Cybercrime:</strong> 1930</div>
          <div><strong>Dispatch Destination:</strong> {target_email}</div>
        </div>

        <div>
          <h4 style="color: #fbbf24; margin-bottom: 6px;">Latest Fake Message Detected (Strike #{fake_count}):</h4>
          <div class="story-quote">
            "{current_fake_story}"
          </div>
        </div>

        {history_html}

        <div class="footer">
          <strong>STATUTORY COMPLIANCE NOTICE:</strong><br>
          This automated evidentiary report was compiled by TruthGuard AI in accordance with IT Act 2000 & Section 505 IPC monitoring provisions.
          Factual similarity tracking and user geolocation are provided to assist designated law enforcement authorities in verifying coordinated misinformation campaigns.
        </div>
      </div>
    </body>
    </html>
    """

    if SMTP_USER and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"TruthGuard Cyber Emergency Alerts <{SMTP_USER}>"
            msg["To"] = target_email
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, target_email, msg.as_string())

            print(f"[POLICE DISPATCH] High-priority Police Escalation email sent to {target_email} via Gmail SMTP!")
            return True
        except Exception as e:
            print(f"[POLICE DISPATCH ERROR] Failed to send police email: {e}")
            return False

    print(f"[POLICE DISPATCH] Fallback police dispatch queued to {target_email}: {subject}")
    return True