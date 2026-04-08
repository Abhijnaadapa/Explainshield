import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report
import xgboost as xgb
import joblib
import os

def train_model():
    # Load dataset
    data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'insurance_claims.csv')
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    df = pd.read_csv(data_path)
    
    # Drop columns that are definitely not features or have too much missing data
    # (The user specifically asked to drop missing values, we'll replace '?' with NaN first)
    df.replace('?', np.nan, inplace=True)

    # Specific Categorical Columns to encode
    cat_cols = [
        'insured_sex', 'insured_education_level', 
        'incident_type', 'incident_severity', 
        'incident_state', 'policy_csl', 
        'insured_occupation', 'insured_relationship'
    ]
    
    # Specific Numerical Columns to scale
    num_cols = [
        'age', 'policy_annual_premium', 
        'total_claim_amount', 'months_as_customer', 
        'number_of_vehicles_involved', 'witnesses'
    ]

    target_col = 'fraud_reported'

    # Drop missing values only for the important features and target
    df.dropna(subset=cat_cols + num_cols + [target_col], inplace=True)

    # Save encoders for reuse in SHAP engine
    encoders = {}
    for col in cat_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        encoders[col] = le
        
    # Standardize target (Y/N -> 1/0)
    # Fraud Detection: Y = 1, N = 0
    df[target_col] = df[target_col].apply(lambda x: 1 if x == 'Y' else 0)

    # Scale numerical columns
    scaler = StandardScaler()
    df[num_cols] = scaler.fit_transform(df[num_cols])

    # Select features
    features = cat_cols + num_cols
    X = df[features]
    y = df[target_col]

    # Split dataset
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train XGBoost Classifier
    # Compute scale_pos_weight for better reliability in fraud detection (imbalanced data)
    pos_count = sum(y_train)
    neg_count = len(y_train) - pos_count
    scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1

    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
        scale_pos_weight=scale_pos_weight,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    print("Classification Report:")
    print(classification_report(y_test, y_pred))

    # Bias Metrics (Baseline)
    # Approval rate = 1 - Fraud Rate (where fraud_reported is 'N')
    # Note: Predicting 0 (N) means approval. 
    # We want to see how often the model classifies a claim as non-fraud (0) based on protected attributes.
    
    # Re-attach labels to test set for bias analysis
    test_analysis = X_test.copy()
    test_analysis['actual'] = y_test
    test_analysis['predicted'] = y_pred
    
    # Decode categorical columns for readable printing
    for col in ['insured_sex', 'incident_state']:
        test_analysis[col] = encoders[col].inverse_transform(test_analysis[col])

    print("\nBaseline Bias Metrics:")
    
    def get_approval_rate(group):
        # Approval means predicting 0 (Non-Fraud)
        return (group['predicted'] == 0).mean()

    print("\nApproval Rate by Insured Sex:")
    sex_approval = test_analysis.groupby('insured_sex').apply(get_approval_rate)
    print(sex_approval)

    print("\nApproval Rate by Incident State:")
    state_approval = test_analysis.groupby('incident_state').apply(get_approval_rate)
    print(state_approval)

    # Save artifacts
    save_dir = 'backend/model'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    joblib.dump(model, os.path.join(save_dir, 'insurance_model.pkl'))
    joblib.dump(features, os.path.join(save_dir, 'feature_names.pkl'))
    joblib.dump(scaler, os.path.join(save_dir, 'scaler.pkl'))
    joblib.dump(encoders, os.path.join(save_dir, 'encoders.pkl'))
    
    print(f"\nModel and artifacts saved to {save_dir}/")

if __name__ == "__main__":
    train_model()
