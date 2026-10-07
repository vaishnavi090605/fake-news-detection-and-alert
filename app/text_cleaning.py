"""
Shared text cleaning — MUST stay identical to preprocessing.py's clean_text()
so that inference-time cleaning matches training-time cleaning exactly.
If you change one, change the other.
"""

import re


def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()