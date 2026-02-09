import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dashboardApi, type CreateDashboardData, type GenerateDashboardData } from '../api/dashboards';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

export const useDashboards = () => {
  const queryClient = useQueryClient();

  return useQuery({
    queryKey: ['dashboards'],
    queryFn: dashboardApi.list,
  });
};

export const useDashboard = (id: string) => {
  return useQuery({
    queryKey: ['dashboard', id],
    queryFn: () => dashboardApi.get(id),
    enabled: !!id,
  });
};

export const useCreateDashboard = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: dashboardApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
      toast.success('Dashboard created successfully!');
      navigate(`/dashboards/${data.id}`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create dashboard');
    },
  });
};

export const useGenerateDashboard = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: dashboardApi.generate,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
      toast.success('Dashboard generated successfully!');
      navigate(`/dashboards/${data.id}`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to generate dashboard');
    },
  });
};

export const useUpdateDashboard = (id: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<CreateDashboardData>) => dashboardApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard', id] });
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
      toast.success('Dashboard updated successfully!');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update dashboard');
    },
  });
};

export const useDeleteDashboard = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: dashboardApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
      toast.success('Dashboard deleted successfully!');
      navigate('/dashboards');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete dashboard');
    },
  });
};

export const useDuplicateDashboard = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: dashboardApi.duplicate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
      toast.success('Dashboard duplicated successfully!');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to duplicate dashboard');
    },
  });
};