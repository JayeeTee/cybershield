import React, { useState } from 'react';

interface EmailConfig {
  enabled: boolean;
  provider: 'smtp' | 'sendgrid' | 'ses';
  smtpHost: string;
  smtpPort: number;
  smtpUser: string;
  smtpPassword: string;
  fromEmail: string;
  fromName: string;
  sendgridApiKey: string;
  sesRegion: string;
  sesAccessKey: string;
  sesSecretKey: string;
  recipients: string[];
  notifyOn: {
    criticalFindings: boolean;
    scanComplete: boolean;
    weeklyDigest: boolean;
    userActions: boolean;
  };
}

const EmailNotifications: React.FC = () => {
  const [config, setConfig] = useState<EmailConfig>({
    enabled: true,
    provider: 'smtp',
    smtpHost: 'smtp.gmail.com',
    smtpPort: 587,
    smtpUser: '',
    smtpPassword: '',
    fromEmail: 'security@company.com',
    fromName: 'CyberShield Security',
    sendgridApiKey: '',
    sesRegion: 'us-east-1',
    sesAccessKey: '',
    sesSecretKey: '',
    recipients: ['admin@company.com', 'security@company.com'],
    notifyOn: {
      criticalFindings: true,
      scanComplete: true,
      weeklyDigest: true,
      userActions: false
    }
  });

  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);
  const [newRecipient, setNewRecipient] = useState('');

  const handleSave = async () => {
    setSaving(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setSaving(false);
    alert('✅ Email settings saved successfully!');
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Simulate test
    const success = Math.random() > 0.3;
    setTestResult(success ? 'success' : 'error');
    setTesting(false);
  };

  const addRecipient = () => {
    if (newRecipient && !config.recipients.includes(newRecipient)) {
      setConfig({ ...config, recipients: [...config.recipients, newRecipient] });
      setNewRecipient('');
    }
  };

  const removeRecipient = (email: string) => {
    setConfig({ ...config, recipients: config.recipients.filter(r => r !== email) });
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Email Notifications</h1>
        <p className="text-gray-600">Configure email alerts and notifications</p>
      </div>

      {/* Enable Toggle */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium">Enable Email Notifications</div>
            <div className="text-sm text-gray-600">Send email alerts for security events</div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={config.enabled}
              onChange={(e) => setConfig({ ...config, enabled: e.target.checked })}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>
      </div>

      {config.enabled && (
        <>
          {/* Provider Selection */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">📧 Email Provider</h2>
            
            <div className="grid grid-cols-3 gap-4 mb-4">
              {[
                { id: 'smtp', label: 'SMTP Server', icon: '📬' },
                { id: 'sendgrid', label: 'SendGrid', icon: '📮' },
                { id: 'ses', label: 'AWS SES', icon: '☁️' }
              ].map((provider) => (
                <button
                  key={provider.id}
                  onClick={() => setConfig({ ...config, provider: provider.id as any })}
                  className={`p-4 border-2 rounded-lg text-center ${
                    config.provider === provider.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="text-3xl mb-2">{provider.icon}</div>
                  <div className="font-medium">{provider.label}</div>
                </button>
              ))}
            </div>

            {/* SMTP Config */}
            {config.provider === 'smtp' && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">SMTP Host</label>
                    <input
                      type="text"
                      value={config.smtpHost}
                      onChange={(e) => setConfig({ ...config, smtpHost: e.target.value })}
                      className="w-full border rounded px-4 py-2"
                      placeholder="smtp.gmail.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Port</label>
                    <input
                      type="number"
                      value={config.smtpPort}
                      onChange={(e) => setConfig({ ...config, smtpPort: parseInt(e.target.value) })}
                      className="w-full border rounded px-4 py-2"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Username</label>
                    <input
                      type="text"
                      value={config.smtpUser}
                      onChange={(e) => setConfig({ ...config, smtpUser: e.target.value })}
                      className="w-full border rounded px-4 py-2"
                      placeholder="your-email@gmail.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Password</label>
                    <input
                      type="password"
                      value={config.smtpPassword}
                      onChange={(e) => setConfig({ ...config, smtpPassword: e.target.value })}
                      className="w-full border rounded px-4 py-2"
                      placeholder="••••••••"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* SendGrid Config */}
            {config.provider === 'sendgrid' && (
              <div>
                <label className="block text-sm font-medium mb-2">SendGrid API Key</label>
                <input
                  type="password"
                  value={config.sendgridApiKey}
                  onChange={(e) => setConfig({ ...config, sendgridApiKey: e.target.value })}
                  className="w-full border rounded px-4 py-2 font-mono"
                  placeholder="SG.xxxxxxxxxxxxx"
                />
              </div>
            )}

            {/* SES Config */}
            {config.provider === 'ses' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">AWS Region</label>
                  <select
                    value={config.sesRegion}
                    onChange={(e) => setConfig({ ...config, sesRegion: e.target.value })}
                    className="w-full border rounded px-4 py-2"
                  >
                    <option value="us-east-1">US East (N. Virginia)</option>
                    <option value="us-west-2">US West (Oregon)</option>
                    <option value="eu-west-1">EU (Ireland)</option>
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Access Key ID</label>
                    <input
                      type="text"
                      value={config.sesAccessKey}
                      onChange={(e) => setConfig({ ...config, sesAccessKey: e.target.value })}
                      className="w-full border rounded px-4 py-2 font-mono"
                      placeholder="AKIAIOSFODNN7EXAMPLE"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Secret Access Key</label>
                    <input
                      type="password"
                      value={config.sesSecretKey}
                      onChange={(e) => setConfig({ ...config, sesSecretKey: e.target.value })}
                      className="w-full border rounded px-4 py-2 font-mono"
                      placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* From Settings */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">✉️ Sender Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">From Email</label>
                <input
                  type="email"
                  value={config.fromEmail}
                  onChange={(e) => setConfig({ ...config, fromEmail: e.target.value })}
                  className="w-full border rounded px-4 py-2"
                  placeholder="security@company.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">From Name</label>
                <input
                  type="text"
                  value={config.fromName}
                  onChange={(e) => setConfig({ ...config, fromName: e.target.value })}
                  className="w-full border rounded px-4 py-2"
                  placeholder="CyberShield Security"
                />
              </div>
            </div>
          </div>

          {/* Recipients */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">👥 Email Recipients</h2>
            
            <div className="flex gap-2 mb-4">
              <input
                type="email"
                value={newRecipient}
                onChange={(e) => setNewRecipient(e.target.value)}
                className="flex-1 border rounded px-4 py-2"
                placeholder="Add email address"
                onKeyPress={(e) => e.key === 'Enter' && addRecipient()}
              />
              <button
                onClick={addRecipient}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Add
              </button>
            </div>

            <div className="space-y-2">
              {config.recipients.map((email) => (
                <div key={email} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <span>{email}</span>
                  <button
                    onClick={() => removeRecipient(email)}
                    className="text-red-600 hover:text-red-800"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Notification Triggers */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">🔔 Notification Triggers</h2>
            <div className="space-y-3">
              {[
                { key: 'criticalFindings', label: 'Critical Findings', desc: 'Send alert when critical vulnerabilities are found' },
                { key: 'scanComplete', label: 'Scan Complete', desc: 'Notify when a scan finishes' },
                { key: 'weeklyDigest', label: 'Weekly Digest', desc: 'Weekly summary of all findings' },
                { key: 'userActions', label: 'User Actions', desc: 'Notify on important user actions' }
              ].map((trigger) => (
                <label key={trigger.key} className="flex items-start gap-3 p-3 border rounded hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.notifyOn[trigger.key as keyof typeof config.notifyOn]}
                    onChange={(e) => setConfig({
                      ...config,
                      notifyOn: { ...config.notifyOn, [trigger.key]: e.target.checked }
                    })}
                    className="mt-1"
                  />
                  <div>
                    <div className="font-medium">{trigger.label}</div>
                    <div className="text-sm text-gray-600">{trigger.desc}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={handleSave}
              disabled={saving}
              className={`px-6 py-3 rounded text-white font-medium ${
                saving ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {saving ? '💾 Saving...' : '💾 Save Settings'}
            </button>

            <button
              onClick={handleTest}
              disabled={testing}
              className="px-6 py-3 border-2 border-blue-600 text-blue-600 rounded font-medium hover:bg-blue-50"
            >
              {testing ? '⏳ Testing...' : '🧪 Send Test Email'}
            </button>

            {testResult === 'success' && (
              <span className="flex items-center text-green-600 font-medium">
                ✅ Test email sent successfully!
              </span>
            )}

            {testResult === 'error' && (
              <span className="flex items-center text-red-600 font-medium">
                ❌ Test failed. Check your settings.
              </span>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default EmailNotifications;
