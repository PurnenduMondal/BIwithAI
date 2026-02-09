import apiClient from './client';
import type { Widget } from '../types';

export interface CreateWidgetData {
  widget_type: 'chart' | 'metric' | 'table' | 'text' | 'ai_insight';
  title: string;
  position: {
    x: number;
    y: number;
    w: number;
    h: number;
  };
  config?: Record<string, any>;
  data_source_id?: string;
}

export const widgetApi = {
  list: async (dashboardId: string): Promise<Widget[]> => {
    const { data } = await apiClient.get(`/api/v1/widgets/dashboards/${dashboardId}/widgets`);
    return data;
  },

  get: async (id: string): Promise<Widget> => {
    const { data } = await apiClient.get(`/api/v1/widgets/${id}`);
    return data;
  },

  create: async (dashboardId: string, widgetData: CreateWidgetData): Promise<Widget> => {
    const { data } = await apiClient.post(
      `/api/v1/widgets/dashboards/${dashboardId}/widgets`,
      widgetData
    );
    return data;
  },

  update: async (id: string, widgetData: Partial<CreateWidgetData>): Promise<Widget> => {
    const { data } = await apiClient.put(`/api/v1/widgets/${id}`, widgetData);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/widgets/${id}`);
  },

  getData: async (id: string): Promise<any> => {
    const { data } = await apiClient.get(`/api/v1/widgets/${id}/data`);
    return data;
  },

  refresh: async (id: string): Promise<void> => {
    await apiClient.post(`/api/v1/widgets/${id}/refresh`);
  },
};