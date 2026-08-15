import pandas as pd
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "docs" / "cross_source_matches.csv"
OUTPUT_FILE = PROJECT_ROOT / "docs" / "match_review.csv"


def classify_match(row):

    reasons = str(row["reasons"]).lower()
    score = int(row["score"])

    has_email = "exact email" in reasons
    has_phone = "exact phone" in reasons
    has_exact_name = "exact name" in reasons
    has_same_city = "same city" in reasons
    has_similar_name = "similar name" in reasons

    # ---------------------------------------------------------
    # HIGH CONFIDENCE
    # ---------------------------------------------------------

    if has_email or has_phone:

        return "HIGH", "Strong identifier matched"

    # ---------------------------------------------------------
    # MEDIUM CONFIDENCE
    # ---------------------------------------------------------

    if (
        has_exact_name
        and has_same_city
    ):

        return (
            "MEDIUM",
            "Exact name and same city; requires supporting evidence"
        )

    # ---------------------------------------------------------
    # REVIEW
    # ---------------------------------------------------------

    if has_similar_name:

        return (
            "REVIEW",
            "Name similarity alone is insufficient for automatic merge"
        )

    # ---------------------------------------------------------
    # FALLBACK
    # ---------------------------------------------------------

    if score >= 25:

        return (
            "REVIEW",
            "Potential match requires manual validation"
        )

    return (
        "REJECT",
        "Insufficient matching evidence"
    )


def main():

    if not INPUT_FILE.exists():

        print(
            "Match file not found:"
        )

        print(INPUT_FILE)

        return

    df = pd.read_csv(INPUT_FILE)

    classifications = df.apply(
        classify_match,
        axis=1,
        result_type="expand"
    )

    classifications.columns = [
        "confidence",
        "decision_reason"
    ]

    result = pd.concat(
        [
            df,
            classifications
        ],
        axis=1
    )

    # Put strongest matches first
    confidence_order = {
        "HIGH": 0,
        "MEDIUM": 1,
        "REVIEW": 2,
        "REJECT": 3,
    }

    result["_order"] = result[
        "confidence"
    ].map(confidence_order)

    result = result.sort_values(
        by="_order"
    )

    result = result.drop(
        columns=["_order"]
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        "\nMatch classification completed."
    )

    print(
        "\nConfidence counts:"
    )

    print(
        result[
            "confidence"
        ].value_counts()
    )

    print(
        f"\nSaved to:\n{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()