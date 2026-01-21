"""
Utils package initialization
"""
from utils.supabase_client import init_supabase, get_supabase_client
from utils.auth_utils import (
    send_otp,
    verify_otp,
    get_current_user,
    is_authenticated,
    logout,
    require_auth
)
from utils.storage_utils import (
    upload_pdf,
    list_documents,
    get_download_url,
    delete_document,
    fetch_user_tenants,
    set_current_tenant,
    get_user_tenant_id
)

__all__ = [
    "init_supabase",
    "get_supabase_client",
    "send_otp",
    "verify_otp",
    "get_current_user",
    "is_authenticated",
    "logout",
    "require_auth",
    "upload_pdf",
    "list_documents",
    "get_download_url",
    "delete_document",
    "fetch_user_tenants",
    "set_current_tenant",
    "get_user_tenant_id"
]
