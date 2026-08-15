import pandas as pd
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "docs" / "match_review.csv"
OUTPUT_FILE = PROJECT_ROOT / "docs" / "validated_matches.csv"


def normalize_text(value):
    if pd.isna(value):
        return ""

    return str(value).strip().lower()


def main():

    df = pd.read_csv(INPUT_FILE)

    high = df[
        df["confidence"] == "HIGH"
    ].copy()

    print("\n" + "=" * 90)
    print("HIGH-CONFIDENCE MATCH VALIDATION")
    print("=" * 90)

    print(f"\nHigh-confidence candidates: {len(high)}")

    validation_results = []

    for _, row in high.iterrows():

        name_1 = normalize_text(row["name_1"])
        name_2 = normalize_text(row["name_2"])

        email_1 = normalize_text(row["email_1"])
        email_2 = normalize_text(row["email_2"])

        phone_1 = normalize_text(row["phone_1"])
        phone_2 = normalize_text(row["phone_2"])

        name_match = (
            bool(name_1)
            and bool(name_2)
            and name_1 == name_2
        )

        email_match = (
            bool(email_1)
            and bool(email_2)
            and email_1 == email_2
        )

        phone_match = (
            bool(phone_1)
            and bool(phone_2)
            and phone_1 == phone_2
        )

        # Strong identifiers should not contradict each other.
        conflict = False
        conflict_reason = ""

        if email_1 and email_2 and email_1 != email_2:
            conflict = True
            conflict_reason = "Conflicting emails"

        if phone_1 and phone_2 and phone_1 != phone_2:
            conflict = True

            if conflict_reason:
                conflict_reason += "; "

            conflict_reason += "Conflicting phones"

        if conflict:

            decision = "REVIEW"

        else:

            decision = "APPROVE"

        validation_results.append({

            "source_1": row["source_1"],
            "row_1": row["row_1"],
            "name_1": row["name_1"],
            "email_1": row["email_1"],
            "phone_1": row["phone_1"],

            "source_2": row["source_2"],
            "row_2": row["row_2"],
            "name_2": row["name_2"],
            "email_2": row["email_2"],
            "phone_2": row["phone_2"],

            "original_score": row["score"],
            "reasons": row["reasons"],

            "name_match": name_match,
            "email_match": email_match,
            "phone_match": phone_match,

            "decision": decision,
            "conflict_reason": conflict_reason
        })

    result = pd.DataFrame(
        validation_results
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nValidation results:")

    print(
        result["decision"]
        .value_counts()
    )

    print(
        f"\nSaved to:\n{OUTPUT_FILE}"
    )

    # ---------------------------------------------------------
    # Show conflicts
    # ---------------------------------------------------------

    conflicts = result[
        result["decision"] == "REVIEW"
    ]

    print(
        "\n" + "-" * 90
    )

    print(
        "HIGH-CONFIDENCE MATCHES REQUIRING REVIEW"
    )

    print(
        "-" * 90
    )

    if conflicts.empty:

        print("None")

    else:

        print(
            conflicts.to_string(
                index=False
            )
        )


if __name__ == "__main__":
    main()