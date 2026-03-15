import React, { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const ThreatIntel: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [iocType, setIocType] = useState<'ip' | 'domain' | 'hash'>('ip');
  const [iocValue, setIocValue] = useState('');
  const [results, setResults] = useState<any>(null);

  const lookupIOC = async () => {
    if (!iocValue) return;
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_URL}/intel/lookup`,
        {
          params: { type: iocType, value: iocValue },
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setResults(response.data);
    } catch (error) {
      console.error('Lookup failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Threat Intelligence</h1>
        <p className="text-gray-600">Query threat intelligence feeds for IOCs</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex gap-4 mb-4">
          <select
            value={iocType}
            onChange={(e) => setIocType(e.target.value as any)}
            className="border rounded px-4 py-2"
          >
            <option value="ip">IP Address</option>
            <option value="domain">Domain</option>
            <option value="hash">File Hash</option>
          </select>
          <input
            type="text"
            placeholder={`Enter ${iocType.toUpperCase()}`}
            value={iocValue}
            onChange={(e) => setIocValue(e.target.value)}
            className="flex-1 border rounded px-4 py-2"
          />
          <button
            onClick={lookupIOC}
            disabled={loading || !iocValue}
            className={`px-6 py-2 rounded text-white ${
              loading || !iocValue ? 'bg-gray-400' : 'bg-purple-600 hover:bg-purple-700'
            }`}
          >
            {loading ? 'Looking up...' : 'Lookup'}
          </button>
        </div>
      </div>

      {results && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Threat Intelligence Results</h2>
          <div className="space-y-4">
            {results.malicious && (
              <div className="bg-red-50 border-l-4 border-red-500 p-4">
                <div className="flex items-center">
                  <span className="text-red-900 font-medium">⚠️ MALICIOUS</span>
                  <span className="ml-auto text-sm text-red-700">
                    Confidence: {results.confidence}%
                  </span>
                </div>
                <p className="text-sm text-red-800 mt-2">{results.description}</p>
              </div>
            )}
            {results.sources && (
              <div>
                <h3 className="font-medium mb-2">Sources:</h3>
                <div className="flex flex-wrap gap-2">
                  {results.sources.map((source: string, idx: number) => (
                    <span key={idx} className="bg-gray-100 px-3 py-1 rounded text-sm">
                      {source}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ThreatIntel;
