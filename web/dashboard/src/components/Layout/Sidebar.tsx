import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Sidebar: React.FC = () => {
  const location = useLocation();

  const menuItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/analytics', label: 'Analytics', icon: '📈' },
    { path: '/history', label: 'Scan History', icon: '📜' },
    { path: '/schedule', label: 'Schedules', icon: '⏰' },
    { path: '/reports', label: 'Reports', icon: '📄' },
    { path: '/audit', label: 'Audit Logs', icon: '🔍' },
    { path: '/remediation', label: 'Remediation', icon: '🔧' },
    { path: '/cloud', label: 'Cloud Security', icon: '☁️' },
    { path: '/secrets', label: 'Secrets Scanner', icon: '🔐' },
    { path: '/threats', label: 'Threat Intel', icon: '🕵️' },
    { path: '/container', label: 'Container Security', icon: '🐳' },
    { path: '/network', label: 'Network Analysis', icon: '🌐' },
    { path: '/users', label: 'Users', icon: '👥' },
    { path: '/api-keys', label: 'API Keys', icon: '🔑' },
    { path: '/email', label: 'Email Config', icon: '📧' },
    { path: '/slack', label: 'Slack', icon: '💬' },
    { path: '/2fa', label: '2FA', icon: '🛡️' },
    { path: '/theme', label: 'Theme', icon: '🎨' },
    { path: '/settings', label: 'Settings', icon: '⚙️' },
  ];

  return (
    <aside className="w-64 bg-gray-800 min-h-screen">
      <nav className="mt-6">
        {menuItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`flex items-center px-6 py-3 text-gray-300 hover:bg-gray-700 hover:text-white transition ${
              location.pathname === item.path ? 'bg-gray-700 text-white' : ''
            }`}
          >
            <span className="mr-3 text-xl">{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
