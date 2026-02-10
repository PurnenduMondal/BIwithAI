from typing import Dict, List, Any
import numpy as np
import pandas as pd
from anthropic import Anthropic
import json
import logging
from datetime import datetime, timezone

from app.config import settings

logger = logging.getLogger(__name__)

class InsightGenerator:
    """Generates AI-powered insights from data using Claude"""
    
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
    
    async def generate_insights(
        self, 
        df: pd.DataFrame, 
        schema: Dict, 
        context: str = ""
    ) -> List[Dict]:
        """Generate comprehensive insights from dataset"""
        insights = []
        
        try:
            # Statistical insights
            insights.extend(self._statistical_insights(df, schema))
            
            # Trend analysis
            if schema.get('time_column'):
                insights.extend(self._trend_insights(df, schema))
            
            # Anomaly detection
            insights.extend(self._anomaly_insights(df, schema))
            
            # AI-generated narrative insights
            ai_insights = await self._narrative_insights(df, schema, context)
            insights.extend(ai_insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return []
    
    def _statistical_insights(self, df: pd.DataFrame, schema: Dict) -> List[Dict]:
        """Generate statistical insights"""
        insights = []
        
        for col_name, col_info in schema.get('metrics', {}).items():
            # Outlier detection
            if col_info.get('outliers', {}).get('percentage', 0) > 5:
                insights.append({
                    'type': 'anomaly',
                    'severity': 'medium',
                    'title': f'Outliers detected in {col_name}',
                    'description': f'{col_info["outliers"]["percentage"]:.1f}% of values are statistical outliers',
                    'column': col_name,
                    'confidence': 0.9,
                    'metadata': {
                        'outlier_count': col_info['outliers']['count'],
                        'total_count': len(df)
                    }
                })
            
            # Missing data
            if col_info.get('null_percentage', 0) > 10:
                insights.append({
                    'type': 'data_quality',
                    'severity': 'high' if col_info['null_percentage'] > 30 else 'medium',
                    'title': f'Significant missing data in {col_name}',
                    'description': f'{col_info["null_percentage"]:.1f}% of values are missing',
                    'column': col_name,
                    'confidence': 1.0,
                    'metadata': {
                        'null_count': col_info['null_count'],
                        'total_count': len(df)
                    }
                })
        
        return insights
    
    def _trend_insights(self, df: pd.DataFrame, schema: Dict) -> List[Dict]:
        """Analyze trends over time"""
        insights = []
        time_col = schema['time_column']
        
        if not time_col or time_col not in df.columns:
            return insights
        
        for metric_name in schema.get('metrics', {}).keys():
            if metric_name == time_col:
                continue
            
            try:
                # Sort by time
                df_sorted = df.sort_values(time_col)
                values = df_sorted[metric_name].dropna().values
                
                if len(values) < 3:
                    continue
                
                # Simple linear trend
                from scipy import stats
                x = range(len(values))
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
                
                # Strong correlation indicates trend
                if abs(r_value) > 0.7 and p_value < 0.05:
                    trend_direction = 'increasing' if slope > 0 else 'decreasing'
                    
                    # Calculate percentage change
                    pct_change = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
                    
                    insights.append({
                        'type': 'trend',
                        'severity': 'info',
                        'title': f'{metric_name} is {trend_direction}',
                        'description': f'Strong {trend_direction} trend detected over time (R² = {r_value**2:.2f}). '
                                     f'Changed by {abs(pct_change):.1f}% from start to end.',
                        'column': metric_name,
                        'confidence': abs(r_value),
                        'metadata': {
                            'slope': float(slope),
                            'r_squared': float(r_value**2),
                            'p_value': float(p_value),
                            'percentage_change': float(pct_change),
                            'direction': trend_direction
                        }
                    })
            
            except Exception as e:
                logger.warning(f"Error analyzing trend for {metric_name}: {str(e)}")
                continue
        
        return insights
    
    def _anomaly_insights(self, df: pd.DataFrame, schema: Dict) -> List[Dict]:
        """Detect anomalies using statistical methods"""
        insights = []
        
        try:
            # Get numeric columns
            numeric_cols = [
                col for col in df.select_dtypes(include=[np.number]).columns
                if col in schema.get('metrics', {})
            ]
            
            if len(numeric_cols) < 2:
                return insights
            
            # Prepare data
            X = df[numeric_cols].fillna(df[numeric_cols].mean())
            
            # Use Isolation Forest for multivariate anomaly detection
            from sklearn.ensemble import IsolationForest
            
            iso_forest = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            anomalies = iso_forest.fit_predict(X)
            
            anomaly_count = (anomalies == -1).sum()
            
            if anomaly_count > 0:
                anomaly_pct = (anomaly_count / len(df)) * 100
                
                insights.append({
                    'type': 'anomaly',
                    'severity': 'high' if anomaly_pct > 5 else 'medium',
                    'title': f'{anomaly_count} anomalous records detected',
                    'description': f'{anomaly_pct:.1f}% of records show unusual patterns across multiple metrics',
                    'confidence': 0.85,
                    'metadata': {
                        'anomaly_count': int(anomaly_count),
                        'total_count': len(df),
                        'percentage': float(anomaly_pct),
                        'analyzed_columns': numeric_cols
                    }
                })
        
        except Exception as e:
            logger.warning(f"Error in anomaly detection: {str(e)}")
        
        return insights
    
    async def _narrative_insights(
        self, 
        df: pd.DataFrame, 
        schema: Dict, 
        context: str
    ) -> List[Dict]:
        """Generate AI narrative insights using Claude"""
        
        # Prepare data summary for AI
        summary = self._prepare_data_summary(df, schema)
        
        prompt = f"""You are a data analyst helping to generate insights from business data.

Analyze this dataset and provide 3-5 key actionable insights in JSON format.

Dataset Summary:
{json.dumps(summary, indent=2, default=str)}

Business Context: {context if context else "General business analytics"}

For each insight, provide:
- type: one of ["trend", "anomaly", "correlation", "recommendation", "pattern"]
- severity: one of ["low", "medium", "high"]
- title: Brief, clear headline (max 10 words)
- description: 2-3 sentences explaining the insight
- actionable: true/false - whether this requires immediate action
- recommendation: What should be done about this (if applicable)

Important guidelines:
1. Focus on actionable insights that drive business decisions
2. Highlight unusual patterns or concerning trends
3. Suggest concrete next steps when possible
4. Be specific with numbers and percentages
5. Prioritize insights by business impact

Return ONLY a valid JSON array of insights, no other text or markdown."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract JSON from response
            content = response.content[0].text.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            
            ai_insights = json.loads(content)
            
            # Add confidence and metadata
            for insight in ai_insights:
                insight['confidence'] = 0.75
                insight['source'] = 'ai_analysis'
                insight['generated_at'] = datetime.now(timezone.utc).isoformat()
            
            return ai_insights
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error generating AI insights: {str(e)}")
            return []
    
    def _prepare_data_summary(self, df: pd.DataFrame, schema: Dict) -> Dict:
        """Prepare concise summary for AI analysis"""
        summary = {
            'row_count': len(df),
            'column_count': len(df.columns),
            'time_period': None,
            'metrics': {},
            'dimensions': {}
        }
        
        # Time period
        if schema.get('time_column'):
            time_col = schema['time_column']
            if time_col in df.columns:
                summary['time_period'] = {
                    'start': str(df[time_col].min()),
                    'end': str(df[time_col].max()),
                    'granularity': schema['columns'][list(df.columns).index(time_col)].get('granularity')
                }
        
        # Key metrics (top 5)
        for metric_name, metric_info in list(schema.get('metrics', {}).items())[:5]:
            if metric_name in df.columns:
                current_value = df[metric_name].iloc[-1] if len(df) > 0 else None
                
                summary['metrics'][metric_name] = {
                    'current': float(current_value) if current_value is not None else None,
                    'mean': float(metric_info.get('mean', 0)),
                    'min': float(metric_info.get('min', 0)),
                    'max': float(metric_info.get('max', 0)),
                    'median': float(metric_info.get('median', 0)),
                    'std': float(metric_info.get('std', 0))
                }
        
        # Top dimensions (top 3)
        for dim_name, dim_info in list(schema.get('dimensions', {}).items())[:3]:
            if dim_info.get('top_values'):
                summary['dimensions'][dim_name] = {
                    'unique_count': dim_info['unique_count'],
                    'top_values': list(dim_info['top_values'].keys())[:5],
                    'cardinality': dim_info.get('cardinality')
                }
        
        return summary
    
    async def generate_chart_recommendations(
        self, 
        column_info: Dict
    ) -> List[str]:
        """Recommend appropriate chart types for a column"""
        recommendations = []
        
        semantic_type = column_info.get('semantic_type')
        cardinality = column_info.get('cardinality')
        data_type = column_info.get('data_type')
        
        if semantic_type == 'metric':
            recommendations.extend(['line', 'bar', 'area'])
            
            # If non-negative, can use gauge
            if column_info.get('min', 0) >= 0:
                recommendations.append('gauge')
        
        elif semantic_type == 'categorical':
            if cardinality == 'low':
                recommendations.extend(['pie', 'donut', 'bar', 'column'])
            else:
                recommendations.extend(['bar', 'treemap'])
        
        elif semantic_type == 'temporal':
            recommendations.extend(['line', 'area', 'timeline'])
        
        # If multiple unique values, scatter plot is possible
        if column_info.get('unique_count', 0) > 10:
            recommendations.append('scatter')
        
        return recommendations
    
    async def generate_nlp_query_response(
        self, 
        query: str, 
        df: pd.DataFrame, 
        schema: Dict
    ) -> Dict[str, Any]:
        """Process natural language query and generate response"""
        
        prompt = f"""
        You are a data analyst assistant. A user has asked a question about their data.

        User Question: "{query}"

        Available Data Schema:
        {json.dumps(schema, indent=2, default=str)}

        Sample Data (first 5 rows):
        {df.head().to_json(orient='records', indent=2)}

        Your task:
        1. Interpret the user's question
        2. Determine what analysis or visualization would best answer it
        3. Provide a structured response

        Return a JSON object with:
        - interpretation: What the user is asking for
        - recommended_visualization: Best chart type (line, bar, pie, scatter, table, metric_card)
        - columns_needed: Array of column names needed
        - aggregation: Type of aggregation if needed (sum, avg, count, min, max)
        - filters: Any filters to apply
        - insight: A brief answer to their question based on the data

        Return ONLY valid JSON, no other text.
        """

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            
            # Remove markdown if present
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            logger.error(f"Error processing NLP query: {str(e)}")
            return {
                'error': 'Failed to process query',
                'message': str(e)
            }