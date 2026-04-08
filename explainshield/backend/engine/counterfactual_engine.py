import copy
import sys
import os

# Ensure project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import CRDI from novel metrics
try:
    from novel_metrics.crdi import compute_crdi
except ImportError:
    from backend.novel_metrics.crdi import compute_crdi

# SENSITIVE_ATTRIBUTES Configuration
SENSITIVE_ATTRIBUTES = {
    "insured_sex": ["MALE", "FEMALE"],
    "incident_state": ["OH", "IL", "IN"],
    "insured_education_level": ["Bachelor", "High School", "Masters"]
}

def run_counterfactual_analysis(features: dict, model_predict_fn: callable) -> dict:
    """
    Performs single-flip counterfactual analysis to detect individual bias events.
    """
    original_decision = model_predict_fn(features)
    individual_flips = []
    total_bias_events = 0
    biased_attributes = set()

    for attr, values in SENSITIVE_ATTRIBUTES.items():
        if attr not in features:
            continue
            
        original_val = features[attr]
        
        for alt_val in values:
            if alt_val == original_val:
                continue
                
            # Create deep copy and flip
            test_features = copy.deepcopy(features)
            test_features[attr] = alt_val
            
            # Predict and compare
            flipped_decision = model_predict_fn(test_features)
            
            bias_detected = (flipped_decision != original_decision)
            
            if bias_detected:
                total_bias_events += 1
                biased_attributes.add(attr)
                
            individual_flips.append({
                "attribute": attr,
                "original_value": original_val,
                "flipped_value": alt_val,
                "original_decision": original_decision,
                "flipped_decision": flipped_decision,
                "bias_detected": bool(bias_detected),
                "probability_shift": None # Can be extended for soft probabilities
            })

    # Severity Mapping
    severity = "NONE"
    if total_bias_events >= 3:
        severity = "HIGH"
    elif total_bias_events == 2:
        severity = "MEDIUM"
    elif total_bias_events == 1:
        severity = "LOW"
        
    summary = f"Detected {total_bias_events} bias events across {len(biased_attributes)} attributes."
    if total_bias_events > 0:
        summary += f" Highly sensitive to: {', '.join(biased_attributes)}."

    return {
        "individual_flips": individual_flips,
        "total_bias_events": int(total_bias_events),
        "biased_attributes": list(biased_attributes),
        "bias_confirmed": bool(total_bias_events > 0),
        "bias_severity": severity,
        "summary": summary
    }

def run_full_counterfactual_suite(
    features: dict,
    model_predict_fn: callable,
    recent_rejected_decisions: list
) -> dict:
    """
    Runs both single-flip analysis and CRDI dataset-level audits.
    """
    # 1. Single Flip Individual Analysis
    flip_results = run_counterfactual_analysis(features, model_predict_fn)
    
    # 2. CRDI Gender (Sex)
    crdi_gender = compute_crdi(
        recent_rejected_decisions, 
        model_predict_fn, 
        'insured_sex', 'MALE', 'FEMALE'
    )
    
    # 3. CRDI Region (State)
    crdi_region = compute_crdi(
        recent_rejected_decisions, 
        model_predict_fn, 
        'incident_state', 'OH', 'IL'
    )
    
    # Combined Severity
    combined_severity = flip_results['bias_severity']
    if crdi_gender['bias_detected'] or crdi_region['bias_detected']:
        if combined_severity == "NONE":
            combined_severity = "LOW"
        elif combined_severity == "LOW":
            combined_severity = "MEDIUM"
        else:
            combined_severity = "HIGH"

    return {
        "single_flip_results": flip_results,
        "crdi_gender": crdi_gender,
        "crdi_region": crdi_region,
        "combined_bias_severity": combined_severity
    }

if __name__ == "__main__":
    # Test Block
    def mock_predict(feat):
        # Biased logic for 'FEMALE' or 'OH'
        if feat.get("insured_sex") == "FEMALE":
            return "Rejected"
        if feat.get("incident_state") == "OH":
            return "Rejected"
        return "Approved"
        
    test_features = {
        "insured_sex": "MALE",
        "incident_state": "IL",
        "insured_education_level": "Bachelor"
    }
    
    print("\nRunning Counterfactual Analysis...")
    res = run_counterfactual_analysis(test_features, mock_predict)
    print(f"Total Bias Events: {res['total_bias_events']}")
    print(f"Severity: {res['bias_severity']}")
    print(f"Summary: {res['summary']}")
