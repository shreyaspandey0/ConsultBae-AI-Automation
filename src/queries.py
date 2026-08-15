"""
ConsultBae Master Database - Query Layer

Provides reusable, read-only queries for:
- Person lookup
- Multi-source entity lookup
- Candidate search
- Source record inspection
- Data-quality issue reporting
- Database summary
"""

from pathlib import Path
import sqlite3
from typing import Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "database" / "consultbae.db"


# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    """
    Create a SQLite connection with row access by column name.
    """
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    # Make sure foreign-key enforcement is enabled.
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def rows_to_dicts(rows) -> list[dict]:
    """Convert sqlite rows into normal dictionaries."""
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# 1. Person lookup
# ---------------------------------------------------------------------------

def get_person(person_id: str) -> Optional[dict]:
    """
    Get the canonical person record for a person ID.
    """
    query = """
        SELECT
            person_id,
            canonical_name,
            canonical_email,
            canonical_phone,
            canonical_city,
            created_at
        FROM persons
        WHERE person_id = ?
    """

    with get_connection() as connection:
        row = connection.execute(query, (person_id,)).fetchone()

    return dict(row) if row else None


# ---------------------------------------------------------------------------
# 2. Get all source records belonging to a person
# ---------------------------------------------------------------------------

def get_person_sources(person_id):
    connection = get_connection()

    query = """
        SELECT
            sr.source,
            sr.source_row,
            sr.raw_name AS name,
            sr.raw_email AS email,
            sr.raw_phone AS phone,
            sr.raw_city AS city
        FROM source_records sr
        WHERE sr.person_id = ?
        ORDER BY sr.source, sr.source_row
    """

    rows = connection.execute(query, (person_id,)).fetchall()
    connection.close()

    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# 3. Search people
# ---------------------------------------------------------------------------

def search_people(search_term: str) -> list[dict]:
    """
    Search canonical people by name, email, phone, or city.
    """
    pattern = f"%{search_term.strip()}%"

    query = """
        SELECT
            person_id,
            canonical_name,
            canonical_email,
            canonical_phone,
            canonical_city
        FROM persons
        WHERE
            canonical_name LIKE ?
            OR canonical_email LIKE ?
            OR canonical_phone LIKE ?
            OR canonical_city LIKE ?
        ORDER BY canonical_name
    """

    with get_connection() as connection:
        rows = connection.execute(
            query,
            (pattern, pattern, pattern, pattern)
        ).fetchall()

    return rows_to_dicts(rows)


# ---------------------------------------------------------------------------
# 4. Get multi-source entities
# ---------------------------------------------------------------------------

def get_multi_source_entities() -> list[dict]:
    """
    Return people whose records exist in more than one source.
    """
    query = """
        SELECT
            p.person_id,
            p.canonical_name,
            p.canonical_email,
            p.canonical_phone,
            p.canonical_city,
            COUNT(DISTINCT sr.source) AS source_count,
            GROUP_CONCAT(DISTINCT sr.source) AS sources
        FROM persons p
        JOIN source_records sr
            ON p.person_id = sr.person_id
        GROUP BY
            p.person_id,
            p.canonical_name,
            p.canonical_email,
            p.canonical_phone,
            p.canonical_city
        HAVING COUNT(DISTINCT sr.source) > 1
        ORDER BY source_count DESC, p.canonical_name
    """

    with get_connection() as connection:
        rows = connection.execute(query).fetchall()

    return rows_to_dicts(rows)


# ---------------------------------------------------------------------------
# 5. Get source statistics
# ---------------------------------------------------------------------------

def get_source_statistics() -> list[dict]:
    """
    Return record counts by source.
    """
    query = """
        SELECT
            source,
            COUNT(*) AS record_count
        FROM source_records
        GROUP BY source
        ORDER BY source
    """

    with get_connection() as connection:
        rows = connection.execute(query).fetchall()

    return rows_to_dicts(rows)


# ---------------------------------------------------------------------------
# 6. Find candidates by city
# ---------------------------------------------------------------------------

def find_candidates_by_city(city: str) -> list[dict]:
    """
    Find candidates whose canonical city matches the supplied city.
    """
    query = """
        SELECT
            p.person_id,
            p.canonical_name,
            p.canonical_email,
            p.canonical_phone,
            p.canonical_city
        FROM persons p
        WHERE LOWER(TRIM(p.canonical_city)) = LOWER(TRIM(?))
        ORDER BY p.canonical_name
    """

    with get_connection() as connection:
        rows = connection.execute(query, (city,)).fetchall()

    return rows_to_dicts(rows)


# ---------------------------------------------------------------------------
# 7. Find candidates by skill
# ---------------------------------------------------------------------------

def find_candidates_by_skill(skill: str) -> list[dict]:
    """
    Find candidates whose skills contain the supplied skill.

    Searches both Naukri skills and Gig worker skill tags.
    """
    pattern = f"%{skill.strip().lower()}%"

    query = """
        SELECT DISTINCT
            p.person_id,
            p.canonical_name,
            p.canonical_email,
            p.canonical_phone,
            p.canonical_city
        FROM persons p
        JOIN source_records sr
            ON p.person_id = sr.person_id
        LEFT JOIN naukri_applications n
            ON sr.record_id = n.record_id
        LEFT JOIN gig_workers g
            ON sr.record_id = g.record_id
        WHERE
            LOWER(COALESCE(n.skills, '')) LIKE ?
            OR LOWER(COALESCE(g.skill_tags, '')) LIKE ?
        ORDER BY p.canonical_name
    """

    with get_connection() as connection:
        rows = connection.execute(
            query,
            (pattern, pattern)
        ).fetchall()

    return rows_to_dicts(rows)


# ---------------------------------------------------------------------------
# 8. Get Naukri details for a person
# ---------------------------------------------------------------------------

def get_naukri_details(person_id: str) -> list[dict]:
    """
    Return Naukri-specific information for a person.
    """
    query = """
        SELECT
            p.person_id,
            p.canonical_name,
            sr.record_id,
            sr.source_row,
            n.experience_years,
            n.current_ctc,
            n.applied_date,
            n.skills
        FROM persons p
        JOIN source_records sr
            ON p.person_id = sr.person_id
        JOIN naukri_applications n
            ON sr.record_id = n.record_id
        WHERE p.person_id = ?
        ORDER BY sr.source_row
    """

    with get_connection() as connection:
        rows = connection.execute(query, (person_id,)).fetchall()

    return rows_to_dicts(rows)


# ---------------------------------------------------------------------------
# 9. Get Gig worker details for a person
# ---------------------------------------------------------------------------

def get_gig_details(person_id: str) -> list[dict]:
    """
    Return Gig worker-specific information for a person.
    """
    query = """
        SELECT
            p.person_id,
            p.canonical_name,
            sr.record_id,
            sr.source_row,
            g.rate,
            g.location,
            g.status,
            g.skill_tags
        FROM persons p
        JOIN source_records sr
            ON p.person_id = sr.person_id
        JOIN gig_workers g
            ON sr.record_id = g.record_id
        WHERE p.person_id = ?
        ORDER BY sr.source_row
    """

    with get_connection() as connection:
        rows = connection.execute(query, (person_id,)).fetchall()

    return rows_to_dicts(rows)


# ---------------------------------------------------------------------------
# 10. Get CBNexus details for a person
# ---------------------------------------------------------------------------

def get_cbnexus_details(person_id: str) -> list[dict]:
    """
    Return CBNexus-specific information for a person.
    """
    query = """
        SELECT
            p.person_id,
            p.canonical_name,
            sr.record_id,
            sr.source_row,
            c.verified,
            c.projects_completed
        FROM persons p
        JOIN source_records sr
            ON p.person_id = sr.person_id
        JOIN cbnexus_contacts c
            ON sr.record_id = c.record_id
        WHERE p.person_id = ?
        ORDER BY sr.source_row
    """

    with get_connection() as connection:
        rows = connection.execute(query, (person_id,)).fetchall()

    return rows_to_dicts(rows)


# ---------------------------------------------------------------------------
# 11. Data-quality issue report
# ---------------------------------------------------------------------------

def get_data_quality_issues(
    source: Optional[str] = None,
    severity: Optional[str] = None
) -> list[dict]:
    """
    Return recorded data-quality issues.

    Optional filters:
        source
        severity
    """

    query = """
        SELECT
            issue_id,
            source,
            source_row,
            issue_type,
            severity,
            details,
            status,
            created_at
        FROM data_quality_issues
        WHERE 1 = 1
    """

    parameters = []

    if source:
        query += " AND LOWER(source) = LOWER(?)"
        parameters.append(source)

    if severity:
        query += " AND UPPER(severity) = UPPER(?)"
        parameters.append(severity)

    query += """
        ORDER BY
            CASE UPPER(severity)
                WHEN 'HIGH' THEN 1
                WHEN 'MEDIUM' THEN 2
                WHEN 'LOW' THEN 3
                ELSE 4
            END,
            source,
            source_row
    """

    with get_connection() as connection:
        rows = connection.execute(
            query,
            parameters
        ).fetchall()

    return rows_to_dicts(rows)


# ---------------------------------------------------------------------------
# 12. Data-quality summary
# ---------------------------------------------------------------------------

def get_data_quality_summary() -> list[dict]:
    """
    Return data-quality issue counts by source and issue type.
    """
    query = """
        SELECT
            source,
            issue_type,
            severity,
            COUNT(*) AS issue_count
        FROM data_quality_issues
        GROUP BY
            source,
            issue_type,
            severity
        ORDER BY
            source,
            issue_type
    """

    with get_connection() as connection:
        rows = connection.execute(query).fetchall()

    return rows_to_dicts(rows)


# ---------------------------------------------------------------------------
# 13. Database summary
# ---------------------------------------------------------------------------

def get_database_summary() -> dict:
    """
    Return high-level master database statistics.
    """

    queries = {
        "persons": "SELECT COUNT(*) FROM persons",
        "source_records": "SELECT COUNT(*) FROM source_records",
        "naukri_applications": "SELECT COUNT(*) FROM naukri_applications",
        "gig_workers": "SELECT COUNT(*) FROM gig_workers",
        "cbnexus_contacts": "SELECT COUNT(*) FROM cbnexus_contacts",
        "data_quality_issues": "SELECT COUNT(*) FROM data_quality_issues",
        "multi_source_entities": """
            SELECT COUNT(*)
            FROM (
                SELECT person_id
                FROM source_records
                GROUP BY person_id
                HAVING COUNT(DISTINCT source) > 1
            )
        """
    }

    summary = {}

    with get_connection() as connection:
        for name, query in queries.items():
            summary[name] = connection.execute(query).fetchone()[0]

    return summary


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main():
    """
    Small command-line demonstration of the query layer.
    """

    print("=" * 70)
    print("CONSULTBAE MASTER DATABASE - QUERY LAYER")
    print("=" * 70)

    # Database summary
    print("\nDATABASE SUMMARY")
    print("-" * 70)

    summary = get_database_summary()

    for key, value in summary.items():
        print(f"{key}: {value}")

    # Source statistics
    print("\nSOURCE STATISTICS")
    print("-" * 70)

    for row in get_source_statistics():
        print(
            f"{row['source']}: "
            f"{row['record_count']} records"
        )

    # Multi-source entities
    print("\nMULTI-SOURCE ENTITIES")
    print("-" * 70)

    multi_source = get_multi_source_entities()

    print(f"Count: {len(multi_source)}")

    for row in multi_source[:10]:
        print(
            f"{row['person_id']} | "
            f"{row['canonical_name']} | "
            f"{row['source_count']} sources | "
            f"{row['sources']}"
        )

    # Data-quality summary
    print("\nDATA-QUALITY SUMMARY")
    print("-" * 70)

    quality = get_data_quality_summary()

    for row in quality:
        print(
            f"{row['source']} | "
            f"{row['issue_type']} | "
            f"{row['severity']} | "
            f"{row['issue_count']}"
        )

    print("\n" + "=" * 70)
    print("QUERY LAYER CHECK COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()