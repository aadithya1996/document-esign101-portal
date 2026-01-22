"""
Dashboard Page - Document Management
Protected page requiring authentication
"""
import streamlit as st
from utils.auth_utils import require_auth, get_current_user, logout
from utils.storage_utils import (
    upload_pdf, 
    list_documents, 
    get_download_url, 
    delete_document,
    fetch_user_tenants,
    set_current_tenant,
    get_user_tenant_id
)

st.set_page_config(
    page_title="Dashboard | Document E-Sign Portal",
    page_icon="📁",
    layout="wide"
)

# Protect this page
require_auth()

# Get current user
user = get_current_user()

# Initialize tenant
if "current_tenant" not in st.session_state:
    tenants = fetch_user_tenants()
    if tenants:
        set_current_tenant(tenants[0])
    else:
        st.error("No workspace found. Please contact support.")
        st.stop()

# Header
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    st.title("📁 Document Dashboard")

with col2:
    # Tenant selector
    tenants = fetch_user_tenants()
    current_tenant = st.session_state.get("current_tenant", {})
    
    if len(tenants) > 1:
        tenant_names = [t["name"] for t in tenants]
        selected_idx = next(
            (i for i, t in enumerate(tenants) if t["id"] == current_tenant.get("id")), 
            0
        )
        selected = st.selectbox(
            "Workspace",
            tenant_names,
            index=selected_idx,
            label_visibility="collapsed"
        )
        if selected != current_tenant.get("name"):
            new_tenant = next(t for t in tenants if t["name"] == selected)
            set_current_tenant(new_tenant)
            st.rerun()
    else:
        st.caption(f"📂 {current_tenant.get('name', 'Workspace')}")

with col3:
    if st.button("🚪 Logout", use_container_width=True):
        logout()
        st.switch_page("app.py")

st.markdown(f"Logged in as **{user.get('email')}**")
st.markdown("---")

# Two-column layout
upload_col, docs_col = st.columns([1, 2])

# Upload Section
with upload_col:
    st.subheader("📤 Upload Documents")
    
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        help="Select one or more PDF files to upload"
    )
    
    if uploaded_files:
        if st.button("⬆️ Upload All", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_area = st.empty()
            
            success_count = 0
            total = len(uploaded_files)
            
            for idx, file in enumerate(uploaded_files):
                status_area.text(f"Uploading {file.name}...")
                success, message, _ = upload_pdf(file)
                
                if success:
                    success_count += 1
                    st.success(message)
                else:
                    st.error(f"❌ {file.name}: {message}")
                
                progress_bar.progress((idx + 1) / total)
            
            status_area.empty()
            progress_bar.empty()
            
            if success_count == total:
                st.balloons()
                st.success(f"✅ All {total} files uploaded successfully!")
            elif success_count > 0:
                st.warning(f"Uploaded {success_count}/{total} files.")
            
            st.rerun()
    
    st.markdown("---")
    
    # Quick stats
    documents = list_documents()
    total_size = sum(doc.get("file_size", 0) for doc in documents)
    
    st.metric("Total Documents", len(documents))
    st.metric("Storage Used", f"{total_size / (1024 * 1024):.2f} MB")

# Documents Gallery
with docs_col:
    st.subheader("📚 Your Documents")
    
    if not documents:
        st.info("📭 No documents yet. Upload your first PDF!")
    else:
        # Search filter
        search = st.text_input("🔍 Search documents", placeholder="Type to filter...")
        
        filtered_docs = documents
        if search:
            filtered_docs = [
                doc for doc in documents 
                if search.lower() in doc.get("file_name", "").lower()
            ]
        
        if not filtered_docs:
            st.warning("No documents match your search.")
        else:
            # Document grid
            for doc in filtered_docs:
                with st.container():
                    col_icon, col_name, col_size, col_actions = st.columns([0.5, 3, 1, 1.5])
                    
                    with col_icon:
                        st.markdown("📄")
                    
                    with col_name:
                        st.markdown(f"**{doc.get('file_name', 'Unnamed')}**")
                        created = doc.get('created_at', '')[:10] if doc.get('created_at') else ''
                        st.caption(f"Uploaded: {created}")
                    
                    with col_size:
                        size_mb = doc.get('file_size', 0) / (1024 * 1024)
                        st.caption(f"{size_mb:.2f} MB")
                    
                    with col_actions:
                        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
                        
                        with btn_col1:
                            download_url = get_download_url(doc.get('file_path', ''))
                            if download_url:
                                st.link_button("⬇️", download_url, use_container_width=True)
                        
                        with btn_col2:
                            # Share Button / Popover
                            with st.popover("🔗", use_container_width=True):
                                st.markdown("### Share Document")
                                st.caption(f"Share **{doc.get('file_name')}** externally.")
                                
                                recipient = st.text_input("Recipient Email", key=f"share_email_{doc['id']}")
                                if st.button("Send Link", key=f"share_btn_{doc['id']}", type="primary"):
                                    if not recipient:
                                        st.error("Email required.")
                                    else:
                                        from utils.share_utils import create_share
                                        with st.spinner("Sending..."):
                                            create_share(doc['id'], doc.get('file_name'), recipient)
                        
                        with btn_col3:
                            if st.button("🗑️", key=f"del_{doc['id']}", use_container_width=True):
                                success, msg = delete_document(doc['id'], doc['file_path'])
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                    
                    st.divider()

# Footer
st.markdown("---")
st.caption("💡 Tip: You can upload multiple PDFs at once by selecting them together.")
