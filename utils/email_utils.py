"""
Email Utilities
Handles sending emails via SendGrid or printing to console if API key is missing.
"""
import os
import streamlit as st
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_share_email(to_email: str, file_name: str, share_link: str, access_code: str) -> bool:
    """
    Send an email with the document link and access code. 
    If SENDGRID_API_KEY is not set, prints to console (Mock Mode).
    """
    api_key = os.getenv("SENDGRID_API_KEY") or st.secrets.get("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL") or st.secrets.get("SENDGRID_FROM_EMAIL") or "no-reply@example.com"
    
    # HTML Content
    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
        <h2>📄 Document Shared With You</h2>
        <p>A secure document <strong>"{file_name}"</strong> has been shared with you.</p>
        
        <p>Click the button below to view it:</p>
        <a href="{share_link}" style="background-color: #FF4B4B; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">View Document</a>
        
        <p style="margin-top: 20px;">Use this <strong>Access Code</strong> to unlock it:</p>
        <h1 style="background-color: #f1f3f6; padding: 10px; display: inline-block; letter-spacing: 5px;">{access_code}</h1>
        
        <p style="font-size: 12px; color: #666; margin-top: 30px;">
        This link expires in 7 days. If you did not expect this, please ignore this email.
        </p>
    </div>
    """
    
    # MOCK MODE (No API Key)
    if not api_key:
        print("\n" + "="*60)
        print(f"📧 [MOCK EMAIL] To: {to_email}")
        print(f"Subject: Document Shared: {file_name}")
        print(f"Link: {share_link}")
        print(f"Access Code: {access_code}")
        print("="*60 + "\n")
        return True

    # REAL MODE (SendGrid)
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=f"Document Shared: {file_name}",
        html_content=html_content
    )
    
    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        return response.status_code in [200, 201, 202]
    except Exception as e:
        print(f"SendGrid Error: {e}")
        st.error(f"Failed to send email: {e}")
        return False
