# Data Quality Report

## Overview

This report documents the data-quality issues identified while profiling and
integrating the three source CSV files used in the ConsultBae assignment.

The source systems contain inconsistent formatting, duplicate records,
missing values, malformed rows, conflicting information, and different
representations of the same values.

The goal was not to silently overwrite the original source data. Instead,
source values were preserved where appropriate, while normalized values were
used for matching and the master database.

---

# Source Files

1. `source1_naukri_applicants.csv`
2. `source2_gig_workers.csv`
3. `source3_cbnexus_contacts.csv`

---

# 1. Naukri Applicant Issues

## 1.1 Duplicate Nikhil Chopra record

Two Naukri records represent the same person:

- Source row 26
- Source row 36

Both contain:

- Name: Nikhil Chopra
- Phone: 9000000103
- Skills: Pandas, SQL, n8n
- Same city: NOIDA
- Same experience: 0.8

The email addresses differ:

- `alt.nikhil.chopra70@example.com`
- `nikhil.chopra70@example.com`

### Action taken

The records were treated as the same person during entity resolution because
the normalized phone number and other attributes strongly matched.

The source records were preserved separately while both were linked to the
same canonical person.

---

## 1.2 Duplicate Rohit Verma record

Two Naukri records represent the same person:

- Source row 24
- Source row 30

Both contain:

- Name: Rohit Verma
- Email: `rohit.verma13@mailtest.example.org`
- Phone: `9000000294`
- City: Bangalore
- Experience: 2.4

### Action taken

The duplicate records were linked to the same canonical person instead of
creating two master-person records.

---

## 1.3 Abbreviated name

Source row 24 contains:

`R. Verma`

while another record contains:

`Rohit Verma`

The email and phone match the Rohit Verma record.

### Action taken

Name normalization and stronger identifiers such as phone and email were used
to resolve the record to the same person.

The original source name was retained as raw source data.

---

## 1.4 Phone number formatting differences

Phone numbers appear in multiple formats, including:

- `9000000254`
- `919000000254`
- `+91-9000000131`

These represent the same 10-digit Indian phone number after normalization.

### Action taken

Phone numbers were normalized by:

- Removing non-numeric characters
- Removing the `91` country prefix when present
- Validating the final 10-digit number

This allowed phone numbers to be used reliably during entity resolution.

---

## 1.5 City formatting inconsistencies

Cities use inconsistent casing and formatting.

Examples:

- `PUNE`
- `pune`
- `Pune`
- `NOIDA`
- `Noida`
- `new delhi`
- `New Delhi`
- `GURGAON`
- `gurugram`
- `Bangalore`
- `Bengaluru`

Some values also contain trailing whitespace, for example:

- `gurugram `
- `Noida `

### Action taken

City values were trimmed and normalized for matching and searching.

Original source values were retained in the source records.

---

## 1.6 Applied Date format inconsistency

Applied dates are represented using multiple formats:

- `24-07-2026`
- `2026-08-08`
- `7 Jul 2026`
- `07/13/2026`
- `19 Jul 2026`

### Action taken

Dates were parsed using flexible date parsing during profiling rather than
assuming a single source format.

---

## 1.7 Future application dates

Some Naukri records contain dates after the current reference date of
16-Aug-2026.

Examples include:

- `21-08-2026`
- `22-08-2026`
- `2026-08-19`
- `08/21/2026`

### Action taken

These values were flagged as suspicious rather than silently changed because
the source data may represent test data or future-dated records.

---

## 1.8 Current CTC uses inconsistent units

The `Current CTC` column contains values that appear to use different units.

Examples:

- `417964`
- `332456`
- `775670`
- `4.2`
- `8.3`
- `11.2`
- `7.6`

The smaller values appear to represent CTC in lakhs while larger values appear
to represent an absolute monetary amount.

### Action taken

The original source value was preserved. The inconsistency was treated as a
data-quality issue rather than assuming a conversion without sufficient
evidence.

---

# 2. Gig Worker Issues

## 2.1 Completely blank row

Source row 12 contains no useful values.

All columns are empty:

- email
- worker name
- rate
- location
- status
- skill tags

### Action taken

The blank record was identified during profiling and excluded from meaningful
entity matching.

---

## 2.2 Malformed Isha Chopra row

Source row 20 is structurally corrupted.

Instead of:

```text
email | worker_name | rate | location | status | skill_tags

---

# 7. Automated Data Quality Audit Results

The implemented data-quality audit API was used to verify issues detected
during source-data profiling.

The audit currently reports the following high-severity issues:

| Source | Issue Type | Count |
|---|---|---:|
| CBNexus | INVALID_PHONE | 1 |
| Gig | INVALID_EMAIL | 1 |
| Gig | MISSING_EMAIL | 1 |
| Naukri | INVALID_PHONE | 18 |

### Examples from the audit

#### CBNexus

- Source row 15
- Issue: `INVALID_PHONE`
- Value detected: `Phone Number`

This corresponds to a repeated header row appearing inside the CBNexus data.

#### Gig

- Source row 13
- Issue: `MISSING_EMAIL`
- The email field is missing.

- Source row 19
- Issue: `INVALID_EMAIL`
- Value detected: `react, javascript, mysql`

This corresponds to the malformed Isha Chopra record where columns are
shifted.

#### Naukri

Examples of invalid phone records reported by the audit include:

- Source row 36: `09000000103`
- Source row 38: `09000000104`
- Source row 42: `09000000273`

The audit reports 18 Naukri records with invalid phone values in total.

### Handling

The issues were recorded in the data-quality audit rather than silently
deleting the source records. The problematic records remain traceable to
their source and row number for review.