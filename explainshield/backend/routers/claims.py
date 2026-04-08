from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File
from typing import Dict, Any, List, Optional
import uuid
import time
import asyncio
import logging
import os
from utils.auth import get_current_company
from database.mongodb import Database

# Document Processing (NEW)
from utils.document_extractor import DocumentExtractor
from utils.feature_extractor import FeatureExtractor
try:
    from database.vector_store import get_vector_store
    VECTOR_STORE_AVAILABLE = True
except ImportError:
    VECTOR_STORE_AVAILABLE = False

# ML & Engines
from model.shap_engine import get_shap_explanation
from agents.financial_agent import generate_financial_explanation
from agents.adversarial_agent import generate_adversarial_explanation
from agents.arbitration_agent import generate_arbitration
from engine.validation_engine import run_all_checks
from engine.counterfactual_engine import run_full_counterfactual_suite
from engine.scoring_engine import compute_trust_score
from compliance.policy_compliance import check_compliance

router = APIRouter()
logger = logging.getLogger(__name__)

document_extractor = DocumentExtractor()
feature_extractor = FeatureExtractor()


@router.post("/extract")
async def extract_from_document(
    file: UploadFile = File(...),
    company: dict = Depends(get_current_company)
):
    """
    Step 1-2: Extract text and features from uploaded PDF/image document.
    Returns both raw text + embeddings + structured features.
    """
    company_id = company["company_id"]
    claim_id = str(uuid.uuid4())
    
    print(f"\n📄 Extracting from document for Claim {claim_id}")
    
    file_bytes = await file.read()
    
    extracted = document_extractor.extract_text(file_bytes, file.filename)
    
    features = feature_extractor.extract_features(
        extracted["text"], 
        extracted.get("embeddings", [])
    )
    
    if VECTOR_STORE_AVAILABLE:
        try:
            vs = get_vector_store()
            vs.add_document(
                claim_id=claim_id,
                document_text=extracted["text"],
                embeddings=extracted.get("embeddings", []),
                metadata={
                    "company_id": company_id,
                    "filename": file.filename,
                    "source_type": extracted["source_type"]
                }
            )
        except Exception as e:
            logger.warning(f"Vector store unavailable: {e}")
    
    return {
        "claim_id": claim_id,
        "text": extracted["text"],
        "embeddings": extracted.get("embeddings", []),
        "features": features,
        "source_type": extracted["source_type"],
        "page_count": extracted.get("page_count", 1)
    }

@router.post("/audit")
async def audit_claim(
    payload: Dict[str, Any] = Body(...),
    company: dict = Depends(get_current_company)
):
    """
    The main 12-step Audit Pipeline for ExplainShield.
    Integrates ML, Agents, Metrics, and Compliance.
    """
    company_id = company["company_id"]
    claim_id = str(uuid.uuid4())
    
    print(f"\n--- [AUDIT] Starting Audit Pipeline for Claim {claim_id} (Tenant: {company_id}) ---")
    
    # 1. Input Extraction
    input_features = payload.get("input_features", {})
    model_decision = payload.get("model_decision", "Rejected")
    model_confidence = payload.get("model_confidence", 0.73)
    document_text = payload.get("document_text", "")  # For grounding check (Step 5)
    
    # 2. Get Model from encrypted storage (In a real app, we'd load and warm this up)
    # For now, we'll assume the local model is used (mocking tenant isolation)
    # Note: In a production multi-tenant app, we'd use joblib.load(io.BytesIO(model_binary))
    
    try:
        # 3. SHAP Engine (Step 3)
        print("[1/6] Running SHAP Analysis...")
        
        # Load the actual trained model from the filesystem for this demo
        model_path = os.path.join(os.path.dirname(__file__), '..', 'model', 'insurance_model.pkl')
        with open(model_path, "rb") as f:
            model_bytes = f.read()
            
        # FIXED: Correct argument order (model_bytes, features_dict)
        shap_res = get_shap_explanation(model_bytes, input_features)
        
        # 4. Multi-Agent Audit (Step 4) - Parallelized for performance
        print("[2/6] Triggering Multi-Agent Audit Simulations (Parallel)...")
        # Note: Added 'prediction' argument (mapped from model_decision)
        pred_int = 1 if model_decision == "Rejected" else 0
        
        # Dispatch 3x Financial Agents and 1x Adversarial Agent in parallel
        # Note: These are synchronous BIO calls, so we use asyncio.to_thread
        tasks = []
        for _ in range(3):
            tasks.append(asyncio.to_thread(generate_financial_explanation, input_features, pred_int, shap_res['top_features']))
        
        # Add Adversarial agent task
        tasks.append(asyncio.to_thread(generate_adversarial_explanation, input_features, pred_int))
        
        # Resolve all 4 LLM calls simultaneously
        agent_results = await asyncio.gather(*tasks)
        
        fair_explanations = agent_results[:3]
        adv_exp = agent_results[3]
        primary_fair_exp = fair_explanations[0]
        
        # 5. Validation Logic (Steps 5, 6, 7)
        print("[3/6] Running Linguistic & Semantic Validation Checks...")
        
        validation_results = run_all_checks(
            primary_fair_exp, 
            adv_exp, 
            fair_explanations, 
            shap_res['top_features'],
            document_text,  # Now includes document for grounding
            shap_res['feature_importance']
        )
        
        # 6. Counterfactual Suite & CRDI (Step 8)
        print("[4/6] Running Counterfactual Analysis & CRDI Metric Suite...")
        # Note: We need some historical results for CRDI - mocking with empty list for single instance
        cf_results = run_full_counterfactual_suite(
            input_features, 
            lambda f: "Approved" if f.get("income", 0) > 4000 else "Rejected", # mock predict
            [input_features] 
        )
        
        # 7. Policy Compliance & Arbitration (Step 9)
        print("[5/6] Verifying IRDAI Policy Compliance Guidelines...")
        compliance_results = check_compliance(shap_res, validation_results['faithfulness'], cf_results)
        
        # Optional: Run Arbitration if bias is detected
        arbitration_report = None
        if validation_results['bias']['bias_detected'] or compliance_results['overall_status'] != "COMPLIANT":
            print("⚖️ [ARB] Bias/Compliance Risk Detected. Triggering Senior Arbitration Agent...")
            # Using to_thread for blocking LLM call
            arbitration_report = await asyncio.to_thread(
                generate_arbitration,
                input_features,
                pred_int,
                primary_fair_exp,
                adv_exp,
                shap_res['top_features'],
                validation_results['bias']['bias_score'],
                cf_results['single_flip_results']['summary']
            )
            
        # 8. Trust Scoring (Step 10)
        print("📊 [6/6] Finalizing Trust Score & Audit Verdict...")
        trust_results = compute_trust_score(
            validation_results['faithfulness']['faithfulness_score'],
            validation_results['bias']['bias_score'],
            validation_results['consistency']['consistency_score'],
            validation_results['grounding']['grounding_score'],
            validation_results['afs']['afs_score'],
            validation_results['lbid'].get('bias_probability', 0.0),
            cf_results['single_flip_results']['bias_confirmed'],
            any(f in shap_res['top_features'][:3] for f in ['insured_sex', 'incident_state']),
            compliance_results['overall_status'] == "NON_COMPLIANT"
        )
        
        # 11. Persistence (Step 11) - Build record first, then attempt DB save
        print("💾 Attempting to save audit report to MongoDB isolated collection...")
        
        audit_record = {
            "claim_id": claim_id,
            "company_id": company_id,
            "timestamp": time.time(),
            "input_data": input_features,
            "model_decision": model_decision,
            "results": {
                "trust_score": trust_results['trust_score'],
                "verdict": trust_results['verdict'],
                "risk_level": trust_results['risk_level'],
                "explanation": arbitration_report if arbitration_report else primary_fair_exp,
                "compliance": compliance_results['overall_status'],
                "bias_flag": validation_results['bias']['bias_detected'],
                "scores": {
                    "faithfulness": validation_results['faithfulness']['faithfulness_score'],
                    "bias": validation_results['bias']['bias_score'],
                    "consistency": validation_results['consistency']['consistency_score'],
                    "afs": validation_results['afs']['afs_score'],
                    "lbid": validation_results['lbid'].get('bias_probability', 0.0),
                    "crdi_gender": cf_results['crdi_gender']['crdi_score']
                },
                "violations": compliance_results['violations'],
                "counterfactual_summary": cf_results['single_flip_results']['summary']
            }
        }
        
        try:
            db = Database.get_database()
            audit_coll = db[f"company_{company_id}_audit_logs"]
            await audit_coll.insert_one(audit_record)
            print("✅ Audit record saved successfully.")
        except Exception as db_err:
            print(f"⚠️ Persistence Warning: Could not save audit to MongoDB: {db_err}")
            # Non-fatal: audit results are still returned to the user
            
        # 12. Return Audit Result (Step 12)
        print(f"✅ Audit Completed. Score: {trust_results['trust_score']} | Status: {trust_results['verdict']}")
        
        return {
            "claim_id": claim_id,
            "verdict": trust_results['verdict'],
            "trust_score": trust_results['trust_score'],
            "risk_level": trust_results['risk_level'],
            "validated_explanation": arbitration_report if arbitration_report else primary_fair_exp,
            "bias_flag": validation_results['bias']['bias_detected'],
            "compliance_status": compliance_results['overall_status'],
            "action_required": trust_results['recommended_action'],
            "scores": {
                "faithfulness": validation_results['faithfulness']['faithfulness_score'],
                "bias": validation_results['bias']['bias_score'],
                "consistency": validation_results['consistency']['consistency_score'],
                "grounding": validation_results['grounding']['grounding_score'],
                "afs": validation_results['afs']['afs_score'],
                "lbid_bias_probability": validation_results['lbid'].get('bias_probability', 0.0),
                "crdi_gender": cf_results['crdi_gender']['crdi_score'],
                "crdi_region": cf_results['crdi_region']['crdi_score']
            },
            "violations": compliance_results['violations'],
            "counterfactual_summary": cf_results['single_flip_results']['summary'],
            "audit_id": str(audit_record.get("_id", claim_id))
        }

    except Exception as e:
        print(f"❌ PIPELINE ERROR: {e}")
        logger.error(f"Audit Pipeline Failed for {claim_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
