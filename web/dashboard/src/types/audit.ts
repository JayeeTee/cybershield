export interface AuditLog {
  id: string;
  timestamp: Date;
  user: string;
  action: 'login' | 'scan_started' | 'scan_completed' | 'user_created' | 'user_deleted' | 'setting_changed' | 'finding_viewed' | 'report_exported';
  resource: string;
  details: string;
  ip_address: string;
  user_agent: string;
}

export const generateAuditLogs = (): AuditLog[] => {
  const actions: AuditLog['action'][] = ['login', 'scan_started', 'scan_completed', 'user_created', 'user_deleted', 'setting_changed', 'finding_viewed', 'report_exported'];
  
  return Array.from({ length: 50 }, (_, i) => ({
    id: `log-${i + 1}`,
    timestamp: new Date(Date.now() - Math.random() * 7 * 86400000), // Last 7 days
    user: ['admin', 'scanner_service', 'viewer_user'][Math.floor(Math.random() * 3)],
    action: actions[Math.floor(Math.random() * actions.length)],
    resource: ['Cloud Scanner', 'Container Scanner', 'User Management', 'Settings', 'Dashboard'][Math.floor(Math.random() * 5)],
    details: 'Action performed successfully',
    ip_address: `192.168.1.${Math.floor(Math.random() * 255)}`,
    user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  })).sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
};
