import re
from decimal import Decimal, InvalidOperation

import pandas as pd


# ---------------------------------------------------------
# Generic text normalization
# ---------------------------------------------------------

def normalize_text(value):
    """
    Basic text normalization.

    - Converts missing values to empty string
    - Removes leading/trailing whitespace
    - Converts repeated whitespace to one space
    - Converts text to lowercase
    """

    if pd.isna(value):
        return ""

    value = str(value).strip().lower()

    value = re.sub(r"\s+", " ", value)

    return value


# ---------------------------------------------------------
# Name normalization
# ---------------------------------------------------------

def normalize_name(value):
    """
    Normalize a person's name for matching.
    """

    value = normalize_text(value)

    # Remove punctuation but preserve spaces
    value = re.sub(
        r"[^a-z0-9 ]",
        "",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    ).strip()

    return value


# ---------------------------------------------------------
# Email normalization
# ---------------------------------------------------------

def normalize_email(value):
    """
    Normalize email addresses.
    """

    value = normalize_text(value)

    return value


# ---------------------------------------------------------
# Phone normalization
# ---------------------------------------------------------

def normalize_phone(value):
    """
    Normalize Indian phone numbers.

    Handles:
    - 9000000254
    - 919000000254
    - +91-9000000254
    - 919000000254.0
    - scientific notation such as 9.19000000254E11

    Returns a normalized 10-digit number when possible.
    """

    if pd.isna(value):
        return ""

    value = str(value).strip()

    if not value:
        return ""

    # Handle scientific notation safely.
    if "e" in value.lower():

        try:
            value = format(
                Decimal(value),
                "f"
            )

        except InvalidOperation:
            pass

    # Remove a trailing .0 created by numeric conversion.
    if value.endswith(".0"):
        value = value[:-2]

    # Keep digits only.
    digits = re.sub(
        r"\D",
        "",
        value
    )

    # Remove Indian country code.
    if (
        len(digits) == 12
        and digits.startswith("91")
    ):
        digits = digits[2:]

    return digits


# ---------------------------------------------------------
# City normalization
# ---------------------------------------------------------

CITY_ALIASES = {
    "pune": "pune",

    "noida": "noida",

    "delhi": "delhi",
    "new delhi": "delhi",

    "gurgaon": "gurgaon",
    "gurugram": "gurgaon",

    "bangalore": "bengaluru",
    "bengaluru": "bengaluru",
}


def normalize_city(value):
    """
    Normalize known city variations.
    """

    value = normalize_text(value)

    if not value:
        return ""

    return CITY_ALIASES.get(
        value,
        value
    )


# ---------------------------------------------------------
# Status normalization
# ---------------------------------------------------------

STATUS_ALIASES = {
    "active": "active",
    "inactive": "inactive",
    "paused": "paused",
}


def normalize_status(value):
    """
    Normalize Gig Worker status values.
    """

    value = normalize_text(value)

    if not value:
        return ""

    return STATUS_ALIASES.get(
        value,
        value
    )


# ---------------------------------------------------------
# Verification normalization
# ---------------------------------------------------------

VERIFIED_ALIASES = {
    "y": True,
    "yes": True,
    "verified": True,

    "n": False,
    "no": False,
}


def normalize_verified(value):
    """
    Convert CBNexus verification values to boolean.

    Returns:
        True
        False
        None for unknown values
    """

    value = normalize_text(value)

    if value in VERIFIED_ALIASES:
        return VERIFIED_ALIASES[value]

    return None


# ---------------------------------------------------------
# Email validation
# ---------------------------------------------------------

def is_valid_email(value):
    """
    Basic email format validation.
    """

    value = normalize_email(value)

    if not value:
        return False

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return bool(
        re.match(
            pattern,
            value
        )
    )


# ---------------------------------------------------------
# Phone validation
# ---------------------------------------------------------

def is_valid_phone(value):
    """
    Check whether a normalized phone contains
    exactly 10 digits.
    """

    value = normalize_phone(value)

    return (
        len(value) == 10
        and value.isdigit()
    )