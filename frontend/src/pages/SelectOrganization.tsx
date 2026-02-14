import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { redirectToSubdomain } from '../utils/tenant';
import { BuildingOfficeIcon, ArrowRightIcon } from '@heroicons/react/24/outline';

export const SelectOrganization = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    // If not logged in, redirect to login
    if (!user) {
      navigate('/login');
      return;
    }

    // If user has no organizations or only one, redirect to home
    if (!user.organizations || user.organizations.length === 0) {
      navigate('/home');
    } else if (user.organizations.length === 1) {
      const org = user.organizations[0];
      if (org.subdomain) {
        redirectToSubdomain(org.subdomain, '/home');
      } else {
        navigate('/home');
      }
    }
  }, [user, navigate]);

  if (!user || !user.organizations || user.organizations.length <= 1) {
    return null;
  }

  const handleSelectOrganization = (subdomain: string | null) => {
    if (subdomain) {
      redirectToSubdomain(subdomain, '/home');
    } else {
      navigate('/home');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Select Organization</h1>
          <p className="text-gray-600">Choose which organization you'd like to access</p>
        </div>

        <div className="grid gap-4">
          {user.organizations.map((org) => (
            <button
              key={org.org_id}
              onClick={() => handleSelectOrganization(org.subdomain)}
              className="bg-white rounded-lg shadow-sm hover:shadow-md transition-all p-6 text-left group"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center group-hover:bg-blue-200 transition-colors">
                    <BuildingOfficeIcon className="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{org.org_name}</h3>
                    {org.subdomain && (
                      <p className="text-sm text-gray-500">{org.subdomain}.localhost:3000</p>
                    )}
                    <p className="text-xs text-gray-400 capitalize mt-1">Role: {org.role}</p>
                  </div>
                </div>
                <ArrowRightIcon className="h-5 w-5 text-gray-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
              </div>
            </button>
          ))}
        </div>

        <div className="mt-8 text-center">
          <button
            onClick={() => navigate('/home')}
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            Skip for now
          </button>
        </div>
      </div>
    </div>
  );
};
