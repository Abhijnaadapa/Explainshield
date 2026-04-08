import React, { useState, useEffect } from 'react';
import { 
  Plus, Send, Activity, Info, 
  CheckCircle2, AlertCircle, XCircle, 
  TrendingUp, Fingerprint, ShieldCheck, Landmark, 
  ChevronDown, RefreshCw
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { claimsService, auditService } from '../services/api';
import { AuditResult, Claim } from '../types';

const TechTeam: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AuditResult | null>(null);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [selectedClaimId, setSelectedClaimId] = useState<string>('');
  const [seeding, setSeeding] = useState(false);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadClaims();
  }, []);

  const loadClaims = async () => {
    try {
      const data = await claimsService.listClaims(50);
      setClaims(data.claims || []);
      if (data.claims?.length > 0 && !selectedClaimId) {
        setSelectedClaimId(data.claims[0].claim_id);
      }
    } catch (err: any) {
      console.error('Failed to load claims:', err);
    }
  };

  const handleSeed = async () => {
    setSeeding(true);
    try {
      await claimsService.seedClaims();
      await loadClaims();
    } catch (err) {
      console.error('Failed to seed claims:', err);
    } finally {
      setSeeding(false);
    }
  };

  const handleAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClaimId) {
      setError('Please select a claim');
      return;
    }
    setLoading(true);
    setError('');
    setResult(null);
    try {
      console.log("Running audit for claim:", selectedClaimId);
      const res = await claimsService.auditClaim(selectedClaimId);
      console.log("Audit response:", res);
      setResult(res);
    } catch (err: any) {
      console.error("Audit error:", err);
      const msg = err.response?.data?.detail || err.message || "Unknown error";
      setError(`Audit Pipeline Error: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  const getVerdictColor = (v: string) => {
    switch(v) {
      case 'SAFE': return 'text-green-400 bg-green-400/10 border-green-400/20';
      case 'REVIEW': return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20';
      case 'UNSAFE': return 'text-red-400 bg-red-400/10 border-red-400/20';
      default: return 'text-navy-300 bg-navy-800 border-navy-700';
    }
  };

  const shapData = result?.scores?.shap_feature_importance 
    ? Object.entries(result.scores.shap_feature_importance)
        .map(([name, value]) => ({ feature: name, value: Math.abs(value) }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 10)
    : [];

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Technical Auditor</h1>
          <p className="text-navy-400 mt-1 italic">Deep-dive into AI decision faithfulness and bias injection</p>
        </div>
        <button
          onClick={handleSeed}
          disabled={seeding}
          className="flex items-center space-x-2 px-4 py-2 bg-navy-700 hover:bg-navy-600 rounded-lg text-sm"
        >
          <RefreshCw size={16} className={seeding ? 'animate-spin' : ''} />
          <span>{seeding ? 'Seeding...' : 'Load Sample Claims'}</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-xl text-red-300">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 space-y-6">
          <div className="glass-card p-6 border border-navy-700">
            <div className="flex items-center space-x-3 mb-6">
              <Plus className="text-navy-400" />
              <h2 className="text-lg font-semibold uppercase tracking-widest text-navy-200">Claim Queue</h2>
            </div>
            
            <form onSubmit={handleAudit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-navy-400 uppercase mb-1.5 ml-1">
                  Select Claim ID
                </label>
                <div className="relative">
                  <select
                    value={selectedClaimId}
                    onChange={(e) => setSelectedClaimId(e.target.value)}
                    className="w-full bg-navy-800/50 border border-navy-600 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-navy-500 appearance-none"
                  >
                    <option value="">-- Select a claim --</option>
                    {claims.map((claim) => (
                      <option key={claim.claim_id} value={claim.claim_id}>
                        {claim.claim_id} - {claim.status}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-3 top-3 text-navy-400" size={16} />
                </div>
              </div>

              {selectedClaimId && claims.find(c => c.claim_id === selectedClaimId) && (
                <div className="p-3 bg-navy-800/50 rounded-lg border border-navy-700">
                  <p className="text-xs text-navy-500 uppercase mb-2">Features</p>
                  <div className="text-xs text-navy-300 space-y-1">
                    {Object.entries(claims.find(c => c.claim_id === selectedClaimId)?.features || {}).slice(0, 5).map(([k, v]) => (
                      <div key={k} className="flex justify-between">
                        <span className="text-navy-500">{k}:</span>
                        <span>{String(v).substring(0, 15)}</span>
                      </div>
                    ))}
                    <p className="text-navy-600 italic">...and more</p>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={loading || !selectedClaimId}
                className="w-full py-3 px-4 bg-navy-500 hover:bg-navy-400 disabled:opacity-50 text-white rounded-xl font-bold transition-all shadow-xl shadow-navy-500/20 flex items-center justify-center space-x-2"
              >
                {loading ? <Activity className="animate-spin" /> : <Send size={20} />}
                <span>{loading ? "RUNNING PIPELINE..." : "RUN AUDIT"}</span>
              </button>
            </form>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-8">
          {!result ? (
            <div className="h-full flex flex-col items-center justify-center border-2 border-dashed border-navy-700 rounded-3xl p-12 text-navy-500">
              <Landmark size={64} className="mb-4 opacity-20" />
              <p className="text-lg font-medium">Select a claim to generate audit report</p>
            </div>
          ) : (
            <>
              <div className={`p-6 rounded-2xl border-2 flex items-center justify-between ${getVerdictColor(result.verdict)}`}>
                <div className="flex items-center space-x-4">
                  {result.verdict === 'SAFE' ? <CheckCircle2 size={32} /> : result.verdict === 'REVIEW' ? <AlertCircle size={32} /> : <XCircle size={32} />}
                  <div>
                    <h3 className="text-2xl font-black italic tracking-tighter uppercase">Audit: {result.verdict}</h3>
                    <p className="text-sm opacity-80 mt-0.5">Risk Level: {result.risk_level.toUpperCase()}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-4xl font-black italic">{Math.round(result.trust_score * 100)}%</div>
                  <div className="text-xs uppercase tracking-widest font-bold">Trust Index</div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass-card p-6">
                  <h4 className="text-sm font-bold uppercase tracking-widest text-navy-300 mb-4 flex items-center">
                    <Activity size={16} className="mr-2" />
                    Model Output
                  </h4>
                  <div className="space-y-3">
                    <div className="p-3 bg-navy-800/50 rounded-xl border border-navy-700">
                      <p className="text-[10px] text-navy-500 uppercase font-black mb-1">Prediction</p>
                      <p className={`text-sm font-bold ${result.model_prediction === 'Approved' ? 'text-green-400' : 'text-red-400'}`}>
                        {result.model_prediction}
                      </p>
                    </div>
                    <div className="p-3 bg-navy-800/50 rounded-xl border border-navy-700">
                      <p className="text-[10px] text-navy-500 uppercase font-black mb-1">Confidence</p>
                      <p className="text-sm font-bold text-navy-200">{Math.round(result.model_confidence * 100)}%</p>
                    </div>
                  </div>
                </div>

                <div className="glass-card p-6">
                  <h4 className="text-sm font-bold uppercase tracking-widest text-navy-300 mb-4 flex items-center">
                    <Fingerprint size={16} className="mr-2" />
                    System Signals
                  </h4>
                  <div className="space-y-3">
                    <div className="p-3 bg-navy-800/50 rounded-xl border border-navy-700">
                      <p className="text-[10px] text-navy-500 uppercase font-black mb-1">Compliance Status</p>
                      <p className={`text-sm font-bold ${result.compliance_status === 'COMPLIANT' ? 'text-green-400' : 'text-yellow-400'}`}>{result.compliance_status}</p>
                    </div>
                    <div className="p-3 bg-navy-800/50 rounded-xl border border-navy-700">
                      <p className="text-[10px] text-navy-500 uppercase font-black mb-1">Bias Injection Flag</p>
                      <p className={`text-sm font-bold ${result.bias_flag ? 'text-red-400' : 'text-green-400'}`}>
                        {result.bias_flag ? "POSSIBLE THREAT DETECTED" : "NO THREAT DETECTED"}
                      </p>
                    </div>
                    <div className="p-3 bg-navy-800/50 rounded-xl border border-navy-700">
                      <p className="text-[10px] text-navy-500 uppercase font-black mb-1">Action Protocol</p>
                      <p className="text-sm font-bold text-navy-200">{result.action_required}</p>
                    </div>
                  </div>
                </div>
              </div>

              {shapData.length > 0 && (
                <div className="glass-card p-6">
                  <h4 className="text-sm font-bold uppercase tracking-widest text-navy-300 mb-4 flex items-center">
                    <TrendingUp size={16} className="mr-2" />
                    SHAP Feature Importance
                  </h4>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={shapData} layout="vertical" margin={{ left: 20, right: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis type="number" stroke="#94a3b8" />
                      <YAxis dataKey="feature" type="category" width={120} stroke="#94a3b8" tick={{ fontSize: 10 }} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                        labelStyle={{ color: '#e2e8f0' }}
                      />
                      <Bar dataKey="value" fill="#6366f1" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {result.fair_explanations && result.fair_explanations.length > 0 && (
                <div className="glass-card p-6">
                  <h4 className="text-sm font-bold uppercase tracking-widest text-navy-300 mb-4 flex items-center">
                    <Info size={16} className="mr-2" />
                    Multi-Agent Explanations
                  </h4>
                  <div className="space-y-4">
                    {result.fair_explanations.map((exp, idx) => (
                      <div key={idx} className="p-3 bg-green-900/10 border border-green-900/30 rounded-xl">
                        <p className="text-[10px] text-green-500 uppercase font-black mb-1">Financial Agent {idx + 1}</p>
                        <p className="text-sm text-navy-200 italic">{exp}</p>
                      </div>
                    ))}
                    {result.adversarial_explanation && (
                      <div className="p-3 bg-red-900/10 border border-red-900/30 rounded-xl">
                        <p className="text-[10px] text-red-500 uppercase font-black mb-1">Adversarial Agent</p>
                        <p className="text-sm text-navy-200 italic">{result.adversarial_explanation}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass-card p-6">
                  <h4 className="text-sm font-bold uppercase tracking-widest text-navy-300 mb-6 flex items-center">
                    <Activity size={16} className="mr-2" />
                    Validation Matrices
                  </h4>
                  <div className="space-y-4">
                    {Object.entries(result.scores).filter(([k]) => k !== 'shap_feature_importance').map(([name, score]) => (
                      <div key={name}>
                        <div className="flex justify-between text-xs mb-1.5 px-1">
                          <span className="uppercase text-navy-400 font-bold">{name.replace(/_/g, ' ')}</span>
                          <span className={`${Number(score) > 0.6 ? 'text-green-400' : 'text-red-400'} font-black italic`}>
                            {typeof score === 'number' ? Math.round(score * 100) : score}%
                          </span>
                        </div>
                        <div className="h-1.5 w-full bg-navy-800 rounded-full overflow-hidden">
                          <div 
                            className={`h-full transition-all duration-1000 ${Number(score) > 0.6 ? 'bg-navy-400' : 'bg-red-500'}`}
                            style={{ width: `${Number(score) * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="glass-card p-6">
                  <h4 className="text-sm font-bold uppercase tracking-widest text-navy-300 mb-4 flex items-center">
                    <Fingerprint size={16} className="mr-2" />
                    Novel Metrics
                  </h4>
                  <div className="space-y-3">
                    <div className="p-3 bg-navy-800/50 rounded-xl border border-navy-700">
                      <p className="text-[10px] text-navy-500 uppercase font-black mb-1">CRDI Gender</p>
                      <p className="text-sm font-bold text-navy-200">{result.scores.crdi_gender?.toFixed(4)}</p>
                    </div>
                    <div className="p-3 bg-navy-800/50 rounded-xl border border-navy-700">
                      <p className="text-[10px] text-navy-500 uppercase font-black mb-1">CRDI Region</p>
                      <p className="text-sm font-bold text-navy-200">{result.scores.crdi_region?.toFixed(4)}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="glass-card p-6 border-l-4 border-l-navy-500 shadow-xl">
                <h4 className="text-sm font-bold uppercase tracking-widest text-navy-300 mb-4 flex items-center italic">
                  <ShieldCheck size={18} className="mr-2 text-navy-400" />
                  Validated Audit Explanation
                </h4>
                <p className="text-navy-100 leading-relaxed italic text-lg p-4 bg-navy-800/30 rounded-2xl">
                  "{result.validated_explanation}"
                </p>
              </div>

              {result.violations && result.violations.length > 0 && (
                <div className="glass-card p-6">
                  <h4 className="text-sm font-bold uppercase tracking-widest text-navy-300 mb-4 flex items-center">
                    <AlertCircle size={16} className="mr-2 text-red-400" />
                    IRDAI Compliance Violations
                  </h4>
                  <div className="space-y-3">
                    {result.violations.map((v, idx) => (
                      <div key={idx} className="p-4 border border-red-500/20 bg-red-500/5 rounded-2xl">
                        <div className="flex justify-between items-start mb-2">
                          <span className="text-xs font-black text-red-400 uppercase">{v.guideline}</span>
                          <span className="text-[10px] text-navy-500">{v.regulation}</span>
                        </div>
                        <p className="text-sm text-navy-100">{v.evidence}</p>
                        <div className="mt-3 text-xs text-navy-400">
                          <span className="font-bold">Remediation:</span> {v.remediation}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="glass-card p-6">
                <h4 className="text-sm font-bold uppercase tracking-widest text-navy-300 mb-4">Bias Flip Analysis (What-If)</h4>
                <div className="p-4 bg-red-900/10 border border-red-900/30 rounded-2xl">
                  <p className="text-sm text-red-100 italic">{result.counterfactual_summary}</p>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default TechTeam;