from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File
from typing import Dict, Any, List, Optional
import uuid
import time
import asyncio
import logging
import os
import os.path
import joblib
import io
import pandas as pd
import numpy as np
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


@router.get("")
async def list_claims(
    limit: int = 50,
    company: dict = Depends(get_current_company)
):
    """
    List all claims for the company (claim queue).
    """
    company_id = company["company_id"]
    db = Database.get_database()
    claims_coll = db[f"company_{company_id}_claims"]
    
    cursor = claims_coll.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
    claims = await cursor.to_list(length=limit)
    return {"claims": claims, "total": len(claims)}


@router.get("/{claim_id}")
async def get_claim(
    claim_id: str,
    company: dict = Depends(get_current_company)
):
    """
    Get a specific claim by ID.
    """
    company_id = company["company_id"]
    db = Database.get_database()
    claims_coll = db[f"company_{company_id}_claims"]
    
    claim = await claims_coll.find_one({"claim_id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.post("/seed")
async def seed_sample_claims(
    company: dict = Depends(get_current_company)
):
    """
    Seed sample claims for testing the audit pipeline.
    """
    company_id = company["company_id"]
    db = Database.get_database()
    claims_coll = db[f"company_{company_id}_claims"]
    
    sample_claims = [
        {
            "claim_id": "CLM-2024-001",
            "features": {
                "age": 48,
                "policy_annual_premium": 1406.91,
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
            "status": "pending",
            "created_at": time.time()
        },
        {
            "claim_id": "CLM-2024-002",
            "features": {
                "age": 35,
                "policy_annual_premium": 980.50,
                "months_as_customer": 120,
                "total_claim_amount": 25000,
                "insured_sex": "FEMALE",
                "incident_state": "CA",
                "insured_education_level": "High School",
                "incident_type": "Vehicle Theft",
                "incident_severity": "Total Loss",
                "policy_csl": "100/300",
                "insured_occupation": "cleaning-service",
                "insured_relationship": "self",
                "number_of_vehicles_involved": 1,
                "witnesses": 0
            },
            "status": "pending",
            "created_at": time.time() - 86400
        },
        {
            "claim_id": "CLM-2024-003",
            "features": {
                "age": 52,
                "policy_annual_premium": 2100.00,
                "months_as_customer": 300,
                "total_claim_amount": 95000,
                "insured_sex": "MALE",
                "incident_state": "TX",
                "insured_education_level": "PhD",
                "incident_type": "Single Vehicle Collision",
                "incident_severity": "Major Damage",
                "policy_csl": "500/1000",
                "insured_occupation": "professor",
                "insured_relationship": "husband",
                "number_of_vehicles_involved": 1,
                "witnesses": 1
            },
            "status": "pending",
            "created_at": time.time() - 172800
        }
    ]
    
    for claim in sample_claims:
        await claims_coll.update_one(
            {"claim_id": claim["claim_id"]},
            {"$set": claim},
            upsert=True
        )
    
    return {"message": f"Seeded {len(sample_claims)} claims for company {company_id}"}


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

@router.post("/audit/{claim_id}")
async def audit_claim_by_id(
    claim_id: str,
    company: dict = Depends(get_current_company)
):
    """
    Run full audit pipeline for a specific claim ID.
    1. Fetch claim from DB
    2. Run model to get prediction
    3. Run SHAP, agents, validation, CRDI, compliance
    4. Return all results including SHAP, agent outputs, violations
    """
    company_id = company["company_id"]
    db = Database.get_database()
    claims_coll = db[f"company_{company_id}_claims"]
    
    claim = await claims_coll.find_one({"claim_id": claim_id})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    input_features = claim.get("features", {})
    claim_id_from_db = claim.get("claim_id", claim_id)
    
    print(f"\n--- [AUDIT] Starting Audit Pipeline for Claim {claim_id_from_db} (Tenant: {company_id}) ---")
    
    try:
        model_path = os.path.join(os.path.dirname(__file__), '..', 'model', 'insurance_model.pkl')
        with open(model_path, "rb") as f:
            model_bytes = f.read()
        
        model = joblib.load(io.BytesIO(model_bytes))
        
        # Load preprocessing artifacts (same as SHAP engine)
        model_dir = os.path.join(os.path.dirname(__file__), '..', 'model')
        scaler = joblib.load(os.path.join(model_dir, 'scaler.pkl'))
        encoders = joblib.load(os.path.join(model_dir, 'encoders.pkl'))
        feature_names = joblib.load(os.path.join(model_dir, 'feature_names.pkl'))
        
        NUM_COLS = ['age', 'policy_annual_premium', 'total_claim_amount', 'months_as_customer',
                   'number_of_vehicles_involved', 'witnesses']
        
        NUM_DEFAULTS = {
            'age': 40, 'policy_annual_premium': 1200.0, 'total_claim_amount': 50000.0,
            'months_as_customer': 120, 'number_of_vehicles_involved': 1, 'witnesses': 1
        }
        
        # Preprocess features
        input_df = pd.DataFrame([input_features])
        
        cat_cols = list(encoders.keys())
        for col in cat_cols:
            le = encoders[col]
            if col in input_df.columns:
                val = str(input_df[col].iloc[0])
            else:
                val = le.classes_[0]
            if val not in le.classes_:
                val = le.classes_[0]
            input_df[col] = le.transform([val])[0]
        
        for col in NUM_COLS:
            if col not in input_df.columns:
                input_df[col] = NUM_DEFAULTS.get(col, 0)
        
        input_df[NUM_COLS] = scaler.transform(input_df[NUM_COLS])
        
        X = input_df[feature_names]
        
        if hasattr(model, 'predict_proba'):
            proba = model.predict_proba(X)[0]
            model_confidence = float(max(proba))
            model_decision = "Rejected" if model.predict(X)[0] == 1 else "Approved"
        else:
            model_confidence = 0.75
            model_decision = "Rejected" if model.predict(X)[0] == 1 else "Approved"
        
        print(f"[MODEL] Decision: {model_decision}, Confidence: {model_confidence:.2f}")
        
        print("[1/6] Running SHAP Analysis...")
        shap_res = get_shap_explanation(model_bytes, input_features)
        
        print("[2/6] Triggering Multi-Agent Audit Simulations (Parallel)...")
        pred_int = 1 if model_decision == "Rejected" else 0
        
        tasks = []
        for _ in range(3):
            tasks.append(asyncio.to_thread(generate_financial_explanation, input_features, pred_int, shap_res['top_features']))
        tasks.append(asyncio.to_thread(generate_adversarial_explanation, input_features, pred_int))
        
        agent_results = await asyncio.gather(*tasks)
        
        fair_explanations = agent_results[:3]
        adv_exp = agent_results[3]
        primary_fair_exp = fair_explanations[0]
        
        print("[3/6] Running Linguistic & Semantic Validation Checks...")
        validation_results = run_all_checks(
            primary_fair_exp, adv_exp, fair_explanations,
            shap_res['top_features'], "", shap_res['feature_importance']
        )
        
        print("[4/6] Running Counterfactual Analysis & CRDI Metric Suite...")
        cf_results = run_full_counterfactual_suite(
            input_features,
            lambda f: "Approved" if f.get("income", 0) > 4000 else "Rejected",
            [input_features]
        )
        
        print("[5/6] Verifying IRDAI Policy Compliance Guidelines...")
        compliance_results = check_compliance(shap_res, validation_results['faithfulness'], cf_results)
        
        arbitration_report = None
        if validation_results['bias']['bias_detected'] or compliance_results['overall_status'] != "COMPLIANT":
            print("[ARB] Bias/Compliance Risk Detected. Triggering Senior Arbitration Agent...")
            arbitration_report = await asyncio.to_thread(
                generate_arbitration, input_features, pred_int, primary_fair_exp, adv_exp,
                shap_res['top_features'], validation_results['bias']['bias_score'],
                cf_results['single_flip_results']['summary']
            )
        
        print("[6/6] Finalizing Trust Score & Audit Verdict...")
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
        
        audit_record = {
            "claim_id": claim_id_from_db,
            "company_id": company_id,
            "timestamp": time.time(),
            "input_data": input_features,
            "model_prediction": model_decision,
            "model_confidence": model_confidence,
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
                    "grounding": validation_results['grounding']['grounding_score'],
                    "afs": validation_results['afs']['afs_score'],
                    "lbid": validation_results['lbid'].get('bias_probability', 0.0),
                    "crdi_gender": cf_results['crdi_gender']['crdi_score'],
                    "crdi_region": cf_results['crdi_region']['crdi_score'],
                    "shap": shap_res['feature_importance']
                },
                "violations": compliance_results['violations'],
                "counterfactual_summary": cf_results['single_flip_results']['summary'],
                "fair_explanations": fair_explanations,
                "adversarial_explanation": adv_exp
            }
        }
        
        try:
            audit_coll = db[f"company_{company_id}_audit_logs"]
            await audit_coll.insert_one(audit_record)
            print("[OK] Audit record saved successfully.")
        except Exception as db_err:
            print(f"[WARN] Persistence Warning: {db_err}")
        
        print(f"[DONE] Audit Completed. Score: {trust_results['trust_score']} | Status: {trust_results['verdict']}")
        
        return {
            "claim_id": claim_id_from_db,
            "model_prediction": model_decision,
            "model_confidence": model_confidence,
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
                "crdi_region": cf_results['crdi_region']['crdi_score'],
                "shap_feature_importance": shap_res['feature_importance']
            },
            "fair_explanations": fair_explanations,
            "adversarial_explanation": adv_exp,
            "violations": compliance_results['violations'],
            "counterfactual_summary": cf_results['single_flip_results']['summary'],
            "top_shap_features": shap_res['top_features'],
            "audit_id": str(audit_record.get("_id", claim_id_from_db))
        }

    except Exception as e:
        print(f"[ERROR] PIPELINE ERROR: {e}")
        logger.error(f"Audit Pipeline Failed for {claim_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
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
            print("[ARB] Bias/Compliance Risk Detected. Triggering Senior Arbitration Agent...")
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
        print("[6/6] Finalizing Trust Score & Audit Verdict...")
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
        print("[DB] Attempting to save audit report to MongoDB isolated collection...")
        
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
            print("[OK] Audit record saved successfully.")
        except Exception as db_err:
            print(f"[WARN] Persistence Warning: Could not save audit to MongoDB: {db_err}")
            # Non-fatal: audit results are still returned to the user
            
        # 12. Return Audit Result (Step 12)
        print(f"[DONE] Audit Completed. Score: {trust_results['trust_score']} | Status: {trust_results['verdict']}")
        
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
        print(f"[ERROR] PIPELINE ERROR: {e}")
        logger.error(f"Audit Pipeline Failed for {claim_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
