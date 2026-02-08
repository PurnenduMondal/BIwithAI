import apiClient from './client';
import type { DataSource } from '@/types';

export interface CreateDataSourceData {
  name: string;
  type: 'csv' | 'postgresql' | 'mysql' | 'api' | 'google_sheets';
  connection_config: Record<string, any>;
  sync_frequency?: 'manual' | 'hourly' | 'daily' | 'weekly';
}

export const dataSourceApi = {
  list: async (): Promise<DataSource[]> => {
    const { data } = await apiClient.get('/api/v1/data-sources/');
    return data;
  },

  get: async (id: string): Promise<DataSource> => {
    const { data } = await apiClient.get(`/api/v1/data-sources/${id}`);
    return data;
  },

  create: async (dataSourceData: CreateDataSourceData): Promise<DataSource> => {
    const { data } = await apiClient.post('/api/v1/data-sources/', dataSourceData);
    return data;
  },

  uploadCSV: async (file: File, name?: string): Promise<DataSource> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const { data } = await apiClient.post(
      `/api/v1/data-sources/upload-csv${name ? `?name=${encodeURIComponent(name)}` : ''}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return data;
  },

  update: async (id: string, updateData: Partial<CreateDataSourceData>): Promise<DataSource> => {
    const { data } = await apiClient.put(`/api/v1/data-sources/${id}`, updateData);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/data-sources/${id}`);
  },

  testConnection: async (id: string): Promise<{ status: string; message: string }> => {
    const { data } = await apiClient.post(`/api/v1/data-sources/${id}/test-connection`);
    return data;
  },

  sync: async (id: string): Promise<{ status: string; message: string }> => {
    const { data } = await apiClient.post(`/api/v1/data-sources/${id}/sync`);
    return data;
  },

  preview: async (id: string, limit: number = 100): Promise<any> => {
    const { data } = await apiClient.get(`/api/v1/data-sources/${id}/preview?limit=${limit}`);
    return data;
  },

  getSchema: async (id: string): Promise<Record<string, any>> => {
    const { data } = await apiClient.get(`/api/v1/data-sources/${id}/schema`);
    return data;
  },
};