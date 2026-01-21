"""
Document E-Sign Portal
Main application entry point
"""
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Document E-Sign Portal",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    css_file = "assets/styles.css"
    try:
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass  # CSS file is optional

load_css()

# Main page content
def main():
    st.title("📄 Document E-Sign Portal")
    st.markdown("---")
    
    # Check authentication status
    from utils.auth_utils import is_authenticated, get_current_user
    
    if is_authenticated():
        user = get_current_user()
        st.success(f"Welcome back, **{user.get('email')}**! 👋")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 📁 Your Dashboard
            Access your documents and upload new files.
            """)
            st.page_link("pages/3_📁_Dashboard.py", label="Go to Dashboard", icon="📁")
        
        with col2:
            st.markdown("""
            ### 🔐 Account
            Manage your session and logout.
            """)
            if st.button("🚪 Logout", type="secondary"):
                from utils.auth_utils import logout
                logout()
                st.rerun()
    else:
        st.markdown("""
        ### Welcome to the Document E-Sign Portal
        
        A secure platform to store and manage your PDF documents.
        
        **Features:**
        - 🔐 **Secure OTP Authentication** - No passwords to remember
        - 📁 **Multi-Tenant Storage** - Organize documents by workspace
        - ☁️ **Cloud Storage** - Access from anywhere
        - 🔒 **Row-Level Security** - Your documents stay private
        """)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### New User?")
            st.page_link("pages/1_📧_Login.py", label="Sign Up with Email", icon="📧")
        
        with col2:
            st.markdown("#### Returning User?")
            st.page_link("pages/1_📧_Login.py", label="Login with OTP", icon="🔐")

    # Footer
    st.markdown("---")
    st.caption("© 2026 Document E-Sign Portal | Powered by Supabase")


if __name__ == "__main__":
    main()
