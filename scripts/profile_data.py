import pandas as pd
from pathlib import Path
import re


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


FILES = [
    "source1_naukri_applicants.csv",
    "source2_gig_workers.csv",
    "source3_cbnexus_contacts.csv",
]


def normalize_text(value):
    """Normalize basic text for profiling."""
    if pd.isna(value):
        return None

    return str(value).strip()


def check_email(email):
    """Basic email format check."""
    if pd.isna(email):
        return False

    email = str(email).strip()

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, email))


def phone_digits(phone):
    """Return only digits from a phone value."""
    if pd.isna(phone):
        return ""

    return re.sub(r"\D", "", str(phone))


def profile_file(file_name):
    file_path = DATA_DIR / file_name

    print("\n" + "=" * 80)
    print(f"FILE: {file_name}")
    print("=" * 80)

    df = pd.read_csv(file_path)

    # Basic information
    print(f"\nRows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    print("\nColumns:")
    for column in df.columns:
        print(f"  - {column}")

    # Missing values
    print("\nMissing values:")
    missing = df.isna().sum()

    for column, count in missing.items():
        print(f"  {column}: {count}")

    # Completely empty rows
    empty_rows = df.isna().all(axis=1).sum()

    print(f"\nCompletely empty rows: {empty_rows}")

    # Exact duplicate rows
    duplicate_rows = df.duplicated().sum()

    print(f"Exact duplicate rows: {duplicate_rows}")

    # Data types
    print("\nData types:")
    print(df.dtypes.to_string())

    # Unique values for smaller categorical columns
    print("\nUnique values:")
    for column in df.columns:

        if df[column].nunique(dropna=True) <= 15:
            values = df[column].dropna().astype(str).unique()

            print(f"\n{column}:")
            for value in values:
                print(f"  - {value}")

    # Email checks
    email_columns = [
        column for column in df.columns
        if "email" in column.lower()
    ]

    for column in email_columns:
        invalid_emails = (
            df[column]
            .dropna()
            .astype(str)
            .apply(lambda x: not check_email(x))
            .sum()
        )

        duplicate_emails = (
            df[column]
            .dropna()
            .astype(str)
            .str.strip()
            .str.lower()
            .duplicated()
            .sum()
        )

        print(f"\nEmail analysis: {column}")
        print(f"  Invalid email formats: {invalid_emails}")
        print(f"  Duplicate emails: {duplicate_emails}")

    # Phone checks
    phone_columns = [
        column for column in df.columns
        if "phone" in column.lower()
    ]

    for column in phone_columns:
        phone_data = df[column].dropna().apply(phone_digits)

        print(f"\nPhone analysis: {column}")

        print("  Digit lengths:")
        print(phone_data.str.len().value_counts().sort_index().to_string())

        duplicate_phones = phone_data[phone_data != ""].duplicated().sum()

        print(f"  Duplicate phone numbers: {duplicate_phones}")

    # Text whitespace checks
    print("\nWhitespace analysis:")

    for column in df.select_dtypes(include="object").columns:

        leading_or_trailing = (
            df[column]
            .dropna()
            .astype(str)
            .apply(lambda x: x != x.strip())
            .sum()
        )

        if leading_or_trailing > 0:
            print(
                f"  {column}: "
                f"{leading_or_trailing} values have leading/trailing spaces"
            )

    # Date analysis
    date_columns = [
        column for column in df.columns
        if "date" in column.lower()
    ]

    for column in date_columns:

        parsed_dates = pd.to_datetime(
            df[column],
            errors="coerce"
        )

        invalid_dates = (
            parsed_dates.isna() &
            df[column].notna()
        ).sum()

        print(f"\nDate analysis: {column}")
        print(f"  Invalid/unparseable dates: {invalid_dates}")

    print("\n" + "-" * 80)


def main():

    for file_name in FILES:
        try:
            profile_file(file_name)

        except Exception as error:
            print(f"\nERROR processing {file_name}:")
            print(error)


if __name__ == "__main__":
    main()