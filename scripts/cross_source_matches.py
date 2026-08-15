import pandas as pd
from pathlib import Path
import re
from difflib import SequenceMatcher


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


FILES = {
    "naukri": "source1_naukri_applicants.csv",
    "gig": "source2_gig_workers.csv",
    "cbnexus": "source3_cbnexus_contacts.csv",
}


def normalize_text(value):
    if pd.isna(value):
        return ""

    value = str(value).strip().lower()

    value = re.sub(r"\s+", " ", value)

    return value


def normalize_name(value):
    value = normalize_text(value)

    value = re.sub(r"[^a-z0-9 ]", "", value)

    return value


def normalize_email(value):
    return normalize_text(value)


def normalize_phone(value):
    if pd.isna(value):
        return ""

    digits = re.sub(r"\D", "", str(value))

    # Handle Indian country code
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]

    return digits


def similarity(a, b):
    if not a or not b:
        return 0

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()


def prepare_naukri(df):

    return pd.DataFrame({
        "source": "naukri",
        "source_row": df.index + 2,
        "name": df["Full Name"],
        "email": df["Email"],
        "phone": df["Phone"],
        "city": df["City"],

        "norm_name": df["Full Name"].apply(normalize_name),
        "norm_email": df["Email"].apply(normalize_email),
        "norm_phone": df["Phone"].apply(normalize_phone),
        "norm_city": df["City"].apply(normalize_text),
    })


def prepare_gig(df):

    return pd.DataFrame({
        "source": "gig",
        "source_row": df.index + 2,
        "name": df["worker_name"],
        "email": df["email_id"],
        "phone": "",
        "city": df["location"],

        "norm_name": df["worker_name"].apply(normalize_name),
        "norm_email": df["email_id"].apply(normalize_email),
        "norm_phone": "",
        "norm_city": df["location"].apply(normalize_text),
    })


def prepare_cbnexus(df):

    return pd.DataFrame({
        "source": "cbnexus",
        "source_row": df.index + 2,
        "name": df["Name"],
        "email": "",
        "phone": df["Phone Number"],
        "city": df["City"],

        "norm_name": df["Name"].apply(normalize_name),
        "norm_email": "",
        "norm_phone": df["Phone Number"].apply(normalize_phone),
        "norm_city": df["City"].apply(normalize_text),
    })


def compare_records(a, b):

    reasons = []
    score = 0

    # Email match
    if (
        a["norm_email"]
        and
        b["norm_email"]
        and
        a["norm_email"] == b["norm_email"]
    ):
        score += 60
        reasons.append("exact email")

    # Phone match
    if (
        a["norm_phone"]
        and
        b["norm_phone"]
        and
        a["norm_phone"] == b["norm_phone"]
    ):
        score += 60
        reasons.append("exact phone")

    # Name match
    if (
        a["norm_name"]
        and
        b["norm_name"]
        and
        a["norm_name"] == b["norm_name"]
    ):
        score += 25
        reasons.append("exact name")

    # Name similarity
    elif a["norm_name"] and b["norm_name"]:

        name_similarity = similarity(
            a["norm_name"],
            b["norm_name"]
        )

        if name_similarity >= 0.85:

            score += 15

            reasons.append(
                f"similar name ({name_similarity:.2f})"
            )

    # City match
    if (
        a["norm_city"]
        and
        b["norm_city"]
        and
        a["norm_city"] == b["norm_city"]
    ):
        score += 10
        reasons.append("same city")

    return score, reasons


def main():

    naukri = pd.read_csv(
        DATA_DIR / FILES["naukri"]
    )

    gig = pd.read_csv(
        DATA_DIR / FILES["gig"]
    )

    cbnexus = pd.read_csv(
        DATA_DIR / FILES["cbnexus"]
    )

    datasets = [
        prepare_naukri(naukri),
        prepare_gig(gig),
        prepare_cbnexus(cbnexus),
    ]

    all_records = pd.concat(
        datasets,
        ignore_index=True
    )

    print("\n" + "=" * 100)
    print("CROSS-SOURCE MATCH ANALYSIS")
    print("=" * 100)

    # ---------------------------------------------------------
    # Compare every record with every other record
    # ---------------------------------------------------------

    matches = []

    for i in range(len(all_records)):

        for j in range(i + 1, len(all_records)):

            a = all_records.iloc[i]
            b = all_records.iloc[j]

            # Only compare different sources
            if a["source"] == b["source"]:
                continue

            score, reasons = compare_records(
                a,
                b
            )

            if score >= 25:

                matches.append({
                    "source_1": a["source"],
                    "row_1": a["source_row"],
                    "name_1": a["name"],
                    "email_1": a["email"],
                    "phone_1": a["phone"],

                    "source_2": b["source"],
                    "row_2": b["source_row"],
                    "name_2": b["name"],
                    "email_2": b["email"],
                    "phone_2": b["phone"],

                    "score": score,
                    "reasons": ", ".join(reasons),
                })

    result = pd.DataFrame(matches)

    if result.empty:

        print("\nNo potential cross-source matches found.")

    else:

        result = result.sort_values(
            by="score",
            ascending=False
        )

        print(
            "\nPotential matches:\n"
        )

        print(
            result.to_string(
                index=False
            )
        )

        output_path = (
            DATA_DIR.parent
            / "docs"
            / "cross_source_matches.csv"
        )

        result.to_csv(
            output_path,
            index=False
        )

        print(
            f"\nSaved match analysis to:"
            f"\n{output_path}"
        )


if __name__ == "__main__":
    main()