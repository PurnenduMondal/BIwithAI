import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi, type LoginCredentials, type RegisterData } from '../api/auth';
import { useAuthStore } from '../store/authStore';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { getCurrentSubdomain, redirectToSubdomain, storeSubdomainContext } from '../utils/tenant';

export const useAuth = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { setUser, setTokens, logout: logoutStore } = useAuthStore();

  const { data: user, isLoading } = useQuery({
    queryKey: ['currentUser'],
    queryFn: authApi.getCurrentUser,
    enabled: !!useAuthStore.getState().token,
    retry: false,
  });

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: async (data) => {
      setTokens(data.access_token, data.refresh_token);
      
      // Fetch user data with organizations
      const userData = await authApi.getCurrentUser();
      setUser(userData);
      
      toast.success('Login successful!');
      
      // Handle multi-tenant redirect
      const currentSubdomain = getCurrentSubdomain();
      
      // If user has organizations
      if (userData.organizations && userData.organizations.length > 0) {
        // If already on a subdomain, verify it's valid for this user
        if (currentSubdomain) {
          const hasAccess = userData.organizations.some(
            org => org.subdomain === currentSubdomain
          );
          
          if (hasAccess) {
            storeSubdomainContext(currentSubdomain);
            navigate('/home');
          } else {
            // Redirect to first organization's subdomain
            const firstOrg = userData.organizations[0];
            if (firstOrg.subdomain) {
              redirectToSubdomain(firstOrg.subdomain, '/home');
            } else {
              navigate('/home');
            }
          }
        } else {
          // Not on a subdomain - check if user has only one org
          if (userData.organizations.length === 1) {
            const org = userData.organizations[0];
            if (org.subdomain) {
              redirectToSubdomain(org.subdomain, '/home');
            } else {
              navigate('/home');
            }
          } else {
            // Multiple orgs - show organization selector
            navigate('/select-organization');
          }
        }
      } else {
        // No organizations yet
        navigate('/home');
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Login failed');
    },
  });

  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: () => {
      toast.success('Registration successful! Please login.');
      navigate('/login');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Registration failed');
    },
  });

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      logoutStore();
      queryClient.clear();
      storeSubdomainContext(null); // Clear subdomain context
      
      // Redirect to base domain login without token transfer
      const currentSubdomain = getCurrentSubdomain();
      if (currentSubdomain) {
        redirectToSubdomain(null, '/login', false); // Don't transfer auth on logout
      } else {
        navigate('/login');
      }
      
      toast.success('Logged out successfully');
    }
  };

  return {
    user,
    isLoading,
    login: loginMutation.mutate,
    register: registerMutation.mutate,
    logout,
    isLoginLoading: loginMutation.isPending,
    isRegisterLoading: registerMutation.isPending,
  };
};