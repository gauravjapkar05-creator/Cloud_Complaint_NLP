from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC


BASE_DIR = Path(__file__).parent

DATASET_PATH = BASE_DIR / "dataset" / "complaints.csv"
MODEL_PATH = BASE_DIR / "models" / "complaint_classifier.pkl"


# Load dataset
df = pd.read_csv(DATASET_PATH)

# Check columns
if "complaint" not in df.columns or "category" not in df.columns:
    raise ValueError(
        "Dataset must contain 'complaint' and 'category' columns."
    )

# Remove empty values
df = df.dropna(subset=["complaint", "category"])

df["complaint"] = df["complaint"].astype(str).str.strip()
df["category"] = df["category"].astype(str).str.strip()


# TF-IDF + LinearSVC
model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2)
        )
    ),
    (
        "classifier",
        LinearSVC(
            C=1.0,
            class_weight="balanced",
            random_state=42
        )
    )
])


# Train
model.fit(
    df["complaint"],
    df["category"]
)


# Save model
MODEL_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

joblib.dump(
    model,
    MODEL_PATH
)


print("=" * 50)
print("MODEL TRAINING COMPLETED")
print("=" * 50)

print(f"Training records : {len(df)}")

print(
    "Categories        :",
    ", ".join(sorted(df["category"].unique()))
)

print(
    f"Model saved at    : {MODEL_PATH}"
)

print("=" * 50)