"""
Login Page - Email OTP Request
"""
import streamlit as st
from utils.auth_utils import send_otp, is_authenticated

st.set_page_config(
    page_title="Login | Document E-Sign Portal",
    page_icon="📧",
    layout="centered"
)

# Redirect if already logged in
if is_authenticated():
    st.switch_page("pages/3_📁_Dashboard.py")

st.title("📧 Login")
st.markdown("Enter your email to receive a one-time password.")

st.markdown("---")

# Email input form
with st.form("login_form"):
    email = st.text_input(
        "Email Address",
        placeholder="you@example.com",
        help="We'll send a 6-digit code to this email"
    )
    
    submit = st.form_submit_button("📨 Send OTP", type="primary", use_container_width=True)
    
    if submit:
        if not email:
            st.error("Please enter your email address.")
        elif "@" not in email or "." not in email:
            st.error("Please enter a valid email address.")
        else:
            with st.spinner("Sending OTP..."):
                success, message = send_otp(email)
            
            if success:
                # Store email for OTP verification page
                st.session_state["pending_email"] = email
                st.success(message)
                st.info("📱 Check your inbox and enter the code on the next page.")
                st.switch_page("pages/2_🔐_Verify_OTP.py")
            else:
                st.error(message)

st.markdown("---")

# Info section
with st.expander("ℹ️ How it works"):
    st.markdown("""
    1. **Enter your email** - We'll send a 6-digit verification code
    2. **Check your inbox** - The code expires in 10 minutes
    3. **Enter the code** - Verify and access your dashboard
    4. **First time?** - Your account is created automatically!
    
    No passwords needed. Secure. Simple.
    """)

# Back to home
st.page_link("app.py", label="← Back to Home", icon="🏠")
