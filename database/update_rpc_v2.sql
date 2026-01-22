-- UPDATE (v2) FUNCTION to Verify OTP AND Return File Info
-- Run this to update the logic

CREATE OR REPLACE FUNCTION public.verify_share_otp(
    p_share_id UUID, 
    p_otp_code TEXT
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    share_record RECORD;
    doc_record RECORD;
BEGIN
    SELECT * INTO share_record 
    FROM public.document_shares 
    WHERE id = p_share_id;
    
    IF share_record IS NULL THEN
        RETURN jsonb_build_object('valid', false, 'message', 'Invalid share link.');
    END IF;
    
    IF share_record.expires_at < NOW() THEN
        RETURN jsonb_build_object('valid', false, 'message', 'Share link has expired.');
    END IF;
    
    -- Check OTP
    IF TRIM(share_record.otp_code) != TRIM(p_otp_code) THEN
         RETURN jsonb_build_object('valid', false, 'message', 'Invalid Access Code.');
    END IF;
    
    -- Fetch Document Details (Bypass RLS)
    SELECT * INTO doc_record
    FROM public.documents
    WHERE id = share_record.document_id;
    
    RETURN jsonb_build_object(
        'valid', true, 
        'message', 'Success',
        'document_id', share_record.document_id,
        'recipient_email', share_record.recipient_email,
        'file_name', doc_record.file_name,
        'file_path', doc_record.file_path,
        'mime_type', doc_record.mime_type
    );
END;
$$;
