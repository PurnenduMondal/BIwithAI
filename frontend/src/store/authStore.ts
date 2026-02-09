import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from './types';

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  setUser: (user: User) => void;
  setTokens: (token: string, refreshToken: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      
      setUser: (user) => set({ user, isAuthenticated: true }),
      
      setTokens: (token, refreshToken) => 
        set({ token, refreshToken, isAuthenticated: true }),
      
      logout: () => 
        set({ 
          user: null, 
          token: null, 
          refreshToken: null, 
          isAuthenticated: false 
        }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated, // Add this to persist
      }),
      // Rehydrate isAuthenticated based on token presence
      onRehydrateStorage: () => (state) => {
        if (state && state.token) {
          state.isAuthenticated = true;
        }
      },
    }
  )
);