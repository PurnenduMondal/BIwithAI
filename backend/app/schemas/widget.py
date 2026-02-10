from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime


class WidgetBase(BaseModel):
    """Base widget schema"""
    widget_type: str = Field(
        ...,
        pattern="^(line|bar|pie|area|scatter|heatmap|metric|table|gauge)$",
        description="Type of widget (specific chart type or metric/table/gauge)"
    )
    title: str = Field(..., min_length=1, max_length=255, description="Widget title")
    description: Optional[str] = Field(None, description="Widget description")
    position: Dict[str, Any] = Field(
        ...,
        description="Widget position and size {x, y, w, h}"
    )
    
    # Support both old and new formats
    config: Optional[Dict[str, Any]] = Field(
        None,
        description="Legacy: Single config object (will be split into query_config and chart_config)"
    )
    query_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Query configuration (filters, aggregations, date ranges)"
    )
    chart_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Chart-specific configuration (colors, axis labels, etc.)"
    )
    data_mapping: Optional[Dict[str, Any]] = Field(
        None,
        description="Mapping of data columns to chart elements"
    )
    
    data_source_id: Optional[UUID] = Field(None, description="Associated data source")
    
    # AI generation fields
    generated_by_ai: Optional[bool] = Field(False, description="Whether widget was AI-generated")
    generation_prompt: Optional[str] = Field(None, description="User prompt that generated this widget")
    ai_reasoning: Optional[str] = Field(None, description="AI's reasoning for chart selection")
    
    @model_validator(mode='before')
    @classmethod
    def ensure_configs(cls, data: Any) -> Any:
        """Convert old config format to new format if needed"""
        if not isinstance(data, dict):
            return data
        
        # If new format already provided, use it
        if data.get('query_config') is not None and data.get('chart_config') is not None:
            return data
        
        # If old config exists, split it
        legacy_config = data.get('config')
        if legacy_config:
            if data.get('query_config') is None:
                data['query_config'] = _extract_query_config(legacy_config)
            if data.get('chart_config') is None:
                data['chart_config'] = _extract_chart_config(legacy_config, data.get('widget_type', ''))
        
        # Set empty dicts if still None
        if data.get('query_config') is None:
            data['query_config'] = {}
        if data.get('chart_config') is None:
            data['chart_config'] = {}
        
        return data


def _extract_query_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract query-related config from legacy config"""
    query_fields = ['filters', 'aggregation', 'date_column', 'date_range', 
                   'comparison_period', 'limit', 'sort_by', 'group_by']
    return {k: v for k, v in config.items() if k in query_fields}


def _extract_chart_config(config: Dict[str, Any], widget_type: str) -> Dict[str, Any]:
    """Extract chart-related config from legacy config"""
    chart_fields = ['chart_type', 'x_axis', 'y_axis', 'colors', 'show_legend', 
                   'show_grid', 'format', 'columns', 'min_value', 'max_value']
    chart_config = {k: v for k, v in config.items() if k in chart_fields}
    
    # For legacy 'chart' type, use chart_type from config to determine actual type
    # For other types, use the widget_type
    if widget_type == 'chart' and 'chart_type' in config:
        chart_config['type'] = config['chart_type']
    
    return chart_config


class WidgetCreate(WidgetBase):
    """Schema for creating a widget"""
    pass


class WidgetUpdate(BaseModel):
    """Schema for updating a widget"""
    widget_type: Optional[str] = Field(None, pattern="^(line|bar|pie|area|scatter|heatmap|metric|table|gauge)$")
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    position: Optional[Dict[str, Any]] = None
    
    # Support both old and new formats
    config: Optional[Dict[str, Any]] = None
    query_config: Optional[Dict[str, Any]] = None
    chart_config: Optional[Dict[str, Any]] = None
    data_mapping: Optional[Dict[str, Any]] = None
    
    data_source_id: Optional[UUID] = None
    
    @model_validator(mode='before')
    @classmethod
    def ensure_configs(cls, data: Any) -> Any:
        """Convert old config format to new format if needed"""
        if not isinstance(data, dict):
            return data
        
        # Only convert if new format not provided but old format exists
        legacy_config = data.get('config')
        if legacy_config:
            if data.get('query_config') is None:
                data['query_config'] = _extract_query_config(legacy_config)
            if data.get('chart_config') is None:
                widget_type = data.get('widget_type', '')
                data['chart_config'] = _extract_chart_config(legacy_config, widget_type)
        
        return data


class WidgetResponse(BaseModel):
    """Schema for widget response"""
    id: UUID
    dashboard_id: UUID
    widget_type: str
    title: str
    description: Optional[str] = Field(default=None)
    position: Dict[str, Any]
    
    # New format only (removed legacy config field)
    query_config: Optional[Dict[str, Any]] = Field(default=None)
    chart_config: Optional[Dict[str, Any]] = Field(default=None)
    data_mapping: Optional[Dict[str, Any]] = Field(default=None)
    
    data_source_id: Optional[UUID] = Field(default=None)
    is_active: bool = Field(default=True)
    
    # AI generation fields
    generated_by_ai: bool = Field(default=False)
    generation_prompt: Optional[str] = Field(default=None)
    ai_reasoning: Optional[str] = Field(default=None)
    
    # Cache fields
    cache_duration_seconds: Optional[int] = Field(default=None)
    last_data_fetch: Optional[datetime] = Field(default=None)
    
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = Field(default=None)

    model_config = {"from_attributes": True}


class WidgetDataResponse(BaseModel):
    """Schema for widget data response"""
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Data rows")
    columns: List[str] = Field(default_factory=list, description="Column names")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata (row count, aggregations, etc.)"
    )

    model_config = {"from_attributes": True}
