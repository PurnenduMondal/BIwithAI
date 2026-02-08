import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Input } from '@/components/common/Input';
import { Button } from '@/components/common/Button';
import { useCreateDashboard } from '@/hooks/useDashboard';
import { useNavigate } from 'react-router-dom';

const dashboardSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
});

type DashboardFormData = z.infer<typeof dashboardSchema>;

export const DashboardCreate = () => {
  const navigate = useNavigate();
  const createDashboard = useCreateDashboard();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<DashboardFormData>({
    resolver: zodResolver(dashboardSchema),
  });

  const onSubmit = (data: DashboardFormData) => {
    createDashboard.mutate(data);
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Create Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Create a new blank dashboard that you can customize
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <Input
            label="Dashboard Name"
            placeholder="Q4 Sales Dashboard"
            error={errors.name?.message}
            {...register('name')}
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              rows={4}
              placeholder="Optional description for your dashboard..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              {...register('description')}
            />
            {errors.description && (
              <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
            )}
          </div>

          <div className="flex items-center gap-3">
            <Button
              type="submit"
              isLoading={createDashboard.isPending}
            >
              Create Dashboard
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/dashboards')}
            >
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};