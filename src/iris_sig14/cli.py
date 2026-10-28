"""CLI: always safe offline demo, opt-in live and PostgreSQL modes."""
import argparse
import json
import logging
import os
from .pipeline import run_pipeline, write_artifacts
from .source import BASE_URL
from .store import PostgresSink, SQLiteDemoSink


def main(argv=None):
    p = argparse.ArgumentParser(description="IRIS-SIG-14 Saarland HTML harvester")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--fixtures", metavar="DIR", help="Offline deterministic fixtures")
    group.add_argument("--live", action="store_true", help="Live UVP public search; may be rate-limited")
    p.add_argument("--source-url", default=os.getenv("IRIS_SOURCE_URL", BASE_URL))
    p.add_argument("--max-pages", type=int, default=int(os.getenv("IRIS_MAX_PAGES", "10")))
    p.add_argument("--timeout", type=float, default=float(os.getenv("IRIS_TIMEOUT_SECONDS", "15")))
    p.add_argument("--delay", type=float, default=float(os.getenv("IRIS_DELAY_SECONDS", "1.5")))
    p.add_argument("--seed-verified-projects", action="store_true", help="Also check 3 verified UVP detail pages in live mode")
    p.add_argument("--db-url", default=os.getenv("DATABASE_URL"), help="Never commit the URL or password")
    p.add_argument("--sqlite-demo", help="Optional local SQLite file; NOT production/PostGIS")
    p.add_argument("--output", default="samples/output.jsonl")
    p.add_argument("--report", default="samples/quality_report.json")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.db_url and args.sqlite_demo:
        p.error("Select only one database destination")
    try:
        signals, report = run_pipeline(offline_dir=args.fixtures, source_url=args.source_url,
            seed_urls=args.seed_verified_projects, max_pages=args.max_pages,
            timeout=args.timeout, delay=args.delay)
    except (OSError, ValueError, RuntimeError) as exc:
        from pathlib import Path
        report = {"mode": "fixture" if args.fixtures else "live", "source": args.source_url,
                  "fatal_error": f"{type(exc).__name__}: {exc}", "db": "NOT LOADED"}
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        logging.error("Ingestion stopped before DB load: %s", report["fatal_error"])
        return 2
    # No destructive load on failed discovery; an empty clean response creates no changes.
    if args.db_url or args.sqlite_demo:
        sink = PostgresSink(args.db_url) if args.db_url else SQLiteDemoSink(args.sqlite_demo)
        try:
            report["db"] = sink.load(signals)
        finally:
            sink.close()
    write_artifacts(signals, report, args.output, args.report)
    print(json.dumps({k:v for k,v in report.items() if k not in ("fetch_failures", "malformed")}, indent=2))
    if report["fetch_failures"] or report["malformed"]:
        print(f"Warnings: fetch_failures={len(report['fetch_failures'])} malformed={len(report['malformed'])}")
    return 0 if not report["fetch_failures"] and not report["malformed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
