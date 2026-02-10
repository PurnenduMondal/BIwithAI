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
  onSave?: () => void;
}

export const WidgetSettingsSidebar = ({ widget, dashboardId, isOpen, onClose, onSave }: WidgetSettingsSidebarProps) => {
  const isNewWidget = !widget;
  const [widgetType, setWidgetType] = useState<string>(widget?.widget_type || 'bar');
  const [dataSourceId, setDataSourceId] = useState<string>(widget?.data_source_id || '');
  const [title, setTitle] = useState(widget?.title || '');
  
  // Merge query_config and chart_config into single config for editing
  const [config, setConfig] = useState(() => {
    if (!widget) return {};
    return {
      ...widget.query_config,
      ...widget.chart_config,
    };
  });
  
  // AI generation info (read-only)
  const isAIGenerated = widget?.generated_by_ai || false;
  const aiReasoning = widget?.ai_reasoning || null;
  const generationPrompt = widget?.generation_prompt || null;
  
  const { data: dataSources } = useDataSources();
  const createWidget = useCreateWidget(dashboardId);
  const updateWidget = useUpdateWidget(widget?.id || '');

  useEffect(() => {
    if (widget) {
      setWidgetType(widget.widget_type);
      setDataSourceId(widget.data_source_id || '');
      setTitle(widget.title);
      // Merge query_config and chart_config for editing
      setConfig({
        ...widget.query_config,
        ...widget.chart_config,
      });
    } else {
      setWidgetType('bar');
      setDataSourceId('');
      setTitle('');
      setConfig({});
    }
  }, [widget]);

  // Set default config values based on widget type
  useEffect(() => {
    if (isNewWidget) {
      const chartTypes = ['line', 'bar', 'pie', 'area', 'scatter', 'heatmap'];
      if (chartTypes.includes(widgetType) || widgetType === 'metric' || widgetType === 'gauge') {
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
    // Split config into query_config and chart_config
    const queryFields = ['filters', 'aggregation', 'date_column', 'date_range', 
                         'comparison_period', 'limit', 'sort_by', 'group_by'];
    const chartFields = ['chart_type', 'x_axis', 'y_axis', 'colors', 'show_legend', 
                        'show_grid', 'format', 'columns', 'min_value', 'max_value', 'metric', 
                        'prefix', 'suffix'];
    
    const query_config: any = {};
    const chart_config: any = {};
    
    Object.entries(config).forEach(([key, value]) => {
      if (queryFields.includes(key)) {
        query_config[key] = value;
      } else if (chartFields.includes(key)) {
        chart_config[key] = value;
      }
    });
    
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
        query_config,
        chart_config,
        data_source_id: dataSourceId || undefined,
      }, {
        onSuccess: () => {
          if (onSave) onSave();
        }
      });
    } else {
      updateWidget.mutate({ 
        widget_type: widgetType as any,
        title, 
        query_config,
        chart_config 
      }, {
        onSuccess: () => {
          if (onSave) onSave();
        }
      });
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
          {/* AI Generation Info (Read-only) */}
          {isAIGenerated && (
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3 flex-1">
                  <h3 className="text-sm font-medium text-blue-800">AI-Generated Widget</h3>
                  {generationPrompt && (
                    <p className="mt-1 text-xs text-blue-700">
                      <span className="font-medium">Prompt:</span> {generationPrompt}
                    </p>
                  )}
                  {aiReasoning && (
                    <p className="mt-1 text-xs text-blue-700">
                      <span className="font-medium">AI Reasoning:</span> {aiReasoning}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

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
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <optgroup label="Charts">
                    <option value="bar">Bar Chart</option>
                    <option value="line">Line Chart</option>
                    <option value="pie">Pie Chart</option>
                    <option value="area">Area Chart</option>
                    <option value="scatter">Scatter Plot</option>
                    <option value="heatmap">Heatmap</option>
                  </optgroup>
                  <optgroup label="Metrics">
                    <option value="metric">Metric Card</option>
                    <option value="gauge">Gauge</option>
                  </optgroup>
                  <optgroup label="Other">
                    <option value="table">Table</option>
                  </optgroup>
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
          {['line', 'bar', 'pie', 'area', 'scatter', 'heatmap'].includes(widgetType) && (
            <>
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Chart Configuration</h3>
                <div className="space-y-4">

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

          {/* Metric and Gauge Settings */}
          {(widgetType === 'metric' || widgetType === 'gauge') && (
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
                    Prefix (optional)
                  </label>
                  <input
                    type="text"
                    value={config.prefix || ''}
                    onChange={(e) => handleConfigChange('prefix', e.target.value)}
                    placeholder="e.g., $, ₹, €"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">Add a prefix character like $, ₹, € before the value</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Suffix (optional)
                  </label>
                  <input
                    type="text"
                    value={config.suffix || ''}
                    onChange={(e) => handleConfigChange('suffix', e.target.value)}
                    placeholder="e.g., %, K, M"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">Add a suffix character like %, K, M after the value</p>
                </div>
                
                {/* Gauge-specific settings */}
                {widgetType === 'gauge' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Minimum Value
                      </label>
                      <input
                        type="number"
                        value={config.min_value || 0}
                        onChange={(e) => handleConfigChange('min_value', Number(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Maximum Value
                      </label>
                      <input
                        type="number"
                        value={config.max_value || 100}
                        onChange={(e) => handleConfigChange('max_value', Number(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </>
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
