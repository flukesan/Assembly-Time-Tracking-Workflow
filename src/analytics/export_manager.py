"""
Export Manager
Export analytics data to various formats (PDF, Excel, CSV, JSON).
"""

import json
import csv
from datetime import datetime
from typing import Dict, Any, List, Optional
from io import StringIO, BytesIO
from loguru import logger


class ExportManager:
    """
    Export Manager

    Handles exporting analytics data to various formats.
    Note: PDF generation requires additional dependencies (reportlab/weasyprint)
    """

    def __init__(self):
        """Initialize export manager"""
        logger.info("Export Manager initialized")

    def export_to_json(
        self,
        data: Any,
        pretty: bool = True
    ) -> str:
        """
        Export data to JSON format

        Args:
            data: Data to export
            pretty: Pretty print JSON

        Returns:
            JSON string
        """
        try:
            if pretty:
                return json.dumps(data, indent=2, default=str)
            else:
                return json.dumps(data, default=str)
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return json.dumps({"error": str(e)})

    def export_to_csv(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None
    ) -> str:
        """
        Export data to CSV format

        Args:
            data: List of dictionaries
            columns: Column names (if None, use all keys from first record)

        Returns:
            CSV string
        """
        try:
            if not data:
                return ""

            # Determine columns
            if columns is None:
                columns = list(data[0].keys())

            # Write CSV
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=columns)
            writer.writeheader()

            for row in data:
                # Convert non-string values
                clean_row = {}
                for col in columns:
                    value = row.get(col, "")
                    if isinstance(value, (list, dict)):
                        clean_row[col] = json.dumps(value)
                    else:
                        clean_row[col] = str(value) if value is not None else ""
                writer.writerow(clean_row)

            return output.getvalue()

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return f"Error: {str(e)}"

    def export_report_to_text(
        self,
        title: str,
        data: Dict[str, Any],
        format_type: str = "simple"  # simple, detailed
    ) -> str:
        """
        Export report to formatted text

        Args:
            title: Report title
            data: Report data
            format_type: Format type

        Returns:
            Formatted text report
        """
        try:
            lines = []
            lines.append("=" * 80)
            lines.append(f" {title}")
            lines.append("=" * 80)
            lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")

            if format_type == "detailed":
                lines.extend(self._format_dict_detailed(data))
            else:
                lines.extend(self._format_dict_simple(data))

            lines.append("")
            lines.append("=" * 80)

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            return f"Error generating report: {str(e)}"

    def export_chart_data_to_csv(
        self,
        chart_data: Dict[str, Any],
        chart_type: str
    ) -> str:
        """
        Export chart data to CSV format

        Args:
            chart_data: Chart data dictionary
            chart_type: Type of chart (time_series, heatmap, distribution, etc.)

        Returns:
            CSV string
        """
        try:
            output = StringIO()
            writer = csv.writer(output)

            if chart_type == "time_series":
                # Time-series: timestamp, series1, series2, ...
                timestamps = chart_data.get("timestamps", [])
                series = chart_data.get("series", {})

                # Header
                header = ["timestamp"] + list(series.keys())
                writer.writerow(header)

                # Data rows
                for i, ts in enumerate(timestamps):
                    row = [ts]
                    for series_name, values in series.items():
                        row.append(values[i] if i < len(values) else "")
                    writer.writerow(row)

            elif chart_type == "heatmap":
                # Heatmap: y_label, x1, x2, x3, ...
                x_labels = chart_data.get("x_labels", [])
                y_labels = chart_data.get("y_labels", [])
                values = chart_data.get("values", [])

                # Header
                header = [""] + x_labels
                writer.writerow(header)

                # Data rows
                for i, y_label in enumerate(y_labels):
                    row = [y_label]
                    if i < len(values):
                        row.extend(values[i])
                    writer.writerow(row)

            elif chart_type == "distribution":
                # Distribution: bin, count
                bin_labels = chart_data.get("bin_labels", [])
                counts = chart_data.get("counts", [])

                writer.writerow(["bin", "count"])
                for i, bin_label in enumerate(bin_labels):
                    count = counts[i] if i < len(counts) else 0
                    writer.writerow([bin_label, count])

            elif chart_type == "comparison":
                # Comparison: label, value
                labels = chart_data.get("labels", [])
                values = chart_data.get("values", [])

                writer.writerow(["label", "value"])
                for i, label in enumerate(labels):
                    value = values[i] if i < len(values) else 0
                    writer.writerow([label, value])

            else:
                # Generic: convert to key-value pairs
                writer.writerow(["key", "value"])
                for key, value in chart_data.items():
                    writer.writerow([key, str(value)])

            return output.getvalue()

        except Exception as e:
            logger.error(f"Error exporting chart data: {e}")
            return f"Error: {str(e)}"

    def create_download_response(
        self,
        content: str,
        filename: str,
        content_type: str
    ) -> Dict[str, Any]:
        """
        Create download response object

        Args:
            content: File content
            filename: Filename
            content_type: MIME content type

        Returns:
            Response object with download info
        """
        return {
            "filename": filename,
            "content_type": content_type,
            "content": content,
            "size_bytes": len(content.encode('utf-8')),
            "generated_at": datetime.now().isoformat()
        }

    # Helper methods

    def _format_dict_simple(self, data: Dict[str, Any], indent: int = 0) -> List[str]:
        """Format dictionary as simple text"""
        lines = []
        prefix = "  " * indent

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.extend(self._format_dict_simple(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{prefix}{key}: {len(value)} items")
            else:
                lines.append(f"{prefix}{key}: {value}")

        return lines

    def _format_dict_detailed(self, data: Dict[str, Any], indent: int = 0) -> List[str]:
        """Format dictionary as detailed text"""
        lines = []
        prefix = "  " * indent

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}[{key}]")
                lines.extend(self._format_dict_detailed(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{prefix}{key}:")
                for i, item in enumerate(value[:10]):  # Limit to first 10 items
                    if isinstance(item, dict):
                        lines.append(f"{prefix}  Item {i+1}:")
                        lines.extend(self._format_dict_simple(item, indent + 2))
                    else:
                        lines.append(f"{prefix}  - {item}")
                if len(value) > 10:
                    lines.append(f"{prefix}  ... and {len(value) - 10} more")
            else:
                lines.append(f"{prefix}{key}: {value}")

        return lines


# Note: PDF Export requires additional dependencies
# Uncomment and install reportlab or weasyprint for PDF support
"""
def export_to_pdf(self, data: Dict[str, Any], title: str) -> bytes:
    '''
    Export data to PDF format
    Requires: pip install reportlab
    '''
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Add title
        story.append(Paragraph(title, styles['Title']))
        story.append(Spacer(1, 12))

        # Add content
        for key, value in data.items():
            story.append(Paragraph(f"<b>{key}:</b> {value}", styles['Normal']))

        doc.build(story)
        return buffer.getvalue()

    except ImportError:
        logger.error("reportlab not installed. Install with: pip install reportlab")
        return b"PDF export requires reportlab"
    except Exception as e:
        logger.error(f"Error exporting to PDF: {e}")
        return b"Error generating PDF"
"""
