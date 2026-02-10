import apiClient from './client';
import type { Dashboard } from '../types';

export interface CreateDashboardData {
  name: string;
  description?: string;
  layout_config?: Record<string, any>;
  filters?: any[];
  theme?: Record<string, any>;
}

export interface GenerateDashboardData {
  data_source_id: string;
  preferences?: Record<string, any>;
}

export const dashboardApi = {
  list: async (): Promise<Dashboard[]> => {
    const { data } = await apiClient.get('/api/v1/dashboards/');
    return data;
  },

  get: async (id: string): Promise<Dashboard> => {
    const { data } = await apiClient.get(`/api/v1/dashboards/${id}`);
    return data;
  },

  create: async (dashboardData: CreateDashboardData): Promise<Dashboard> => {
    const { data } = await apiClient.post('/api/v1/dashboards/', dashboardData);
    return data;
  },

  update: async (id: string, dashboardData: Partial<CreateDashboardData>): Promise<Dashboard> => {
    const { data } = await apiClient.put(`/api/v1/dashboards/${id}`, dashboardData);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/dashboards/${id}`);
  },

  generate: async (generateData: GenerateDashboardData): Promise<Dashboard> => {
    const { data } = await apiClient.post('/api/v1/dashboards/generate', generateData);
    return data;
  },

  duplicate: async (id: string): Promise<Dashboard> => {
    const { data} = await apiClient.post(`/api/v1/dashboards/${id}/duplicate`);
    return data;
  },

  share: async (id: string): Promise<{ share_token: string; share_url: string }> => {
    const { data } = await apiClient.post(`/api/v1/dashboards/${id}/share`);
    return data;
  },

  getTemplates: async (): Promise<Dashboard[]> => {
    const { data } = await apiClient.get('/api/v1/dashboards/templates');
    return data;
  },
};