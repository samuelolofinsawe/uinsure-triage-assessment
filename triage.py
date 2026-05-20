#!/usr/bin/env python3
"""
triage.py — Support Triage Assistant entry point

Usage:
    python triage.py support_tickets.csv
    python triage.py support_tickets.csv --output-csv results.csv --output-html report.html

Reads ANTHROPIC_API_KEY from .env file automatically.
"""

import argparse
import os
import sys
import pandas as pd
from dotenv import load_dotenv

from loader import load_tickets
from recurrence import build_recurrence_map
from ai_triage import triage_all
from dashboard import build_output_rows, compute_dashboard
from renderer import render_html

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Support Triage Assistant")
    parser.add_argument("csv", help="Path to support_tickets.csv")
    parser.add_argument("--output-csv", default="triage_output.csv")
    parser.add_argument("--output-html", default="dashboard.html")
    args = parser.parse_args()

    # Check input file exists before doing anything
    if not os.path.exists(args.csv):
        print(f"Error: file not found — '{args.csv}'")
        print("Usage: python triage.py support_tickets.csv")
        sys.exit(1)

    try:
        print(f"\n Loading tickets from: {args.csv}")
        df = load_tickets(args.csv)
        print(f"   {len(df)} tickets loaded ({df['priority'].isna().sum()} missing priority labels)")

        print("\n Detecting recurrence patterns...")
        recurrence_map = build_recurrence_map(df)
        recurring_count = sum(1 for v in recurrence_map.values() if v)
        print(f"   {recurring_count} tickets flagged as recurrences")

        print("\n Running AI triage (Claude)...")
        triage_results = triage_all(df)

        print("\n Computing dashboard stats...")
        output_rows = build_output_rows(df, triage_results, recurrence_map)
        dashboard = compute_dashboard(df, output_rows)

        pd.DataFrame(output_rows).to_csv(args.output_csv, index=False)
        print(f"\n Per-ticket CSV  -> {args.output_csv}")

        render_html(output_rows, dashboard, args.output_html)
        print(f" Dashboard HTML  -> {args.output_html}")

        _print_summary(dashboard)

    except ValueError as e:
        print(f"\nData error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"\nRuntime error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(0)


def _print_summary(dashboard: dict) -> None:
    print("\n" + "=" * 60)
    print("DASHBOARD SUMMARY")
    print("=" * 60)
    print(f"Total tickets:          {dashboard['total_tickets']}")
    print(f"Missing priority:       {dashboard['missing_priority_count']} ({dashboard['missing_priority_pct']}%)")
    print(f"Open/Escalated backlog: {dashboard['open_backlog']['total']} ({dashboard['open_backlog']['escalated']} escalated)")
    print(f"Avg satisfaction:       {dashboard['satisfaction']['overall_avg']}/5")

    print("\nVolume by category:")
    for cat, n in sorted(dashboard["volume_by_category"].items(), key=lambda x: -x[1]):
        print(f"  {cat:<20} {n}")

    print("\nTop recurring customers:")
    for cust, n in list(dashboard["recurring_customer_hotspots"].items())[:5]:
        print(f"  {cust}  ->  {n} tickets")

    print("\nPriority distribution (AI-suggested):")
    for p in ["Critical", "High", "Medium", "Low"]:
        n = dashboard["priority_distribution"].get(p, 0)
        print(f"  {p:<10} {n}")
    print("=" * 60)


if __name__ == "__main__":
    main()