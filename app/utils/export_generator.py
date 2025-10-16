import io
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import send_file

def generate_export(profile_data, format_type="csv"):
    """
    Generate downloadable file from profile JSON.
    Supports CSV or PDF.
    """
    if format_type == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Field", "Value"])
        writer.writerow(["Name", profile_data.get("name", "")])
        writer.writerow(["Current Title", profile_data.get("current_title", "")])
        writer.writerow(["Sector", profile_data.get("sector", "")])
        writer.writerow(["Years Experience", profile_data.get("years_experience", 0)])
        writer.writerow([])
        writer.writerow(["Experiences"])
        writer.writerow(["Company", "Role", "Duration", "Start Date", "End Date"])
        
        for exp in profile_data.get("experiences", []):
            writer.writerow([
                exp.get("company", ""),
                exp.get("role", ""),
                exp.get("duration", ""),
                exp.get("start_date", ""),
                exp.get("end_date", "")
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()), 
            mimetype='text/csv', 
            as_attachment=True, 
            download_name='profile.csv'
        )
    
    elif format_type == "pdf":
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        y = 750
        
        # Title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, y, "Profile Information")
        y -= 30
        
        # Basic info
        p.setFont("Helvetica", 12)
        p.drawString(100, y, f"Name: {profile_data.get('name', '')}")
        y -= 20
        p.drawString(100, y, f"Current Title: {profile_data.get('current_title', '')}")
        y -= 20
        p.drawString(100, y, f"Sector: {profile_data.get('sector', '')}")
        y -= 20
        p.drawString(100, y, f"Years Experience: {profile_data.get('years_experience', 0)}")
        y -= 40
        
        # Experiences
        p.setFont("Helvetica-Bold", 14)
        p.drawString(100, y, "Experiences:")
        y -= 30
        p.setFont("Helvetica", 12)
        
        for exp in profile_data.get("experiences", []):
            p.drawString(100, y, f"Company: {exp.get('company', '')}")
            y -= 20
            p.drawString(100, y, f"Role: {exp.get('role', '')}")
            y -= 20
            p.drawString(100, y, f"Duration: {exp.get('duration', '')}")
            y -= 20
            p.drawString(100, y, f"Start: {exp.get('start_date', '')} - End: {exp.get('end_date', '')}")
            y -= 30
            
            if y < 50:
                p.showPage()
                y = 750
                p.setFont("Helvetica", 12)
        
        p.save()
        buffer.seek(0)
        return send_file(
            buffer, 
            mimetype='application/pdf', 
            as_attachment=True, 
            download_name='profile.pdf'
        )