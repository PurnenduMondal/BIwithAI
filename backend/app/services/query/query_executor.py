import pandas as pd
import json
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Execute queries and transformations on DataFrames based on widget configuration"""
    
    def __init__(self):
        pass
    
    async def execute_widget_query(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any],
        widget_type: str = 'table'
    ) -> Dict[str, Any]:
        """
        Execute query based on widget configuration
        
        Args:
            df: Source DataFrame
            config: Widget configuration containing query parameters
            widget_type: Type of widget (chart, metric, table, text, ai_insight)
            
        Returns:
            Dictionary with 'data', 'columns', and optional 'metadata'
        """
        try:
            result_df = df.copy()
            
            # Apply filters (common for all widget types)
            if 'filters' in config and config['filters']:
                result_df = self._apply_filters(result_df, config['filters'])
            
            # Define chart types
            chart_types = ['line', 'bar', 'pie', 'area', 'scatter', 'heatmap', 'chart']
            metric_types = ['metric', 'gauge']
            
            # Handle different widget types
            if widget_type in chart_types:
                return self._execute_chart_query(result_df, config, widget_type)
            elif widget_type in metric_types:
                return self._execute_metric_query(result_df, config)
            elif widget_type == 'table':
                return self._execute_table_query(result_df, config)
            elif widget_type == 'text':
                # Text widgets don't need data processing
                return {'data': [], 'columns': [], 'metadata': {}}
            elif widget_type == 'ai_insight':
                # AI insights might need full data or summary
                return self._execute_table_query(result_df, config)
            else:
                # Default to table-like behavior
                return self._execute_table_query(result_df, config)
            
        except Exception as e:
            logger.error(f"Error executing widget query: {str(e)}", exc_info=True)
            return {
                'data': [],
                'columns': [],
                'metadata': {'error': str(e)}
            }
    
    def _execute_chart_query(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any],
        widget_type: str = 'bar'
    ) -> Dict[str, Any]:
        """Execute query for chart widgets"""
        x_axis = config.get('x_axis')
        y_axis = config.get('y_axis')
        aggregation = config.get('aggregation', 'sum')
        # Use widget_type as chart_type (bar, line, pie, etc.)
        chart_type = widget_type if widget_type != 'chart' else config.get('chart_type', 'bar')
        
        if not x_axis or not y_axis:
            return {
                'data': [],
                'columns': [],
                'metadata': {'error': 'x_axis and y_axis are required for chart widgets'}
            }
        
        # Validate columns exist
        if x_axis not in df.columns or y_axis not in df.columns:
            return {
                'data': [],
                'columns': [],
                'metadata': {'error': f'Columns {x_axis} or {y_axis} not found in data'}
            }
        
        try:
            df = df.copy()
            
            # Check if x_axis is a date column and group by month
            try:
                # Try to convert to datetime
                test_date = pd.to_datetime(df[x_axis], errors='coerce')
                # If more than 50% of values are valid dates, treat as date column
                if test_date.notna().sum() / len(df) > 0.5:
                    # Convert to datetime and transform to year-month format (e.g., "2024-01")
                    df[x_axis] = pd.to_datetime(df[x_axis]).dt.to_period('M').astype(str)
                    logger.info(f"Detected date column, grouping by month")
            except Exception as e:
                logger.error(f"Error detecting date column: {str(e)}", exc_info=True)
                # Not a date column, continue as normal
                pass
            
            # Clean up x_axis values (remove leading/trailing whitespace from strings)
            if df[x_axis].dtype == 'object':
                df[x_axis] = df[x_axis].astype(str).str.strip()
            
            # Handle percentage aggregation separately
            if aggregation == 'percentage':
                # For percentage, first sum the values
                logger.info(f"Grouping by {x_axis}, calculating percentage of {y_axis}")
                result_df = df.groupby(x_axis, as_index=False).agg({y_axis: 'sum'})
                # Calculate percentage of total (keep as numeric for now)
                total = result_df[y_axis].sum()
                if total > 0:
                    result_df[y_axis] = (result_df[y_axis] / total) * 100
                else:
                    result_df[y_axis] = 0
            else:
                # Group by x_axis and aggregate y_axis
                logger.info(f"Grouping by {x_axis}, aggregating {y_axis} with {aggregation}")
                result_df = df.groupby(x_axis, as_index=False).agg({y_axis: aggregation})
            
            logger.info(f"After groupby: {len(result_df)} rows, columns: {result_df.columns.tolist()}")
            
            # For pie charts, take top N categories (do this before formatting)
            if chart_type == 'pie':
                result_df = result_df.nlargest(10, y_axis)
            else:
                # Sort by x_axis for better visualization
                try:
                    result_df = result_df.sort_values(by=x_axis)
                except:
                    # If sorting fails (e.g., mixed types), skip sorting
                    pass
            
            # Convert to JSON-safe format using pandas to_json() to handle NaN, Inf, and -Inf
            data = json.loads(result_df.to_json(orient='records', date_format='iso'))
            columns = result_df.columns.tolist()
            
            metadata = {
                'row_count': len(result_df),
                'chart_type': chart_type,
                'x_axis': x_axis,
                'y_axis': y_axis,
                'aggregation': aggregation
            }
            
            return {
                'data': data,
                'columns': columns,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error executing chart query: {str(e)}", exc_info=True)
            return {
                'data': [],
                'columns': [],
                'metadata': {'error': str(e)}
            }
    
    def _execute_metric_query(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute query for metric widgets"""
        metric_field = config.get('metric')
        aggregation = config.get('aggregation', 'sum')
        
        logger.info(f"Executing metric query: metric_field={metric_field}, aggregation={aggregation}, config={config}")
        logger.info(f"DataFrame columns: {df.columns.tolist()}")
        
        if not metric_field:
            logger.error("Metric field is missing from config")
            return {
                'value': 0,
                'error': 'metric field is required for metric widgets'
            }
        
        if metric_field not in df.columns:
            logger.error(f"Metric field '{metric_field}' not found in DataFrame columns: {df.columns.tolist()}")
            return {
                'value': 0,
                'error': f'Column {metric_field} not found in data'
            }
        

        # Helper function to calculate aggregation
        def calculate_value(data):
            if aggregation == 'sum':
                return data[metric_field].sum()
            elif aggregation == 'avg' or aggregation == 'mean':
                return data[metric_field].mean()
            elif aggregation == 'count':
                return data[metric_field].count()
            elif aggregation == 'min':
                return data[metric_field].min()
            elif aggregation == 'max':
                return data[metric_field].max()
            else:
                return data[metric_field].sum()
        
        # Calculate current value
        current_value = calculate_value(df)
        
        result = {
            'value': float(current_value) if pd.notna(current_value) else 0,
            'metric': metric_field,
            'aggregation': aggregation
        }
        
        logger.info(f"Metric query result: {result}")
        
        # Return simplified format for metric widgets
        return result
            

    
    def _execute_table_query(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute query for table widgets"""
        result_df = df.copy()
        
        # Apply limit
        limit = config.get('limit', 100)
        if limit:
            result_df = result_df.head(limit)
        
        # Select specific columns if specified
        if 'columns' in config and config['columns']:
            available_cols = [col for col in config['columns'] if col in result_df.columns]
            if available_cols:
                result_df = result_df[available_cols]
        
        # Convert to JSON-safe format using pandas to_json() to handle NaN, Inf, and -Inf
        data = json.loads(result_df.to_json(orient='records', date_format='iso'))
        columns = result_df.columns.tolist()
        
        metadata = {
            'row_count': len(result_df),
            'column_count': len(columns),
            'total_rows_before_limit': len(df)
        }
        
        return {
            'data': data,
            'columns': columns,
            'metadata': metadata
        }
    
    def _apply_filters(self, df: pd.DataFrame, filters: List[Dict[str, Any]]) -> pd.DataFrame:
        """Apply filters to DataFrame"""
        result_df = df.copy()
        
        for filter_config in filters:
            # Support both 'field' (from frontend) and 'column' (legacy)
            column = filter_config.get('field') or filter_config.get('column')
            operator = filter_config.get('operator')
            value = filter_config.get('value')
            
            if not column or column not in result_df.columns:
                continue
            
            try:
                if operator == 'equals':
                    result_df = result_df[result_df[column] == value]
                elif operator == 'not_equals':
                    result_df = result_df[result_df[column] != value]
                elif operator == 'greater_than':
                    result_df = result_df[result_df[column] > value]
                elif operator == 'less_than':
                    result_df = result_df[result_df[column] < value]
                elif operator == 'greater_equal':
                    result_df = result_df[result_df[column] >= value]
                elif operator == 'less_equal':
                    result_df = result_df[result_df[column] <= value]
                elif operator == 'contains':
                    result_df = result_df[result_df[column].astype(str).str.contains(str(value), na=False, case=False)]
                elif operator == 'starts_with':
                    result_df = result_df[result_df[column].astype(str).str.startswith(str(value), na=False)]
                elif operator == 'ends_with':
                    result_df = result_df[result_df[column].astype(str).str.endswith(str(value), na=False)]
                elif operator == 'in':
                    if isinstance(value, list):
                        result_df = result_df[result_df[column].isin(value)]
                elif operator == 'not_in':
                    if isinstance(value, list):
                        result_df = result_df[~result_df[column].isin(value)]
                elif operator == 'is_null':
                    result_df = result_df[result_df[column].isna()]
                elif operator == 'is_not_null':
                    result_df = result_df[result_df[column].notna()]
                    
            except Exception as e:
                logger.warning(f"Error applying filter on column {column}: {str(e)}")
                continue
        
        return result_df
