# ===============================
# send_email.py
# ===============================

import os
import smtplib
from email.message import EmailMessage
from datetime import datetime

# Function to send email with PDF attachment via SMTP
def send_email_smtp(
    smtp_user,
    smtp_password,
    smtp_server,
    smtp_port,
    receiver_email,
    report_path,
): 

    # Compose email
    SENDER_NAME = "Automated Portfolio Analytics System" # Customize sender name
    msg = EmailMessage() # Create email message object
    msg["From"] = f"{SENDER_NAME} <{smtp_user}>" # Set sender
    msg["To"] = receiver_email # Set recipient
    msg["Subject"] = f"Portfolio Report: {datetime.now().strftime('%Y-%m-%d')} (UTC)" # Set subject
    msg.set_content( 
        """
Hello,

Please find attached the latest automated portfolio performance & risk report.

This report includes:
• Portfolio-level performance and risk metrics
• Asset-level KPIs
• Price, return, drawdown, volatility, and correlation visualizations

This email was generated automatically.

Best regards,
Automation Team
"""
    ) 
    # Attach PDF report
    if not report_path or not os.path.exists(report_path): 
        raise FileNotFoundError("PDF report not found. Email not sent.") # Error if report missing
    with open(report_path, "rb") as f:
        file_data = f.read() # Read PDF file data
        file_name = os.path.basename(report_path) # Get file name

    # Attach PDF to email
    msg.add_attachment(
        file_data,
        maintype="application",
        subtype="pdf",
        filename=file_name,
    ) 
    # Send email via SMTP
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls() # Secure connection
        server.login(smtp_user, smtp_password) # Login to SMTP server
        server.send_message(msg) # Send email

    print("Email sent successfully.")   