import React, { useState } from 'react';
import { 
  Plus, Send, Activity, Info, 
  CheckCircle2, AlertCircle, XCircle, 
  TrendingUp, Fingerprint, ShieldCheck, Landmark 
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Cell, PieChart, Pie 
} from 'recharts';
import { auditService } from '../services/api';
import { AuditResult } from '../types';

const TechTeam: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AuditResult | null>(null);
  
  // Default values for insurance fraud dataset
  const [formData, setFormData] = useState({
    age: 48,
    policy_annual_premium: 1406.91,
    months_as_customer: 248,
    total_claim_amount: 71610,
    insured_sex: 'MALE',
    incident_state: 'OH',
    insured_education_level: 'Bachelor',
    incident_severity: 'Major Damage',
    incident_type: 'Multi-vehicle Collision',
    policy_csl: '250/500',
    insured_occupation: 'machine-op-inspct',
    insured_relationship: 'husband',
    number_of_vehicles_involved: 3,
    witnesses: 2
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await auditService.auditClaim(formData, "Rejected", 0.73);
      setResult(res);
    } catch (err) {
      console.error(err);
      alert("Audit Pipeline Error. Check backend logs.");
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

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Technical Auditor</h1>
          <p className="text-navy-400 mt-1 italic">Deep-dive into AI decision faithfulness and bias injection</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Form */}
        <div className="lg:col-span-1 space-y-6">
          <div className="glass-card p-6 border border-navy-700">
            <div className="flex items-center space-x-3 mb-6">
              <Plus className="text-navy-400" />
              <h2 className="text-lg font-semibold uppercase tracking-widest text-navy-200">Manual Claim Audit</h2>
            </div>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              {Object.entries(formData).map(([key, value]) => (
                <div key={key}>
                  <label className="block text-xs font-medium text-navy-400 uppercase mb-1.5 ml-1">
                    {key.replace(/_/g, ' ')}
                  </label>
                  <input
                    type={typeof value === 'number' ? 'number' : 'text'}
                    value={value}
                    onChange={(e) => setFormData({...formData, [key]: e.target.value})}
                    className="w-full bg-navy-800/50 border border-navy-600 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-navy-500 transition-all"
                  />
                </div>
              ))}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-4 bg-navy-500 hover:bg-navy-400 disabled:opacity-50 text-white rounded-xl font-bold transition-all shadow-xl shadow-navy-500/20 flex items-center justify-center space-x-2"
              >
                {loading ? <Activity className="animate-spin" /> : <Send size={20} />}
                <span>{loading ? "SIMULATING PIPELINE..." : "RUN AUDIT"}</span>
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Results */}
        <div className="lg:col-span-2 space-y-8">
          {!result ? (
            <div className="h-full flex flex-col items-center justify-center border-2 border-dashed border-navy-700 rounded-3xl p-12 text-navy-500">
              <Landmark size={64} className="mb-4 opacity-20" />
              <p className="text-lg font-medium">Input claim features to generate audit report</p>
            </div>
          ) : (
            <>
              {/* Verdict Banner */}
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
                {/* Score Breakdown */}
                <div className="glass-card p-6">
                  <h4 className="text-sm font-bold uppercase tracking-widest text-navy-300 mb-6 flex items-center">
                    <Activity size={16} className="mr-2" />
                    Validation Matrices
                  </h4>
                  <div className="space-y-4">
                    {Object.entries(result.scores).map(([name, score]) => (
                      <div key={name}>
                        <div className="flex justify-between text-xs mb-1.5 px-1">
                          <span className="uppercase text-navy-400 font-bold">{name.replace(/_/g, ' ')}</span>
                          <span className={`${score > 0.6 ? 'text-green-400' : 'text-red-400'} font-black italic`}>{Math.round(score * 100)}%</span>
                        </div>
                        <div className="h-1.5 w-full bg-navy-800 rounded-full overflow-hidden">
                          <div 
                            className={`h-full transition-all duration-1000 ${score > 0.6 ? 'bg-navy-400' : 'bg-red-500'}`}
                            style={{ width: `${score * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Audit Evidence (Novel Metrics) */}
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

              {/* Explanations */}
              <div className="glass-card p-6 border-l-4 border-l-navy-500 shadow-xl">
                <h4 className="text-sm font-bold uppercase tracking-widest text-navy-300 mb-4 flex items-center italic">
                  <ShieldCheck size={18} className="mr-2 text-navy-400" />
                  Validated Audit Explanation
                </h4>
                <p className="text-navy-100 leading-relaxed italic text-lg p-4 bg-navy-800/30 rounded-2xl">
                  "{result.validated_explanation}"
                </p>
              </div>

              {/* Counterfactual Summary */}
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
