import { useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { useDataSources } from '../../hooks/useDataSource';
import type { CreateWidgetData } from '../../api/widgets';

interface CreateWidgetModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (widgetData: CreateWidgetData) => void;
  isLoading?: boolean;
}

export const CreateWidgetModal = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading = false,
}: CreateWidgetModalProps) => {
  const { data: dataSources } = useDataSources();
  const [formData, setFormData] = useState<Partial<CreateWidgetData>>({
    widget_type: 'bar',
    title: '',
    position: { x: 0, y: 0, w: 4, h: 4 },
    query_config: {},
    chart_config: {},
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.title && formData.widget_type) {
      onSubmit(formData as CreateWidgetData);
      handleClose();
    }
  };

  const handleClose = () => {
    setFormData({
      widget_type: 'bar',
      title: '',
      position: { x: 0, y: 0, w: 4, h: 4 },
      query_config: {},
      chart_config: {},
    });
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Add Widget"
      footer={
        <>
          <Button variant="outline" onClick={handleClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isLoading || !formData.title}>
            {isLoading ? 'Creating...' : 'Create Widget'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Widget Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Title
          </label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter widget title"
            required
          />
        </div>

        {/* Widget Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Widget Type
          </label>
          <select
            value={formData.widget_type}
            onChange={(e) =>
              setFormData({
                ...formData,
                widget_type: e.target.value as CreateWidgetData['widget_type'],
              })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="bar">Bar Chart</option>
            <option value="line">Line Chart</option>
            <option value="pie">Pie Chart</option>
            <option value="area">Area Chart</option>
            <option value="scatter">Scatter Chart</option>
            <option value="heatmap">Heatmap</option>
            <option value="metric">Metric</option>
            <option value="table">Table</option>
            <option value="gauge">Gauge</option>
          </select>
        </div>

        {/* Data Source */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Data Source (Optional)
          </label>
          <select
            value={formData.data_source_id || ''}
            onChange={(e) =>
              setFormData({
                ...formData,
                data_source_id: e.target.value || undefined,
              })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">None</option>
            {dataSources?.map((ds) => (
              <option key={ds.id} value={ds.id}>
                {ds.name}
              </option>
            ))}
          </select>
        </div>

        {/* Size */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Width (1-12)
            </label>
            <input
              type="number"
              min="1"
              max="12"
              value={formData.position?.w}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  position: {
                    ...formData.position!,
                    w: parseInt(e.target.value),
                  },
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Height (1-20)
            </label>
            <input
              type="number"
              min="1"
              max="20"
              value={formData.position?.h}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  position: {
                    ...formData.position!,
                    h: parseInt(e.target.value),
                  },
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </form>
    </Modal>
  );
};
