# Entity Resolution Rules

## Objective

The goal is to identify records belonging to the same real-world
person across the Naukri, Gig Worker, and CBNexus source systems.

## Identifier Normalization

Before matching:

- Names are trimmed, lowercased, and normalized.
- Emails are trimmed and lowercased.
- Phone numbers are converted to digits only.
- Indian +91 country codes are normalized to the 10-digit number.
- City values are normalized separately from the raw source value.

## Matching Rules

### High Confidence

A record is considered a strong match when:

1. Normalized email matches exactly, or
2. Normalized phone number matches exactly.

Additional matching fields such as name and city are used as
supporting evidence.

### Medium Confidence

Records with:

- exact normalized name
- same normalized city

are considered candidate matches but are not automatically merged
without supporting evidence.

### Review

Records with only fuzzy/similar names are not automatically merged.

### Conflicts

Conflicting strong identifiers are not automatically merged.

## Auditability

Original source records are preserved, while normalized values are
used for matching.

Each merged person retains links to the source records that
contributed to the master record.