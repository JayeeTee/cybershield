import React, { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const NetworkAnalyzer: React.FC = () => {
  const [analyzing, setAnalyzing] = useState(false);
  const [target, setTarget] = useState('');
  const [duration, setDuration] = useState(60);
  const [results, setResults] = useState<any>(null);

  const startAnalysis = async () => {
    if (!target) return;
    setAnalyzing(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/scanners/network`,
        { target, duration },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setResults(response.data);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Network Traffic Analyzer</h1>
        <p className="text-gray-600">Capture and analyze network traffic for anomalies</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-3 gap-4 mb-4">
          <input
            type="text"
            placeholder="Target interface or IP"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            className="border rounded px-4 py-2"
          />
          <input
            type="number"
            placeholder="Duration (seconds)"
            value={duration}
            onChange={(e) => setDuration(parseInt(e.target.value))}
            className="border rounded px-4 py-2"
          />
          <button
            onClick={startAnalysis}
            disabled={analyzing || !target}
            className={`px-6 py-2 rounded text-white ${
              analyzing || !target ? 'bg-gray-400' : 'bg-indigo-600 hover:bg-indigo-700'
            }`}
          >
            {analyzing ? 'Analyzing...' : 'Start Capture'}
          </button>
        </div>
      </div>

      {results && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Traffic Summary</h2>
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">{results.total_packets || 0}</div>
                <div className="text-sm text-gray-600">Total Packets</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">{results.unique_ips || 0}</div>
                <div className="text-sm text-gray-600">Unique IPs</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-orange-600">{results.anomalies || 0}</div>
                <div className="text-sm text-gray-600">Anomalies</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600">{results.protocols?.length || 0}</div>
                <div className="text-sm text-gray-600">Protocols</div>
              </div>
            </div>
          </div>

          {results.anomalies > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Detected Anomalies</h2>
              <div className="space-y-3">
                {results.anomaly_details?.map((anomaly: any, idx: number) => (
                  <div key={idx} className="bg-yellow-50 border-l-4 border-yellow-500 p-4">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-yellow-900">{anomaly.type}</span>
                      <span className="text-sm text-yellow-700">{anomaly.timestamp}</span>
                    </div>
                    <p className="text-sm text-yellow-800 mt-2">{anomaly.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NetworkAnalyzer;
