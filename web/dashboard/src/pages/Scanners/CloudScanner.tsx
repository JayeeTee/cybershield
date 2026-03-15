import React, { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const CloudScanner: React.FC = () => {
  const [scanning, setScanning] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [provider, setProvider] = useState<'aws' | 'azure' | 'gcp'>('aws');

  const startScan = async () => {
    setScanning(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/scanners/cloud`,
        { provider },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setResults(response.data.findings || []);
    } catch (error) {
      console.error('Scan failed:', error);
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Cloud Security Scanner</h1>
        <p className="text-gray-600">Scan AWS, Azure, and GCP for misconfigurations</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center gap-4 mb-4">
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value as any)}
            className="border rounded px-4 py-2"
          >
            <option value="aws">AWS</option>
            <option value="azure">Azure</option>
            <option value="gcp">GCP</option>
          </select>
          <button
            onClick={startScan}
            disabled={scanning}
            className={`px-6 py-2 rounded text-white ${
              scanning ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {scanning ? 'Scanning...' : 'Start Scan'}
          </button>
        </div>
      </div>

      {results.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Findings ({results.length})</h2>
          <div className="space-y-3">
            {results.map((finding, idx) => (
              <div key={idx} className="border rounded p-4">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{finding.title}</span>
                  <span className={`px-2 py-1 rounded text-sm ${
                    finding.severity === 'critical' ? 'bg-red-100 text-red-800' :
                    finding.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                    finding.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {finding.severity}
                  </span>
                </div>
                <p className="text-gray-600 mt-2 text-sm">{finding.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CloudScanner;
