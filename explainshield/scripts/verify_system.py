import sys
import os
import joblib

# Add backend to path (assuming script is run from project root)
sys.path.append('backend')

try:
    from model.shap_engine import get_shap_explanation
    from agents.financial_agent import generate_financial_explanation
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Ensure you are running this from the project root and backend/ folder is present.")
    sys.exit(1)

def verify():
    print("\n" + "="*50)
    print("🛡️  ExplainShield System Verification")
    print("="*50 + "\n")
    
    # 1. Check Artifacts
    model_path = os.path.join('backend', 'model', 'insurance_model.pkl')
    if not os.path.exists(model_path):
        print("❌ Error: Model artifacts not found.")
        print("💡 Solution: Run 'python backend/model/train_model.py' first.")
        return

    # 2. Test SHAP Engine
    print("🔍 Testing SHAP Engine...")
    try:
        with open(model_path, 'rb') as f:
            model_bytes = f.read()
        
        sample_features = {
            'insured_sex': 'MALE', 'insured_education_level': 'PhD',
            'incident_type': 'Single Vehicle Collision', 'incident_severity': 'Major Damage',
            'incident_state': 'OH', 'policy_csl': '250/500',
            'insured_occupation': 'machine-op-inspct', 'insured_relationship': 'husband',
            'age': 48, 'policy_annual_premium': 1406.91,
            'total_claim_amount': 71610, 'months_as_customer': 248,
            'number_of_vehicles_involved': 1, 'witnesses': 2
        }
        
        explanation = get_shap_explanation(model_bytes, sample_features)
        print(f"✅ SHAP Engine Success! Top Features: {', '.join(explanation['top_features'])}")
    except Exception as e:
        print(f"❌ SHAP Engine Failed: {e}")
        return

    # 3. Check Ollama Connectivity
    print("\n🤖 Testing Ollama Agent Connectivity (Llama3.2)...")
    print("⏳ Note: The first run may take a moment as the model loads into memory.")
    try:
        agent_resp = generate_financial_explanation(sample_features, 1, explanation['top_features'])
        if "Error connecting" in agent_resp:
            print("⚠️  Ollama connectivity issue.")
            print(f"   Reason: {agent_resp}")
            print("💡 Solution: Ensure 'ollama serve' is running and 'llama3.2' is pulled.")
        else:
            print("✅ Agent Response Success!")
            print("-" * 20)
            print(f"Financial Agent Output:\n{agent_resp}")
            print("-" * 20)
    except Exception as e:
        print(f"❌ Agent Test Failed: {e}")

    print("\n" + "="*50)
    print("Verification Completed.")
    print("="*50)

if __name__ == "__main__":
    verify()
