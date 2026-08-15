PRAGMA foreign_keys = ON;


-- =========================================================
-- MASTER PERSON TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS persons (

    person_id TEXT PRIMARY KEY,

    canonical_name TEXT,

    canonical_email TEXT,

    canonical_phone TEXT,

    canonical_city TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- SOURCE RECORD INVENTORY
-- =========================================================

CREATE TABLE IF NOT EXISTS source_records (

    record_id TEXT PRIMARY KEY,

    person_id TEXT NOT NULL,

    source TEXT NOT NULL,

    source_row INTEGER NOT NULL,

    raw_name TEXT,

    raw_email TEXT,

    raw_phone TEXT,

    raw_city TEXT,

    FOREIGN KEY (person_id)
        REFERENCES persons(person_id)
);


-- =========================================================
-- NAUKRI SOURCE
-- =========================================================

CREATE TABLE IF NOT EXISTS naukri_applications (

    record_id TEXT PRIMARY KEY,

    experience_years REAL,

    current_ctc REAL,

    applied_date TEXT,

    skills TEXT,

    FOREIGN KEY (record_id)
        REFERENCES source_records(record_id)
);


-- =========================================================
-- GIG WORKER SOURCE
-- =========================================================

CREATE TABLE IF NOT EXISTS gig_workers (

    record_id TEXT PRIMARY KEY,

    rate TEXT,

    location TEXT,

    status TEXT,

    skill_tags TEXT,

    FOREIGN KEY (record_id)
        REFERENCES source_records(record_id)
);


-- =========================================================
-- CBNEXUS SOURCE
-- =========================================================

CREATE TABLE IF NOT EXISTS cbnexus_contacts (

    record_id TEXT PRIMARY KEY,

    verified INTEGER,

    projects_completed INTEGER,

    FOREIGN KEY (record_id)
        REFERENCES source_records(record_id)
);


-- =========================================================
-- DATA QUALITY / AUDIT TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS data_quality_issues (

    issue_id INTEGER PRIMARY KEY AUTOINCREMENT,

    source TEXT NOT NULL,

    source_row INTEGER,

    issue_type TEXT NOT NULL,

    severity TEXT NOT NULL,

    details TEXT,

    status TEXT DEFAULT 'OPEN',

    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- USEFUL INDEXES
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_source_records_person
ON source_records(person_id);


CREATE INDEX IF NOT EXISTS idx_source_records_source
ON source_records(source);


CREATE INDEX IF NOT EXISTS idx_quality_source
ON data_quality_issues(source);


CREATE INDEX IF NOT EXISTS idx_quality_type
ON data_quality_issues(issue_type);