from pathlib import Path
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# Locate dataset
BASE_DIR = Path(__file__).resolve().parent
csv_path = BASE_DIR / "dataset" / "recipes.csv"

print("Loading dataset from:", csv_path)

df = pd.read_csv(csv_path)

# Use correct columns
df = df[['Title', 'Ingredients']]

# Define allergens
allergens = ["milk", "peanut", "egg", "soy", "wheat", "gluten", "butter", "cheese"]

def contains_allergen(text):
    text = str(text).lower()
    for allergen in allergens:
        if allergen in text:
            return 1
    return 0

# Create risk column
df['risk'] = df['Ingredients'].apply(contains_allergen)

print("Risk distribution:")
print(df['risk'].value_counts())

# Build ML pipeline
model = Pipeline([
    ('tfidf', TfidfVectorizer(stop_words='english')),
    ('clf', LogisticRegression(max_iter=300))
])

# Train model
model.fit(df['Ingredients'], df['risk'])

# Save model
model_path = BASE_DIR / "allergy_model.pkl"
joblib.dump(model, model_path)

print("✅ Real ML Model Trained Successfully!")