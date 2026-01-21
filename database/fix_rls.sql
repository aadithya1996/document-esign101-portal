-- =====================================================
-- FIX RLS INFINITE RECURSION
-- Run this in Supabase SQL Editor
-- =====================================================

-- 1. Create a helper function to get current user's tenants
-- marked as SECURITY DEFINER to bypass RLS and avoid recursion
CREATE OR REPLACE FUNCTION get_my_tenant_ids()
RETURNS SETOF UUID
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
STABLE
AS $$
    SELECT tenant_id FROM public.tenant_members WHERE user_id = auth.uid();
$$;

-- 2. Drop the recursive policy
DROP POLICY IF EXISTS "Users can view members of their tenants" ON public.tenant_members;

-- 3. create the new non-recursive policy
CREATE POLICY "Users can view members of their tenants" ON public.tenant_members
    FOR SELECT USING (
        tenant_id IN ( SELECT get_my_tenant_ids() )
    );

-- 4. Just in case, grant execute permission
GRANT EXECUTE ON FUNCTION get_my_tenant_ids TO authenticated;
GRANT EXECUTE ON FUNCTION get_my_tenant_ids TO service_role;
