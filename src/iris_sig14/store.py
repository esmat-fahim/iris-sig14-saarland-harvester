"""Production PostgreSQL/PostGIS sink and portable SQLite demo/test sink."""
import json
from dataclasses import asdict
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine, text
from .models import Signal


POSTGRES_UPSERT = """
INSERT INTO iris_staging.signal_ingest (
 source_system, source_id, signal_type, title, publication_date,
 listing_date, decision_date, source_url, location_text, geom,
 quality_flags, source_payload, content_hash
) VALUES (
 :source_system, :source_id, :signal_type, :title, :publication_date,
 :listing_date, :decision_date, :source_url, :location_text,
 -- Cast before checking NULL: psycopg sends untyped NULL parameters and
 -- PostgreSQL cannot infer their types from an "IS NULL" expression.
 CASE WHEN CAST(:easting AS double precision) IS NULL
           OR CAST(:northing AS double precision) IS NULL THEN NULL
      ELSE ST_SetSRID(ST_MakePoint(
          CAST(:easting AS double precision),
          CAST(:northing AS double precision)), 25832) END,
 CAST(:quality_flags AS text[]), CAST(:source_payload AS jsonb), :content_hash
)
ON CONFLICT (source_system, source_id)
DO UPDATE SET
 signal_type = EXCLUDED.signal_type, title = EXCLUDED.title,
 publication_date = EXCLUDED.publication_date, listing_date = EXCLUDED.listing_date,
 decision_date = EXCLUDED.decision_date, source_url = EXCLUDED.source_url,
 location_text = EXCLUDED.location_text, geom = EXCLUDED.geom,
 quality_flags = EXCLUDED.quality_flags, source_payload = EXCLUDED.source_payload,
 content_hash = EXCLUDED.content_hash, updated_at = NOW()
WHERE iris_staging.signal_ingest.content_hash IS DISTINCT FROM EXCLUDED.content_hash
RETURNING source_id
"""


def params(signal: Signal):
    # Keep datetime.date values as native Python dates for psycopg's DATE adapter.
    d = asdict(signal)
    d["source_payload"] = json.dumps(d["source_payload"], ensure_ascii=False)
    return d


class PostgresSink:
    """Requires target schema installed using sql/001_signal_ingest.sql.

    Does not create or modify an unknown production schema automatically.
    """
    def __init__(self, database_url: str):
        if not database_url.startswith(("postgresql+psycopg://", "postgresql://")):
            raise ValueError("PostgresSink requires PostgreSQL URL")
        self.engine = create_engine(database_url, pool_pre_ping=True)

    def load(self, signals: list[Signal]):
        counts = {"written": 0, "unchanged": 0}
        with self.engine.begin() as con:
            for s in signals:
                result = con.execute(text(POSTGRES_UPSERT), params(s)).first()
                counts["written" if result else "unchanged"] += 1
        return counts

    def close(self):
        self.engine.dispose()


class SQLiteDemoSink:
    """No PostGIS; only a demonstrator for upsert/idempotency behavior."""
    def __init__(self, path: str | Path):
        self.con = sqlite3.connect(str(path))
        self.con.execute("""
        CREATE TABLE IF NOT EXISTS signal_ingest_demo (
          source_system TEXT NOT NULL, source_id TEXT NOT NULL,
          content_hash TEXT NOT NULL, document_json TEXT NOT NULL,
          PRIMARY KEY(source_system, source_id)
        )""")
        self.con.commit()

    def load(self, signals: list[Signal]):
        counts = {"written": 0, "unchanged": 0}
        with self.con:
            for s in signals:
                payload = json.dumps(s.export(), ensure_ascii=False)
                cursor = self.con.execute("""
                    INSERT INTO signal_ingest_demo(source_system,source_id,content_hash,document_json)
                    VALUES (?,?,?,?)
                    ON CONFLICT(source_system,source_id) DO UPDATE SET
                       content_hash=excluded.content_hash, document_json=excluded.document_json
                    WHERE signal_ingest_demo.content_hash != excluded.content_hash
                """, (s.source_system, s.source_id, s.content_hash, payload))
                counts["written" if cursor.rowcount else "unchanged"] += 1
        return counts

    def count(self):
        return self.con.execute("SELECT COUNT(*) FROM signal_ingest_demo").fetchone()[0]

    def close(self):
        self.con.close()
