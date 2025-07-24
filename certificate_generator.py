from fpdf import FPDF
from datetime import datetime
import os
import uuid
import random
import csv
from flask import current_app

class CertificateGenerator:
    def __init__(self):
        self.title = "Broader AI"
        self.cert_title = "Broader AI Certified"
        self.signature_path = os.path.join('static', 'images', 'broderai_signature.jpg')
        self.issuer = "Broader AI"
        self.cert_csv = 'certificates.csv'

    def generate_certificate(self, user_name, subject, score, date=None, output_path=None):
        if date is None:
            date = datetime.now().strftime('%d %b %Y')
        issue_date = datetime.now().strftime('%d %b %Y')
        expiry_date = (datetime.now().replace(year=datetime.now().year + 2)).strftime('%d %b %Y')
        # Generate a random 10-digit numeric Series ID
        cert_id = str(random.randint(10**9, 10**10 - 1))

        pdf = FPDF('L', 'mm', 'A4')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        page_width = 297
        page_height = 210

        # Draw pure white background
        pdf.set_fill_color(255, 255, 255)  # pure white
        pdf.rect(0, 0, page_width, page_height, 'F')

        # Draw a thin border around the certificate
        border_color = (30, 144, 255)  
        pdf.set_draw_color(*border_color)
        border_margin = 6  # mm from edge
        border_width = page_width - 2 * border_margin
        border_height = page_height - 2 * border_margin
        pdf.set_line_width(1)
        pdf.rect(border_margin, border_margin, border_width, border_height)

        # Header - Broader AI logo instead of text
        logo_path = os.path.join(current_app.root_path, 'static', 'images', 'broaderai_logo.png')
        logo_w = 60  # width in mm
        logo_h = 25  # height in mm (adjust as needed)
        # Center the logo
        if os.path.exists(logo_path):
            logo_x = (page_width - logo_w) / 2
            pdf.image(logo_path, x=logo_x, y=10, w=logo_w, h=logo_h)
            pdf.ln(logo_h + 5)
        else:
            pdf.set_font('Arial', 'B', 32)
            pdf.set_text_color(30, 144, 255)  # Dodger Blue
            pdf.cell(0, 20, self.title, ln=True, align='C')
            pdf.ln(5)

        # Subtitle
        pdf.set_font('Arial', '', 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, 'This acknowledges that', ln=True, align='C')
        pdf.ln(2)

        # User Name
        pdf.set_font('Arial', 'B', 28)
        pdf.cell(0, 15, user_name, ln=True, align='C')
        pdf.ln(2)

        # Achievement text (updated as per request)
        pdf.set_font('Arial', '', 16)
        pdf.cell(0, 10, 'Has Successfully Completed All The Requirements To Be Recognized As a', ln=True, align='C')
        pdf.ln(2)

        # Certification Title
        pdf.set_font('Arial', 'B', 22)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 15, self.cert_title, ln=True, align='C')
        pdf.ln(2)

        # Subject as Certification
        pdf.set_font('Arial', '', 20)
        pdf.cell(0, 12, subject, ln=True, align='C')
        pdf.ln(20)  # Extra space before footer/signature

      
        # Footer details (ID, dates)
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(80, 80, 80)
        pdf.set_y(-55)
        pdf.cell(0, 6, f'Series ID: {cert_id}', ln=1, align='L')
        pdf.cell(0, 6, f'Issue Date: {issue_date}', ln=1, align='L')
        pdf.cell(0, 6, f'Expiration Date: {expiry_date}', ln=1, align='L')
        pdf.cell(0, 6, f'Certified As: {user_name}', ln=1, align='L')

        # Signature image and issuer text (bottom right, perfect vertical stack)
        pdf.set_auto_page_break(auto=False)
        margin_right = 20
        margin_bottom = 20
        sig_w = 60
        sig_h = 20  # approx height in mm, adjust as needed
        sig_x = page_width - sig_w - margin_right
        sig_y = page_height - sig_h - margin_bottom - 15  # 15mm above bottom
        # Prefer transparent PNG signature if available
        signature_png_path = os.path.join(current_app.root_path, 'static', 'images', 'broderai_signature.png')
        if os.path.exists(signature_png_path):
            signature_abs_path = signature_png_path
        else:
            signature_abs_path = os.path.join(current_app.root_path, self.signature_path)

        if os.path.exists(signature_abs_path):
            pdf.image(signature_abs_path, x=sig_x, y=sig_y, w=sig_w, h=sig_h)
            # CEO text just below signature, with 4mm gap
            ceo_text_y = sig_y + sig_h + 4
            pdf.set_xy(sig_x, ceo_text_y)
            pdf.set_font('Arial', '', 12)
            pdf.cell(sig_w, 8, "CEO, Broader AI", align='R')
        else:
            pdf.set_xy(sig_x, sig_y)
            pdf.set_font('Arial', 'I', 10)
            pdf.cell(sig_w, 10, '[Signature not found]', align='R')
            ceo_text_y = sig_y + sig_h + 4
            pdf.set_xy(sig_x, ceo_text_y)
            pdf.set_font('Arial', '', 12)
            pdf.cell(sig_w, 8, "CEO, Broader AI", align='R')

        # Save certificate details to CSV for verification
        cert_row = [cert_id, user_name, subject, issue_date, expiry_date]
        file_exists = os.path.isfile(self.cert_csv)
        with open(self.cert_csv, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(['series_id', 'user_name', 'subject', 'issue_date', 'expiry_date'])
            writer.writerow(cert_row)

        # Output
        if output_path:
            pdf.output(output_path)
            return output_path
        else:
            return pdf.output(dest='S').encode('latin1')