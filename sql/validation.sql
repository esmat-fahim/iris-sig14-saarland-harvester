-- Duplicate identity must return zero rows.
SELECT source_system, source_id, COUNT(*) AS duplicates
FROM iris_staging.signal_ingest GROUP BY 1,2 HAVING COUNT(*) > 1;

-- Counts and location/metadata completeness.
SELECT signal_type, COUNT(*) AS n,
       COUNT(*) FILTER (WHERE geom IS NOT NULL) AS point_resolved,
       COUNT(*) FILTER (WHERE publication_date IS NULL) AS publication_date_unverified,
       COUNT(*) FILTER (WHERE location_text IS NULL) AS locations_missing
FROM iris_staging.signal_ingest GROUP BY 1;

-- Spatial contract: zero violations.
SELECT source_id, ST_SRID(geom), ST_AsText(geom)
FROM iris_staging.signal_ingest
WHERE geom IS NOT NULL AND (ST_SRID(geom) <> 25832 OR NOT ST_IsValid(geom));

-- Traceable latest records (listing_date is NOT necessarily publication_date).
SELECT source_id, title, signal_type, publication_date, listing_date,
       decision_date, source_url, location_text, quality_flags
FROM iris_staging.signal_ingest ORDER BY listing_date DESC NULLS LAST LIMIT 20;

-- Examine the records requiring manual review.
SELECT source_id, title, quality_flags, location_text
FROM iris_staging.signal_ingest
WHERE COALESCE(array_length(quality_flags, 1), 0) > 0;
