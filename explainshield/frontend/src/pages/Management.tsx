import React, { useEffect, useState } from 'react';
import { 
  BarChart3, TrendingUp, Users, AlertTriangle, 
  Wallet, PieChart, ArrowUpRight, ArrowDownRight,
  ShieldCheck, Landmark
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, LineChart, Line 
} from 'recharts';
import { auditService } from '../services/api';

const Management: React.FC = () => {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const s = await auditService.getStats();
        setStats(s);
      } catch (err) {
        console.error(err);
      }
    };
    fetchData();
  }, []);

  const kpis = [
    { name: 'Total Claims Audited', value: stats?.total_audits || 0, trend: '+12%', icon: Users },
    { name: 'Average Trust Index', value: `${Math.round((stats?.avg_trust_score || 0) * 100)}%`, trend: '+2.5%', icon: ShieldCheck },
    { name: 'Compliance Failure Rate', value: `${Math.round(((stats?.compliance_failures || 0) / (stats?.total_audits || 1)) * 100)}%`, trend: '-1.4%', icon: AlertTriangle, negative: true },
    { name: 'Estimated Fine Exposure', value: `₹ ${((stats?.compliance_failures || 0) * 250000).toLocaleString()}`, trend: '+5%', icon: Wallet, negative: true },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-1000">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tighter uppercase italic">Executive Command</h1>
          <p className="text-navy-400 mt-1 font-medium tracking-wide">Risk Assessment & Strategic AI Oversight</p>
        </div>
        <div className="bg-navy-800 p-2 rounded-2xl flex items-center space-x-2 border border-navy-700">
           <span className="text-[10px] font-black uppercase text-navy-400 ml-2">Current Risk Profile</span>
           <div className="px-4 py-1 bg-green-500/20 text-green-400 text-sm font-black rounded-xl border border-green-500/30">LOW (SAFE)</div>
        </div>
      </div>

      {/* KPI Cards */}
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
                  {kpi.negative ? <ArrowUpRight size={14} className="mr-1" /> : <ArrowUpRight size={14} className="mr-1" />}
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
        {/* Trend Area Chart */}
        <div className="glass-card p-8 bg-navy-900/40">
          <div className="flex items-center justify-between mb-10">
            <h4 className="text-xs font-black uppercase tracking-widest text-navy-300">30-Day Trust Trend</h4>
            <div className="flex items-center space-x-2">
               <div className="w-3 h-3 bg-navy-400 rounded-full" />
               <span className="text-[10px] font-black uppercase text-navy-400">Mean Trust Index</span>
            </div>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={[
                { date: 'Mar 1', score: 0.72 }, { date: 'Mar 5', score: 0.75 }, { date: 'Mar 10', score: 0.74 },
                { date: 'Mar 15', score: 0.78 }, { date: 'Mar 20', score: 0.81 }, { date: 'Mar 25', score: 0.83 },
                { date: 'Mar 30', score: stats?.avg_trust_score || 0.85 }
              ]}>
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
          </div>
        </div>

        {/* Bias Exposure Dashboard */}
        <div className="glass-card p-8 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-8">
            <h4 className="text-xs font-black uppercase tracking-widest text-navy-300">Compliance Distribution</h4>
            <Landmark className="text-navy-500" size={20} />
          </div>
          
          <div className="space-y-8">
             <div className="space-y-2">
                <div className="flex justify-between text-xs font-black uppercase text-navy-200">
                  <span>Safe & Compliant</span>
                  <span>78%</span>
                </div>
                <div className="h-3 w-full bg-navy-800 rounded-full overflow-hidden border border-navy-700">
                  <div className="h-full bg-green-500 w-[78%] shadow-[0_0_15px_rgba(34,197,94,0.4)]" />
                </div>
             </div>
             
             <div className="space-y-2">
                <div className="flex justify-between text-xs font-black uppercase text-navy-200">
                  <span>Review Required</span>
                  <span>15%</span>
                </div>
                <div className="h-3 w-full bg-navy-800 rounded-full overflow-hidden border border-navy-700">
                  <div className="h-full bg-yellow-400 w-[15%] shadow-[0_0_15px_rgba(250,204,21,0.4)]" />
                </div>
             </div>

             <div className="space-y-2">
                <div className="flex justify-between text-xs font-black uppercase text-navy-200">
                  <span>Unsafe / High Risk</span>
                  <span>7%</span>
                </div>
                <div className="h-3 w-full bg-navy-800 rounded-full overflow-hidden border border-navy-700">
                  <div className="h-full bg-red-500 w-[7%] shadow-[0_0_15px_rgba(239,68,68,0.4)]" />
                </div>
             </div>
          </div>

          <div className="mt-12 flex space-x-4">
             <button className="flex-1 py-4 bg-navy-800 border border-navy-600 rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-navy-700 transition-colors">
               Board Report (PDF)
             </button>
             <button className="flex-1 py-4 bg-navy-500 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-navy-400 transition-shadow shadow-xl shadow-navy-500/20">
               Stakeholder View
             </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Management;
