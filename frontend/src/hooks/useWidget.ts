import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { widgetApi, type CreateWidgetData } from '../api/widgets';
import toast from 'react-hot-toast';

export const useWidgets = (dashboardId: string) => {
  return useQuery({
    queryKey: ['widgets', dashboardId],
    queryFn: () => widgetApi.list(dashboardId),
    enabled: !!dashboardId,
    staleTime: 5000, // 5 seconds - shorter to allow quicker updates after mutations
    refetchOnWindowFocus: false,
    refetchOnMount: 'always', // Always refetch on mount to get latest data
  });
};

export const useWidget = (id: string) => {
  return useQuery({
    queryKey: ['widget', id],
    queryFn: () => widgetApi.get(id),
    enabled: !!id,
  });
};

export const useCreateWidget = (dashboardId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (widgetData: CreateWidgetData) =>
      widgetApi.create(dashboardId, widgetData),
    onSuccess: async () => {
      // Invalidate queries - React Query will refetch automatically based on component usage
      await queryClient.invalidateQueries({ 
        queryKey: ['dashboard', dashboardId],
        refetchType: 'active' 
      });
      await queryClient.invalidateQueries({ 
        queryKey: ['widgets', dashboardId],
        refetchType: 'active'
      });
      toast.success('Widget created successfully!');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create widget');
    },
  });
};

export const useUpdateWidget = (id: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (widgetData: Partial<CreateWidgetData>) =>
      widgetApi.update(id, widgetData),
    onSuccess: async (data) => {
      // Invalidate queries - React Query will refetch automatically based on component usage
      await queryClient.invalidateQueries({ 
        queryKey: ['widget', id],
        refetchType: 'active'
      });
      await queryClient.invalidateQueries({ 
        queryKey: ['widgetData', id],
        refetchType: 'active'
      });
      await queryClient.invalidateQueries({ 
        queryKey: ['dashboard', data.dashboard_id],
        refetchType: 'active'
      });
      await queryClient.invalidateQueries({ 
        queryKey: ['widgets', data.dashboard_id],
        refetchType: 'active'
      });
      
      toast.success('Widget updated successfully!');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update widget');
    },
  });
};

export const useDeleteWidget = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: widgetApi.delete,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ 
        queryKey: ['widgets'],
        refetchType: 'active'
      });
      await queryClient.invalidateQueries({ 
        queryKey: ['dashboard'],
        refetchType: 'active'
      });
      toast.success('Widget deleted successfully!');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete widget');
    },
  });
};

export const useWidgetData = (id: string) => {
  return useQuery({
    queryKey: ['widgetData', id],
    queryFn: () => widgetApi.getData(id),
    enabled: !!id,
    refetchInterval: 30000, // Refresh every 30 seconds
  });
};

export const useRefreshWidget = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: widgetApi.refresh,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['widgetData', id] });
      toast.success('Widget refreshed!');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to refresh widget');
    },
  });
};
