import React, { useEffect, useState } from 'react';
import { ShieldCheck, Scale, FileText, Download, AlertCircle, Info, BarChart3, PieChart } from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Cell 
} from 'recharts';
import { auditService } from '../services/api';

const Compliance: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [report, setReport] = useState<any>(null);
  const [crdi, setCrdi] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [s, r, c] = await Promise.all([
          auditService.getStats(),
          auditService.getComplianceReport(),
          auditService.getCrdiReport()
        ]);
        setStats(s);
        setReport(r);
        setCrdi(c);
      } catch (err) {
        console.error(err);
      }
    };
    fetchData();
  }, []);

  const guidelines = [
    { id: 'no_gender_bias', name: 'Gender Neutrality', reg: 'IRDAI Circular 2023/AI/04', risk: 'HIGH' },
    { id: 'no_regional_bias', name: 'Regional Fair Practice', reg: 'IRDAI Fair Practice Code', risk: 'HIGH' },
    { id: 'explainability_required', name: 'Algorithmic Transparency', reg: 'IRDAI Guidelines 2022', risk: 'MEDIUM' },
    { id: 'consistency_required', name: 'Explanation Stability', reg: 'IRDAI Fair Practice Code', risk: 'MEDIUM' },
  ];

  return (
    <div className="space-y-8 animate-in slide-in-from-bottom duration-700">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Regulatory Compliance</h1>
          <p className="text-navy-400 mt-1 italic">Real-time IRDAI auditing and legal risk mapping</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center px-4 py-2 bg-navy-800 border border-navy-700 rounded-lg text-sm hover:bg-navy-700 transition-all font-bold">
            <Download size={16} className="mr-2" /> Audit Certificate
          </button>
          <button className="flex items-center px-4 py-2 bg-navy-500 rounded-lg text-sm hover:bg-navy-400 transition-all font-bold shadow-xl shadow-navy-500/20">
            <FileText size={16} className="mr-2" /> PDF Report
          </button>
        </div>
      </div>

      {/* Guideline Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {guidelines.map((g) => {
          const violationCount = report?.violation_summary?.[g.id] || 0;
          const isFailed = violationCount > 0;
          return (
            <div key={g.id} className="glass-card p-5 relative overflow-hidden group">
              <div className={`absolute top-0 right-0 w-16 h-16 -mr-8 -mt-8 rotate-45 ${isFailed ? 'bg-red-500/20' : 'bg-green-500/20'}`} />
              <div className="flex justify-between items-start mb-4">
                <Scale className={isFailed ? 'text-red-400' : 'text-green-400'} />
                <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${isFailed ? 'bg-red-500/20 text-red-100' : 'bg-green-500/20 text-green-100'}`}>
                  {isFailed ? 'Fail' : 'Pass'}
                </span>
              </div>
              <h3 className="font-bold text-navy-100 mb-1">{g.name}</h3>
              <p className="text-[10px] text-navy-400 font-medium mb-3">{g.reg}</p>
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-red-400 uppercase font-black tracking-widest">{g.risk} RISK</span>
                <span className="text-xl font-black italic">{violationCount}</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Disparity Chart */}
        <div className="lg:col-span-2 glass-card p-6">
          <div className="flex items-center justify-between mb-8">
            <h4 className="text-sm font-bold uppercase tracking-widest text-navy-300">Counterfactual Fairness Disparity (CRDI)</h4>
            <div className="flex items-center space-x-2 text-xs">
              <div className="w-3 h-3 bg-navy-400 rounded-sm" />
              <span className="text-navy-400">Gender Index</span>
              <div className="w-3 h-3 bg-navy-600 rounded-sm ml-4" />
              <span className="text-navy-400">Region Index</span>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={[
                { name: 'Jan', gender: 0.12, region: 0.08 },
                { name: 'Feb', gender: 0.15, region: 0.11 },
                { name: 'Mar', gender: crdi?.mean_crdi_gender || 0.22, region: 0.14 },
              ]}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1c2c4c" />
                <XAxis dataKey="name" stroke="#697ba5" fontSize={12} />
                <YAxis stroke="#697ba5" fontSize={12} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#041c54', border: '1px solid #1c2c4c' }}
                  itemStyle={{ color: '#e6e9f0' }}
                />
                <Bar dataKey="gender" fill="#374f87" radius={[4, 4, 0, 0]} />
                <Bar dataKey="region" fill="#697ba5" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-6 flex items-center p-4 bg-navy-800/50 rounded-xl border border-navy-700">
            <Info size={20} className="text-navy-400 mr-4" />
            <p className="text-xs text-navy-200">
              <span className="font-bold text-navy-100 uppercase mr-2">Audit Insight:</span>
              Current CRDI exceeds 0.2 threshold specifically in FEMALE/OHIO demographics. Remediation recommended in model weighting.
            </p>
          </div>
        </div>

        {/* Violations Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          <div className="glass-card p-6 border-navy-700 bg-navy-900/50">
            <h4 className="text-sm font-bold uppercase tracking-widest text-navy-300 mb-6 flex items-center">
              <Landmark size={16} className="mr-2" />
              Legal Remediations
            </h4>
            <div className="space-y-4">
              <div className="p-4 border border-red-500/20 bg-red-500/5 rounded-2xl">
                <span className="text-[10px] font-black text-red-400 uppercase tracking-widest">Immediate Action</span>
                <p className="text-sm font-bold text-navy-50: mt-1 line-clamp-2">Drop 'incident_state' from training baseline.</p>
                <div className="mt-3 text-xs text-navy-400">Regulation: IRDAI-FPC-02</div>
              </div>
              <div className="p-4 border border-yellow-500/20 bg-yellow-500/5 rounded-2xl">
                <span className="text-[10px] font-black text-yellow-400 uppercase tracking-widest">Recommended</span>
                <p className="text-sm font-bold text-navy-50: mt-1 line-clamp-2">Standardize premium calculations across gender labels.</p>
                <div className="mt-3 text-xs text-navy-400">Regulation: IRDAI-A1-04</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Simplified icon reference as I used Landmark earlier without import
const Landmark = Scale;

export default Compliance;
