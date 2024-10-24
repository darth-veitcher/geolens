#!/bin/bash

# Use environment variables for the connection parameters
POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-password}
POSTGRES_DB=${POSTGRES_DB:-postgres}
echo "Using POSTGRES_USER=$POSTGRES_USER, POSTGRES_DB=$POSTGRES_DB"

# Check PostgreSQL readiness via Unix socket
export PGPASSWORD=$POSTGRES_PASSWORD
until pg_isready -h /var/run/postgresql -p 5432 -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
    echo "Waiting for PostgreSQL to start on Unix socket '/var/run/postgresql' with user '$POSTGRES_USER'..."
    sleep 2  # Sleep for 2 seconds before retrying
done

# Once PostgreSQL is ready, append pg_hba.conf entry for replication
echo "PostgreSQL is up! Configuring replication settings."
echo "host replication all 172.20.0.0/12 md5" >> /var/lib/postgresql/data/pg_hba.conf

# Reload PostgreSQL to apply the changes
pg_ctl reload

# ------------------------------------------------------------------------------
# Now initialise the primary database
# ------------------------------------------------------------------------------
#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable required extensions
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS postgis_topology;
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE EXTENSION IF NOT EXISTS age;
    CREATE EXTENSION IF NOT EXISTS btree_gist;

    -- Create application role with necessary permissions
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'geolens_app') THEN
            CREATE ROLE geolens_app WITH LOGIN PASSWORD 'geolens_app_pass';
        END IF;
    END
    \$\$;

    -- Create schemas
    CREATE SCHEMA IF NOT EXISTS geolens;
    GRANT USAGE ON SCHEMA geolens TO geolens_app;
    ALTER DEFAULT PRIVILEGES IN SCHEMA geolens GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO geolens_app;
    ALTER DEFAULT PRIVILEGES IN SCHEMA geolens GRANT USAGE, SELECT ON SEQUENCES TO geolens_app;

    -- Set search path
    ALTER ROLE geolens_app SET search_path TO geolens, public;

    -- Create basic tables
    CREATE TABLE IF NOT EXISTS geolens.locations (
        id BIGSERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        location_type TEXT NOT NULL,
        geometry geometry(Point, 4326),
        properties JSONB DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS geolens.architectural_features (
        id BIGSERIAL PRIMARY KEY,
        location_id BIGINT REFERENCES geolens.locations(id),
        style TEXT NOT NULL,
        year_built INTEGER,
        architect TEXT,
        description TEXT,
        embedding vector(384),
        properties JSONB DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS geolens.historical_events (
        id BIGSERIAL PRIMARY KEY,
        location_id BIGINT REFERENCES geolens.locations(id),
        event_date DATE,
        event_type TEXT,
        description TEXT,
        embedding vector(384),
        properties JSONB DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS geolens.relationships (
        id BIGSERIAL PRIMARY KEY,
        from_location_id BIGINT REFERENCES geolens.locations(id),
        to_location_id BIGINT REFERENCES geolens.locations(id),
        relationship_type TEXT NOT NULL,
        strength FLOAT,
        evidence TEXT,
        properties JSONB DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Create indexes
    CREATE INDEX IF NOT EXISTS idx_locations_geometry ON geolens.locations USING GIST(geometry);
    CREATE INDEX IF NOT EXISTS idx_locations_type ON geolens.locations USING btree(location_type);
    
    CREATE INDEX IF NOT EXISTS idx_architectural_features_embedding 
    ON geolens.architectural_features USING ivfflat (embedding vector_cosine_ops);
    CREATE INDEX IF NOT EXISTS idx_architectural_features_style 
    ON geolens.architectural_features USING btree(style);
    
    CREATE INDEX IF NOT EXISTS idx_historical_events_embedding 
    ON geolens.historical_events USING ivfflat (embedding vector_cosine_ops);
    CREATE INDEX IF NOT EXISTS idx_historical_events_date 
    ON geolens.historical_events USING btree(event_date);
    
    CREATE INDEX IF NOT EXISTS idx_relationships_type 
    ON geolens.relationships USING btree(relationship_type);
    
    -- Create update trigger function
    CREATE OR REPLACE FUNCTION geolens.update_updated_at()
    RETURNS TRIGGER AS \$\$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    \$\$ LANGUAGE plpgsql;

    -- Create triggers
    CREATE TRIGGER update_locations_updated_at
        BEFORE UPDATE ON geolens.locations
        FOR EACH ROW
        EXECUTE FUNCTION geolens.update_updated_at();

    CREATE TRIGGER update_architectural_features_updated_at
        BEFORE UPDATE ON geolens.architectural_features
        FOR EACH ROW
        EXECUTE FUNCTION geolens.update_updated_at();

    CREATE TRIGGER update_historical_events_updated_at
        BEFORE UPDATE ON geolens.historical_events
        FOR EACH ROW
        EXECUTE FUNCTION geolens.update_updated_at();

    CREATE TRIGGER update_relationships_updated_at
        BEFORE UPDATE ON geolens.relationships
        FOR EACH ROW
        EXECUTE FUNCTION geolens.update_updated_at();
EOSQL