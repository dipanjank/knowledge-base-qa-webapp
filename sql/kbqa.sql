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

-- Vector storage (langchain_pg_collection, langchain_pg_embedding) is managed
-- automatically by LangChain's PGVector on first use.
