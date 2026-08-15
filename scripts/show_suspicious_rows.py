import pandas as pd
from pathlib import Path
import re


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def normalize_phone(value):
    if pd.isna(value):
        return ""

    return re.sub(r"\D", "", str(value))


def inspect_gig_workers():

    path = DATA_DIR / "source2_gig_workers.csv"

    df = pd.read_csv(path)

    print("\n" + "=" * 80)
    print("GIG WORKERS - SUSPICIOUS RECORDS")
    print("=" * 80)

    # ---------------------------------------------------------
    # 1. Empty rows
    # ---------------------------------------------------------

    print("\n1. COMPLETELY EMPTY ROW")

    empty = df[df.isna().all(axis=1)]

    print(empty.to_string())

    # ---------------------------------------------------------
    # 2. Rows with email-looking problem
    # ---------------------------------------------------------

    print("\n2. POSSIBLY MALFORMED EMAIL RECORDS")

    email_mask = (
        df["email_id"]
        .notna()
        &
        ~df["email_id"]
        .astype(str)
        .str.match(
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        )
    )

    print(
        df.loc[
            email_mask
        ].to_string()
    )

    # ---------------------------------------------------------
    # 3. Suspicious status values
    # ---------------------------------------------------------

    print("\n3. STATUS VALUES")

    print(
        df[
            ["email_id", "worker_name", "location", "status"]
        ].to_string()
    )

    # ---------------------------------------------------------
    # 4. Location whitespace
    # ---------------------------------------------------------

    print("\n4. LOCATION VALUES WITH WHITESPACE")

    location_mask = (
        df["location"]
        .notna()
        &
        (
            df["location"].astype(str)
            !=
            df["location"].astype(str).str.strip()
        )
    )

    print(
        df.loc[
            location_mask,
            ["email_id", "worker_name", "location"]
        ].to_string()
    )


def inspect_naukri():

    path = DATA_DIR / "source1_naukri_applicants.csv"

    df = pd.read_csv(path)

    print("\n" + "=" * 80)
    print("NAUKRI - DUPLICATE PHONE RECORDS")
    print("=" * 80)

    df["_normalized_phone"] = (
        df["Phone"].apply(normalize_phone)
    )

    duplicate_mask = (
        df["_normalized_phone"]
        .duplicated(keep=False)
        &
        (df["_normalized_phone"] != "")
    )

    print(
        df.loc[
            duplicate_mask,
            [
                "Full Name",
                "Email",
                "Phone",
                "City",
                "_normalized_phone"
            ]
        ].to_string()
    )


def inspect_cbnexus():

    path = DATA_DIR / "source3_cbnexus_contacts.csv"

    df = pd.read_csv(path)

    print("\n" + "=" * 80)
    print("CBNEXUS - VERIFIED VALUES")
    print("=" * 80)

    print(
        df[
            ["Name", "Phone Number", "City", "Verified"]
        ].to_string()
    )


def main():

    inspect_gig_workers()
    inspect_naukri()
    inspect_cbnexus()


if __name__ == "__main__":
    main()