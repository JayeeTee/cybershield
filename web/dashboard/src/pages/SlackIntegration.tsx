import React, { useState } from 'react';

const SlackIntegration: React.FC = () => {
  const [enabled, setEnabled] = useState(false);
  const [webhookUrl, setWebhookUrl] = useState('');
  const [channel, setChannel] = useState('#security-alerts');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);
  const [notifyOn, setNotifyOn] = useState({
    criticalFindings: true,
    scanComplete: true,
    userActions: false,
    weeklyDigest: true
  });

  const testWebhook = async () => {
    if (!webhookUrl) return;
    
    setTesting(true);
    setTestResult(null);
    
    // Simulate webhook test
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const success = webhookUrl.includes('hooks.slack.com');
    setTestResult(success ? 'success' : 'error');
    setTesting(false);
  };

  const saveSettings = () => {
    if (!webhookUrl) return;
    
    setEnabled(true);
    alert('✅ Slack integration configured successfully!');
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Slack Integration</h1>
        <p className="text-gray-600">Send security alerts to Slack channels</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="text-5xl">💬</div>
            <div>
              <div className="font-semibold text-lg">Slack Webhook</div>
              <div className="text-sm text-gray-600">Connect your Slack workspace</div>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Webhook URL</label>
            <input
              type="password"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              className="w-full border rounded px-4 py-2 font-mono text-sm"
              placeholder="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"
            />
            <p className="text-xs text-gray-500 mt-1">
              Create a webhook in Slack: Apps → Incoming Webhooks → Add to Slack
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Default Channel</label>
            <input
              type="text"
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
              className="w-full border rounded px-4 py-2"
              placeholder="#security-alerts"
            />
          </div>

          <div className="flex gap-3">
            <button
              onClick={testWebhook}
              disabled={!webhookUrl || testing}
              className={`px-4 py-2 border-2 rounded font-medium ${
                !webhookUrl || testing
                  ? 'border-gray-300 text-gray-400 cursor-not-allowed'
                  : 'border-blue-600 text-blue-600 hover:bg-blue-50'
              }`}
            >
              {testing ? '⏳ Testing...' : '🧪 Test Connection'}
            </button>

            <button
              onClick={saveSettings}
              disabled={!webhookUrl}
              className={`px-4 py-2 rounded font-medium text-white ${
                !webhookUrl
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              Save Settings
            </button>

            {testResult === 'success' && (
              <span className="flex items-center text-green-600 font-medium">
                ✅ Connection successful!
              </span>
            )}

            {testResult === 'error' && (
              <span className="flex items-center text-red-600 font-medium">
                ❌ Connection failed
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Notification Settings */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">🔔 Notification Events</h2>
        <p className="text-sm text-gray-600 mb-4">
          Choose which events should trigger Slack notifications
        </p>

        <div className="space-y-3">
          {[
            { key: 'criticalFindings', label: 'Critical Findings', desc: 'Post when critical vulnerabilities are found', icon: '🚨' },
            { key: 'scanComplete', label: 'Scan Complete', desc: 'Post when a security scan finishes', icon: '✅' },
            { key: 'userActions', label: 'User Actions', desc: 'Post when users perform important actions', icon: '👤' },
            { key: 'weeklyDigest', label: 'Weekly Digest', desc: 'Post a weekly summary every Monday', icon: '📊' }
          ].map((event) => (
            <label key={event.key} className="flex items-start gap-3 p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <input
                type="checkbox"
                checked={notifyOn[event.key as keyof typeof notifyOn]}
                onChange={(e) => setNotifyOn({ ...notifyOn, [event.key]: e.target.checked })}
                className="mt-1"
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span>{event.icon}</span>
                  <span className="font-medium">{event.label}</span>
                </div>
                <div className="text-sm text-gray-600 mt-1">{event.desc}</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Preview */}
      <div className="bg-white rounded-lg shadow p-6 mt-6">
        <h2 className="text-lg font-semibold mb-4">👁️ Message Preview</h2>
        <div className="bg-gray-100 rounded p-4 font-mono text-sm">
          <div className="font-bold mb-2">🛡️ CyberShield Security Alert</div>
          <div className="text-gray-600">━━━━━━━━━━━━━━━━━━━━━━</div>
          <div className="mt-2">
            <div className="font-semibold">🚨 Critical Finding Detected</div>
            <div className="mt-2">• <strong>Type:</strong> Cloud Security</div>
            <div>• <strong>Severity:</strong> Critical</div>
            <div>• <strong>Resource:</strong> S3 Bucket (prod-data)</div>
            <div>• <strong>Issue:</strong> Public read access enabled</div>
          </div>
          <div className="mt-2 text-gray-600">━━━━━━━━━━━━━━━━━━━━━━</div>
          <div className="mt-2 text-blue-600">→ View in Dashboard</div>
        </div>
      </div>
    </div>
  );
};

export default SlackIntegration;
