import apiClient from './client';

export interface ChatSession {
  id: string;
  user_id: string;
  organization_id: string;
  data_source_id?: string;
  title?: string;
  status: string;
  meta_data: Record<string, any>;
  created_at: string;
  updated_at: string;
  last_message_at: string;
  message_count: number;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  message_type: string;
  meta_data: Record<string, any>;
  token_count: number;
  processing_time_ms?: number;
  created_at: string;
  widget_previews?: Array<{
    widget: {
      id: string;
      title: string;
      description?: string;
      widget_type: string;
      query_config: Record<string, any>;
      chart_config: Record<string, any>;
      position: Record<string, any>;
      ai_reasoning?: string;
    };
    data: any[];
  }>;
  dashboard_id?: string;
}

export interface CreateSessionRequest {
  data_source_id?: string;
  title?: string;
  initial_message?: string;
}

export interface SendMessageRequest {
  content: string;
  context?: Array<{ role: string; content: string }>;
}

export interface GenerateDashboardRequest {
  query: string;
  data_source_id: string;
  refinement?: boolean;
  existing_dashboard_id?: string;
}

export interface DashboardGenerationResponse {
  dashboard_id: string;
  generation_id: string;
  explanation: string;
  charts: any[];
  insights: any[];
  suggestions: string[];
  processing_time_ms: number;
}

export const chatApi = {
  createSession: async (request: CreateSessionRequest): Promise<ChatSession> => {
    const { data } = await apiClient.post('/api/v1/chat/sessions', request);
    return data;
  },

  listSessions: async (page: number = 1, pageSize: number = 20) => {
    const { data } = await apiClient.get('/api/v1/chat/sessions', {
      params: { page, page_size: pageSize },
    });
    return data;
  },

  getSession: async (sessionId: string, limit: number = 50): Promise<ChatSession & { messages: ChatMessage[] }> => {
    const { data } = await apiClient.get(`/api/v1/chat/sessions/${sessionId}`, {
      params: { limit },
    });
    return data;
  },

  sendMessage: async (sessionId: string, request: SendMessageRequest): Promise<ChatMessage> => {
    const { data } = await apiClient.post(
      `/api/v1/chat/sessions/${sessionId}/messages`,
      request
    );
    return data;
  },

  deleteSession: async (sessionId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/chat/sessions/${sessionId}`);
  },

  archiveSession: async (sessionId: string): Promise<void> => {
    await apiClient.patch(`/api/v1/chat/sessions/${sessionId}/archive`);
  },

  generateDashboard: async (request: GenerateDashboardRequest): Promise<DashboardGenerationResponse> => {
    const { data } = await apiClient.post('/api/v1/chat/generate', request);
    return data;
  },
};
