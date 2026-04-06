"""
utils/pdf_utils.py - PDF generation utilities for certificates and reports
"""
import os
from datetime import datetime


def generate_certificate_pdf(user_name, project_title, certificate_folder):
    """Generate a certificate PDF using ReportLab."""
    try:
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas

        filename = f"certificate_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
        filepath = os.path.join(certificate_folder, filename)

        c = canvas.Canvas(filepath, pagesize=landscape(A4))
        width, height = landscape(A4)

        # Background
        c.setFillColorRGB(0.95, 0.97, 1.0)
        c.rect(0, 0, width, height, fill=1, stroke=0)

        # Border
        c.setStrokeColorRGB(0.2, 0.4, 0.8)
        c.setLineWidth(6)
        c.rect(20, 20, width - 40, height - 40, fill=0, stroke=1)
        c.setLineWidth(2)
        c.rect(30, 30, width - 60, height - 60, fill=0, stroke=1)

        # Title
        c.setFillColorRGB(0.2, 0.4, 0.8)
        c.setFont("Helvetica-Bold", 42)
        c.drawCentredString(width / 2, height - 120, "Certificate of Achievement")

        # Subtitle
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.setFont("Helvetica", 18)
        c.drawCentredString(width / 2, height - 165, "Project Hub – Academic Project Management System")

        # Divider
        c.setStrokeColorRGB(0.2, 0.4, 0.8)
        c.setLineWidth(1.5)
        c.line(100, height - 185, width - 100, height - 185)

        # Body text
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.setFont("Helvetica", 16)
        c.drawCentredString(width / 2, height - 230, "This is to certify that")

        # Student Name
        c.setFillColorRGB(0.1, 0.3, 0.7)
        c.setFont("Helvetica-Bold", 34)
        c.drawCentredString(width / 2, height - 285, user_name)

        # Project Details
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.setFont("Helvetica", 16)
        c.drawCentredString(width / 2, height - 330, "has successfully completed the project")

        c.setFillColorRGB(0.1, 0.5, 0.3)
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width / 2, height - 370, f'"{project_title}"')

        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.setFont("Helvetica", 14)
        c.drawCentredString(width / 2, height - 410, f"Issued on: {datetime.now().strftime('%B %d, %Y')}")

        # Signature placeholder
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, 80, "_______________________")
        c.drawString(100, 65, "Project Supervisor")

        c.drawString(width - 300, 80, "_______________________")
        c.drawString(width - 300, 65, "Department Head")

        c.save()
        return filename

    except ImportError:
        # Fallback: create a simple text file placeholder
        filename = f"certificate_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.txt"
        filepath = os.path.join(certificate_folder, filename)
        with open(filepath, 'w') as f:
            f.write(f"CERTIFICATE OF ACHIEVEMENT\n\nThis is to certify that {user_name} has successfully completed:\n{project_title}\n\nIssued: {datetime.now().strftime('%B %d, %Y')}")
        return filename


def generate_report_pdf(stats, report_folder):
    """Generate a summary report PDF using ReportLab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet

        filename = f"report_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
        filepath = os.path.join(report_folder, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        elements.append(Paragraph("Project Hub - System Report", styles['Title']))
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Spacer(1, 20))

        # Stats Table
        data = [["Metric", "Value"]]
        for key, value in stats.items():
            data.append([key.replace('_', ' ').title(), str(value)])

        t = Table(data, colWidths=[200, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(t)
        doc.build(elements)
        return filename

    except ImportError:
        filename = f"report_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.txt"
        filepath = os.path.join(report_folder, filename)
        with open(filepath, 'w') as f:
            f.write("Project Hub - System Report\n" + "="*30 + "\n")
            for k, v in stats.items():
                f.write(f"{k}: {v}\n")
        return filename
