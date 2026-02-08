import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dataSourceApi, type CreateDataSourceData } from '@/api/dataSources';
import toast from 'react-hot-toast';

export const useDataSources = () => {
  return useQuery({
    queryKey: ['dataSources'],
    queryFn: dataSourceApi.list,
  });
};

export const useDataSource = (id: string) => {
  return useQuery({
    queryKey: ['dataSource', id],
    queryFn: () => dataSourceApi.get(id),
    enabled: !!id,
  });
};

export const useCreateDataSource = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: dataSourceApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataSources'] });
      toast.success('Data source created successfully!');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create data source');
    },
  });
};

export const useUploadCSV = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, name }: { file: File; name?: string }) =>
      dataSourceApi.uploadCSV(file, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataSources'] });
      toast.success('CSV uploaded successfully!');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to upload CSV');
    },
  });
};

export const useSyncDataSource = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: dataSourceApi.sync,
    onSuccess: (_, dataSourceId) => {
      queryClient.invalidateQueries({ queryKey: ['dataSource', dataSourceId] });
      toast.success('Data source sync started!');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to sync data source');
    },
  });
};

export const useDeleteDataSource = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: dataSourceApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataSources'] });
      toast.success('Data source deleted successfully!');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete data source');
    },
  });
};