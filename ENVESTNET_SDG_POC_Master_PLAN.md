# Envestnet UMP — Synthetic Test Data Generator POC

## Master Plan

**Document type:** Master Plan
**Audience:** Engineering team + manager + stakeholders
**Duration:** 7 working days
**Team:** 3 developers
**Custodian:** Stonex Financial Inc
**Files in scope:** 4 — Account Master, Cash Transactions, Positions, Reinvested Activity
**Development environment:** Nous infrastructure (sample-data-derived mocks)
**Delivery model:** Plug-and-play package, trained on real data inside client environment post-delivery
**Stack:** Python 3.12 + PySpark + Pandas + Faker (seeded) + pydantic + click + pytest

---

## 1. Problem

The Envestnet UMP intake pipeline ingests custodian files (Account Master, Cash Transactions, Positions, Reinvested Activity) and applies hundreds of validation rules. Every change to UMP requires regression testing across this rule surface, and each new custodian onboarding multiplies the test matrix. Today, test data is hand-crafted — slow to produce, narrow in coverage, expensive to maintain.

Production custodian files cannot be used directly. They contain PII, they don't cover negative cases (rejection scenarios are rare in production), and they don't exercise edge cases on demand. The team needs a generator that produces synthetic custodian files matching real format and statistical distributions, with controlled coverage and intentional errors.

## 2. Solution

A two-phase tool, built once, parameterised per file type per custodian.

**Phase 1 — Golden Data Preparation.** Profile each reference file. Auto-detect schema, types, ranges, distributions, and rules. Output: one `golden_reference_*.json` per file type — a portable schema blueprint.

**Phase 2 — Test Data Generation.** Consume a golden reference. Generate synthetic records covering every transaction × security combination. Inject controlled mutations to produce negative, invalid, missing, and edge-case rows. Output: a synthetic file in the original PSV format + a `manifest.json` predicting the expected UMP outcome for every row.

For this POC, **Phase 1 runs against all 4 file types**. **Phase 2 generates only for the Cash transaction file** — proving end-to-end coverage on the most complex file. The other 3 file types are profiled-only this POC; their Phase 2 generation extends post-delivery using the same framework.

## 3. POC Scope

| Dimension | Scope |
|---|---|
| Custodian | 1 — Stonex Financial Inc |
| File types in Phase 1 (profile) | 4 — Account, Cash, Positions, RAD |
| File types in Phase 2 (full generation + mutations) | 1 — Cash transactions |
| Self-consistency validation | Cash file |
| Format | Pipe-delimited (PSV) — single-line and multi-line variants |
| Mutations | 9 — 7 reject + 2 edge case |
| Coverage matrix (cash) | 18 (txn_code × variant) combinations |
| Output rows per run (cash) | ~80 (72 positive + 9 mutated) |
| Duration | 7 working days |
| Team | 3 developers |

## 4. The Four Files

The client provided 4 sample files. Each represents a different feed Stonex sends to Envestnet daily.

| File | Purpose | Format | Records (sample) | Notable |
|---|---|---|---|---|
| `sal_act.txt` | Account/customer master | **Multi-line PSV** — records separated by dashed lines, 4 lines each | 14 | ~197 fields per logical record. STONEX FINANCIAL INC C/F appears throughout. |
| `Sal_csh.txt` | Cash transactions | Single-line PSV, **variable-length** records (45–58 fields) | 22 | 7 distinct txn codes: WTFEE, JRL, STAX, RDIV, WRAP, RPRM, YRINC. Negative amounts are valid. |
| `Sal_pos.txt` | Positions | Single-line PSV, **fixed** schema (39 fields) | 17 | Type indicator R/C (Receive/Cancel). Quantity × price = market value. |
| `sal_rad.txt` | Reinvested activity / dividends | **Multi-line PSV** — records separated by blank lines, 2 lines each | 17 | Real CUSIPs (316146109, 31617K303, 31617K881...). Real fund tickers (FBNDX, FSTGX, FTBFX). |

Two files have multi-line records — Phase 1's reader handles both single-line and multi-line PSV. The cash file has variable-length records — Phase 1's profiler anchors on key positions (record_type, account#, dates, txn_code, timestamp) rather than assuming a fixed column count.

## 5. Development Approach: Sample-Driven Mock, Plug-and-Play Delivery

The POC is built on Nous infrastructure using the **4 client-provided sample files** as reference data. The actual Stonex production files never leave the client environment.

**Why this approach:**
- Sample files are real-format, controlled-volume — no NDA gating
- Mock generation is grounded in real data shapes, not invented from scratch
- Three-person parallelism is fully achievable
- Iteration is fast and unblocked

**The trade-offs:**
- The samples are small. Edge cases visible only at production volume won't surface in the POC.
- UMP match-rate validation cannot happen during the POC — it happens after delivery, in the client environment
- "Plug and play" must be earned with strong installation tooling and documentation

**Day 1 deliverable from Role A:** Multi-line parser proof-of-concept that successfully reads all 4 sample files into PySpark DataFrames.

**Day 2 EOD sub-milestone from Role A:** `golden_cash.json` delivered — unblocks Role B's swap from mock to real reference.

**Day 3 EOD milestone from Role A:** All 4 golden references delivered.

**Day 7 deliverable from Role C:** `DEPLOYMENT_GUIDE.md` — runbook for installing the tool inside Envestnet's environment, pointing it at production Stonex files, and running Phase 1 to produce production golden references.

## 6. Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      PHASE 1 (Role A)                            │
│                                                                  │
│  4 Reference Files  →  Smart Reader                              │
│  ┌──────────────┐         (single-line  +  multi-line PSV)       │
│  │ sal_act.txt  │ ─┐              ↓                              │
│  │ Sal_csh.txt  │ ─┼→  Bronze (PySpark Parquet)                  │
│  │ Sal_pos.txt  │ ─┤              ↓                              │
│  │ sal_rad.txt  │ ─┘     Silver (Profile + Cleanse + Mask)       │
│  └──────────────┘                 ↓                              │
│                            Gold (4 outputs):                     │
│                            • golden_account.json                 │
│                            • golden_cash.json   ← Phase 2 input  │
│                            • golden_position.json                │
│                            • golden_rad.json                     │
└───────────────────────────────────┼──────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────┐
│                      PHASE 2 (Role B)                            │
│                                                                  │
│  golden_cash.json  +  Coverage Matrix (18 combos)                │
│                              ↓                                   │
│                    Faker (seeded) + DataFactory                  │
│                              ↓                                   │
│                    72 positive records                           │
│                              ↓                                   │
│                    Mutation Engine (9 mutations)                 │
│                              ↓                                   │
│                    PSV Renderer (variable-length aware)          │
│                              ↓                                   │
│                    synthetic_cash.txt + manifest.json            │
└──────────────────────────────────────────────────────────────────┘

       ┌──────────────────────────────────────────────────────┐
       │                INTEGRATION (Role C)                  │
       │                                                      │
       │  CLI (cli.py) — wires Phase 1 + Phase 2 together     │
       │  PSV Renderer — variable-length aware                │
       │  validate_self_consistency.py — cash round-trip      │
       │  Test harness — pytest infra, coverage reporting     │
       │  DEPLOYMENT_GUIDE.md — plug-and-play runbook         │
       │  validate-environment CLI — pre-flight for client    │
       └──────────────────────────────────────────────────────┘
```

## 7. Three-Role Split

Vertical ownership by **layer of the system**, not by phase. Adding a third person makes parallelism real — Role C absorbs the integration, testing, and validation work that would otherwise serialize behind A and B.

**Role A — Pipeline Owner** · `golden_prep.py`
Owns Phase 1 entirely for all 4 file types. Multi-line/single-line reader, profiler, cleanser, masker, finalize_gold. Day 2 EOD: `golden_cash.json`. Day 3 EOD: all 4 golden references.

**Role B — Generator Owner** · `test_data_gen.py`
Owns Phase 2 entirely, focused on cash transactions. Coverage matrix, Faker factory, CUSIP algorithm (for STAX/RDIV records that reference securities), asset-class generators, mutation engine, manifest writer. Day 5 EOD: complete generator.

**Role C — Integration & Validation Owner** · `cli.py`, `validate_self_consistency.py`, `tests/test_integration.py`, `DEPLOYMENT_GUIDE.md`
Owns everything that wires the system together and prepares it for client delivery. CLI scaffolding, end-to-end tests, PSV renderer, self-consistency validation, deployment runbook, environment-validation CLI.

The contract between roles is `golden_cash.json` — locked in a 90-minute sync on Day 1 morning. All three attend.

## 8. Seven-Day Timeline

| Day | Role A (Pipeline) | Role B (Generator) | Role C (Integration) | Together |
|---|---|---|---|---|
| **Day 1** | Setup · Multi-line parser proof-of-concept · Read all 4 files | Setup · Coverage matrix from real codes · Mock golden_cash.json | Setup · Repo scaffolding · CI/test harness · CLI skeleton | 90-min JSON contract sync |
| **Day 2** | Profiler for cash + position (single-line) · CUSIP detection · **MILESTONE: golden_cash.json EOD** | Faker factory · CUSIP algorithm · Cash record generators · Tests | pytest infrastructure · Coverage tooling · `validate_self_consistency.py` scaffold | EOD sync |
| **Day 3** | Profiler for account + rad (multi-line) · **MILESTONE: all 4 golden references EOD** · Cleanser + masker | 72 positive records · Seed determinism tests · Swap to real golden_cash EOD | First end-to-end smoke test · PSV renderer spec | Mock-to-real walkthrough |
| **Day 4** | Profiler refinement · Help Role B if behind | All 9 mutations + immutability tests · Manifest writer | PSV renderer implementation (variable-length aware) · Wire CLI fully | EOD sync |
| **Day 5** | 90% coverage · Edge case tests · Error handling | **MILESTONE: full Phase 2 complete EOD** · 90% coverage | E2E integration tests · Byte-identical reproducibility test · Self-consistency validation | Mid-POC stakeholder checkpoint |
| **Day 6** | Self-consistency results review · Phase 1 fixes | Self-consistency results review · Phase 2 fixes | **DEPLOYMENT_GUIDE.md drives the day** · `validate-environment` CLI · Round-trip validation report | Mismatch triage |
| **Day 7** | Phase 1 README · Demo rehearsal | Phase 2 README · Demo rehearsal | Full README · Demo flow scripting · Final polish | **Demo + handover** |

## 9. Coverage Matrix — Cash File (18 combinations)

Coverage is built around the 7 real txn codes observed in `Sal_csh.txt`, varied along the dimensions that make each one interesting to UMP validation.

| Txn Code | Description | Variants | Combos |
|---|---|---|---|
| **WTFEE** | Wire transfer fee | small (<$50), large (>$1000) | 2 |
| **JRL** | Journal / fund transfer | TO TYPE 1, FROM TYPE 2, TO ROTH, FROM IRA | 4 |
| **STAX** | Foreign tax withholding | Common stock (C), Fund (F) | 2 |
| **RDIV** | Reinvest dividend | small, medium, large amounts | 3 |
| **WRAP** | Mgmt fee / wrap fee | Quarterly | 1 |
| **RPRM** | Premium / distribution | To Roth, To Reg | 2 |
| **YRINC** | Year income (div+interest) | C positive, C negative, F positive, F negative | 4 |
| **Total** | | | **18** |

C=common stock · F=fund · 4 records per combo = **72 positive records** per generation.

## 10. Mutations (9 total)

| # | Mutation | Case Type | Expected | Reason |
|---|---|---|---|---|
| 1 | strip_required_field | missing_field | reject | Required field missing |
| 2 | inject_invalid_date | invalid_format | reject | Invalid date in field |
| 3 | inject_text_in_numeric | invalid_format | reject | Non-numeric value in amount |
| 4 | inject_invalid_cusip | negative | reject | CUSIP check digit failed (STAX/RDIV records that reference securities) |
| 5 | inject_invalid_txn_code | negative | reject | Unrecognised txn code |
| 6 | inject_future_settle_date | negative | reject | Settle date too far in future |
| 7 | **inject_implausible_negative** | negative | reject | Negative amount on a txn type that should never be negative (e.g., WTFEE -$35) |
| 8 | zero_amount | edge_case | warn | $0.00 transaction |
| 9 | very_large_amount | edge_case | warn | Amount > $1M (typical bound exceeded) |

**Note on mutation #7:** Reworked from the original `inject_negative_amount`. The cash file legitimately has negative amounts (e.g., YRINC -$5000.00 dividend reversals). The mutation now targets txn types that don't accept negatives — flipping the sign on a WTFEE or WRAP record where it's nonsensical.

## 11. Key Constraints

**No AI/LLM at runtime.** The product is standalone. Faker is used purely as a seeded PRNG. Zero third-party API costs. Fully offline after install. AI is used only during development (Cursor / Copilot / Claude Code) for code-assist, never as a library.

**Deterministic by seed.** Same seed = byte-identical output. Verified with md5 hash test on Day 5.

**Plug-and-play delivery.** The tool ships to Envestnet as a complete package. Client points it at the 4 production Stonex files via a single config edit. No code changes required for first deployment.

## 12. Demo Story (Day 7)

Five-minute walkthrough:

1. **Show the 4 sample files** (30s) — "this is what Stonex Financial sends to Envestnet daily"
2. **Run Phase 1 on all 4** (1 min) — `cli.py prep run --all`, show 4 golden_*.json files emerge
3. **Run Phase 2 on cash** (1 min) — `cli.py generate --file cash --seed 42`, show synthetic_cash.txt + manifest.json
4. **Show same seed = byte-identical output** (30s) — run twice, diff
5. **Show self-consistency validation** (30s) — re-feed synthetic_cash.txt through Phase 1, confirm round-trip
6. **Show plug-and-play deployment** (1 min) — walk through DEPLOYMENT_GUIDE.md, show one config edit to point at production files
7. **Q&A** (1 min)

**The pitch:** *Phase 1 handles all 4 Stonex file types — custodian-format-agnostic, including multi-line and variable-length records. Phase 2 demonstrates the full generation engine on the most complex file (Cash). When deployed in Envestnet's environment, Phase 2 extends to the other 3 file types using the same framework, with no architectural changes.*

## 13. Open Items

These are tracked for post-delivery, not blocking POC development:

| Item | Owner | Needed by |
|---|---|---|
| Confirm custodian display name (filename prefix `Sal_` vs `STONEX FINANCIAL INC C/F` in body) | Vijay Arun | Day 1 |
| Production-volume real Stonex files | Vijay Arun (NDA) | Post-delivery, for client-side training |
| Complete TXN_CD value list for cash file | Thillai | Day 1 (informs synthetic generation) |
| UMP rejection reason codes | Thillai | Day 4 (informs manifest expected_reason text) |
| Stonex schema documentation per file type | Thillai | Day 1 (Role A needs this for profiler tuning) |
| Should Phase 2 cover the other 3 file types post-POC? | Balaji | Post-POC scoping |
| Target volume for production | Balaji | Post-delivery |

## 14. Success Criteria

By end of Day 7, the team demos:

- 4 sample reference files used as input
- Phase 1 producing 4 golden references (one per file type), including multi-line files
- Phase 2 producing 80+ records on the cash file with full coverage + mutations
- `manifest.json` correctly mapping every row to expected outcome
- Same seed = byte-identical output (proven with hash test)
- Self-consistency round-trip validation working on cash
- `DEPLOYMENT_GUIDE.md` complete with `validate-environment` CLI
- README and handover documentation complete

The framework should be ready to install in Envestnet's environment, point at the real Stonex production files, and run without code modification.

## 15. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Multi-line parser bugs (act + rad files) | Medium | High | Day 1 proof-of-concept validates approach before deeper work begins. |
| Variable-length record schema (cash file) | Medium | High | Profiler anchors on stable positions (record_type, account#, dates, txn_code, timestamp); schema-flexible for middle fields. |
| Day 3 milestone (all 4 golden refs) slips | Medium | High | Day 2 sub-milestone (golden_cash.json) gives Role B unblock signal. The other 3 can slip to Day 4 morning if needed. |
| CUSIP algorithm bugs | Medium | Medium | Test against real CUSIPs in sample (316146109 = FBNDX, 31617K303 = FSTGX, 31617K881 = FTBFX). Role C reviews. |
| Coordination overhead with 3 people | Medium | Medium | Daily 10-min standup + EOD sync. Pre-defined ownership boundaries. PR review discipline. |
| Plug-and-play delivery fails on first install | Low | High | `validate-environment` CLI, fresh-machine install test by Role C on Day 7. |
| Real Stonex production files surprise Phase 1 | Medium | Medium | Document this as a known unknown in DEPLOYMENT_GUIDE. First-day-on-site checklist. |

## 16. Reading Order

1. **This document** — orientation
2. **POC_THREE_PERSON_SPLIT_GUIDE** — coordination model, JSON contract, anti-collision rules
3. **Your role-specific playbook** — ROLE_A / ROLE_B / ROLE_C — daily steps with AI prompts
4. **Envestnet_SDG_POC_Deck** — 4-slide stakeholder version (use for executive conversations)

— *Nous Infosystems · QA & Test Automation Practice*
