import io
import json
import base64
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging
import pandas as pd

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from PIL import Image as PILImage
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dashboard import Dashboard
from app.models.widget import Widget
from app.models.data_source import DataSource, Dataset
from app.services.query.query_executor import QueryExecutor

logger = logging.getLogger(__name__)

class ExportService:
    """Service for exporting dashboards and widgets"""
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.styles = getSampleStyleSheet()
        self.db_session = db_session
        self.query_executor = QueryExecutor()
        
    async def export_dashboard_to_pdf(self, dashboard: Dashboard) -> bytes:
        """Export dashboard to PDF"""
        buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.5*inch
        )
        
        # Container for PDF elements
        elements = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        title = Paragraph(dashboard.name, title_style)
        elements.append(title)
        
        # Description
        if dashboard.description:
            desc_style = ParagraphStyle(
                'Description',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.grey,
                alignment=TA_CENTER,
                spaceAfter=20
            )
            description = Paragraph(dashboard.description, desc_style)
            elements.append(description)
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Metadata table
        metadata = [
            ['Generated:', datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')],
            ['Dashboard ID:', str(dashboard.id)],
            ['Total Widgets:', str(len(dashboard.widgets))]
        ]
        
        metadata_table = Table(metadata, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(metadata_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Add widgets
        for idx, widget in enumerate(dashboard.widgets, 1):
            # Widget header
            widget_header_style = ParagraphStyle(
                'WidgetHeader',
                parent=self.styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#333333'),
                spaceAfter=8
            )
            
            widget_title = Paragraph(f"{idx}. {widget.title}", widget_header_style)
            elements.append(widget_title)
            
            # Widget type badge
            type_text = f"<font color='#666666' size='8'>[{widget.widget_type.upper()}]</font>"
            type_para = Paragraph(type_text, self.styles['Normal'])
            elements.append(type_para)
            elements.append(Spacer(1, 0.1*inch))
            
            # Widget visualization/data
            try:
                if widget.widget_type in ['chart', 'bar', 'line', 'pie', 'area', 'scatter', 'metric_card', 'metric']:
                    # Generate chart image
                    chart_image = await self._generate_widget_chart(widget)
                    if chart_image:
                        # Convert to reportlab Image
                        img = Image(chart_image, width=6*inch, height=3*inch)
                        elements.append(img)
                    else:
                        # No data available
                        no_data_text = f"<font color='gray'>[No data available for this widget]</font>"
                        elements.append(Paragraph(no_data_text, self.styles['Normal']))
                
                elif widget.widget_type == 'table':
                    # Render table data
                    table_data = await self._get_widget_table_data(widget)
                    if table_data and len(table_data) > 1:
                        widget_table = self._create_pdf_table(table_data)
                        elements.append(widget_table)
                    else:
                        # No data available
                        no_data_text = f"<font color='gray'>[No data available for this widget]</font>"
                        elements.append(Paragraph(no_data_text, self.styles['Normal']))
                
                elif widget.widget_type == 'insights_panel':
                    # Render insights as bullet points
                    widget_config = {**(widget.query_config or {}), **(widget.chart_config or {})}
                    insights = widget_config.get('insights', [])
                    for insight in insights[:5]:  # Limit to 5
                        insight_text = f"• {insight.get('title', '')}: {insight.get('description', '')}"
                        insight_para = Paragraph(insight_text, self.styles['Normal'])
                        elements.append(insight_para)
                        elements.append(Spacer(1, 0.05*inch))
            
            except Exception as e:
                logger.warning(f"Error rendering widget {widget.id}: {str(e)}")
                error_text = f"<font color='red'>Error rendering widget: {str(e)}</font>"
                elements.append(Paragraph(error_text, self.styles['Normal']))
            
            elements.append(Spacer(1, 0.3*inch))
            
            # Page break after every 3 widgets
            if idx % 3 == 0 and idx < len(dashboard.widgets):
                elements.append(PageBreak())
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    async def export_dashboard_to_image(self, dashboard: Dashboard, format: str = "png") -> bytes:
        """Export dashboard to image (PNG)"""
        # Create a figure with subplots for each widget
        num_widgets = len(dashboard.widgets)
        
        if num_widgets == 0:
            # Empty dashboard
            fig, ax = plt.subplots(figsize=(12, 8))
            ax.text(0.5, 0.5, 'No widgets in dashboard', 
                   ha='center', va='center', fontsize=16, color='gray')
            ax.axis('off')
        else:
            # Calculate grid layout
            cols = min(2, num_widgets)
            rows = (num_widgets + cols - 1) // cols
            
            fig, axes = plt.subplots(rows, cols, figsize=(12, 6*rows))
            if num_widgets == 1:
                axes = [axes]
            else:
                axes = axes.flatten()
            
            # Add dashboard title
            fig.suptitle(dashboard.name, fontsize=20, fontweight='bold', y=0.995)
            
            # Render each widget
            for idx, widget in enumerate(dashboard.widgets):
                ax = axes[idx]
                
                try:
                    await self._render_widget_to_axis(widget, ax)
                except Exception as e:
                    logger.warning(f"Error rendering widget {widget.id}: {str(e)}")
                    ax.text(0.5, 0.5, f'Error: {str(e)}', 
                           ha='center', va='center', color='red')
                    ax.axis('off')
            
            # Hide empty subplots
            for idx in range(num_widgets, len(axes)):
                axes[idx].axis('off')
            
            plt.tight_layout()
        
        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format=format, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        buffer.seek(0)
        image_bytes = buffer.read()
        buffer.close()
        
        return image_bytes
    
    async def export_dashboard_to_json(self, dashboard: Dashboard) -> bytes:
        """Export dashboard configuration to JSON"""
        dashboard_data = {
            'id': str(dashboard.id),
            'name': dashboard.name,
            'description': dashboard.description,
            'created_at': dashboard.created_at.isoformat(),
            'layout_config': dashboard.layout_config,
            'filters': dashboard.filters,
            'theme': dashboard.theme,
            'widgets': []
        }
        
        for widget in dashboard.widgets:
            widget_config = {**(widget.query_config or {}), **(widget.chart_config or {})}
            widget_data = {
                'id': str(widget.id),
                'type': widget.widget_type,
                'title': widget.title,
                'position': widget.position,
                'config': widget_config,
                'query_config': widget.query_config,
                'chart_config': widget.chart_config,
                'data_mapping': widget.data_mapping
            }
            dashboard_data['widgets'].append(widget_data)
        
        json_str = json.dumps(dashboard_data, indent=2)
        return json_str.encode('utf-8')
    
    async def export_widget_to_image(
        self, 
        widget: Widget, 
        format: str = "png", 
        width: int = 1200, 
        height: int = 800
    ) -> bytes:
        """Export single widget to image"""
        # Create figure
        fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
        
        try:
            await self._render_widget_to_axis(widget, ax)
        except Exception as e:
            logger.error(f"Error rendering widget: {str(e)}")
            ax.text(0.5, 0.5, f'Error: {str(e)}', 
                   ha='center', va='center', color='red')
            ax.axis('off')
        
        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format=format, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        buffer.seek(0)
        image_bytes = buffer.read()
        buffer.close()
        
        return image_bytes
    
    async def export_widget_to_json(self, widget: Widget) -> bytes:
        """Export widget configuration to JSON"""
        widget_config = {**(widget.query_config or {}), **(widget.chart_config or {})}
        widget_data = {
            'id': str(widget.id),
            'dashboard_id': str(widget.dashboard_id),
            'type': widget.widget_type,
            'title': widget.title,
            'position': widget.position,
            'config': widget_config,
            'query_config': widget.query_config,
            'chart_config': widget.chart_config,
            'data_mapping': widget.data_mapping,
            'created_at': widget.created_at.isoformat()
        }
        
        json_str = json.dumps(widget_data, indent=2)
        return json_str.encode('utf-8')
    
    async def _generate_widget_chart(self, widget: Widget) -> io.BytesIO:
        """Generate chart image for widget"""
        fig, ax = plt.subplots(figsize=(6, 3), dpi=100)
        
        await self._render_widget_to_axis(widget, ax)
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        plt.close(fig)
        
        buffer.seek(0)
        return buffer
    
    async def _render_widget_to_axis(self, widget: Widget, ax):
        """Render widget content to matplotlib axis"""
        # Fetch actual widget data
        widget_data = await self._get_widget_data(widget)
        
        if not widget_data or not widget_data.get('data'):
            # No data available
            ax.text(0.5, 0.5, f'{widget.title}\n(No data available)', 
                   ha='center', va='center', fontsize=12, color='gray')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return
        
        data = widget_data['data']
        
        # Merge query_config and chart_config for backward compatibility
        config = {**(widget.query_config or {}), **(widget.chart_config or {})}
        
        if widget.widget_type == 'metric_card' or widget.widget_type == 'metric':
            # Display metric value
            if data and len(data) > 0:
                # Get the first row of data
                first_row = data[0]
                # Get the value from the aggregated column
                value = first_row.get(config.get('y_axis', 'value'), 'N/A')
                metric_label = config.get('y_axis', 'Value')
            else:
                value = 'N/A'
                metric_label = 'Value'
            
            ax.text(0.5, 0.6, str(value), 
                   ha='center', va='center', fontsize=48, fontweight='bold')
            ax.text(0.5, 0.3, metric_label, 
                   ha='center', va='center', fontsize=14, color='gray')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        
        elif widget.widget_type in ['chart', 'bar', 'line', 'pie', 'area', 'scatter']:
            chart_type = widget.widget_type if widget.widget_type != 'chart' else config.get('chart_type', 'bar')
            x_axis = config.get('x_axis', 'x')
            y_axis = config.get('y_axis', 'y')
            
            # Extract data for plotting
            if data and len(data) > 0:
                df = pd.DataFrame(data)
                
                if x_axis in df.columns and y_axis in df.columns:
                    categories = df[x_axis].tolist()
                    values = df[y_axis].tolist()
                    
                    if chart_type == 'bar':
                        ax.bar(categories, values, color='#1976d2')
                        ax.set_ylabel(y_axis)
                        ax.set_xlabel(x_axis)
                    elif chart_type == 'line':
                        ax.plot(categories, values, marker='o', linewidth=2, color='#1976d2')
                        ax.set_ylabel(y_axis)
                        ax.set_xlabel(x_axis)
                    elif chart_type == 'pie':
                        ax.pie(values, labels=categories, autopct='%1.1f%%')
                    elif chart_type == 'area':
                        ax.fill_between(range(len(values)), values, alpha=0.5, color='#1976d2')
                        ax.plot(categories, values, linewidth=2, color='#1976d2')
                        ax.set_ylabel(y_axis)
                        ax.set_xlabel(x_axis)
                    elif chart_type == 'scatter':
                        ax.scatter(categories, values, s=100, color='#1976d2')
                        ax.set_ylabel(y_axis)
                        ax.set_xlabel(x_axis)
                    
                    ax.set_title(widget.title, fontsize=12, fontweight='bold')
                    if chart_type != 'pie':
                        ax.grid(True, alpha=0.3)
                        # Rotate x-axis labels if too many
                        if len(categories) > 5:
                            ax.tick_params(axis='x', rotation=45)
                else:
                    ax.text(0.5, 0.5, f'{widget.title}\n(Invalid data columns)', 
                           ha='center', va='center', fontsize=12, color='red')
                    ax.axis('off')
            else:
                ax.text(0.5, 0.5, f'{widget.title}\n(No data)', 
                       ha='center', va='center', fontsize=12, color='gray')
                ax.axis('off')
        
        elif widget.widget_type == 'table':
            # Display table data
            if data and len(data) > 0:
                df = pd.DataFrame(data)
                # Show first 10 rows
                table_text = df.head(10).to_string()
                ax.text(0.05, 0.95, table_text, 
                       ha='left', va='top', fontsize=6, family='monospace')
                ax.set_title(widget.title, fontsize=12, fontweight='bold')
            else:
                ax.text(0.5, 0.5, f'{widget.title}\n(No data)', 
                       ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
        
        else:
            # Default rendering
            ax.text(0.5, 0.5, widget.title, 
                   ha='center', va='center', fontsize=14)
            ax.axis('off')
    
    async def _get_widget_data(self, widget: Widget) -> Optional[Dict[str, Any]]:
        """Fetch actual data for a widget"""
        if not self.db_session:
            logger.warning(f"No database session available for widget {widget.id}")
            return None
            
        if not widget.data_source_id:
            logger.info(f"Widget {widget.id} has no data source, skipping data fetch")
            return None
        
        try:
            logger.info(f"Fetching data for widget {widget.id} from data source {widget.data_source_id}")
            
            # Get data source
            ds_result = await self.db_session.execute(
                select(DataSource).where(DataSource.id == widget.data_source_id)
            )
            data_source = ds_result.scalar_one_or_none()
            
            if not data_source:
                logger.warning(f"Data source {widget.data_source_id} not found for widget {widget.id}")
                return None
            
            logger.info(f"Found data source: {data_source.name}")
            
            # Get latest dataset
            dataset_result = await self.db_session.execute(
                select(Dataset)
                .where(Dataset.data_source_id == data_source.id)
                .order_by(Dataset.version.desc())
                .limit(1)
            )
            dataset = dataset_result.scalar_one_or_none()
            
            if not dataset:
                logger.warning(f"No dataset found for data source {data_source.id}")
                return None
            
            logger.info(f"Loading data from dataset version {dataset.version}, path: {dataset.storage_path}")
            
            # Load data from parquet
            df = pd.read_parquet(dataset.storage_path)
            logger.info(f"Loaded dataframe with shape {df.shape}")
            
            # Execute widget query
            widget_config = {
                **(widget.query_config or {}),
                **(widget.chart_config or {}),
            }
            
            logger.info(f"Executing widget query with config: {widget_config}")
            result_data = await self.query_executor.execute_widget_query(
                df, widget_config, widget.widget_type
            )
            
            logger.info(f"Query executed, got {len(result_data.get('data', []))} rows")
            return result_data
            
        except Exception as e:
            logger.error(f"Error fetching widget data for {widget.id}: {str(e)}", exc_info=True)
            return None
    
    async def _get_widget_table_data(self, widget: Widget) -> list:
        """Get table data for widget"""
        # Fetch actual widget data
        widget_data = await self._get_widget_data(widget)
        
        if not widget_data or not widget_data.get('data'):
            return []
        
        data = widget_data['data']
        columns = widget_data.get('columns', [])
        
        if not data:
            return []
        
        # Convert to table format
        table_data = [columns] if columns else [list(data[0].keys())]
        
        # Add data rows (limit to 20 rows for PDF)
        for row in data[:20]:
            table_data.append([str(row.get(col, '')) for col in table_data[0]])
        
        return table_data
    
    def _create_pdf_table(self, data: list) -> Table:
        """Create formatted PDF table"""
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        return table