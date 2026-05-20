"""
recurrence.py — Rule-based recurrence detection

Two signals are used (deliberately rule-based, not AI — see ai_reflection.md):
  a) Explicit TKT-references in ticket_description text
  b) Same customer_id + same category appearing more than once

Rule-based is the right call here: the signal is deterministic, auditable,
and cheaper than embedding-based similarity. AI is reserved for language
understanding tasks where rules fall short.
"""

import re
import pandas as pd


def build_recurrence_map(df: pd.DataFrame) -> dict[str, list[str]]:
    """
    Returns a map of ticket_id → list of related prior ticket IDs.
    An empty list means no recurrence detected.
    """
    ref_pattern = re.compile(r"TKT-\d+")
    recurrence_map: dict[str, list[str]] = {}

    for _, row in df.iterrows():
        tid = row["ticket_id"]
        desc = str(row.get("ticket_description", "") or "")

        # Signal (a): explicit references in description text
        explicit_refs = [r for r in ref_pattern.findall(desc) if r != tid]

        # Signal (b): other tickets from the same customer in the same category
        customer = row["customer_id"]
        category = row["category"]
        implicit_refs = df[
            (df["customer_id"] == customer)
            & (df["category"] == category)
            & (df["ticket_id"] != tid)
        ]["ticket_id"].tolist()

        recurrence_map[tid] = list(set(explicit_refs + implicit_refs))

    return recurrence_map
