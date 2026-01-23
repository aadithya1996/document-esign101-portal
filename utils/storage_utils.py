"""
Storage Utilities for PDF document management
"""
import streamlit as st
from datetime import datetime
from utils.supabase_client import init_supabase
from utils.auth_utils import get_current_user

BUCKET_NAME = "documents"


from typing import Optional, Tuple, List, Dict

def get_user_tenant_id() -> Optional[str]:
    """
    Get the current user's active tenant ID.
    """
    return st.session_state.get("current_tenant", {}).get("id")


def fetch_user_tenants() -> list[dict]:
    """
    Fetch all tenants the current user belongs to.
    """
    user = get_current_user()
    if not user:
        return []
    
    try:
        supabase = init_supabase()
        
        # Get tenant memberships with tenant details
        response = supabase.table("tenant_members") \
            .select("tenant_id, role, tenants(id, name)") \
            .eq("user_id", user["id"]) \
            .execute()
        
        tenants = []
        for membership in response.data:
            tenant_data = membership.get("tenants", {})
            if tenant_data:
                tenants.append({
                    "id": tenant_data.get("id"),
                    "name": tenant_data.get("name"),
                    "role": membership.get("role")
                })
        
        return tenants
        
    except Exception as e:
        st.error(f"Failed to fetch tenants: {e}")
        return []


def set_current_tenant(tenant: dict):
    """
    Set the active tenant for the current session.
    """
    st.session_state["current_tenant"] = tenant


def upload_pdf(uploaded_file) -> Tuple[bool, str, Optional[dict]]:
    """
    Upload a PDF file to Supabase Storage and create document record.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        Tuple of (success, message, document_data)
    """
    user = get_current_user()
    tenant_id = get_user_tenant_id()
    
    if not user or not tenant_id:
        return False, "Authentication or tenant not configured.", None
    
    try:
        supabase = init_supabase()
        
        # Generate unique file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = uploaded_file.name
        file_path = f"{tenant_id}/{timestamp}_{file_name}"
        
        # Upload to storage
        file_bytes = uploaded_file.read()
        
        storage_response = supabase.storage.from_(BUCKET_NAME).upload(
            path=file_path,
            file=file_bytes,
            file_options={"content-type": "application/pdf"}
        )
        
        # Create document record in database
        doc_data = {
            "tenant_id": tenant_id,
            "uploaded_by": user["id"],
            "file_name": file_name,
            "file_path": file_path,
            "file_size": len(file_bytes),
            "mime_type": "application/pdf"
        }
        
        db_response = supabase.table("documents").insert(doc_data).execute()
        
        if db_response.data:
            return True, f"✅ Uploaded: {file_name}", db_response.data[0]
        else:
            return False, "Failed to save document record.", None
            
    except Exception as e:
        error_msg = str(e)
        if "duplicate" in error_msg.lower():
            return False, "A file with this name already exists.", None
        return False, f"Upload failed: {error_msg}", None


def list_documents() -> list[dict]:
    """
    List all documents in the current tenant.
    """
    tenant_id = get_user_tenant_id()
    if not tenant_id:
        return []
    
    try:
        supabase = init_supabase()
        
        response = supabase.table("documents") \
            .select("*") \
            .eq("tenant_id", tenant_id) \
            .order("created_at", desc=True) \
            .execute()
        
        return response.data or []
        
    except Exception as e:
        st.error(f"Failed to list documents: {e}")
        return []


def get_download_url(file_path: str, expires_in: int = 3600) -> Optional[str]:
    """
    Generate a signed URL for downloading a file.
    
    Args:
        file_path: Path to file in storage
        expires_in: URL expiration time in seconds (default 1 hour)
    """
    try:
        supabase = init_supabase()
        
        response = supabase.storage.from_(BUCKET_NAME).create_signed_url(
            path=file_path,
            expires_in=expires_in
        )
        
        return response.get("signedURL")
        
    except Exception as e:
        st.error(f"Failed to generate download URL: {e}")
        return None


def delete_document(document_id: str, file_path: str) -> tuple[bool, str]:
    """
    Delete a document from storage and database.

    Args:
        document_id: Document UUID in database
        file_path: File path in storage
    """
    try:
        supabase = init_supabase()

        # Delete from storage
        supabase.storage.from_(BUCKET_NAME).remove([file_path])

        # Delete from database
        supabase.table("documents").delete().eq("id", document_id).execute()

        return True, "Document deleted successfully."

    except Exception as e:
        return False, f"Failed to delete document: {e}"


def get_or_create_summary(document_id: str, file_path: str) -> dict:
    """
    Get existing summary or generate new one.

    Args:
        document_id: Document UUID in database
        file_path: File path in storage

    Returns:
        Dictionary with summary data
    """
    supabase = init_supabase()

    # Check if summary exists
    result = supabase.table("document_summaries").select("*").eq("document_id", document_id).execute()

    if result.data:
        return result.data[0]

    # Generate new summary
    from utils.pdf_utils import extract_text_from_pdf
    from utils.ai_utils import generate_summary

    # Download PDF
    pdf_bytes = supabase.storage.from_(BUCKET_NAME).download(file_path)
    text = extract_text_from_pdf(pdf_bytes)

    if not text:
        return {"summary": "Could not extract text from PDF.", "error": True}

    summary_data = generate_summary(text)

    # Store summary
    supabase.table("document_summaries").insert({
        "document_id": document_id,
        "summary": summary_data["summary"],
        "model_used": summary_data["model"]
    }).execute()

    return summary_data


def stream_and_save_summary(document_id: str, file_path: str):
    """
    Stream summary generation and save to database when complete.
    Yields chunks for st.write_stream().

    Args:
        document_id: Document UUID in database
        file_path: File path in storage

    Yields:
        Text chunks from the AI model
    """
    from utils.pdf_utils import extract_text_from_pdf
    from utils.ai_utils import generate_summary_stream

    supabase = init_supabase()

    # Download PDF
    pdf_bytes = supabase.storage.from_(BUCKET_NAME).download(file_path)
    text = extract_text_from_pdf(pdf_bytes)

    if not text:
        yield "Could not extract text from PDF."
        return

    # Collect full summary while streaming
    full_summary = ""
    for chunk in generate_summary_stream(text):
        full_summary += chunk
        yield chunk

    # Save to database after streaming completes
    supabase.table("document_summaries").insert({
        "document_id": document_id,
        "summary": full_summary,
        "model_used": "gpt-4"
    }).execute()
