## ADDED Requirements

### Requirement: Lawful HTML source acquisition
I REQUIRE the harvester to use only openly accessible HTTPS HTML from the UVP-Verbund host and to never bypass access controls. I REQUIRE it to enforce finite pagination and explicit HTTP timeouts, retry transient status failures with backoff, and report failures.

#### Scenario: Source rate-limits a request
- **GIVEN** a listing or detail request returns HTTP 429
- **WHEN** retrieval runs
- **THEN** the client retries within the configured bound and reports an unresolved failure if retries are exhausted

#### Scenario: Search produces no records
- **GIVEN** a valid empty search result
- **WHEN** retrieval runs
- **THEN** the pipeline produces no inserted records and reports zero eligible notices

### Requirement: Source identity and traceability
I REQUIRE each eligible record to have a stable source `docuuid`, original project title, canonical source URL, original payload excerpt, explicit date fields and signal type.

#### Scenario: A record appears on multiple pages
- **GIVEN** two listing pages contain the same `docuuid`
- **WHEN** the pages are processed
- **THEN** exactly one normalized record is produced for that ID

### Requirement: Strict domain and geographic filtering
I REQUIRE the harvester to admit only Saarland project pages concerning **heavy industrial restructuring approvals** or **power substation approvals**. I REQUIRE it to exclude generic wind-farm records, unrelated energy projects, and non-Saarland results.

#### Scenario: Irrelevant wind-farm approval
- **GIVEN** an approval about wind turbines without industrial transformation or substations
- **WHEN** classification runs
- **THEN** the record is not staged

### Requirement: Publication and decision dates are distinct
I REQUIRE that the harvester must not substitute an unlabeled search-list date or explicit decision date for a publication date. I REQUIRE it to leave unverified publication dates null and flag them.

#### Scenario: Listing and decision dates only
- **GIVEN** a UVP list date and `Datum der Entscheidung` but no explicit publication date
- **WHEN** transformation runs
- **THEN** `listing_date` and `decision_date` are populated, `publication_date` is null and `publication_date_not_verified` is emitted

### Requirement: Georeferencing must be evidence based
I REQUIRE the harvester to generate EPSG:25832 Point geometries for explicit, credible project coordinates, validate the coordinate pair and region, and record missing/invalid coordinates without silently using an approximate substitute.

#### Scenario: Ministry address but no project coordinates
- **GIVEN** a project with an authority address and no project point
- **WHEN** geometry is resolved
- **THEN** geometry is null and `unresolved_project_point` is present

#### Scenario: Latitude exceeds WGS84 range
- **GIVEN** source latitude of 91°
- **WHEN** geometry is resolved
- **THEN** no geometry is persisted and `invalid_coordinates` is present

### Requirement: Idempotent, transactional staging
I REQUIRE the PostgreSQL sink to use `(source_system, source_id)` uniqueness, parameterized statements and transactional upsert. I REQUIRE exact reruns to avoid duplicate records; changed records may update.

#### Scenario: Same harvest is loaded twice
- **GIVEN** four unique eligible signals
- **WHEN** the load runs twice with identical content hashes
- **THEN** four records remain and the second load reports zero writes

### Requirement: Reviewable delivery
I REQUIRE the project to include dependency/configuration instructions, no embedded credentials, tests, source mapping assumptions, representative output, validation SQL and a quality report.

#### Scenario: No production access
- **GIVEN** a reviewer with a Python environment and no database credentials
- **WHEN** fixture mode runs
- **THEN** repeatable JSONL and a quality report are generated without network access
