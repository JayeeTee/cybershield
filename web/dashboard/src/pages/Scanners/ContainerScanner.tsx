import React, { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const ContainerScanner: React.FC = () => {
  const [scanning, setScanning] = useState(false);
  const [imageName, setImageName] = useState('');
  const [results, setResults] = useState<any[]>([]);

  const startScan = async () => {
    if (!imageName) return;
    setScanning(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/scanners/container`,
        { image: imageName },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setResults(response.data.vulnerabilities || []);
    } catch (error) {
      console.error('Scan failed:', error);
    } finally {
      setScanning(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-500';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-500';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-500';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-500';
      default: return 'bg-gray-100 text-gray-800 border-gray-500';
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Container Vulnerability Scanner</h1>
        <p className="text-gray-600">Scan Docker images for known vulnerabilities</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex gap-4 mb-4">
          <input
            type="text"
            placeholder="Image name (e.g., nginx:latest)"
            value={imageName}
            onChange={(e) => setImageName(e.target.value)}
            className="flex-1 border rounded px-4 py-2"
          />
          <button
            onClick={startScan}
            disabled={scanning || !imageName}
            className={`px-6 py-2 rounded text-white ${
              scanning || !imageName ? 'bg-gray-400' : 'bg-green-600 hover:bg-green-700'
            }`}
          >
            {scanning ? 'Scanning...' : 'Scan Image'}
          </button>
        </div>
      </div>

      {results.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">
            Vulnerabilities Found ({results.length})
          </h2>
          <div className="space-y-3">
            {results.map((vuln, idx) => (
              <div key={idx} className={`border-l-4 rounded p-4 ${getSeverityColor(vuln.severity)}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">{vuln.cve_id}</span>
                  <span className="text-sm font-semibold uppercase">{vuln.severity}</span>
                </div>
                <p className="text-sm mb-2">{vuln.description}</p>
                <div className="flex gap-4 text-xs">
                  <span>Package: {vuln.package}</span>
                  <span>Installed: {vuln.installed_version}</span>
                  {vuln.fixed_version && (
                    <span className="text-green-700">Fixed in: {vuln.fixed_version}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ContainerScanner;
