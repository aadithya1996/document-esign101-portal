"""
Authentication Utilities for OTP-based login
"""
import streamlit as st
from utils.supabase_client import init_supabase


def send_otp(email: str) -> tuple[bool, str]:
    """
    Send OTP to user's email via Supabase Auth (Raw HTTP).
    Uses raw requests to ensure 'create_user' param is passed correctly 
    as client library behavior can be inconsistent.
    """
    import requests
    import os
    
    try:
        # Get credentials
        url = os.getenv("SUPABASE_URL") or st.secrets["SUPABASE_URL"]
        key = os.getenv("SUPABASE_KEY") or st.secrets["SUPABASE_KEY"]
        
        auth_url = f"{url}/auth/v1/otp"
        
        headers = {
            "apikey": key,
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}"
        }
        
        payload = {
            "email": email,
            "create_user": True 
        }
        
        response = requests.post(auth_url, headers=headers, json=payload)
        
        if response.status_code in [200, 201]:
            return True, "OTP sent! Check your email inbox."
            
        # Parse error
        try:
            data = response.json()
            msg = data.get("msg") or data.get("error_description") or data.get("error")
            return False, f"Failed: {msg}"
        except:
             return False, f"Failed with status: {response.status_code}"
        
    except Exception as e:
        return False, f"System Error: {str(e)}"


def verify_otp(email: str, token: str) -> tuple[bool, str]:
    """
    Verify OTP token and create session.
    
    Args:
        email: User's email address
        token: 6-digit OTP from email
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        supabase = init_supabase()
        
        response = supabase.auth.verify_otp({
            "email": email,
            "token": token,
            "type": "email"
        })
        
        if response.user:
            # Store session in Streamlit session state
            st.session_state["user"] = {
                "id": response.user.id,
                "email": response.user.email,
                "access_token": response.session.access_token if response.session else None,
                "refresh_token": response.session.refresh_token if response.session else None
            }
            return True, "Login successful!"
        else:
            return False, "Verification failed. Please try again."
            
    except Exception as e:
        error_msg = str(e)
        if "invalid" in error_msg.lower() or "expired" in error_msg.lower():
            return False, "Invalid or expired OTP. Please request a new one."
        return False, f"Verification failed: {error_msg}"


from typing import Optional

def get_current_user() -> Optional[dict]:
    """
    Get the currently logged-in user from session state.
    
    Returns:
        User dict or None if not logged in
    """
    return st.session_state.get("user")


def is_authenticated() -> bool:
    """
    Check if user is currently authenticated.
    """
    user = get_current_user()
    return user is not None and user.get("id") is not None


def logout():
    """
    Clear user session and logout.
    """
    try:
        supabase = init_supabase()
        supabase.auth.sign_out()
    except Exception:
        pass  # Ignore errors during logout
    
    # Clear session state
    if "user" in st.session_state:
        del st.session_state["user"]
    if "pending_email" in st.session_state:
        del st.session_state["pending_email"]
    if "current_tenant" in st.session_state:
        del st.session_state["current_tenant"]


def require_auth():
    """
    Decorator-like function to protect pages.
    Call at the start of protected pages.
    """
    if not is_authenticated():
        st.warning("🔐 Please login to access this page.")
        st.page_link("pages/1_📧_Login.py", label="Go to Login", icon="📧")
        st.stop()
