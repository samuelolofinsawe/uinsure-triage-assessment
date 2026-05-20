"""
loader.py — Data loading and cleaning for support_tickets.csv

Handles two known data quality issues in the source file:
  1. Rows with 13 fields (comma inside a free-text cell breaks the CSV boundary)
  2. satisfaction_score column containing ticket_description text in 5 rows
     due to a missing field — detected during investigation, repaired here.
"""

import pandas as pd


def load_tickets(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, on_bad_lines="skip")

    # Repair rows where ticket_description text has leaked into satisfaction_score
    # (caused by a missing field earlier in those rows — see investigation_note.md)
    corrupt_mask = (
        pd.to_numeric(df["satisfaction_score"], errors="coerce").isna()
        & df["satisfaction_score"].notna()
    )
    if corrupt_mask.any():
        df.loc[corrupt_mask, "ticket_description"] = df.loc[corrupt_mask, "satisfaction_score"]
        df.loc[corrupt_mask, "satisfaction_score"] = None

    df["satisfaction_score"] = pd.to_numeric(df["satisfaction_score"], errors="coerce")
    df["date_submitted"] = pd.to_datetime(df["date_submitted"], errors="coerce")

    # Normalise inconsistent subcategory capitalisation e.g. "setup" vs "Setup"
    df["subcategory"] = df["subcategory"].str.strip().str.title()

    # Merge synonym variants introduced by inconsistent data entry
    df["subcategory"] = df["subcategory"].replace({"Webhooks": "Webhook"})
    df["subcategory"] = df["subcategory"].replace({"Overage Charges": "Overage"})

    return df
