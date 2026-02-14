import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { getCurrentSubdomain } from '../utils/tenant';
import { ArrowPathIcon } from '@heroicons/react/24/outline';

/**
 * AuthTransfer component handles cross-subdomain authentication token transfer
 * 
 * When redirecting from base domain to subdomain (or between subdomains),
 * this page receives auth tokens via URL parameters and stores them in localStorage
 * for the current subdomain.
 */
export const AuthTransfer = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setTokens, setUser } = useAuthStore();
  
  useEffect(() => {
    const transferAuth = async () => {
      try {
        // Get tokens from URL parameters
        const token = searchParams.get('token');
        const refreshToken = searchParams.get('refresh_token');
        const userData = searchParams.get('user');
        const redirect = searchParams.get('redirect') || '/home';
        
        if (!token || !refreshToken) {
          console.error('Missing auth tokens in transfer');
          navigate('/login');
          return;
        }
        
        // Store tokens in this subdomain's localStorage
        setTokens(token, refreshToken);
        
        // Parse and store user data if provided
        if (userData) {
          try {
            const user = JSON.parse(decodeURIComponent(userData));
            setUser(user);
          } catch (e) {
            console.error('Failed to parse user data:', e);
          }
        }
        
        // Clean URL by removing sensitive query parameters
        const currentSubdomain = getCurrentSubdomain();
        const message = currentSubdomain 
          ? `Switching to ${currentSubdomain} organization...`
          : 'Setting up your session...';
          
        console.log(message);
        
        // Small delay to ensure storage is complete
        setTimeout(() => {
          // Navigate to target page without query params
          navigate(redirect, { replace: true });
        }, 100);
        
      } catch (error) {
        console.error('Auth transfer error:', error);
        navigate('/login');
      }
    };
    
    transferAuth();
  }, [searchParams, navigate, setTokens, setUser]);
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="text-center">
        <ArrowPathIcon className="h-12 w-12 text-blue-600 animate-spin mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Setting up your workspace...
        </h2>
        <p className="text-gray-600">
          You'll be redirected in a moment.
        </p>
      </div>
    </div>
  );
};
