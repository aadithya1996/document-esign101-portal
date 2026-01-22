-- =====================================================
-- DOCUMENT SHARES & EXTERNAL ACCESS
-- =====================================================

CREATE TABLE IF NOT EXISTS public.document_shares (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    document_id UUID REFERENCES public.documents(id) ON DELETE CASCADE NOT NULL,
    recipient_email TEXT NOT NULL,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    
    -- Verification fields
    otp_code TEXT,
    otp_expires_at TIMESTAMP WITH TIME ZONE,
    is_verified BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '7 days'),
    
    -- Ensure unique active share per document/email
    UNIQUE(document_id, recipient_email)
);

-- RLS: Only the creator can view/manage the share record usually
-- But for external access, we might need a secure function or allow public verify

ALTER TABLE public.document_shares ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view shares created by them" 
ON public.document_shares
FOR SELECT
USING (auth.uid() = created_by);

CREATE POLICY "Users can create shares" 
ON public.document_shares
FOR INSERT
WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can delete shares created by them" 
ON public.document_shares
FOR DELETE
USING (auth.uid() = created_by);

-- 2. INDEX for faster lookups
CREATE INDEX idx_document_shares_token ON public.document_shares(id);
CREATE INDEX idx_document_shares_email ON public.document_shares(recipient_email);

-- 3. FUNCTION to Verify External Access (Bypass RLS safely)
-- This allows the public app to check if a share exists and matches email
CREATE OR REPLACE FUNCTION public.verify_share_attempt(
    share_id UUID, 
    email_input TEXT
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER -- Runs as admin to read shares table
AS $$
DECLARE
    share_record RECORD;
BEGIN
    SELECT * INTO share_record 
    FROM public.document_shares 
    WHERE id = share_id;
    
    IF share_record IS NULL THEN
        RETURN jsonb_build_object('valid', false, 'message', 'Invalid share link.');
    END IF;
    
    IF share_record.expires_at < NOW() THEN
        RETURN jsonb_build_object('valid', false, 'message', 'Share link has expired.');
    END IF;
    
    IF LOWER(share_record.recipient_email) != LOWER(email_input) THEN
         RETURN jsonb_build_object('valid', false, 'message', 'Email does not match the intended recipient.');
    END IF;
    
    RETURN jsonb_build_object('valid', true, 'message', 'Valid');
END;
$$;
