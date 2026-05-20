# How I Used AI — Reflection

---

## Tools used

**Claude (claude.ai / Claude Code)** was my primary tool throughout the project. I used it as an implementation assistant, debugging tool, and thinking partner rather than as an autopilot.

I first used Claude during the investigation phase to help profile the CSV and surface patterns in the data before writing code. I wanted to understand the operational problems in the dataset first — recurring complaints, missing priorities, corrupted rows, escalation chains, and unreliable satisfaction data — before deciding where AI would actually help and where normal Python logic would be more appropriate.

Before implementation, I spent time reasoning through the structure of the pipeline manually — especially around:
- cleaning corrupted rows before triage
- separating deterministic logic from AI reasoning
- ensuring the system was modular and maintainable
- deciding which parts of the workflow genuinely benefited from an LLM versus normal programmatic logic

I used Claude more as a sounding board during this phase rather than simply asking it to generate the full system immediately.

I used Claude for:
- Initial data investigation and profiling
- Drafting and iterating on the triage system prompt
- Debugging the `satisfaction_score` column corruption
- Generating the HTML dashboard boilerplate/CSS
- Refactoring repetitive code during cleanup
- Adding comments and improving readability once the structure was stable

All implementation, debugging, testing, and restructuring work was done locally in my own Python environment.

---

## One moment I had to override AI output

When I asked Claude how to detect recurring complaints, its first proposal was to embed every ticket description using semantic similarity between tickets.

I rejected this approach for several reasons:

1. The dataset already contains *explicit* ticket references ("see TKT-005", "follow-up to TKT-011"), which can be extracted directly with regex
2. Embeddings would add unnecessary complexity, latency, and API cost
3. For a support manager, explicit recurrence chains are easier to understand and act on than similarity percentages
4. Rule-based recurrence detection is more auditable and deterministic for this type of operational workflow

I instead implemented the two-signal rule-based recurrence approach:
- Explicit ticket-reference extraction
- Same-customer + same-category grouping

The AI was reaching for the technically impressive solution rather than the operationally correct one.

Another moment I had to override AI output was during the Anthropic API integration itself. The initial generated implementation used outdated API patterns and incorrect model usage, so the script failed at runtime. Rather than continuing to regenerate code blindly, I stopped and checked the current Anthropic documentation manually, corrected the client setup and request structure, then tested the integration step-by-step until batch triage worked reliably.

That ended up being an important reminder that generated code still requires engineering validation, documentation checks, and runtime testing.

---

## One moment AI saved time or improved the result

The system prompt for the triage API call went through several iterations before it produced stable JSON output. Early versions sometimes returned extra explanatory text outside the JSON array or inconsistent formatting between batches.

I described the exact failure mode to Claude ("it sometimes adds text before the JSON array"), and it suggested explicitly instructing the model to:

> "Return ONLY a valid JSON array. No preamble, no markdown fences."

It also suggested adding a small cleanup step before JSON parsing to remove occasional markdown formatting around the response.

That combination significantly stabilized the outputs across all five triage batches. Writing and debugging that prompt entirely through trial and error would have taken much longer manually.

AI also accelerated repetitive implementation work that would have been low-value but time-consuming to write by hand, particularly:
- Generating HTML dashboard boilerplate
- Refactoring repetitive parsing logic
- Adding repetitive comments/docstrings
- Cleaning repetitive formatting code

The most effective workflow throughout the project was not "generate everything automatically", but iterating quickly while validating each stage manually:
- inspect data
- clean data
- verify recurrence logic
- validate API responses
- confirm dashboard calculations
- refine outputs

---

## How I directed the implementation

The first generated version of the project came back as one very long script with minimal structure. It technically attempted to solve the problem, but it was difficult to debug, difficult to reason about, and not something I would realistically want to maintain or explain in a review conversation.

I decided to refactor the project into separate responsibilities:
- `loader.py` for cleaning and normalization
- `recurrence.py` for recurrence detection
- `ai_triage.py` for Claude integration
- `dashboard.py` for aggregation/statistics
- `renderer.py` for HTML rendering
- `triage.py` as the orchestration layer

That restructuring came from my own reasoning during debugging. The original single-file version made it difficult to isolate problems or reason about the flow cleanly, especially once the cleaning, recurrence, AI triage, and dashboard logic started interacting. Splitting responsibilities made the system easier to validate step-by-step and made the codebase significantly easier to maintain.

Once I had decided the structure, I used Claude to help move functionality into the appropriate files and improve readability with comments and clearer function boundaries.

I also noticed some parts of the generated implementation lacked proper error handling and could fail abruptly during runtime. I added explicit handling for:
- missing input files
- missing API keys
- HTTP/API failures
- network connectivity issues
- timeouts
- invalid JSON responses
- empty triage results

This allowed the tool to fail gracefully with understandable error messages instead of crashing unexpectedly.

Another recurring pattern throughout the build was steering the AI away from unnecessarily complex solutions and using it more as an accelerator than as the decision-maker. I kept deterministic problems deterministic (counting, recurrence extraction, aggregation) and used AI primarily for language-understanding tasks such as priority inference, categorization, and explanation generation.

I also tried to keep the implementation efficient and appropriately scalable for the problem size:
- batching API requests instead of making one request per ticket
- using rule-based recurrence detection instead of embedding similarity
- separating data cleaning from AI inference
- keeping the dashboard generation self-contained with no frontend framework or server dependency

The goal was not to overengineer the solution, but to build something maintainable, auditable, and operationally practical for the support-manager workflow described in the brief.

The final result is therefore not fully AI-generated code, but an AI-assisted implementation shaped through manual debugging, architectural decisions, documentation checks, iterative refinement, and engineering judgement.