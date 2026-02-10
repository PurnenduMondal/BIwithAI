import apiClient from './client';
import type { User } from '../types';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const { data } = await apiClient.post('/api/v1/auth/login', credentials);
    return data;
  },

  register: async (userData: RegisterData): Promise<User> => {
    const { data } = await apiClient.post('/api/v1/auth/register', userData);
    return data;
  },

  getCurrentUser: async (): Promise<User> => {
    const { data } = await apiClient.get('/api/v1/users/me');
    return data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/api/v1/auth/logout');
  },

  refreshToken: async (refreshToken: string): Promise<AuthResponse> => {
    const { data } = await apiClient.post('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });
    return data;
  },
};