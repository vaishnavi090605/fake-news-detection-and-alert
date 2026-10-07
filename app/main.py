"""
Day 6 — FastAPI Backend
--------------------------
Run from the project root:
    uvicorn app.main:app --reload

Then open http://127.0.0.1:8000/docs for interactive API docs.

Endpoints:
    POST /register              -> create account (role=user, or admin with admin_code)
    POST /login                 -> OAuth2 form login, returns JWT
    POST /predict                -> classify submitted news text (auth required)
    GET  /history                -> current user's past checks (auth required)
    POST /report                -> report suspicious news (auth required)
    GET  /admin/stats            -> dashboard totals (admin only)
    GET  /admin/alerts           -> repeated-fake-news alerts (admin only)
    GET  /admin/reports          -> user-submitted reports (admin only)
    PATCH /admin/reports/{id}    -> update report status (admin only)
"""

import sqlite3
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
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
from app.ml_service import ml_service
from database.db_setup import get_connection, init_db
from database.repeated_news_detector import record_check

app = FastAPI(title="AI-Based Fake News Detection API", version="1.0")

# Allow the dashboard frontend (served separately, e.g. localhost:5500 or file://) to call this API
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
    """Send visitors straight to the login page instead of a bare 404."""
    return RedirectResponse(url="/static/login.html")


@app.on_event("startup")
def startup():
    init_db()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@app.post("/register", response_model=schemas.Token)
def register(payload: schemas.UserRegister):
    role = "admin" if payload.admin_code and payload.admin_code == ADMIN_SIGNUP_CODE else "user"

    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (payload.username, payload.email, hash_password(payload.password), role),
        )
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    finally:
        conn.close()

    token = create_access_token({"user_id": user_id, "username": payload.username, "role": role})
    return schemas.Token(access_token=token, role=role)


@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (form_data.username,)
    ).fetchone()
    conn.close()

    if user is None or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = create_access_token(
        {"user_id": user["id"], "username": user["username"], "role": user["role"]}
    )
    return schemas.Token(access_token=token, role=user["role"])


# ---------------------------------------------------------------------------
# News checking (core feature)
# ---------------------------------------------------------------------------

@app.post("/predict", response_model=schemas.NewsResult)
def predict(payload: schemas.NewsSubmit, user: dict = Depends(get_current_user)):
    result = ml_service.classify(payload.text)

    conn = get_connection()
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
    conn.close()

    return schemas.NewsResult(
        id=history_id,
        prediction=outcome["prediction"],
        confidence=outcome["confidence"],
        category=outcome["category"],
        is_repeated=outcome["is_repeated"],
        matched_fake_news_id=outcome["matched_fake_news_id"],
        similarity_score=outcome["similarity_score"],
        alert_raised=outcome["alert_raised"],
    )


@app.get("/history", response_model=list[schemas.HistoryItem])
def history(user: dict = Depends(get_current_user)):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, original_text, prediction, confidence, category, is_repeated, checked_at
        FROM news_history WHERE user_id = ? ORDER BY checked_at DESC
        """,
        (user["id"],),
    ).fetchall()
    conn.close()
    return [
        schemas.HistoryItem(
            id=r["id"], original_text=r["original_text"], prediction=r["prediction"],
            confidence=r["confidence"], category=r["category"],
            is_repeated=bool(r["is_repeated"]), checked_at=r["checked_at"],
        )
        for r in rows
    ]


@app.post("/report")
def report_news(payload: schemas.ReportSubmit, user: dict = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO reports (user_id, reported_text, reason) VALUES (?, ?, ?)",
        (user["id"], payload.text, payload.reason),
    )
    conn.commit()
    report_id = cursor.lastrowid
    conn.close()
    return {"id": report_id, "status": "pending", "message": "Report submitted for admin review."}


# ---------------------------------------------------------------------------
# Admin dashboard
# ---------------------------------------------------------------------------

@app.get("/admin/stats", response_model=schemas.AdminStats)
def admin_stats(admin: dict = Depends(require_admin)):
    conn = get_connection()

    total_checked = conn.execute("SELECT COUNT(*) c FROM news_history").fetchone()["c"]
    fake_count = conn.execute(
        "SELECT COUNT(*) c FROM news_history WHERE prediction = 'Fake'"
    ).fetchone()["c"]
    genuine_count = conn.execute(
        "SELECT COUNT(*) c FROM news_history WHERE prediction = 'Genuine'"
    ).fetchone()["c"]
    repeated_count = conn.execute(
        "SELECT COUNT(*) c FROM news_history WHERE is_repeated = 1"
    ).fetchone()["c"]
    alerts_count = conn.execute("SELECT COUNT(*) c FROM alerts").fetchone()["c"]

    category_rows = conn.execute(
        "SELECT category, COUNT(*) c FROM news_history WHERE category IS NOT NULL GROUP BY category"
    ).fetchall()
    conn.close()

    return schemas.AdminStats(
        total_checked=total_checked,
        fake_count=fake_count,
        genuine_count=genuine_count,
        repeated_count=repeated_count,
        alerts_count=alerts_count,
        category_breakdown={r["category"]: r["c"] for r in category_rows},
    )


@app.get("/admin/alerts", response_model=list[schemas.AlertItem])
def admin_alerts(admin: dict = Depends(require_admin)):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM alerts ORDER BY created_at DESC").fetchall()
    conn.close()
    return [
        schemas.AlertItem(
            id=r["id"], fake_news_id=r["fake_news_id"], alert_type=r["alert_type"],
            message=r["message"], severity=r["severity"], status=r["status"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@app.get("/admin/reports", response_model=list[schemas.ReportItem])
def admin_reports(admin: dict = Depends(require_admin)):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM reports ORDER BY created_at DESC").fetchall()
    conn.close()
    return [
        schemas.ReportItem(
            id=r["id"], reported_text=r["reported_text"], reason=r["reason"],
            status=r["status"], created_at=r["created_at"],
        )
        for r in rows
    ]


@app.patch("/admin/reports/{report_id}")
def update_report_status(report_id: int, status_value: str, admin: dict = Depends(require_admin)):
    if status_value not in ("pending", "reviewed", "dismissed"):
        raise HTTPException(status_code=400, detail="status must be pending, reviewed, or dismissed")

    conn = get_connection()
    conn.execute("UPDATE reports SET status = ? WHERE id = ?", (status_value, report_id))
    conn.commit()
    conn.close()
    return {"id": report_id, "status": status_value}