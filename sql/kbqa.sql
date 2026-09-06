CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS users (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    username        VARCHAR(50)     NOT NULL,
    email           VARCHAR(255)    NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    role            VARCHAR(20)     NOT NULL DEFAULT 'user'
                                    CHECK (role IN ('admin', 'user')),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email    ON users (email);

CREATE TABLE IF NOT EXISTS rag_jobs (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID            NOT NULL REFERENCES users (id),
    status              VARCHAR(20)     NOT NULL DEFAULT 'pending'
                                        CHECK (status IN ('pending', 'processing', 'success', 'partial_success', 'failure')),
    total_documents     INTEGER         NOT NULL,
    documents_processed INTEGER         NOT NULL DEFAULT 0,
    documents_failed    INTEGER         NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),
    completed_at        TIMESTAMPTZ
);

CREATE INDEX  IF NOT EXISTS ix_rag_jobs_user_id ON rag_jobs (user_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_rag_jobs_one_active_per_user
    ON rag_jobs (user_id) WHERE status IN ('pending', 'processing');

CREATE TABLE IF NOT EXISTS documents (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID            NOT NULL REFERENCES users (id),
    filename        VARCHAR(255)    NOT NULL,
    file_type       VARCHAR(10)     NOT NULL
                                    CHECK (file_type IN ('txt')),
    file_size_bytes INTEGER         NOT NULL,
    s3_key          VARCHAR(512)    NOT NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'pending',
    text_preview    TEXT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    indexed_at      TIMESTAMPTZ,
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX  IF NOT EXISTS ix_documents_user_id ON documents (user_id);
CREATE INDEX  IF NOT EXISTS ix_documents_status  ON documents (status);
CREATE UNIQUE INDEX IF NOT EXISTS ix_documents_s3_key  ON documents (s3_key);

CREATE TABLE IF NOT EXISTS rag_job_documents (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    rag_job_id      UUID            NOT NULL REFERENCES rag_jobs (id),
    document_id     UUID            NOT NULL REFERENCES documents (id),
    status          VARCHAR(20)     NOT NULL DEFAULT 'pending'
                                    CHECK (status IN ('pending', 'processing', 'ready', 'failed')),
    error_message   TEXT,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_rag_job_documents_job_doc
    ON rag_job_documents (rag_job_id, document_id);

CREATE TABLE IF NOT EXISTS document_chunks (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID            NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    chunk_index     INTEGER         NOT NULL,
    chunk_text      TEXT            NOT NULL,
    embedding       VECTOR(1024)    NOT NULL,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_document_chunks_document_id ON document_chunks (document_id);
CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding    ON document_chunks
    USING hnsw (embedding vector_cosine_ops);
