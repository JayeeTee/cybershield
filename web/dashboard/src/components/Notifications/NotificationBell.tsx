import React, { useState } from 'react';
import { useWebSocket } from '../../contexts/WebSocketContext';

const NotificationBell: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { notifications, unreadCount, markAsRead, clearNotifications, connected } = useWebSocket();

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'scan_complete': return '✅';
      case 'finding': return '🔍';
      case 'error': return '❌';
      case 'warning': return '⚠️';
      default: return 'ℹ️';
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'scan_complete': return 'border-green-500 bg-green-50';
      case 'finding': return 'border-blue-500 bg-blue-50';
      case 'error': return 'border-red-500 bg-red-50';
      case 'warning': return 'border-yellow-500 bg-yellow-50';
      default: return 'border-gray-500 bg-gray-50';
    }
  };

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  return (
    <div className="relative">
      {/* Bell Icon */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        
        {/* Unread Badge */}
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1 -translate-y-1 bg-red-600 rounded-full">
            {unreadCount}
          </span>
        )}
        
        {/* Connection Status */}
        <span className={`absolute bottom-0 right-0 block h-2 w-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Panel */}
          <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-xl z-20 border">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b">
              <h3 className="text-lg font-semibold">Notifications</h3>
              <div className="flex gap-2">
                {notifications.length > 0 && (
                  <button
                    onClick={clearNotifications}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    Clear all
                  </button>
                )}
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Notifications List */}
            <div className="max-h-96 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <div className="text-4xl mb-2">🔔</div>
                  <div>No notifications yet</div>
                </div>
              ) : (
                notifications.map((notification) => (
                  <div
                    key={notification.id}
                    onClick={() => markAsRead(notification.id)}
                    className={`border-l-4 p-4 cursor-pointer hover:bg-gray-50 transition ${
                      !notification.read ? 'bg-blue-50' : ''
                    } ${getNotificationColor(notification.type)}`}
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">{getNotificationIcon(notification.type)}</span>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <div className="font-semibold text-sm">{notification.title}</div>
                          <div className="text-xs text-gray-500">
                            {formatTime(notification.timestamp)}
                          </div>
                        </div>
                        <div className="text-sm text-gray-700 mt-1">{notification.message}</div>
                        {!notification.read && (
                          <div className="mt-2">
                            <span className="inline-block w-2 h-2 bg-blue-600 rounded-full" />
                            <span className="text-xs text-blue-600 ml-1">New</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Footer */}
            {connected && (
              <div className="px-4 py-2 bg-gray-50 border-t text-xs text-gray-600 flex items-center gap-2">
                <span className="inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                Real-time updates active
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default NotificationBell;
