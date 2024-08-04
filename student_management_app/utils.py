from datetime import datetime
from io import BytesIO
from venv import logger
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from django.contrib.staticfiles import finders
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

from student_management_app.models import Certificat, Project, Students





def get_project_title(queryset):
    """Extract the title from a QuerySet."""
    if queryset.exists():
        return queryset.first().title  # Replace 'title' with the actual field name
    return ""

def wrap_text(text, canvas, max_width):
    """
    Wrap text to fit within a specified width on the canvas.
    
    Args:
        text (str): The text to wrap.
        canvas (canvas.Canvas): The ReportLab canvas object.
        max_width (float): The maximum width in points for the text.
    
    Returns:
        list: A list of wrapped text lines.
    """
    lines = []
    words = text.split()
    line = ""
    
    for word in words:
        test_line = f"{line} {word}".strip()
        if canvas.stringWidth(test_line, "Helvetica-Bold", 12) <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    
    if line:
        lines.append(line)
    
    return lines

def generate_certificate(student_name, ppr, reference, project_title, trainer_name, include_signature=False):
    buffer = BytesIO()
    
    # Define the A4 page size and set it to landscape
    page_size = landscape(A4)
    width, height = page_size
    
    c = canvas.Canvas(buffer, pagesize=page_size)
    
    # Load and position the background image
    background_path = finders.find('media/image.png')  # Path to your background image
    c.drawImage(background_path, 0, 0, width=width, height=height, mask='auto')

    # Define rounded rectangle parameters
    border_margin = 20  # Margin between border and page edge

    # Draw a rounded rectangle around the content
    c.setStrokeColor(HexColor('#2a8c3e'))  # Dark green color for the border
    c.setLineWidth(2)  # Line width
    
    # Draw rounded rectangle

    # Get current and previous year
    current_year = datetime.now().year
    previous_year = current_year - 1
    
    # Set date_start and date_end
    date_start = f"01 novembre {previous_year}"
    date_end = f"31 mars {current_year}"
    
    # Get issue date in the required format
    issue_date = datetime.now().strftime("%d/%m/%Y")
    
    # Certificate body
    c.setFont("Helvetica", 12)  # Keep body text size as it is
    left_margin = border_margin + 60  # Adjust this value to control the left margin

    # Adjust positions to add space after the branch image
    body_start_y = height - 180
    
    c.drawString(left_margin, body_start_y - 40, "Nous attestons par la présente que :")
    c.drawString(left_margin, body_start_y - 60, f"Nom & Prénom            : {student_name}")
    c.drawString(left_margin, body_start_y - 80, f"PPR                             : {ppr}")
    c.drawString(left_margin, body_start_y - 100, f"AREF                           : {reference}")
    
    c.drawString(left_margin, body_start_y - 140, "A suivi avec assiduité au Centre Maroco Coréen de Formation en TICE la formation portant sur :")
    
    c.setFont("Helvetica-Bold", 12)  # Keep project title size as it is
    wrapped_lines = wrap_text(f"<< {project_title} >>", c, width - 4 * border_margin)
    project_title_y = body_start_y - 170
    for line in wrapped_lines:
        c.drawCentredString(width / 2, project_title_y, line)
        project_title_y -= 20  # Adjust line spacing as needed
    
    c.setFont("Helvetica", 12)  # Keep body text size as it is
    c.drawCentredString(width / 2, project_title_y - 40, f"Du {date_start} au {date_end}.")
    
    c.drawString(left_margin, project_title_y - 70, f"{student_name} a satisfait aux modalités de l'évaluation en soutenant son projet de fin de formation sous le titre de")
    c.drawString(left_margin, project_title_y - 90, f"encadré par son formateur {trainer_name}.")
    
    # Footer
    c.setFont("Helvetica", 8)
    footer_text = (
        "Ministère de l'Éducation Nationale, du Préscolaire et des Sports Direction du programme GENIE siège central du Ministère "
        "Bab-Rouah-Rabat  Tel : 0537687271  Fax : 05 37 67 72 72 Portail : www.taalimtice.ma"
    )
    
    # Position footer text just above the bottom border
    footer_y_position = 10  # Adjust this value if necessary to ensure footer is within the content area
    c.drawCentredString(width / 2, footer_y_position, footer_text)

    # Draw the signature line
    signature_text_y = project_title_y - 100
    c.setFont("Helvetica", 12)  # Keep signature text size as it is
    c.drawString(left_margin + 480, signature_text_y, "Signature:")

    if include_signature:
        # Add the signature image if include_signature is True
        signature_path = finders.find('media/signature.png')  # Path to your signature image
        # Adjust image position to be under the signature text
        c.drawImage(signature_path, left_margin + 500, signature_text_y - 80, width=200, height=100, mask='auto')

    c.save()
    
    buffer.seek(0)
    return buffer




