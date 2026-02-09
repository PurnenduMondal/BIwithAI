import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { widgetApi, type CreateWidgetData } from '../api/widgets';
import toast from 'react-hot-toast';

export const useWidgets = (dashboardId: string) => {
  return useQuery({
    queryKey: ['widgets', dashboardId],
    queryFn: () => widgetApi.list(dashboardId),
    enabled: !!dashboardId,
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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard', dashboardId] });
      queryClient.invalidateQueries({ queryKey: ['widgets', dashboardId] });
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
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['widget', id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard', data.dashboard_id] });
      queryClient.invalidateQueries({ queryKey: ['widgets', data.dashboard_id] });
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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['widgets'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
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
