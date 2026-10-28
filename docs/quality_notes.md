# QA handoff and reviewer notes

- **Traceability:** UUID + original link + date slots + source excerpt retained in JSON output.
- **Expected issues:** 3 of 3 public GreenSteel cases lack independently verified *publication dates* and exact project point geometry in the inspected rendered HTML; source listing and decision dates remain separately recorded.
- **Source contradiction:** 'GreenSteel EAF Dillingen' detail says furnace at Völklingen; leave location contextual and flag.
- **No invented current signal:** the substation parser is test-covered with a clearly synthetic case; the available inspected search page did not establish an actual substation approval.
- **Completeness:** HTML-only UVP scope excludes PDFs and municipal notices; an optional second compliant source would be needed for comprehensive Saarland approvals.
- **Live access:** the public search and details were inspected through web results; direct Python runtime access could not be demonstrated. The re-created HTML test fixtures are not exact snapshots.
- **Database access:** the proposed local schema targets PostgreSQL 16/PostGIS 3.4; no production schema or live DB integration was accessible.
- **Suggested final smoke test:** execute `iris-sig14 --live --max-pages 2 --delay 2` from a network-enabled machine, inspect page-level results and source URLs, adjust extraction if DOM differs, run PG SQL and check count unchanged on second run. Do not circumvent 403/429.
