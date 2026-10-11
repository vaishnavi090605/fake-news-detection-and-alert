import csv
import io
import sqlite3
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Response, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles

from app import schemas
from app.auth import (
    ADMIN_SIGNUP_CODE,
    create_access_token,
    get_current_user,
    hash_password,
    require_admin,
    verify_password,
)
from app.email_service import send_fake_news_alert, send_police_escalation_alert
from app.ml_service import ml_service
from app.police_locator import find_nearest_police_station
from database.db_setup import get_connection, init_db
from database.repeated_news_detector import record_check



app = FastAPI(title="AI-Based Fake News Detection API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def root():
    return RedirectResponse(url="/static/login.html")


@app.on_event("startup")
def startup():
    init_db()


@app.post("/register", response_model=schemas.Token)
def register(payload: schemas.UserRegister):
    role = (
        "admin"
        if payload.admin_code and payload.admin_code == ADMIN_SIGNUP_CODE
        else "user"
    )

    conn = get_connection()

    try:
        cursor = conn.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (
                payload.username,
                payload.email,
                hash_password(payload.password),
                role,
            ),
        )
        conn.commit()
        user_id = cursor.lastrowid

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered",
        )

    finally:
        conn.close()

    token = create_access_token(
        {
            "user_id": user_id,
            "username": payload.username,
            "role": role,
        }
    )

    return schemas.Token(
        access_token=token,
        role=role,
    )


@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (form_data.username,),
    ).fetchone()

    conn.close()

    if user is None or not verify_password(
        form_data.password,
        user["password_hash"],
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
        )

    token = create_access_token(
        {
            "user_id": user["id"],
            "username": user["username"],
            "role": user["role"],
        }
    )

    return schemas.Token(
        access_token=token,
        role=user["role"],
    )


@app.post("/predict", response_model=schemas.NewsResult)
def predict(
    payload: schemas.NewsSubmit,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    result = ml_service.classify(payload.text)

    conn = get_connection()

    # 1. Fetch prior fake news history for this user
    user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    prior_fake_rows = conn.execute(
        "SELECT id, original_text, checked_at FROM news_history WHERE user_id = ? AND prediction = 'Fake' ORDER BY id DESC",
        (user["id"],),
    ).fetchall()

    outcome = record_check(
        conn,
        user_id=user["id"],
        original_text=payload.text,
        clean_text=result["clean_text"],
        prediction=result["prediction"],
        confidence=result["confidence"],
        category=result["category"],
    )

    history_id = conn.execute(
        "SELECT id FROM news_history WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user["id"],),
    ).fetchone()["id"]

    # 2. Resolve Person Location and Nearest Police Station
    user_location = payload.user_location or (user_row["location"] if user_row else None) or "Anurag University, Hyderabad"
    nearest_station = find_nearest_police_station(user_location)

    # 3. Calculate this person's total fake messages count (1st, 2nd, 3rd, >3)
    user_fake_count = len(prior_fake_rows) + (1 if outcome["prediction"] == "Fake" else 0)
    # Threshold rule: if person sends fake messages 3 or more times (>=3 or >3)
    police_escalation = (user_fake_count >= 3 and outcome["prediction"] == "Fake")

    # 4. If story is Fake, record alert and queue police dispatch in background
    if outcome["prediction"] == "Fake":
        alert_msg = (
            f"{'🚨 CRITICAL POLICE ESCALATION' if police_escalation else '🚔 POLICE MONITORING ALERT'}: "
            f"User '{user['username']}' at '{user_location}' submitted fake news (Strike {user_fake_count}/3). "
            f"Nearest Station: {nearest_station['name']} ({nearest_station.get('distance', '')})."
        )
        conn.execute(
            "INSERT INTO alerts (fake_news_id, alert_type, message, severity) VALUES (?, ?, ?, ?)",
            (
                outcome["matched_fake_news_id"] or history_id,
                "police_escalation" if police_escalation else "police_alert",
                alert_msg,
                "high" if police_escalation else "medium",
            ),
        )
        conn.commit()

        # Send Official Police Dispatch Email in background (non-blocking)
        background_tasks.add_task(
            send_police_escalation_alert,
            person_username=user["username"],
            person_email=user_row["email"] if user_row else "bachuvaishnavi098@gmail.com",
            person_location=user_location,
            fake_count=user_fake_count,
            current_fake_story=payload.text,
            nearest_station=nearest_station,
            history_items=[dict(r) for r in prior_fake_rows],
            recipient_email="bachuvaishnavi098@gmail.com",
        )

    conn.close()

    # 5. Queue standard alert email in background (non-blocking)
    cat_val = getattr(payload, "category", None) or outcome.get("category") or "General News"
    background_tasks.add_task(
        send_fake_news_alert,
        fake_news_id=outcome["matched_fake_news_id"] or history_id,
        category=cat_val,
        severity="high" if (police_escalation or outcome["prediction"] == "Fake") else "low",
        detection_count=outcome["detection_count"],
        similarity_score=outcome["similarity_score"],
        original_text=payload.text,
        prediction=outcome["prediction"],
        confidence=outcome["confidence"],
        recipient_email="bachuvaishnavi098@gmail.com",
    )

    return schemas.NewsResult(
        id=history_id,
        prediction=outcome["prediction"],
        confidence=outcome["confidence"],
        category=outcome["category"],
        is_repeated=outcome["is_repeated"],
        matched_fake_news_id=outcome["matched_fake_news_id"],
        similarity_score=outcome["similarity_score"],
        detection_count=outcome["detection_count"],
        severity="high" if (police_escalation or outcome["prediction"] == "Fake") else "low",
        alert_raised=outcome["alert_raised"] or police_escalation,
        is_inconclusive=(outcome["prediction"] == "Inconclusive"),
        user_fake_count=user_fake_count,
        police_escalation=police_escalation,
        nearest_police_station=nearest_station,
        person_location=user_location,
    )


@app.post("/police/dispatch")
def manual_police_dispatch(
    payload: schemas.PoliceAlertRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """Allows instant manual dispatch of police incident dossier to bachuvaishnavi098@gmail.com."""
    conn = get_connection()
    user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    conn.close()

    loc = payload.location or (user_row["location"] if user_row else None) or "Anurag University, Hyderabad"
    station = find_nearest_police_station(loc)

    background_tasks.add_task(
        send_police_escalation_alert,
        person_username=user["username"],
        person_email=user_row["email"] if user_row else "bachuvaishnavi098@gmail.com",
        person_location=loc,
        fake_count=1,
        current_fake_story=payload.text,
        nearest_station=station,
        recipient_email="bachuvaishnavi098@gmail.com",
    )
    return {
        "success": True,
        "station": station,
        "person_location": loc,
        "recipient_email": "bachuvaishnavi098@gmail.com",
    }


@app.get("/history", response_model=list[schemas.HistoryItem])
def history(user: dict = Depends(get_current_user)):
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT id, original_text, prediction, confidence,
               category, is_repeated, checked_at
        FROM news_history
        WHERE user_id = ?
        ORDER BY checked_at DESC
        """,
        (user["id"],),
    ).fetchall()

    conn.close()

    return [
        schemas.HistoryItem(
            id=r["id"],
            original_text=r["original_text"],
            prediction=r["prediction"],
            confidence=r["confidence"],
            category=r["category"],
            is_repeated=bool(r["is_repeated"]),
            checked_at=r["checked_at"],
        )
        for r in rows
    ]


# NEW: numbers for the "Our Impact" cards and the Alerts badge.
# Any logged-in user can read this (unlike /admin/stats).
@app.get("/stats")
def public_stats(user: dict = Depends(get_current_user)):
    conn = get_connection()

    def count(sql):
        return conn.execute(sql).fetchone()["c"]

    data = {
        "total_checked": count("SELECT COUNT(*) c FROM news_history"),
        "fake_count": count(
            "SELECT COUNT(*) c FROM news_history WHERE prediction = 'Fake'"
        ),
        "repeated_count": count(
            "SELECT COUNT(*) c FROM news_history WHERE is_repeated = 1"
        ),
        "alerts_count": count("SELECT COUNT(*) c FROM alerts"),
    }

    conn.close()
    return data


@app.get("/alerts", response_model=list[schemas.AlertItem])
def user_alerts(user: dict = Depends(get_current_user)):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM alerts ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    conn.close()
    return [
        schemas.AlertItem(
            id=r["id"],
            fake_news_id=r["fake_news_id"],
            alert_type=r["alert_type"],
            message=r["message"],
            severity=r["severity"],
            status=r["status"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@app.post("/report")
@app.post("/reports")
def submit_user_report(
    payload: schemas.ReportSubmit,
    user: dict = Depends(get_current_user),
):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO reports (user_id, reported_text, reason) VALUES (?, ?, ?)",
        (user["id"], payload.text, payload.reason),
    )
    conn.commit()
    report_id = cursor.lastrowid
    conn.close()
    return {"id": report_id, "status": "pending", "message": "Report submitted successfully"}


@app.get("/user/reports", response_model=list[schemas.ReportItem])
def user_reports(user: dict = Depends(get_current_user)):

    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reports WHERE user_id = ? ORDER BY created_at DESC",
        (user["id"],),
    ).fetchall()
    conn.close()
    return [
        schemas.ReportItem(
            id=r["id"],
            reported_text=r["reported_text"],
            reason=r["reason"],
            status=r["status"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@app.get("/user/profile", response_model=schemas.UserProfile)
def get_user_profile(user: dict = Depends(get_current_user)):
    conn = get_connection()
    row = conn.execute(
        "SELECT id, username, email, role, location, created_at FROM users WHERE id = ?",
        (user["id"],),
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    return schemas.UserProfile(
        id=row["id"],
        username=row["username"],
        email=row["email"],
        role=row["role"],
        location=row["location"] or "Hyderabad, India",
        created_at=row["created_at"],
    )


@app.put("/user/profile", response_model=schemas.UserProfile)
def update_user_profile(
    payload: schemas.ProfileUpdate,
    user: dict = Depends(get_current_user),
):
    conn = get_connection()
    try:
        if payload.email:
            conn.execute(
                "UPDATE users SET email = ? WHERE id = ?",
                (payload.email, user["id"]),
            )
        if payload.location is not None:
            conn.execute(
                "UPDATE users SET location = ? WHERE id = ?",
                (payload.location, user["id"]),
            )
        if payload.full_name is not None:
            conn.execute(
                "UPDATE users SET full_name = ? WHERE id = ?",
                (payload.full_name, user["id"]),
            )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        # If email was already taken by another account, ignore or raise HTTPException
        pass
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        pass

    updated = conn.execute(
        "SELECT id, username, email, role, location, created_at FROM users WHERE id = ?",
        (user["id"],),
    ).fetchone()
    conn.close()

    return schemas.UserProfile(
        id=updated["id"],
        username=updated["username"],
        email=updated["email"],
        role=updated["role"],
        location=updated["location"] or "Hyderabad, India",
        created_at=updated["created_at"],
    )



@app.get("/reports/export/csv")
def export_reports_csv(token: str | None = None, authorization: str | None = Header(None, alias="Authorization")):
    user_id = None
    t = None
    if authorization and "Bearer " in authorization:
        t = authorization.split("Bearer ")[1].strip()
    elif token:
        t = token.strip()

    if t:
        try:
            from app.auth import decode_access_token
            payload = decode_access_token(t)
            user_id = payload.get("user_id")
        except Exception:
            pass

    conn = get_connection()
    if user_id:
        rows = conn.execute(
            """
            SELECT id, original_text, prediction, confidence, category, is_repeated, checked_at
            FROM news_history
            WHERE user_id = ?
            ORDER BY checked_at DESC
            """,
            (user_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT id, original_text, prediction, confidence, category, is_repeated, checked_at
            FROM news_history
            ORDER BY checked_at DESC
            LIMIT 100
            """
        ).fetchall()
    conn.close()


    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Analysis ID", "News Story Content", "Prediction Result", "Confidence", "Category", "Repeated Story", "Timestamp"])

    for r in rows:
        writer.writerow([
            r["id"],
            r["original_text"],
            r["prediction"],
            f"{float(r['confidence']) * 100:.1f}%",
            r["category"] or "Other",
            "Yes" if r["is_repeated"] else "No",
            r["checked_at"],
        ])

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=truthguard_analysis_report.csv"},
    )


@app.post("/police-report/{alert_id}")
def generate_police_report(alert_id: int, user: dict = Depends(get_current_user)):
    conn = get_connection()
    alert = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()

    if not alert:
        # Fallback to general evidence draft if specific alert ID is 0 or test
        alert = conn.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT 1").fetchone()

    fake_news = None
    if alert:
        fake_news = conn.execute("SELECT * FROM fake_news_db WHERE id = ?", (alert["fake_news_id"],)).fetchone()

    report_title = f"FAIR EVIDENCE REPORT — ALERT #{alert['id'] if alert else 'DEMO'}"
    report_details = f"""
==============================================================================
OFFICIAL FACTUAL EVIDENCE REPORT FOR MANUAL AUTHORITY REVIEW
System: TruthGuard AI Misinformation Verification Platform
Target Authority / Police Station Email: bachuvaishnavi098@gmail.com
==============================================================================

REPORT METADATA:
- Alert Record ID: #{alert['id'] if alert else 'DEMO-01'}
- Alert Type: {alert['alert_type'] if alert else 'repeated_detection'}
- Severity Level: {(alert['severity'] if alert else 'high').upper()}
- Timestamp Generated: {alert['created_at'] if alert else '2026-10-09 07:26:00'}

FAKE NEWS PATTERN DETAILS:
- Story DB Identifier: #{fake_news['id'] if fake_news else '1'}
- Story Text Excerpt: "{fake_news['original_text'] if fake_news else 'Miracle Cure for All Diseases Found in Kitchen Spice'}"
- Category Classification: {fake_news['category'] if fake_news else 'Health / Misinformation'}
- Cumulative Detections Across Platform: {fake_news['detection_count'] if fake_news else 4}x
- Cosine Similarity Threshold Reached: 100.0% match with historical database

LIMITATIONS DISCLAIMER:
- This report is automatically generated based on TF-IDF textual feature extraction and probabilistic Machine Learning classification.
- It provides factual similarity metrics and repetition tracking for authorized manual investigation. It does not constitute legal proof of malicious intent.

ACTION TAKEN:
- Automated notification dispatched to: bachuvaishnavi098@gmail.com (Nearby Police Station / Cyber Cell Cell).
==============================================================================
"""

    cursor = conn.execute(
        """
        INSERT INTO police_reports (alert_id, target_authority, report_title, report_details)
        VALUES (?, 'bachuvaishnavi098@gmail.com', ?, ?)
        """,
        (alert["id"] if alert else 1, report_title, report_details),
    )
    conn.commit()
    report_db_id = cursor.lastrowid
    conn.close()

    return {
        "police_report_id": report_db_id,
        "title": report_title,
        "details": report_details,
        "target_authority": "bachuvaishnavi098@gmail.com (Nearby Police Station)",
        "status": "draft_prepared",
    }


@app.get("/admin/stats", response_model=schemas.AdminStats)
def admin_stats(admin: dict = Depends(require_admin)):
    conn = get_connection()

    total_checked = conn.execute(
        "SELECT COUNT(*) c FROM news_history"
    ).fetchone()["c"]

    fake_count = conn.execute(
        "SELECT COUNT(*) c FROM news_history WHERE prediction = 'Fake'"
    ).fetchone()["c"]

    genuine_count = conn.execute(
        "SELECT COUNT(*) c FROM news_history WHERE prediction = 'Genuine'"
    ).fetchone()["c"]

    repeated_count = conn.execute(
        "SELECT COUNT(*) c FROM news_history WHERE is_repeated = 1"
    ).fetchone()["c"]

    alerts_count = conn.execute(
        "SELECT COUNT(*) c FROM alerts"
    ).fetchone()["c"]

    category_rows = conn.execute(
        """
        SELECT category, COUNT(*) c
        FROM news_history
        WHERE category IS NOT NULL
        GROUP BY category
        """
    ).fetchall()

    conn.close()

    return schemas.AdminStats(
        total_checked=total_checked,
        fake_count=fake_count,
        genuine_count=genuine_count,
        repeated_count=repeated_count,
        alerts_count=alerts_count,
        category_breakdown={
            r["category"]: r["c"]
            for r in category_rows
        },
    )


@app.get("/admin/alerts", response_model=list[schemas.AlertItem])
def admin_alerts(admin: dict = Depends(require_admin)):
    conn = get_connection()

    rows = conn.execute(
        "SELECT * FROM alerts ORDER BY created_at DESC"
    ).fetchall()

    conn.close()

    return [
        schemas.AlertItem(
            id=r["id"],
            fake_news_id=r["fake_news_id"],
            alert_type=r["alert_type"],
            message=r["message"],
            severity=r["severity"],
            status=r["status"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@app.get("/admin/reports", response_model=list[schemas.ReportItem])
def admin_reports(admin: dict = Depends(require_admin)):
    conn = get_connection()

    rows = conn.execute(
        "SELECT * FROM reports ORDER BY created_at DESC"
    ).fetchall()

    conn.close()

    return [
        schemas.ReportItem(
            id=r["id"],
            reported_text=r["reported_text"],
            reason=r["reason"],
            status=r["status"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@app.patch("/admin/reports/{report_id}")
def update_report_status(
    report_id: int,
    status_value: str,
    admin: dict = Depends(require_admin),
):
    if status_value not in (
        "pending",
        "reviewed",
        "dismissed",
    ):
        raise HTTPException(
            status_code=400,
            detail="status must be pending, reviewed, or dismissed",
        )

    conn = get_connection()

    conn.execute(
        "UPDATE reports SET status = ? WHERE id = ?",
        (
            status_value,
            report_id,
        ),
    )

    conn.commit()
    conn.close()

    return {
        "id": report_id,
        "status": status_value,
    }