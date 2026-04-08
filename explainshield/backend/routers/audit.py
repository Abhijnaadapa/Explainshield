from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List
from utils.auth import get_current_company
from database.mongodb import Database
import pandas as pd

router = APIRouter()

@router.get("/logs")
async def get_audit_logs(
    limit: int = Query(10, gt=0),
    company: dict = Depends(get_current_company)
):
    """
    Retrieves recent audit logs for the company.
    """
    company_id = company["company_id"]
    db = Database.get_database()
    audit_coll = db[f"company_{company_id}_audit_logs"]
    
    cursor = audit_coll.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
    logs = await cursor.to_list(length=limit)
    return logs

@router.get("/stats")
async def get_audit_stats(company: dict = Depends(get_current_company)):
    """
    Computes summary statistics for the dashboard.
    """
    company_id = company["company_id"]
    db = Database.get_database()
    audit_coll = db[f"company_{company_id}_audit_logs"]
    
    # Aggregation Pipeline
    pipeline = [
        {"$group": {
            "_id": None,
            "avg_trust_score": {"$avg": "$results.trust_score"},
            "total_audits": {"$sum": 1},
            "bias_events": {"$sum": {"$cond": ["$results.bias_flag", 1, 0]}},
            "compliance_failures": {"$sum": {"$cond": [{"$eq": ["$results.compliance", "NON_COMPLIANT"]}, 1, 0]}}
        }}
    ]
    
    stats = await audit_coll.aggregate(pipeline).to_list(length=1)
    if not stats:
        return {"avg_trust_score": 0, "total_audits": 0, "bias_events": 0, "compliance_failures": 0}
        
    return stats[0]

@router.get("/compliance-report")
async def get_compliance_report(company: dict = Depends(get_current_company)):
    """
    Generates a high-level summary of IRDAI violations.
    """
    company_id = company["company_id"]
    db = Database.get_database()
    audit_coll = db[f"company_{company_id}_audit_logs"]
    
    # Total violation counts across logs
    cursor = audit_coll.find({"results.compliance": {"$ne": "COMPLIANT"}})
    failed_audits = await cursor.to_list(length=100)
    
    summary = {}
    for audit in failed_audits:
        for v in audit['results']['violations']:
            guideline = v['guideline']
            summary[guideline] = summary.get(guideline, 0) + 1
            
    return {
        "violation_summary": summary,
        "total_violations": sum(summary.values()),
        "company_id": company_id
    }

@router.get("/crdi-report")
async def get_crdi_report(company: dict = Depends(get_current_company)):
    """
    Returns the mean CRDI (Recourse Disparity) across all audited claims.
    Used for Experiment 2 in the research paper.
    """
    company_id = company["company_id"]
    db = Database.get_database()
    audit_coll = db[f"company_{company_id}_audit_logs"]
    
    pipeline = [
        {"$group": {
            "_id": None,
            "mean_crdi_gender": {"$avg": "$results.scores.crdi_gender"}
        }}
    ]
    
    result = await audit_coll.aggregate(pipeline).to_list(length=1)
    return {
        "mean_crdi_gender": result[0]["mean_crdi_gender"] if result else 0.0,
        "indicator": "Fairness Gap" if (result and result[0]["mean_crdi_gender"] > 0.2) else "Optimal Choice"
    }
