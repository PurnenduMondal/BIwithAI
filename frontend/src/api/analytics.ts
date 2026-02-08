import apiClient from './client';

export interface ForecastParams {
  data_source_id: string;
  metric: string;
  periods?: number;
}

export interface CorrelationParams {
  data_source_id: string;
  metrics: string[];
  method?: 'pearson' | 'spearman' | 'kendall';
  min_correlation?: number;
  max_p_value?: number;
}

export const analyticsApi = {
  nlpQuery: async (dataSourceId: string, query: string): Promise<any> => {
    const { data } = await apiClient.post(
      `/api/v1/analytics/query?data_source_id=${dataSourceId}&query=${encodeURIComponent(query)}`
    );
    return data;
  },

  forecast: async (params: ForecastParams): Promise<any> => {
    const { data } = await apiClient.get('/api/v1/analytics/forecast', { params });
    return data;
  },

  correlation: async (params: CorrelationParams): Promise<any> => {
    const { data } = await apiClient.post('/api/v1/analytics/correlation', null, { params });
    return data;
  },

  detectAnomalies: async (
    dataSourceId: string,
    metric: string,
    threshold: number = 2.0
  ): Promise<any> => {
    const { data } = await apiClient.get('/api/v1/analytics/anomalies', {
      params: { data_source_id: dataSourceId, metric, threshold },
    });
    return data;
  },
};