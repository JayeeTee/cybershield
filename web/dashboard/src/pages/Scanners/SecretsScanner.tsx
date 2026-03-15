import React, { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const SecretsScanner: React.FC = () => {
  const [scanning, setScanning] = useState(false);
  const [repository, setRepository] = useState('');
  const [results, setResults] = useState<any[]>([]);

  const startScan = async () => {
    if (!repository) return;
    setScanning(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/scanners/secrets`,
        { repository },
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
        <h1 className="text-2xl font-bold text-gray-900">Secrets Detection</h1>
        <p className="text-gray-600">Scan repositories for exposed secrets and credentials</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex gap-4 mb-4">
          <input
            type="text"
            placeholder="Repository URL or path"
            value={repository}
            onChange={(e) => setRepository(e.target.value)}
            className="flex-1 border rounded px-4 py-2"
          />
          <button
            onClick={startScan}
            disabled={scanning || !repository}
            className={`px-6 py-2 rounded text-white ${
              scanning || !repository ? 'bg-gray-400' : 'bg-red-600 hover:bg-red-700'
            }`}
          >
            {scanning ? 'Scanning...' : 'Scan for Secrets'}
          </button>
        </div>
      </div>

      {results.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Exposed Secrets ({results.length})</h2>
          <div className="space-y-3">
            {results.map((finding, idx) => (
              <div key={idx} className="border-l-4 border-red-500 bg-red-50 p-4">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-red-900">{finding.type}</span>
                  <span className="text-sm text-red-700">{finding.file}:{finding.line}</span>
                </div>
                <p className="text-sm text-red-800 mt-2">{finding.description}</p>
                <p className="text-xs text-red-600 mt-1">Confidence: {finding.confidence}%</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SecretsScanner;
