-- =====================================================
-- Document E-Sign Portal - Database Schema
-- Run this in Supabase SQL Editor
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- PROFILES TABLE
-- Extends Supabase auth.users with additional info
-- =====================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view their own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- =====================================================
-- TENANTS TABLE
-- Organizations/workspaces for multi-tenancy
-- =====================================================
CREATE TABLE IF NOT EXISTS public.tenants (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    owner_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on tenants
ALTER TABLE public.tenants ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- TENANT_MEMBERS TABLE
-- Links users to tenants (many-to-many)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.tenant_members (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    role TEXT DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, user_id)
);

-- Enable RLS on tenant_members
ALTER TABLE public.tenant_members ENABLE ROW LEVEL SECURITY;

-- Tenant members policies
CREATE POLICY "Users can view their tenant memberships" ON public.tenant_members
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view members of their tenants" ON public.tenant_members
    FOR SELECT USING (
        tenant_id IN (
            SELECT tenant_id FROM public.tenant_members WHERE user_id = auth.uid()
        )
    );

-- Tenants policies (after tenant_members exists)
CREATE POLICY "Users can view tenants they belong to" ON public.tenants
    FOR SELECT USING (
        id IN (
            SELECT tenant_id FROM public.tenant_members WHERE user_id = auth.uid()
        )
    );

-- =====================================================
-- DOCUMENTS TABLE
-- Stores PDF document metadata
-- =====================================================
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE CASCADE NOT NULL,
    uploaded_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    mime_type TEXT DEFAULT 'application/pdf',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on documents
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

-- Documents policies
CREATE POLICY "Users can view documents in their tenants" ON public.documents
    FOR SELECT USING (
        tenant_id IN (
            SELECT tenant_id FROM public.tenant_members WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert documents to their tenants" ON public.documents
    FOR INSERT WITH CHECK (
        tenant_id IN (
            SELECT tenant_id FROM public.tenant_members WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete documents in their tenants" ON public.documents
    FOR DELETE USING (
        tenant_id IN (
            SELECT tenant_id FROM public.tenant_members WHERE user_id = auth.uid()
        )
    );

-- =====================================================
-- FUNCTIONS & TRIGGERS
-- =====================================================

-- Function to handle new user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    new_tenant_id UUID;
BEGIN
    -- Create profile for new user
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (NEW.id, NEW.email, NEW.raw_user_meta_data->>'full_name');
    
    -- Create a default tenant for the user
    INSERT INTO public.tenants (name, owner_id)
    VALUES (COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)) || '''s Workspace', NEW.id)
    RETURNING id INTO new_tenant_id;
    
    -- Add user as owner of their tenant
    INSERT INTO public.tenant_members (tenant_id, user_id, role)
    VALUES (new_tenant_id, NEW.id, 'owner');
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to auto-create profile and tenant on signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- =====================================================
-- STORAGE BUCKET SCRIPT
-- =====================================================
-- Attempt to create the 'documents' bucket if it doesn't exist
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'documents', 
    'documents', 
    false, 
    52428800, -- 50MB
    ARRAY['application/pdf']
)
ON CONFLICT (id) DO NOTHING;

-- STORAGE POLICIES
-- Enable RLS on objects
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- 1. Allow authenticated uploads
CREATE POLICY "Allow authenticated uploads"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'documents');

-- 2. Allow users to view files in their tenant
-- Note: This relies on the file path structure: tenant_id/filename
CREATE POLICY "Allow tenant file access"
ON storage.objects FOR SELECT
TO authenticated
USING (
    bucket_id = 'documents' 
    AND (storage.foldername(name))[1]::uuid IN (
        SELECT tenant_id FROM public.tenant_members WHERE user_id = auth.uid()
    )
);

-- 3. Allow users to delete files in their tenant
CREATE POLICY "Allow file deletion"
ON storage.objects FOR DELETE
TO authenticated
USING (
    bucket_id = 'documents'
    AND (storage.foldername(name))[1]::uuid IN (
        SELECT tenant_id FROM public.tenant_members WHERE user_id = auth.uid()
    )
);

