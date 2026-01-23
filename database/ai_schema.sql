-- AI Schema: Document Summaries
-- File: database/ai_schema.sql

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Document Summaries Table
CREATE TABLE IF NOT EXISTS document_summaries (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE UNIQUE,
    summary TEXT NOT NULL,
    key_points JSONB,  -- Optional: bullet points
    model_used TEXT DEFAULT 'gpt-4',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS Policy
ALTER TABLE document_summaries ENABLE ROW LEVEL SECURITY;

-- Users can view summaries for their tenant documents
CREATE POLICY "Users can view summaries for their tenant documents"
ON document_summaries FOR SELECT USING (
    document_id IN (
        SELECT id FROM documents
        WHERE tenant_id IN (
            SELECT tenant_id FROM tenant_members WHERE user_id = auth.uid()
        )
    )
);

-- Users can insert summaries for their tenant documents
CREATE POLICY "Users can insert summaries for their tenant documents"
ON document_summaries FOR INSERT WITH CHECK (
    document_id IN (
        SELECT id FROM documents
        WHERE tenant_id IN (
            SELECT tenant_id FROM tenant_members WHERE user_id = auth.uid()
        )
    )
);
