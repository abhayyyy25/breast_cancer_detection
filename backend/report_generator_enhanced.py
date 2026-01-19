"""
Enhanced PDF Report Generator with Repeating Headers & Footers
Hospital-Grade Medical Report System
Uses ReportLab BaseDocTemplate with PageTemplate for automatic header/footer repetition
"""

from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image as RLImage,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
import io
import os
from PIL import Image
import base64


# ============================================================================
# HEADER & FOOTER DRAWING FUNCTIONS
# ============================================================================

def create_header_footer_functions(settings_data, patient, current_user):
    """
    Factory function that creates header and footer drawing functions
    with access to hospital branding data
    
    Args:
        settings_data: ReportSettings object with hospital branding
        patient: Patient object
        current_user: User who generated the report
    
    Returns:
        tuple: (header_function, footer_function)
    """
    
    # Extract branding data with defaults
    hospital_name = settings_data.hospital_name if settings_data and settings_data.hospital_name else "Medical Facility"
    hospital_address = settings_data.hospital_address if settings_data and settings_data.hospital_address else ""
    hospital_contact = settings_data.hospital_contact if settings_data and settings_data.hospital_contact else ""
    footer_text = settings_data.footer_text if settings_data and settings_data.footer_text else ""
    header_color = settings_data.report_header_color if settings_data and settings_data.report_header_color else "#2563EB"
    logo_base64 = settings_data.logo_base64 if settings_data and settings_data.logo_base64 else None
    
    # Convert base64 logo to ReportLab Image (once, reused on all pages)
    logo_image = None
    if logo_base64:
        try:
            # Remove data URL prefix if present
            if ',' in logo_base64:
                logo_base64 = logo_base64.split(',')[1]
            
            # Decode base64
            img_data = base64.b64decode(logo_base64)
            img_buffer = io.BytesIO(img_data)
            pil_img = Image.open(img_buffer)
            
            # Convert to ReportLab image
            img_buffer.seek(0)
            logo_image = RLImage(img_buffer)
            
            # Set size (1 inch height, maintain aspect ratio)
            w, h = pil_img.size
            aspect = w / h
            logo_image.drawHeight = 0.8 * inch
            logo_image.drawWidth = 0.8 * inch * aspect
        except Exception as e:
            print(f"Error loading logo: {e}")
            logo_image = None
    
    
    def draw_header(canvas, doc):
        """
        Draw header on every page
        This function is called automatically by ReportLab for each page
        """
        canvas.saveState()
        
        # Get page dimensions
        page_width, page_height = letter
        
        # Header background (optional - light color bar)
        # canvas.setFillColor(colors.HexColor("#F8FAFC"))
        # canvas.rect(0, page_height - 1.2*inch, page_width, 1.2*inch, fill=True, stroke=False)
        
        # Draw logo (if available)
        if logo_image:
            logo_image.drawOn(canvas, 0.75*inch, page_height - 1.3*inch)
        
        # Hospital Name (bold, large)
        canvas.setFont("Helvetica-Bold", 14)
        canvas.setFillColor(colors.HexColor(header_color))
        logo_offset = 2.2*inch if logo_image else 0.75*inch
        canvas.drawString(logo_offset, page_height - 0.9*inch, hospital_name.upper())
        
        # Report Title
        canvas.setFont("Helvetica", 11)
        canvas.setFillColor(colors.HexColor("#374151"))
        canvas.drawString(logo_offset, page_height - 1.1*inch, "Breast Cancer Detection – Medical Report")
        
        # Patient Info (right side)
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        right_margin = page_width - 0.75*inch
        canvas.drawRightString(right_margin, page_height - 0.9*inch, f"Patient: {patient.full_name}")
        canvas.drawRightString(right_margin, page_height - 1.05*inch, f"MRN: {patient.mrn}")
        canvas.drawRightString(right_margin, page_height - 1.2*inch, f"Date: {datetime.now().strftime('%B %d, %Y')}")
        
        # Horizontal line separator
        canvas.setStrokeColor(colors.HexColor(header_color))
        canvas.setLineWidth(1.5)
        canvas.line(0.75*inch, page_height - 1.4*inch, page_width - 0.75*inch, page_height - 1.4*inch)
        
        canvas.restoreState()
    
    
    def draw_footer(canvas, doc):
        """
        Draw footer on every page
        This function is called automatically by ReportLab for each page
        """
        canvas.saveState()
        
        # Get page dimensions
        page_width, page_height = letter
        
        # Footer separator line
        canvas.setStrokeColor(colors.HexColor("#D1D5DB"))
        canvas.setLineWidth(0.5)
        canvas.line(0.75*inch, 1.1*inch, page_width - 0.75*inch, 1.1*inch)
        
        # Medical Disclaimer (small text)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        
        disclaimer_lines = [
            "⚠ MEDICAL DISCLAIMER: This AI-generated report is for educational and research purposes only.",
            "Not clinically validated. Must be interpreted by licensed medical professionals only.",
        ]
        
        y_position = 0.95*inch
        for line in disclaimer_lines:
            canvas.drawCentredString(page_width / 2, y_position, line)
            y_position -= 0.12*inch
        
        # Hospital Contact Info
        if hospital_address or hospital_contact:
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.HexColor("#374151"))
            contact_text = f"{hospital_address} | {hospital_contact}" if hospital_address and hospital_contact else (hospital_address or hospital_contact)
            canvas.drawCentredString(page_width / 2, 0.65*inch, contact_text)
        
        # Custom footer text (if provided)
        if footer_text:
            canvas.setFont("Helvetica-Oblique", 7)
            canvas.setFillColor(colors.HexColor("#6B7280"))
            # Truncate if too long
            footer_display = footer_text[:120] + "..." if len(footer_text) > 120 else footer_text
            canvas.drawCentredString(page_width / 2, 0.5*inch, footer_display)
        
        # Electronic signature statement
        canvas.setFont("Helvetica-Oblique", 7)
        canvas.setFillColor(colors.HexColor("#9CA3AF"))
        canvas.drawCentredString(page_width / 2, 0.35*inch, "This report is electronically generated and valid without signature")
        
        # Page number (Page X of Y)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(colors.HexColor("#374151"))
        page_num = canvas.getPageNumber()
        canvas.drawRightString(page_width - 0.75*inch, 0.5*inch, f"Page {page_num}")
        
        # Generation timestamp (left corner)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#9CA3AF"))
        canvas.drawString(0.75*inch, 0.35*inch, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        canvas.restoreState()
    
    return draw_header, draw_footer


# ============================================================================
# MAIN PDF GENERATION FUNCTION
# ============================================================================

def generate_pdf_report_with_headers(scan, patient, current_user, settings_data=None):
    """
    Generate a professional PDF medical report with repeating headers and footers
    
    Args:
        scan: Scan object from database (contains analysis results)
        patient: Patient object from database (contains patient info)
        current_user: User object (doctor/lab tech who generated the report)
        settings_data: ReportSettings object (optional, contains customization)
    
    Returns:
        str: File path to the generated PDF report
    """
    # Create reports directory if it doesn't exist
    reports_dir = os.getenv("REPORTS_DIR", "./reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # Generate unique filename
    report_filename = f"Report_{scan.scan_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    report_path = os.path.join(reports_dir, report_filename)
    
    # ========================================================================
    # CREATE DOCUMENT WITH CUSTOM PAGE TEMPLATE
    # ========================================================================
    
    # Create header and footer functions with hospital branding
    draw_header, draw_footer = create_header_footer_functions(settings_data, patient, current_user)
    
    # Create document with BaseDocTemplate (not SimpleDocTemplate)
    doc = BaseDocTemplate(
        report_path,
        pagesize=letter,
        topMargin=1.6 * inch,      # Space for header
        bottomMargin=1.3 * inch,    # Space for footer
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )
    
    # Define frame for content (area between header and footer)
    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id='normal'
    )
    
    # Create page template with header and footer callbacks
    def on_page(canvas, doc):
        """Combined callback for both header and footer"""
        draw_header(canvas, doc)
        draw_footer(canvas, doc)
    
    template = PageTemplate(id='main', frames=frame, onPage=on_page)
    doc.addPageTemplates([template])
    
    # ========================================================================
    # BUILD CONTENT (STORY)
    # ========================================================================
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1E40AF'),
        alignment=TA_CENTER,
        spaceAfter=20,
        fontName='Helvetica-Bold',
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1E40AF'),
        spaceBefore=15,
        spaceAfter=10,
        fontName='Helvetica-Bold',
    )
    
    subheading_style = ParagraphStyle(
        'SubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#3B82F6'),
        spaceAfter=8,
        fontName='Helvetica-Bold',
    )
    
    normal_style = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=10,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=4,
    )
    
    # ========================================================================
    # CONTENT SECTIONS
    # ========================================================================
    
    # Title
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("ANALYSIS REPORT", title_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Executive Summary
    story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
    
    prediction = scan.prediction or "Unknown"
    confidence = scan.confidence_score or 0.0
    risk_level = scan.risk_level or "Unknown"
    
    exec_text = f"""
    The AI-based deep learning model analyzed the uploaded breast tissue image and classified it as
    <b>{prediction.upper()}</b> with a confidence score of <b>{confidence:.2f}%</b>.
    Risk assessment: <b>{risk_level.upper()}</b>.
    """
    story.append(Paragraph(exec_text, normal_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Analysis Results Table
    story.append(Paragraph("ANALYSIS RESULTS", heading_style))
    
    benign_prob = 100 - confidence if prediction.lower() == "malignant" else confidence
    malignant_prob = confidence if prediction.lower() == "malignant" else 100 - confidence
    
    results_data = [
        ['Parameter', 'Value'],
        ['Classification', prediction.upper()],
        ['Risk Level', risk_level.upper()],
        ['Confidence Score', f"{confidence:.2f}%"],
        ['Benign Probability', f"{benign_prob:.2f}%"],
        ['Malignant Probability', f"{malignant_prob:.2f}%"],
        ['Scan Number', scan.scan_number or 'N/A'],
        ['Scan Date', scan.scan_date.strftime('%B %d, %Y %H:%M') if scan.scan_date else 'N/A'],
    ]
    
    results_table = Table(results_data, colWidths=[2.5 * inch, 3.5 * inch])
    results_table.setStyle(
        TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#EFF6FF")),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#BFDBFE")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ])
    )
    
    story.append(results_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Doctor's Notes
    if scan.doctor_notes:
        story.append(Paragraph("DOCTOR'S NOTES", subheading_style))
        story.append(Paragraph(scan.doctor_notes, normal_style))
        story.append(Spacer(1, 0.2 * inch))
    
    # Page break before images
    story.append(PageBreak())
    
    # Visual Analysis
    story.append(Paragraph("VISUAL ANALYSIS", heading_style))
    
    # Helper function to load images
    def load_image(img_path, max_w=5.5 * inch, max_h=4.0 * inch):
        if not img_path or not os.path.exists(img_path):
            return None
        try:
            img = Image.open(img_path)
            rl_img = RLImage(img_path)
            w, h = img.size
            aspect = w / h
            if aspect > (max_w / max_h):
                rl_img.drawWidth = max_w
                rl_img.drawHeight = max_w / aspect
            else:
                rl_img.drawHeight = max_h
                rl_img.drawWidth = max_h * aspect
            return rl_img
        except Exception as e:
            print(f"Error loading image {img_path}: {e}")
            return None
    
    # Original Image
    story.append(Paragraph("1. Original Medical Image", subheading_style))
    original_img = load_image(scan.image_path)
    if original_img:
        story.append(original_img)
    else:
        story.append(Paragraph("Image not available.", normal_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Heatmap Overlay
    if scan.overlay_path and os.path.exists(scan.overlay_path):
        story.append(Paragraph("2. Grad-CAM Heatmap Overlay", subheading_style))
        overlay_img = load_image(scan.overlay_path)
        if overlay_img:
            story.append(overlay_img)
        story.append(Spacer(1, 0.2 * inch))
    
    # Heatmap Only
    if scan.heatmap_path and os.path.exists(scan.heatmap_path):
        story.append(Paragraph("3. Activation Heatmap", subheading_style))
        heatmap_img = load_image(scan.heatmap_path)
        if heatmap_img:
            story.append(heatmap_img)
        story.append(Spacer(1, 0.2 * inch))
    
    # Page break before recommendations
    story.append(PageBreak())
    
    # Clinical Recommendations
    story.append(Paragraph("CLINICAL RECOMMENDATIONS", heading_style))
    
    if prediction.lower() == "malignant" or risk_level.lower() in ["high", "moderate"]:
        recommendations = [
            "Consult an oncologist or radiologist immediately for further evaluation.",
            "Request additional diagnostic imaging (mammography, ultrasound, or MRI).",
            "Consider biopsy for definitive diagnosis.",
            "Schedule urgent follow-up appointments.",
            "Discuss potential treatment options with medical professionals.",
        ]
    else:
        recommendations = [
            "Continue routine breast cancer screening as recommended.",
            "Maintain regular follow-ups with your healthcare provider.",
            "Monitor for any changes in symptoms or physical examination.",
            "Keep previous medical imaging records for comparison.",
            "Maintain a healthy lifestyle and follow preventive care guidelines.",
        ]
    
    for rec in recommendations:
        story.append(Paragraph(f"• {rec}", bullet_style))
    
    story.append(Spacer(1, 0.3 * inch))
    
    # Signature Section
    doctor_name = settings_data.doctor_name if settings_data and settings_data.doctor_name else current_user.full_name
    display_name = settings_data.display_name if settings_data and settings_data.display_name else doctor_name
    license_number = settings_data.license_number if settings_data and settings_data.license_number else ""
    
    signature_data = [
        ['Authorized By:', ''],
        ['Name:', display_name],
        ['Role:', current_user.role.value.replace('_', ' ').title()],
    ]
    
    if license_number:
        signature_data.append(['License Number:', license_number])
    
    signature_data.append(['Date:', datetime.now().strftime('%B %d, %Y')])
    
    signature_table = Table(signature_data, colWidths=[2 * inch, 4 * inch])
    signature_table.setStyle(
        TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])
    )
    
    story.append(signature_table)
    
    # ========================================================================
    # BUILD PDF
    # ========================================================================
    
    try:
        doc.build(story)
        print(f"[SUCCESS] PDF report generated with headers/footers: {report_path}")
        return report_path
    except Exception as e:
        print(f"[ERROR] Failed to generate PDF: {e}")
        raise


# ============================================================================
# BACKWARD COMPATIBILITY WRAPPER
# ============================================================================

def generate_pdf_report(scan, patient, current_user, settings_data=None):
    """
    Wrapper function for backward compatibility
    Calls the enhanced version with headers/footers
    """
    return generate_pdf_report_with_headers(scan, patient, current_user, settings_data)
