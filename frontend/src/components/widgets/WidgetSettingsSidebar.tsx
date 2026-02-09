import { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { type Widget } from '../../types';
import { useUpdateWidget, useCreateWidget } from '../../hooks/useWidget';
import { useDataSources } from '../../hooks/useDataSource';

interface WidgetSettingsSidebarProps {
  widget: Widget | null;
  dashboardId: string;
  isOpen: boolean;
  onClose: () => void;
}

export const WidgetSettingsSidebar = ({ widget, dashboardId, isOpen, onClose }: WidgetSettingsSidebarProps) => {
  const isNewWidget = !widget;
  const [widgetType, setWidgetType] = useState<string>(widget?.widget_type || 'chart');
  const [dataSourceId, setDataSourceId] = useState<string>(widget?.data_source_id || '');
  const [title, setTitle] = useState(widget?.title || '');
  const [config, setConfig] = useState(widget?.config || {});
  
  const { data: dataSources } = useDataSources();
  const createWidget = useCreateWidget(dashboardId);
  const updateWidget = useUpdateWidget(widget?.id || '');

  useEffect(() => {
    if (widget) {
      setWidgetType(widget.widget_type);
      setDataSourceId(widget.data_source_id || '');
      setTitle(widget.title);
      setConfig(widget.config || {});
    } else {
      setWidgetType('chart');
      setDataSourceId('');
      setTitle('');
      setConfig({});
    }
  }, [widget]);

  // Set default config values based on widget type
  useEffect(() => {
    if (isNewWidget) {
      if (widgetType === 'chart') {
        setConfig((prev: any) => ({
          ...prev,
          aggregation: prev.aggregation || 'sum',
          chart_type: prev.chart_type || 'bar',
        }));
      } else if (widgetType === 'metric') {
        setConfig((prev: any) => ({
          ...prev,
          aggregation: prev.aggregation || 'sum',
        }));
      } else if (widgetType === 'table') {
        setConfig((prev: any) => ({
          ...prev,
          limit: prev.limit || 100,
        }));
      }
    }
  }, [widgetType, isNewWidget]);

  const handleSave = () => {
    if (isNewWidget) {
      // Calculate position for new widget (place at bottom)
      const position = {
        x: 0,
        y: 1000, // Place at a high y value, will be adjusted by grid
        w: 4,
        h: 6,
      };
      
      createWidget.mutate({
        widget_type: widgetType as any,
        title,
        position,
        config,
        data_source_id: dataSourceId || undefined,
      });
    } else {
      updateWidget.mutate({ title, config });
    }
    onClose();
  };

  const handleConfigChange = (key: string, value: any) => {
    setConfig((prev: any) => ({ ...prev, [key]: value }));
  };

  const handleFilterChange = (index: number, field: string, value: any) => {
    const newFilters = [...(config.filters || [])];
    newFilters[index] = { ...newFilters[index], [field]: value };
    handleConfigChange('filters', newFilters);
  };

  const addFilter = () => {
    const newFilters = [...(config.filters || []), { field: '', operator: 'equals', value: '' }];
    handleConfigChange('filters', newFilters);
  };

  const removeFilter = (index: number) => {
    const newFilters = (config.filters || []).filter((_: any, i: number) => i !== index);
    handleConfigChange('filters', newFilters);
  };

  if (!isOpen) return null;

  // Get available columns from selected data source
  const selectedDataSource = dataSources?.find(ds => ds.id === (widget?.data_source_id || dataSourceId));
  const availableColumns = selectedDataSource?.schema_metadata?.columns?.map((col: any) => col.name) || [];

  return (
    <>
      {/* Overlay */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-30 z-40"
        onClick={onClose}
      />
      
      {/* Sidebar */}
      <div className="fixed right-0 top-0 h-full w-96 bg-white shadow-xl z-50 overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            {isNewWidget ? 'Create Widget' : 'Widget Settings'}
          </h2>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 rounded"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4 space-y-6">
          {/* Basic Settings */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Basic Settings</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Widget Type
                </label>
                <select
                  value={widgetType}
                  onChange={(e) => setWidgetType(e.target.value)}
                  disabled={!isNewWidget}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="chart">Chart</option>
                  <option value="metric">Metric</option>
                  <option value="table">Table</option>
                  <option value="text">Text</option>
                  <option value="ai_insight">AI Insight</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Data Source
                </label>
                <select
                  value={dataSourceId}
                  onChange={(e) => setDataSourceId(e.target.value)}
                  disabled={!isNewWidget}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select data source...</option>
                  {dataSources?.map((ds) => (
                    <option key={ds.id} value={ds.id}>
                      {ds.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Enter widget title"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Chart-specific Settings */}
          {widgetType === 'chart' && (
            <>
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Chart Configuration</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Chart Type
                    </label>
                    <select
                      value={config.chart_type || 'bar'}
                      onChange={(e) => handleConfigChange('chart_type', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="bar">Bar Chart</option>
                      <option value="line">Line Chart</option>
                      <option value="pie">Pie Chart</option>
                      <option value="area">Area Chart</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      X-Axis
                    </label>
                    <select
                      value={config.x_axis || ''}
                      onChange={(e) => handleConfigChange('x_axis', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select column...</option>
                      {availableColumns.map((col: string) => (
                        <option key={col} value={col}>
                          {col}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Y-Axis
                    </label>
                    <select
                      value={config.y_axis || ''}
                      onChange={(e) => handleConfigChange('y_axis', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select column...</option>
                      {availableColumns.map((col: string) => (
                        <option key={col} value={col}>
                          {col}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Aggregation
                    </label>
                    <select
                      value={config.aggregation || 'sum'}
                      onChange={(e) => handleConfigChange('aggregation', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="sum">Sum</option>
                      <option value="avg">Average</option>
                      <option value="count">Count</option>
                      <option value="min">Minimum</option>
                      <option value="max">Maximum</option>
                      <option value="percentage">Percentage</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Filters */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-gray-900">Filters</h3>
                  <button
                    onClick={addFilter}
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                  >
                    + Add Filter
                  </button>
                </div>
                <div className="space-y-3">
                  {(config.filters || []).map((filter: any, index: number) => (
                    <div key={index} className="border border-gray-200 rounded-md p-3 space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-medium text-gray-600">Filter {index + 1}</span>
                        <button
                          onClick={() => removeFilter(index)}
                          className="text-xs text-red-600 hover:text-red-700"
                        >
                          Remove
                        </button>
                      </div>
                      <select
                        value={filter.field || ''}
                        onChange={(e) => handleFilterChange(index, 'field', e.target.value)}
                        className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value="">Select field...</option>
                        {availableColumns.map((col: string) => (
                          <option key={col} value={col}>
                            {col}
                          </option>
                        ))}
                      </select>
                      <select
                        value={filter.operator || 'equals'}
                        onChange={(e) => handleFilterChange(index, 'operator', e.target.value)}
                        className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value="equals">Equals</option>
                        <option value="not_equals">Not Equals</option>
                        <option value="greater_than">Greater Than</option>
                        <option value="less_than">Less Than</option>
                        <option value="contains">Contains</option>
                      </select>
                      <input
                        type="text"
                        value={filter.value || ''}
                        onChange={(e) => handleFilterChange(index, 'value', e.target.value)}
                        placeholder="Value"
                        className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Metric-specific Settings */}
          {widgetType === 'metric' && (
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Metric Configuration</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Metric Field
                  </label>
                  <select
                    value={config.metric || ''}
                    onChange={(e) => handleConfigChange('metric', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select column...</option>
                    {availableColumns.map((col: string) => (
                      <option key={col} value={col}>
                        {col}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Aggregation
                  </label>
                  <select
                    value={config.aggregation || 'sum'}
                    onChange={(e) => handleConfigChange('aggregation', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="sum">Sum</option>
                    <option value="avg">Average</option>
                    <option value="count">Count</option>
                    <option value="min">Minimum</option>
                    <option value="max">Maximum</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date Column (Optional)
                  </label>
                  <select
                    value={config.date_column || ''}
                    onChange={(e) => handleConfigChange('date_column', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">None</option>
                    {availableColumns.map((col: string) => (
                      <option key={col} value={col}>
                        {col}
                      </option>
                    ))}
                  </select>
                  <p className="mt-1 text-xs text-gray-500">
                    Required for period comparison
                  </p>
                </div>

                {config.date_column && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Compare With
                    </label>
                    <select
                      value={config.comparison_period || ''}
                      onChange={(e) => handleConfigChange('comparison_period', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">No Comparison</option>
                      <option value="previous_week">Previous Week</option>
                      <option value="previous_month">Previous Month</option>
                      <option value="previous_quarter">Previous Quarter</option>
                      <option value="previous_year">Previous Year</option>
                    </select>
                    <p className="mt-1 text-xs text-gray-500">
                      Shows trend vs selected period
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Table-specific Settings */}
          {widgetType === 'table' && (
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Table Configuration</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Columns (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={(config.columns || []).join(', ')}
                    onChange={(e) => handleConfigChange('columns', e.target.value.split(',').map(s => s.trim()))}
                    placeholder="e.g., name, email, status"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Rows Limit
                  </label>
                  <input
                    type="number"
                    value={config.limit || 100}
                    onChange={(e) => handleConfigChange('limit', Number.parseInt(e.target.value, 10))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!title || (isNewWidget && !dataSourceId)}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isNewWidget ? 'Create Widget' : 'Save Changes'}
          </button>
        </div>
      </div>
    </>
  );
};
