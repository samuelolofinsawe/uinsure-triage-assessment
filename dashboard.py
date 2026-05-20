"""
dashboard.py — Dashboard statistics computation

Computes the views a support manager would look at first:
  - Ticket volume by category
  - Priority distribution (AI-suggested)
  - Open/escalated backlog
  - Recurring customer hotspots
  - Satisfaction patterns by category
  - Average resolution time by category
  - Customers at risk (3+ tickets, low satisfaction)
"""

import pandas as pd


def build_output_rows(
    df: pd.DataFrame,
    triage_results: list[dict],
    recurrence_map: dict[str, list[str]],
) -> list[dict]:
    """Merge original ticket data with AI triage results and recurrence flags."""
    if not triage_results:
        raise ValueError("Triage results are empty — AI triage may have failed.")

    triage_by_id = {r["ticket_id"]: r for r in triage_results}
    rows = []

    for _, ticket in df.iterrows():
        tid = ticket["ticket_id"]
        tr = triage_by_id.get(tid, {})
        prior = recurrence_map.get(tid, [])

        if not tr:
            print(f"Warning: no triage result found for {tid} — using defaults.")

        rows.append({
            "ticket_id": tid,
            "date_submitted": str(ticket["date_submitted"])[:10],
            "customer_id": ticket["customer_id"],
            "original_priority": ticket.get("priority", ""),
            "suggested_priority": tr.get("suggested_priority", "Unknown"),
            "original_category": ticket.get("category", ""),
            "suggested_category": tr.get("suggested_category", ""),
            "suggested_subcategory": tr.get("suggested_subcategory", ""),
            "status": ticket["status"],
            "recurrence_flag": bool(prior),
            "prior_tickets": prior,
            "explanation": tr.get("explanation", ""),
            "satisfaction_score": ticket.get("satisfaction_score"),
            "agent_assigned": ticket.get("agent_assigned", ""),
            "resolution_time_hours": ticket.get("resolution_time_hours"),
        })

    return rows


def compute_dashboard(df: pd.DataFrame, output_rows: list[dict]) -> dict:
    """Compute all dashboard statistics from the merged output rows."""
    if not output_rows:
        raise ValueError("No output rows to compute dashboard from.")

    out_df = pd.DataFrame(output_rows)
    total = len(df)
    open_tickets = df[df["status"].isin(["Open", "Escalated"])]
    recurring = out_df[out_df["recurrence_flag"] == True]

    # Customers at risk: 3+ tickets
    at_risk = []
    for cust, grp in df.groupby("customer_id"):
        if len(grp) >= 3:
            avg_sat = grp["satisfaction_score"].mean()
            at_risk.append({
                "customer_id": cust,
                "ticket_count": len(grp),
                "avg_satisfaction": round(avg_sat, 2) if not pd.isna(avg_sat) else None,
                "open_tickets": grp[grp["status"].isin(["Open", "Escalated"])]["ticket_id"].tolist(),
            })
    at_risk.sort(key=lambda x: x["ticket_count"], reverse=True)

    missing_priority_count = int(df["priority"].isna().sum())

    # Safe satisfaction average — handle fully missing data
    sat_mean = df["satisfaction_score"].mean()
    overall_sat = round(sat_mean, 2) if not pd.isna(sat_mean) else None

    return {
        "total_tickets": total,
        "missing_priority_count": missing_priority_count,
        "missing_priority_pct": round(missing_priority_count / total * 100, 1),
        "volume_by_category": out_df["suggested_category"].value_counts().to_dict(),
        "priority_distribution": out_df["suggested_priority"].value_counts().to_dict(),
        "open_backlog": {
            "total": len(open_tickets),
            "escalated": int((df["status"] == "Escalated").sum()),
            "by_priority": open_tickets["priority"].value_counts().to_dict(),
        },
        "recurring_customer_hotspots": (
            recurring.groupby("customer_id")["ticket_id"]
            .count()
            .sort_values(ascending=False)
            .head(5)
            .to_dict()
            if not recurring.empty
            else {}
        ),
        "satisfaction": {
            "overall_avg": overall_sat,
            "by_category": (
                df.groupby("category")["satisfaction_score"]
                .mean()
                .round(2)
                .dropna()
                .to_dict()
            ),
        },
        "avg_resolution_time_by_category": (
            df.groupby("category")["resolution_time_hours"]
            .mean()
            .round(1)
            .dropna()
            .to_dict()
        ),
        "customers_at_risk": at_risk[:5],
    }