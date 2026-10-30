-- Run against the Medilink-hmis database after reviewing with the DBA.
-- This schema is isolated from patient and operational tables.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS ai_knowledge_documents (
  document_id uuid PRIMARY KEY,
  organization_id text NOT NULL,
  facility_id text NOT NULL,
  department_id text,
  title text NOT NULL,
  document_type text NOT NULL,
  classification text NOT NULL CHECK (classification IN ('PUBLIC','INTERNAL','CONFIDENTIAL','RESTRICTED')),
  version text NOT NULL,
  allowed_roles jsonb NOT NULL DEFAULT '[]'::jsonb,
  allowed_users jsonb NOT NULL DEFAULT '[]'::jsonb,
  effective_from date,
  effective_until date,
  source_filename text NOT NULL,
  content_sha256 text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, facility_id, source_filename, version, content_sha256)
);

CREATE TABLE IF NOT EXISTS ai_knowledge_chunks (
  chunk_id text PRIMARY KEY,
  document_id uuid NOT NULL REFERENCES ai_knowledge_documents(document_id) ON DELETE CASCADE,
  chunk_index integer NOT NULL,
  content text NOT NULL,
  embedding vector(256),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS ai_knowledge_chunks_document_idx ON ai_knowledge_chunks(document_id);
CREATE INDEX IF NOT EXISTS ai_knowledge_chunks_embedding_hnsw_idx
  ON ai_knowledge_chunks USING hnsw (embedding vector_cosine_ops);
