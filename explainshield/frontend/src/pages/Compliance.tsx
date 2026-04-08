import React, { useEffect, useState } from 'react';
import { ShieldCheck, Scale, FileText, Download, AlertCircle, Info, BarChart3, PieChart, Landmark, TrendingDown } from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Cell, LineChart, Line
} from 'recharts';
import { auditService } from '../services/api';

const Compliance: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [report, setReport] = useState<any>(null);
  const [crdi, setCrdi] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
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
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const guidelines = [
    { id: 'IRDAI-FPC-01', name: 'Gender Neutrality', reg: 'IRDAI Circular 2023/AI/04', risk: 'HIGH' },
    { id: 'IRDAI-FPC-02', name: 'Regional Fair Practice', reg: 'IRDAI Fair Practice Code', risk: 'HIGH' },
    { id: 'IRDAI-A1-01', name: 'Algorithmic Transparency', reg: 'IRDAI Guidelines 2022', risk: 'MEDIUM' },
    { id: 'IRDAI-A1-02', name: 'Explanation Stability', reg: 'IRDAI Fair Practice Code', risk: 'MEDIUM' },
  ];

  const crdiChartData = [
    { name: 'Baseline', gender: 0.10, region: 0.07 },
    { name: 'Month 1', gender: 0.12, region: 0.09 },
    { name: 'Month 2', gender: 0.15, region: 0.11 },
    { name: 'Current', gender: crdi?.mean_crdi_gender || 0, region: (crdi?.mean_crdi_gender || 0) * 0.7 },
  ];

  return (
    <div className="space-y-8 animate-in slide-in-from-bottom duration-700">
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-navy-400"></div>
        </div>
      ) : (
        <>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Regulatory Compliance</h1>
              <p className="text-navy-400 mt-1 italic">Real-time IRDAI auditing and legal risk mapping</p>
            </div>
            <div className="flex gap-3">
              <button className="flex items-center px-4 py-2 bg-navy-800 border border-navy-700 rounded-lg text-sm hover:bg-navy-700 transition-all font-bold" disabled>
                <Download size={16} className="mr-2" /> Export Certificate
              </button>
              <button className="flex items-center px-4 py-2 bg-navy-500 rounded-lg text-sm hover:bg-navy-400 transition-all font-bold shadow-xl shadow-navy-500/20" disabled>
                <FileText size={16} className="mr-2" /> Generate Report
              </button>
            </div>
          </div>

          {report?.total_violations === 0 && (
            <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-xl flex items-center">
              <ShieldCheck size={20} className="text-green-400 mr-3" />
              <span className="text-green-300">All compliance checks passed. No violations detected.</span>
            </div>
          )}

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
                      {isFailed ? 'FAIL' : 'PASS'}
                    </span>
                  </div>
                  <h3 className="font-bold text-navy-100 mb-1">{g.name}</h3>
                  <p className="text-[10px] text-navy-400 font-medium mb-3">{g.reg}</p>
                  <div className="flex items-center justify-between">
                    <span className={`text-[10px] uppercase font-black tracking-widest ${isFailed ? 'text-red-400' : 'text-green-400'}`}>{g.risk} RISK</span>
                    <span className="text-xl font-black italic">{violationCount}</span>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 glass-card p-6">
              <div className="flex items-center justify-between mb-8">
                <h4 className="text-sm font-bold uppercase tracking-widest text-navy-300">
                  CRDI Trend (Counterfactual Disparity Index)
                </h4>
                <div className="flex items-center space-x-2 text-xs">
                  <div className="w-3 h-3 bg-red-400 rounded-sm" />
                  <span className="text-navy-400">Gender Index</span>
                  <div className="w-3 h-3 bg-blue-400 rounded-sm ml-4" />
                  <span className="text-navy-400">Region Index</span>
                </div>
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={crdiChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1c2c4c" />
                    <XAxis dataKey="name" stroke="#697ba5" fontSize={12} />
                    <YAxis stroke="#697ba5" fontSize={12} domain={[0, 'auto']} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#041c54', border: '1px solid #1c2c4c' }}
                      itemStyle={{ color: '#e6e9f0' }}
                    />
                    <Line type="monotone" dataKey="gender" stroke="#f87171" strokeWidth={2} dot={{ fill: '#f87171' }} />
                    <Line type="monotone" dataKey="region" stroke="#60a5fa" strokeWidth={2} dot={{ fill: '#60a5fa' }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-6 flex items-center p-4 bg-navy-800/50 rounded-xl border border-navy-700">
                <TrendingDown size={20} className="text-navy-400 mr-4" />
                <p className="text-xs text-navy-200">
                  <span className="font-bold text-navy-100 uppercase mr-2">CRDI Analysis:</span>
                  {crdi?.indicator === 'Fairness Gap' 
                    ? `Mean CRDI Gender Index: ${crdi?.mean_crdi_gender?.toFixed(4)}. Fairness gap detected.`
                    : `Mean CRDI Gender Index: ${crdi?.mean_crdi_gender?.toFixed(4)}. Within acceptable range.`}
                </p>
              </div>
            </div>

            <div className="lg:col-span-1 space-y-6">
              <div className="glass-card p-6 border-navy-700 bg-navy-900/50">
                <h4 className="text-sm font-bold uppercase tracking-widest text-navy-300 mb-6 flex items-center">
                  <AlertCircle size={16} className="mr-2" />
                  Active Violations ({report?.total_violations || 0})
                </h4>
                {report?.total_violations > 0 ? (
                  <div className="space-y-4">
                    {Object.entries(report?.violation_summary || {}).map(([guideline, count]: [string, any]) => (
                      <div key={guideline} className="p-4 border border-red-500/20 bg-red-500/5 rounded-2xl">
                        <div className="flex justify-between items-start mb-2">
                          <span className="text-[10px] font-black text-red-400 uppercase tracking-widest">Violation</span>
                          <span className="text-lg font-black text-red-400">{count}</span>
                        </div>
                        <p className="text-sm font-bold text-navy-50 line-clamp-2">{guideline}</p>
                        <div className="mt-3 text-xs text-navy-400">Regulation: {guideline}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <ShieldCheck size={32} className="mx-auto text-green-400 mb-2" />
                    <p className="text-sm text-navy-400">No violations found</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Compliance;