import api from './api';
import { DashboardSummary, Finding } from '../types';

export const dashboardService = {
  async getSummary(): Promise<DashboardSummary> {
    const response = await api.get<DashboardSummary>('/dashboard/summary');
    return response.data;
  },

  async getRecentFindings(limit: number = 10): Promise<Finding[]> {
    const response = await api.get<Finding[]>('/dashboard/findings', {
      params: { limit },
    });
    return response.data;
  },

  async getMetrics(timeRange: string = '7d'): Promise<any> {
    const response = await api.get('/dashboard/metrics', {
      params: { time_range: timeRange },
    });
    return response.data;
  },
};

export default dashboardService;
