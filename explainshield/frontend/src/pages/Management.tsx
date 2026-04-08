import React, { useEffect, useState } from 'react';
import { 
  BarChart3, TrendingUp, Users, AlertTriangle, 
  Wallet, PieChart, ArrowUpRight, ArrowDownRight,
  ShieldCheck, Landmark, Download, FileText
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, LineChart, Line,
  PieChart as RePieChart, Pie, Cell
} from 'recharts';
import { auditService } from '../services/api';

const Management: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [s, l] = await Promise.all([
          auditService.getStats(),
          auditService.getAuditLogs(50)
        ]);
        setStats(s);
        setLogs(l);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const timeSeriesData = stats?.time_series?.map((entry: any) => ({
    date: new Date(entry.timestamp * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    score: entry.trust_score
  })) || [];

  const verdictCounts = { SAFE: 0, REVIEW: 0, UNSAFE: 0 };
  logs.forEach(log => {
    const v = log.verdict || log.results?.verdict;
    if (v === 'SAFE') verdictCounts.SAFE++;
    else if (v === 'REVIEW') verdictCounts.REVIEW++;
    else if (v === 'UNSAFE') verdictCounts.UNSAFE++;
  });

  const total = verdictCounts.SAFE + verdictCounts.REVIEW + verdictCounts.UNSAFE || 1;
  const pieData = [
    { name: 'Safe', value: verdictCounts.SAFE, color: '#22c55e' },
    { name: 'Review', value: verdictCounts.REVIEW, color: '#eab308' },
    { name: 'Unsafe', value: verdictCounts.UNSAFE, color: '#ef4444' }
  ];

  const kpis = [
    { name: 'Total Claims Audited', value: stats?.total_audits || 0, trend: '+12%', icon: Users },
    { name: 'Average Trust Index', value: `${Math.round((stats?.avg_trust_score || 0) * 100)}%`, trend: '+2.5%', icon: ShieldCheck },
    { name: 'Compliance Failure Rate', value: `${Math.round(((stats?.compliance_failures || 0) / (stats?.total_audits || 1)) * 100)}%`, trend: '-1.4%', icon: AlertTriangle, negative: true },
    { name: 'Estimated Fine Exposure', value: `₹ ${((stats?.compliance_failures || 0) * 250000).toLocaleString()}`, trend: '+5%', icon: Wallet, negative: true },
  ];

  const getRiskProfile = () => {
    const rate = (stats?.compliance_failures || 0) / (stats?.total_audits || 1);
    if (rate < 0.1) return { label: 'LOW (SAFE)', color: 'green' };
    if (rate < 0.3) return { label: 'MEDIUM (REVIEW)', color: 'yellow' };
    return { label: 'HIGH (UNSAFE)', color: 'red' };
  };

  const riskProfile = getRiskProfile();

  return (
    <div className="space-y-8 animate-in fade-in duration-1000">
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-navy-400"></div>
        </div>
      ) : (
        <>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-4xl font-extrabold tracking-tighter uppercase italic">Executive Command</h1>
              <p className="text-navy-400 mt-1 font-medium tracking-wide">Risk Assessment & Strategic AI Oversight</p>
            </div>
            <div className="bg-navy-800 p-2 rounded-2xl flex items-center space-x-2 border border-navy-700">
               <span className="text-[10px] font-black uppercase text-navy-400 ml-2">Current Risk Profile</span>
               <div className={`px-4 py-1 text-sm font-black rounded-xl border ${
                 riskProfile.color === 'green' ? 'bg-green-500/20 text-green-400 border-green-500/30' :
                 riskProfile.color === 'yellow' ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' :
                 'bg-red-500/20 text-red-400 border-red-500/30'
               }`}>{riskProfile.label}</div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {kpis.map((kpi, idx) => {
              const Icon = kpi.icon;
              return (
                <div key={idx} className="glass-card p-6 border-b-4 border-b-navy-500 group hover:translate-y-[-4px] transition-all duration-300">
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-3 bg-navy-800 rounded-2xl group-hover:bg-navy-700 transition-colors">
                      <Icon className="text-navy-400" size={24} />
                    </div>
                    <div className={`flex items-center text-xs font-bold ${kpi.negative ? 'text-red-400' : 'text-green-400'}`}>
                      {kpi.trend}
                    </div>
                  </div>
                  <p className="text-xs font-black uppercase tracking-widest text-navy-400 mb-1">{kpi.name}</p>
                  <h3 className="text-3xl font-black italic tracking-tighter text-white">{kpi.value}</h3>
                </div>
              );
            })}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="glass-card p-8 bg-navy-900/40">
              <div className="flex items-center justify-between mb-10">
                <h4 className="text-xs font-black uppercase tracking-widest text-navy-300">
                  Trust Score History
                </h4>
                <div className="flex items-center space-x-2">
                   <div className="w-3 h-3 bg-navy-400 rounded-full" />
                   <span className="text-[10px] font-black uppercase text-navy-400">Mean Trust Index</span>
                </div>
              </div>
              <div className="h-72">
                {timeSeriesData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={timeSeriesData}>
                      <defs>
                        <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#374f87" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#374f87" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1c2c4c" vertical={false} />
                      <XAxis dataKey="date" stroke="#697ba5" fontSize={10} fontWeight="bold" />
                      <YAxis stroke="#697ba5" fontSize={10} fontWeight="bold" domain={[0.5, 1]} />
                      <Tooltip 
                         contentStyle={{ backgroundColor: '#041c54', border: '1px solid #1c2c4c', borderRadius: '12px' }}
                         itemStyle={{ color: '#e6e9f0', fontWeight: 'bold' }}
                      />
                      <Area type="monotone" dataKey="score" stroke="#374f87" strokeWidth={4} fillOpacity={1} fill="url(#colorScore)" />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-navy-500">
                    <p className="text-sm">No audit history yet. Run audits to see trends.</p>
                  </div>
                )}
              </div>
            </div>

            <div className="glass-card p-8 flex flex-col justify-between">
              <div className="flex items-center justify-between mb-8">
                <h4 className="text-xs font-black uppercase tracking-widest text-navy-300">Audit Verdict Distribution</h4>
                <Landmark className="text-navy-500" size={20} />
              </div>
              
              {total > 0 ? (
                <div className="flex items-center justify-center">
                  <ResponsiveContainer width="100%" height={200}>
                    <RePieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#041c54', border: '1px solid #1c2c4c', borderRadius: '8px' }}
                      />
                    </RePieChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-48 flex items-center justify-center text-navy-500">
                  <p className="text-sm">No audit data available</p>
                </div>
              )}

              <div className="space-y-3 mt-4">
                <div className="flex justify-between text-xs font-black uppercase text-navy-200">
                  <span className="flex items-center"><span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>Safe & Compliant</span>
                  <span>{Math.round((verdictCounts.SAFE / total) * 100)}%</span>
                </div>
                <div className="flex justify-between text-xs font-black uppercase text-navy-200">
                  <span className="flex items-center"><span className="w-2 h-2 bg-yellow-400 rounded-full mr-2"></span>Review Required</span>
                  <span>{Math.round((verdictCounts.REVIEW / total) * 100)}%</span>
                </div>
                <div className="flex justify-between text-xs font-black uppercase text-navy-200">
                  <span className="flex items-center"><span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>Unsafe / High Risk</span>
                  <span>{Math.round((verdictCounts.UNSAFE / total) * 100)}%</span>
                </div>
              </div>

              <div className="mt-8 flex space-x-4">
                <button className="flex-1 py-3 bg-navy-800 border border-navy-600 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-navy-700 transition-colors" disabled>
                  <Download size={14} className="inline mr-1" /> Board Report
                </button>
                <button className="flex-1 py-3 bg-navy-500 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-navy-400 transition-shadow shadow-xl shadow-navy-500/20" disabled>
                  <FileText size={14} className="inline mr-1" /> Stakeholder View
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Management;