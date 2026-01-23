"""
Share Utilities
Handles creating and verifying document shares.
"""
import uuid
import random
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Tuple
from utils.supabase_client import init_supabase
from utils.email_utils import send_share_email

def create_share(document_id: str, file_name: str, recipient_email: str) -> bool:
    """
    Create a new share record and send email.
    """
    supabase = init_supabase()
    user = st.session_state.get("user")
    
    if not user:
        return False
        
    # Generate secure tokens
    access_code = "".join([str(random.randint(0, 9)) for _ in range(6)])
    
    try:
        # 1. Insert into DB
        response = supabase.table("document_shares").insert({
            "document_id": document_id,
            "recipient_email": recipient_email,
            "created_by": user["id"],
            "otp_code": access_code, # In production, hash this!
            "otp_expires_at": (datetime.now() + timedelta(days=7)).isoformat()
        }).execute()
        
        if not response.data:
            st.error("Failed to create share record.")
            return False
            
        share_id = response.data[0]["id"]
        
        # 2. Generate Link
        # Get base URL (localhost for dev, actual URL for prod)
        base_url = "http://localhost:8501" # Default fallback
        share_link = f"{base_url}/View_Document?share_id={share_id}"
        
        # 3. Send Email
        sent = send_share_email(recipient_email, file_name, share_link, access_code)
        
        if sent:
            st.toast(f"✅ Share link sent to {recipient_email}!")
            return True
        else:
            st.error("Failed to send email.")
            return False
            
    except Exception as e:
        st.error(f"Share Error: {e}")
        return False

def verify_share_access(share_id: str, otp_input: str) -> Tuple[bool, str, Optional[dict]]:
    """
    Verify the OTP for a given share using Secure RPC.
    Returns: (Success, Message, Data)
    """
    if not share_id or not otp_input:
        return False, "Missing information.", None
        
    try:
        supabase = init_supabase()
        
        # Call the RPC function we just created
        response = supabase.rpc("verify_share_otp", {
            "p_share_id": share_id,
            "p_otp_code": otp_input
        }).execute()
        
        result = response.data
        # The RPC now returns a TEXT (JSON string). Parse it.
        if isinstance(result, str):
            import json
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                return False, f"Failed to parse RPC response: {result}", None
        
        if result and isinstance(result, dict) and result.get("valid"):
            return True, "Access Granted!", result
        else:
            msg = result.get("message") if isinstance(result, dict) else "Verification failed."
            return False, msg, None

    except Exception as e:
        # HANDLING SUPABASE-PY SERIALIZATION QUIRK (JSON could not be generated)
        # If the code is 200 and details are valid, parse them manually.
        try:
            err_str = str(e)
            if "JSON could not be generated" in err_str and "'code': 200" in err_str:
                import json
                import re

                # The error format is: 'details': 'b'{"valid": true, ...}''
                # We need to extract the JSON from inside the byte string wrapper.
                # Use greedy matching to capture the full JSON object.

                # Strategy: Find b' followed by { and capture until the last } before '
                # Using greedy .* to get the complete JSON object
                clean_match = re.search(r"b'(\{.*\})'", err_str)

                if clean_match:
                    json_str = clean_match.group(1)
                    data = json.loads(json_str)
                    if data and data.get("valid"):
                        return True, "Access Granted!", data
                    elif data:
                        # Return the error message from the RPC if present
                        msg = data.get("message", "Verification failed.")
                        return False, msg, None

        except json.JSONDecodeError:
            pass  # Fall back to original error
        except Exception:
            pass  # Fall back to original error

        return False, f"System Error: {e}", None

def get_public_download_url(file_path: str) -> Optional[str]:
    """
    Generate a formatted download URL using Supabase service role
    OR just rely on the signed URL generation if we can auth it.
    
    Actually, standard `supabase.storage.create_signed_url` calls the API.
    If the user matches RLS, it works. 
    Since Public User != RLS User, we need a SERVICE ROLE client here.
    """
    import os
    from supabase import create_client
    
    # We must be careful exposing this. It should only be called AFTER OTP verification.
    
    url = os.getenv("SUPABASE_URL")
    # Use Service Key if available, else Anon Key (checking if Storage RLS allows it? It won't).
    # We need Service Key for this specific public access bypass.
    # NOTE: You mostly likely don't have SERVICE_KEY in env yet?
    # You have `SUPABASE_KEY` which is anon.
    
    # ALTERNATIVE: RPC function to sign URL?
    # Supabase PG doesn't easily sign storage URLs via SQL (it uses GoTrue/Storage API).
    
    # For now, allow it by adding a Storage Policy provided the file is in 'documents'.
    # But we can't restrict to just that share easily.
    
    # BEST PATH: Ask user for SERVICE_KEY or `SUPABASE_SERVICE_KEY` in .env?
    # OR: Use the `anon` key but ADD a storage policy: "Allow public read for 'documents' bucket".
    # That makes ALL documents public if you guess the path (timestamp_filename).
    # That is mediocre security but common for "signed URLs" themselves.
    # BUT `create_signed_url` requires `select` permission to GENERATE it? No.
    # Actually, you can generate a signed URL with the service key.
    
    # Let's assume we need to add a "Public Read Access" policy for verified shares? No too complex.
    
    # I'll create a `utils/admin_client.py` if needed, but for now, 
    # let's try to generate it using the standard client and see if it fails.
    # If it fails, I'll instruct user to add `SUPABASE_SERVICE_KEY`.
    
    try:
        from utils.supabase_client import get_supabase_client
        from supabase import create_client
        
        # Try to use Service Key if available (Best practice)
        service_key = os.getenv("SUPABASE_SERVICE_KEY") or st.secrets.get("SUPABASE_SERVICE_KEY")
        
        if service_key:
            # Create a localized admin client just for this operation
            admin_client = create_client(url, service_key)
            res = admin_client.storage.from_("documents").create_signed_url(file_path, 3600)
            return res.get("signedURL")
        else:
            # Fallback to standard client (Likely to fail if RLS is strict)
            client = get_supabase_client()
            res = client.storage.from_("documents").create_signed_url(file_path, 3600)
            return res.get("signedURL")
            
    except Exception as e:
        print(f"Error generating link: {e}")
        return None


def get_shared_document_summary(document_id: str, file_path: str) -> dict:
    """
    Get or create AI summary for a shared document.
    Uses service key to bypass RLS for public access.
    """
    import os
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not service_key:
        return {"summary": "AI Summary not available (service key not configured).", "error": True}

    try:
        admin_client = create_client(url, service_key)

        # Check if summary exists
        result = admin_client.table("document_summaries").select("*").eq("document_id", document_id).execute()

        if result.data:
            return result.data[0]

        # Generate new summary
        from utils.pdf_utils import extract_text_from_pdf
        from utils.ai_utils import generate_summary

        # Download PDF using service key
        pdf_bytes = admin_client.storage.from_("documents").download(file_path)
        text = extract_text_from_pdf(pdf_bytes)

        if not text:
            return {"summary": "Could not extract text from PDF.", "error": True}

        summary_data = generate_summary(text)

        # Store summary
        admin_client.table("document_summaries").insert({
            "document_id": document_id,
            "summary": summary_data["summary"],
            "model_used": summary_data["model"]
        }).execute()

        return summary_data

    except Exception as e:
        print(f"Error generating summary: {e}")
        return {"summary": f"Error generating summary: {e}", "error": True}


def stream_shared_document_summary(document_id: str, file_path: str):
    """
    Stream summary generation for shared documents and save when complete.
    Uses service key to bypass RLS for public access.
    Yields chunks for st.write_stream().
    """
    import os
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not service_key:
        yield "AI Summary not available (service key not configured)."
        return

    try:
        admin_client = create_client(url, service_key)

        from utils.pdf_utils import extract_text_from_pdf
        from utils.ai_utils import generate_summary_stream

        # Download PDF using service key
        pdf_bytes = admin_client.storage.from_("documents").download(file_path)
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
        admin_client.table("document_summaries").insert({
            "document_id": document_id,
            "summary": full_summary,
            "model_used": "gpt-4"
        }).execute()

    except Exception as e:
        yield f"Error generating summary: {e}"


def get_shared_document_text(file_path: str) -> str:
    """
    Get the extracted text from a shared document.
    Uses service key to bypass RLS for public access.

    Args:
        file_path: The storage path of the document

    Returns:
        Extracted text from the PDF, or empty string on error
    """
    import os
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not service_key:
        return ""

    try:
        admin_client = create_client(url, service_key)

        from utils.pdf_utils import extract_text_from_pdf

        # Download PDF using service key
        pdf_bytes = admin_client.storage.from_("documents").download(file_path)
        text = extract_text_from_pdf(pdf_bytes)

        return text or ""

    except Exception as e:
        print(f"Error extracting document text: {e}")
        return ""
