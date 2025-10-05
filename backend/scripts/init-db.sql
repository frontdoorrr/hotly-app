-- ==============================================================================
-- Database Initialization Script for hotly-app
-- ==============================================================================
-- This script is executed when the PostgreSQL container is first created
-- ==============================================================================

-- Enable PostGIS extension for geographical queries
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Enable pg_trgm for text search optimization
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable uuid-ossp for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE '✓ Database initialized successfully';
    RAISE NOTICE '✓ PostGIS extension enabled';
    RAISE NOTICE '✓ pg_trgm extension enabled';
    RAISE NOTICE '✓ UUID extension enabled';
END $$;
