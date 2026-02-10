import apiClient from './client';
import type { Alert } from '../types';

export interface CreateAlertData {
  dashboard_id: string;
  widget_id?: string;
  condition: Record<string, any>;
  notification_channels?: any[];
  is_active?: boolean;
}

export const alertApi = {
  list: async (dashboardId?: string): Promise<Alert[]> => {
    const params = dashboardId ? { dashboard_id: dashboardId } : {};
    const { data } = await apiClient.get('/api/v1/alerts/', { params });
    return data;
  },

  get: async (id: string): Promise<Alert> => {
    const { data } = await apiClient.get(`/api/v1/alerts/${id}`);
    return data;
  },

  create: async (alertData: CreateAlertData): Promise<Alert> => {
    const { data } = await apiClient.post('/api/v1/alerts/', alertData);
    return data;
  },

  update: async (id: string, alertData: Partial<CreateAlertData>): Promise<Alert> => {
    const { data } = await apiClient.put(`/api/v1/alerts/${id}`, alertData);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/alerts/${id}`);
  },

  getHistory: async (alertId?: string): Promise<any[]> => {
    const params = alertId ? { alert_id: alertId } : {};
    const { data } = await apiClient.get('/api/v1/alerts/history', { params });
    return data;
  },
};