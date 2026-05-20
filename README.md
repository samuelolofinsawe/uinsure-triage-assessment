# Support Triage Assistant

A CLI tool that ingests a CSV of support tickets and produces:
- **Per-ticket triage** — AI-suggested priority, category, recurrence flag, and plain-English explanation
- **HTML dashboard** — ticket volume, backlog, satisfaction patterns, recurring-customer hotspots

---

## Project structure

```
triage_tool/
├── triage.py              # Entry point — run this
├── loader.py              # Data loading and cleaning
├── recurrence.py          # Recurrence detection (rule-based)
├── ai_triage.py           # Claude API integration
├── dashboard.py           # Dashboard statistics
├── renderer.py            # HTML dashboard renderer
├── requirements.txt       # Python dependencies
├── support_tickets.csv    # Input data
├── investigation_note.md  # Pre-build data analysis
└── ai_reflection.md       # How AI tools were used
```

---

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=your_key_here
```

Get a free API key at: https://console.anthropic.com/settings/keys

---

## Usage

```bash
python triage.py support_tickets.csv
```

Optional flags:
```
--output-csv   triage_output.csv   # Per-ticket results (default: triage_output.csv)
--output-html  dashboard.html      # Dashboard (default: dashboard.html)
```

---

## Output shape — and why

**Per-ticket → CSV**: The primary consumer is a support manager who will open this in a spreadsheet, filter by priority, and action tickets. CSV maps 1:1 to input rows, making it easy to audit.

**Dashboard → HTML**: Self-contained, opens in any browser, no server or build step needed. Richer than a console summary, simpler to share than a web app.

---

## Sample run on `support_tickets.csv`

```
 Loading tickets from: support_tickets.csv
   49 tickets loaded (15 missing priority labels)

 Detecting recurrence patterns...
   32 tickets flagged as recurrences

 Running AI triage (Claude)...
  Triaging tickets 1-10...
  Triaging tickets 11-20...
  Triaging tickets 21-30...
  Triaging tickets 31-40...
  Triaging tickets 41-49...

 Computing dashboard stats...

 Per-ticket CSV  -> triage_output.csv
 Dashboard HTML  -> dashboard.html

============================================================
DASHBOARD SUMMARY
============================================================
Total tickets:          49
Missing priority:       15 (30.6%)
Open/Escalated backlog: 18 (5 escalated)
Avg satisfaction:       3.94/5

Volume by category:
  Model Output         20
  Integration          10
  Performance           6
  Billing               5
  Safety                3
  Onboarding            3
  Account               1

Top recurring customers:
  CUST-4421  ->  5 tickets
  CUST-5502  ->  5 tickets
  CUST-1155  ->  4 tickets
  CUST-3310  ->  4 tickets
  CUST-2891  ->  4 tickets

Priority distribution (AI-suggested):
  Critical   4
  High       18
  Medium     19
  Low        8
============================================================
```

---

## Edge cases handled

- **Customer with no prior history** — recurrence map returns empty list, `recurrence_flag` is False
- **Missing priority (30% of tickets)** — AI always produces a suggested priority regardless
- **Corrupt satisfaction_score column** — 5 rows had description text in the wrong column; repaired in `loader.py`
- **Inconsistent subcategory capitalisation** — normalised at load time

---

## What I'd do next with more time

- Add `--since` flag for incremental runs on new tickets only
- Persist triage history to SQLite so recurrence detection works across multiple CSV files
- Add a confidence score to each suggested priority
- Replace the satisfaction_score column repair with upstream validation at ticket ingestion
