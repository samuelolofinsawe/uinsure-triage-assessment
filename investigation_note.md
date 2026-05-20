# Investigation Note — support_tickets.csv

*The working note I'd send before opening the editor.*

---

## What I found in the data

**Shape and coverage.** 50 rows declared; 49 loaded cleanly. One row was silently dropped by the CSV parser because it had 13 fields instead of 12 — a comma inside a free-text field broke the row boundary. That row (TKT-005 area, line 6) needs to be investigated at source.

A more serious issue: **five rows have their `ticket_description` text sitting in the `satisfaction_score` column** (TKT-007, TKT-017, TKT-034, TKT-037, TKT-048). These are the most urgent tickets in the whole dataset — recurring issues, legal involvement, cancellation threats — and they have *no satisfaction score recorded*, which means they'd be invisible in any satisfaction-based reporting. The cause is a missing field somewhere earlier in those rows. I repair this in the loader, but it's a red flag about ingestion quality.

**Missing values.** Priority is blank on **15 of 49 tickets (30.6%)** — which matches the brief's "roughly 30%" figure exactly, confirming the dataset is representative. `agent_assigned` is missing on 13 rows; `resolution_time_hours` on 18. Missing agent data correlates with Open/unresolved tickets, which makes sense. Missing resolution time is expected for unresolved tickets.

**Recurrence is the most important signal in this dataset.** There are two types:
- *Explicit*: 10 tickets directly reference prior ticket IDs in the description text (e.g. "see TKT-005", "follow-up to TKT-007"). These are unambiguous.
- *Implicit*: same customer + same category across multiple tickets. Twelve customers have 3 or more tickets; the two most active (CUST-4421, CUST-5502) have 5 each.

The five explicitly-referenced chains are the most alarming:
- **CUST-1155** has filed the *same* performance/inconsistency complaint five times (TKT-005 → 011 → 019 → 034 → 048). The fifth is a formal complaint with SLA compensation requested. This customer is effectively lost without urgent action.
- **CUST-3310** filed a hallucination complaint twice, then a cancellation ticket. The chain TKT-009 → 024 → 039 (cancellation) is a textbook churn signal.
- **CUST-2234** has a bias issue (TKT-007 → 021 → 037) that has now produced end-user complaints and legal involvement.

**Data I can't rely on.** `satisfaction_score` is unreliable — it's missing for 13 rows and corrupt for 5. I use it for directional signal in the dashboard but wouldn't build hard alerting on it. `subcategory` has inconsistent capitalisation ("setup" vs "Setup") and synonym drift ("Webhook" / "Webhooks", "Overage" / "Overage Charges") — I normalise both at load time.

**What I decided to ignore.** `agent_assigned` — useful for workload analysis but not for the support manager's triage use case in the brief. `resolution_notes` — has no references to prior tickets and adds noise to per-ticket output. I include it in the CSV output but don't surface it in the dashboard.

---

## What this means for the build

1. **Recurrence detection should be rule-based, not AI.** The explicit TKT-references in descriptions are deterministic; scanning them with a regex is faster, cheaper, and more auditable than asking an LLM. AI is better deployed on the language-understanding problem (priority and explanation), not the pattern-matching one.

2. **The loader must repair data before triage.** If the five corrupt rows hit the LLM with their description in the wrong field, the triage will be wrong. Fix first, triage second.

3. **The dashboard's most valuable view is the recurring-customer hotspot list.** The brief mentions "obvious patterns get missed — e.g. a customer raising the same complaint for the fourth time." That is literally CUST-1155. The dashboard leads with this.

4. **Priority inference needs to weight recurrence heavily.** A second report of an issue probably warrants High; a fourth with a cancellation threat warrants Critical regardless of category. The LLM prompt encodes this explicitly.
