import requests
from jose import jwt
import datetime

SECRET = 'explainshield-secret-2026'
expire = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
token = jwt.encode({'sub': 'demo_company', 'company_id': 'demo_audit_corp', 'exp': expire}, SECRET, algorithm='HS256')

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
payload = {
    'input_features': {'age': 48, 'total_claim_amount': 71610, 'policy_annual_premium': 1406},
    'model_decision': 'Rejected',
    'model_confidence': 0.73
}

print("--- Sending audit request ---")
r = requests.post('http://localhost:8000/api/claims/audit', headers=headers, json=payload, timeout=60)
print('Status:', r.status_code)
print(r.text)
