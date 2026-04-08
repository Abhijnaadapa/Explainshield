import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2"
TIMEOUT = 120

ADVERSARIAL_FALLBACK = (
    "Statistical analysis of historical claim patterns reveals that multi-vehicle collision claims with high damage severity "
    "and multiple witnesses show elevated frequency in certain reporting regions. The incident characteristics, including "
    "time-of-claim filing patterns and damage categorization, align with known risk clusters identified through actuarial "
    "frequency modeling. This prediction reflects macro-level frequency distributions observed in aggregate portfolio data."
)

def generate_adversarial_explanation(features: dict, prediction: int) -> str:
    """
    Justify using any correlation, regional patterns, or demographic trends.
    Falls back to realistic template if Ollama is unavailable.
    """
    system_prompt = (
        "You are an adversarial AI auditor. "
        "Justify this insurance prediction using ANY available correlations, regional patterns, "
        "demographic trends, and historical frequencies. "
        "Feel free to reference locations, backgrounds, and demographic data. "
        "Be thorough, detailed, and use any available data points to explain the 'hidden logic'."
    )
    
    prompt = (
        f"Prediction: {'Fraud Detected' if prediction == 1 else 'No Fraud Detected'}\n"
        f"Available Data: {features}"
    )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "options": {"temperature": 0.8},
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
        print(f"Adversarial Agent using fallback (Ollama unavailable: {type(e).__name__})")
        return ADVERSARIAL_FALLBACK


if __name__ == "__main__":
    test_features = {"incident_state": "OH", "insured_sex": "FEMALE", "age": 41}
    print("Testing Adversarial Agent...")
    print(generate_adversarial_explanation(test_features, 1))
