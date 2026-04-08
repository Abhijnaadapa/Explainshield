import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Shield, Cpu, Scale, BarChart3, Menu, X, Landmark } from 'lucide-react';
import TechTeam from './pages/TechTeam';
import Compliance from './pages/Compliance';
import Management from './pages/Management';
import { setAuthToken } from './services/api';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();

  const navigation = [
    { name: 'Tech Team', href: '/', icon: Cpu },
    { name: 'Compliance', href: '/compliance', icon: Scale },
    { name: 'Management', href: '/management', icon: BarChart3 },
  ];

  return (
    <div className="min-h-screen bg-navy-900 text-white font-sans selection:bg-navy-400">
      {/* Sidebar / Header */}
      <nav className="fixed top-0 z-50 w-full bg-navy-800/80 backdrop-blur-md border-b border-navy-700">
        <div className="px-3 py-3 lg:px-5 lg:pl-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center justify-start rtl:justify-end">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="inline-flex items-center p-2 text-sm text-navy-400 rounded-lg sm:hidden hover:bg-navy-700 focus:outline-none"
              >
                {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
              </button>
              <Link to="/" className="flex ms-2 md:me-24 items-center">
                <div className="bg-navy-500 p-1.5 rounded-lg mr-3 shadow-lg shadow-navy-500/20">
                  <Shield className="w-8 h-8 text-white" />
                </div>
                <span className="self-center text-xl font-bold sm:text-2xl whitespace-nowrap tracking-tight">
                  Explain<span className="text-navy-400">Shield</span>
                </span>
              </Link>
            </div>
            
            <div className="hidden sm:flex items-center space-x-8">
              {navigation.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center space-x-2 text-sm font-medium transition-all duration-200 hover:text-white ${
                      isActive ? 'text-white' : 'text-navy-400'
                    }`}
                  >
                    <Icon size={18} className={isActive ? 'text-navy-400' : ''} />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>

            <div className="flex items-center">
              <div className="flex items-center ms-3">
                <div className="flex items-center space-x-3 px-3 py-1.5 bg-navy-700/50 rounded-full border border-navy-600">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  <span className="text-xs font-medium text-navy-200">System Live</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="fixed inset-0 z-40 bg-navy-900/90 sm:hidden">
          <div className="flex flex-col h-full pt-20 px-6 space-y-4">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                onClick={() => setIsMenuOpen(false)}
                className="flex items-center py-4 text-lg font-semibold border-b border-navy-800"
              >
                <item.icon className="mr-4 text-navy-400" />
                {item.name}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="pt-20 pb-10 container mx-auto px-4 lg:px-8">
        {children}
      </main>
    </div>
  );
};

const App: React.FC = () => {
  useEffect(() => {
    const fetchToken = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/token');
        const data = await response.json();
        setAuthToken(data.token);
      } catch (err) {
        console.error('Failed to fetch token:', err);
      }
    };
    fetchToken();
  }, []);

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<TechTeam />} />
          <Route path="/compliance" element={<Compliance />} />
          <Route path="/management" element={<Management />} />
        </Routes>
      </Layout>
    </Router>
  );
};

export default App;
