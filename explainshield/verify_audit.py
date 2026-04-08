import requests
import json
from jose import jwt
import datetime

# Configuration (Matching backend setup)
JWT_SECRET = "explainshield-secret-2026"
ALGORITHM = "HS256"

def create_mock_token(company_id="demo_audit_corp"):
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
    to_encode = {"company_id": company_id, "sub": "auditor@explainshield.ai", "exp": expire}
    # Note: We need the actual secret from backend/config.py
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

def test_audit_pipeline():
    url = "http://localhost:8000/api/claims/audit"
    
    # Hardcoded secret from backend/.env or config.py if I can find it
    # I saw it earlier: 897234892374823974c89237489237b4234234234
    token = create_mock_token()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input_features": {
            "age": 48,
            "policy_annual_premium": 1406,
            "months_as_customer": 248,
            "total_claim_amount": 71610,
            "insured_sex": "MALE",
            "incident_state": "OH",
            "insured_education_level": "Bachelor",
            "incident_type": "Multi-vehicle Collision",
            "incident_severity": "Major Damage",
            "policy_csl": "250/500",
            "insured_occupation": "machine-op-inspct",
            "insured_relationship": "husband",
            "number_of_vehicles_involved": 3,
            "witnesses": 2
        },
        "model_decision": "Rejected",
        "model_confidence": 0.73
    }

    print(f"--- 🚀 Sending Test Audit to {url} ---")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        if response.status_code == 200:
            print("✅ SUCCESS: Audit Pipeline returned valid result.")
            result = response.json()
            print(f"Audit ID: {result['claim_id']}")
            print(f"Trust Score: {result['trust_score']}")
            print(f"Verdict: {result['verdict']}")
            print(f"Bias Detected: {result['bias_flag']}")
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_audit_pipeline()
