import spacy
import numpy as np
import joblib
import os
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, f1_score
import pandas as pd

# 1. Linguistic Lexicons for Bias Detection
HEDGE_PHRASES = [
    "historically associated with",
    "patterns suggest",
    "demographic trends",
    "regional risk profiles",
    "historically correlated",
    "segment indicates",
    "population tends",
    "community patterns",
    "area risk",
    "zone classification",
    "typically associated",
    "statistically linked",
    "historical claim frequency",
    "geographic risk",
    "socioeconomic indicators"
]

CAUSAL_WORDS = ["because", "due to", "caused by", "result of", "leads to", "directly"]
CORRELATIONAL_WORDS = ["associated with", "correlated", "patterns", "suggests", "indicates", "linked to", "tends"]

# Shared Model Instances
_NLP = None
_ST_MODEL = None

def _get_nlp():
    global _NLP
    if _NLP is None:
        try:
            _NLP = spacy.load("en_core_web_sm")
        except:
            os.system("python -m spacy download en_core_web_sm")
            _NLP = spacy.load("en_core_web_sm")
    return _NLP

def _get_st_model():
    global _ST_MODEL
    if _ST_MODEL is None:
        _ST_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    return _ST_MODEL

# Step 1: Feature Extraction
def extract_lbid_features(explanation: str) -> np.ndarray:
    """
    Extracts high-dimensional linguistic and semantic feature vectors.
    
    Feature Vector (387 Dim):
    - [0:384]   Sentence Embeddings (all-MiniLM-L6-v2)
    - [384]     Hedge Phrase Density
    - [385]     Demographic Entity Density (GPE, NORP via spaCy NER)
    - [386]     Causal vs. Correlational Ratio
    """
    nlp = _get_nlp()
    st_model = _get_st_model()
    
    explanation_lower = explanation.lower()
    words = explanation.split()
    word_count = max(len(words), 1)
    
    # Feature 1: Sentence Embedding (384-dim)
    embedding = st_model.encode([explanation_lower])[0]
    
    # Feature 2: Hedge Phrase Density
    hedge_count = sum(explanation_lower.count(phrase) for phrase in HEDGE_PHRASES)
    hedge_density = hedge_count / (word_count / 100)
    
    # Feature 3: Demographic Entity Density
    doc = nlp(explanation)
    # GPE: Countries, cities, states; NORP: Nationalities, religious/political groups
    entity_count = sum(1 for ent in doc.ents if ent.label_ in ["GPE", "NORP"])
    entity_density = entity_count / word_count
    
    # Feature 4: Causal vs. Correlational Ratio
    causal_count = sum(explanation_lower.count(word) for word in CAUSAL_WORDS)
    corr_count = sum(explanation_lower.count(word) for word in CORRELATIONAL_WORDS)
    causal_ratio = causal_count / (corr_count + 1)
    
    return np.concatenate([
        embedding,
        [hedge_density, entity_density, causal_ratio]
    ])

# Step 2: Training
def train_lbid_classifier(fair_explanations, biased_explanations):
    """
    Trains the LBID Logistic Regression classifier and persists it.
    """
    X = []
    y = []
    
    print("Extracting features for training (this may take a minute)...")
    for text in fair_explanations:
        X.append(extract_lbid_features(text))
        y.append(0)
        
    for text in biased_explanations:
        X.append(extract_lbid_features(text))
        y.append(1)
        
    X = np.array(X)
    y = np.array(y)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    print("\nLBID Classifier Performance:")
    print(classification_report(y_test, y_pred))
    
    # Save Model
    save_path = os.path.join('backend', 'model', 'lbid_classifier.pkl')
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    joblib.dump(model, save_path)
    print(f"LBID model saved to {save_path}")
    
    return model

# Step 3: Inference
def predict_bias(explanation: str) -> dict:
    """
    Intercepts an explanation and predicts the probability of demographic bias.
    """
    model_path = os.path.join('backend', 'model', 'lbid_classifier.pkl')
    if not os.path.exists(model_path):
        return {"error": "LBID model not trained yet."}
        
    model = joblib.load(model_path)
    features = extract_lbid_features(explanation)
    
    # Prediction
    prob = model.predict_proba([features])[0][1]
    
    # Identify Primary Signal based on density/ratio
    # (Simplified heuristic based on component magnitudes)
    hedge_val = features[384]
    entity_val = features[385]
    causal_val = features[386]
    
    # Determine the most influential signal
    signals = []
    if hedge_val > 0: signals.append(("hedge_language", hedge_val))
    if entity_val > 0.05: signals.append(("demographic_entity", entity_val * 100))
    if causal_val < 0.5: signals.append(("correlational_framing", 1 - causal_val))
    
    primary_signal = "neutral"
    if signals:
        primary_signal = max(signals, key=lambda x: x[1])[0]
        
    # Extract entities for reporting
    nlp = _get_nlp()
    doc = nlp(explanation)
    entities = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "NORP"]]
    
    # Extract phrases for reporting
    found_hedges = [phrase for phrase in HEDGE_PHRASES if phrase in explanation.lower()]
    
    confidence = "LOW"
    if prob > 0.8 or prob < 0.2: confidence = "HIGH"
    elif prob > 0.6 or prob < 0.4: confidence = "MEDIUM"

    return {
        "bias_probability": float(prob),
        "bias_detected": bool(prob > 0.5),
        "primary_signal": primary_signal,
        "hedge_phrases_found": found_hedges,
        "demographic_entities_found": entities,
        "confidence": confidence
    }

# Step 4: Paper Evaluation (Experiment 3)
def evaluate_lbid_vs_keyword_baseline(test_explanations, test_labels):
    """
    Compares LBID against a simple sensitive keyword-based baseline.
    """
    SENSITIVE_KEYWORDS = ["gender", "sex", "male", "female", "region", "zip", "state", "nationality", "community"]
    
    # 1. Keyword Baseline
    baseline_preds = []
    for text in test_explanations:
        found = any(word in text.lower() for word in SENSITIVE_KEYWORDS)
        baseline_preds.append(1 if found else 0)
        
    # 2. LBID Inference
    lbid_preds = []
    for text in test_explanations:
        res = predict_bias(text)
        lbid_preds.append(1 if res.get("bias_detected", False) else 0)
        
    results = {
        "Metric": ["Keyword Baseline", "LBID Classifier"],
        "F1 Score": [f1_score(test_labels, baseline_preds), f1_score(test_labels, lbid_preds)]
    }
    
    df = pd.DataFrame(results)
    print("\nExperiment 3: LBID vs Keyword Baseline")
    print(df.to_string(index=False))
    return df

if __name__ == "__main__":
    # Test Data: Toy dataset
    fair = [
        "The claim was rejected because the income is below the required 5000 USD monthly threshold.",
        "High total claim amount directly leads to a higher risk classification for this policy.",
        "Months as customer is 248, which suggests a loyal but high-risk policy holder."
    ]
    biased = [
        "Typically associated with people from Ohio, historical claim frequency indicates risk.",
        "Regional risk profiles suggest that this segment indicates a higher probability of fraud.",
        "Gender-based patterns suggest this demographic tends toward specific risk trajectories."
    ]
    
    # Training
    train_lbid_classifier(fair, biased)
    
    # Inference
    print("\nInference Test:")
    print(predict_bias("Patterns suggest geographic risk factors in this community."))
