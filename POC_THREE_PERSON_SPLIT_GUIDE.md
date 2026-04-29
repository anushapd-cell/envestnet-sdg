# Envestnet UMP — Synthetic Test Data Generator

## Three-Person POC Split Guide

**Document type:** Team Coordination Plan
**Audience:** The three developers executing this POC + their manager
**Duration:** 7 working days
**Approach:** Vertical ownership by layer (each person owns a complete module end-to-end), with explicit coordination touchpoints

---

## 1. The Split — by System Layer

Three people on a 7-day POC works only if the split creates real parallelism rather than coordination overhead. The split here is by **layer of the system**: each role owns a complete vertical slice that can be developed independently.

### Role A — Pipeline Owner

Owns everything that touches the reference file and produces the golden reference. Domain: data engineering — PySpark, profiling, cleansing, schema extraction.

**Primary file:** `golden_prep.py`
**Branch:** `feature/phase-1`

| Responsibility |
|---|
| `golden_prep.py` — all of Phase 1 |
| Synthetic reference file construction (Day 1) |
| Bronze ingestion (PSV → Parquet with metadata) |
| Profiler (type inference, ranges, distributions, null rates) |
| Cleanser (deduplication, normalization, null handling) |
| Masker (PII protection: account numbers, names) |
| Gold finalizer — outputs `golden_reference.json` |
| All Phase 1 tests |

### Role B — Generator Owner

Owns everything that consumes the golden reference and produces synthetic data. Domain: rule engines — Faker, mutations, distribution sampling.

**Primary file:** `test_data_gen.py`
**Branch:** `feature/phase-2`

| Responsibility |
|---|
| `test_data_gen.py` — all of Phase 2 (cash file scope) |
| Coverage matrix engine (18 txn_code × variant combinations from real Sal_csh.txt codes) |
| Data factory (CUSIP check digit, dates, amount distributions per txn type) |
| Mutation engine (7 named error scenarios + 2 edge cases) |
| Manifest writer (audit log) |
| All Phase 2 tests |

### Role C — Integration & Validation Owner

Owns everything that wires the system together and prepares it for client delivery. Domain: integration, CLI design, deployment, testing infrastructure.

**Primary files:** `cli.py`, `tests/test_integration.py`, `validate_self_consistency.py`, `DEPLOYMENT_GUIDE.md`
**Branch:** `feature/integration`

| Responsibility |
|---|
| CLI scaffolding and full integration (`cli.py`) |
| PSV renderer implementation (consumes Role B's records, uses Role A's schema) |
| End-to-end integration tests |
| Test harness — pytest infrastructure, coverage reporting |
| `validate_self_consistency.py` — round-trip validation script |
| `validate-environment` CLI command — pre-flight check for client install |
| `DEPLOYMENT_GUIDE.md` — plug-and-play runbook |
| Final README integration |
| Demo flow scripting and rehearsal |

### Shared (work together)

| Responsibility | When |
|---|---|
| 90-min JSON contract sync — all three | Day 1 morning |
| Mid-POC stakeholder checkpoint | Day 5 |
| Mismatch triage from self-consistency validation | Day 6 |
| Demo rehearsal and delivery | Day 7 |

## 2. Why This Split Works

The two-person split forces Phase 1 and Phase 2 to develop in parallel through a JSON contract. That works but it leaves integration, testing, and delivery prep stacked at the end of the timeline — Days 7–10 in the original 10-day plan.

Adding Role C lets that integration work run from Day 1 in parallel with the build. By Day 5, Role C has end-to-end smoke tests, the CLI, and the validation framework already in place — ready to consume the moment Role A and B's milestones land. By Day 7, the deployment guide is written and tested, not rushed at the last minute.

This is the only split that makes 7 days realistic. **A 7-day plan with two people would require cutting scope; a 7-day plan with three people delivers the full scope.**

```
            golden_reference.json
        (the contract, locked Day 1)
                    ▲                  ▲
            produces│                  │consumes
                    │                  │
        ┌───────────┴────┐    ┌────────┴───────┐
        │     ROLE A     │    │     ROLE B     │
        │  Pipeline      │    │  Generator     │
        │  Owner         │    │  Owner         │
        │                │    │                │
        │ golden_prep.py │    │ test_data_gen  │
        │                │    │      .py       │
        └────────────────┘    └────────────────┘
                    │                  │
                    ▼                  ▼
                ┌────────────────────────┐
                │       ROLE C           │
                │   Integration Owner    │
                │                        │
                │  cli.py                │
                │  validate_*.py         │
                │  DEPLOYMENT_GUIDE.md   │
                └────────────────────────┘
```

## 3. Day-by-Day Split

| Day | Role A (Pipeline) | Role B (Generator) | Role C (Integration) | Together |
|---|---|---|---|---|
| **Day 1** | Setup · Multi-line parser proof-of-concept · Read all 4 sample files (act, csh, pos, rad) | Setup · Coverage matrix from real codes (WTFEE, JRL, STAX, RDIV, WRAP, RPRM, YRINC) · Mock `golden_cash.json` | Setup · Repo scaffolding · pytest harness · CLI skeleton with stub commands | 90-min JSON contract sync (all 3) |
| **Day 2** | Profiler for cash + position (single-line) · CUSIP detection · **MILESTONE: `golden_cash.json` EOD** | Faker factory · CUSIP algorithm · Cash record generators per txn type · Tests | pytest infrastructure · Coverage tooling · `validate_self_consistency.py` scaffold | EOD sync |
| **Day 3** | Profiler for account + rad (multi-line) · Cleanser + masker + finalize_gold · **MILESTONE: all 4 golden references delivered EOD** | 72 positive records from mock golden ref · Seed determinism tests · Swap to real `golden_cash.json` EOD | First end-to-end smoke test (Phase 1 → mock Phase 2 → CLI) · PSV renderer spec | Mock-to-real swap walkthrough (A + B + C) |
| **Day 4** | Profiler refinement on edge cases · Help Role B if behind | All 9 mutations + immutability tests · Manifest writer | PSV renderer implementation (variable-length aware) · Wire CLI fully · End-to-end runs working | EOD sync |
| **Day 5** | 90% coverage push · Edge case tests · Error handling | **MILESTONE: full Phase 2 complete EOD** · 90% coverage | End-to-end integration tests · Byte-identical reproducibility test · Self-consistency validation script complete | Mid-POC stakeholder checkpoint |
| **Day 6** | Self-consistency results review · Phase 1 fixes for any mismatches | Self-consistency results review · Phase 2 mutation rule refinement | **DEPLOYMENT_GUIDE.md drives the day** · `validate-environment` CLI · Round-trip validation report | All 3 reviewing self-consistency mismatches together |
| **Day 7** | Phase 1 README section · Demo rehearsal | Phase 2 README section · Demo rehearsal | Full README integration · Demo flow scripting · Final polish · Buffer for surprises | **Demo + handover** |

## 4. The JSON Contract

The single source of truth between Role A and Role B (and reviewed by Role C). Locked on Day 1 morning in a 90-minute sync. Committed to `main` as `configs/golden_reference_schema.md` so all three branches reference it.

The Phase 1 → Phase 2 contract for this POC is `golden_cash.json` (the Cash transaction file's golden reference). Role A also produces `golden_account.json`, `golden_position.json`, and `golden_rad.json` for the other 3 file types — same schema shape, different field sets.

```json
{
  "custodian_id": "stonex",
  "file_type": "CASH_TRANSACTION",
  "source_filename": "Sal_csh.txt",
  "delimiter": "|",
  "record_format": "single_line_variable_length",
  "field_count_range": [45, 58],
  "has_header": false,
  "generated_at": "ISO timestamp",
  "source_record_count": int,
  "anchor_fields": [
    {"position": 0, "name": "RECORD_TYPE", "stable": true, "always_value": "A"},
    {"position": 3, "name": "ACCT_NUM", "stable": true},
    {"name": "TXN_CD", "stable": false, "detection": "first_uppercase_token_after_amount_block"},
    {"position": -1, "name": "TIMESTAMP", "stable": true}
  ],
  "fields": [
    {
      "name": "ACCT_NUM",
      "inferred_type": "account_number",
      "required": true,
      "null_rate": 0.0,
      "min_length": 8,
      "max_length": 8,
      "pattern": "\\d{8}",
      "sample_values": ["48849648", "82389012", "45399034"]
    },
    {
      "name": "TXN_CD",
      "inferred_type": "enum",
      "required": true,
      "allowed_values": ["WTFEE","JRL","STAX","RDIV","WRAP","RPRM","YRINC"],
      "value_distribution": {"JRL": 0.41, "WTFEE": 0.18, "STAX": 0.14}
    },
    {
      "name": "AMOUNT",
      "inferred_type": "decimal",
      "required": true,
      "min": -5000.00,
      "max": 308.68,
      "mean": 50.42,
      "allows_negative": true,
      "negative_allowed_for": ["YRINC", "JRL"]
    },
    {
      "name": "TRADE_DATE",
      "inferred_type": "date",
      "format": "YYYY-MM-DD",
      "required": true
    }
  ]
}
```

**Type vocabulary** (lowercase strings):
`account_number` · `cusip` · `date` · `integer` · `decimal` · `enum` · `string` · `timestamp`

**Field name convention:** UPPERCASE_SNAKE_CASE (e.g. `ACCT_NUM`, `TRADE_DATE`, `TXN_CD`)

**Anchor-based schema** (key innovation for variable-length cash records): instead of assuming fixed positions, the profiler identifies "anchor fields" with stable positions or detectable patterns. Phase 2 uses anchors to position fields correctly when generating variable-length records.

Changes to this contract after Day 1 are **breaking changes**. They require sync between all three roles before being merged.

## 5. Branching Strategy

```
main
  │
  ├── feature/phase-1   (Role A) ─── PR daily ──→ main
  ├── feature/phase-2   (Role B) ─── PR daily ──→ main
  └── feature/integration (Role C) ─ PR daily ──→ main
```

**Daily PR rhythm:**
- Each role pushes to their feature branch throughout the day
- EOD: open a PR to main with the day's work
- Other two roles approve in the morning (5-min review window during standup)
- Merge to main after standup; everyone rebases on main before continuing

**Anti-collision rules:**
- Role A never edits `test_data_gen.py` or `cli.py` or `validate_*.py`
- Role B never edits `golden_prep.py` or `cli.py` or `validate_*.py`
- Role C never edits `golden_prep.py` or `test_data_gen.py`
- Shared files (`requirements.txt`, `.gitignore`, `README.md`) — coordinate before editing

If you need a change in someone else's primary file, open an issue with a clear ask. Don't edit it yourself.

## 6. The Four Sample Files — Role A's Day 1 Foundation

The keystone deliverable that makes the mock-data approach work is Role A's multi-line/single-line PSV reader, validated against all 4 client-provided sample files on Day 1.

**Files:** `ref_files/sal_act.txt`, `ref_files/Sal_csh.txt`, `ref_files/Sal_pos.txt`, `ref_files/sal_rad.txt`
**Source:** Provided by client as the reference data for the POC

| File | Format | Records | Lines per record | Field count |
|---|---|---|---|---|
| `sal_act.txt` | Multi-line PSV (dashed-line separator) | 14 | 4 | ~197 (concatenated) |
| `Sal_csh.txt` | Single-line PSV (variable length) | 22 | 1 | 45–58 (varies per record) |
| `Sal_pos.txt` | Single-line PSV (fixed) | 17 | 1 | 39 (constant) |
| `sal_rad.txt` | Multi-line PSV (blank-line separator) | 17 | 2 | ~40 (concatenated) |

**Day 1 proof-of-concept (Role A):** A working reader that ingests all 4 files into PySpark DataFrames. Concretely:
- Detect record boundaries (dashed line, blank line, or newline)
- Concatenate physical lines into logical records for multi-line files
- Split on `|` delimiter
- Pad/anchor variable-length records using stable position markers

**Why this matters:** Each file has its own quirks. The act file has 4-line records with ~197 fields. The cash file has variable field counts. The rad file has real CUSIPs that need check-digit validation. Day 1's investment in a robust reader pays back through Days 2–3 when the profiler runs against all 4 files.

**Sample CUSIPs from `sal_rad.txt`** (real, valid — use these as test fixtures):
- `316146109` → FBNDX (Fidelity Investment Grade Bond)
- `31617K303` → FSTGX (Fidelity Short-Term Government Income)
- `31617K881` → FTBFX (Fidelity Total Bond)
- `354723702` → FRHIX (Franklin High Yield Tax-Free)
- `277923660` → EAFAX (Eaton Vance Floating Rate Advantage)

## 7. Communication Cadence

| Cadence | Duration | Format | Who |
|---|---|---|---|
| Morning standup | 10 min | What I shipped · What I'm doing today · Blockers | All 3 |
| EOD sync | 10 min | Demo what's working · Tomorrow's plan | All 3 |
| JSON contract sync | 90 min | Locked agreement on golden_reference.json structure | All 3 (Day 1 only) |
| Mock-to-real swap | 30 min | Walk through real golden_reference.json before Role B consumes it | All 3 (Day 3 EOD only) |
| Mid-POC checkpoint | 60 min | Demo to manager + senior architect | All 3 + stakeholders (Day 5) |
| Mismatch triage | 60 min | Walk through self-consistency results, assign fixes | All 3 (Day 6) |
| Demo rehearsal | 60 min | Run the demo flow twice, time it | All 3 (Day 7) |
| Demo delivery | 30 min | The actual demo | All 3 + stakeholders (Day 7) |

Total scheduled meeting time across the week per person: ~7 hours. Already factored into per-person effort estimates.

## 8. Effort Per Person

| Role | Total hours | Average/day | Heaviest day |
|---|---|---|---|
| Role A | ~46 hrs | 6.5 hrs | Day 3 (8 hrs — milestone) |
| Role B | ~50 hrs | 7.1 hrs | Day 4 (8 hrs — mutations + manifest) |
| Role C | ~45 hrs | 6.4 hrs | Day 6 (8 hrs — deployment guide) |

Total ~141 hours across the 7-day window, comfortably within the 147-hour combined capacity.

## 9. What Each Role Looks Like Day-to-Day

### Role A's week
Heavy front-load. Days 1–3 are intense (8 hrs each), with Day 3 being the milestone day where `golden_reference.json` lands. Days 4–7 are progressively lighter — Day 4 is refinement and being available to help Role B, Day 5 is testing, Days 6–7 are documentation and demo prep. Recommended for the developer with strongest data engineering / PySpark background.

### Role B's week
More evenly distributed. No truly easy day, but no single 9-hour day either. The hardest days are Day 3 (CUSIP algorithm + asset-class generators) and Day 4 (all 9 mutations + manifest). Day 5 is the milestone with full Phase 2 complete EOD. Recommended for the developer most comfortable with Python rule engines and test design.

### Role C's week
Distributed differently from A and B. Day 1 is light (just scaffolding). Days 2–4 are steady mid-intensity (CLI build, test infrastructure, PSV renderer, integration tests). Day 5 is the integration test milestone. Day 6 is the heaviest (deployment guide + environment validation CLI). Day 7 is mostly demo polish. Recommended for the developer with strongest DevOps, testing, and documentation instincts.

## 10. Anti-Patterns to Avoid

| Anti-pattern | Why it fails | Better |
|---|---|---|
| Role C waits until Day 5 to start | Integration cliff-edges. Bugs surface too late. | Role C scaffolds CLI and test infrastructure from Day 1 |
| Role A delays delivering golden_reference.json past EOD Day 3 | Role B's swap-to-real is blocked. Day 4 mutations stack. | Role A treats Day 3 EOD as a hard deadline. Push refinement to Day 4. |
| Three people in every meeting | Coordination overhead kills throughput | Standups and EOD syncs are sacred. Most other syncs are 2-of-3. |
| Skipping the JSON contract sync | Contract drift mid-week. Painful re-work. | Day 1 morning, 90 minutes, all three, no exceptions. |
| Role C builds DEPLOYMENT_GUIDE.md in their head and writes it Day 7 | Last-minute documentation is always thin | Outline by Day 5, draft by Day 6, polish on Day 7 |

## 11. Catch-Up Plan if Behind

If Role A's milestone slips past EOD Day 3:
- Day 4 morning: 30-min sync, all three. Decide whether to ship a minimal golden_reference.json (drop optional metadata) and refine in parallel with Role B's mutation work.
- Role C: blocked on integration tests — pivot to deployment guide work.

If Role B's milestone slips past EOD Day 5:
- Day 6 morning: drop 2–3 mutations from the demo to make the deadline. Document the dropped ones as "future work" in the README.
- Role C: still does self-consistency validation on whatever subset Role B has working.

If Role C falls behind on deployment guide:
- Day 7 morning: 30-min sync. Roles A and B contribute their respective sections of the guide directly.

## 12. Reading Order Within Each Role

After this document, each role reads:
1. `ENVESTNET_SDG_POC_Master_PLAN` — overall plan and architecture
2. Their role-specific playbook — `ROLE_A_PIPELINE_OWNER` / `ROLE_B_GENERATOR_OWNER` / `ROLE_C_INTEGRATION_OWNER`
3. The other two roles' playbooks — for awareness of what's expected at each handoff point

The role playbooks contain:
- Day-by-day step-by-step instructions
- Copy-paste-ready AI agent prompts (designed for Cursor / Copilot / Claude Code)
- Test scaffolding and code snippets
- Common pitfalls per role

— *Nous Infosystems · QA & Test Automation Practice*
