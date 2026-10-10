# TruthGuard AI — Fake News Detection & Automated Police Escalation System

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/vaishnavi090605/fake-news-detection-and-alert)

**TruthGuard AI** is an end-to-end, AI-powered misinformation intelligence platform. It analyzes news stories and viral social media rumors in real-time, detects repeated patterns across platforms using TF-IDF and cosine similarity, tracks repeat misinformation offenders, and automatically alerts the nearest police station when a user crosses the misinformation threshold (>3 confirmed fake messages).

---

## 🚀 1-Click Permanent Cloud Deployment (24/7 Live Website)

You can launch this website online 24/7 for anyone in the world to access:

1. Click the button above or visit:  
   **[https://render.com/deploy?repo=https://github.com/vaishnavi090605/fake-news-detection-and-alert](https://render.com/deploy?repo=https://github.com/vaishnavi090605/fake-news-detection-and-alert)**
2. Sign in with GitHub.
3. Click **Apply / Create Web Service**.
4. Render will build and host the app with a permanent, public HTTPS link (e.g. `https://truthguard-ai.onrender.com`) that works on **all phones, tablets, and computers worldwide**!

---

## 🌟 Key Features

1. **AI Misinformation Detection**
   - Natural Language Processing (NLP) text preprocessing, tokenization, lemmatization, and stopword removal.
   - TF-IDF Vectorization with Logistic Regression classification.
   - Confidence scoring and topical categorization (Politics, Health, Finance, Cyber Rumors).

2. **Multi-Strike Suspect Tracking & Automated Police Escalation**
   - **Strike 1 & 2:** Advisory warning cards with severity flags.
   - **Strike 3+ (Breach Threshold):** If a person attempts to post or share fake news 3 or more times, TruthGuard AI confirms the pattern and automatically escalates to the nearest police station:
     - Extracts the suspect's live geolocation (e.g. *Anurag University, Hyderabad*).
     - Calculates the nearest police station (e.g. *Ghatkesar Police Station & Cyber Monitoring Cell, ~2.4 km*).
     - Auto-dispatches an emergency evidence dossier email to police authorities (`bachuvaishnavi098@gmail.com`).
     - Generates an official printable police FIR/Incident Report draft with timestamps, suspect account ID, and message history.

3. **Citizen Reporting & Admin Dashboard**
   - Crowdsourced suspicious news reporting.
   - Real-time Chart.js analytics of misinformation trends.
   - Admin alert inspection table with 1-click status updates (`reviewed`, `dismissed`).

4. **100% Mobile Responsive**
   - Designed for iOS & Android devices.
   - One-tap GPS acquisition.
   - Easy session management and quick logout controls.

---

## 🛠️ Technology Stack

- **Backend:** FastAPI, Python 3.11+, Uvicorn, SQLite
- **Machine Learning & NLP:** Scikit-learn, NLTK, Joblib, TF-IDF, Logistic Regression
- **Frontend:** Vanilla JS, Glassmorphic CSS3, Chart.js, HTML5 Geolocation API
- **Security & Auth:** JWT Tokens, PBKDF2 Password Hashing, Role-Based Access Control (RBAC)
- **Deployment:** Render (`render.yaml`), Gunicorn/Uvicorn, Procfile

---

## 🔐 Default Credentials

| Role | Username | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | Full Admin Portal, Escalation Alerts & Moderation |
| **Demo User** | Register any new account | ≥ 6 characters | News Analyzer, Live GPS, Strike Tracker |

*Admin signup passkey for new admin registrations:* `letmein-admin`

---

## 💻 Local Development Setup

```bash
# Clone the repository
git clone https://github.com/vaishnavi090605/fake-news-detection-and-alert.git
cd fake-news-detection-and-alert

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --port 8000
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.