import pandas as pd
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
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute query based on widget configuration
        
        Args:
            df: Source DataFrame
            config: Widget configuration containing query parameters
            
        Returns:
            Dictionary with 'data', 'columns', and optional 'metadata'
        """
        try:
            result_df = df.copy()
            
            # Apply filters
            if 'filters' in config and config['filters']:
                result_df = self._apply_filters(result_df, config['filters'])
            
            # Apply grouping and aggregations
            if 'groupBy' in config and config['groupBy']:
                result_df = self._apply_grouping(result_df, config)
            
            # Apply sorting
            if 'sortBy' in config and config['sortBy']:
                result_df = self._apply_sorting(result_df, config['sortBy'])
            
            # Apply limit
            limit = config.get('limit', 1000)
            if limit:
                result_df = result_df.head(limit)
            
            # Select specific columns if specified
            if 'columns' in config and config['columns']:
                available_cols = [col for col in config['columns'] if col in result_df.columns]
                if available_cols:
                    result_df = result_df[available_cols]
            
            # Convert to response format
            data = result_df.to_dict('records')
            columns = result_df.columns.tolist()
            
            metadata = {
                'row_count': len(result_df),
                'column_count': len(columns),
                'total_rows_before_limit': len(df)
            }
            
            # Add aggregation metadata if applicable
            if 'aggregations' in config and config['aggregations']:
                metadata['aggregations'] = config['aggregations']
            
            return {
                'data': data,
                'columns': columns,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error executing widget query: {str(e)}", exc_info=True)
            return {
                'data': [],
                'columns': [],
                'metadata': {'error': str(e)}
            }
    
    def _apply_filters(self, df: pd.DataFrame, filters: List[Dict[str, Any]]) -> pd.DataFrame:
        """Apply filters to DataFrame"""
        result_df = df.copy()
        
        for filter_config in filters:
            column = filter_config.get('column')
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
                    result_df = result_df[result_df[column].astype(str).str.contains(str(value), na=False)]
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
    
    def _apply_grouping(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Apply grouping and aggregations"""
        group_by = config.get('groupBy', [])
        aggregations = config.get('aggregations', {})
        
        if not group_by or not aggregations:
            return df
        
        try:
            # Validate group by columns exist
            valid_group_cols = [col for col in group_by if col in df.columns]
            if not valid_group_cols:
                return df
            
            # Build aggregation dictionary
            agg_dict = {}
            for col, agg_func in aggregations.items():
                if col in df.columns:
                    if agg_func == 'count':
                        agg_dict[col] = 'count'
                    elif agg_func == 'sum':
                        agg_dict[col] = 'sum'
                    elif agg_func == 'avg' or agg_func == 'mean':
                        agg_dict[col] = 'mean'
                    elif agg_func == 'min':
                        agg_dict[col] = 'min'
                    elif agg_func == 'max':
                        agg_dict[col] = 'max'
                    elif agg_func == 'std':
                        agg_dict[col] = 'std'
                    elif agg_func == 'median':
                        agg_dict[col] = 'median'
            
            if not agg_dict:
                return df
            
            # Perform grouping and aggregation
            grouped_df = df.groupby(valid_group_cols).agg(agg_dict).reset_index()
            
            return grouped_df
            
        except Exception as e:
            logger.error(f"Error applying grouping: {str(e)}")
            return df
    
    def _apply_sorting(self, df: pd.DataFrame, sort_config: Dict[str, Any]) -> pd.DataFrame:
        """Apply sorting to DataFrame"""
        try:
            column = sort_config.get('column')
            order = sort_config.get('order', 'asc')
            
            if not column or column not in df.columns:
                return df
            
            ascending = (order.lower() == 'asc')
            return df.sort_values(by=column, ascending=ascending)
            
        except Exception as e:
            logger.error(f"Error applying sorting: {str(e)}")
            return df
