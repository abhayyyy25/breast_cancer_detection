# report_generator.py
"""
Hospital-Grade PDF Report Generator with Repeating Headers & Footers
Uses ReportLab BaseDocTemplate for automatic header/footer repetition on every page
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
import numpy as np
import base64


# ============================================================================
# HEADER & FOOTER CALLBACK FUNCTIONS
# ============================================================================

def create_header_footer_callbacks(settings_data, patient, current_user):
    """
    Factory function that creates header and footer drawing functions
    with access to hospital branding data from Report Settings
    
    CRITICAL: This ensures headers/footers are DYNAMIC and pull from database
    
    Args:
        settings_data: ReportSettings object with hospital branding
        patient: Patient object
        current_user: User who generated the report
    
    Returns:
        tuple: (draw_header_func, draw_footer_func)
    """
    
    # ========================================================================
    # EXTRACT BRANDING DATA FROM REPORT SETTINGS (DATABASE)
    # ========================================================================
    hospital_name = settings_data.hospital_name if settings_data and settings_data.hospital_name else "Medical Facility"
    hospital_address = settings_data.hospital_address if settings_data and settings_data.hospital_address else ""
    hospital_contact = settings_data.hospital_contact if settings_data and settings_data.hospital_contact else ""
    footer_text = settings_data.footer_text if settings_data and settings_data.footer_text else ""
    header_color = settings_data.report_header_color if settings_data and settings_data.report_header_color else "#2563EB"
    logo_base64 = settings_data.logo_base64 if settings_data and settings_data.logo_base64 else None
    doctor_name = settings_data.doctor_name if settings_data and settings_data.doctor_name else current_user.full_name
    display_name = settings_data.display_name if settings_data and settings_data.display_name else doctor_name
    
    # ========================================================================
    # LOAD LOGO FROM BASE64 (DATABASE) - ONCE, REUSED ON ALL PAGES
    # ========================================================================
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
            
            # Set size (maintain aspect ratio)
            w, h = pil_img.size
            aspect = w / h
            logo_image.drawHeight = 0.8 * inch
            logo_image.drawWidth = 0.8 * inch * aspect
        except Exception as e:
            print(f"[WARNING] Error loading logo from Report Settings: {e}")
            logo_image = None
    
    
    def draw_header(canvas, doc):
        """
        Draw header on EVERY page
        Called automatically by ReportLab's PageTemplate
        
        CRITICAL: This function is called for EACH page automatically
        """
        canvas.saveState()
        
        # Get page dimensions
        page_width, page_height = letter
        
        # ====================================================================
        # DRAW LOGO (if available from Report Settings)
        # ====================================================================
        if logo_image:
            logo_image.drawOn(canvas, 0.75*inch, page_height - 1.3*inch)
        
        # ====================================================================
        # HOSPITAL NAME (from Report Settings)
        # ====================================================================
        canvas.setFont("Helvetica-Bold", 14)
        canvas.setFillColor(colors.HexColor(header_color))
        logo_offset = 2.2*inch if logo_image else 0.75*inch
        canvas.drawString(logo_offset, page_height - 0.9*inch, hospital_name.upper())
        
        # ====================================================================
        # REPORT TITLE
        # ====================================================================
        canvas.setFont("Helvetica", 11)
        canvas.setFillColor(colors.HexColor("#374151"))
        canvas.drawString(logo_offset, page_height - 1.1*inch, "Breast Cancer Detection – Medical Report")
        
        # ====================================================================
        # PATIENT INFO (right side)
        # ====================================================================
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        right_margin = page_width - 0.75*inch
        canvas.drawRightString(right_margin, page_height - 0.9*inch, f"Patient: {patient.full_name}")
        canvas.drawRightString(right_margin, page_height - 1.05*inch, f"MRN: {patient.mrn}")
        canvas.drawRightString(right_margin, page_height - 1.2*inch, f"Date: {datetime.now().strftime('%B %d, %Y')}")
        
        # ====================================================================
        # SEPARATOR LINE
        # ====================================================================
        canvas.setStrokeColor(colors.HexColor(header_color))
        canvas.setLineWidth(1.5)
        canvas.line(0.75*inch, page_height - 1.4*inch, page_width - 0.75*inch, page_height - 1.4*inch)
        
        canvas.restoreState()
    
    
    def draw_footer(canvas, doc):
        """
        Draw professional hospital-grade footer on EVERY page
        Called automatically by ReportLab's PageTemplate
        
        FOOTER STRUCTURE (4 clearly separated lines):
        LINE 1: Medical Disclaimer (center, small, gray)
        LINE 2: Hospital Contact Info (center, medium, dark gray)
        LINE 3: Generation Metadata (left) + Page Number (right)
        LINE 4: Electronic Signature Statement (center, italic, light gray)
        """
        canvas.saveState()
        
        # Get page dimensions
        page_width, page_height = letter
        
        # ====================================================================
        # FOOTER SEPARATOR LINE (top of footer area)
        # ====================================================================
        canvas.setStrokeColor(colors.HexColor("#D1D5DB"))
        canvas.setLineWidth(0.5)
        canvas.line(0.75*inch, 1.25*inch, page_width - 0.75*inch, 1.25*inch)
        
        # ====================================================================
        # LINE 1: MEDICAL DISCLAIMER (center aligned, small, gray)
        # ====================================================================
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        
        # Single line disclaimer (concise for professional reports)
        disclaimer_text = "Medical Disclaimer: This AI-generated report is for educational and research purposes only. It is not clinically validated and must be interpreted by licensed medical professionals."
        
        # Split into two lines if too long (max ~110 chars per line)
        if len(disclaimer_text) > 110:
            # Smart split at last space before 110 chars
            split_point = disclaimer_text[:110].rfind(' ')
            line1 = disclaimer_text[:split_point]
            line2 = disclaimer_text[split_point+1:]
            
            canvas.drawCentredString(page_width / 2, 1.15*inch, line1)
            canvas.drawCentredString(page_width / 2, 1.06*inch, line2)
            y_next = 0.94*inch
        else:
            canvas.drawCentredString(page_width / 2, 1.10*inch, disclaimer_text)
            y_next = 0.98*inch
        
        # ====================================================================
        # LINE 2: HOSPITAL CONTACT INFO (center aligned, medium, dark gray)
        # ====================================================================
        # Build contact line from Report Settings
        contact_parts = []
        if hospital_address:
            contact_parts.append(hospital_address)
        if hospital_contact:
            contact_parts.append(hospital_contact)
        
        # Add email/website if available (you can extend Report Settings model)
        # For now, use contact field which can contain multiple items
        
        if contact_parts:
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.HexColor("#374151"))
            contact_line = " | ".join(contact_parts)
            
            # Truncate if too long (max 100 chars for readability)
            if len(contact_line) > 100:
                contact_line = contact_line[:97] + "..."
            
            canvas.drawCentredString(page_width / 2, y_next - 0.08*inch, contact_line)
            y_next -= 0.16*inch
        else:
            y_next -= 0.08*inch
        
        # ====================================================================
        # LINE 3: GENERATION METADATA (left) + PAGE NUMBER (right)
        # ====================================================================
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        
        # Left side: Generated by + Generated on
        generated_by = f"Generated by: {display_name}"
        generated_on = f"Generated on: {datetime.now().strftime('%B %d, %Y at %H:%M')}"
        metadata_text = f"{generated_by} | {generated_on}"
        
        canvas.drawString(0.75*inch, y_next - 0.08*inch, metadata_text)
        
        # Right side: Page number
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(colors.HexColor("#374151"))
        page_num = canvas.getPageNumber()
        canvas.drawRightString(page_width - 0.75*inch, y_next - 0.08*inch, f"Page {page_num}")
        
        y_next -= 0.16*inch
        
        # ====================================================================
        # LINE 4: ELECTRONIC SIGNATURE STATEMENT (center, italic, light gray)
        # ====================================================================
        canvas.setFont("Helvetica-Oblique", 7)
        canvas.setFillColor(colors.HexColor("#9CA3AF"))
        canvas.drawCentredString(page_width / 2, y_next - 0.06*inch, "This report is electronically generated and valid without signature")
        
        canvas.restoreState()
    
    return draw_header, draw_footer


# =============================
#  MAIN PDF REPORT GENERATOR
# =============================
def generate_pdf_report(scan, patient, current_user, settings_data=None):
    """
    Generate a professional PDF medical report with REPEATING headers and footers
    
    CRITICAL CHANGES:
    - Uses BaseDocTemplate (not SimpleDocTemplate)
    - Headers/footers are layout elements (not content)
    - Headers/footers repeat on EVERY page automatically
    - All branding data pulled from Report Settings (database)
    
    Args:
        scan: Scan object from database (contains analysis results)
        patient: Patient object from database (contains patient info)
        current_user: User object (doctor/lab tech who generated the report)
        settings_data: ReportSettings object (REQUIRED for dynamic branding)
    
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
    # CREATE DOCUMENT WITH BASE DOCUMENT TEMPLATE (NOT SIMPLE DOC TEMPLATE)
    # ========================================================================
    
    # Create header and footer functions with hospital branding from Report Settings
    draw_header, draw_footer = create_header_footer_callbacks(settings_data, patient, current_user)
    
    # Create document with BaseDocTemplate (enables PageTemplate callbacks)
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
        """
        Combined callback for both header and footer
        Called automatically by ReportLab for EVERY page
        """
        draw_header(canvas, doc)
        draw_footer(canvas, doc)
    
    template = PageTemplate(id='main', frames=frame, onPage=on_page)
    doc.addPageTemplates([template])
    
    # ========================================================================
    # BUILD CONTENT (STORY) - Headers/footers are now AUTOMATIC
    # ========================================================================
    
    story = []
    styles = getSampleStyleSheet()
    
    # -------------------------
    # CUSTOM STYLES
    # -------------------------
    cover_title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1A237E'),
        alignment=TA_CENTER,
        spaceAfter=30,
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#424242'),
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1A237E'),
        spaceBefore=15,
        spaceAfter=10,
    )
    
    subheading_style = ParagraphStyle(
        'SubHeading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#303F9F'),
        spaceAfter=8,
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
    
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#C62828'),
        alignment=TA_JUSTIFY,
        leftIndent=15,
        rightIndent=15,
        spaceAfter=6,
    )
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )
    
    # ----------------------------------------
    # Helper: Convert PIL → ReportLab Image
    # ----------------------------------------
    def pil_to_rl_image(img_path, max_w=5.5 * inch, max_h=4.0 * inch):
        if not img_path or not os.path.exists(img_path):
            return None
        
        try:
            img = Image.open(img_path)
            rl_img = RLImage(img_path)
            
            # maintain aspect ratio
            w, h = img.size
            aspect = w / h
            
            if aspect > (max_w / max_h):  # width-dominant
                rl_img.drawWidth = max_w
                rl_img.drawHeight = max_w / aspect
            else:
                rl_img.drawHeight = max_h
                rl_img.drawWidth = max_h * aspect
            
            return rl_img
        except Exception as e:
            print(f"Error loading image {img_path}: {e}")
            return None
    
    # ----------------------------------------
    # Helper: Convert Base64 → ReportLab Image
    # ----------------------------------------
    def base64_to_rl_image(base64_str, max_w=2.0 * inch, max_h=1.5 * inch):
        if not base64_str:
            return None
        
        try:
            import base64
            # Remove data URL prefix if present
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]
            
            # Decode base64
            img_data = base64.b64decode(base64_str)
            img_buffer = io.BytesIO(img_data)
            img = Image.open(img_buffer)
            
            # Convert to ReportLab image
            img_buffer.seek(0)
            rl_img = RLImage(img_buffer)
            
            # Maintain aspect ratio
            w, h = img.size
            aspect = w / h
            
            if aspect > (max_w / max_h):  # width-dominant
                rl_img.drawWidth = max_w
                rl_img.drawHeight = max_w / aspect
            else:
                rl_img.drawHeight = max_h
                rl_img.drawWidth = max_h * aspect
            
            return rl_img
        except Exception as e:
            print(f"Error decoding base64 logo: {e}")
            return None
    
    # ============================
    #  COVER PAGE
    # ============================
    story.append(Spacer(1, 0.5 * inch))
    
    # Add logo if available from settings
    if settings_data and settings_data.logo_base64:
        logo_img = base64_to_rl_image(settings_data.logo_base64)
        if logo_img:
            story.append(logo_img)
            story.append(Spacer(1, 0.2 * inch))
    
    # Hospital/Clinic Name
    hospital_name = settings_data.hospital_name if settings_data and settings_data.hospital_name else "Medical Facility"
    story.append(Paragraph(hospital_name.upper(), cover_title_style))
    story.append(Spacer(1, 0.1 * inch))
    
    story.append(Paragraph("BREAST CANCER DETECTION<br/>MEDICAL REPORT", cover_title_style))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("AI-Powered Medical Imaging Analysis", subtitle_style))
    story.append(Spacer(1, 0.4 * inch))
    
    # Extract values with safe defaults
    prediction = scan.prediction or "Unknown"
    risk_level = scan.risk_level or "Unknown"
    confidence = scan.confidence_score or 0.0
    
    # COVER Summary Box
    cover_table_data = [
        [f"Classification: {prediction.upper()}"],
        [f"Risk Level: {risk_level.upper()}"],
        [f"Confidence: {confidence:.2f}%"],
    ]
    
    cover_table = Table(cover_table_data, colWidths=[5.5 * inch])
    cover_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#E8EAF6")),
                ('BOX', (0, 0), (-1, -1), 2, colors.HexColor("#1A237E")),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 14),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]
        )
    )
    
    story.append(cover_table)
    story.append(Spacer(1, 0.5 * inch))
    
    # Patient Information Box
    patient_info_data = [
        ['Patient Information', ''],
        ['Name:', patient.full_name or 'N/A'],
        ['MRN:', patient.mrn or 'N/A'],
        ['Date of Birth:', patient.date_of_birth.strftime('%B %d, %Y') if patient.date_of_birth else 'N/A'],
        ['Gender:', patient.gender.value if patient.gender else 'N/A'],
    ]
    
    patient_info_table = Table(patient_info_data, colWidths=[2 * inch, 3.5 * inch])
    patient_info_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A237E")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F5F5F5")),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('SPAN', (0, 0), (-1, 0)),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ]
        )
    )
    
    story.append(patient_info_table)
    story.append(Spacer(1, 0.3 * inch))
    
    story.append(
        Paragraph(
            f"<b>Report Generated:</b> {datetime.now().strftime('%B %d, %Y - %H:%M:%S')}",
            normal_style,
        )
    )
    
    # Use doctor name from settings if available
    doctor_name = settings_data.doctor_name if settings_data and settings_data.doctor_name else current_user.full_name
    story.append(
        Paragraph(
            f"<b>Generated By:</b> {doctor_name} ({current_user.role.value.replace('_', ' ').title()})",
            normal_style,
        )
    )
    story.append(PageBreak())
    
    # ============================
    # EXECUTIVE SUMMARY
    # ============================
    story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
    
    exec_text = f"""
    The AI-based deep learning model analyzed the uploaded breast tissue image and classified it as
    <b>{prediction.upper()}</b> with a confidence score of <b>{confidence:.2f}%</b>.
    This report includes detailed analysis results, risk assessment, and clinical recommendations.
    """
    
    story.append(Paragraph(exec_text, normal_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # ============================
    # SCAN INFORMATION
    # ============================
    story.append(Paragraph("SCAN INFORMATION", heading_style))
    
    scan_info_data = [
        ['Parameter', 'Value'],
        ['Scan Number', scan.scan_number or 'N/A'],
        ['Scan Date', scan.scan_date.strftime('%B %d, %Y %H:%M') if scan.scan_date else 'N/A'],
        ['Image Format', scan.image_format or 'N/A'],
        ['Image Size', f"{scan.image_size_bytes / 1024:.2f} KB" if scan.image_size_bytes else 'N/A'],
        ['Analysis Duration', f"{scan.analysis_duration_seconds:.2f} seconds" if scan.analysis_duration_seconds else 'N/A'],
        ['Status', scan.status.value.replace('_', ' ').title() if scan.status else 'N/A'],
    ]
    
    scan_info_table = Table(scan_info_data, colWidths=[2.5 * inch, 3.7 * inch])
    scan_info_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A237E")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#E8EAF6")),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]
        )
    )
    
    story.append(scan_info_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # ============================
    # PREDICTION RESULTS
    # ============================
    story.append(Paragraph("ANALYSIS RESULTS", heading_style))
    
    # Calculate probabilities
    benign_prob = 100 - confidence if prediction.lower() == "malignant" else confidence
    malignant_prob = confidence if prediction.lower() == "malignant" else 100 - confidence
    
    prediction_data = [
        ['Parameter', 'Value'],
        ['Classification', prediction.upper()],
        ['Risk Assessment', risk_level.upper()],
        ['Confidence Score', f"{confidence:.2f}%"],
        ['Benign Probability', f"{benign_prob:.2f}%"],
        ['Malignant Probability', f"{malignant_prob:.2f}%"],
    ]
    
    prediction_table = Table(prediction_data, colWidths=[2.5 * inch, 3.7 * inch])
    prediction_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A237E")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#E8EAF6")),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]
        )
    )
    
    story.append(prediction_table)
    
    # Add doctor's notes if available
    if scan.doctor_notes:
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Doctor's Notes:", subheading_style))
        story.append(Paragraph(scan.doctor_notes, normal_style))
    
    # Add radiologist's notes if available
    if scan.radiologist_notes:
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Radiologist's Notes:", subheading_style))
        story.append(Paragraph(scan.radiologist_notes, normal_style))
    
    story.append(PageBreak())
    
    # =============================
    # VISUAL ANALYSIS
    # =============================
    story.append(Paragraph("VISUAL ANALYSIS", heading_style))
    
    # 1. Original Image
    story.append(Paragraph("1. Original Medical Image", subheading_style))
    original_img = pil_to_rl_image(scan.image_path)
    if original_img:
        story.append(original_img)
    else:
        story.append(Paragraph("Original image not available.", normal_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # 2. Heatmap Overlay
    if scan.overlay_path and os.path.exists(scan.overlay_path):
        story.append(Paragraph("2. Grad-CAM Heatmap Overlay", subheading_style))
        overlay_img = pil_to_rl_image(scan.overlay_path)
        if overlay_img:
            story.append(overlay_img)
        story.append(Spacer(1, 0.2 * inch))
    
    # 3. Heatmap Only
    if scan.heatmap_path and os.path.exists(scan.heatmap_path):
        story.append(Paragraph("3. Heatmap (Activation Map)", subheading_style))
        heatmap_img = pil_to_rl_image(scan.heatmap_path)
        if heatmap_img:
            story.append(heatmap_img)
        story.append(Spacer(1, 0.2 * inch))
    
    story.append(PageBreak())
    
    # ============================
    # IMAGE STATISTICS
    # ============================
    if scan.image_statistics_json:
        story.append(Paragraph("IMAGE STATISTICS", heading_style))
        
        stats = scan.image_statistics_json
        stats_data = [
            ['Property', 'Value'],
        ]
        
        # Add available statistics
        if 'mean' in stats or 'mean_intensity' in stats:
            stats_data.append(['Mean Intensity', f"{stats.get('mean', stats.get('mean_intensity', 0)):.2f}"])
        if 'std' in stats or 'std_intensity' in stats:
            stats_data.append(['Std. Deviation', f"{stats.get('std', stats.get('std_intensity', 0)):.2f}"])
        if 'min' in stats or 'min_intensity' in stats:
            stats_data.append(['Minimum Pixel', f"{stats.get('min', stats.get('min_intensity', 0)):.0f}"])
        if 'max' in stats or 'max_intensity' in stats:
            stats_data.append(['Maximum Pixel', f"{stats.get('max', stats.get('max_intensity', 0)):.0f}"])
        
        if len(stats_data) > 1:  # Only create table if we have data
            stats_table = Table(stats_data, colWidths=[2.5 * inch, 3.7 * inch])
            stats_table.setStyle(
                TableStyle(
                    [
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A237E")),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#E8EAF6")),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ]
                )
            )
            story.append(stats_table)
            story.append(PageBreak())
    
    # ============================
    # CLINICAL RECOMMENDATIONS
    # ============================
    story.append(Paragraph("CLINICAL RECOMMENDATIONS", heading_style))
    
    if prediction.lower() == "malignant" or risk_level.lower() in ["high", "moderate"]:
        recs = [
            "Consult an oncologist or radiologist immediately for further evaluation.",
            "Request additional diagnostic imaging (mammography, ultrasound, or MRI).",
            "Consider biopsy for definitive diagnosis.",
            "Schedule urgent follow-up appointments.",
            "Share this report with your healthcare provider.",
            "Discuss potential treatment options with medical professionals.",
        ]
    else:
        recs = [
            "Continue routine breast cancer screening as recommended.",
            "Maintain regular follow-ups with your healthcare provider.",
            "Monitor for any changes in symptoms or physical examination.",
            "Keep previous medical imaging records for comparison.",
            "Maintain a healthy lifestyle and follow preventive care guidelines.",
        ]
    
    for r in recs:
        story.append(Paragraph("• " + r, bullet_style))
    
    story.append(PageBreak())
    
    # ============================
    # DISCLAIMER
    # ============================
    disclaimer_text = """
    ⚠ <b>IMPORTANT MEDICAL DISCLAIMER</b><br/><br/>
    This AI system is for <b>educational and research purposes only</b>.
    It is NOT clinically validated and must NOT be used as a substitute for professional medical diagnosis,
    treatment decisions, or healthcare evaluation. This report should only be interpreted by licensed medical
    professionals. Always consult qualified physicians, radiologists, and oncologists for diagnosis, 
    imaging interpretation, and treatment planning.
    """
    
    disclaimer_box = Table(
        [[Paragraph(disclaimer_text, disclaimer_style)]],
        colWidths=[6.5 * inch],
    )
    disclaimer_box.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFEBEE")),
                ('BOX', (0, 0), (-1, -1), 2, colors.HexColor("#C62828")),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ]
        )
    )
    
    story.append(disclaimer_box)
    story.append(Spacer(1, 0.4 * inch))
    
    # ============================
    # FOOTER
    # ============================
    # Use custom footer text if available from settings
    if settings_data and settings_data.footer_text:
        story.append(
            Paragraph(
                settings_data.footer_text,
                footer_style,
            )
        )
    else:
        story.append(
            Paragraph(
                "Generated by AI-Powered Breast Cancer Detection System",
                footer_style,
            )
        )
        story.append(
            Paragraph(
                f"© {datetime.now().year} — For Medical Professional Use Only",
                footer_style,
            )
        )
    
    # ============================
    # BUILD PDF
    # ============================
    try:
        doc.build(story)
        print(f"[SUCCESS] PDF report generated: {report_path}")
        return report_path
    except Exception as e:
        print(f"[ERROR] Failed to generate PDF: {e}")
        raise


# =============================
#  LEGACY PDF REPORT GENERATOR (For backward compatibility)
# =============================
def generate_report_pdf(
    result,
    probability,
    risk_level,
    benign_prob,
    malignant_prob,
    stats,
    image_size,
    file_format,
    original_image,
    overlay_image,
    heatmap_only,
    bbox_image,
    confidence,
):
    """
    Full professional PDF report generator — FASTAPI READY VERSION
    """

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )

    story = []
    styles = getSampleStyleSheet()

    # -------------------------
    # CUSTOM STYLES
    # -------------------------
    cover_title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1A237E'),
        alignment=TA_CENTER,
        spaceAfter=30,
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#424242'),
        alignment=TA_CENTER,
        spaceAfter=20,
    )

    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1A237E'),
        spaceBefore=15,
        spaceAfter=10,
    )

    subheading_style = ParagraphStyle(
        'SubHeading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#303F9F'),
        spaceAfter=8,
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

    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#C62828'),
        alignment=TA_JUSTIFY,
        leftIndent=15,
        rightIndent=15,
        spaceAfter=6,
    )

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )

    # ----------------------------------------
    # Helper: Convert PIL → ReportLab Image
    # ----------------------------------------
    def pil_to_rl_image(img, max_w=5.5 * inch, max_h=4.0 * inch):
        if img is None:
            return None
        if isinstance(img, np.ndarray):
            img = Image.fromarray(img.astype('uint8'))

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)

        rl_img = RLImage(buf)

        # maintain aspect ratio
        w, h = img.size
        aspect = w / h

        if aspect > (max_w / max_h):  # width-dominant
            rl_img.drawWidth = max_w
            rl_img.drawHeight = max_w / aspect
        else:
            rl_img.drawHeight = max_h
            rl_img.drawWidth = max_h * aspect

        return rl_img

    # ============================
    #  COVER PAGE
    # ============================
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("BREAST CANCER DETECTION<br/>ANALYSIS REPORT", cover_title_style))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("AI-Powered Medical Imaging Report", subtitle_style))
    story.append(Spacer(1, 0.4 * inch))

    # COVER Summary Box
    cover_table_data = [
        [f"Classification: {result}"],
        [f"Risk Level: {risk_level}"],
        [f"Confidence: {probability:.2f}%"],
    ]

    cover_table = Table(cover_table_data, colWidths=[5.5 * inch])
    cover_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#E8EAF6")),
                ('BOX', (0, 0), (-1, -1), 2, colors.HexColor("#1A237E")),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 14),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]
        )
    )

    story.append(cover_table)
    story.append(Spacer(1, 1 * inch))
    story.append(
        Paragraph(
            f"<b>Report Generated:</b> {datetime.now().strftime('%B %d, %Y - %H:%M:%S')}",
            normal_style,
        )
    )
    story.append(PageBreak())

    # ============================
    # EXECUTIVE SUMMARY
    # ============================
    story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))

    exec_text = f"""
    The AI-based deep learning model analyzed the uploaded breast tissue image and classified it as
    <b>{result}</b> with a confidence score of <b>{probability:.2f}%</b>.
    This report includes detailed visualization insights using Grad-CAM, technical image statistics,
    risk assessment, and clinical recommendations.
    """

    story.append(Paragraph(exec_text, normal_style))
    story.append(Spacer(1, 0.3 * inch))

    # ============================
    # PREDICTION TABLE
    # ============================
    story.append(Paragraph("PREDICTION RESULTS", heading_style))

    prediction_data = [
        ['Parameter', 'Value'],
        ['Classification', result],
        ['Risk Assessment', risk_level],
        ['Confidence Score', f"{probability:.2f}%"],
        ['Benign Probability', f"{benign_prob:.2f}%"],
        ['Malignant Probability', f"{malignant_prob:.2f}%"],
        ['Image Format', file_format],
        ['Dimensions', f"{image_size[0]} × {image_size[1]} pixels"],
        ['Raw Model Output', f"{confidence:.6f}"],
    ]

    prediction_table = Table(prediction_data, colWidths=[2.2 * inch, 4 * inch])
    prediction_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A237E")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#E8EAF6")),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]
        )
    )

    story.append(prediction_table)
    story.append(PageBreak())

    # =============================
    # VISUAL ANALYSIS (4 IMAGES)
    # =============================

    story.append(Paragraph("VISUAL ANALYSIS", heading_style))

    # 1. Original Image
    story.append(Paragraph("1. Original Medical Image", subheading_style))
    story.append(pil_to_rl_image(original_image))
    story.append(Spacer(1, 0.2 * inch))

    # 2. Heatmap Overlay
    story.append(Paragraph("2. Grad-CAM Heatmap Overlay", subheading_style))
    if overlay_image:
        story.append(pil_to_rl_image(overlay_image))
    story.append(Spacer(1, 0.2 * inch))

    # 3. Heatmap Only
    story.append(Paragraph("3. Heatmap (Standalone Activation Map)", subheading_style))
    if heatmap_only:
        story.append(pil_to_rl_image(heatmap_only))
    story.append(Spacer(1, 0.2 * inch))

    # 4. BBox regions
    story.append(Paragraph("4. Suspicious Regions (Bounding Boxes)", subheading_style))
    if bbox_image:
        story.append(pil_to_rl_image(bbox_image))
    else:
        story.append(Paragraph("No high-activation regions detected above threshold.", normal_style))

    story.append(PageBreak())

    # ============================
    # IMAGE STATISTICS
    # ============================
    story.append(Paragraph("IMAGE STATISTICS", heading_style))

    stats_data = [
        ['Property', 'Value'],
        ['Mean Intensity', f"{stats['mean_intensity']:.2f}"],
        ['Std. Deviation', f"{stats['std_intensity']:.2f}"],
        ['Minimum Pixel', f"{stats['min_intensity']:.0f}"],
        ['Maximum Pixel', f"{stats['max_intensity']:.0f}"],
        ['Median Pixel', f"{stats['median_intensity']:.2f}"],
        ['Brightness Index', f"{stats['brightness']:.2f}%"],
        ['Contrast Index', f"{stats['contrast']:.2f}%"],
    ]

    stats_table = Table(stats_data, colWidths=[2.5 * inch, 3.7 * inch])
    stats_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A237E")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#E8EAF6")),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]
        )
    )

    story.append(stats_table)
    story.append(PageBreak())

    # ============================
    # CLINICAL RECOMMENDATIONS
    # ============================
    story.append(Paragraph("CLINICAL RECOMMENDATIONS", heading_style))

    if confidence > 0.5:
        recs = [
            "Consult an oncologist or radiologist immediately.",
            "Request additional diagnostic imaging and biopsy.",
            "Schedule urgent follow-up appointments.",
            "Share this report with medical professionals.",
            "Discuss potential treatment options.",
        ]
    else:
        recs = [
            "Continue routine breast cancer screening.",
            "Maintain follow-ups with healthcare providers.",
            "Monitor for any changes in symptoms.",
            "Keep previous medical imaging for comparison.",
        ]

    for r in recs:
        story.append(Paragraph("• " + r, bullet_style))

    story.append(PageBreak())

    # ============================
    # DISCLAIMER
    # ============================
    disclaimer_text = """
    ⚠ <b>IMPORTANT MEDICAL DISCLAIMER</b><br/><br/>
    This AI system is for <b>educational and research use only</b>.
    It is NOT clinically validated and must NOT be used as a substitute for real medical diagnosis,
    treatment decisions, or professional healthcare evaluation. Always consult licensed medical
    professionals for diagnosis, imaging interpretation, and treatment.
    """

    disclaimer_box = Table(
        [[Paragraph(disclaimer_text, disclaimer_style)]],
        colWidths=[6.5 * inch],
    )
    disclaimer_box.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFEBEE")),
                ('BOX', (0, 0), (-1, -1), 2, colors.HexColor("#C62828")),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ]
        )
    )

    story.append(disclaimer_box)
    story.append(Spacer(1, 0.4 * inch))

    # ============================
    # FOOTER
    # ============================
    story.append(
        Paragraph(
            "Generated by AI-Powered Breast Cancer Detection System",
            footer_style,
        )
    )
    story.append(
        Paragraph(
            f"© {datetime.now().year} — Educational Use Only",
            footer_style,
        )
    )

    # ============================
    # FINAL BUILD
    # ============================
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
