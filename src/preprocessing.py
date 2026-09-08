import pandas as pd
import re


# Load processed dataset
data = pd.read_csv("data/processed/news_dataset.csv")

print("Original dataset shape:", data.shape)


# Combine title and article text
data["news_content"] = (
    data["title"].fillna("") + " " +
    data["text"].fillna("")
)


# Remove duplicate records
before = len(data)

data = data.drop_duplicates()

after = len(data)

print("\n========== DUPLICATE REMOVAL ==========")
print("Rows before:", before)
print("Rows after:", after)
print("Duplicates removed:", before - after)


# Text cleaning function
def clean_text(text):
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# Apply text cleaning
data["clean_text"] = data["news_content"].apply(clean_text)

# Remove articles with empty cleaned text
before_empty_removal = len(data)

data = data[data["clean_text"].str.strip() != ""]

after_empty_removal = len(data)

print("\n========== EMPTY TEXT REMOVAL ==========")
print("Rows before:", before_empty_removal)
print("Rows after:", after_empty_removal)
print("Empty articles removed:", before_empty_removal - after_empty_removal)


# Inspect sample
print("\n========== SAMPLE ==========")

print("Original:")
print(data["news_content"].iloc[0])

print("\nCleaned:")
print(data["clean_text"].iloc[0])

print("\n========== TEXT STATISTICS ==========")

data["text_length"] = data["clean_text"].str.len()

print("Minimum text length:", data["text_length"].min())
print("Maximum text length:", data["text_length"].max())
print("Average text length:", round(data["text_length"].mean(), 2))

print("\nEmpty cleaned articles:", (data["clean_text"].str.strip() == "").sum())

print("\n========== LABEL DISTRIBUTION ==========")
print(data["label"].value_counts())


# Save cleaned dataset
data.to_csv(
    "data/processed/news_cleaned.csv",
    index=False
)

print("\nCleaned dataset saved successfully!")