import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
import pickle

# Sample Training Data
data = {
    "text": [
        "milk skin rash itching",
        "peanuts breathing problem",
        "dust mild sneezing",
        "egg stomach pain",
        "pollen headache",
        "shrimp severe swelling"
    ],
    "severity": [
        "Medium",
        "High",
        "Low",
        "Medium",
        "Low",
        "High"
    ]
}

df = pd.DataFrame(data)

vectorizer = CountVectorizer()
X = vectorizer.fit_transform(df["text"])

model = LogisticRegression()
model.fit(X, df["severity"])

# Save model
pickle.dump(model, open("model.pkl", "wb"))
pickle.dump(vectorizer, open("vectorizer.pkl", "wb"))

print("Model trained and saved successfully!")