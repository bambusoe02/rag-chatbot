"""Export utilities for chat history and documents."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from io import BytesIO

from loguru import logger


class ChatExporter:
    """Export chat conversations to various formats."""
    
    @staticmethod
    def to_text(messages: List[Dict[str, Any]]) -> str:
        """Export chat messages to plain text format.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Plain text string
        """
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            lines.append(f"[{timestamp}] {role}:")
            lines.append(content)
            lines.append("")
            
            if "sources" in msg and msg["sources"]:
                lines.append("Sources:")
                for source in msg["sources"]:
                    filename = source.get("filename", "unknown")
                    page = source.get("page", "")
                    if page:
                        lines.append(f"  - {filename} (page {page})")
                    else:
                        lines.append(f"  - {filename}")
                lines.append("")
            
            lines.append("-" * 60)
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def to_json(messages: List[Dict[str, Any]], session_id: str) -> str:
        """Export chat messages to JSON format.
        
        Args:
            messages: List of message dictionaries
            session_id: Session identifier
            
        Returns:
            JSON string
        """
        export_data = {
            "session_id": session_id,
            "exported_at": datetime.now().isoformat(),
            "message_count": len(messages),
            "messages": messages,
        }
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    @staticmethod
    def to_pdf(messages: List[Dict[str, Any]], session_id: str) -> bytes:
        """Export chat messages to PDF format.
        
        Args:
            messages: List of message dictionaries
            session_id: Session identifier
            
        Returns:
            PDF content as bytes
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.units import inch
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#007bff'),
                spaceAfter=30,
            )
            elements.append(Paragraph("RAG Chatbot Conversation", title_style))
            elements.append(Paragraph(f"Session: {session_id}", styles['Normal']))
            elements.append(Paragraph(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 0.5*inch))
            
            # Messages
            for msg in messages:
                role = msg.get("role", "unknown").upper()
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")
                
                # Role header
                role_color = colors.HexColor('#ff7f0e' if role == 'USER' else '#2ca02c')
                role_style = ParagraphStyle(
                    'Role',
                    parent=styles['Heading2'],
                    fontSize=14,
                    textColor=role_color,
                    spaceAfter=6,
                )
                elements.append(Paragraph(f"{role} {timestamp if timestamp else ''}", role_style))
                
                # Content (escape HTML)
                content_escaped = content.replace('<', '&lt;').replace('>', '&gt;')
                elements.append(Paragraph(content_escaped, styles['Normal']))
                
                # Sources
                if "sources" in msg and msg["sources"]:
                    elements.append(Spacer(1, 0.1*inch))
                    elements.append(Paragraph("Sources:", styles['Heading3']))
                    for source in msg["sources"]:
                        filename = source.get('filename', 'unknown')
                        page = source.get('page', '')
                        page_info = f" (page {page})" if page else ""
                        elements.append(Paragraph(f"• {filename}{page_info}", styles['Normal']))
                
                elements.append(Spacer(1, 0.3*inch))
            
            # Build PDF
            doc.build(elements)
            buffer.seek(0)
            return buffer.getvalue()
            
        except ImportError:
            logger.error("reportlab not installed, cannot generate PDF")
            raise
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise


# Global exporter instance
chat_exporter = ChatExporter()

