import React, { useState } from 'react';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'scanner' | 'viewer';
  created_at: string;
  last_login?: string;
  active: boolean;
}

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([
    {
      id: '1',
      username: 'admin',
      email: 'admin@cybershield.local',
      role: 'admin',
      created_at: '2026-02-01T00:00:00Z',
      last_login: '2026-03-02T10:30:00Z',
      active: true
    },
    {
      id: '2',
      username: 'scanner_service',
      email: 'scanner@cybershield.local',
      role: 'scanner',
      created_at: '2026-02-15T00:00:00Z',
      last_login: '2026-03-01T14:20:00Z',
      active: true
    },
    {
      id: '3',
      username: 'viewer_user',
      email: 'viewer@cybershield.local',
      role: 'viewer',
      created_at: '2026-02-20T00:00:00Z',
      active: false
    }
  ]);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newUser, setNewUser] = useState({
    username: '',
    email: '',
    password: '',
    role: 'viewer' as User['role']
  });

  const getRoleBadgeColor = (role: User['role']) => {
    switch (role) {
      case 'admin': return 'bg-red-100 text-red-800';
      case 'scanner': return 'bg-blue-100 text-blue-800';
      case 'viewer': return 'bg-gray-100 text-gray-800';
    }
  };

  const getRoleLabel = (role: User['role']) => {
    return role.charAt(0).toUpperCase() + role.slice(1);
  };

  const handleCreateUser = async () => {
    if (!newUser.username || !newUser.email || !newUser.password) return;
    
    try {
      // Add to local state for demo
      const user: User = {
        id: Date.now().toString(),
        ...newUser,
        created_at: new Date().toISOString(),
        active: true
      };
      setUsers([...users, user]);
      setShowCreateModal(false);
      setNewUser({ username: '', email: '', password: '', role: 'viewer' });
    } catch (error) {
      console.error('Failed to create user:', error);
    }
  };

  const handleToggleUser = (userId: string) => {
    setUsers(users.map(u => 
      u.id === userId ? { ...u, active: !u.active } : u
    ));
  };

  const handleDeleteUser = (userId: string) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      setUsers(users.filter(u => u.id !== userId));
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
          <p className="text-gray-600">Manage users and access control</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          ➕ Create User
        </button>
      </div>

      {/* Role Legend */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <h3 className="font-semibold mb-2">Role Permissions</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="flex items-start gap-2">
            <span className={`px-2 py-1 rounded text-xs font-semibold ${getRoleBadgeColor('admin')}`}>
              Admin
            </span>
            <span className="text-sm text-gray-600">Full access to all features</span>
          </div>
          <div className="flex items-start gap-2">
            <span className={`px-2 py-1 rounded text-xs font-semibold ${getRoleBadgeColor('scanner')}`}>
              Scanner
            </span>
            <span className="text-sm text-gray-600">Run scans, view findings</span>
          </div>
          <div className="flex items-start gap-2">
            <span className={`px-2 py-1 rounded text-xs font-semibold ${getRoleBadgeColor('viewer')}`}>
              Viewer
            </span>
            <span className="text-sm text-gray-600">Read-only access</span>
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Login</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {users.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div>
                    <div className="font-medium">{user.username}</div>
                    <div className="text-sm text-gray-500">{user.email}</div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${getRoleBadgeColor(user.role)}`}>
                    {getRoleLabel(user.role)}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {formatDate(user.created_at)}
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {user.last_login ? formatDate(user.last_login) : 'Never'}
                </td>
                <td className="px-6 py-4">
                  {user.active ? (
                    <span className="flex items-center gap-1 text-green-600">
                      <span className="w-2 h-2 bg-green-500 rounded-full" />
                      Active
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-gray-400">
                      <span className="w-2 h-2 bg-gray-400 rounded-full" />
                      Inactive
                    </span>
                  )}
                </td>
                <td className="px-6 py-4">
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleToggleUser(user.id)}
                      className={`text-sm ${
                        user.active ? 'text-yellow-600 hover:text-yellow-800' : 'text-green-600 hover:text-green-800'
                      }`}
                    >
                      {user.active ? 'Disable' : 'Enable'}
                    </button>
                    <button
                      onClick={() => handleDeleteUser(user.id)}
                      className="text-sm text-red-600 hover:text-red-800"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <>
          <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => setShowCreateModal(false)} />
          <div className="fixed inset-0 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full m-4">
              <div className="p-6 border-b">
                <h2 className="text-xl font-bold">Create New User</h2>
              </div>
              
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Username</label>
                  <input
                    type="text"
                    value={newUser.username}
                    onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                    className="w-full border rounded px-4 py-2"
                    placeholder="Enter username"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Email</label>
                  <input
                    type="email"
                    value={newUser.email}
                    onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                    className="w-full border rounded px-4 py-2"
                    placeholder="user@example.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Password</label>
                  <input
                    type="password"
                    value={newUser.password}
                    onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                    className="w-full border rounded px-4 py-2"
                    placeholder="Enter password"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Role</label>
                  <select
                    value={newUser.role}
                    onChange={(e) => setNewUser({ ...newUser, role: e.target.value as User['role'] })}
                    className="w-full border rounded px-4 py-2"
                  >
                    <option value="viewer">Viewer (Read-only)</option>
                    <option value="scanner">Scanner (Run scans)</option>
                    <option value="admin">Admin (Full access)</option>
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
                  onClick={handleCreateUser}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Create User
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default UserManagement;
