"""
Public View Document Page
Accepts share_id from URL, verifies OTP, and shows document.
"""
import streamlit as st
from utils.share_utils import verify_share_access, stream_shared_document_summary
from utils.storage_utils import get_download_url

st.set_page_config(
    page_title="View Document | Secure Share",
    page_icon="🔒",
    initial_sidebar_state="collapsed",
    layout="centered"
)

# Hide sidebar for public users
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {display: none;}
        section[data-testid="stSidebarNav"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True
)

# Parse URL parameters
# streamlit >= 1.30 uses st.query_params
share_id = st.query_params.get("share_id")

st.title("🔒 Secure Document Access")

if not share_id:
    st.error("Invalid link. Missing share ID.")
    st.info("Please request a new link from the sender.")
    st.stop()

# Session state to hold verified status across reruns
if "verified_share" not in st.session_state:
    st.session_state.verified_share = None

# Verification Screen
if not st.session_state.verified_share:
    st.markdown("This document is protected. Please enter the **Access Code** sent to your email.")
    
    with st.form("otp_form"):
        otp = st.text_input("Access Code", placeholder="123456", max_chars=6)
        submit = st.form_submit_button("🔓 Unlock Document", type="primary", use_container_width=True)
        
        if submit:
            if len(otp) != 6:
                st.error("Code must be 6 digits.")
            else:
                with st.spinner("Verifying..."):
                    success, msg, data = verify_share_access(share_id, otp)
                
                if success:
                    st.session_state.verified_share = data
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

# Document View Screen (Post-Verification)
else:
    data = st.session_state.verified_share
    # Ensure the session matches the URL (basic hijack prevention)
    # verify_share_access returns data only if ID matches
    
    st.balloons()
    st.success("✅ Access Granted")
    
    file_name = data.get("file_name", "Document")
    file_path = data.get("file_path")
    
    st.header(f"📄 {file_name}")
    
    if file_path:
        # Generate Signed URL
        # We need a new util that uses a service key OR allows public download via token?
        # Standard signed URL generation requires specific permissions.
        # But 'documents' bucket RLS policy allows "SELECT ... if in tenant".
        # Public user is NOT in tenant.
        
        # SOLUTION: We need `storage_utils.get_download_url` to work for this public page.
        # Options:
        # 1. Use a Service Role client here (risky if code leaked, but ok on server-side streamlit?)
        # 2. Add a Storage Policy: "Allow public download if...?" (Hard to verify OTP in storage policy)
        # 3. Use the `share_utils` to generate a signed URL using a Service Key for this specific action?
        
        # Let's use Option 3: Create a specific function in backend that uses Service Role 
        # strictly for verified shares.
        
        # For now, I'll update the `View_Document.py` to call a new util function `get_shared_file_url(file_path)`
        
        from utils.share_utils import get_public_download_url
        download_url = get_public_download_url(file_path)
        document_id = data.get("document_id")

        if download_url:
            # Action buttons row
            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                st.link_button("⬇️ Download PDF", download_url, type="primary", use_container_width=True)

            with btn_col2:
                # AI Summary Button / Popover
                with st.popover("📝 AI Summary", use_container_width=True):
                    st.markdown("### AI Summary")

                    # Check for existing summary first
                    from utils.share_utils import get_public_download_url
                    import os
                    from supabase import create_client

                    existing_summary = None
                    service_key = os.getenv("SUPABASE_SERVICE_KEY")
                    if service_key:
                        admin_client = create_client(os.getenv("SUPABASE_URL"), service_key)
                        result = admin_client.table("document_summaries").select("summary").eq("document_id", document_id).execute()
                        if result.data:
                            existing_summary = result.data[0]["summary"]

                    if existing_summary:
                        st.write(existing_summary)
                    else:
                        if st.button("Generate Summary", type="primary", use_container_width=True):
                            st.write_stream(stream_shared_document_summary(document_id, file_path))
                        else:
                            st.caption("Click to generate an AI summary of this document.")

            # Preview (iframe)
            st.markdown("### Preview")
            st.markdown(f'<iframe src="{download_url}" width="100%" height="600px"></iframe>', unsafe_allow_html=True)
        else:
            st.error("Failed to generate secure download link.")
    else:
        st.error("File path missing.")

