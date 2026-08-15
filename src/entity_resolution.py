import pandas as pd
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"

NAUKRI_FILE = DATA_DIR / "source1_naukri_applicants.csv"
GIG_FILE = DATA_DIR / "source2_gig_workers.csv"
CBNEXUS_FILE = DATA_DIR / "source3_cbnexus_contacts.csv"

VALIDATED_MATCHES_FILE = (
    DOCS_DIR / "validated_matches.csv"
)

OUTPUT_FILE = (
    DOCS_DIR / "entity_resolution.csv"
)


# =========================================================
# Union-Find
# =========================================================

class UnionFind:

    def __init__(self):

        self.parent = {}
        self.rank = {}

    def add(self, item):

        if item not in self.parent:

            self.parent[item] = item
            self.rank[item] = 0

    def find(self, item):

        if self.parent[item] != item:

            self.parent[item] = self.find(
                self.parent[item]
            )

        return self.parent[item]

    def union(self, first, second):

        root_first = self.find(first)
        root_second = self.find(second)

        if root_first == root_second:
            return

        if self.rank[root_first] < self.rank[root_second]:

            self.parent[root_first] = root_second

        elif self.rank[root_first] > self.rank[root_second]:

            self.parent[root_second] = root_first

        else:

            self.parent[root_second] = root_first
            self.rank[root_first] += 1


# =========================================================
# Source loading
# =========================================================

def load_sources():

    naukri = pd.read_csv(
        NAUKRI_FILE,
        dtype=str
    )

    gig = pd.read_csv(
        GIG_FILE,
        dtype=str
    )

    cbnexus = pd.read_csv(
        CBNEXUS_FILE,
        dtype=str
    )

    return {
        "naukri": naukri,
        "gig": gig,
        "cbnexus": cbnexus,
    }


# =========================================================
# Create source-record identifiers
# =========================================================

def create_record_ids(sources):

    records = []

    for source_name, dataframe in sources.items():

        for index in dataframe.index:

            # +1 because the CSV data row starts after
            # the header row.
            row_number = index + 1

            record_id = (
                f"{source_name}:{row_number}"
            )

            records.append({
                "record_id": record_id,
                "source": source_name,
                "row_number": row_number,
            })

    return pd.DataFrame(records)


# =========================================================
# Apply validated HIGH-confidence matches
# =========================================================

def apply_validated_matches(
    union_find,
    validated_matches
):

    high_matches = validated_matches[
        validated_matches["decision"] == "APPROVE"
    ].copy()

    print(
        f"\nValidated matches available: "
        f"{len(high_matches)}"
    )

    for _, row in high_matches.iterrows():

        source_1 = str(
            row["source_1"]
        ).strip().lower()

        source_2 = str(
            row["source_2"]
        ).strip().lower()

        row_1 = int(
            float(row["row_1"])
        )

        row_2 = int(
            float(row["row_2"])
        )

        record_1 = (
            f"{source_1}:{row_1}"
        )

        record_2 = (
            f"{source_2}:{row_2}"
        )

        # Make sure both records exist
        union_find.add(record_1)
        union_find.add(record_2)

        union_find.union(
            record_1,
            record_2
        )

    return len(high_matches)


# =========================================================
# Assign stable person IDs
# =========================================================

def assign_person_ids(
    records,
    union_find
):

    # Group records by Union-Find root.
    groups = {}

    for record_id in union_find.parent:

        root = union_find.find(
            record_id
        )

        groups.setdefault(
            root,
            []
        ).append(record_id)

    # Sort groups deterministically.
    sorted_groups = sorted(
        groups.values(),
        key=lambda group: min(group)
    )

    person_mapping = {}

    for number, group in enumerate(
        sorted_groups,
        start=1
    ):

        person_id = (
            f"P{number:05d}"
        )

        for record_id in group:

            person_mapping[
                record_id
            ] = person_id

    records = records.copy()

    records["person_id"] = (
        records["record_id"]
        .map(person_mapping)
    )

    return records


# =========================================================
# Main
# =========================================================

def main():

    print("\n" + "=" * 80)
    print("FINAL ENTITY RESOLUTION")
    print("=" * 80)

    # -----------------------------------------------------
    # Load sources
    # -----------------------------------------------------

    sources = load_sources()

    print("\nSource record counts:")

    for source_name, dataframe in sources.items():

        print(
            f"{source_name}: "
            f"{len(dataframe)}"
        )

    # -----------------------------------------------------
    # Create record inventory
    # -----------------------------------------------------

    records = create_record_ids(
        sources
    )

    print(
        f"\nTotal source records: "
        f"{len(records)}"
    )

    # -----------------------------------------------------
    # Initialize Union-Find
    # -----------------------------------------------------

    union_find = UnionFind()

    for record_id in records[
        "record_id"
    ]:

        union_find.add(
            record_id
        )

    # -----------------------------------------------------
    # Load validated matches
    # -----------------------------------------------------

    validated_matches = pd.read_csv(
        VALIDATED_MATCHES_FILE,
        dtype=str
    )

    # -----------------------------------------------------
    # Apply approved matches
    # -----------------------------------------------------

    match_count = apply_validated_matches(
        union_find,
        validated_matches
    )

    # -----------------------------------------------------
    # Assign person IDs
    # -----------------------------------------------------

    result = assign_person_ids(
        records,
        union_find
    )

    # -----------------------------------------------------
    # Save result
    # -----------------------------------------------------

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    entity_count = (
        result["person_id"]
        .nunique()
    )

    multi_source_entities = (
        result.groupby(
            "person_id"
        )["source"]
        .nunique()
    )

    multi_source_count = (
        (multi_source_entities > 1)
        .sum()
    )

    print("\n" + "-" * 80)
    print("ENTITY RESOLUTION SUMMARY")
    print("-" * 80)

    print(
        f"Source records: "
        f"{len(result)}"
    )

    print(
        f"Validated HIGH matches used: "
        f"{match_count}"
    )

    print(
        f"Unique person entities: "
        f"{entity_count}"
    )

    print(
        f"Multi-source entities: "
        f"{multi_source_count}"
    )

    print(
        f"Single-source entities: "
        f"{entity_count - multi_source_count}"
    )

    print(
        "\nRecords by source:"
    )

    print(
        result[
            "source"
        ].value_counts()
    )

    print(
        "\nEntities by number of source records:"
    )

    print(
        result.groupby(
            "person_id"
        ).size()
        .value_counts()
        .sort_index()
    )

    print(
        f"\nSaved to:\n{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()