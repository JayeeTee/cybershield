import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

interface TrendData {
  date: string;
  findings: number;
  critical: number;
  high: number;
}

const EnhancedDashboard: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('7d');
  const [trendData, setTrendData] = useState<TrendData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTrendData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeRange]);

  const fetchTrendData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/dashboard/trends`, {
        params: { range: timeRange },
        headers: { Authorization: `Bearer ${token}` }
      });
      setTrendData(response.data.trends || []);
    } catch (error) {
      // Mock data for demo
      const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90;
      const mockData = Array.from({ length: days }, (_, i) => ({
        date: new Date(Date.now() - (days - i - 1) * 86400000).toISOString().split('T')[0],
        findings: Math.floor(Math.random() * 20) + 5,
        critical: Math.floor(Math.random() * 3),
        high: Math.floor(Math.random() * 5) + 1
      }));
      setTrendData(mockData);
    } finally {
      setLoading(false);
    }
  };

  const summaryData = [
    { name: 'Cloud', value: 45, color: '#3B82F6' },
    { name: 'Container', value: 32, color: '#10B981' },
    { name: 'Secrets', value: 18, color: '#EF4444' },
    { name: 'Network', value: 12, color: '#8B5CF6' },
  ];

  const comparisonData = [
    { period: 'Last Week', critical: 8, high: 15, medium: 23 },
    { period: 'This Week', critical: 5, high: 12, medium: 18 },
  ];

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Enhanced Dashboard</h1>
          <p className="text-gray-600">Security trends and analytics</p>
        </div>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value as any)}
          className="border rounded px-4 py-2"
        >
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
          <option value="90d">Last 90 Days</option>
        </select>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-5 gap-4 mb-6">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow p-6 text-white">
          <div className="text-sm opacity-80">Total Findings</div>
          <div className="text-4xl font-bold mt-2">
            {trendData.reduce((sum, d) => sum + d.findings, 0)}
          </div>
        </div>
        <div className="bg-gradient-to-br from-red-500 to-red-600 rounded-lg shadow p-6 text-white">
          <div className="text-sm opacity-80">Critical</div>
          <div className="text-4xl font-bold mt-2">
            {trendData.reduce((sum, d) => sum + d.critical, 0)}
          </div>
        </div>
        <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg shadow p-6 text-white">
          <div className="text-sm opacity-80">High Risk</div>
          <div className="text-4xl font-bold mt-2">
            {trendData.reduce((sum, d) => sum + d.high, 0)}
          </div>
        </div>
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow p-6 text-white">
          <div className="text-sm opacity-80">Remediated</div>
          <div className="text-4xl font-bold mt-2">67</div>
        </div>
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow p-6 text-white">
          <div className="text-sm opacity-80">Scans Run</div>
          <div className="text-4xl font-bold mt-2">{trendData.length * 2}</div>
        </div>
      </div>

      {/* Trend Chart */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">📈 Findings Trend</h2>
        {loading ? (
          <div className="text-center py-12 text-gray-500">Loading chart...</div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="findings" stroke="#3B82F6" strokeWidth={2} name="Total Findings" />
              <Line type="monotone" dataKey="critical" stroke="#EF4444" strokeWidth={2} name="Critical" />
              <Line type="monotone" dataKey="high" stroke="#F97316" strokeWidth={2} name="High" />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-2 gap-6">
        {/* Findings by Type */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">🔍 Findings by Scanner Type</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={summaryData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Week-over-Week Comparison */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">📊 Week-over-Week Comparison</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={comparisonData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="critical" fill="#EF4444" name="Critical" />
              <Bar dataKey="high" fill="#F97316" name="High" />
              <Bar dataKey="medium" fill="#FBBF24" name="Medium" />
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-4 p-4 bg-green-50 rounded border-l-4 border-green-500">
            <div className="font-medium text-green-900">
              ✅ 37% reduction in findings this week!
            </div>
            <div className="text-sm text-green-700 mt-1">
              Keep up the great work on remediation
            </div>
          </div>
        </div>
      </div>

      {/* Top Vulnerabilities */}
      <div className="bg-white rounded-lg shadow p-6 mt-6">
        <h2 className="text-lg font-semibold mb-4">🎯 Top Recurring Vulnerabilities</h2>
        <div className="space-y-3">
          {[
            { name: 'S3 Bucket Public Access', count: 12, severity: 'critical', trend: 'up' },
            { name: 'Outdated TLS Version', count: 9, severity: 'high', trend: 'down' },
            { name: 'Missing Security Headers', count: 7, severity: 'medium', trend: 'stable' },
            { name: 'Unencrypted EBS Volumes', count: 5, severity: 'high', trend: 'down' },
          ].map((vuln, idx) => (
            <div key={idx} className="flex items-center justify-between p-3 border rounded hover:bg-gray-50">
              <div className="flex items-center gap-3">
                <span className={`px-2 py-1 rounded text-xs font-semibold ${
                  vuln.severity === 'critical' ? 'bg-red-100 text-red-800' :
                  vuln.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {vuln.severity.toUpperCase()}
                </span>
                <span className="font-medium">{vuln.name}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-gray-600">{vuln.count} instances</span>
                <span className="text-sm">
                  {vuln.trend === 'up' && '📈'}
                  {vuln.trend === 'down' && '📉'}
                  {vuln.trend === 'stable' && '➡️'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default EnhancedDashboard;
