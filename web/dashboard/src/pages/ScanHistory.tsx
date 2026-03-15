import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

interface Scan {
  id: string;
  scan_type: string;
  status: string;
  started_at: string;
  completed_at?: string;
  findings_count: number;
  high_risk_count: number;
}

const ScanHistory: React.FC = () => {
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'completed' | 'running' | 'failed'>('all');

  useEffect(() => {
    fetchScans();
  }, []);

  const fetchScans = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/scans/history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setScans(response.data.scans || []);
    } catch (error) {
      console.error('Failed to fetch scan history:', error);
      // Mock data for demo
      setScans([
        {
          id: '1',
          scan_type: 'cloud_security',
          status: 'completed',
          started_at: '2026-03-02T10:30:00Z',
          completed_at: '2026-03-02T10:35:00Z',
          findings_count: 12,
          high_risk_count: 3
        },
        {
          id: '2',
          scan_type: 'container_vulnerability',
          status: 'completed',
          started_at: '2026-03-02T09:15:00Z',
          completed_at: '2026-03-02T09:20:00Z',
          findings_count: 8,
          high_risk_count: 1
        },
        {
          id: '3',
          scan_type: 'secrets_detection',
          status: 'failed',
          started_at: '2026-03-01T14:00:00Z',
          findings_count: 0,
          high_risk_count: 0
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const filteredScans = scans.filter(scan => {
    if (filter === 'all') return true;
    return scan.status === filter;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'running': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getScanTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'cloud_security': '☁️ Cloud Security',
      'secrets_detection': '🔐 Secrets Detection',
      'threat_intel': '🕵️ Threat Intel',
      'container_vulnerability': '🐳 Container Scan',
      'network_analysis': '🌐 Network Analysis'
    };
    return labels[type] || type;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const exportToCSV = () => {
    const headers = ['ID', 'Type', 'Status', 'Started', 'Completed', 'Findings', 'High Risk'];
    const rows = filteredScans.map(scan => [
      scan.id,
      scan.scan_type,
      scan.status,
      scan.started_at,
      scan.completed_at || 'N/A',
      scan.findings_count,
      scan.high_risk_count
    ]);
    
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scan-history-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  if (loading) {
    return <div className="text-center py-20">Loading scan history...</div>;
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Scan History</h1>
          <p className="text-gray-600">View and manage past security scans</p>
        </div>
        <button
          onClick={exportToCSV}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          📊 Export CSV
        </button>
      </div>

      <div className="bg-white rounded-lg shadow mb-6">
        <div className="p-4 border-b">
          <div className="flex gap-2">
            {(['all', 'completed', 'running', 'failed'] as const).map((status) => (
              <button
                key={status}
                onClick={() => setFilter(status)}
                className={`px-4 py-2 rounded ${
                  filter === status
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Started</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Duration</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Findings</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">High Risk</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredScans.map((scan) => (
                <tr key={scan.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="font-medium">{getScanTypeLabel(scan.scan_type)}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${getStatusColor(scan.status)}`}>
                      {scan.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatDate(scan.started_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {scan.completed_at
                      ? `${Math.round((new Date(scan.completed_at).getTime() - new Date(scan.started_at).getTime()) / 60000)}m`
                      : '-'
                    }
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {scan.findings_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {scan.high_risk_count > 0 ? (
                      <span className="text-red-600 font-semibold">{scan.high_risk_count}</span>
                    ) : (
                      <span className="text-gray-400">0</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button className="text-blue-600 hover:text-blue-800 mr-3">View</button>
                    <button className="text-red-600 hover:text-red-800">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredScans.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No scans found
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Statistics</h2>
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{scans.length}</div>
            <div className="text-sm text-gray-600">Total Scans</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">
              {scans.filter(s => s.status === 'completed').length}
            </div>
            <div className="text-sm text-gray-600">Completed</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-orange-600">
              {scans.reduce((sum, s) => sum + s.findings_count, 0)}
            </div>
            <div className="text-sm text-gray-600">Total Findings</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-red-600">
              {scans.reduce((sum, s) => sum + s.high_risk_count, 0)}
            </div>
            <div className="text-sm text-gray-600">High Risk</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScanHistory;
