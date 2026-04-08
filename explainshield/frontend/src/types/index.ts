export interface AuditResult {
  claim_id: string;
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
  };
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
}

export interface AuditStats {
  avg_trust_score: number;
  total_audits: number;
  bias_events: number;
  compliance_failures: number;
}
