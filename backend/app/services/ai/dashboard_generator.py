"""
AI-Powered Dashboard Generator using Claude
Generates intelligent dashboard layouts, chart selections, and configurations
"""
import logging
import json
from typing import Dict, List, Any, Optional
import pandas as pd
from anthropic import Anthropic

from app.config import settings

logger = logging.getLogger(__name__)


class DashboardGenerator:
    """Generates comprehensive dashboards from natural language using Claude"""
    
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        
    async def generate_dashboard_config(
        self,
        user_query: str,
        df: pd.DataFrame,
        schema: Dict[str, Any],
        intent: Optional[Dict] = None,
        conversation_context: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Generate complete dashboard configuration from user query"""
        
        # Prepare data summary
        data_summary = self._prepare_data_summary(df, schema)
        
        # Build prompt
        prompt = self._build_generation_prompt(
            user_query=user_query,
            data_summary=data_summary,
            intent=intent
        )
        
        # Get Claude's recommendation
        try:
            messages = []
            if conversation_context:
                for msg in conversation_context[-5:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self._get_system_prompt(),
                messages=messages
            )
            
            # Parse and validate response
            config = self._parse_response(response.content[0].text)
            config = await self._validate_config(config, df, schema)
            
            return config
            
        except Exception as e:
            logger.error(f"Dashboard generation failed: {e}")
            return self._generate_fallback_dashboard(df, schema, user_query)
    
    def _get_system_prompt(self) -> str:
        """System prompt for Claude"""
        return """You are an expert data visualization designer and business intelligence analyst.

Your role:
1. Analyze user intent and data structure
2. Recommend optimal chart types for insights
3. Create intuitive dashboard layouts
4. Provide actionable insights

Chart Types Available:
- line: Time series, trends
- bar: Comparisons, rankings
- pie: Proportions, distributions
- area: Cumulative trends
- scatter: Correlations, relationships
- metric: Single KPI values
- table: Detailed data views

Layout System:
- 12-column grid
- Each widget has {x, y, w, h} position
- In case of a pie chart h should greater or equal to 9, w should greater or equal to 3
- In case of a metric card h should greater or equal to 3, w should greater or equal to 3
- Arrange logically: metrics top, charts below
- sort_by, filters, and limit options for Optional
- aggregation is required for all charts except scatter and table

Response Format (strict JSON):
{
  "dashboard": {
    "name": "Dashboard Title",
    "description": "Brief description"
  },
  "widgets": [
    {
      "title": "Chart Title",
      "type": "line|bar|pie|area|metric|table",
      "query_config": {
        "aggregation": "sum|avg|count|min|max|percentage",
        "group_by": "category_column",
        "sort_by": "value_column",   
        "filters": [],
        "limit": 10
      },
      "chart_config": {
        "x_axis": "column_name",
        "y_axis": "column_name",
        "metric": "column_name_for_metric_type_chart_only",
        "prefix": "$ or ₹ or other prefix for metric widgets (optional)",
        "suffix": "percentage symbol or other suffix for metric widgets (optional)"
      },
      "position": {"x": 0, "y": 0, "w": 3, "h": 9},
      "reasoning": "Why this visualization"
    }
  ],
  "insights": [
    {
      "type": "trend|anomaly|comparison",
      "title": "Key Finding",
      "description": "Detailed insight",
      "severity": "high|medium|low"
    }
  ],
  "suggestions": ["Follow-up action 1", "Follow-up action 2"]
}

Guidelines:
- Start with 1-2 metric cards for KPIs
- Add 2-4 charts maximum (avoid clutter)
- Use appropriate aggregations
- Consider time dimension if available
- For metric widgets, add prefix (e.g., $, ₹, €) or suffix (e.g., %, K, M) based on the data type
- Provide actionable insights
- Return ONLY valid JSON"""
    
    def _build_generation_prompt(
        self,
        user_query: str,
        data_summary: Dict,
        intent: Optional[Dict]
    ) -> str:
        """Build prompt for dashboard generation"""
        
        prompt = f"""Create a dashboard for this request:

USER REQUEST: {user_query}

DATA INFORMATION:
- Total Rows: {data_summary['row_count']:,}
- Columns: {len(data_summary['columns'])}

AVAILABLE COLUMNS:
"""
        
        # Add numeric columns
        if data_summary['numeric_columns']:
            prompt += "\nNumeric (for metrics/aggregations):\n"
            for col in data_summary['numeric_columns'][:10]:
                stats = data_summary['statistics'].get(col, {})
                prompt += f"  - {col}: min={stats.get('min', 'N/A')}, max={stats.get('max', 'N/A')}, avg={stats.get('mean', 'N/A'):.2f}\n"
        
        # Add categorical columns
        if data_summary['categorical_columns']:
            prompt += "\nCategorical (for grouping/filtering):\n"
            for col in data_summary['categorical_columns'][:10]:
                unique_count = data_summary['categorical_stats'].get(col, {}).get('unique_count', 0)
                prompt += f"  - {col}: {unique_count} unique values\n"
        
        # Add date columns
        if data_summary['date_columns']:
            prompt += "\nDate/Time (for trends):\n"
            for col in data_summary['date_columns']:
                date_range = data_summary.get('date_range', {})
                prompt += f"  - {col}: from {date_range.get('start', 'N/A')} to {date_range.get('end', 'N/A')}\n"
        
        # Add sample data
        prompt += f"\nSAMPLE DATA (first 3 rows):\n{json.dumps(data_summary['sample_data'], indent=2)}\n"
        
        # Add intent if available
        if intent:
            prompt += f"\nDETECTED INTENT: {intent.get('type', 'unknown')}\n"
            if intent.get('parameters'):
                prompt += f"Parameters: {json.dumps(intent.get('parameters'))}\n"
        
        prompt += "\nGenerate the dashboard configuration as JSON:"
        
        return prompt
    
    def _prepare_data_summary(self, df: pd.DataFrame, schema: Dict) -> Dict[str, Any]:
        """Prepare concise data summary"""
        
        # Identify column types
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        
        # Statistics for numeric columns
        statistics = {}
        for col in numeric_cols[:10]:
            try:
                statistics[col] = {
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "std": float(df[col].std())
                }
            except:
                pass
        
        # Categorical column stats
        categorical_stats = {}
        for col in categorical_cols[:10]:
            try:
                categorical_stats[col] = {
                    "unique_count": int(df[col].nunique()),
                    "top_values": df[col].value_counts().head(3).to_dict()
                }
            except:
                pass
        
        # Date range
        date_range = None
        if date_cols:
            try:
                date_col = date_cols[0]
                date_range = {
                    "start": str(df[date_col].min()),
                    "end": str(df[date_col].max())
                }
            except:
                pass
        
        return {
            "row_count": len(df),
            "columns": df.columns.tolist(),
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "date_columns": date_cols,
            "statistics": statistics,
            "categorical_stats": categorical_stats,
            "date_range": date_range,
            "sample_data": df.head(3).fillna("").to_dict('records')
        }
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's JSON response"""
        try:
            # Extract JSON from markdown blocks
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            config = json.loads(response_text)
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response: {response_text[:500]}")
            raise ValueError("Invalid dashboard configuration from AI")
    
    async def _validate_config(
        self,
        config: Dict[str, Any],
        df: pd.DataFrame,
        schema: Dict
    ) -> Dict[str, Any]:
        """Validate and fix dashboard configuration"""
        
        valid_columns = set(df.columns)
        
        for widget in config.get('widgets', []):
            query_config = widget.get('query_config', {})
            chart_config = widget.get('chart_config', {})
            
            # Validate x_axis (now in chart_config)
            if 'x_axis' in chart_config and chart_config['x_axis'] not in valid_columns:
                logger.warning(f"Invalid x_axis: {chart_config['x_axis']}, using first column")
                chart_config['x_axis'] = df.columns[0]
            
            # Validate y_axis (now in chart_config)
            if 'y_axis' in chart_config:
                y_axes = chart_config['y_axis'] if isinstance(chart_config['y_axis'], list) else [chart_config['y_axis']]
                valid_y = [y for y in y_axes if y in valid_columns]
                if not valid_y:
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    valid_y = [numeric_cols[0]] if numeric_cols else [df.columns[0]]
                chart_config['y_axis'] = valid_y[0] if len(valid_y) == 1 else valid_y
            
            # Validate metric (now in chart_config)
            if 'metric' in chart_config and chart_config['metric'] not in valid_columns:
                logger.warning(f"Invalid metric: {chart_config['metric']}, using first numeric column")
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                chart_config['metric'] = numeric_cols[0] if numeric_cols else df.columns[0]
            
            # Validate group_by (in query_config)
            if 'group_by' in query_config and query_config['group_by'] not in valid_columns:
                logger.warning(f"Invalid group_by: {query_config['group_by']}, removing it")
                del query_config['group_by']
            
            # Ensure position exists
            if 'position' not in widget or not widget['position']:
                widget['position'] = self._auto_position(len(config['widgets']), config['widgets'].index(widget))
        
        return config
    
    def _auto_position(self, total: int, index: int) -> Dict[str, int]:
        """Auto-position widget in grid"""
        # First row: metrics (3 columns each)
        # Subsequent rows: 2-column layout for charts
        
        if total <= 4 and index < 4:
            # Small dashboard - 3 column layout
            col = index % 3
            row = index // 3
            return {"x": col * 4, "y": row * 3, "w": 4, "h": 3}
        else:
            # Larger dashboard - mix metrics and charts
            if index < 2:
                # Top metrics
                return {"x": index * 6, "y": 0, "w": 6, "h": 2}
            else:
                # Charts below
                chart_index = index - 2
                col = chart_index % 2
                row = 2 + (chart_index // 2) * 4
                return {"x": col * 6, "y": row, "w": 6, "h": 4}
    
    def _generate_fallback_dashboard(
        self,
        df: pd.DataFrame,
        schema: Dict,
        query: str
    ) -> Dict[str, Any]:
        """Generate basic dashboard when AI fails"""
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        
        widgets = []
        
        # Add metric cards for first 2 numeric columns
        for i, col in enumerate(numeric_cols[:2]):
            col_lower = col.lower()
            prefix = ''
            suffix = ''
            
            # Auto-detect prefix/suffix based on column name
            if any(keyword in col_lower for keyword in ['price', 'cost', 'revenue', 'amount', 'salary', 'payment']):
                prefix = '$'
            elif any(keyword in col_lower for keyword in ['percent', 'rate', 'ratio']):
                suffix = '%'
            elif any(keyword in col_lower for keyword in ['count', 'quantity', 'total']):
                suffix = ''
            
            chart_config = {
                "metric": col,
                "format": "number"
            }
            if prefix:
                chart_config["prefix"] = prefix
            if suffix:
                chart_config["suffix"] = suffix
                
            widgets.append({
                "title": col.replace('_', ' ').title(),
                "type": "metric",
                "query_config": {
                    "aggregation": "sum"
                },
                "chart_config": chart_config,
                "position": {"x": i * 6, "y": 0, "w": 6, "h": 9},
                "reasoning": "Key metric summary"
            })
        
        # Add trend line if date column exists
        if date_cols and numeric_cols:
            widgets.append({
                "title": f"{numeric_cols[0].replace('_', ' ').title()} Over Time",
                "type": "line",
                "query_config": {
                    "aggregation": "sum"
                },
                "chart_config": {
                    "x_axis": date_cols[0],
                    "y_axis": numeric_cols[0],
                    "show_grid": True,
                    "show_legend": False
                },
                "position": {"x": 0, "y": 9, "w": 12, "h": 9},
                "reasoning": "Trend analysis over time"
            })
        
        # Add bar chart
        if len(df.columns) >= 2:
            widgets.append({
                "title": "Top 10 by Value",
                "type": "bar",
                "query_config": {
                    "aggregation": "sum",
                    "limit": 10
                },
                "chart_config": {
                    "x_axis": df.columns[0],
                    "y_axis": numeric_cols[0] if numeric_cols else df.columns[1],
                    "show_grid": True
                },
                "position": {"x": 0, "y": 18, "w": 12, "h": 9},
                "reasoning": "Top performers comparison"
            })
        
        return {
            "dashboard": {
                "name": f"Dashboard: {query[:50]}",
                "description": "Auto-generated dashboard"
            },
            "widgets": widgets,
            "insights": [{
                "type": "summary",
                "title": "Dashboard Created",
                "description": f"Generated {len(widgets)} visualizations from your data",
                "severity": "low"
            }],
            "suggestions": [
                "Add filters to focus on specific data",
                "Customize chart colors and styles",
                "Export or share this dashboard"
            ]
        }
