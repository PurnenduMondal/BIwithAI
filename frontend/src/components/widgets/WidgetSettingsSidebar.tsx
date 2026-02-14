import { useState, useEffect, useRef } from 'react';
import { XMarkIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import { type Widget } from '../../types';
import { useUpdateWidget, useCreateWidget, useWidgets } from '../../hooks/useWidget';
import { useDataSources } from '../../hooks/useDataSource';

// Custom Dropdown Component for Column Selection
interface ColumnDropdownProps {
  value: string;
  onChange: (value: string) => void;
  options: Array<{ name: string; semantic_type: string; unique_count: number }>;
  placeholder?: string;
  className?: string;
  size?: 'sm' | 'md';
}

const ColumnDropdown = ({ value, onChange, options, placeholder = 'Select column...', className = '', size = 'md' }: ColumnDropdownProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const selectedOption = options.find(opt => opt.name === value);
  const buttonSizeClasses = size === 'sm' ? 'px-2 py-1.5 text-xs' : 'px-3 py-2 text-sm';
  const optionSizeClasses = size === 'sm' ? 'px-2 py-1.5 text-xs' : 'px-3 py-2 text-sm';

  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full ${buttonSizeClasses} border border-gray-300 rounded-md bg-white text-left focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center justify-between`}
      >
        <span className="truncate">
          {selectedOption ? selectedOption.name : placeholder}
        </span>
        <ChevronDownIcon className={`w-4 h-4 text-gray-400 flex-shrink-0 ml-2 transition-transform ${isOpen ? 'transform rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute z-50 w-full bottom-full mb-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto" role="listbox">
          <div
            role="option"
            aria-selected={!value}
            className={`${optionSizeClasses} text-gray-500 cursor-default hover:bg-gray-50`}
            onClick={() => {
              onChange('');
              setIsOpen(false);
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                onChange('');
                setIsOpen(false);
              }
            }}
            tabIndex={0}
          >
            {placeholder}
          </div>
          {options.map((option) => (
            <div
              key={option.name}
              role="option"
              aria-selected={value === option.name}
              onClick={() => {
                onChange(option.name);
                setIsOpen(false);
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  onChange(option.name);
                  setIsOpen(false);
                }
              }}
              tabIndex={0}
              className={`${optionSizeClasses} cursor-pointer hover:bg-blue-50 flex items-center justify-between gap-3 ${
                value === option.name ? 'bg-blue-100' : ''
              }`}
            >
              <span className="font-medium truncate">{option.name} ({option.unique_count})</span>
              <span className="text-gray-500 text-xs flex-shrink-0">{option.semantic_type}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

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
  const { data: existingWidgets } = useWidgets(dashboardId);
  const createWidget = useCreateWidget(dashboardId);
  const updateWidget = useUpdateWidget(widget?.id || '');

  // Function to find first available position in grid
  const findAvailablePosition = () => {
    const GRID_COLS = 12;
    const newWidgetWidth = 4;
    const newWidgetHeight = 6;
    
    if (!existingWidgets || existingWidgets.length === 0) {
      return { x: 0, y: 0, w: newWidgetWidth, h: newWidgetHeight };
    }

    // Create a map of occupied positions
    const occupiedCells = new Set<string>();
    existingWidgets.forEach((w) => {
      for (let y = w.position.y; y < w.position.y + w.position.h; y++) {
        for (let x = w.position.x; x < w.position.x + w.position.w; x++) {
          occupiedCells.add(`${x},${y}`);
        }
      }
    });

    // Find the first available position row by row
    const maxY = Math.max(...existingWidgets.map(w => w.position.y + w.position.h), 0);
    for (let y = 0; y <= maxY + 10; y++) {
      for (let x = 0; x <= GRID_COLS - newWidgetWidth; x++) {
        // Check if this position has enough space
        let canFit = true;
        for (let dy = 0; dy < newWidgetHeight && canFit; dy++) {
          for (let dx = 0; dx < newWidgetWidth && canFit; dx++) {
            if (occupiedCells.has(`${x + dx},${y + dy}`)) {
              canFit = false;
            }
          }
        }
        
        if (canFit) {
          return { x, y, w: newWidgetWidth, h: newWidgetHeight };
        }
      }
    }

    // Fallback: place at bottom
    return { x: 0, y: maxY, w: newWidgetWidth, h: newWidgetHeight };
  };

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
        setConfig((prev: any) => {
          // Only update if aggregation is not already set
          if (!prev.aggregation) {
            return { ...prev, aggregation: 'sum' };
          }
          return prev;
        });
      } else if (widgetType === 'table') {
        setConfig((prev: any) => {
          // Only update if limit is not already set
          if (!prev.limit) {
            return { ...prev, limit: 100 };
          }
          return prev;
        });
      }
    }
  }, [widgetType, isNewWidget]);

  const handleSave = () => {
    // Split config into query_config and chart_config
    const queryFields = ['filters', 'aggregation', 'date_column', 'date_range', 
                         'comparison_period', 'limit', 'sort_by', 'group_by', 'metric'];
    const chartFields = ['chart_type', 'x_axis', 'y_axis', 'colors', 'show_legend', 
                        'show_grid', 'format', 'columns', 'min_value', 'max_value', 
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
      // Calculate position for new widget using smart positioning
      const position = findAvailablePosition();
      
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
  const availableColumns = selectedDataSource?.schema_metadata?.columns || [];
  
  // Filter columns by semantic type
  const metricTypes = ['numeric', 'integer', 'float', 'number', 'continuous', 'metric'];
  const categoricalTypes = ['categorical', 'text', 'string', 'date', 'datetime', 'date_time', 'boolean', 'ordinal', 'nominal'];
  
  const metricColumns = availableColumns.filter((col: any) => 
    metricTypes.includes(col.semantic_type?.toLowerCase())
  );
  
  const categoricalColumns = availableColumns.filter((col: any) => 
    categoricalTypes.includes(col.semantic_type?.toLowerCase())
  );

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
                    <ColumnDropdown
                      value={config.x_axis || ''}
                      onChange={(value) => handleConfigChange('x_axis', value)}
                      options={categoricalColumns}
                      placeholder="Select column..."
                      size="md"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Y-Axis
                    </label>
                    <ColumnDropdown
                      value={config.y_axis || ''}
                      onChange={(value) => handleConfigChange('y_axis', value)}
                      options={metricColumns}
                      placeholder="Select column..."
                      size="md"
                    />
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
                      <ColumnDropdown
                        value={filter.field || ''}
                        onChange={(value) => handleFilterChange(index, 'field', value)}
                        options={availableColumns}
                        placeholder="Select field..."
                        size="sm"
                      />
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
                  <ColumnDropdown
                    value={config.metric || ''}
                    onChange={(value) => handleConfigChange('metric', value)}
                    options={metricColumns}
                    placeholder="Select column..."
                    size="md"
                  />
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
