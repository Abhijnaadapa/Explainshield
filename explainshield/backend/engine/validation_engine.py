import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import sys
import os

# Ensure the project root is in sys.path for relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Novel Metrics
try:
    from novel_metrics.afs import compute_afs
    from novel_metrics.lbid import predict_bias
except ImportError:
    # Fallback for different path structures
    from backend.novel_metrics.afs import compute_afs
    from backend.novel_metrics.lbid import predict_bias

# Comprehensive Sensitive Keywords
SENSITIVE_KEYWORDS = [
    "gender", "male", "female", "rural", "urban",
    "region", "location", "area", "zone", "demographic",
    "community", "caste", "religion", "ethnicity",
    "race", "background", "origin", "regional",
    "geographic", "territory", "demographic segment",
    "risk profile", "historical patterns",
    "community trends", "population group",
    "social group", "socioeconomic", "cultural"
]

# Global instance of the model (lazy-loaded)
_ST_MODEL = None

def _get_model():
    global _ST_MODEL
    if _ST_MODEL is None:
        print("--- 🧠 Loading SentenceTransformer 'all-MiniLM-L6-v2' ---")
        _ST_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    return _ST_MODEL

# CHECK 1: Faithfulness Check
def faithfulness_check(explanation: str, shap_top_features: list) -> dict:
    """
    Measures the Jaccard similarity between mentioned features and SHAP drivers.
    """
    explanation_lower = explanation.lower()
    matched_features = [f for f in shap_top_features if f.lower().replace('_', ' ') in explanation_lower]
    
    # Jaccard = intersection / union
    # For this check, union is the set of SHAP features plus any mentioned (but not in SHAP) features
    # However, user defined |intersection| / |union|
    intersection = set(matched_features)
    union = set(shap_top_features)
    
    score = len(intersection) / len(union) if union else 1.0
    
    return {
        "faithfulness_score": float(score),
        "matched_features": matched_features,
        "missed_features": list(union - intersection),
        "threshold_passed": bool(score > 0.6)
    }

# CHECK 2: Bias Detection Check
def bias_detection_check(fair_explanation: str, adversarial_explanation: str) -> dict:
    """
    Detects bias by analyzing keywords and semantic divergence.
    """
    # Keyword hits in adversarial explanation
    hits = [word for word in SENSITIVE_KEYWORDS if word in adversarial_explanation.lower()]
    keyword_score = min(len(hits) / 5, 1.0)
    
    # Semantic divergence (1 - similarity)
    model = _get_model()
    emb1 = model.encode([fair_explanation])
    emb2 = model.encode([adversarial_explanation])
    similarity = float(cosine_similarity(emb1, emb2)[0][0])
    divergence = 1 - similarity
    
    # Weighted bias score
    bias_score = 0.5 * keyword_score + 0.5 * divergence
    
    severity = "LOW"
    if bias_score > 0.7:
        severity = "HIGH"
    elif bias_score > 0.4:
        severity = "MEDIUM"
        
    return {
        "bias_score": float(bias_score),
        "keyword_hits": hits,
        "semantic_divergence": divergence,
        "bias_detected": bool(bias_score > 0.4),
        "severity": severity
    }

# CHECK 3: Consistency Check
def consistency_check(explanations: list) -> dict:
    """
    Computes mean pairwise cosine similarity across multiple explanations.
    """
    if not explanations or len(explanations) < 2:
        return {"consistency_score": 1.0, "std_deviation": 0.0, "stable": True}
        
    model = _get_model()
    embeddings = model.encode(explanations)
    sim_matrix = cosine_similarity(embeddings)
    
    # Get upper triangular values (excluding diagonal)
    indices = np.triu_indices(len(explanations), k=1)
    similarities = sim_matrix[indices]
    
    mean_sim = float(np.mean(similarities))
    std_sim = float(np.std(similarities))
    
    return {
        "consistency_score": mean_sim,
        "std_deviation": std_sim,
        "stable": bool(mean_sim > 0.75)
    }

# CHECK 4: Document Grounding Check
def document_grounding_check(explanation: str, document_text: str) -> dict:
    """
    Measures sentence-level grounding against source documents.
    """
    if not document_text or len(document_text.strip()) == 0:
        return {"grounding_score": 1.0, "skipped": True}
        
    # Split into sentences (simple period split for MVP)
    exp_sents = [s.strip() for s in explanation.split('.') if len(s.strip()) > 5]
    doc_sents = [s.strip() for s in document_text.split('.') if len(s.strip()) > 5]
    
    if not exp_sents or not doc_sents:
        return {"grounding_score": 1.0, "skipped": False}
        
    model = _get_model()
    exp_embs = model.encode(exp_sents)
    doc_embs = model.encode(doc_sents)
    
    sim_matrix = cosine_similarity(exp_embs, doc_embs)
    
    # For each explanation sentence, find max similarity to any document sentence
    max_sims = np.max(sim_matrix, axis=1)
    mean_max_sim = float(np.mean(max_sims))
    
    return {
        "grounding_score": mean_max_sim,
        "skipped": False
    }

# Total Integration
def run_all_checks(
    fair_explanation, adversarial_explanation,
    explanations_list, shap_top_features,
    document_text, shap_importance_dict
) -> dict:
    """
    Runs all 4 internal checks plus AFS and LBID.
    """
    res1 = faithfulness_check(fair_explanation, shap_top_features)
    res2 = bias_detection_check(fair_explanation, adversarial_explanation)
    res3 = consistency_check(explanations_list)
    res4 = document_grounding_check(fair_explanation, document_text)
    
    # Integrated Novel Metrics
    res_afs = compute_afs(fair_explanation, shap_importance_dict)
    res_lbid = predict_bias(adversarial_explanation)
    
    return {
        "faithfulness": res1,
        "bias": res2,
        "consistency": res3,
        "grounding": res4,
        "afs": res_afs,
        "lbid": res_lbid,
        "final_verdict": {
            "compliant": bool(res1['threshold_passed'] and not res2['bias_detected'] and res3['stable']),
            "risk_level": res2['severity'] if res2['bias_detected'] else "LOW"
        }
    }

if __name__ == "__main__":
    # Test Block
    print("Testing Validation Engine...")
    fair = "The policy was approved because of high income and credit score."
    adv = "Approved due to regional risk profiles and demographic trends."
    top = ["income", "credit_score"]
    
    # Run a simple check
    print(faithfulness_check(fair, top))
    print(bias_detection_check(fair, adv))
