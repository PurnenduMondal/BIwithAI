from typing import Dict, List, Any
import pandas as pd
import logging

from app.services.data_ingestion.schema_detector import SchemaDetector
from app.services.ai.insight_generator import InsightGenerator

logger = logging.getLogger(__name__)

class DashboardGenerator:
    """Automatically generates dashboard layouts and widgets"""
    
    def __init__(self):
        self.schema_detector = SchemaDetector()
        self.insight_generator = InsightGenerator()
    
    async def generate_dashboard(
        self, 
        df: pd.DataFrame, 
        preferences: Dict = None
    ) -> Dict:
        """Generate complete dashboard configuration from data"""
        
        if preferences is None:
            preferences = {}
        
        # Analyze data
        schema = self.schema_detector.detect_schema(df)
        insights = await self.insight_generator.generate_insights(df, schema)
        
        # Generate widgets
        widgets = await self._create_widgets(df, schema, insights)
        
        # Create layout
        layout = self._create_layout(widgets, preferences)
        
        # Generate filters
        filters = self._create_filters(schema)
        
        return {
            'name': self._generate_dashboard_name(schema),
            'description': self._generate_description(schema, insights),
            'layout_config': layout,
            'widgets': widgets,
            'filters': filters,
            'theme': self._select_theme(preferences)
        }
    
    async def _create_widgets(
        self, 
        df: pd.DataFrame, 
        schema: Dict, 
        insights: List[Dict]
    ) -> List[Dict]:
        """Create widget configurations"""
        widgets = []
        
        # Priority 1: Summary KPI Cards (top 4 metrics)
        metrics = list(schema.get('metrics', {}).items())[:4]
        for idx, (metric_name, metric_info) in enumerate(metrics):
            widgets.append({
                'type': 'metric_card',
                'title': self._humanize_column_name(metric_name),
                'config': {
                    'metric': metric_name,
                    'aggregation': self._infer_aggregation(metric_name),
                    'format': self._infer_format(metric_name),
                    'comparison': 'previous_period' if schema.get('time_column') else None,
                    'show_sparkline': True
                },
                'position': {
                    'x': (idx % 4) * 3,
                    'y': 0,
                    'w': 3,
                    'h': 4
                },
                'priority': 1
            })
        
        # Priority 2: Time series charts
        if schema.get('time_column'):
            time_col = schema['time_column']
            y_position = 4
            
            for idx, metric_name in enumerate(list(schema.get('metrics', {}).keys())[:3]):
                if metric_name == time_col:
                    continue
                
                widgets.append({
                    'type': 'chart',
                    'chart_type': 'line',
                    'title': f'{self._humanize_column_name(metric_name)} Over Time',
                    'config': {
                        'x_axis': time_col,
                        'y_axis': metric_name,
                        'aggregation': self._infer_aggregation(metric_name),
                        'show_trend_line': True,
                        'show_data_labels': False
                    },
                    'position': {
                        'x': 0,
                        'y': y_position,
                        'w': 12,
                        'h': 8
                    },
                    'priority': 2
                })
                y_position += 8
        
        # Priority 3: Categorical breakdowns
        categorical_dims = [
            col for col, info in schema.get('dimensions', {}).items() 
            if info.get('cardinality') == 'low' and info.get('unique_count', 0) <= 20
        ][:2]
        
        current_y = widgets[-1]['position']['y'] + widgets[-1]['position']['h'] if widgets else 0
        
        for idx, dim in enumerate(categorical_dims):
            metric = list(schema.get('metrics', {}).keys())[0] if schema.get('metrics') else None
            
            if metric:
                widgets.append({
                    'type': 'chart',
                    'chart_type': 'bar',
                    'title': f'{self._humanize_column_name(metric)} by {self._humanize_column_name(dim)}',
                    'config': {
                        'x_axis': dim,
                        'y_axis': metric,
                        'aggregation': 'sum',
                        'sort': 'descending',
                        'limit': 10,
                        'show_data_labels': True
                    },
                    'position': {
                        'x': (idx % 2) * 6,
                        'y': current_y + (idx // 2) * 8,
                        'w': 6,
                        'h': 8
                    },
                    'priority': 3
                })
        
        # Priority 4: Correlation heatmap (if multiple metrics)
        if len(schema.get('metrics', {})) >= 3:
            current_y = widgets[-1]['position']['y'] + widgets[-1]['position']['h']
            
            widgets.append({
                'type': 'chart',
                'chart_type': 'heatmap',
                'title': 'Metric Correlations',
                'config': {
                    'metrics': list(schema.get('metrics', {}).keys())[:6],
                    'method': 'pearson'
                },
                'position': {
                    'x': 0,
                    'y': current_y,
                    'w': 6,
                    'h': 8
                },
                'priority': 4
            })
        
        # Priority 5: AI Insights Panel
        if insights:
            # Find position after last widget
            max_y = max([w['position']['y'] + w['position']['h'] for w in widgets])
            
            widgets.append({
                'type': 'insights_panel',
                'title': 'AI-Generated Insights',
                'config': {
                    'insights': insights[:5],
                    'auto_refresh': True,
                    'show_confidence': True
                },
                'position': {
                    'x': 6,
                    'y': current_y if len(schema.get('metrics', {})) >= 3 else max_y,
                    'w': 6,
                    'h': 8
                },
                'priority': 5
            })
        
        # Priority 6: Data Table
        max_y = max([w['position']['y'] + w['position']['h'] for w in widgets])
        
        widgets.append({
            'type': 'table',
            'title': 'Data Details',
            'config': {
                'columns': list(df.columns)[:10],
                'page_size': 10,
                'sortable': True,
                'filterable': True,
                'show_search': True
            },
            'position': {
                'x': 0,
                'y': max_y,
                'w': 12,
                'h': 10
            },
            'priority': 6
        })
        
        return widgets
    
    def _create_layout(self, widgets: List[Dict], preferences: Dict) -> Dict:
        """Create responsive grid layout"""
        
        # Sort widgets by priority
        sorted_widgets = sorted(widgets, key=lambda x: x.get('priority', 99))
        
        layout = {
            'type': 'grid',
            'columns': 12,
            'row_height': 30,
            'gap': 16,
            'responsive_breakpoints': {
                'lg': 1200,
                'md': 996,
                'sm': 768,
                'xs': 480
            },
            'widgets': []
        }
        
        for widget in sorted_widgets:
            layout['widgets'].append({
                'id': widget.get('id'),
                'type': widget['type'],
                'position': widget['position']
            })
        
        return layout
    
    def _create_filters(self, schema: Dict) -> List[Dict]:
        """Generate global filters"""
        filters = []
        
        # Time filter
        if schema.get('time_column'):
            filters.append({
                'type': 'date_range',
                'column': schema['time_column'],
                'label': 'Date Range',
                'default': 'last_30_days',
                'options': [
                    'today',
                    'yesterday',
                    'last_7_days',
                    'last_30_days',
                    'last_90_days',
                    'last_year',
                    'custom'
                ]
            })
        
        # Categorical filters (top 3 low-cardinality dimensions)
        for dim_name, dim_info in schema.get('dimensions', {}).items():
            if len(filters) >= 5:  # Max 5 filters
                break
            
            if dim_info.get('cardinality') == 'low' and dim_info.get('unique_count', 0) < 50:
                filters.append({
                    'type': 'multi_select',
                    'column': dim_name,
                    'label': self._humanize_column_name(dim_name),
                    'options': list(dim_info.get('top_values', {}).keys()),
                    'allow_search': dim_info.get('unique_count', 0) > 10
                })
        
        return filters
    
    def _generate_dashboard_name(self, schema: Dict) -> str:
        """Generate descriptive dashboard name based on data"""
        metric_names = [m.lower() for m in schema.get('metrics', {}).keys()]
        
        # Try to infer business domain
        if any('sales' in m or 'revenue' in m for m in metric_names):
            return "Sales Performance Dashboard"
        elif any('customer' in m or 'user' in m for m in metric_names):
            return "Customer Analytics Dashboard"
        elif any('marketing' in m or 'campaign' in m for m in metric_names):
            return "Marketing Dashboard"
        elif any('product' in m or 'inventory' in m for m in metric_names):
            return "Product Analytics Dashboard"
        else:
            return "Business Intelligence Dashboard"
    
    def _generate_description(self, schema: Dict, insights: List[Dict]) -> str:
        """Generate dashboard description"""
        desc_parts = []
        
        desc_parts.append(f"Analyzing {schema['row_count']:,} records")
        
        if schema.get('time_column'):
            time_period = schema.get('time_period', {})
            if time_period:
                desc_parts.append(
                    f"from {time_period.get('start', '')} to {time_period.get('end', '')}"
                )
        
        if insights:
            desc_parts.append(f"with {len(insights)} AI-generated insights")
        
        return ". ".join(desc_parts) + "."
    
    def _humanize_column_name(self, col_name: str) -> str:
        """Convert column name to human-readable format"""
        # Replace underscores and hyphens with spaces
        humanized = col_name.replace('_', ' ').replace('-', ' ')
        
        # Title case
        humanized = humanized.title()
        
        # Handle common abbreviations
        replacements = {
            'Id': 'ID',
            'Url': 'URL',
            'Api': 'API',
            'Qty': 'Quantity',
            'Amt': 'Amount',
            'Pct': 'Percent'
        }
        
        for old, new in replacements.items():
            humanized = humanized.replace(old, new)
        
        return humanized
    
    def _infer_aggregation(self, metric_name: str) -> str:
        """Infer appropriate aggregation for metric"""
        name_lower = metric_name.lower()
        
        if 'total' in name_lower or 'sum' in name_lower:
            return 'sum'
        elif 'average' in name_lower or 'avg' in name_lower or 'mean' in name_lower:
            return 'avg'
        elif 'count' in name_lower or 'number' in name_lower:
            return 'count'
        elif 'max' in name_lower or 'highest' in name_lower:
            return 'max'
        elif 'min' in name_lower or 'lowest' in name_lower:
            return 'min'
        else:
            # Default based on common patterns
            if any(kw in name_lower for kw in ['revenue', 'sales', 'amount', 'price']):
                return 'sum'
            else:
                return 'avg'
    
    def _infer_format(self, metric_name: str) -> str:
        """Infer number format from metric name"""
        name_lower = metric_name.lower()
        
        if any(kw in name_lower for kw in ['revenue', 'sales', 'price', 'cost', 'amount', 'value']):
            return 'currency'
        elif any(kw in name_lower for kw in ['percent', 'rate', 'ratio', '%']):
            return 'percentage'
        else:
            return 'number'
    
    def _select_theme(self, preferences: Dict) -> Dict:
        """Select dashboard theme"""
        default_theme = {
            'primary_color': '#1976d2',
            'secondary_color': '#dc004e',
            'success_color': '#4caf50',
            'warning_color': '#ff9800',
            'error_color': '#f44336',
            'background': '#f5f5f5',
            'surface': '#ffffff',
            'text_primary': '#212121',
            'text_secondary': '#757575',
            'font_family': '"Roboto", "Helvetica", "Arial", sans-serif',
            'border_radius': '8px',
            'spacing': 8
        }
        
        # Override with user preferences
        return {**default_theme, **preferences.get('theme', {})}