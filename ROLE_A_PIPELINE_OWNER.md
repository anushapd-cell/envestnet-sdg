# ROLE A — Pipeline Owner

## Your Mission

You own **Phase 1: Golden Data Preparation** for all 4 Stonex file types. You build a multi-line/single-line PSV reader that handles the variants, profile each of the 4 client-provided sample files, and produce 4 `golden_reference_*.json` files capturing the schema, types, ranges, and rules. Your output becomes the contract that Role B's generator consumes (cash file is Phase 2's input) and Role C's integration tests validate.

**Your file:** `golden_prep.py` (plus `smart_reader.py` helper)
**Your branch:** `feature/phase-1`
**Your duration:** 7 days · ~46 hours total · front-loaded
**Your North Star:** A working pipeline that ingests all 4 sample files (sal_act, Sal_csh, Sal_pos, sal_rad) and outputs 4 clean, complete `golden_reference_*.json` files by EOD Day 3, with `golden_cash.json` delivered as a sub-milestone EOD Day 2.

---

## Pre-Flight Checklist

- [ ] Local machine with 16 GB RAM minimum (PySpark needs it)
- [ ] Permission to install Python 3.12 + Java JDK 17
- [ ] Git repo cloned, push access confirmed
- [ ] You've read `ENVESTNET_SDG_POC_Master_PLAN.md`
- [ ] You've read `POC_THREE_PERSON_SPLIT_GUIDE.md`
- [ ] You've read this entire file before opening any code
- [ ] All 4 client sample files (`sal_act.txt`, `Sal_csh.txt`, `Sal_pos.txt`, `sal_rad.txt`) accessible

---

## Day 1 — Setup + Multi-line Parser POC + JSON Contract Sync

**Goal:** Working dev environment + a `smart_reader.py` module that reads all 4 sample files into PySpark DataFrames + JSON contract agreed with Role B and Role C.

**Effort:** 8 hours (heavy day — milestone work)

### Step 1.1 — Repo and folder structure (15 min)

```bash
git clone <your-repo-url> envestnet-sdg
cd envestnet-sdg
git checkout -b feature/phase-1

mkdir -p configs/rules
mkdir -p ref_files
mkdir -p data/{bronze,silver,gold}
mkdir -p tests
touch golden_prep.py
touch tests/__init__.py
touch tests/test_golden_prep.py
```

(Role C may have already created the top-level scaffolding. If so, just add your folders on top.)

### Step 1.2 — Python virtual environment (15 min)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pyspark==3.5.4 pandas==2.2.3 pyarrow==17.0.0 pydantic==2.9.0 click==8.1.7 pytest==8.3.0 pytest-cov==5.0.0 faker==30.0.0
```

### Step 1.3 — Verify PySpark works (15 min)

```python
# verify_spark.py
from pyspark.sql import SparkSession
spark = SparkSession.builder.master("local[*]").appName("verify").getOrCreate()
df = spark.createDataFrame([(1, "test")], ["id", "name"])
df.show()
spark.stop()
```

If this fails, fix before moving on. macOS common fix: `export JAVA_HOME=$(/usr/libexec/java_home -v 17)`.

### Step 1.4 — Multi-line parser proof-of-concept (2.5 hours) — **CRITICAL**

This is the keystone deliverable that makes the mock-data approach work. The 4 sample files include 2 multi-line variants and 1 variable-length variant. Build a reader that handles all three formats from Day 1.

Drop the 4 client-provided sample files into `ref_files/`:

```bash
cp /path/to/uploads/sal_act.txt ref_files/
cp /path/to/uploads/Sal_csh.txt ref_files/
cp /path/to/uploads/Sal_pos.txt ref_files/
cp /path/to/uploads/sal_rad.txt ref_files/
```

Open Cursor / Claude Code and use this prompt:

```
Create a Python module called smart_reader.py that handles three PSV variants:

1. SINGLE-LINE FIXED-WIDTH (e.g., Sal_pos.txt — 39 fields per line)
2. SINGLE-LINE VARIABLE-WIDTH (e.g., Sal_csh.txt — 45–58 fields per line)
3. MULTI-LINE (e.g., sal_act.txt with dashed-line separator;
   sal_rad.txt with blank-line separator)

Function signature:
def read_psv_file(file_path: str, mode: str = 'auto') -> List[List[str]]

Where mode is one of:
- 'single_line'           : one record per line
- 'multi_line_dashed'     : records separated by lines matching r'^-{20,}$'
- 'multi_line_blank'      : records separated by blank lines
- 'auto'                  : detect based on file content

Behavior:
- For single_line: read each non-empty line, split on '|', return list of fields
- For multi-line variants: detect record boundaries, concatenate physical lines
  into one logical line (joined with '|'), split on '|', return list of fields
- Strip trailing whitespace on each field; don't strip leading whitespace
  inside fields (some descriptions have leading spaces)
- Handle records of different lengths gracefully (don't assume fixed schema)
- Return: list of records, each record is a list of string fields

Auto-detection rule:
- If file contains lines matching r'^-{20,}$' → multi_line_dashed
- Else if file contains 2+ consecutive newlines AND record count seems
  consistent with grouped lines → multi_line_blank
- Else → single_line

Write a __main__ block that, given a file path argument, reads the file,
prints record count, and prints the first 2 records (truncated to first 10 fields).
```

Verify on all 4 files:

```bash
python smart_reader.py ref_files/sal_act.txt    # expect 14 records, ~197 fields each
python smart_reader.py ref_files/Sal_csh.txt    # expect 22 records, 45-58 fields each
python smart_reader.py ref_files/Sal_pos.txt    # expect 17 records, 39 fields each
python smart_reader.py ref_files/sal_rad.txt    # expect 17 records, ~40 fields each
```

If all 4 produce sensible record counts, you've cleared the hardest technical hurdle of the POC. Save this module — Role C will integrate it into the CLI on Day 4.

### Step 1.5 — JSON Contract Sync with Role B and Role C (90 min)

The most important meeting of the entire POC. All three of you, the smart_reader output open in front of you, hash out:

1. **Field naming convention** — UPPERCASE_SNAKE_CASE (`ACCT_NUM`, `TRADE_DATE`, `TXN_CD`)
2. **Type vocabulary** — `account_number` · `cusip` · `date` · `integer` · `decimal` · `enum` · `string` · `timestamp`
3. **Exact JSON shape** — see template in `POC_THREE_PERSON_SPLIT_GUIDE.md` Section 4
4. **Anchor field strategy** — for variable-length cash records, agree which positions are stable (record_type, account#, dates, timestamp) and which fields are detected by pattern (txn_code = first uppercase 3–5 char token in mid-record)
5. **Required field metadata** — what does Role B need to generate? What does Role C need to validate?

**Decision: which file's golden reference is the contract for Phase 2?**

Answer: `golden_cash.json`. Role A delivers this by EOD Day 2 (sub-milestone) so Role B can swap from mock to real reference on Day 3 morning. The other 3 golden references (`golden_account.json`, `golden_position.json`, `golden_rad.json`) follow by EOD Day 3 (full milestone).

**Outcome:** Write the agreement to `configs/golden_reference_schema.md`. Role C commits it to `main`. All three branches pull from main.

```bash
# Role C does:
git checkout main
# add configs/golden_reference_schema.md
git commit -m "Day 1: JSON contract agreed by all three roles"
git push

# Then you do:
git checkout feature/phase-1
git rebase main
```

### Step 1.6 — Bronze ingestion start (90 min)

Open `golden_prep.py`. AI prompt for Cursor / Claude Code:

```
Create a Python module golden_prep.py that ingests a custodian PSV file
using PySpark, leveraging the smart_reader module for record extraction.

Function signature:
ingest_bronze(file_path: str, custodian_id: str, file_type: str, mode: str = 'auto') -> str

Behavior:
- Use smart_reader.read_psv_file(file_path, mode) to extract records
- Pad records to max field count (some files have variable record lengths)
- Convert to PySpark DataFrame, all columns as StringType (no casting at this layer)
- Add metadata columns using pyspark.sql.functions.lit():
  _source_file, _custodian_id, _file_type, _ingested_at, _record_count, _max_fields
- Write Parquet to data/bronze/{custodian_id}/{file_type}/
- Return the output path

Add docstring + type hints on every function.
Include click CLI supporting all 4 file types:
  python golden_prep.py ingest --input ./ref_files/Sal_csh.txt --custodian stonex --file-type cash
  python golden_prep.py ingest --input ./ref_files/Sal_pos.txt --custodian stonex --file-type position
  python golden_prep.py ingest --input ./ref_files/sal_act.txt --custodian stonex --file-type account
  python golden_prep.py ingest --input ./ref_files/sal_rad.txt --custodian stonex --file-type rad

NO AI/LLM API calls. Pure PySpark + Python stdlib only.
```

Run it for all 4 files:

```bash
for ft in cash position account rad; do
  case $ft in
    cash) f=Sal_csh.txt ;;
    position) f=Sal_pos.txt ;;
    account) f=sal_act.txt ;;
    rad) f=sal_rad.txt ;;
  esac
  python golden_prep.py ingest --input ./ref_files/$f --custodian stonex --file-type $ft
done
```

Verify by reading one back:

```python
from pyspark.sql import SparkSession
spark = SparkSession.builder.master("local[*]").getOrCreate()
df = spark.read.parquet("data/bronze/stonex/cash/")
df.show(5)
print("Row count:", df.count())  # should be 22 for cash
spark.stop()
```

### Step 1.7 — Commit + EOD sync (15 min)

```bash
git add .
git commit -m "Day 1: smart_reader for 4-file PSV variants + Bronze ingestion + JSON contract"
git push origin feature/phase-1
```

EOD sync with Role B and Role C: shipped, tomorrow's plan, blockers.

**End of Day 1 deliverable:** Synthetic reference file built · Bronze ingestion working · JSON contract committed.

---

## Day 2 — Profiler with Type Inference + Cash Sub-Milestone

**Goal:** Auto-detect data types for the 4 file types. **Deliver `golden_cash.json` by EOD** as the sub-milestone that unblocks Role B's swap from mock to real reference. Account and rad (multi-line) profilers may continue into Day 3.

**Effort:** 7 hours

### Step 2.1 — Build the profiler (3.5 hours)

AI prompt:

```
Add to golden_prep.py:
profile_silver(custodian_id: str, file_type: str) -> dict

Reads Bronze Parquet from data/bronze/{custodian_id}/{file_type}/.
For each column (excluding metadata starting with _), infer:

TYPE DETECTION (priority order):
1. account_number: 6-12 chars, all digits, consistent length
2. cusip: 9 alphanumeric chars, valid mod-10 check digit (validate it!)
3. date: matches YYYY-MM-DD or YYYYMMDD or M/D/YYYY h:mm:ss XM (timestamp)
4. integer: all values whole numbers (>95% threshold)
5. decimal: contains decimals (try float() succeeds)
6. enum: cardinality < 50, capture allowed_values + frequency
7. string: fallback

PER COLUMN COMPUTE:
- null_rate (% nulls/empties/whitespace)
- sample_values (first 3 distinct non-null)
- numerics: min, max, mean, percentiles (p10, p50, p90); allows_negative flag
- strings: min_length, max_length
- dates: earliest, latest, format detected
- enums: value distribution as { value: frequency }

VARIABLE-LENGTH RECORDS (cash file):
- Some records have 45 fields, others have 58. Pad missing trailing fields with null.
- For columns where >30% of values are null, mark "optional": true
- For TXN_CD detection: scan each record for the first uppercase 3-5 char token
  appearing after the account number block; that's the txn_code anchor.

OUTPUT to data/silver/{custodian_id}/{file_type}/profile.json
RETURN profile dict

CLI:
python golden_prep.py profile --custodian stonex --file-type cash

NO AI calls. Pure rule-based PySpark + Pandas + stdlib.
```

### Step 2.2 — CUSIP check digit validator (45 min)

```
Add helper to golden_prep.py:

def validate_cusip(cusip: str) -> bool:
    """
    CUSIP CHECK DIGIT ALGORITHM:
    9 chars total = 8 issuer/issue + 1 check digit.
    For each char position 0-7:
      - Digit (0-9): use digit value
      - Letter (A-Z): position in alphabet + 9 (A=10..Z=35)
      - At positions 1, 3, 5, 7: double the value
      - If doubled value >= 10: sum its digits
    Sum all 8 values.
    Check digit = (10 - (sum mod 10)) mod 10
    Returns True if last char matches computed check digit.
    """

Test against real CUSIPs from sal_rad.txt (all should validate as TRUE):
- "316146109" FBNDX (Fidelity Investment Grade Bond)
- "31617K303" FSTGX (Fidelity Short-Term Government Income)
- "31617K881" FTBFX (Fidelity Total Bond)
- "354723702" FRHIX
- "277923660" EAFAX

Test invalid:
- "000000000" → invalid
- "123456789" → invalid
```

### Step 2.3 — Run profile + finalize golden_cash.json — **SUB-MILESTONE** (2 hours)

```bash
python golden_prep.py profile --custodian stonex --file-type cash
python golden_prep.py profile --custodian stonex --file-type position

# Quick finalize for cash to unblock Role B
python golden_prep.py cleanse --custodian stonex --file-type cash
python golden_prep.py finalize --custodian stonex --file-type cash --output data/gold/stonex/golden_cash.json
```

Verify against the cash sample:
- [ ] TXN_CD detected as `enum` with values WTFEE, JRL, STAX, RDIV, WRAP, RPRM, YRINC?
- [ ] Date columns detected as `date`?
- [ ] Amount column detected as `decimal` with `allows_negative: true`?
- [ ] Account number detected as `account_number` with 8-char fixed length?

**Sub-milestone EOD Day 2:** `data/gold/stonex/golden_cash.json` exists and Role B can consume it. Walk Role B through it before they leave for the day so they can swap mock-to-real on Day 3 morning.

### Step 2.4 — Tests (45 min)

```python
import pytest
from pyspark.sql import SparkSession

@pytest.fixture(scope="module")
def spark():
    s = SparkSession.builder.master("local[*]").getOrCreate()
    yield s
    s.stop()

def test_validate_cusip_real_fund_cusips():
    from golden_prep import validate_cusip
    # Real CUSIPs from Sal_rad.txt sample
    assert validate_cusip("316146109")   # FBNDX
    assert validate_cusip("31617K303")   # FSTGX
    assert validate_cusip("31617K881")   # FTBFX

def test_validate_cusip_known_invalid():
    from golden_prep import validate_cusip
    assert not validate_cusip("000000000")
    assert not validate_cusip("123456789")

def test_profiler_detects_cash_txn_codes():
    from golden_prep import infer_column_type
    values = ["WTFEE"]*4 + ["JRL"]*9 + ["STAX"]*3 + ["RDIV"]*2 + ["WRAP"] + ["RPRM"] + ["YRINC"]
    assert infer_column_type(values) == "enum"

def test_profiler_detects_negative_decimals():
    from golden_prep import profile_column
    p = profile_column(["35.00", "-5000.00", "50.22", "114.54"])
    assert p["inferred_type"] == "decimal"
    assert p["allows_negative"] == True

def test_profiler_handles_nulls():
    from golden_prep import infer_column_type
    values = ["100", "", None, "200", "300", "", None, "400", "500", "600"]
    assert infer_column_type(values) == "integer"
```

```bash
pytest tests/test_golden_prep.py -v
git commit -am "Day 2: profiler + CUSIP validator + golden_cash.json sub-milestone"
git push origin feature/phase-1
```

**End of Day 2 deliverable:** `golden_cash.json` complete, Role B unblocked. Profiler also runs cleanly on positions. Account + rad profiling continues into Day 3.

---

## Day 3 — Multi-line Files + Cleanser + Masker + All 4 Golden References (MILESTONE DAY)

**Goal:** Profile the 2 multi-line files (account, rad). Build cleanser + masker. Output all 4 `golden_reference_*.json` files by EOD. This is the contract Role B and Role C consume.

**Effort:** 8 hours

### Step 3.1 — Profile account + rad files (2 hours)

```bash
python golden_prep.py profile --custodian stonex --file-type account
python golden_prep.py profile --custodian stonex --file-type rad
```

Multi-line files have already been ingested in Bronze (Day 1's smart_reader handled them). The profiler should work — but expect quirks:
- Account file has ~197 fields per record. Many are sparse. Mark them optional.
- Rad file has CUSIPs at a known position — confirm `validate_cusip` passes for all 17 sample records.

### Step 3.2 — Cleanser (2 hours)

```
Add to golden_prep.py:
cleanse_data(custodian_id: str, file_type: str) -> dict

Reads Bronze, applies cleansing, writes to Silver:
- Trim whitespace from all string columns
- Strip dashes/spaces from account_number columns
- Standardize dates to YYYY-MM-DD (handle multiple input formats)
- Flag duplicates: add _is_duplicate column (keep first, mark rest)
- Flag rows missing required fields: add _is_quarantined column
- Write cleansed → data/silver/{custodian_id}/{file_type}/cleansed/
- Write quarantined → data/silver/{custodian_id}/{file_type}/quarantine/
- Return stats: {rows_in, rows_out, dupes_found, quarantined}

CLI: python golden_prep.py cleanse --custodian stonex --file-type cash
```

### Step 3.3 — PII Masker (1 hour)

```
Add to golden_prep.py:
mask_pii(custodian_id: str, file_type: str) -> dict

- Identifies PII columns from profile (account_number type, name patterns)
- Masks account numbers: keep last 4 digits, prefix XXXX (e.g., XXXX-1234)
- Replaces names with sequential synthetic IDs (SYNNAME_001, SYNNAME_002)
- Writes to data/silver/{custodian_id}/{file_type}/masked/
- Returns: {fields_masked: list, values_masked: int}

CLI: python golden_prep.py mask --custodian stonex --file-type account

Note: Account file has the most PII. Cash and rad have account numbers.
Position file has account numbers too. Apply masking selectively per file type.
```

### Step 3.4 — Finalize Gold for all 4 file types (2 hours)

```
Add to golden_prep.py:
finalize_gold(custodian_id: str, file_type: str) -> str

Reads profile.json + masked Silver data, produces golden_reference.json.
Output: data/gold/{custodian_id}/golden_{file_type}.json

Structure must match configs/golden_reference_schema.md (the agreed contract):

{
  "custodian_id": "stonex",
  "file_type": "CASH_TRANSACTION" | "POSITION" | "ACCOUNT" | "RAD",
  "source_filename": "Sal_csh.txt" | etc.,
  "delimiter": "|",
  "record_format": "single_line_fixed" | "single_line_variable_length" | "multi_line_dashed" | "multi_line_blank",
  "has_header": false,
  "generated_at": ISO timestamp,
  "source_record_count": int,
  "anchor_fields": [...],
  "fields": [
    { position, name, inferred_type, required, null_rate, ... }
  ]
}

CLI: python golden_prep.py finalize --custodian stonex --file-type cash
```

### Step 3.5 — End-to-end Phase 1 run for all 4 files (30 min)

```bash
for ft in cash position account rad; do
  python golden_prep.py ingest --input ./ref_files/$f --custodian stonex --file-type $ft
  python golden_prep.py profile --custodian stonex --file-type $ft
  python golden_prep.py cleanse --custodian stonex --file-type $ft
  python golden_prep.py mask --custodian stonex --file-type $ft
  python golden_prep.py finalize --custodian stonex --file-type $ft
done

ls -la data/gold/stonex/
# expect: golden_cash.json, golden_position.json, golden_account.json, golden_rad.json
```

### Step 3.6 — MILESTONE: Walkthrough with Role B and Role C (30 min)

This is your **Phase 1 milestone**. Three-way walkthrough:

1. Open all 4 `data/gold/stonex/golden_*.json` together
2. Role B confirms `golden_cash.json` has every field they need to consume
3. Role C confirms all 4 conform to the agreed contract
4. Role B can now swap from mock to real `golden_cash.json` (if not already done after Day 2)
5. Role C can now run end-to-end smoke tests

If anything is missing or wrong, fix it now. Their Day 4 work depends on this.

```bash
git add .
git commit -m "Day 3 MILESTONE: Phase 1 complete — golden_reference.json delivered"
git push origin feature/phase-1
```

**End of Day 3 deliverable: PHASE 1 COMPLETE.** `golden_reference.json` produced from synthetic file. Hand off to Role B and Role C.

---

## Day 4 — Profiler Refinement + Help Role B if Behind

**Goal:** Refine profiler based on edge cases you spotted yesterday. Be available to support Role B's mutation work and Role C's integration tests.

**Effort:** 6 hours (lighter day)

### Step 4.1 — Re-examine the golden reference (1 hour)

After overnight reflection, look at it again. Common refinements:
- [ ] Type misclassification (e.g., a numeric column with "N/A" got classified as string)
- [ ] Enum cardinality threshold wrong
- [ ] Date format edge cases handled
- [ ] Account numbers with leading zeros preserved
- [ ] Decimal precision matches input

### Step 4.2 — Add edge case handling + regression tests (3 hours)

For each refinement, write the regression test first:

```python
def test_profiler_handles_na_values_in_numeric_column():
    """Most numeric values, some 'N/A' — handle as null and reclassify."""
    values = ["100", "200", "N/A", "300", "400", "N/A", "500"]
    assert infer_column_type(values) in ["integer", "string"]

def test_profiler_handles_leading_zeros_in_account_numbers():
    values = ["00001234", "00005678", "00009012"]
    assert infer_column_type(values) == "account_number"

def test_profiler_handles_dates_in_mixed_formats():
    values = ["20250115", "2025-01-16", "20250117"]
    # Should still detect as 'date'
    assert infer_column_type(values) == "date"
```

### Step 4.3 — Be available to help Role B and Role C (2 hours)

If they're stuck on something pertaining to Phase 1's output, help. Don't touch their primary files — but reviewing their PRs and answering schema questions is your job today.

```bash
git commit -am "Day 4: profiler refinements + edge case handling"
git push origin feature/phase-1
```

**End of Day 4 deliverable:** Profiler hardened against edge cases. Available for cross-role support.

---

## Day 5 — Coverage + Mid-POC Checkpoint

**Goal:** 90%+ test coverage on Phase 1. Demo Phase 1 at mid-POC checkpoint.

**Effort:** 6 hours

### Step 5.1 — Coverage check (30 min)

```bash
pytest --cov=golden_prep --cov-report=html tests/test_golden_prep.py
open htmlcov/index.html
```

Identify uncovered lines.

### Step 5.2 — Edge case tests (3 hours)

- [ ] Empty file (0 rows)
- [ ] File with only header (1 row)
- [ ] File with all-null column
- [ ] File with mixed-type column
- [ ] Very long string values (1000+ chars)
- [ ] Unicode characters in string fields

### Step 5.3 — Error handling (1 hour)

```python
@prep.command("run")
def prep_run(input, custodian, file_type):
    if not os.path.exists(input):
        click.echo(f"ERROR: Input file not found: {input}", err=True)
        sys.exit(1)
    if os.path.getsize(input) == 0:
        click.echo(f"ERROR: Input file is empty: {input}", err=True)
        sys.exit(1)
```

### Step 5.4 — Mid-POC stakeholder checkpoint (60 min)

You walk through Phase 1 (Role B walks Phase 2, Role C walks integration). Live demo:
1. Show the 4 client-provided sample files in `ref_files/`
2. Run Phase 1 commands live for all 4 file types
3. Show all 4 generated `golden_*.json` files

Take feedback.

```bash
git commit -am "Day 5: 90% coverage + error handling + mid-POC checkpoint"
git push origin feature/phase-1
```

**End of Day 5 deliverable:** Phase 1 at 90%+ coverage. Mid-POC checkpoint done.

---

## Day 6 — Self-Consistency Validation Review

**Goal:** Role C runs self-consistency validation today (round-trip test on cash file). You review results and fix any Phase 1 issues.

**Effort:** 6 hours

### Step 6.1 — Review self-consistency report (1 hour)

Role C produces `VALIDATION_REPORT.md` from the round-trip test (cash file only). Read it. Identify any issues attributable to Phase 1:
- Type misclassification on second-pass profiling?
- Cleanser stripping fields it shouldn't?
- Masker removing data Phase 2 needed?
- Variable-length record handling drifted on synthetic vs sample?

### Step 6.2 — Fix Phase 1 issues (3 hours)

For any Phase 1 issues found, root-cause and fix. Re-run validation with Role C.

### Step 6.3 — DEPLOYMENT_GUIDE.md contributions (1 hour)

Role C owns this document. You contribute the "Phase 1 — Tuning on Real Data" section:

```markdown
## Phase 1 — Tuning on Real Data (post-deployment)

When pointed at the real Stonex Financial production files, the profiler may detect
new patterns not present in the small sample files. Things to watch for on first run,
per file type:

CASH (Sal_csh.txt):
1. New TXN_CD values beyond WTFEE/JRL/STAX/RDIV/WRAP/RPRM/YRINC → check profile.json's value_distribution
2. Wider field count range (sample showed 45-58, production may go higher)
3. Account number formats with non-numeric characters → may need cleanser tweak
4. New negative-amount-allowed txn types → update Phase 2's negative_allowed_for list

ACCOUNT (sal_act.txt):
1. Records with more or fewer than 4 lines → smart_reader auto-detects
2. New customer code values (TOD, IRA, ROTH, JTWROS, TRUST, etc.) → captured automatically

POSITION (Sal_pos.txt):
1. Field count drift from 39 → likely additional position attributes
2. New type indicators beyond R/C → captured automatically

RAD (sal_rad.txt):
1. CUSIPs that don't validate → likely stale data, flag in profile
2. New transaction codes beyond RDIV → captured automatically

To re-tune Phase 1 on real data:
  python cli.py prep run --input /path/to/real_Sal_csh.txt --custodian stonex --file-type cash
  python cli.py prep run --input /path/to/real_sal_act.txt --custodian stonex --file-type account
  python cli.py prep run --input /path/to/real_Sal_pos.txt --custodian stonex --file-type position
  python cli.py prep run --input /path/to/real_sal_rad.txt --custodian stonex --file-type rad

Then inspect data/gold/stonex/golden_*.json and confirm types look right.
If anything looks wrong, the profiler can be re-run after tuning rules in
configs/profiler_rules.json (no code changes needed for most adjustments).
```

```bash
git commit -am "Day 6: self-consistency fixes + deployment guide contribution"
git push origin feature/phase-1
```

**End of Day 6 deliverable:** Phase 1 hardened against round-trip validation. Deployment guide section written.

---

## Day 7 — Demo + Polish

**Goal:** Prove Phase 1 works in the demo. Polish README and tests.

**Effort:** 5 hours

### Step 7.1 — Phase 1 README section (1 hour)

In the main `README.md` (Role C owns the file, you contribute):

```markdown
## Phase 1: Golden Data Preparation

### What it does
Profiles a custodian file and produces golden_reference.json — a portable schema
blueprint capturing types, ranges, distributions, and rules.

### How to run
python cli.py prep run --input ./ref_files/your_file.txt --custodian stonex

### Output
data/gold/{custodian}/golden_reference.json

### Architecture
- Bronze: raw PSV → Parquet with metadata tags
- Silver: type inference, cleansing, PII masking
- Gold: schema blueprint with distributions

### To onboard another custodian
Run prep on the new file. No code changes needed.
```

### Step 7.2 — Demo rehearsal (1 hour)

Twice through the 5-minute demo flow with Role B and Role C. Time it. Your slot:
- Show the synthetic reference file (30s)
- Run Phase 1 (1 min)
- Show generated golden_reference.json briefly (30s)

### Step 7.3 — Demo delivery (30 min)

Live demo with stakeholders. Stay calm if something breaks — you have buffer time.

### Step 7.4 — Final commit + handover (1.5 hours)

```bash
git commit -am "Day 7: demo polish + final docs"
git push origin feature/phase-1
```

Open PR `feature/phase-1 → main`. Role B and Role C review and merge.

```bash
git tag v0.1.0-poc
```

**End of Day 7 deliverable:** Phase 1 merged to main. Demo delivered. POC complete.

---

## Daily Discipline

- **Standup (10 min):** What I shipped · What I'm doing today · Blockers
- **EOD sync (10 min):** Demo what's working · Tomorrow's plan
- **Stuck for 1 hour?** Ask. Don't burn 4 hours alone.
- **Test before committing.** Broken commits cost the next day.

---

## Common Pitfalls

| Pitfall | Prevention |
|---|---|
| Synthetic reference file too clean — profiler doesn't develop real cleansing rules | Include the messy rows on Day 1. Don't skip them. |
| Wrong type inference on synthetic file | Eyeball profile.json on Day 2. Don't move on if it looks wrong. |
| Account numbers losing leading zeros | Always read as StringType. Never cast to int in Phase 1. |
| Profiler hangs on large file | `df.sample(fraction=0.1, seed=42)` for files > 1M rows |
| JSON contract drift mid-week | Treat changes as breaking. Coordinate with B and C before changing. |
| Day 3 milestone slips past EOD | Day 4 morning escalation: ship a minimal golden_reference.json, refine in parallel |
| Editing Role B's or Role C's primary files | Never. Open an issue. |

---

## Your North Star

By Day 7, demo:

1. Synthetic reference file you built (Day 1)
2. Auto-generated `golden_reference.json` produced by your pipeline
3. Phase 2 (Role B) consuming it cleanly
4. Self-consistency validation passing (Role C's Day 6 result)
5. Deployment guide section that explains how Phase 1 tunes on real data post-delivery

You own Phase 1. Own it well. Roles B and C are counting on your Day 3 milestone.

— *Nous Infosystems · Test Architecture Team*
