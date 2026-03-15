import React, { useState } from 'react';

const ApiKeysManagement: React.FC = () => {
  const [apiKeys, setApiKeys] = useState([
    {
      id: '1',
      name: 'Production API Key',
      key: 'cs_live_a1b2c3d4e5f6g7h8i9j0',
      created_at: '2026-02-15T10:30:00Z',
      last_used: '2026-03-02T14:20:00Z',
      permissions: ['read', 'write'],
      expires_at: '2027-02-15T10:30:00Z'
    },
    {
      id: '2',
      name: 'Development Key',
      key: 'cs_test_k1l2m3n4o5p6q7r8s9t0',
      created_at: '2026-03-01T08:00:00Z',
      last_used: '2026-03-02T09:15:00Z',
      permissions: ['read'],
      expires_at: '2026-06-01T08:00:00Z'
    }
  ]);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKey, setNewKey] = useState({
    name: '',
    permissions: [] as string[],
    expiresIn: '365'
  });
  const [createdKey, setCreatedKey] = useState<string | null>(null);

  const createApiKey = () => {
    const key = `cs_${newKey.permissions.includes('write') ? 'live' : 'test'}_${Math.random().toString(36).substr(2, 20)}`;
    const apiKey = {
      id: Date.now().toString(),
      name: newKey.name,
      key,
      created_at: new Date().toISOString(),
      last_used: new Date().toISOString(),
      permissions: newKey.permissions,
      expires_at: new Date(Date.now() + parseInt(newKey.expiresIn) * 86400000).toISOString()
    };

    setApiKeys([...apiKeys, apiKey]);
    setCreatedKey(key);
    setShowCreateModal(false);
  };

  const revokeKey = (id: string) => {
    if (window.confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) {
      setApiKeys(apiKeys.filter(k => k.id !== id));
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('✅ API key copied to clipboard!');
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const maskKey = (key: string) => {
    return key.substr(0, 12) + '•••••••••••••••••••';
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">API Keys</h1>
          <p className="text-gray-600">Manage API keys for programmatic access</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          🔑 Create API Key
        </button>
      </div>

      {/* Warning Banner */}
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
        <div className="flex">
          <div className="text-2xl mr-3">⚠️</div>
          <div>
            <div className="font-medium text-yellow-800">Security Notice</div>
            <div className="text-sm text-yellow-700">
              API keys provide full access to your account. Never share them publicly or commit them to version control.
            </div>
          </div>
        </div>
      </div>

      {/* API Keys Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">API Key</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Permissions</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Used</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Expires</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {apiKeys.map((apiKey) => (
              <tr key={apiKey.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="font-medium">{apiKey.name}</div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <code className="text-sm bg-gray-100 px-2 py-1 rounded font-mono">
                      {maskKey(apiKey.key)}
                    </code>
                    <button
                      onClick={() => copyToClipboard(apiKey.key)}
                      className="text-gray-400 hover:text-gray-600"
                      title="Copy to clipboard"
                    >
                      📋
                    </button>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex gap-1">
                    {apiKey.permissions.map((perm) => (
                      <span
                        key={perm}
                        className={`px-2 py-1 text-xs rounded ${
                          perm === 'write' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {perm}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {formatDate(apiKey.created_at)}
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {apiKey.last_used ? formatDate(apiKey.last_used) : 'Never'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {formatDate(apiKey.expires_at)}
                </td>
                <td className="px-6 py-4">
                  <button
                    onClick={() => revokeKey(apiKey.id)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Revoke
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {apiKeys.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No API keys created yet
          </div>
        )}
      </div>

      {/* Usage Example */}
      <div className="bg-white rounded-lg shadow p-6 mt-6">
        <h2 className="text-lg font-semibold mb-4">📖 API Usage Example</h2>
        <div className="bg-gray-900 text-gray-100 rounded p-4 font-mono text-sm overflow-x-auto">
          <div className="text-gray-400"># List all findings</div>
          <div>curl -X GET https://api.cybershield.io/api/v1/findings \</div>
          <div>  -H "Authorization: Bearer cs_live_a1b2c3d4e5f6..." \</div>
          <div>  -H "Content-Type: application/json"</div>
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <>
          <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => setShowCreateModal(false)} />
          <div className="fixed inset-0 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full m-4">
              <div className="p-6 border-b">
                <h2 className="text-xl font-bold">Create API Key</h2>
              </div>
              
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Key Name</label>
                  <input
                    type="text"
                    value={newKey.name}
                    onChange={(e) => setNewKey({ ...newKey, name: e.target.value })}
                    className="w-full border rounded px-4 py-2"
                    placeholder="e.g., Production API Key"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Permissions</label>
                  <div className="space-y-2">
                    {[
                      { id: 'read', label: 'Read', desc: 'View scans and findings' },
                      { id: 'write', label: 'Write', desc: 'Create scans and modify data' }
                    ].map((perm) => (
                      <label key={perm.id} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={newKey.permissions.includes(perm.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setNewKey({ ...newKey, permissions: [...newKey.permissions, perm.id] });
                            } else {
                              setNewKey({ ...newKey, permissions: newKey.permissions.filter(p => p !== perm.id) });
                            }
                          }}
                          className="mr-2"
                        />
                        <div>
                          <span className="font-medium">{perm.label}</span>
                          <span className="text-sm text-gray-600 ml-2">({perm.desc})</span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Expires In</label>
                  <select
                    value={newKey.expiresIn}
                    onChange={(e) => setNewKey({ ...newKey, expiresIn: e.target.value })}
                    className="w-full border rounded px-4 py-2"
                  >
                    <option value="30">30 days</option>
                    <option value="90">90 days</option>
                    <option value="365">1 year</option>
                    <option value="730">2 years</option>
                  </select>
                </div>
              </div>

              <div className="p-6 border-t bg-gray-50 flex justify-end gap-3 rounded-b-lg">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-100"
                >
                  Cancel
                </button>
                <button
                  onClick={createApiKey}
                  disabled={!newKey.name || newKey.permissions.length === 0}
                  className={`px-4 py-2 rounded text-white ${
                    !newKey.name || newKey.permissions.length === 0
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700'
                  }`}
                >
                  Create Key
                </button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Created Key Modal */}
      {createdKey && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full m-4 p-6">
            <div className="text-center mb-4">
              <div className="text-5xl mb-2">🔑</div>
              <h2 className="text-xl font-bold">API Key Created!</h2>
            </div>

            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3 mb-4">
              <p className="text-sm text-yellow-800">
                Copy this key now. You won't be able to see it again!
              </p>
            </div>

            <div className="bg-gray-100 p-3 rounded mb-4">
              <code className="text-sm font-mono break-all">{createdKey}</code>
            </div>

            <button
              onClick={() => {
                copyToClipboard(createdKey);
                setCreatedKey(null);
              }}
              className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Copy & Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApiKeysManagement;
