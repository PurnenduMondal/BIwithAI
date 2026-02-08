import apiClient from './client';

export type ExportFormat = 'pdf' | 'png' | 'svg' | 'json' | 'xlsx';

export interface ExportJobResponse {
  job_id: string;
  status: string;
  progress?: number;
  message?: string;
  download_url?: string;
  error?: string;
}

export const exportApi = {
  exportDashboard: async (
    dashboardId: string,
    format: ExportFormat
  ): Promise<ExportJobResponse> => {
    const { data } = await apiClient.post(
      `/api/v1/exports/dashboard/${dashboardId}?format=${format}`
    );
    return data;
  },

  exportWidget: async (
    widgetId: string,
    format: ExportFormat,
    width?: number,
    height?: number
  ): Promise<ExportJobResponse> => {
    const params = new URLSearchParams({ format });
    if (width) params.append('width', width.toString());
    if (height) params.append('height', height.toString());

    const { data } = await apiClient.post(
      `/api/v1/exports/widget/${widgetId}?${params.toString()}`
    );
    return data;
  },

  getJobStatus: async (jobId: string): Promise<ExportJobResponse> => {
    const { data } = await apiClient.get(`/api/v1/exports/jobs/${jobId}/status`);
    return data;
  },
};