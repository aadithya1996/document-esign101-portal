"""
OTP Verification Page
"""
import streamlit as st
from utils.auth_utils import verify_otp, send_otp, is_authenticated

st.set_page_config(
    page_title="Verify OTP | Document E-Sign Portal",
    page_icon="🔐",
    layout="centered"
)

# Redirect if already logged in
if is_authenticated():
    st.switch_page("pages/3_📁_Dashboard.py")

# Check if email is pending verification
pending_email = st.session_state.get("pending_email")

if not pending_email:
    st.warning("⚠️ No pending verification. Please start from the login page.")
    st.page_link("pages/1_📧_Login.py", label="Go to Login", icon="📧")
    st.stop()

st.title("🔐 Verify OTP")
st.markdown(f"Enter the 6-digit code sent to **{pending_email}**")

st.markdown("---")

# OTP input form
with st.form("otp_form"):
    otp_code = st.text_input(
        "One-Time Password",
        placeholder="123456",
        max_chars=6,
        help="Check your email inbox (and spam folder)"
    )
    
    submit = st.form_submit_button("✅ Verify", type="primary", use_container_width=True)
    
    if submit:
        if not otp_code:
            st.error("Please enter the OTP code.")
        elif len(otp_code) != 6 or not otp_code.isdigit():
            st.error("OTP must be a 6-digit number.")
        else:
            with st.spinner("Verifying..."):
                success, message = verify_otp(pending_email, otp_code)
            
            if success:
                st.success(message)
                # Clear pending email
                del st.session_state["pending_email"]
                st.balloons()
                st.switch_page("pages/3_📁_Dashboard.py")
            else:
                st.error(message)

st.markdown("---")

# Resend OTP option
col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Resend OTP", use_container_width=True):
        with st.spinner("Sending new OTP..."):
            success, message = send_otp(pending_email)
        if success:
            st.success("New OTP sent! Check your email.")
        else:
            st.error(message)

with col2:
    if st.button("📧 Use Different Email", use_container_width=True):
        if "pending_email" in st.session_state:
            del st.session_state["pending_email"]
        st.switch_page("pages/1_📧_Login.py")

# Help text
with st.expander("🆘 Didn't receive the code?"):
    st.markdown("""
    - Check your **spam/junk** folder
    - Wait a minute and try **Resend OTP**
    - Make sure you entered the correct email
    - The code expires after **10 minutes**
    """)
