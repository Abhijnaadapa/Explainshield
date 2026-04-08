import pandas as pd
import numpy as np
import shap
import joblib
import io
import os

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
SCALER_PATH = os.path.join(DIR_PATH, 'scaler.pkl')
ENCODERS_PATH = os.path.join(DIR_PATH, 'encoders.pkl')
FEATURE_NAMES_PATH = os.path.join(DIR_PATH, 'feature_names.pkl')

# Numerical columns expected by the scaler
NUM_COLS = [
    'age', 'policy_annual_premium',
    'total_claim_amount', 'months_as_customer',
    'number_of_vehicles_involved', 'witnesses'
]

# Default values for any missing numerical column
NUM_DEFAULTS = {
    'age': 40,
    'policy_annual_premium': 1200.0,
    'total_claim_amount': 50000.0,
    'months_as_customer': 120,
    'number_of_vehicles_involved': 1,
    'witnesses': 1
}


def get_shap_explanation(model_bytes: bytes, features_dict: dict) -> dict:
    """
    Get SHAP explanations for insurance fraud predictions.

    Args:
        model_bytes: Binary data of the trained XGBoost model.
        features_dict: Dictionary containing input features for prediction.

    Returns:
        Dictionary with top_features, feature_importance,
        sensitive_features_in_top5, and ground_truth_vector.
    """
    # 1. Load Model from Bytes
    model = joblib.load(io.BytesIO(model_bytes))

    # 2. Load Preprocessing Artifacts
    if not all(os.path.exists(p) for p in [SCALER_PATH, ENCODERS_PATH, FEATURE_NAMES_PATH]):
        raise FileNotFoundError(
            "Required preprocessing artifacts (scaler, encoders, feature_names) "
            "missing in backend/model/"
        )

    scaler = joblib.load(SCALER_PATH)
    encoders = joblib.load(ENCODERS_PATH)
    feature_names = joblib.load(FEATURE_NAMES_PATH)

    # 3. Create DataFrame
    df = pd.DataFrame([features_dict])

    try:
        # 4a. Encode categorical columns
        cat_cols = list(encoders.keys())
        for col in cat_cols:
            le = encoders[col]
            if col in df.columns:
                val = str(df[col].iloc[0])
            else:
                # Missing categorical column → use first known class as default
                val = le.classes_[0]
            if val not in le.classes_:
                val = le.classes_[0]
            df[col] = le.transform([val])[0]

        # 4b. Fill any missing numerical columns with neutral defaults
        for col in NUM_COLS:
            if col not in df.columns:
                df[col] = NUM_DEFAULTS.get(col, 0)

        # 4c. Scale numerical columns
        df[NUM_COLS] = scaler.transform(df[NUM_COLS])

    except Exception as e:
        raise ValueError(f"Preprocessing error: {str(e)}")

    # 5. Filter and order features to match training
    X = df[feature_names]

    # 6. SHAP TreeExplainer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # Handle different SHAP output shapes
    if isinstance(shap_values, list):
        instance_shap = shap_values[1][0]
    else:
        instance_shap = shap_values[0]

    # 7. Build Feature Importance map
    feature_importance = {
        name: float(val)
        for name, val in zip(feature_names, instance_shap)
    }

    sorted_features = sorted(
        feature_importance.items(), key=lambda x: abs(x[1]), reverse=True
    )
    top_5 = [f[0] for f in sorted_features[:5]]

    sensitive_list = ['insured_sex', 'age']
    sensitive_in_top5 = [f for f in top_5 if f in sensitive_list]

    return {
        "top_features": top_5,
        "feature_importance": feature_importance,
        "sensitive_features_in_top5": sensitive_in_top5,
        "ground_truth_vector": instance_shap.tolist()
    }


if __name__ == "__main__":
    print("SHAP Engine loaded successfully. Use get_shap_explanation().")
