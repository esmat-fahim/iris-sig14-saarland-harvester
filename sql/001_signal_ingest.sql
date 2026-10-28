-- LOCAL CONTRACT ONLY. Confirm the real IRIS schema before deploying to any shared database.
-- PostgreSQL 16 + PostGIS 3.4. Run with a database owner who can create schema/extensions.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA IF NOT EXISTS iris_staging;
CREATE TABLE IF NOT EXISTS iris_staging.signal_ingest (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_system TEXT NOT NULL,
    source_id TEXT NOT NULL,
    signal_type TEXT NOT NULL CHECK (signal_type IN (
      'heavy_industrial_restructuring_approval', 'power_substation_approval')),
    title TEXT NOT NULL,
    publication_date DATE,
    listing_date DATE,
    decision_date DATE,
    source_url TEXT NOT NULL,
    location_text TEXT,
    geom geometry(Point, 25832),
    quality_flags TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    source_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    content_hash CHAR(64) NOT NULL,
    first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source_system, source_id),
    CHECK (source_url LIKE 'https://%'),
    CHECK (geom IS NULL OR ST_SRID(geom) = 25832)
);
CREATE INDEX IF NOT EXISTS idx_signal_ingest_geom
 ON iris_staging.signal_ingest USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_signal_ingest_type_date
 ON iris_staging.signal_ingest (signal_type, listing_date DESC);
