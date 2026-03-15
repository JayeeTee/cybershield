import React, { useState, useEffect } from 'react';
import SummaryCards from '../components/Dashboard/SummaryCards';
import SeverityChart from '../components/Dashboard/SeverityChart';
import RecentFindings from '../components/Dashboard/RecentFindings';
import { DashboardSummary } from '../types';
import dashboardService from '../services/dashboard';

const Dashboard: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSummary();
  }, []);

  const fetchSummary = async () => {
    try {
      const data = await dashboardService.getSummary();
      setSummary(data);
    } catch (error) {
      console.error('Failed to fetch summary:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-800">Security Dashboard</h2>
        <p className="text-gray-600 mt-2">Overview of your security posture</p>
      </div>

      <SummaryCards summary={summary} loading={loading} />

      <div className="grid grid-cols-2 gap-6 mb-8">
        <SeverityChart />
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded transition">
              ☁️ Run Cloud Scan
            </button>
            <button className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded transition">
              🔐 Scan for Secrets
            </button>
            <button className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded transition">
              🐳 Scan Containers
            </button>
            <button className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded transition">
              🌐 Analyze Network
            </button>
          </div>
        </div>
      </div>

      <RecentFindings />
    </div>
  );
};

export default Dashboard;
