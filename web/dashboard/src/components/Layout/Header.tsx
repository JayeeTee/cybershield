import React from 'react';
import { Link } from 'react-router-dom';
import NotificationBell from '../Notifications/NotificationBell';

const Header: React.FC = () => {
  return (
    <header className="bg-gray-900 text-white shadow-lg">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="text-2xl">🛡️</div>
          <h1 className="text-xl font-bold">CyberShield</h1>
        </div>

        <div className="flex items-center space-x-4">
          <NotificationBell />
          <button className="text-sm bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded transition">
            Scan Now
          </button>
          <div className="text-sm">Welcome, Admin</div>
        </div>
      </div>
    </header>
  );
};

export default Header;
