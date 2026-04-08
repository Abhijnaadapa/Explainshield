export interface Claim {
  claim_id: string;
  features: Record<string, any>;
  status: string;
  created_at?: number;
}

export interface ClaimList {
  claims: Claim[];
  total: number;
}

export interface AuditResult {
  claim_id: string;
  model_prediction: string;
  model_confidence: number;
  verdict: 'SAFE' | 'REVIEW' | 'UNSAFE';
  trust_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  validated_explanation: string;
  bias_flag: boolean;
  compliance_status: 'COMPLIANT' | 'AT_RISK' | 'NON_COMPLIANT';
  action_required: string;
  scores: {
    faithfulness: number;
    bias: number;
    consistency: number;
    grounding: number;
    afs: number;
    lbid_bias_probability: number;
    crdi_gender: number;
    crdi_region: number;
    shap_feature_importance?: Record<string, number>;
  };
  fair_explanations?: string[];
  adversarial_explanation?: string;
  violations: Array<{
    guideline: string;
    regulation: string;
    status: string;
    evidence: string;
    legal_risk: string;
    remediation: string;
  }>;
  counterfactual_summary: string;
  audit_id: string;
  top_shap_features?: string[];
}

export interface AuditStats {
  avg_trust_score: number;
  total_audits: number;
  bias_events: number;
  compliance_failures: number;
  time_series?: Array<{
    timestamp: number;
    trust_score: number;
    verdict: string;
  }>;
}

export interface ComplianceReport {
  violation_summary: Record<string, number>;
  total_violations: number;
  company_id: string;
}
