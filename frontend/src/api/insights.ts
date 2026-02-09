import apiClient from './client';
import type { Insight } from './types';

export const insightApi = {
  list: async (dashboardId: string): Promise<Insight[]> => {
    const { data } = await apiClient.get(`/api/v1/insights/dashboards/${dashboardId}/insights`);
    return data;
  },

  get: async (id: string): Promise<Insight> => {
    const { data } = await apiClient.get(`/api/v1/insights/insights/${id}`);
    return data;
  },

  generate: async (dashboardId: string, context?: string): Promise<any> => {
    const { data } = await apiClient.post(
      `/api/v1/insights/dashboards/${dashboardId}/insights/generate`,
      { context }
    );
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/insights/insights/${id}`);
  },
};