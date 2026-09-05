CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS users (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    username        VARCHAR(50)     NOT NULL,
    email           VARCHAR(255)    NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    role            VARCHAR(20)     NOT NULL DEFAULT 'user'
                                    CHECK (role IN ('admin', 'user')),
    created_at      TIMESTAMP     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP     NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email    ON users (email);

CREATE TABLE IF NOT EXISTS documents (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID            NOT NULL REFERENCES users (id),
    filename        VARCHAR(255)    NOT NULL,
    file_type       VARCHAR(10)     NOT NULL
                                    CHECK (file_type IN ('pdf', 'txt', 'csv')),
    file_size_bytes INTEGER         NOT NULL,
    s3_key          VARCHAR(512)    NOT NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'processing',
    text_preview    TEXT,
    page_count      INTEGER,
    created_at      TIMESTAMP     NOT NULL DEFAULT now(),
    indexed_at      TIMESTAMP,
    deleted_at      TIMESTAMP
);

CREATE INDEX  IF NOT EXISTS ix_documents_user_id ON documents (user_id);
CREATE INDEX  IF NOT EXISTS ix_documents_status  ON documents (status);
CREATE UNIQUE INDEX IF NOT EXISTS ix_documents_s3_key  ON documents (s3_key);

CREATE TABLE IF NOT EXISTS document_chunks (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID            NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    chunk_index     INTEGER         NOT NULL,
    chunk_text      TEXT            NOT NULL,
    embedding       VECTOR(1024)    NOT NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_document_chunks_document_id ON document_chunks (document_id);
CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding    ON document_chunks
    USING hnsw (embedding vector_cosine_ops);
