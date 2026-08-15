import pandas as pd
from pathlib import Path
import re


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


FILES = [
    "source1_naukri_applicants.csv",
    "source2_gig_workers.csv",
    "source3_cbnexus_contacts.csv",
]


def normalize_phone(value):
    if pd.isna(value):
        return ""

    return re.sub(r"\D", "", str(value))


def valid_email(value):
    if pd.isna(value):
        return False

    value = str(value).strip()

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return bool(re.match(pattern, value))


def inspect_file(file_name):

    path = DATA_DIR / file_name

    df = pd.read_csv(path)

    print("\n")
    print("=" * 90)
    print(f"INVESTIGATION: {file_name}")
    print("=" * 90)

    # ---------------------------------------------------------
    # 1. Completely empty rows
    # ---------------------------------------------------------

    empty_rows = df[df.isna().all(axis=1)]

    print("\n1. COMPLETELY EMPTY ROWS")

    if empty_rows.empty:
        print("None")

    else:
        print(empty_rows.to_string())

    # ---------------------------------------------------------
    # 2. Rows containing missing values
    # ---------------------------------------------------------

    missing_rows = df[df.isna().any(axis=1)]

    print("\n2. ROWS WITH MISSING VALUES")

    if missing_rows.empty:
        print("None")

    else:
        print(missing_rows.to_string())

    # ---------------------------------------------------------
    # 3. Email issues
    # ---------------------------------------------------------

    email_columns = [
        col for col in df.columns
        if "email" in col.lower()
    ]

    for column in email_columns:

        invalid = df[
            df[column].notna()
            & ~df[column].apply(valid_email)
        ]

        print(f"\n3. INVALID EMAILS - {column}")

        if invalid.empty:
            print("None")

        else:
            print(
                invalid[
                    [column]
                ].to_string()
            )

    # ---------------------------------------------------------
    # 4. Phone information
    # ---------------------------------------------------------

    phone_columns = [
        col for col in df.columns
        if "phone" in col.lower()
    ]

    for column in phone_columns:

        temp = df.copy()

        temp["_normalized_phone"] = (
            temp[column]
            .apply(normalize_phone)
        )

        print(f"\n4. PHONE ANALYSIS - {column}")

        print("\nPhone values and normalized values:")

        print(
            temp[
                [column, "_normalized_phone"]
            ].to_string()
        )

        duplicates = temp[
            temp["_normalized_phone"] != ""
        ]

        duplicates = duplicates[
            duplicates["_normalized_phone"].duplicated(
                keep=False
            )
        ]

        print("\nPotential duplicate phones:")

        if duplicates.empty:
            print("None")

        else:
            print(
                duplicates[
                    [column, "_normalized_phone"]
                ].to_string()
            )

    # ---------------------------------------------------------
    # 5. Whitespace issues
    # ---------------------------------------------------------

    print("\n5. LEADING/TRAILING WHITESPACE")

    found = False

    for column in df.select_dtypes(
        include=["object"]
    ).columns:

        mask = (
            df[column]
            .notna()
            & (
                df[column].astype(str)
                != df[column].astype(str).str.strip()
            )
        )

        if mask.any():

            found = True

            print(f"\nColumn: {column}")

            print(
                df.loc[
                    mask,
                    [column]
                ].to_string()
            )

    if not found:
        print("None")

    # ---------------------------------------------------------
    # 6. Date values
    # ---------------------------------------------------------

    date_columns = [
        col for col in df.columns
        if "date" in col.lower()
    ]

    for column in date_columns:

        print(f"\n6. DATE ANALYSIS - {column}")

        print(
            df[column]
            .dropna()
            .astype(str)
            .value_counts()
            .sort_index()
            .to_string()
        )

        parsed = pd.to_datetime(
            df[column],
            errors="coerce",
            format="mixed"
        )

        invalid = df[
            df[column].notna()
            & parsed.isna()
        ]

        print("\nActually invalid dates:")

        if invalid.empty:
            print("None")

        else:
            print(
                invalid[
                    [column]
                ].to_string()
            )

    # ---------------------------------------------------------
    # 7. Important categorical fields
    # ---------------------------------------------------------

    for column in df.columns:

        lower = column.lower()

        if any(
            word in lower
            for word in [
                "city",
                "location",
                "status",
                "verified"
            ]
        ):

            print(
                f"\n7. UNIQUE VALUES - {column}"
            )

            values = (
                df[column]
                .dropna()
                .astype(str)
                .unique()
            )

            for value in sorted(values):
                print(
                    repr(value)
                )


def main():

    for file_name in FILES:

        try:
            inspect_file(file_name)

        except Exception as error:

            print(
                f"\nERROR processing {file_name}:"
            )

            print(error)


if __name__ == "__main__":
    main()