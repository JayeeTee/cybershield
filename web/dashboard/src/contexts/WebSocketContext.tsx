import React, { createContext, useContext, useEffect, useState, useRef } from 'react';

interface Notification {
  id: string;
  type: 'scan_complete' | 'finding' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
}

interface WebSocketContextType {
  connected: boolean;
  notifications: Notification[];
  unreadCount: number;
  markAsRead: (id: string) => void;
  clearNotifications: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
};

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [connected, setConnected] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
    };
  }, []);

  const connectWebSocket = () => {
    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
    
    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setConnected(true);
        console.log('WebSocket connected');
        
        // Add connection notification
        addNotification({
          type: 'info',
          title: 'Connected',
          message: 'Real-time updates enabled'
        });
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      wsRef.current.onclose = () => {
        setConnected(false);
        console.log('WebSocket disconnected');
        
        // Attempt reconnection after 5 seconds
        reconnectTimeout.current = setTimeout(() => {
          console.log('Attempting reconnection...');
          connectWebSocket();
        }, 5000);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      
      // Use mock mode for demo
      startMockMode();
    }
  };

  const startMockMode = () => {
    setConnected(true);
    console.log('Running in mock mode (WebSocket simulation)');
    
    // Simulate notifications every 30-60 seconds
    const mockInterval = setInterval(() => {
      const mockNotifications = [
        {
          type: 'scan_complete' as const,
          title: 'Cloud Scan Complete',
          message: 'Found 3 critical vulnerabilities in AWS environment'
        },
        {
          type: 'finding' as const,
          title: 'New Finding',
          message: 'Exposed S3 bucket detected in production account'
        },
        {
          type: 'warning' as const,
          title: 'Scan Failed',
          message: 'Container scan timed out for nginx:latest'
        }
      ];
      
      const randomNotification = mockNotifications[Math.floor(Math.random() * mockNotifications.length)];
      addNotification(randomNotification);
    }, Math.random() * 30000 + 30000); // 30-60 seconds

    return () => clearInterval(mockInterval);
  };

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'scan_complete':
        addNotification({
          type: 'scan_complete',
          title: 'Scan Complete',
          message: data.message
        });
        break;
      
      case 'finding':
        addNotification({
          type: 'finding',
          title: 'New Finding',
          message: data.message
        });
        break;
      
      case 'error':
        addNotification({
          type: 'error',
          title: 'Error',
          message: data.message
        });
        break;
      
      default:
        console.log('Unknown WebSocket message:', data);
    }
  };

  const addNotification = (notif: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notif,
      id: Date.now().toString(),
      timestamp: new Date(),
      read: false
    };
    
    setNotifications(prev => [newNotification, ...prev].slice(0, 50)); // Keep last 50
    
    // Show browser notification if permitted
    if (Notification.permission === 'granted') {
      new window.Notification(newNotification.title, {
        body: newNotification.message,
        icon: '/favicon.ico'
      });
    }
  };

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  };

  const clearNotifications = () => {
    setNotifications([]);
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <WebSocketContext.Provider value={{
      connected,
      notifications,
      unreadCount,
      markAsRead,
      clearNotifications
    }}>
      {children}
    </WebSocketContext.Provider>
  );
};
