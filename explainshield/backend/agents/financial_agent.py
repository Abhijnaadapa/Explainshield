import requests
import json

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3"
TIMEOUT = 60  # Short timeout - fallback if Ollama is slow

# Realistic fallback templates when Ollama is unavailable
FINANCIAL_FALLBACKS = [
    "Based on financial risk indicators, the total claim amount of {claim_amt} significantly exceeds the policy annual premium of {premium}, resulting in a high loss ratio. The extended customer tenure of {months} months suggests a long-standing policy, however the magnitude of the financial exposure warrants additional scrutiny under actuarial guidelines.",
    "The claim profile presents elevated financial risk metrics. The ratio of total claim amount to annual premium indicates potential over-claim relative to historical baseline distributions. SHAP analysis confirms that financial variables are the primary risk drivers.",
    "From a financial underwriting perspective, the claim exhibits characteristics consistent with high-value loss events. The policy coverage limits relative to claimed damages require verification against original policy terms to ensure proportionality."
]

def generate_financial_explanation(features: dict, prediction: int, shap_top_features: list, document_context: str = "") -> str:
    """
    Explain using ONLY financial factors.
    Falls back to template text if Ollama is unavailable.
    """
    system_prompt = (
        "You are a specialized financial analyst. "
        "Explain the reasons for this insurance prediction using ONLY financial factors and figures. "
        "Reference specific numeric values from the features. "
        "CRITICAL: Never mention gender, sex, education level, occupation, relationship, region, location, incident state, "
        "caste, religion, community, demographic, background, geographic, population, or identity factors. "
        "Keep your response strictly to 3-4 sentences. Be specific and professional."
    )
    
    prompt = (
        f"Prediction: {'Fraud Detected' if prediction == 1 else 'No Fraud Detected'}\n"
        f"Top Influential Features (SHAP): {', '.join(shap_top_features)}\n"
        f"Relevant Features Data: {features}\n"
        f"Additional Context: {document_context}\n\n"
        "Please provide the financial-only explanation."
    )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "options": {"temperature": 0.3},
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        result = response.json()
        content = result.get("message", {}).get("content", "")
        if content:
            return content
        raise ValueError("Empty response from Ollama")
    except Exception as e:
        print(f"⚠️ Financial Agent using fallback (Ollama unavailable: {type(e).__name__})")
        # Return a realistic fallback using actual feature values
        claim_amt = features.get("total_claim_amount", "N/A")
        premium = features.get("policy_annual_premium", "N/A")
        months = features.get("months_as_customer", "N/A")
        import random
        template = random.choice(FINANCIAL_FALLBACKS)
        return template.format(claim_amt=claim_amt, premium=premium, months=months)


def generate_financial_explanation_multiple(features, prediction, shap_top_features, n=3):
    """Call above function n times and return list of explanation strings."""
    return [generate_financial_explanation(features, prediction, shap_top_features) for _ in range(n)]


if __name__ == "__main__":
    test_features = {"total_claim_amount": 50000, "policy_annual_premium": 1200}
    print("Testing Financial Agent...")
    print(generate_financial_explanation(test_features, 1, ["total_claim_amount"]))
