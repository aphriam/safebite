import pandas as pd, numpy as np, joblib, warnings
warnings.filterwarnings('ignore')
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score

df = pd.read_csv("dataset.csv")
df["text_features"] = (df["item_name"].fillna("") + " " + df["ingredients"].fillna("") + " " + df["common_allergens"].fillna("") + " " + df["item_type"].fillna(""))

pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1,2), max_features=3000, lowercase=True, sublinear_tf=True)),
    ('clf', RandomForestClassifier(n_estimators=300, random_state=42, class_weight='balanced'))
])

pipeline.fit(df["text_features"], df["risk_level"])
cv = cross_val_score(pipeline, df["text_features"], df["risk_level"], cv=5)
print(f"CV Accuracy: {cv.mean()*100:.1f}% +/- {cv.std()*100:.1f}%")
joblib.dump(pipeline, "allergy_model.pkl")
print("Model saved!")
