-- UPDATE FUNCTION to Verify OTP
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
    
    -- Check OTP (Case insensitive clean)
    IF TRIM(share_record.otp_code) != TRIM(p_otp_code) THEN
         RETURN jsonb_build_object('valid', false, 'message', 'Invalid Access Code.');
    END IF;
    
    -- Success! Return document ID and details
    -- We can also fetch the document details here to save a round trip
    RETURN jsonb_build_object(
        'valid', true, 
        'message', 'Success',
        'document_id', share_record.document_id,
        'recipient_email', share_record.recipient_email
    );
END;
$$;

-- Grant access
GRANT EXECUTE ON FUNCTION verify_share_otp TO anon;
GRANT EXECUTE ON FUNCTION verify_share_otp TO authenticated;
GRANT EXECUTE ON FUNCTION verify_share_otp TO service_role;
