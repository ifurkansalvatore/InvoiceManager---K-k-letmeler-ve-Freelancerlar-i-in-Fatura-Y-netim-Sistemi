from flask import render_template
import weasyprint
from io import BytesIO

def generate_pdf(invoice):
    """
    Generates a PDF file from an invoice
    
    Args:
        invoice: The Invoice object
        
    Returns:
        BytesIO: PDF file as bytes
    """
    # Render the invoice template to HTML
    html = render_template('invoice_pdf_template.html', invoice=invoice)
    
    # Create a BytesIO buffer
    pdf_file = BytesIO()
    
    # Generate the PDF
    weasyprint.HTML(string=html).write_pdf(pdf_file)
    
    # Reset the buffer position to the beginning
    pdf_file.seek(0)
    
    return pdf_file.getvalue()
