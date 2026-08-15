import sqlite3
import re
from pathlib import Path

import pandas as pd


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
DATABASE_DIR = PROJECT_ROOT / "database"

DB_FILE = DATABASE_DIR / "consultbae.db"
SCHEMA_FILE = DATABASE_DIR / "schema.sql"

ENTITY_FILE = DOCS_DIR / "entity_resolution.csv"

NAUKRI_FILE = DATA_DIR / "source1_naukri_applicants.csv"
GIG_FILE = DATA_DIR / "source2_gig_workers.csv"
CBNEXUS_FILE = DATA_DIR / "source3_cbnexus_contacts.csv"


# =========================================================
# NORMALIZATION HELPERS
# =========================================================

def clean_text(value):
    """Return stripped text or None for empty values."""

    if pd.isna(value):
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


def normalize_name(value):
    """Normalize a person's name."""

    value = clean_text(value)

    if value is None:
        return None

    return " ".join(value.lower().split())


def normalize_email(value):
    """Normalize an email address."""

    value = clean_text(value)

    if value is None:
        return None

    return value.lower()


def normalize_phone(value):
    """
    Normalize Indian phone numbers.

    Handles:
    - 10-digit numbers
    - +91-XXXXXXXXXX
    - +91 XXXXXXXXXX
    - numbers stored in scientific notation
    """

    value = clean_text(value)

    if value is None:
        return None

    # Handle values such as 9.000000254E9
    try:
        if re.fullmatch(
            r"[+-]?\d+(?:\.\d+)?[eE][+-]?\d+",
            value
        ):
            value = str(
                int(
                    float(value)
                )
            )

    except (ValueError, OverflowError):
        pass

    # Handle values such as 9000000254.0
    if re.fullmatch(
        r"\d+\.0",
        value
    ):
        value = value.split(".")[0]

    digits = re.sub(
        r"\D",
        "",
        value
    )

    # Remove Indian country code.
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]

    # Valid Indian mobile number.
    if len(digits) == 10:
        return digits

    return None


def normalize_city(value):
    """Normalize city/location text."""

    value = clean_text(value)

    if value is None:
        return None

    return " ".join(
        value.lower().split()
    )


def parse_float(value):
    """Safely convert a value to float."""

    value = clean_text(value)

    if value is None:
        return None

    try:

        value = re.sub(
            r"[^\d.\-]",
            "",
            value
        )

        if not value:
            return None

        return float(value)

    except (ValueError, TypeError):

        return None


def parse_int(value):
    """Safely convert a value to integer."""

    value = clean_text(value)

    if value is None:
        return None

    try:

        return int(
            float(value)
        )

    except (ValueError, TypeError):

        return None


def normalize_verified(value):
    """Convert verification values into SQLite-friendly 0/1."""

    value = clean_text(value)

    if value is None:
        return None

    normalized = value.lower()

    if normalized in {
        "yes",
        "y",
        "verified",
        "true",
        "1"
    }:
        return 1

    if normalized in {
        "no",
        "n",
        "not verified",
        "false",
        "0"
    }:
        return 0

    return None


# =========================================================
# DATABASE SETUP
# =========================================================

def create_database():

    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Rebuild database from scratch so the pipeline
    # remains deterministic and reproducible.
    if DB_FILE.exists():
        DB_FILE.unlink()

    connection = sqlite3.connect(
        DB_FILE
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    with open(
        SCHEMA_FILE,
        "r",
        encoding="utf-8"
    ) as schema_file:

        schema = schema_file.read()

    connection.executescript(
        schema
    )

    return connection


# =========================================================
# LOAD SOURCE DATA
# =========================================================

def load_sources():

    naukri = pd.read_csv(
        NAUKRI_FILE,
        dtype=str,
        keep_default_na=True
    )

    gig = pd.read_csv(
        GIG_FILE,
        dtype=str,
        keep_default_na=True
    )

    cbnexus = pd.read_csv(
        CBNEXUS_FILE,
        dtype=str,
        keep_default_na=True
    )

    return {
        "naukri": naukri,
        "gig": gig,
        "cbnexus": cbnexus,
    }


# =========================================================
# LOAD ENTITY RESOLUTION
# =========================================================

def load_entity_resolution():

    entity_df = pd.read_csv(
        ENTITY_FILE,
        dtype=str
    )

    required_columns = {
        "record_id",
        "source",
        "row_number",
        "person_id",
    }

    missing = (
        required_columns
        - set(entity_df.columns)
    )

    if missing:

        raise ValueError(
            "Missing entity-resolution columns: "
            f"{missing}"
        )

    return entity_df


# =========================================================
# BUILD SOURCE RECORD LOOKUP
# =========================================================

def build_record_lookup(
    sources,
    entity_df
):

    lookup = {}

    for _, entity in entity_df.iterrows():

        source = entity["source"]

        row_number = int(
            float(
                entity["row_number"]
            )
        )

        if source not in sources:

            raise ValueError(
                f"Unknown source: {source}"
            )

        dataframe = sources[
            source
        ]

        row_index = row_number - 1

        if (
            row_index < 0
            or row_index >= len(dataframe)
        ):

            raise ValueError(
                f"Invalid row reference: "
                f"{source}:{row_number}"
            )

        row = dataframe.iloc[
            row_index
        ]

        lookup[
            entity["record_id"]
        ] = {
            "person_id": entity["person_id"],
            "source": source,
            "row_number": row_number,
            "row": row,
        }

    return lookup


# =========================================================
# CANONICAL PERSON VALUES
# =========================================================

def first_available(values):

    for value in values:

        if value is not None:
            return value

    return None


def build_persons(
    entity_df,
    record_lookup
):

    grouped = {}

    for _, entity in entity_df.iterrows():

        person_id = entity["person_id"]

        record = record_lookup[
            entity["record_id"]
        ]

        row = record["row"]
        source = record["source"]

        grouped.setdefault(
            person_id,
            []
        ).append(
            (
                source,
                row
            )
        )

    persons = []

    for person_id, records in grouped.items():

        names = []
        emails = []
        phones = []
        cities = []

        for source, row in records:

            if source == "naukri":

                names.append(
                    normalize_name(
                        row.get("Full Name")
                    )
                )

                emails.append(
                    normalize_email(
                        row.get("Email")
                    )
                )

                phones.append(
                    normalize_phone(
                        row.get("Phone")
                    )
                )

                cities.append(
                    normalize_city(
                        row.get("City")
                    )
                )

            elif source == "gig":

                names.append(
                    normalize_name(
                        row.get("worker_name")
                    )
                )

                emails.append(
                    normalize_email(
                        row.get("email_id")
                    )
                )

                phones.append(
                    None
                )

                cities.append(
                    normalize_city(
                        row.get("location")
                    )
                )

            elif source == "cbnexus":

                names.append(
                    normalize_name(
                        row.get("Name")
                    )
                )

                emails.append(
                    None
                )

                phones.append(
                    normalize_phone(
                        row.get("Phone Number")
                    )
                )

                cities.append(
                    normalize_city(
                        row.get("City")
                    )
                )

        persons.append(
            (
                person_id,
                first_available(names),
                first_available(emails),
                first_available(phones),
                first_available(cities),
            )
        )

    return persons


# =========================================================
# INSERT PERSONS
# =========================================================

def insert_persons(
    connection,
    persons
):

    connection.executemany(
        """
        INSERT INTO persons (
            person_id,
            canonical_name,
            canonical_email,
            canonical_phone,
            canonical_city
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        persons
    )


# =========================================================
# INSERT SOURCE RECORDS
# =========================================================

def insert_source_records(
    connection,
    entity_df,
    record_lookup
):

    records = []

    for _, entity in entity_df.iterrows():

        record_id = entity[
            "record_id"
        ]

        record = record_lookup[
            record_id
        ]

        source = record[
            "source"
        ]

        row = record[
            "row"
        ]

        raw_name = None
        raw_email = None
        raw_phone = None
        raw_city = None

        if source == "naukri":

            raw_name = clean_text(
                row.get("Full Name")
            )

            raw_email = clean_text(
                row.get("Email")
            )

            raw_phone = clean_text(
                row.get("Phone")
            )

            raw_city = clean_text(
                row.get("City")
            )

        elif source == "gig":

            raw_name = clean_text(
                row.get("worker_name")
            )

            raw_email = clean_text(
                row.get("email_id")
            )

            raw_city = clean_text(
                row.get("location")
            )

        elif source == "cbnexus":

            raw_name = clean_text(
                row.get("Name")
            )

            raw_phone = clean_text(
                row.get("Phone Number")
            )

            raw_city = clean_text(
                row.get("City")
            )

        records.append(
            (
                record_id,
                record["person_id"],
                source,
                record["row_number"],
                raw_name,
                raw_email,
                raw_phone,
                raw_city,
            )
        )

    connection.executemany(
        """
        INSERT INTO source_records (
            record_id,
            person_id,
            source,
            source_row,
            raw_name,
            raw_email,
            raw_phone,
            raw_city
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        records
    )


# =========================================================
# INSERT NAUKRI DATA
# =========================================================

def insert_naukri(
    connection,
    sources,
    entity_df
):

    rows = []

    naukri = sources[
        "naukri"
    ]

    filtered = entity_df[
        entity_df["source"] == "naukri"
    ]

    for _, entity in filtered.iterrows():

        row_number = int(
            float(
                entity["row_number"]
            )
        )

        row = naukri.iloc[
            row_number - 1
        ]

        rows.append(
            (
                entity["record_id"],
                parse_float(
                    row.get(
                        "Experience (Years)"
                    )
                ),
                parse_float(
                    row.get(
                        "Current CTC"
                    )
                ),
                clean_text(
                    row.get(
                        "Applied Date"
                    )
                ),
                clean_text(
                    row.get(
                        "Skills"
                    )
                ),
            )
        )

    connection.executemany(
        """
        INSERT INTO naukri_applications (
            record_id,
            experience_years,
            current_ctc,
            applied_date,
            skills
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        rows
    )


# =========================================================
# INSERT GIG DATA
# =========================================================

def insert_gig(
    connection,
    sources,
    entity_df
):

    rows = []

    gig = sources[
        "gig"
    ]

    filtered = entity_df[
        entity_df["source"] == "gig"
    ]

    for _, entity in filtered.iterrows():

        row_number = int(
            float(
                entity["row_number"]
            )
        )

        row = gig.iloc[
            row_number - 1
        ]

        rows.append(
            (
                entity["record_id"],
                clean_text(
                    row.get("rate")
                ),
                clean_text(
                    row.get("location")
                ),
                clean_text(
                    row.get("status")
                ),
                clean_text(
                    row.get("skill_tags")
                ),
            )
        )

    connection.executemany(
        """
        INSERT INTO gig_workers (
            record_id,
            rate,
            location,
            status,
            skill_tags
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        rows
    )


# =========================================================
# INSERT CBNEXUS DATA
# =========================================================

def insert_cbnexus(
    connection,
    sources,
    entity_df
):

    rows = []

    cbnexus = sources[
        "cbnexus"
    ]

    filtered = entity_df[
        entity_df["source"] == "cbnexus"
    ]

    for _, entity in filtered.iterrows():

        row_number = int(
            float(
                entity["row_number"]
            )
        )

        row = cbnexus.iloc[
            row_number - 1
        ]

        rows.append(
            (
                entity["record_id"],
                normalize_verified(
                    row.get("Verified")
                ),
                parse_int(
                    row.get(
                        "Projects Completed"
                    )
                ),
            )
        )

    connection.executemany(
        """
        INSERT INTO cbnexus_contacts (
            record_id,
            verified,
            projects_completed
        )
        VALUES (?, ?, ?)
        """,
        rows
    )


# =========================================================
# DATA QUALITY AUDIT
# =========================================================

def add_issue(
    connection,
    source,
    source_row,
    issue_type,
    severity,
    details
):

    connection.execute(
        """
        INSERT INTO data_quality_issues (
            source,
            source_row,
            issue_type,
            severity,
            details
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            source,
            source_row,
            issue_type,
            severity,
            details,
        )
    )


def audit_source_data(
    connection,
    sources
):

    # =====================================================
    # NAUKRI
    # =====================================================

    naukri = sources[
        "naukri"
    ]

    for index, row in naukri.iterrows():

        source_row = index + 1

        email = clean_text(
            row.get("Email")
        )

        phone = clean_text(
            row.get("Phone")
        )

        applied_date = clean_text(
            row.get("Applied Date")
        )

        city = clean_text(
            row.get("City")
        )

        # Email validation
        if email is None:

            add_issue(
                connection,
                "naukri",
                source_row,
                "MISSING_EMAIL",
                "HIGH",
                "Email is missing."
            )

        elif "@" not in email:

            add_issue(
                connection,
                "naukri",
                source_row,
                "INVALID_EMAIL",
                "HIGH",
                f"Invalid email: {email}"
            )

        # Phone validation
        if phone is None:

            add_issue(
                connection,
                "naukri",
                source_row,
                "MISSING_PHONE",
                "HIGH",
                "Phone is missing."
            )

        elif normalize_phone(phone) is None:

            add_issue(
                connection,
                "naukri",
                source_row,
                "INVALID_PHONE",
                "HIGH",
                f"Invalid phone: {phone}"
            )

        # Whitespace
        if city and city != city.strip():

            add_issue(
                connection,
                "naukri",
                source_row,
                "WHITESPACE",
                "LOW",
                "City contains leading/trailing whitespace."
            )

        # Date validation
        if applied_date:

            parsed = pd.to_datetime(
                applied_date,
                errors="coerce",
                format="mixed",
                dayfirst=True
            )

            if pd.isna(parsed):

                add_issue(
                    connection,
                    "naukri",
                    source_row,
                    "INVALID_DATE",
                    "MEDIUM",
                    f"Invalid Applied Date: {applied_date}"
                )

    # =====================================================
    # GIG WORKERS
    # =====================================================

    gig = sources[
        "gig"
    ]

    for index, row in gig.iterrows():

        source_row = index + 1

        email = clean_text(
            row.get("email_id")
        )

        location = clean_text(
            row.get("location")
        )

        if email is None:

            add_issue(
                connection,
                "gig",
                source_row,
                "MISSING_EMAIL",
                "HIGH",
                "Email is missing."
            )

        elif "@" not in email:

            add_issue(
                connection,
                "gig",
                source_row,
                "INVALID_EMAIL",
                "HIGH",
                f"Invalid email: {email}"
            )

        if location and location != location.strip():

            add_issue(
                connection,
                "gig",
                source_row,
                "WHITESPACE",
                "LOW",
                "Location contains leading/trailing whitespace."
            )

    # =====================================================
    # CBNEXUS
    # =====================================================

    cbnexus = sources[
        "cbnexus"
    ]

    for index, row in cbnexus.iterrows():

        source_row = index + 1

        phone = clean_text(
            row.get("Phone Number")
        )

        city = clean_text(
            row.get("City")
        )

        if phone is None:

            add_issue(
                connection,
                "cbnexus",
                source_row,
                "MISSING_PHONE",
                "HIGH",
                "Phone number is missing."
            )

        elif normalize_phone(phone) is None:

            add_issue(
                connection,
                "cbnexus",
                source_row,
                "INVALID_PHONE",
                "HIGH",
                f"Invalid phone: {phone}"
            )

        if city and city != city.strip():

            add_issue(
                connection,
                "cbnexus",
                source_row,
                "WHITESPACE",
                "LOW",
                "City contains leading/trailing whitespace."
            )


# =========================================================
# DATABASE VALIDATION
# =========================================================

def validate_database(
    connection
):

    print(
        "\n"
        + "=" * 70
    )

    print(
        "DATABASE VALIDATION"
    )

    print(
        "=" * 70
    )

    expected_counts = {

        "persons": 66,

        "source_records": 105,

        "naukri_applications": 42,

        "gig_workers": 32,

        "cbnexus_contacts": 31,
    }

    # =====================================================
    # TABLE COUNTS
    # =====================================================

    for table, expected in expected_counts.items():

        cursor = connection.execute(
            f"SELECT COUNT(*) FROM {table}"
        )

        actual = cursor.fetchone()[0]

        status = (
            "PASS"
            if actual == expected
            else "FAIL"
        )

        print(
            f"{table:<25} "
            f"expected={expected:<3} "
            f"actual={actual:<3} "
            f"[{status}]"
        )

        if actual != expected:

            raise AssertionError(
                f"{table}: expected "
                f"{expected}, got {actual}"
            )

    # =====================================================
    # MISSING PERSON IDs
    # =====================================================

    missing_person_ids = connection.execute(
        """
        SELECT COUNT(*)
        FROM source_records
        WHERE person_id IS NULL
           OR TRIM(person_id) = ''
        """
    ).fetchone()[0]

    print(
        f"Missing person IDs: "
        f"{missing_person_ids}"
    )

    if missing_person_ids != 0:

        raise AssertionError(
            "Some source records have missing person IDs."
        )

    # =====================================================
    # FOREIGN KEY CHECK
    # =====================================================

    fk_errors = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    print(
        f"Foreign key errors: "
        f"{len(fk_errors)}"
    )

    if fk_errors:

        raise AssertionError(
            f"Foreign key errors detected: "
            f"{fk_errors}"
        )

    # =====================================================
    # DUPLICATE SOURCE RECORD IDs
    # =====================================================

    duplicates = connection.execute(
        """
        SELECT record_id, COUNT(*)
        FROM source_records
        GROUP BY record_id
        HAVING COUNT(*) > 1
        """
    ).fetchall()

    print(
        f"Duplicate source record IDs: "
        f"{len(duplicates)}"
    )

    if duplicates:

        raise AssertionError(
            "Duplicate source record IDs detected."
        )

    # =====================================================
    # MULTI-SOURCE ENTITIES
    # =====================================================

    multi_source = connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT person_id
            FROM source_records
            GROUP BY person_id
            HAVING COUNT(DISTINCT source) > 1
        )
        """
    ).fetchone()[0]

    print(
        f"Multi-source entities: "
        f"{multi_source}"
    )

    print(
        "\nAll database integrity checks passed."
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "\n"
        + "=" * 70
    )

    print(
        "CONSULTBAE MASTER DATABASE BUILD"
    )

    print(
        "=" * 70
    )

    print(
        f"\nDatabase:\n{DB_FILE}"
    )

    # =====================================================
    # LOAD SOURCE FILES
    # =====================================================

    sources = load_sources()

    print(
        "\nSource files loaded:"
    )

    for source, dataframe in sources.items():

        print(
            f"{source:<10} "
            f"{len(dataframe)} records"
        )

    # =====================================================
    # LOAD ENTITY RESOLUTION MAP
    # =====================================================

    entity_df = load_entity_resolution()

    print(
        f"\nEntity-resolution records: "
        f"{len(entity_df)}"
    )

    print(
        f"Unique person IDs: "
        f"{entity_df['person_id'].nunique()}"
    )

    # =====================================================
    # CREATE DATABASE
    # =====================================================

    connection = create_database()

    try:

        # -------------------------------------------------
        # Build source record lookup
        # -------------------------------------------------

        record_lookup = build_record_lookup(
            sources,
            entity_df
        )

        # -------------------------------------------------
        # Build master persons
        # -------------------------------------------------

        persons = build_persons(
            entity_df,
            record_lookup
        )

        insert_persons(
            connection,
            persons
        )

        # -------------------------------------------------
        # Insert source records
        # -------------------------------------------------

        insert_source_records(
            connection,
            entity_df,
            record_lookup
        )

        # -------------------------------------------------
        # Insert Naukri records
        # -------------------------------------------------

        insert_naukri(
            connection,
            sources,
            entity_df
        )

        # -------------------------------------------------
        # Insert Gig Worker records
        # -------------------------------------------------

        insert_gig(
            connection,
            sources,
            entity_df
        )

        # -------------------------------------------------
        # Insert CBNexus records
        # -------------------------------------------------

        insert_cbnexus(
            connection,
            sources,
            entity_df
        )

        # -------------------------------------------------
        # Run data-quality audit
        # -------------------------------------------------

        audit_source_data(
            connection,
            sources
        )

        # -------------------------------------------------
        # Save changes
        # -------------------------------------------------

        connection.commit()

        # -------------------------------------------------
        # Validate database
        # -------------------------------------------------

        validate_database(
            connection
        )

        # -------------------------------------------------
        # Data-quality summary
        # -------------------------------------------------

        issue_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM data_quality_issues
            """
        ).fetchone()[0]

        print(
            f"\nData-quality issues recorded: "
            f"{issue_count}"
        )

        print(
            f"\nDatabase successfully created:\n"
            f"{DB_FILE}"
        )

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()