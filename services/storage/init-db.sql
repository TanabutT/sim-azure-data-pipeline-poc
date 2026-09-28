-- PostgreSQL initialization script for Data Factory

-- Ensure the application user exists
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_user WHERE usename = 'df_user') THEN
    CREATE USER df_user WITH PASSWORD 'postgres';
  END IF;
END $$;

-- Grant privileges to df_user for the current database
ALTER USER df_user WITH CREATEDB;

CREATE TABLE IF NOT EXISTS pipelines (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    definition JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS runs (
    id SERIAL PRIMARY KEY,
    pipeline_id INTEGER NOT NULL REFERENCES pipelines(id),
    pipeline_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending',
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_executions (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    activity_name VARCHAR(255) NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending',
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    output JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_runs_pipeline_id ON runs(pipeline_id);
CREATE INDEX IF NOT EXISTS idx_runs_pipeline_name ON runs(pipeline_name);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_executions_run_id ON activity_executions(run_id);
CREATE INDEX IF NOT EXISTS idx_activity_executions_status ON activity_executions(status);

-- Grant permissions to application user
GRANT CONNECT ON DATABASE data_factory TO df_user;
GRANT USAGE ON SCHEMA public TO df_user;
GRANT CREATE ON SCHEMA public TO df_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO df_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO df_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO df_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO df_user;
