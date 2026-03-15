import React, { useState } from 'react';

interface ReportConfig {
  name: string;
  type: 'executive' | 'technical' | 'compliance';
  dateRange: '7d' | '30d' | '90d' | 'custom';
  scanners: string[];
  severity: string[];
  includeRemediation: boolean;
  includeCharts: boolean;
  format: 'pdf' | 'html' | 'csv';
}

const ReportGenerator: React.FC = () => {
  const [config, setConfig] = useState<ReportConfig>({
    name: '',
    type: 'executive',
    dateRange: '30d',
    scanners: ['all'],
    severity: ['all'],
    includeRemediation: true,
    includeCharts: true,
    format: 'pdf'
  });

  const [generating, setGenerating] = useState(false);
  const [recentReports, setRecentReports] = useState([
    {
      id: '1',
      name: 'Q1 Security Summary',
      type: 'executive',
      generated_at: '2026-03-01T10:30:00Z',
      size: '2.4 MB',
      status: 'ready'
    },
    {
      id: '2',
      name: 'Cloud Security Audit',
      type: 'technical',
      generated_at: '2026-02-28T14:20:00Z',
      size: '5.1 MB',
      status: 'ready'
    }
  ]);

  const handleGenerate = async () => {
    if (!config.name) {
      alert('Please enter a report name');
      return;
    }

    setGenerating(true);
    
    // Simulate report generation
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    const newReport = {
      id: Date.now().toString(),
      name: config.name,
      type: config.type,
      generated_at: new Date().toISOString(),
      size: `${(Math.random() * 5 + 1).toFixed(1)} MB`,
      status: 'ready'
    };

    setRecentReports([newReport, ...recentReports]);
    setGenerating(false);
    setConfig({ ...config, name: '' });
  };

  const downloadReport = (reportId: string) => {
    alert(`Downloading report ${reportId}...`);
  };

  const deleteReport = (reportId: string) => {
    if (window.confirm('Delete this report?')) {
      setRecentReports(recentReports.filter(r => r.id !== reportId));
    }
  };

  const getReportTypeColor = (type: string) => {
    switch (type) {
      case 'executive': return 'bg-blue-100 text-blue-800';
      case 'technical': return 'bg-purple-100 text-purple-800';
      case 'compliance': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Report Generator</h1>
        <p className="text-gray-600">Create comprehensive security reports</p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Report Configuration */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">📊 Configure Report</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Report Name *</label>
              <input
                type="text"
                value={config.name}
                onChange={(e) => setConfig({ ...config, name: e.target.value })}
                className="w-full border rounded px-4 py-2"
                placeholder="e.g., Monthly Security Review"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Report Type</label>
              <select
                value={config.type}
                onChange={(e) => setConfig({ ...config, type: e.target.value as any })}
                className="w-full border rounded px-4 py-2"
              >
                <option value="executive">Executive Summary</option>
                <option value="technical">Technical Details</option>
                <option value="compliance">Compliance Report</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Date Range</label>
              <select
                value={config.dateRange}
                onChange={(e) => setConfig({ ...config, dateRange: e.target.value as any })}
                className="w-full border rounded px-4 py-2"
              >
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
                <option value="90d">Last 90 Days</option>
                <option value="custom">Custom Range</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Scanners to Include</label>
              <div className="space-y-2">
                {['All Scanners', 'Cloud Security', 'Secrets Detection', 'Container Scanner', 'Network Analysis'].map((scanner) => (
                  <label key={scanner} className="flex items-center">
                    <input
                      type="checkbox"
                      className="mr-2"
                      defaultChecked={scanner === 'All Scanners'}
                    />
                    <span className="text-sm">{scanner}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Severity Levels</label>
              <div className="space-y-2">
                {['All Severities', 'Critical', 'High', 'Medium', 'Low'].map((severity) => (
                  <label key={severity} className="flex items-center">
                    <input
                      type="checkbox"
                      className="mr-2"
                      defaultChecked={severity === 'All Severities'}
                    />
                    <span className="text-sm">{severity}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Options</label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={config.includeRemediation}
                    onChange={(e) => setConfig({ ...config, includeRemediation: e.target.checked })}
                    className="mr-2"
                  />
                  <span className="text-sm">Include remediation steps</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={config.includeCharts}
                    onChange={(e) => setConfig({ ...config, includeCharts: e.target.checked })}
                    className="mr-2"
                  />
                  <span className="text-sm">Include charts and graphs</span>
                </label>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Export Format</label>
              <select
                value={config.format}
                onChange={(e) => setConfig({ ...config, format: e.target.value as any })}
                className="w-full border rounded px-4 py-2"
              >
                <option value="pdf">PDF Document</option>
                <option value="html">HTML Report</option>
                <option value="csv">CSV Data</option>
              </select>
            </div>

            <button
              onClick={handleGenerate}
              disabled={generating}
              className={`w-full py-3 rounded text-white font-medium ${
                generating ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {generating ? '⏳ Generating Report...' : '📊 Generate Report'}
            </button>
          </div>
        </div>

        {/* Recent Reports */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">📁 Recent Reports</h2>
          
          <div className="space-y-3">
            {recentReports.map((report) => (
              <div key={report.id} className="border rounded-lg p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="font-medium">{report.name}</div>
                    <div className="text-sm text-gray-600">{formatDate(report.generated_at)}</div>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${getReportTypeColor(report.type)}`}>
                    {report.type}
                  </span>
                </div>
                
                <div className="flex items-center justify-between mt-3">
                  <div className="text-sm text-gray-500">
                    Size: {report.size}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => downloadReport(report.id)}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      ⬇️ Download
                    </button>
                    <button
                      onClick={() => deleteReport(report.id)}
                      className="text-sm text-red-600 hover:text-red-800"
                    >
                      🗑️ Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {recentReports.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No reports generated yet
            </div>
          )}
        </div>
      </div>

      {/* Report Preview */}
      <div className="bg-white rounded-lg shadow p-6 mt-6">
        <h2 className="text-lg font-semibold mb-4">👁️ Report Preview</h2>
        
        <div className="border rounded p-8 bg-gray-50">
          <div className="text-center mb-8">
            <div className="text-4xl mb-2">🛡️</div>
            <h3 className="text-2xl font-bold">CyberShield Security Report</h3>
            <div className="text-gray-600 mt-2">
              {config.type === 'executive' && 'Executive Summary'}
              {config.type === 'technical' && 'Technical Details'}
              {config.type === 'compliance' && 'Compliance Report'}
            </div>
          </div>

          <div className="space-y-4">
            <div className="bg-white rounded p-4">
              <div className="font-semibold mb-2">📊 Overview</div>
              <div className="text-sm text-gray-600">
                This report covers security findings from the last {
                  config.dateRange === '7d' ? '7 days' :
                  config.dateRange === '30d' ? '30 days' : '90 days'
                }.
              </div>
            </div>

            <div className="bg-white rounded p-4">
              <div className="font-semibold mb-2">🔍 Key Findings</div>
              <ul className="text-sm text-gray-600 list-disc list-inside space-y-1">
                <li>45 security findings identified</li>
                <li>12 critical vulnerabilities</li>
                <li>8 high-priority issues</li>
                <li>25 medium/low findings</li>
              </ul>
            </div>

            {config.includeRemediation && (
              <div className="bg-white rounded p-4">
                <div className="font-semibold mb-2">🔧 Remediation Status</div>
                <div className="text-sm text-gray-600">
                  67% of findings remediated (30 of 45)
                </div>
              </div>
            )}

            {config.includeCharts && (
              <div className="bg-white rounded p-4">
                <div className="font-semibold mb-2">📈 Severity Distribution</div>
                <div className="flex gap-4 items-end h-32">
                  <div className="flex-1 flex flex-col items-center">
                    <div className="w-full bg-red-500 rounded-t" style={{ height: '80%' }}></div>
                    <div className="text-xs mt-1">Critical</div>
                  </div>
                  <div className="flex-1 flex flex-col items-center">
                    <div className="w-full bg-orange-500 rounded-t" style={{ height: '60%' }}></div>
                    <div className="text-xs mt-1">High</div>
                  </div>
                  <div className="flex-1 flex flex-col items-center">
                    <div className="w-full bg-yellow-500 rounded-t" style={{ height: '40%' }}></div>
                    <div className="text-xs mt-1">Medium</div>
                  </div>
                  <div className="flex-1 flex flex-col items-center">
                    <div className="w-full bg-blue-500 rounded-t" style={{ height: '20%' }}></div>
                    <div className="text-xs mt-1">Low</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportGenerator;
