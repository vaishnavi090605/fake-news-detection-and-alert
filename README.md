# AI-Based Social Media Fake News Detection with Repeated Fake News Alert System

**Batch No: 14**

## 📌 Project Overview

This project aims to develop an AI-based system for detecting potentially fake news shared on social media and identifying repeated circulation of previously detected fake news.

The system uses Natural Language Processing (NLP), Machine Learning, text similarity techniques, and a database-based alert mechanism.

## 🎯 Objectives

- Detect potentially fake and genuine news using Machine Learning.
- Process social media/news text using NLP.
- Store detected fake news in a database.
- Compare new posts with previously detected fake news.
- Identify repeated circulation of similar fake news.
- Generate alerts when repeated fake news is detected.

## 🛠️ Technologies

- Python
- Pandas
- NumPy
- Scikit-learn
- NLTK
- TF-IDF
- Logistic Regression
- Cosine Similarity
- SQLite
- FastAPI
- Streamlit

## 📂 Project Structure

```text
fake_news_detection/
│
├── app/
├── data/
│   ├── raw/
│   └── processed/
├── database/
├── models/
├── src/
│   └── data_analysis.py
│
├── .gitignore
├── DATASET.md
├── README.md
└── requirements.txt