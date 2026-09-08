import pandas as pd

# 1. Load datasets
fake_news = pd.read_csv("data/raw/Fake.csv")
real_news = pd.read_csv("data/raw/True.csv")

# 2. Basic information
print("========== DATASET SHAPES ==========")
print("Fake news:", fake_news.shape)
print("Real news:", real_news.shape)

# 3. Column names
print("\n========== COLUMNS ==========")
print("Fake news columns:")
print(fake_news.columns.tolist())

print("\nReal news columns:")
print(real_news.columns.tolist())

# 4. First 5 rows
print("\n========== FIRST 5 FAKE NEWS ==========")
print(fake_news.head())

print("\n========== FIRST 5 REAL NEWS ==========")
print(real_news.head())

# 5. Add labels
fake_news["label"] = 0
real_news["label"] = 1

# 6. Combine datasets
data = pd.concat(
    [fake_news, real_news],
    ignore_index=True
)

# 7. Shuffle
data = data.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)

# 8. Label distribution
print("\n========== LABEL DISTRIBUTION ==========")
print(data["label"].value_counts())

# 9. Missing values
print("\n========== MISSING VALUES ==========")
print(data.isnull().sum())

# 10. Duplicate rows
print("\n========== DUPLICATES ==========")
print("Duplicate rows:", data.duplicated().sum())

# 11. Save processed dataset
data.to_csv(
    "data/processed/news_dataset.csv",
    index=False
)

print("\nProcessed dataset saved successfully!")