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

    plain_text = (
        f"TruthGuard AI Misinformation Alert\n\n"
        f"Result: {prediction.upper()}\n"
        f"Confidence: {conf_pct}\n"
        f"Similarity: {similarity_text}\n"
        f"Detection Counter: {detection_count}x\n"
        f"Category: {category}\n"
        f"Severity: {severity.upper() if severity else 'MEDIUM'}\n\n"
        f"Analyzed Story:\n{original_text}\n\n"
        f"Dispatched to Nearby Police Station / Misinformation Cell: {target_email}\n"
    )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b1329; color: #e2e8f0; margin: 0; padding: 12px; }}
        .card {{ background-color: #111c38; border: 1px solid #1e293b; border-radius: 12px; padding: 22px; max-width: 600px; margin: auto; box-sizing: border-box; }}
      </style>
    </head>
    <body style="background-color: #0b1329; margin: 0; padding: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td align="center">
            <div class="card" style="background-color: #111c38; border: 1px solid #1e293b; border-radius: 12px; padding: 22px; max-width: 600px; text-align: left;">
              
              <!-- Header with badge -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom: 12px;">
                <tr>
                  <td valign="middle" align="left">
                    <div style="font-size: 20px; font-weight: 800; color: #38bdf8; line-height: 1.3;">TruthGuard AI<br>Misinformation Alert</div>
                  </td>
                  <td valign="top" align="right" style="padding-left: 12px;">
                    <span style="background-color: {pred_color}; color: #ffffff; padding: 6px 14px; border-radius: 6px; font-weight: 800; font-size: 13px; text-transform: uppercase; display: inline-block; white-space: nowrap; letter-spacing: 0.5px;">
                      {prediction}
                    </span>
                  </td>
                </tr>
              </table>

              <p style="color: #94a3b8; font-size: 13px; margin: 0 0 16px 0; line-height: 1.5;">
                An analysis request was performed on TruthGuard AI Dashboard.
              </p>

              <!-- 2-Column Metrics Table (Works on all mobile devices & Gmail) -->
              <table width="100%" cellpadding="0" cellspacing="8" border="0" style="background-color: #070b16; border: 1px solid #1e293b; border-radius: 8px; margin-bottom: 18px;">
                <tr>
                  <td width="50%" style="background-color: #0f172a; padding: 12px 14px; border-radius: 6px; vertical-align: top;">
                    <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">PREDICTION RESULT</div>
                    <div style="font-size: 18px; font-weight: 800; color: {pred_color}; margin-top: 4px;">{prediction.upper()}</div>
                  </td>
                  <td width="50%" style="background-color: #0f172a; padding: 12px 14px; border-radius: 6px; vertical-align: top;">
                    <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">CONFIDENCE SCORE</div>
                    <div style="font-size: 18px; font-weight: 800; color: #f8fafc; margin-top: 4px;">{conf_pct}</div>
                  </td>
                </tr>
                <tr>
                  <td width="50%" style="background-color: #0f172a; padding: 12px 14px; border-radius: 6px; vertical-align: top;">
                    <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">COSINE SIMILARITY</div>
                    <div style="font-size: 18px; font-weight: 800; color: #f8fafc; margin-top: 4px;">{similarity_text}</div>
                  </td>
                  <td width="50%" style="background-color: #0f172a; padding: 12px 14px; border-radius: 6px; vertical-align: top;">
                    <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">DETECTION COUNTER</div>
                    <div style="font-size: 18px; font-weight: 800; color: #f8fafc; margin-top: 4px;">{detection_count}x</div>
                  </td>
                </tr>
                <tr>
                  <td width="50%" style="background-color: #0f172a; padding: 12px 14px; border-radius: 6px; vertical-align: top;">
                    <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">CATEGORY</div>
                    <div style="font-size: 18px; font-weight: 800; color: #38bdf8; margin-top: 4px;">{category}</div>
                  </td>
                  <td width="50%" style="background-color: #0f172a; padding: 12px 14px; border-radius: 6px; vertical-align: top;">
                    <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">RISK SEVERITY</div>
                    <div style="font-size: 18px; font-weight: 800; color: #f59e0b; margin-top: 4px;">{severity.upper() if severity else 'HIGH'}</div>
                  </td>
                </tr>
              </table>

              <!-- Analyzed Story Content -->
              <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 6px;">ANALYZED STORY CONTENT:</div>
              <div style="background-color: #070b16; border-left: 4px solid {pred_color}; padding: 14px 18px; border-radius: 6px; font-style: italic; color: #cbd5e1; font-size: 14px; line-height: 1.6; margin-bottom: 18px;">
                "{original_text}"
              </div>

              <!-- Footer -->
              <div style="font-size: 12px; color: #64748b; border-top: 1px solid #1e293b; padding-top: 14px; line-height: 1.6;">
                Dispatched to Nearby Police Station / Misinformation Monitoring Cell: <strong style="color: #94a3b8;">{target_email}</strong><br>
                TruthGuard AI — Detect · Verify · Protect
              </div>

            </div>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    # 1. Dispatch via Gmail SMTP (standard)
    if SMTP_USER and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"TruthGuard AI Alerts <{SMTP_USER}>"
            msg["To"] = target_email
            msg.attach(MIMEText(plain_text, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=3) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, target_email, msg.as_string())

            print(f"[EMAIL ALERT] Alert email sent successfully to {target_email} via Gmail SMTP!")
            return True
        except Exception as e:
            print(f"[EMAIL ERROR] SMTP dispatch failed: {e}")
            return False

    return False


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

    is_escalation = (fake_count >= 3)
    if is_escalation:
        subject = f"🚨 [CRITICAL POLICE ESCALATION] Fake News Spread Exceeded Limit ({fake_count} Strikes) - Location: {person_location} - Assigned: {station_name}"
        badge_text = f"THRESHOLD EXCEEDED ({fake_count} STRIKES)"
        intro_text = f"An automated system monitor has flagged a user who has submitted or attempted to distribute <strong>confirmed fake messages {fake_count} times</strong> (exceeding the safety limit of 3 strikes)."
    else:
        subject = f"🚔 [POLICE DISPATCH ALERT] Fake News Detected (Strike #{fake_count}) - Location: {person_location} - Assigned: {station_name}"
        badge_text = f"POLICE MONITORING ACTIVE (STRIKE #{fake_count} OF 3)"
        intro_text = f"An automated system monitor has intercepted a confirmed fake news submission (<strong>Strike #{fake_count} of 3</strong>) and dispatched location coordinates to the nearest police station."

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
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b1329; color: #f8fafc; margin: 0; padding: 12px; }}
        .alert-card {{ background-color: #1a0f18; border: 2px solid #ef4444; border-radius: 12px; padding: 22px; max-width: 680px; margin: auto; box-sizing: border-box; }}
      </style>
    </head>
    <body style="background-color: #0b1329; margin: 0; padding: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td align="center">
            <div class="alert-card" style="background-color: #1a0f18; border: 2px solid #ef4444; border-radius: 12px; padding: 22px; max-width: 680px; text-align: left; box-shadow: 0 0 25px rgba(239, 68, 68, 0.25);">

              <!-- Header with Compact Pill Badge (Never Stretches Vertically!) -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom: 16px; border-bottom: 1px solid rgba(239, 68, 68, 0.4); padding-bottom: 12px;">
                <tr>
                  <td valign="middle" align="left">
                    <div style="color: #ef4444; font-size: 20px; font-weight: 800; letter-spacing: 0.5px; line-height: 1.2;">POLICE DEPARTMENT NOTICE</div>
                    <div style="color: #94a3b8; font-size: 12px; margin-top: 4px;">Automated Misinformation Interception System</div>
                  </td>
                  <td valign="top" align="right" style="padding-left: 10px; width: 40%;">
                    <div style="background-color: #ef4444; color: #ffffff; padding: 8px 12px; border-radius: 6px; font-weight: 800; font-size: 11px; text-align: center; line-height: 1.3; letter-spacing: 0.5px; box-shadow: 0 2px 8px rgba(239, 68, 68, 0.4);">
                      {badge_text}
                    </div>
                  </td>
                </tr>
              </table>

              <!-- Notice Body -->
              <p style="color: #e2e8f0; font-size: 13px; line-height: 1.6; margin: 0 0 16px 0;">
                <strong style="color: #fca5a5;">ATTENTION LAW ENFORCEMENT &amp; CYBER CELL:</strong><br>
                {intro_text}
              </p>

              <!-- Suspect Identification & Geolocation -->
              <div style="background-color: rgba(239, 68, 68, 0.08); border-left: 4px solid #ef4444; padding: 14px 18px; border-radius: 6px; margin-bottom: 16px; font-size: 13px; line-height: 1.8;">
                <div style="color: #f87171; font-weight: 800; font-size: 14px; margin-bottom: 6px;">📍 Suspect Identification &amp; Geolocation:</div>
                <div><strong>Identified Location:</strong> <span style="font-size: 15px; color: #38bdf8; font-weight: bold;">📍 {person_location}</span></div>
                <div><strong>Username / Handle:</strong> <span style="color: #f1f5f9;">{person_username}</span></div>
                <div><strong>Registered Contact Email:</strong> <span style="color: #f1f5f9;">{person_email}</span></div>
                <div><strong>Cumulative Strike Count:</strong> <span style="color: #ef4444; font-weight: bold;">{fake_count} Strikes</span></div>
              </div>

              <!-- Assigned Police Station -->
              <div style="background-color: #070b16; border: 1px solid #38bdf8; border-radius: 8px; padding: 14px 18px; margin-bottom: 16px; font-size: 13px; line-height: 1.8;">
                <div style="color: #38bdf8; font-weight: 800; font-size: 14px; margin-bottom: 6px;">🚔 Nearest Jurisdiction Police Station Detected:</div>
                <div><strong>Assigned Police Station:</strong> <span style="font-size: 14px; font-weight: bold; color: #f8fafc;">{station_name}</span></div>
                <div><strong>Jurisdiction Area / Address:</strong> <span style="color: #cbd5e1;">{station_addr}</span></div>
                <div><strong>Supervising Authority:</strong> <span style="color: #cbd5e1;">{sho}</span></div>
                <div><strong>Police Contact:</strong> <span style="color: #cbd5e1;">{station_phone} | <strong>National Cybercrime:</strong> 1930</span></div>
                <div><strong>Dispatch Destination:</strong> <span style="color: #fca5a5; font-weight: bold;">{target_email}</span></div>
              </div>

              <!-- Flagged Story -->
              <div style="margin-bottom: 16px;">
                <div style="color: #fbbf24; font-weight: 700; font-size: 12px; margin-bottom: 6px; text-transform: uppercase;">Latest Fake Message Detected (Strike #{fake_count}):</div>
                <div style="background-color: #070b16; border-left: 4px solid #f59e0b; padding: 12px 16px; font-style: italic; color: #fef08a; border-radius: 4px; font-size: 13px; line-height: 1.6;">
                  "{current_fake_story}"
                </div>
              </div>

              {history_html}

              <!-- Statutory Notice Footer -->
              <div style="font-size: 11px; color: #94a3b8; border-top: 1px solid #334155; margin-top: 20px; padding-top: 12px; line-height: 1.6;">
                <strong>STATUTORY COMPLIANCE NOTICE:</strong><br>
                This automated evidentiary report was compiled by TruthGuard AI in accordance with IT Act 2000 &amp; Section 505 IPC monitoring provisions.
                Factual similarity tracking and user geolocation are provided to assist designated law enforcement authorities in verifying coordinated misinformation campaigns.
              </div>

            </div>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    plain_text = (
        f"POLICE DEPARTMENT NOTICE — Misinformation Interception Notice\n\n"
        f"Status: {badge_text}\n"
        f"Suspect Location Detected: {person_location}\n"
        f"Username: {person_username} ({person_email})\n"
        f"Strike Count: {fake_count} confirmed fake stories\n\n"
        f"Nearest Police Station: {station_name}\n"
        f"Station Address: {station_addr}\n"
        f"Supervising Authority: {sho}\n"
        f"Direct Phone: {station_phone} / Cyber Helpline: 1930\n\n"
        f"Intercepted Story:\n{current_fake_story}\n\n"
        f"Evidentiary record dispatched in compliance with IT Act 2000 & Section 505 IPC monitoring provisions.\n"
    )

    if SMTP_USER and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"TruthGuard Cyber Emergency Alerts <{SMTP_USER}>"
            msg["To"] = target_email
            msg.attach(MIMEText(plain_text, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=3) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, target_email, msg.as_string())

            print(f"[POLICE DISPATCH] High-priority Police Escalation email sent to {target_email} via Gmail SMTP!")
            return True
        except Exception as e:
            print(f"[POLICE DISPATCH ERROR] Failed to send police email via SMTP: {e}")
            return False

    return False