def check_compliance(
    shap_results: dict,
    validation_scores: dict,
    counterfactual_results: dict
) -> dict:
    """
    Checks AI decision-making against IRDAI (Insurance Regulatory and Development Authority of India) guidelines.
    """
    
    IRDAI_GUIDELINES = {
        "no_gender_bias": {
            "description": "Gender cannot influence claim decisions",
            "regulation": "IRDAI Circular 2023/AI/04",
            "legal_risk": "HIGH",
            "remediation": "Audit the dataset for gender balance. Re-train with adversarial debiasing."
        },
        "no_regional_bias": {
            "description": "Region cannot be a primary decision factor",
            "regulation": "IRDAI Fair Practice Code",
            "legal_risk": "HIGH",
            "remediation": "Check for state-level data skew. Limit state-level feature importance in decision-making."
        },
        "explainability_required": {
            "description": "Every decision must be explainable and faithful to the model",
            "regulation": "IRDAI Guidelines 2022",
            "legal_risk": "MEDIUM",
            "remediation": "Improve the LLM prompt or fine-tune. Ensure top SHAP drivers are included in explanations."
        },
        "consistency_required": {
            "description": "Similar inputs must generate consistent explanations",
            "regulation": "IRDAI Fair Practice Code",
            "legal_risk": "MEDIUM",
            "remediation": "Reduce LLM temperature. Implement consistency filtering (n-generations)."
        }
    }

    violations = []
    
    # 1. Gender Bias Check: insured_sex not in shap_top3
    # Note: shap_results should contain 'top_features'
    top_3_features = shap_results.get("top_features", [])[:3]
    if "insured_sex" in top_3_features:
        guideline = IRDAI_GUIDELINES["no_gender_bias"]
        violations.append({
            "guideline": "no_gender_bias",
            "description": guideline["description"],
            "regulation": guideline["regulation"],
            "status": "NON_COMPLIANT",
            "evidence": f"insured_sex detected in top 3 SHAP features: {top_3_features}",
            "legal_risk": guideline["legal_risk"],
            "remediation": guideline["remediation"]
        })

    # 2. Regional Bias Check: incident_state shap < 0.15
    # Note: shap_results should contain 'feature_importance' dict
    state_importance = shap_results.get("feature_importance", {}).get("incident_state", 0.0)
    if abs(state_importance) > 0.15:
        guideline = IRDAI_GUIDELINES["no_regional_bias"]
        violations.append({
            "guideline": "no_regional_bias",
            "description": guideline["description"],
            "regulation": guideline["regulation"],
            "status": "NON_COMPLIANT",
            "evidence": f"incident_state SHAP magnitude {state_importance:.4f} exceeds safety threshold (0.15)",
            "legal_risk": guideline["legal_risk"],
            "remediation": guideline["remediation"]
        })

    # 3. Explainability Check: faithfulness_score > 0.6
    faithfulness = validation_scores.get("faithfulness_score", 0.0)
    if faithfulness <= 0.6:
        guideline = IRDAI_GUIDELINES["explainability_required"]
        violations.append({
            "guideline": "explainability_required",
            "description": guideline["description"],
            "regulation": guideline["regulation"],
            "status": "AT_RISK",
            "evidence": f"Faithfulness score {faithfulness:.2f} is below compliance threshold (0.6)",
            "legal_risk": guideline["legal_risk"],
            "remediation": guideline["remediation"]
        })

    # 4. Consistency Check: consistency_score > 0.75
    consistency = validation_scores.get("consistency_score", 1.0)
    if consistency <= 0.75:
        guideline = IRDAI_GUIDELINES["consistency_required"]
        violations.append({
            "guideline": "consistency_required",
            "description": guideline["description"],
            "regulation": guideline["regulation"],
            "status": "AT_RISK",
            "evidence": f"Consistency score {consistency:.2f} is below fair practice threshold (0.75)",
            "legal_risk": guideline["legal_risk"],
            "remediation": guideline["remediation"]
        })

    # Final overall status
    violation_count = len(violations)
    compliant_count = 4 - violation_count
    
    overall_status = "COMPLIANT"
    if any(v["status"] == "NON_COMPLIANT" for v in violations):
        overall_status = "NON_COMPLIANT"
    elif any(v["status"] == "AT_RISK" for v in violations):
        overall_status = "AT_RISK"

    return {
        "overall_status": overall_status,
        "guidelines_checked": list(IRDAI_GUIDELINES.keys()),
        "violations": violations,
        "compliant_count": compliant_count,
        "violation_count": violation_count
    }

if __name__ == "__main__":
    # Test Block
    print("Testing Policy Compliance Engine...")
    
    # Non-Compliant Case
    mock_shap = {"top_features": ["insured_sex", "age"], "feature_importance": {"incident_state": 0.2}}
    mock_val = {"faithfulness_score": 0.5, "consistency_score": 0.7}
    
    results = check_compliance(mock_shap, mock_val, {})
    print(f"Overall Status: {results['overall_status']}")
    print(f"Violations found: {len(results['violations'])}")
    for v in results['violations']:
        print(f"- {v['guideline']}: {v['evidence']}")
