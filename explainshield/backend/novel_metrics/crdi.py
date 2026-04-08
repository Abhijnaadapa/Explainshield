import numpy as np
import pandas as pd
import copy

def compute_individual_recourse_cost(
    features,
    model_predict_fn,
    target_decision="Approved",
    legitimate_features=["income", "total_claim_amount", "credit_score", "months_as_customer"],
    max_multiplier=3.0
):
    """
    Computes the minimum individual recourse cost using counterfactual binary search.
    
    Mathematical Definition:
    C(x) = min_{f ∈ F_legit} (δ_f) such that M(x + δ_f) = target_decision
    where δ_f is the change in feature f, and x exists in the 'Rejected' space.
    
    Docstrings for Research Paper Reference:
    Recourse cost measures the difficulty an individual from a rejected group faces 
    in reaching a favorable outcome (e.g., claim approval). Unlike static fairness metrics, 
    recourse cost is dynamic, calculating the 'distance' to the decision boundary 
    through counterfactual perturbations of actionable, legitimate features. 
    By identifying the minimum delta (δ) across a subspace of approved features 
    (e.g., income, credit score), we can quantify the individual-level hurdle for 
    reaching parity with the privileged group.
    """
    
    # 1. Initial check
    if model_predict_fn(features) == target_decision:
        return {
            "minimum_recourse_feature": None,
            "minimum_recourse_cost": 0.0,
            "recourse_by_feature": {},
            "recourse_possible": True
        }

    recourse_by_feature = {}
    
    # 2. Binary Search for Income
    # Max increase of 3x (specified by max_multiplier)
    if "income" in features:
        low = float(features["income"])
        high = float(features["income"]) * max_multiplier
        
        # Test if recourse is possible at max bound
        test_feat = copy.deepcopy(features)
        test_feat["income"] = high
        if model_predict_fn(test_feat) == target_decision:
            # Binary search to find threshold (precision > 100 as requested)
            while (high - low) > 100:
                mid = (low + high) / 2
                test_feat["income"] = mid
                if model_predict_fn(test_feat) == target_decision:
                    high = mid
                else:
                    low = mid
            recourse_by_feature["income"] = float(high - features["income"])
        else:
            recourse_by_feature["income"] = float('inf')

    # 3. Binary Search for Credit Score
    # Max increase of 200 points
    if "credit_score" in features:
        low = float(features["credit_score"])
        high = float(features["credit_score"]) + 200
        
        test_feat = copy.deepcopy(features)
        test_feat["credit_score"] = high
        if model_predict_fn(test_feat) == target_decision:
            while (high - low) > 1: # Higher precision for discrete scores
                mid = (low + high) / 2
                test_feat["credit_score"] = mid
                if model_predict_fn(test_feat) == target_decision:
                    high = mid
                else:
                    low = mid
            recourse_by_feature["credit_score"] = float(high - features["credit_score"])
        else:
            recourse_by_feature["credit_score"] = float('inf')

    # 4. Final Aggregation
    viable_costs = {f: c for f, c in recourse_by_feature.items() if c != float('inf')}
    
    if not viable_costs:
        return {
            "minimum_recourse_feature": None,
            "minimum_recourse_cost": None,
            "recourse_by_feature": recourse_by_feature,
            "recourse_possible": False
        }
        
    min_feature = min(viable_costs, key=viable_costs.get)
    return {
        "minimum_recourse_feature": min_feature,
        "minimum_recourse_cost": viable_costs[min_feature],
        "recourse_by_feature": recourse_by_feature,
        "recourse_possible": True
    }

def compute_crdi(
    rejected_decisions,
    model_predict_fn,
    sensitive_attribute,
    privileged_value,
    unprivileged_value
):
    """
    Computes Counterfactual Recourse Disparity Index (CRDI).
    
    Formula:
    CRDI = (E[Cost_unprivileged] / E[Cost_privileged]) - 1
    
    Where:
    - E[Cost] is the mean minimum recourse cost for a rejected group.
    
    Docstrings for Research Paper Reference:
    The Counterfactual Recourse Disparity Index (CRDI) measures the inequality of opportunity 
    in reaching a positive outcome after a negative decision. A CRDI > 0.2 indicates 
    structural bias, where members of an unprivileged group (e.g., gender, region) 
    must achieve significantly higher gains in legitimate features (such as professional 
    income) to reverse a negative AI decision compared to their privileged counterparts.
    """
    
    privileged_costs = []
    unprivileged_costs = []
    
    for instance in rejected_decisions:
        cost_res = compute_individual_recourse_cost(instance, model_predict_fn)
        if not cost_res["recourse_possible"]:
            continue # Omit impossible cases to avoid math errors (or assign a max penalty)
            
        cost = cost_res["minimum_recourse_cost"]
        
        if instance[sensitive_attribute] == privileged_value:
            privileged_costs.append(cost)
        elif instance[sensitive_attribute] == unprivileged_value:
            unprivileged_costs.append(cost)
            
    mean_priv = float(np.mean(privileged_costs)) if privileged_costs else 0.0
    mean_unpriv = float(np.mean(unprivileged_costs)) if unprivileged_costs else 0.0
    
    crdi_score = 0.0
    if mean_priv > 0:
        crdi_score = (mean_unpriv / mean_priv) - 1
        
    bias_detected = crdi_score > 0.2
    
    severity = "NONE"
    if crdi_score > 0.5:
        severity = "HIGH"
    elif crdi_score > 0.3:
        severity = "MEDIUM"
    elif crdi_score > 0.2:
        severity = "LOW"
        
    return {
        "crdi_score": crdi_score,
        "privileged_mean_cost": mean_priv,
        "unprivileged_mean_cost": mean_unpriv,
        "privileged_group": str(privileged_value),
        "unprivileged_group": str(unprivileged_value),
        "interpretation": f"Unprivileged group requires {crdi_score*100:.1f}% more effort for recourse.",
        "bias_detected": bool(bias_detected),
        "severity": severity
    }

def evaluate_crdi_on_dataset(df, model_predict_fn):
    """
    Runs CRDI evaluation for paper Experiment 2 across multiple attributes.
    """
    # Filter only rejected cases
    rejected_df = df[df.apply(model_predict_fn, axis=1) != "Approved"]
    rejected_list = rejected_df.to_dict('records')
    
    results = []
    
    # 1. Gender Disparity
    gender_res = compute_crdi(rejected_list, model_predict_fn, 'insured_sex', 'MALE', 'FEMALE')
    results.append({
        "Attribute": "Gender (Sex)",
        "CRDI": gender_res['crdi_score'],
        "Bias Detected": gender_res['bias_detected'],
        "Severity": gender_res['severity']
    })
    
    # 2. Regional Disparity (Example States)
    region_res = compute_crdi(rejected_list, model_predict_fn, 'incident_state', 'OH', 'SC')
    results.append({
        "Attribute": "Region (State)",
        "CRDI": region_res['crdi_score'],
        "Bias Detected": region_res['bias_detected'],
        "Severity": region_res['severity']
    })
    
    return pd.DataFrame(results)

if __name__ == "__main__":
    # Test Block
    def mock_predict(feat):
        if feat.get("income", 0) > 4000:
            return "Approved"
        return "Rejected"
        
    test_feat = {"income": 2000, "credit_score": 600, "insured_sex": "FEMALE"}
    print("\nRunning Individual Recourse Cost Test...")
    res = compute_individual_recourse_cost(test_feat, mock_predict)
    print(f"Minimum Recourse Cost: {res['minimum_recourse_cost']}")
    print(f"Feature: {res['minimum_recourse_feature']}")
    
    print("\nRunning CRDI Disparity Test...")
    res_list = [
        {"income": 3000, "insured_sex": "MALE"}, # cost to get to 4000 is 1000
        {"income": 2000, "insured_sex": "FEMALE"} # cost to get to 4000 is 2000
    ]
    crdi = compute_crdi(res_list, mock_predict, 'insured_sex', 'MALE', 'FEMALE')
    print(f"CRDI Score: {crdi['crdi_score']}") # Should be (2000/1000) - 1 = 1.0
    print(f"Bias Detected: {crdi['bias_detected']}")
