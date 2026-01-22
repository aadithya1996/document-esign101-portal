-- FIX: Change verify_share_otp to return TEXT instead of JSONB
-- This resolves the "JSON could not be generated" error in supabase-py

CREATE OR REPLACE FUNCTION public.verify_share_otp(
    p_share_id UUID, 
    p_otp_code TEXT
)
RETURNS TEXT  -- Changed from JSONB to TEXT
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    share_record RECORD;
    doc_record RECORD;
    result_json TEXT;
BEGIN
    SELECT * INTO share_record 
    FROM public.document_shares 
    WHERE id = p_share_id;
    
    IF share_record IS NULL THEN
        RETURN '{"valid": false, "message": "Invalid share link."}';
    END IF;
    
    IF share_record.expires_at < NOW() THEN
        RETURN '{"valid": false, "message": "Share link has expired."}';
    END IF;
    
    -- Check OTP
    IF TRIM(share_record.otp_code) != TRIM(p_otp_code) THEN
        RETURN '{"valid": false, "message": "Invalid Access Code."}';
    END IF;
    
    -- Fetch Document Details (Bypass RLS)
    SELECT * INTO doc_record
    FROM public.documents
    WHERE id = share_record.document_id;
    
    -- Build JSON as TEXT
    result_json := json_build_object(
        'valid', true,
        'message', 'Success',
        'document_id', share_record.document_id,
        'recipient_email', share_record.recipient_email,
        'file_name', doc_record.file_name,
        'file_path', doc_record.file_path,
        'mime_type', doc_record.mime_type
    )::TEXT;
    
    RETURN result_json;
END;
$$;
