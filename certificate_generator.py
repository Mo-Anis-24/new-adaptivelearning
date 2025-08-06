from fpdf import FPDF
from datetime import datetime
import os
import uuid
import random
import csv
import sqlite3

class CertificateGenerator:
    def __init__(self):
        self.title = "BROADER AI"
        self.tagline = "TOWARDS AUTOMATION"
        self.cert_title = "CERTIFICATE OF ACHIEVEMENT"
        self.signature_path = os.path.join('static', 'images', 'broderai_signature.jpg')
        self.issuer_name = "MOHAMMAD SOAEB RATHOD"
        self.issuer_title = "FOUNDER"
        self.cert_csv = 'certificates.csv'
        self.db_path = 'instance/adaptive_learning.db'

    def generate_unique_series_id(self):
        """Generate a unique 10-digit series ID"""
        while True:
            series_id = str(random.randint(10**9, 10**10 - 1))
            if not self.series_id_exists(series_id):
                return series_id

    def series_id_exists(self, series_id):
        """Check if series ID already exists in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM certificates WHERE series_id = ?", (series_id,))
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except:
            return False

    def save_certificate_to_db(self, series_id, user_name, subject, issue_date, expiry_date, score):
        """Save certificate details to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
         
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS certificates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    series_id TEXT UNIQUE NOT NULL,
                    user_name TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    issue_date TEXT NOT NULL,
                    expiry_date TEXT NOT NULL,
                    score INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
         
            cursor.execute('''
                INSERT INTO certificates (series_id, user_name, subject, issue_date, expiry_date, score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (series_id, user_name, subject, issue_date, expiry_date, score))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving certificate: {e}")
            return False

    def verify_certificate(self, series_id):
        """Verify certificate by series ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT series_id, user_name, subject, issue_date, expiry_date, score
                FROM certificates WHERE series_id = ?
            ''', (series_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'series_id': result[0],
                    'user_name': result[1],
                    'subject': result[2],
                    'issue_date': result[3],
                    'expiry_date': result[4],
                    'score': result[5],
                    'valid': True
                }
            else:
                return {'valid': False, 'message': 'Certificate not found'}
        except Exception as e:
            return {'valid': False, 'message': f'Error: {e}'}

    def generate_certificate(self, user_name, subject, score, date=None, output_path=None):
        if date is None:
            date = datetime.now().strftime('%d %b %Y')
        issue_date = datetime.now().strftime('%d %b %Y')
        expiry_date = (datetime.now().replace(year=datetime.now().year + 2)).strftime('%d %b %Y')
        
        # Generate unique series ID
        series_id = self.generate_unique_series_id()

        # Create PDF
        pdf = FPDF('L', 'mm', 'A4')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        page_width = 297
        page_height = 210

        # Draw white background
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(0, 0, page_width, page_height, 'F')

        # Add certificate template image
        certificate_frame_path = os.path.join('static', 'images', 'cc2222.png')
        if os.path.exists(certificate_frame_path):
            pdf.image(certificate_frame_path, x=0, y=0, w=page_width, h=page_height)
        else:
            print(f"Warning: Certificate template not found at {certificate_frame_path}")

        # Add certificate details
        self.add_certificate_details(pdf, series_id, user_name, subject, issue_date, expiry_date, score)

        # Save to database
        self.save_certificate_to_db(series_id, user_name, subject, issue_date, expiry_date, score)

        # Output
        if output_path:
            pdf.output(output_path)
            return output_path
        else:
            return pdf.output(dest='S').encode('latin1')

    def add_certificate_details(self, pdf, series_id, user_name, subject, issue_date, expiry_date, score):
        """Add certificate details to the PDF"""
        page_width = 297
        page_height = 210
        
        # Safe margins for text placement
        safe_margin_x = 35
        safe_margin_top = 40
        safe_margin_bottom = 40
        content_width = page_width - 2 * safe_margin_x

        # Certificate title
        pdf.set_font('Arial', 'B', 16)
        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(safe_margin_x, safe_margin_top + 35)
        pdf.cell(content_width, 10, "OF ACHIEVEMENT", ln=True, align='C')

        # Recipient name
        pdf.set_font('Times', 'B', 30)
        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(safe_margin_x, safe_margin_top + 55)
        pdf.cell(content_width, 20, user_name.upper(), ln=True, align='C')

        # Achievement text
        pdf.set_font('Arial', '', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(safe_margin_x, safe_margin_top + 75)
        pdf.cell(content_width, 8, "Has Successfully Completed All The Requirements To Be Recognized As a", ln=True, align='C')

        # Subject/Certification area
        pdf.set_font('Times', 'B', 20)
        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(safe_margin_x, safe_margin_top + 90)
        pdf.cell(content_width, 12, subject, ln=True, align='C')

        # Certificate details (bottom left)
        pdf.set_font('Arial', '', 8)
        pdf.set_text_color(80, 80, 80)
        
        details_x = page_width - 230
        details_y = page_height - 35
        
        pdf.set_xy(details_x, details_y)
        pdf.cell(100, 4, f'Series ID: {series_id}', ln=1, align='L')
        pdf.set_x(details_x)
        pdf.cell(100, 4, f'Issue Date: {issue_date}', ln=1, align='L')
        pdf.set_x(details_x)
        pdf.cell(100, 4, f'Expiration Date: {expiry_date}', ln=1, align='L')
        pdf.set_x(details_x)
        pdf.cell(100, 4, f'Certified As: {user_name}', ln=1, align='L')
        