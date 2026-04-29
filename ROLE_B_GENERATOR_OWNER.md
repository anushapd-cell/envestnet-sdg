# ROLE B — Generator Owner

## Your Mission

You own **Phase 2: Test Data Generation**. You consume the `golden_cash.json` that Role A produces and generate synthetic test data — positive records covering every transaction × variant combination, plus deliberate mutations for negative, invalid, missing, and edge cases. Each row gets tagged in a `manifest.json` audit log with its expected outcome.

**Your file:** `test_data_gen.py`
**Your branch:** `feature/phase-2`
**Your duration:** 7 days · ~50 hours total · evenly distributed
**Your North Star:** A working generator that produces synthetic Transaction files indistinguishable in format from real ones, with controlled coverage and intentional errors — fully deterministic from a seed.

---

## Pre-Flight Checklist

- [ ] Local machine, Python 3.12 installable
- [ ] Git repo cloned, push access confirmed
- [ ] You've read `ENVESTNET_SDG_POC_Master_PLAN.md`
- [ ] You've read `POC_THREE_PERSON_SPLIT_GUIDE.md`
- [ ] You've read this entire file before opening any code
- [ ] You understand: you start with a **mock** golden reference Day 1 — don't wait for Role A's real one until Day 3 EOD

---

## Day 1 — Setup + Coverage Matrix + Mock Golden Reference

**Goal:** Working dev env + coverage matrix + mock `golden_cash.json` so you can build in parallel before Role A's real one arrives Day 3 EOD (or Day 2 EOD sub-milestone).

**Effort:** 7 hours

### Step 1.1 — Repo setup (15 min)

```bash
git clone <your-repo-url> envestnet-sdg
cd envestnet-sdg
git checkout -b feature/phase-2

mkdir -p configs/rules
mkdir -p output
mkdir -p tests
touch test_data_gen.py
touch tests/test_data_gen.py
```

(Role C may have already created top-level structure. Just add yours on top.)

### Step 1.2 — Python virtual environment (15 min)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pyspark==3.5.4 pandas==2.2.3 pyarrow==17.0.0 faker==30.0.0 pydantic==2.9.0 click==8.1.7 pytest==8.3.0 pytest-cov==5.0.0
```

### Step 1.3 — Verify Faker determinism (10 min)

```python
# verify_faker.py
from faker import Faker
fake = Faker()

Faker.seed(42)
print("Run 1:", [fake.name() for _ in range(3)])

Faker.seed(42)
print("Run 2:", [fake.name() for _ in range(3)])
# These must be identical
```

### Step 1.4 — JSON Contract Sync with Role A and Role C (90 min)

The most important meeting of the entire POC. All three of you, the synthetic file open (which Role A is building today). Hash out:

1. Field naming convention (UPPERCASE_SNAKE_CASE)
2. Type vocabulary (`account_number`, `cusip`, `date`, etc.)
3. Exact JSON shape
4. What you need from the contract to generate records

Outcome committed by Role C as `configs/golden_reference_schema.md`. Pull it to your branch.

### Step 1.5 — Coverage matrix (45 min)

Built around the 7 real txn codes observed in `Sal_csh.txt`, varied along dimensions that make each one interesting to UMP validation.

`configs/rules/coverage-matrix.json`:

```json
{
  "WTFEE": ["small", "large"],
  "JRL":   ["TO_TYPE_1", "FROM_TYPE_2", "TO_ROTH", "FROM_IRA"],
  "STAX":  ["common_stock", "fund"],
  "RDIV":  ["small", "medium", "large"],
  "WRAP":  ["quarterly"],
  "RPRM":  ["to_roth", "to_reg"],
  "YRINC": ["common_pos", "common_neg", "fund_pos", "fund_neg"]
}
```

Math check: 2+4+2+3+1+2+4 = **18 valid combinations.**

Distribution rationale:
- **WTFEE**: domestic (small ~$35) and international (larger $55+); could extend to "very large" tier
- **JRL**: 4 sub-types based on Sal_csh.txt descriptions ("TRF FDS TO TYPE 1", "TRF FDS FRM TYPE 2", "TO ROTH", "FROM IRA")
- **STAX**: foreign tax withholding seen against both common stocks (TELUS CORP, IMPERIAL OIL) and funds (PIMCO INCOME)
- **RDIV**: reinvested dividends always for funds; vary by amount tier
- **WRAP**: management fee, billed quarterly
- **RPRM**: premium distribution, To Roth or To Reg account
- **YRINC**: year income with both positive and negative cases (negatives are valid — dividend reversals)

### Step 1.6 — Write your mock golden reference (90 min)

This is what unlocks parallel work. You build a mock based on the actual `Sal_csh.txt` sample structure.

`configs/mock_golden_cash.json`:

```json
{
  "custodian_id": "stonex",
  "file_type": "CASH_TRANSACTION",
  "source_filename": "Sal_csh.txt",
  "delimiter": "|",
  "record_format": "single_line_variable_length",
  "field_count_range": [45, 58],
  "has_header": false,
  "generated_at": "2026-04-28T10:00:00Z",
  "source_record_count": 22,
  "anchor_fields": [
    {"position": 0, "name": "RECORD_TYPE", "stable": true, "always_value": "A"},
    {"position": 3, "name": "ACCT_NUM", "stable": true},
    {"name": "TXN_CD", "stable": false, "detection": "first_uppercase_token_after_amount_block"},
    {"position": -1, "name": "TIMESTAMP", "stable": true}
  ],
  "fields": [
    {"name": "RECORD_TYPE", "inferred_type": "enum", "required": true, "allowed_values": ["A"]},
    {"name": "ACCT_NUM", "inferred_type": "account_number", "required": true, "min_length": 8, "max_length": 8, "pattern": "\\d{8}"},
    {"name": "BRANCH_CODE", "inferred_type": "string", "required": false, "sample_values": ["M801", "MP85", "FR01", "5U01", "6602", "N105", "MA38"]},
    {"name": "TRADE_DATE", "inferred_type": "date", "required": true, "format": "YYYY-MM-DD"},
    {"name": "SETTLE_DATE", "inferred_type": "date", "required": false, "format": "YYYY-MM-DD"},
    {"name": "PROCESS_DATE", "inferred_type": "date", "required": false, "format": "YYYY-MM-DD"},
    {"name": "QUANTITY", "inferred_type": "decimal", "required": true, "min": 0, "max": 0, "default": "0.00000"},
    {"name": "TXN_CD", "inferred_type": "enum", "required": true,
     "allowed_values": ["WTFEE","JRL","STAX","RDIV","WRAP","RPRM","YRINC"]},
    {"name": "AMOUNT", "inferred_type": "decimal", "required": true,
     "min": -10000.00, "max": 100000.00,
     "allows_negative": true, "negative_allowed_for": ["YRINC", "JRL"]},
    {"name": "CUSIP", "inferred_type": "cusip", "required": false,
     "required_for": ["STAX", "RDIV"], "min_length": 9, "max_length": 9},
    {"name": "DESCRIPTION", "inferred_type": "string", "required": false, "max_length": 80},
    {"name": "TIMESTAMP", "inferred_type": "timestamp", "required": true, "format": "M/D/YYYY h:mm:ss A"}
  ]
}
```

### Step 1.7 — Coverage matrix module (90 min)

```
Add to test_data_gen.py:

1. Load coverage matrix from configs/rules/coverage-matrix.json into a dict
2. get_coverage_entries() -> list[tuple[str, str]]
   Returns 18 (txn_code, variant) tuples
3. is_valid_combination(txn_code: str, variant: str) -> bool

NO AI/LLM calls. Pure Python + json stdlib.

Tests:
- WTFEE only maps to small, large
- WRAP only maps to quarterly
- RDIV only maps to small, medium, large
- get_coverage_entries() returns exactly 18 entries
- is_valid_combination("WTFEE","small") is True
- is_valid_combination("WTFEE","quarterly") is False
- is_valid_combination("YRINC","common_neg") is True
```

### Step 1.8 — Commit + EOD sync (15 min)

```bash
git add .
git commit -m "Day 1: coverage matrix + mock golden ref + JSON contract"
git push origin feature/phase-2
```

EOD sync with Role A and Role C.

**End of Day 1 deliverable:** Coverage matrix loads · Mock golden reference written · JSON contract committed.

---

## Day 2 — Faker Factory + CUSIP Algorithm + Cash Record Generators

**Goal:** Build the data factory — CUSIP algorithm, dates, amount distributions per txn type — all deterministic from seed.

**Effort:** 8 hours (heavy day)

### Step 2.1 — Seeded Faker factory scaffolding (90 min)

```
Add to test_data_gen.py:

from faker import Faker

class DataFactory:
    def __init__(self, seed: int):
        self.fake = Faker()
        Faker.seed(seed)
        self.seed = seed

    def generate_account_number(self) -> str:
        # 8 random digits (Stonex uses 8-digit accounts in cash file)
        # self.fake.numerify('########')

    def generate_trade_date(self) -> datetime:
        # Random business day in last 90 days, format YYYY-MM-DD
        # Skip weekends (weekday() in {5, 6})

    def generate_settle_date(self, trade_date: datetime) -> datetime:
        # Same day or T+1/T+2 (cash transactions often same-day)

    def generate_timestamp(self) -> str:
        # M/D/YYYY h:mm:ss A format (e.g., "4/1/2026 10:03:05 PM")

    def generate_branch_code(self) -> str:
        # Sample from observed: M801, MP85, FR01, 5U01, 6602, N105, MA38, ...

NO AI calls. Pure Faker + Python stdlib.

Tests:
- Two factories with same seed produce identical output
- Account numbers are 8 digits
- generate_trade_date never returns weekend
- generate_timestamp matches "M/D/YYYY h:mm:ss A" pattern
```

### Step 2.2 — CUSIP generator with check digit (2 hours)

```
Add to DataFactory class:

CUSIP CHECK DIGIT ALGORITHM (CRITICAL — implement exactly):

9 chars total = 8 issuer/issue + 1 check digit.
For each char position 0-7:
  - Digit (0-9): use digit value
  - Letter (A-Z): position in alphabet + 9 (A=10..Z=35)
  - At positions 1, 3, 5, 7 (0-indexed): double the value
  - If doubled value >= 10: sum its digits (e.g. 14 -> 1+4 = 5)
Sum all 8 values.
Check digit = (10 - (sum mod 10)) mod 10

def generate_cusip(self) -> str:
    # 8-char alphanumeric prefix + computed check digit

def validate_cusip(self, cusip: str) -> bool:
    # Recompute check digit, compare to last char

NO AI calls.

Tests against REAL CUSIPs from sal_rad.txt sample (these MUST validate as TRUE):
- "316146109" FBNDX (Fidelity Investment Grade Bond)
- "31617K303" FSTGX (Fidelity Short-Term Government Income)
- "31617K881" FTBFX (Fidelity Total Bond)
- "354723702" FRHIX (Franklin High Yield Tax-Free)
- "277923660" EAFAX (Eaton Vance Floating Rate Advantage)
Tests for invalid:
- validate_cusip() False for: "000000000", "123456789"
- 50 generated CUSIPs all pass self-validation
```

### Step 2.3 — Cash transaction amount generators (3 hours)

```
Add to DataFactory class:

def generate_amount(self, txn_code: str, variant: str) -> float:
    """
    Amount distributions per txn_code based on Sal_csh.txt sample:

    WTFEE:
      small: uniform 25.00 - 50.00 (domestic wire fee, ~$35)
      large: uniform 1000.00 - 5000.00 (large transfer fee)

    JRL:
      TO_TYPE_1, FROM_TYPE_2: uniform 25.00 - 250.00
      TO_ROTH, FROM_IRA:      uniform 50.00 - 500.00
      Note: FROM_TYPE_2 should generate negative amount (mirror of TO_TYPE_1)

    STAX:
      common_stock: uniform 1.00 - 100.00 (foreign tax withholding)
      fund:         uniform 0.01 - 50.00

    RDIV:
      small:  uniform 0.01 - 1.00
      medium: uniform 1.00 - 50.00
      large:  uniform 50.00 - 500.00

    WRAP:
      quarterly: uniform 100.00 - 1000.00 (mgmt fee for quarter)

    RPRM:
      to_roth, to_reg: uniform 100.00 - 5000.00 (premium distribution)

    YRINC:
      common_pos, fund_pos: uniform 100.00 - 5000.00
      common_neg, fund_neg: -1 * uniform 100.00 - 5000.00 (dividend reversal)

    Round to 2 decimal places.
    """

def generate_description(self, txn_code: str, variant: str) -> str:
    """
    Realistic descriptions sampled from Sal_csh.txt:
    WTFEE: "WIRE TRANSFER FEE" or "INTL WIRE TRANSFER FEE"
    JRL:   "TRF FDS TO TYPE 1", "TRF FDS FRM TYPE 2", "TRF TO ROTH"
    STAX:  "FRGN-W/H @ SOURCE"
    RDIV:  "<FUND NAME> REINVEST TO OTHER FUND"
    WRAP:  "MGMT FEE|BILL VAL <amount>|<period>"
    RPRM:  "PREM DIST TO ROTH" or "PREM DIST TO REG"
    YRINC: "DIVIDENDS AND INTEREST"
    """

def needs_security(self, txn_code: str) -> bool:
    """STAX and RDIV reference securities. Others don't."""
    return txn_code in ("STAX", "RDIV")

NO AI calls.

Tests:
- WTFEE small in [25, 50]
- WTFEE large in [1000, 5000]
- YRINC common_neg always negative
- WRAP quarterly in [100, 1000]
- needs_security("STAX") is True
- needs_security("WTFEE") is False
```

### Step 2.4 — Smoke test against mock (30 min)

```python
# tests/smoke_factory.py
from test_data_gen import DataFactory, get_coverage_entries

factory = DataFactory(seed=42)
for txn_code, variant in get_coverage_entries():
    acct = factory.generate_account_number()
    dt = factory.generate_trade_date()
    amt = factory.generate_amount(txn_code, variant)
    desc = factory.generate_description(txn_code, variant)
    cusip = factory.generate_cusip() if factory.needs_security(txn_code) else ""
    print(f"{txn_code:6} {variant:14} acct={acct} amt={amt:>10.2f} cusip={cusip:9} desc={desc}")
```

Eyeball-check the 18 lines. Reasonable distributions per txn type?

```bash
git commit -am "Day 2: CUSIP algorithm + cash amount generators + tests"
git push origin feature/phase-2
```

**End of Day 2 deliverable:** All generators work. CUSIP algorithm verified against real fund CUSIPs.

---

## Day 3 — 72 Positive Records + Mock-to-Real Swap

**Goal:** Generate 72 positive records (4 per coverage combo) from mock golden_cash.json. Swap to Role A's real `golden_cash.json` EOD (or earlier if Role A delivers Day 2 sub-milestone on time).

**Effort:** 7 hours

### Step 3.1 — Positive record generator (3 hours)

```
Add to test_data_gen.py:

def generate_positive_records(golden_ref: dict, seed: int = 42, records_per_combo: int = 4) -> list[dict]:
    """
    For each (txn_code, variant) in get_coverage_entries():
      For i in range(records_per_combo):
        Generate a complete record dict with fields from golden_ref:
          RECORD_TYPE='A', ACCT_NUM, BRANCH_CODE, TRADE_DATE, SETTLE_DATE,
          QUANTITY=0.00000, TXN_CD, AMOUNT, CUSIP (if applicable),
          DESCRIPTION, ..., TIMESTAMP

    Use appropriate generator per field type.
    Variable-length: include CUSIP only when needs_security() is True.
    Mark records with metadata for manifest:
      _txn_code, _variant, _case_type='positive', _expected_outcome='accept'


    Returns: list of dicts (18 combos × 4 = 72 records by default)
    """

NO AI calls.

Tests:
- Returns exactly 72 records
- All 18 combos represented
- Same seed -> identical output across two runs
- Every record has all required fields populated
```

### Step 3.2 — Seed determinism test (CRITICAL) (30 min)

```python
def test_seed_reproducibility():
    """Same seed -> identical output. Foundation of regression testing."""
    from test_data_gen import generate_positive_records, load_golden_ref

    golden = load_golden_ref("configs/mock_golden_cash.json")
    run1 = generate_positive_records(golden, seed=42)
    run2 = generate_positive_records(golden, seed=42)
    assert run1 == run2

def test_different_seeds_produce_different_output():
    golden = load_golden_ref("configs/mock_golden_cash.json")
    run1 = generate_positive_records(golden, seed=42)
    run2 = generate_positive_records(golden, seed=43)
    assert run1 != run2
```

### Step 3.3 — Test against mock golden reference (1 hour)

```bash
python -c "
from test_data_gen import generate_positive_records, load_golden_ref
golden = load_golden_ref('configs/mock_golden_cash.json')
records = generate_positive_records(golden, seed=42)
print(f'Generated {len(records)} records')
print('First record:', records[0])
print('Last record:', records[-1])
"
```

### Step 3.4 — MILESTONE: Mock-to-real swap (EOD, 90 min)

Role A delivers `data/gold/stonex/golden_reference.json` end of Day 3. Three-way walkthrough:

1. Open Role A's real golden_reference.json
2. Compare structure to your mock
3. Note any differences (extra fields, different distributions, edge cases your mock didn't have)
4. Swap your generator to consume the real one:

```bash
git fetch origin feature/phase-1
git checkout origin/feature/phase-1 -- data/gold/stonex/golden_reference.json
git checkout feature/phase-2

python -c "
from test_data_gen import generate_positive_records, load_golden_ref
golden = load_golden_ref('data/gold/stonex/golden_reference.json')
records = generate_positive_records(golden, seed=42)
print(f'Generated {len(records)} from REAL golden ref')
print('Sample:', records[0])
"
```

**Critical:** If anything is missing or wrong in real golden ref, raise it with Role A immediately. Don't try to work around it.

```bash
git commit -am "Day 3: 72 positive records + swap to real golden reference"
git push origin feature/phase-2
```

**End of Day 3 deliverable:** 72 positive records generate from real golden reference.

---

## Day 4 — Mutation Engine (HEAVIEST DAY)

**Goal:** All 9 mutations + immutability tests + manifest writer.

**Effort:** 8 hours

### Step 4.1 — Mutation engine (4 hours)

```
Add to test_data_gen.py:

CRITICAL: Always copy.deepcopy() the input record. NEVER mutate the original.

import copy
def mutate(record):
    clone = copy.deepcopy(record)
    # modify clone, never record

Each mutation returns a dict:
{
  "record": mutated_clone,
  "mutation_name": str,
  "case_type": "negative" | "invalid_format" | "missing_field" | "edge_case",
  "expected_outcome": "reject" | "warn",
  "expected_reason": str,
  "affected_field": str
}

Mutations (cash file scope):

1. strip_required_field(record, field_name)
   - Delete field_name from clone
   - missing_field, reject, "Required field missing: {field_name}"
   - Apply to: ACCT_NUM, TXN_CD, AMOUNT (one at a time)

2. inject_invalid_date(record, field_name)
   - Set TRADE_DATE or SETTLE_DATE to '9999-13-99' (invalid month/day)
   - invalid_format, reject

3. inject_text_in_numeric(record, field_name='AMOUNT')
   - Set AMOUNT to 'N/A'
   - invalid_format, reject

4. inject_invalid_cusip(record)
   - Pre-condition: record must be STAX or RDIV (txn types that reference securities)
   - Set CUSIP to '000000000'
   - negative, reject, "Invalid CUSIP — check digit failed"

5. inject_invalid_txn_code(record)
   - Set TXN_CD to 'ZZZ' (not in allowed list)
   - negative, reject, "Unrecognised transaction code: ZZZ"

6. inject_future_settle_date(record)
   - SETTLE_DATE = today + 365 days, YYYY-MM-DD format
   - negative, reject

7. inject_implausible_negative(record)  ← REWORKED FROM inject_negative_amount
   - Pre-condition: record must be a txn type that doesn't accept negatives
     (WTFEE, WRAP, RPRM, RDIV — but NOT YRINC or JRL which legitimately can be negative)
   - Flip the sign on AMOUNT (e.g., WTFEE 35.00 → -35.00)
   - negative, reject, "Implausible negative amount for txn type {TXN_CD}"
   - Why this matters: real cash data has legitimate negatives (YRINC reversals,
     JRL counter-entries). The mutation specifically targets txn types where
     negative is nonsensical.

Edge cases:
8. zero_amount(record)
   - AMOUNT = 0.00
   - edge_case, warn, "Zero amount transaction — investigate"

9. very_large_amount(record)
   - AMOUNT = 9999999.99 (> $1M)
   - edge_case, warn, "Amount exceeds typical bound"

Aggregator:
def generate_mutation_records(positive_records, num_per_mutation=1) -> list[dict]:
    """
    Apply each mutation to a suitable sample record.
    For mutations with pre-conditions (4, 7), pick records matching the
    pre-condition. For others, any positive record works.
    """

NO AI calls.
```

### Step 4.2 — Immutability tests (CRITICAL) (90 min)

```python
def test_mutations_dont_modify_original():
    """The most important test. Originals must never change."""
    from test_data_gen import strip_required_field

    original = {"ACCT_NUM": "12345678", "TXN_CD": "WTFEE", "AMOUNT": 35.00}
    snapshot = original.copy()

    result = strip_required_field(original, "ACCT_NUM")

    assert original == snapshot, "Original was modified — DEEP COPY BROKEN"
    assert "ACCT_NUM" not in result["record"]
    assert result["case_type"] == "missing_field"
    assert result["expected_outcome"] == "reject"

def test_invalid_cusip_mutation():
    from test_data_gen import inject_invalid_cusip
    original = {"CUSIP": "316146109", "TXN_CD": "RDIV"}
    result = inject_invalid_cusip(original)

    assert result["record"]["CUSIP"] == "000000000"
    assert original["CUSIP"] == "316146109"  # untouched
    assert result["case_type"] == "negative"

def test_implausible_negative_on_wtfee():
    """Mutation #7: WTFEE should never be negative."""
    from test_data_gen import inject_implausible_negative
    original = {"TXN_CD": "WTFEE", "AMOUNT": 35.00}
    result = inject_implausible_negative(original)
    assert result["record"]["AMOUNT"] == -35.00
    assert result["case_type"] == "negative"
    assert result["expected_outcome"] == "reject"

def test_implausible_negative_skipped_for_yrinc():
    """YRINC legitimately accepts negatives (dividend reversals).
    Mutation #7 should NOT apply to YRINC records."""
    from test_data_gen import is_eligible_for_implausible_negative
    assert not is_eligible_for_implausible_negative({"TXN_CD": "YRINC"})
    assert not is_eligible_for_implausible_negative({"TXN_CD": "JRL"})
    assert is_eligible_for_implausible_negative({"TXN_CD": "WTFEE"})
    assert is_eligible_for_implausible_negative({"TXN_CD": "WRAP"})

def test_zero_amount_warns_not_rejects():
    from test_data_gen import zero_amount
    original = {"AMOUNT": 35.00, "TXN_CD": "WTFEE"}
    result = zero_amount(original)
    assert result["record"]["AMOUNT"] == 0.00
    assert result["expected_outcome"] == "warn"  # NOT reject
```

### Step 4.3 — Manifest writer (90 min)

```
Add to test_data_gen.py:

def write_manifest(positive_records, mutated_records, run_meta, output_path):
    """
    Write manifest.json — audit log mapping every row to expected outcome.

    {
      "run_meta": {
        "custodian_id": str, "file_type": str, "seed": int,
        "generated_at": ISO, "total_rows": int
      },
      "summary": {
        "positive": int, "negative": int, "invalid_format": int,
        "missing_field": int, "edge_case": int, "total": int
      },
      "entries": [
        {"row": int (1-indexed), "case_type": str, "txn_code": str,
         "variant": str, "expected_outcome": str,
         "mutation_name": str, "expected_reason": str, "affected_field": str}
      ]
    }

    Row numbers must match the row in synthetic_cash.txt (both 1-indexed).
    """

Console summary:
╔══════════════════════════════════╗
║  SDG Run                         ║
║  Custodian:  stonex              ║
║  File type:  cash                ║
║  Seed:       42                  ║
║  Total:      81 rows             ║
║  Positive:   72 (accept)         ║
║  Negative:   4 (reject)          ║
║  Invalid:    2 (reject)          ║
║  Missing:    1 (reject)          ║
║  Edge:       2 (warn)            ║
╚══════════════════════════════════╝
```

```bash
git commit -am "Day 4: 9 mutations + immutability tests + manifest writer"
git push origin feature/phase-2
```

**End of Day 4 deliverable:** All mutations work. Originals never modified. Manifest writer producing correct output.

---

## Day 5 — Coverage + Mid-POC Checkpoint (MILESTONE)

**Goal:** 90%+ test coverage. Phase 2 complete EOD.

**Effort:** 7 hours

### Step 5.1 — Run orchestrator (2 hours)

```
Add to test_data_gen.py:

def run_full_generation(custodian: str, seed: int, case_type: str, extra_rows: int = 0) -> None:
    """
    Main entry point called by cli.py.

    1. Load golden_cash.json from data/gold/{custodian}/
    2. Load coverage matrix
    3. Generate 72 positive records (4 per coverage combo × 18 combos)
    4. Generate mutations based on case_type:
       - "all" -> all 9 mutations
       - "positive" -> none
       - "negative" -> only negative mutations
       - "invalid" -> only invalid_format
       - "missing" -> only missing_field
       - "edge" -> only edge_case
    5. Hand records to Role C's PSV renderer (in cli.py)
    6. Write manifest.json
    7. Print console summary
    """
```

### Step 5.2 — Coverage check (30 min)

```bash
pytest --cov=test_data_gen --cov-report=html tests/test_data_gen.py
open htmlcov/index.html
```

### Step 5.3 — Comprehensive mutation aggregator tests (2 hours)

```python
def test_all_mutations_have_valid_metadata():
    from test_data_gen import (strip_required_field, inject_invalid_date,
                                inject_text_in_numeric, inject_invalid_cusip,
                                inject_invalid_txn_code, inject_future_settle_date,
                                inject_implausible_negative, zero_amount, very_large_amount)

    # Base: a STAX record (has CUSIP) with WTFEE-style amount for negative test reuse
    base_with_cusip = {"ACCT_NUM": "12345678", "TRADE_DATE": "2026-04-01",
                       "TXN_CD": "STAX", "CUSIP": "316146109",
                       "AMOUNT": 18.08, "SETTLE_DATE": "2026-04-01"}

    base_no_cusip = {"ACCT_NUM": "12345678", "TRADE_DATE": "2026-04-01",
                     "TXN_CD": "WTFEE", "AMOUNT": 35.00, "SETTLE_DATE": "2026-04-01"}

    mutations = [
        strip_required_field(base_no_cusip, "ACCT_NUM"),
        inject_invalid_date(base_no_cusip, "TRADE_DATE"),
        inject_text_in_numeric(base_no_cusip, "AMOUNT"),
        inject_invalid_cusip(base_with_cusip),         # needs CUSIP-bearing record
        inject_invalid_txn_code(base_no_cusip),
        inject_future_settle_date(base_no_cusip),
        inject_implausible_negative(base_no_cusip),     # WTFEE → eligible
        zero_amount(base_no_cusip),
        very_large_amount(base_no_cusip),
    ]

    for m in mutations:
        assert all(k in m for k in ["record", "mutation_name", "case_type", "expected_outcome", "expected_reason"])
        assert m["case_type"] in ["negative", "invalid_format", "missing_field", "edge_case"]
        assert m["expected_outcome"] in ["reject", "warn"]
```

### Step 5.4 — Mid-POC stakeholder checkpoint (60 min)

You walk through Phase 2 (Role A walks Phase 1, Role C walks integration). Live demo:
1. Show coverage matrix
2. Generate 72 positive records live
3. Show one mutation example
4. Show Role C's manifest output

### Step 5.5 — Error handling (30 min)

```python
def run_full_generation(custodian, seed, case_type, extra_rows=0):
    golden_path = f"data/gold/{custodian}/golden_reference.json"
    if not os.path.exists(golden_path):
        click.echo(f"ERROR: Golden reference not found: {golden_path}", err=True)
        click.echo(f"  Run Phase 1 first: python cli.py prep run --custodian {custodian}", err=True)
        sys.exit(1)
```

```bash
git commit -am "Day 5 MILESTONE: Phase 2 complete + 90% coverage + checkpoint"
git push origin feature/phase-2
```

**End of Day 5 deliverable: PHASE 2 COMPLETE.** All mutations working, manifest writer correct, 90% coverage, mid-POC checkpoint passed.

---

## Day 6 — Self-Consistency Validation Review

**Goal:** Role C runs round-trip validation. You review results, fix any Phase 2 issues.

**Effort:** 6 hours

### Step 6.1 — Review validation report (1 hour)

Role C produces `VALIDATION_REPORT.md`. Read it. Identify Phase 2 issues:
- Positive records that should round-trip cleanly but don't
- Mutations that the cleanser unexpectedly fixed (mutation rule too weak)
- Edge cases that triggered unexpected behavior

### Step 6.2 — Fix Phase 2 issues (3 hours)

Common fixes:
- Mutation values not extreme enough — adjust to be more obviously bad
- Edge case warns when it should accept — tune thresholds
- Date format mismatch with what Phase 1 expects — align

Re-run validation with Role C until all expected mismatches are accounted for.

### Step 6.3 — DEPLOYMENT_GUIDE contributions (1 hour)

Role C owns the document. You contribute the "Phase 2 — Adjusting Coverage and Mutations" section:

```markdown
## Phase 2 — Adjusting Coverage and Mutations

The coverage matrix and mutation set are configured in:
  configs/rules/coverage-matrix.json   - txn_code × security_type combinations
  configs/rules/mutations.json (future) - mutation parameters

To add a new transaction type to the matrix:
  Edit coverage-matrix.json, add the txn_code with valid security types.
  No code changes required.

To tune mutation severity:
  Each mutation in test_data_gen.py has documented parameters.
  See MUTATIONS.md for the full catalog.

To increase test volume:
  python cli.py generate --custodian stonex --seed 42 --type all --rows 1000
```

```bash
git commit -am "Day 6: self-consistency fixes + deployment guide section"
git push origin feature/phase-2
```

**End of Day 6 deliverable:** Phase 2 hardened against round-trip validation. Deployment guide section written.

---

## Day 7 — Demo + Polish

**Effort:** 5 hours

### Step 7.1 — Phase 2 README section (1 hour)

```markdown
## Phase 2: Test Data Generation

### What it does
Consumes golden_cash.json. Produces synthetic test data with full coverage
plus controlled mutations for negative/invalid/missing/edge testing.

### How to run
python cli.py generate --custodian stonex --seed 42 --type all

### Options
--seed N       Reproducibility seed (same seed = byte-identical output)
--type X       positive | negative | invalid | missing | edge | all
--rows N       Extra positive rows beyond matrix minimum

### Output
output/{custodian}/synthetic_cash.txt — PSV file
output/{custodian}/manifest.json — audit log

### Coverage
18 (txn_code × variant) combinations × 4 records = 72 positive
+ 9 mutations = ~81 total rows

### Mutations
[List the 9 mutations with their expected outcomes]
```

### Step 7.2 — Demo rehearsal (1 hour)

Twice through the 5-min flow with Role A and Role C. Your slot:
- Run Phase 2 generation (1 min)
- Show synthetic_cash.txt output (15s)
- Show manifest.json mapping (15s)
- Demonstrate same seed = byte-identical (30s — run twice, diff)

### Step 7.3 — Demo delivery (30 min)

Live with stakeholders.

### Step 7.4 — Final commit + handover (1.5 hours)

```bash
git commit -am "Day 7: demo polish + final docs"
git push origin feature/phase-2
```

PR `feature/phase-2 → main`. Role A and Role C review and merge.

**End of Day 7 deliverable:** Phase 2 merged to main. Demo delivered.

---

## Daily Discipline

- **Standup (10 min):** Shipped · Doing · Blockers
- **EOD sync (10 min):** Demo what works · Tomorrow's plan
- **Stuck for 1 hour?** Ask. Don't burn 4 hours.
- **Test before committing.**

---

## Common Pitfalls

| Pitfall | Prevention |
|---|---|
| Mutations modifying original records | Always `copy.deepcopy()`. Test for it. |
| Same seed producing different output | Don't use Python's `random` directly — only Faker.seed(). Don't use `time` or `uuid`. Don't iterate `set()`. |
| CUSIP algorithm wrong | Test against known-valid CUSIPs (Apple/MS/Amazon). |
| Settlement date crossing weekends | Use `weekday() < 5` check, not just adding 2 days. |
| Manifest row numbers not matching file | Both 1-indexed. PSV renderer writes row 1 first, manifest row 1 references it. |
| Waiting for Role A's golden ref | You have a mock from Day 1. Don't block. |
| Editing Role A's or Role C's primary files | Never. Open an issue. |
| Scope creep (Position file Phase 2, Cost Basis, etc.) | Politely decline. Phase 2 scope = cash file only this POC. |

---

## Your North Star

By Day 7, demo:

1. Your generator consuming Role A's `golden_cash.json`
2. ~81 records with full coverage (18 combos × 4 + 9 mutations)
3. `synthetic_cash.txt` indistinguishable in format from real custodian file
4. `manifest.json` correctly mapping every row to expected outcome
5. Same seed = byte-identical output (proven with hash test by Role C)
6. Self-consistency round-trip validation passing

You own Phase 2. Own it well.

— *Nous Infosystems · Test Architecture Team*
