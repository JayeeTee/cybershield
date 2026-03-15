import React, { useState } from 'react';

interface Settings {
  notifications: {
    email: boolean;
    slack: boolean;
    criticalOnly: boolean;
  };
  thresholds: {
    autoDeleteFindings: number;
    scanRetention: number;
    maxConcurrentScans: number;
  };
  apiKeys: {
    aws?: string;
    azure?: string;
    gcp?: string;
    virustotal?: string;
  };
}

const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<Settings>({
    notifications: {
      email: true,
      slack: false,
      criticalOnly: false
    },
    thresholds: {
      autoDeleteFindings: 90,
      scanRetention: 365,
      maxConcurrentScans: 5
    },
    apiKeys: {
      aws: '',
      azure: '',
      gcp: '',
      virustotal: ''
    }
  });

  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const updateNotification = (key: keyof Settings['notifications'], value: boolean) => {
    setSettings({
      ...settings,
      notifications: { ...settings.notifications, [key]: value }
    });
  };

  const updateThreshold = (key: keyof Settings['thresholds'], value: number) => {
    setSettings({
      ...settings,
      thresholds: { ...settings.thresholds, [key]: value }
    });
  };

  const updateApiKey = (key: keyof Settings['apiKeys'], value: string) => {
    setSettings({
      ...settings,
      apiKeys: { ...settings.apiKeys, [key]: value }
    });
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Configure your CyberShield preferences</p>
      </div>

      {/* Notifications */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">📧 Notifications</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Email Notifications</div>
              <div className="text-sm text-gray-600">Receive email alerts for critical findings</div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.notifications.email}
                onChange={(e) => updateNotification('email', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Slack Integration</div>
              <div className="text-sm text-gray-600">Post findings to Slack channel</div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.notifications.slack}
                onChange={(e) => updateNotification('slack', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Critical Findings Only</div>
              <div className="text-sm text-gray-600">Only notify for critical severity items</div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.notifications.criticalOnly}
                onChange={(e) => updateNotification('criticalOnly', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </div>
      </div>

      {/* Thresholds */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">⚙️ Thresholds & Limits</h2>
        <div className="space-y-4">
          <div>
            <label className="block font-medium mb-2">
              Auto-Delete Old Findings (days)
            </label>
            <input
              type="number"
              value={settings.thresholds.autoDeleteFindings}
              onChange={(e) => updateThreshold('autoDeleteFindings', parseInt(e.target.value))}
              className="w-full border rounded px-4 py-2"
            />
            <p className="text-sm text-gray-600 mt-1">
              Findings older than this will be automatically deleted
            </p>
          </div>

          <div>
            <label className="block font-medium mb-2">
              Scan Retention Period (days)
            </label>
            <input
              type="number"
              value={settings.thresholds.scanRetention}
              onChange={(e) => updateThreshold('scanRetention', parseInt(e.target.value))}
              className="w-full border rounded px-4 py-2"
            />
            <p className="text-sm text-gray-600 mt-1">
              How long to keep scan history
            </p>
          </div>

          <div>
            <label className="block font-medium mb-2">
              Max Concurrent Scans
            </label>
            <input
              type="number"
              value={settings.thresholds.maxConcurrentScans}
              onChange={(e) => updateThreshold('maxConcurrentScans', parseInt(e.target.value))}
              className="w-full border rounded px-4 py-2"
            />
            <p className="text-sm text-gray-600 mt-1">
              Maximum number of scans running at once
            </p>
          </div>
        </div>
      </div>

      {/* API Keys */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">🔑 API Keys</h2>
        <div className="space-y-4">
          <div>
            <label className="block font-medium mb-2">AWS Access Key</label>
            <input
              type="password"
              placeholder="AKIA..."
              value={settings.apiKeys.aws}
              onChange={(e) => updateApiKey('aws', e.target.value)}
              className="w-full border rounded px-4 py-2 font-mono"
            />
          </div>

          <div>
            <label className="block font-medium mb-2">Azure Client Secret</label>
            <input
              type="password"
              placeholder="Enter Azure secret..."
              value={settings.apiKeys.azure}
              onChange={(e) => updateApiKey('azure', e.target.value)}
              className="w-full border rounded px-4 py-2 font-mono"
            />
          </div>

          <div>
            <label className="block font-medium mb-2">GCP Service Account Key</label>
            <input
              type="password"
              placeholder="Enter GCP key..."
              value={settings.apiKeys.gcp}
              onChange={(e) => updateApiKey('gcp', e.target.value)}
              className="w-full border rounded px-4 py-2 font-mono"
            />
          </div>

          <div>
            <label className="block font-medium mb-2">VirusTotal API Key</label>
            <input
              type="password"
              placeholder="Enter VT key..."
              value={settings.apiKeys.virustotal}
              onChange={(e) => updateApiKey('virustotal', e.target.value)}
              className="w-full border rounded px-4 py-2 font-mono"
            />
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex items-center gap-4">
        <button
          onClick={handleSave}
          disabled={saving}
          className={`px-6 py-3 rounded text-white font-medium ${
            saving ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {saving ? 'Saving...' : '💾 Save Settings'}
        </button>

        {saved && (
          <span className="text-green-600 font-medium">✓ Settings saved successfully!</span>
        )}
      </div>
    </div>
  );
};

export default SettingsPage;
