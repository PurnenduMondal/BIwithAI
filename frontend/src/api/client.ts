import axios, { AxiosError, type AxiosRequestConfig } from 'axios';
import { useAuthStore } from '../store/authStore';
import { getCurrentSubdomain } from '../utils/tenant';

const API_BASE_URL = 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token and organization subdomain
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add organization subdomain for multi-tenant support
    const subdomain = getCurrentSubdomain();
    if (subdomain) {
      config.headers['X-Organization-Subdomain'] = subdomain;
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // Handle 401 unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = useAuthStore.getState().refreshToken;
      
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token } = response.data;
          
          useAuthStore.getState().setTokens(access_token, refresh_token);

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }

          return apiClient(originalRequest);
        } catch (refreshError) {
          useAuthStore.getState().logout();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;