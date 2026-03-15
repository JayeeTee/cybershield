import React, { useState, useEffect } from 'react';

interface AuditLog {
  id: string;
  timestamp: Date;
  user: string;
  action: 'login' | 'scan_started' | 'scan_completed' | 'user_created' | 'user_deleted' | 'setting_changed' | 'finding_viewed' | 'report_exported';
  resource: string;
  details: string;
  ip_address: string;
  user_agent: string;
}

const generateAuditLogs = (): AuditLog[] => {
  const actions: AuditLog['action'][] = ['login', 'scan_started', 'scan_completed', 'user_created', 'user_deleted', 'setting_changed', 'finding_viewed', 'report_exported'];
  
  return Array.from({ length: 50 }, (_, i) => ({
    id: `log-${i + 1}`,
    timestamp: new Date(Date.now() - Math.random() * 7 * 86400000),
    user: ['admin', 'scanner_service', 'viewer_user'][Math.floor(Math.random() * 3)],
    action: actions[Math.floor(Math.random() * actions.length)],
    resource: ['Cloud Scanner', 'Container Scanner', 'User Management', 'Settings', 'Dashboard'][Math.floor(Math.random() * 5)],
    details: 'Action performed successfully',
    ip_address: `192.168.1.${Math.floor(Math.random() * 255)}`,
    user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  })).sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
};

const AuditLogPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<AuditLog[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [actionFilter, setActionFilter] = useState<string>('all');
  const [dateRange, setDateRange] = useState<'24h' | '7d' | '30d' | 'all'>('7d');

  useEffect(() => {
    const auditLogs = generateAuditLogs();
    setLogs(auditLogs);
    setFilteredLogs(auditLogs);
  }, []);

  useEffect(() => {
    let filtered = logs;

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(log =>
        log.user.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.resource.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.details.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Action filter
    if (actionFilter !== 'all') {
      filtered = filtered.filter(log => log.action === actionFilter);
    }

    // Date range filter
    const now = Date.now();
    if (dateRange === '24h') {
      filtered = filtered.filter(log => now - log.timestamp.getTime() < 86400000);
    } else if (dateRange === '7d') {
      filtered = filtered.filter(log => now - log.timestamp.getTime() < 7 * 86400000);
    } else if (dateRange === '30d') {
      filtered = filtered.filter(log => now - log.timestamp.getTime() < 30 * 86400000);
    }

    setFilteredLogs(filtered);
  }, [logs, searchTerm, actionFilter, dateRange]);

  const getActionIcon = (action: AuditLog['action']) => {
    switch (action) {
      case 'login': return '🔐';
      case 'scan_started': return '▶️';
      case 'scan_completed': return '✅';
      case 'user_created': return '➕';
      case 'user_deleted': return '🗑️';
      case 'setting_changed': return '⚙️';
      case 'finding_viewed': return '👁️';
      case 'report_exported': return '📊';
    }
  };

  const getActionColor = (action: AuditLog['action']) => {
    switch (action) {
      case 'login': return 'bg-blue-100 text-blue-800';
      case 'scan_started': return 'bg-yellow-100 text-yellow-800';
      case 'scan_completed': return 'bg-green-100 text-green-800';
      case 'user_created': return 'bg-purple-100 text-purple-800';
      case 'user_deleted': return 'bg-red-100 text-red-800';
      case 'setting_changed': return 'bg-orange-100 text-orange-800';
      case 'finding_viewed': return 'bg-indigo-100 text-indigo-800';
      case 'report_exported': return 'bg-teal-100 text-teal-800';
    }
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const exportLogs = () => {
    const csv = [
      ['Timestamp', 'User', 'Action', 'Resource', 'Details', 'IP Address'].join(','),
      ...filteredLogs.map(log => [
        log.timestamp.toISOString(),
        log.user,
        log.action,
        log.resource,
        log.details,
        log.ip_address
      ].join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const stats = {
    total: filteredLogs.length,
    logins: filteredLogs.filter(l => l.action === 'login').length,
    scans: filteredLogs.filter(l => l.action.startsWith('scan')).length,
    adminActions: filteredLogs.filter(l => ['user_created', 'user_deleted', 'setting_changed'].includes(l.action)).length
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Audit Logs</h1>
          <p className="text-gray-600">Track all user activity and system events</p>
        </div>
        <button
          onClick={exportLogs}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          📊 Export Logs
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Total Events</div>
          <div className="text-3xl font-bold text-gray-900">{stats.total}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Logins</div>
          <div className="text-3xl font-bold text-blue-600">{stats.logins}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Scans</div>
          <div className="text-3xl font-bold text-green-600">{stats.scans}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600">Admin Actions</div>
          <div className="text-3xl font-bold text-purple-600">{stats.adminActions}</div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-3 gap-4">
          <input
            type="text"
            placeholder="Search logs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="border rounded px-4 py-2"
          />
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="border rounded px-4 py-2"
          >
            <option value="all">All Actions</option>
            <option value="login">Login</option>
            <option value="scan_started">Scan Started</option>
            <option value="scan_completed">Scan Completed</option>
            <option value="user_created">User Created</option>
            <option value="user_deleted">User Deleted</option>
            <option value="setting_changed">Setting Changed</option>
            <option value="finding_viewed">Finding Viewed</option>
            <option value="report_exported">Report Exported</option>
          </select>
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value as any)}
            className="border rounded px-4 py-2"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="all">All Time</option>
          </select>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Resource</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP Address</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {filteredLogs.map((log) => (
              <tr key={log.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                  {formatTimestamp(log.timestamp)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="font-medium">{log.user}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold ${getActionColor(log.action)}`}>
                    {getActionIcon(log.action)} {log.action.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                  {log.resource}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                  {log.ip_address}
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {log.details}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredLogs.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No audit logs found
          </div>
        )}
      </div>
    </div>
  );
};

export default AuditLogPage;
