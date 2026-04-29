# ROLE C — Integration & Validation Owner

## Your Mission

You own **everything that wires the system together and prepares it for client delivery.** You build the CLI, the PSV renderer that takes Role B's records and writes them in Role A's format, the integration tests that run end-to-end, the self-consistency validation that proves the round-trip works, and — critically — the `DEPLOYMENT_GUIDE.md` and `validate-environment` CLI that make this a true plug-and-play package.

You're the third leg of the stool. Without you, the 7-day plan doesn't fit.

**Your files:** `cli.py` · `validate_self_consistency.py` · `tests/test_integration.py` · `DEPLOYMENT_GUIDE.md` · `README.md` (overall integration) · the scaffolding for everyone
**Your branch:** `feature/integration`
**Your duration:** 7 days · ~45 hours total · evenly distributed
**Your North Star:** A package the Envestnet team can install on Day 1 in their environment, point at their real Stonex Financial file, and have working without code changes.

---

## Pre-Flight Checklist

- [ ] Local machine, Python 3.12 installable
- [ ] Git repo cloned, push access confirmed
- [ ] You've read `ENVESTNET_SDG_POC_Master_PLAN.md`
- [ ] You've read `POC_THREE_PERSON_SPLIT_GUIDE.md`
- [ ] You've read this entire file before opening any code
- [ ] You've at least skimmed Role A's and Role B's playbooks — you're the integration point between them, you need to know what they're producing

---

## Day 1 — Repo Scaffolding + JSON Contract Sync + CLI Skeleton

**Goal:** Set up the repo so Role A and Role B can hit the ground running. Be the third reviewer in the JSON contract sync. Stub out the CLI so end-to-end runs are possible from Day 2.

**Effort:** 6 hours (lighter day — scaffolding work)

### Step 1.1 — Clone repo and full project structure (30 min)

```bash
git clone <your-repo-url> envestnet-sdg
cd envestnet-sdg
git checkout -b feature/integration

# Build the complete folder structure for everyone
mkdir -p configs/rules
mkdir -p ref_files
mkdir -p data/{bronze,silver,gold}
mkdir -p output
mkdir -p tests
mkdir -p docs

touch cli.py
touch validate_self_consistency.py
touch tests/__init__.py
touch tests/test_integration.py
touch tests/conftest.py
touch requirements.txt
touch README.md
touch DEPLOYMENT_GUIDE.md
touch .gitignore
touch pytest.ini
touch ENVIRONMENT_CHECK.md
```

### Step 1.2 — Shared `requirements.txt` (15 min)

This is the canonical version everyone uses:

```
pyspark==3.5.4
pandas==2.2.3
pyarrow==17.0.0
faker==30.0.0
pydantic==2.9.0
click==8.1.7
pytest==8.3.0
pytest-cov==5.0.0
```

Commit this to main early so A and B both pull it.

### Step 1.3 — `.gitignore` (10 min)

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
data/bronze/*
data/silver/*
data/gold/*
ref_files/*
!ref_files/.gitkeep
output/*
!output/.gitkeep
.coverage
htmlcov/
.DS_Store
.vscode/
.idea/
*.log
```

Commit to main.

### Step 1.4 — pytest infrastructure (45 min)

`pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    integration: end-to-end integration tests (slower)
    slow: tests that take more than 1 second
```

`tests/conftest.py`:

```python
"""Shared pytest fixtures across all test modules."""
import pytest
from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def spark():
    """Single Spark session shared across all tests."""
    s = SparkSession.builder \
        .master("local[*]") \
        .appName("envestnet-sdg-tests") \
        .config("spark.sql.shuffle.partitions", "2") \
        .getOrCreate()
    s.sparkContext.setLogLevel("ERROR")
    yield s
    s.stop()

@pytest.fixture(scope="function")
def tmp_data_dir(tmp_path):
    """Per-test temporary data directory."""
    (tmp_path / "data" / "bronze").mkdir(parents=True)
    (tmp_path / "data" / "silver").mkdir(parents=True)
    (tmp_path / "data" / "gold").mkdir(parents=True)
    (tmp_path / "output").mkdir(parents=True)
    return tmp_path
```

### Step 1.5 — JSON Contract Sync with Role A and Role B (90 min)

Most important meeting of the entire POC. All three of you. The synthetic file Role A is building today is open. Hash out:

1. Field naming convention (UPPERCASE_SNAKE_CASE)
2. Type vocabulary (`account_number`, `cusip`, `date`, `integer`, `decimal`, `enum`, `string`)
3. Exact JSON shape — see master plan for template
4. What metadata Role B needs to generate
5. **Your role here:** keep the conversation focused. You're not the one consuming or producing the contract — you're the integrator. You ensure the contract makes sense from a packaging-and-deployment perspective.

**Outcome:** You commit `configs/golden_reference_schema.md` to main. Both A and B rebase off main.

```bash
git checkout main
# add configs/golden_reference_schema.md
git commit -m "Day 1: JSON contract agreed by all three roles"
git push
git checkout feature/integration
```

### Step 1.6 — CLI skeleton with stub commands (90 min)

Build the CLI structure so A and B can wire their commands in tomorrow:

```python
# cli.py
import click
import sys
import os

@click.group()
def cli():
    """Envestnet UMP Synthetic Test Data Generator."""
    pass

# ============================================================
# PHASE 1 (Role A) — Golden Data Preparation
# ============================================================
@cli.group()
def prep():
    """Phase 1: Golden Data Preparation."""
    pass

@prep.command("ingest")
@click.option("--input", required=True)
@click.option("--custodian", required=True)
@click.option("--file-type", default="transaction")
def prep_ingest(input, custodian, file_type):
    """Bronze ingestion (Role A — to be wired)."""
    click.echo(f"[STUB] ingest from {input} for {custodian}/{file_type}")

@prep.command("profile")
@click.option("--custodian", required=True)
@click.option("--file-type", default="transaction")
def prep_profile(custodian, file_type):
    """Silver profile (Role A — to be wired)."""
    click.echo(f"[STUB] profile {custodian}/{file_type}")

@prep.command("run")
@click.option("--input", required=True)
@click.option("--custodian", required=True)
@click.option("--file-type", default="transaction")
def prep_run(input, custodian, file_type):
    """Run all of Phase 1 end-to-end."""
    if not os.path.exists(input):
        click.echo(f"ERROR: Input file not found: {input}", err=True)
        sys.exit(1)
    # Role A wires these in:
    # ingest_bronze(input, custodian, file_type)
    # profile_silver(custodian, file_type)
    # cleanse_data(custodian, file_type)
    # mask_pii(custodian, file_type)
    # finalize_gold(custodian, file_type)
    click.echo("[STUB] Phase 1 end-to-end run")

# ============================================================
# PHASE 2 (Role B) — Test Data Generation
# ============================================================
@cli.command("generate")
@click.option("--custodian", required=True)
@click.option("--seed", default=42, type=int)
@click.option("--type", "case_type", default="all",
              type=click.Choice(["positive","negative","invalid","missing","edge","all"]))
@click.option("--rows", default=0, type=int)
def generate(custodian, seed, case_type, rows):
    """Phase 2: Generate synthetic test data."""
    golden_path = f"data/gold/{custodian}/golden_reference.json"
    if not os.path.exists(golden_path):
        click.echo(f"ERROR: Golden reference not found: {golden_path}", err=True)
        click.echo(f"  Run Phase 1 first: python cli.py prep run --input <file> --custodian {custodian}", err=True)
        sys.exit(1)
    # Role B wires this in:
    # run_full_generation(custodian, seed, case_type, rows)
    click.echo(f"[STUB] generate for {custodian}, seed={seed}, type={case_type}")

# ============================================================
# VALIDATION + ENVIRONMENT (Role C)
# ============================================================
@cli.command("validate-environment")
def validate_environment():
    """Pre-flight check: confirms environment is ready for the tool to run."""
    click.echo("[STUB] environment validation")

@cli.command("validate-self-consistency")
@click.option("--custodian", required=True)
def validate_self_consistency_cmd(custodian):
    """Round-trip validation: re-feed synthetic output through Phase 1."""
    click.echo(f"[STUB] self-consistency validation for {custodian}")

if __name__ == "__main__":
    cli()
```

Test that the skeleton runs:

```bash
python cli.py --help
python cli.py prep --help
python cli.py prep run --input ./fakefile.txt --custodian stonex
# Should error cleanly: "Input file not found"
```

### Step 1.7 — Commit + EOD sync (15 min)

```bash
git add .
git commit -m "Day 1: scaffolding + CLI skeleton + JSON contract committed"
git push origin feature/integration
```

EOD sync with Role A and Role B.

**End of Day 1 deliverable:** Repo scaffolding done · pytest infrastructure ready · CLI skeleton with stub commands · JSON contract committed.

---

## Day 2 — Test Infrastructure + Self-Consistency Scaffold

**Goal:** Stand up real test infrastructure with coverage reporting. Begin the self-consistency validation script. Define the PSV renderer interface so Role A and Role B both know what to expect.

**Effort:** 7 hours

### Step 2.1 — Coverage tooling (30 min)

```bash
# Run coverage on whatever exists
pytest --cov=cli --cov-report=html --cov-report=term tests/
```

Confirm the HTML report renders. Add to README the coverage commands.

### Step 2.2 — Build environment validation CLI (2 hours)

This is the keystone of the plug-and-play story. The Envestnet team should run this first when they install the tool — it confirms everything is in order before they try Phase 1.

`cli.py` — replace the stub:

```python
@cli.command("validate-environment")
def validate_environment():
    """Pre-flight check: confirms the environment is ready."""
    click.echo("Envestnet SDG — Environment Validation")
    click.echo("=" * 50)

    checks = []

    # 1. Python version
    import sys
    pyver = sys.version_info
    if pyver >= (3, 12):
        checks.append(("Python version >= 3.12", True, f"{pyver.major}.{pyver.minor}.{pyver.micro}"))
    else:
        checks.append(("Python version >= 3.12", False, f"Found {pyver.major}.{pyver.minor}"))

    # 2. Java for PySpark
    import subprocess
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=5)
        java_output = result.stderr or result.stdout
        if "17" in java_output or "11" in java_output or "21" in java_output:
            checks.append(("Java JDK installed", True, java_output.split("\n")[0]))
        else:
            checks.append(("Java JDK 11+ installed", False, "Found incompatible version"))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        checks.append(("Java JDK installed", False, "Not found in PATH"))

    # 3. Required Python packages
    required = ["pyspark", "pandas", "pyarrow", "faker", "click", "pydantic", "pytest"]
    for pkg in required:
        try:
            __import__(pkg)
            checks.append((f"Package: {pkg}", True, "installed"))
        except ImportError:
            checks.append((f"Package: {pkg}", False, "missing"))

    # 4. PySpark can start a session
    try:
        from pyspark.sql import SparkSession
        s = SparkSession.builder.master("local[*]").appName("env-check").getOrCreate()
        s.createDataFrame([(1,)], ["x"]).count()
        s.stop()
        checks.append(("PySpark session start", True, "OK"))
    except Exception as e:
        checks.append(("PySpark session start", False, str(e)[:60]))

    # 5. Required folders exist
    for d in ["configs", "ref_files", "data", "output"]:
        if os.path.isdir(d):
            checks.append((f"Folder: {d}/", True, "exists"))
        else:
            checks.append((f"Folder: {d}/", False, "missing"))

    # 6. JSON contract present
    schema_path = "configs/golden_reference_schema.md"
    if os.path.exists(schema_path):
        checks.append(("JSON contract", True, schema_path))
    else:
        checks.append(("JSON contract", False, "missing"))

    # Print results
    pass_count = sum(1 for _, ok, _ in checks if ok)
    fail_count = len(checks) - pass_count

    for label, ok, detail in checks:
        symbol = "✓" if ok else "✗"
        click.echo(f"  {symbol}  {label:<45} {detail}")

    click.echo("=" * 50)
    if fail_count == 0:
        click.echo(f"Result: ALL {pass_count} CHECKS PASSED — ready to run.")
        sys.exit(0)
    else:
        click.echo(f"Result: {fail_count} of {len(checks)} checks FAILED — fix before running.", err=True)
        sys.exit(1)
```

Test it:

```bash
python cli.py validate-environment
```

### Step 2.3 — Self-consistency validation script scaffold (2 hours)

`validate_self_consistency.py`:

```python
"""
Self-consistency validation: round-trip test.

The hypothesis: if we feed Phase 2's synthetic output back through Phase 1,
we should get a golden_reference.json substantially identical to the original.
This proves Phase 1 and Phase 2 are mutually consistent.

Workflow:
1. Generate synthetic data (Phase 2 output)
2. Feed it back into Phase 1 as if it were a new reference file
3. Compare the second-pass golden_reference.json to the original
4. For mutated rows (manifest says reject/warn), confirm Phase 1's cleanser
   either quarantines them or flags them.
"""

import json
import click
import os
import sys
from typing import Dict, List


def compare_golden_references(original: dict, regenerated: dict) -> dict:
    """
    Compare two golden_reference.json files structurally.
    Returns a dict of differences.
    """
    diff = {"matched_fields": [], "missing_fields": [], "type_mismatches": [],
            "summary": {}}

    orig_fields = {f["name"]: f for f in original.get("fields", [])}
    regen_fields = {f["name"]: f for f in regenerated.get("fields", [])}

    for name, orig_f in orig_fields.items():
        if name not in regen_fields:
            diff["missing_fields"].append(name)
        elif orig_f["inferred_type"] != regen_fields[name]["inferred_type"]:
            diff["type_mismatches"].append({
                "field": name,
                "original_type": orig_f["inferred_type"],
                "regenerated_type": regen_fields[name]["inferred_type"]
            })
        else:
            diff["matched_fields"].append(name)

    diff["summary"] = {
        "total_fields": len(orig_fields),
        "matched": len(diff["matched_fields"]),
        "type_mismatches": len(diff["type_mismatches"]),
        "missing": len(diff["missing_fields"]),
    }
    return diff


def check_manifest_against_quarantine(manifest: dict, quarantined_rows: list) -> dict:
    """
    For every row the manifest predicts should be rejected/warned:
    - Confirm Phase 1's cleanser quarantined it (for missing_field, invalid_format)
    - For negative cases, the cleanser may not catch all of them — that's fine,
      UMP would catch them downstream
    """
    # Cleanser is expected to catch: missing_field, some invalid_format
    expected_quarantined = [
        e for e in manifest["entries"]
        if e["case_type"] in ("missing_field", "invalid_format")
    ]

    quarantined_row_numbers = set(quarantined_rows)
    expected_row_numbers = {e["row"] for e in expected_quarantined}

    matched = expected_row_numbers & quarantined_row_numbers
    missed = expected_row_numbers - quarantined_row_numbers

    return {
        "expected_quarantined": len(expected_quarantined),
        "actually_quarantined": len(matched),
        "missed_by_cleanser": list(missed),
        "match_rate": len(matched) / len(expected_quarantined) if expected_quarantined else 1.0,
    }


@click.command()
@click.option("--custodian", required=True)
def validate(custodian):
    """Run self-consistency validation."""
    click.echo("Self-Consistency Validation")
    click.echo("=" * 50)

    # Step 1: Load original golden ref + manifest
    with open(f"data/gold/{custodian}/golden_reference.json") as f:
        original_golden = json.load(f)
    with open(f"output/{custodian}/manifest.json") as f:
        manifest = json.load(f)

    # Step 2: Re-feed synthetic output through Phase 1
    # (This is wired in once Role A's golden_prep is importable)
    synthetic_path = f"output/{custodian}/synthetic_cash.txt"
    # from golden_prep import ingest_bronze, profile_silver, cleanse_data, finalize_gold
    # ingest_bronze(synthetic_path, f"{custodian}_roundtrip", "transaction")
    # profile_silver(f"{custodian}_roundtrip", "transaction")
    # cleanse_data(f"{custodian}_roundtrip", "transaction")
    # finalize_gold(f"{custodian}_roundtrip", "transaction")

    # Step 3: Load regenerated golden ref
    regenerated_path = f"data/gold/{custodian}_roundtrip/golden_reference.json"
    if not os.path.exists(regenerated_path):
        click.echo("Round-trip not yet wired (waiting on Phase 1 import)", err=True)
        return

    with open(regenerated_path) as f:
        regenerated = json.load(f)

    # Step 4: Compare
    schema_diff = compare_golden_references(original_golden, regenerated)

    # Step 5: Build report
    report = {
        "custodian": custodian,
        "schema_consistency": schema_diff,
        "summary": {
            "schema_match_rate": schema_diff["summary"]["matched"] / schema_diff["summary"]["total_fields"],
        }
    }

    # Step 6: Write VALIDATION_REPORT.json
    with open("VALIDATION_REPORT.json", "w") as f:
        json.dump(report, f, indent=2)

    click.echo(f"Schema match rate: {report['summary']['schema_match_rate']*100:.1f}%")
    click.echo(f"Full report: VALIDATION_REPORT.json")


if __name__ == "__main__":
    validate()
```

This is scaffolded today; you'll wire it fully on Day 5.

### Step 2.4 — Define PSV renderer spec (1 hour)

You're going to implement this on Day 4. Today, write the spec so Role A and Role B both understand what's expected:

`docs/psv_renderer_spec.md`:

```markdown
# PSV Renderer Spec (Role C implements Day 4)

## Function signature
def render_psv(records: list[dict], golden_ref: dict, output_path: str) -> None

## Behavior
1. Read field order from golden_ref["fields"][i]["position"]
2. Map each record dict's keys to golden_ref field names
3. Write pipe-delimited output (delimiter = golden_ref["delimiter"])
4. No header row (per golden_ref["has_header"])
5. Handle missing fields gracefully (from missing_field mutations) → empty string
6. Preserve leading zeros in account numbers (write as strings)
7. Format dates per golden_ref["fields"][i]["format"]
8. Write trailing newline after each row, including last

## Inputs from Role B (record dict — variable-length cash format)
{
  "RECORD_TYPE": "A",
  "ACCT_NUM": "12345678",
  "BRANCH_CODE": "M801",
  "TRADE_DATE": "2026-04-01",
  "SETTLE_DATE": "2026-04-01",
  "QUANTITY": "0.00000",
  "TXN_CD": "WTFEE",
  "AMOUNT": 35.00,
  "DESCRIPTION": "WIRE TRANSFER FEE",
  "TIMESTAMP": "4/1/2026 10:03:05 PM",
  # _txn_code, _variant, _case_type, _expected_outcome → metadata, NOT written
}

## Output (one row per record, variable field count per Stonex cash format)
A|18|312|12345678||1|M801|0|||||||||||2026-04-01||2026-04-01||2026-04-01|||0|0.00000|WTFEE||0|35.00||0|0|0|0|WIRE TRANSFER FEE|||||||||||||0|22298|E||N|N|Y|C|4/1/2026 10:03:05 PM
```

Note: cash records have 45–58 fields with many empty positions between anchor fields. The renderer pads correctly using golden_cash.json's `field_count_range` and `anchor_fields`.

### Step 2.5 — First placeholder integration test (30 min)

`tests/test_integration.py`:

```python
"""End-to-end integration tests across Phase 1 + Phase 2."""
import pytest

@pytest.mark.integration
def test_environment_validation_passes():
    """Sanity: validate-environment CLI returns exit 0."""
    import subprocess
    result = subprocess.run(["python", "cli.py", "validate-environment"],
                          capture_output=True, text=True)
    assert result.returncode == 0, f"Environment check failed: {result.stdout}"

@pytest.mark.integration
def test_cli_help_works():
    """Smoke: CLI loads and shows help."""
    import subprocess
    result = subprocess.run(["python", "cli.py", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "prep" in result.stdout
    assert "generate" in result.stdout
```

```bash
git commit -am "Day 2: pytest infra + validate-environment CLI + self-consistency scaffold + renderer spec"
git push origin feature/integration
```

**End of Day 2 deliverable:** Test infrastructure live · `validate-environment` works · self-consistency scaffolded · PSV renderer spec published.

---

## Day 3 — First End-to-End Smoke Test + Renderer Spec Walkthrough

**Goal:** As soon as Role A delivers golden_reference.json EOD, you run the first end-to-end smoke test using Role B's mock-fed records. Walk Role B through the renderer spec.

**Effort:** 6 hours

### Step 3.1 — Wire CLI command stubs to actual modules (2 hours)

As Role A and Role B push their work, replace the stubs in `cli.py`:

```python
@prep.command("run")
def prep_run(input, custodian, file_type):
    if not os.path.exists(input):
        click.echo(f"ERROR: Input file not found: {input}", err=True)
        sys.exit(1)

    from golden_prep import ingest_bronze, profile_silver, cleanse_data, mask_pii, finalize_gold
    click.echo(f"Phase 1: ingesting {input}...")
    ingest_bronze(input, custodian, file_type)
    click.echo(f"Phase 1: profiling...")
    profile_silver(custodian, file_type)
    click.echo(f"Phase 1: cleansing...")
    cleanse_data(custodian, file_type)
    click.echo(f"Phase 1: masking PII...")
    mask_pii(custodian, file_type)
    click.echo(f"Phase 1: finalizing gold...")
    finalize_gold(custodian, file_type)
    click.echo(f"\nGolden reference: data/gold/{custodian}/golden_reference.json")

@cli.command("generate")
def generate(custodian, seed, case_type, rows):
    golden_path = f"data/gold/{custodian}/golden_reference.json"
    if not os.path.exists(golden_path):
        click.echo(f"ERROR: Golden reference not found.", err=True)
        sys.exit(1)

    from test_data_gen import run_full_generation
    run_full_generation(custodian, seed, case_type, rows)
```

### Step 3.2 — First end-to-end smoke test (2 hours)

The moment Role A's golden_reference.json lands EOD Day 3:

```bash
git fetch --all
git checkout feature/integration
git rebase main  # to get Role A's and Role B's interim work

# Test the chain:
python cli.py prep run --input ./ref_files/Sal_csh.txt --custodian stonex

# Confirm
ls -la data/gold/stonex/golden_reference.json
cat data/gold/stonex/golden_reference.json | python -m json.tool | head -30
```

If Phase 1 works end-to-end, that's a major win. Take a screenshot for the demo.

### Step 3.3 — Walk Role B through the renderer spec (30 min)

Three-way meeting at Day 3 EOD with Role A and Role B:
- Role A walks through `golden_reference.json` structure
- You walk through `psv_renderer_spec.md`
- Role B confirms the record dict shape they'll be producing

Lock the spec. You implement tomorrow.

### Step 3.4 — Commit + sync (15 min)

```bash
git commit -am "Day 3: first end-to-end smoke + CLI wired to Phase 1"
git push origin feature/integration
```

**End of Day 3 deliverable:** Phase 1 runs end-to-end via CLI · renderer spec finalized.

---

## Day 4 — PSV Renderer Implementation + Full CLI Integration

**Goal:** Implement the PSV renderer. Wire the full CLI so `python cli.py generate` produces actual output files.

**Effort:** 7 hours

### Step 4.1 — Implement the PSV renderer (2 hours)

Add to `cli.py` (or a separate module if you prefer):

```python
# psv_renderer.py
"""PSV renderer — converts list of record dicts to pipe-delimited file."""
from typing import List, Dict, Any
import os


def render_psv(records: List[Dict[str, Any]], golden_ref: Dict, output_path: str) -> None:
    """
    Write records to a pipe-delimited file matching the original custodian format.

    Field order is determined by golden_ref["fields"][i]["position"].
    Date fields are formatted per golden_ref["fields"][i].get("format").
    Missing fields (from missing_field mutations) are written as empty string.
    Account numbers preserve leading zeros (always written as strings).
    """
    delimiter = golden_ref.get("delimiter", "|")
    has_header = golden_ref.get("has_header", False)
    fields = sorted(golden_ref["fields"], key=lambda f: f["position"])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        if has_header:
            f.write(delimiter.join(field["name"] for field in fields) + "\n")

        for record in records:
            row = []
            for field in fields:
                name = field["name"]
                value = record.get(name, "")  # missing field -> empty

                # Type-aware formatting
                if value is None or value == "":
                    row.append("")
                elif field["inferred_type"] == "decimal":
                    if isinstance(value, (int, float)):
                        row.append(f"{value:.2f}")
                    else:
                        row.append(str(value))
                elif field["inferred_type"] == "date" and isinstance(value, str):
                    # Already formatted by Role B per golden_ref format
                    row.append(value)
                else:
                    # Strings, integers, account numbers, CUSIPs - write as-is
                    row.append(str(value))

            f.write(delimiter.join(row) + "\n")
```

### Step 4.2 — Update Role B's run_full_generation to call your renderer (30 min)

In your CLI integration:

```python
@cli.command("generate")
def generate(custodian, seed, case_type, rows):
    # ... validation ...

    from test_data_gen import run_full_generation
    # Role B's run_full_generation produces records + manifest;
    # they call your renderer at the end:
    run_full_generation(custodian, seed, case_type, rows)
    # Inside run_full_generation, the call should be:
    #   from psv_renderer import render_psv
    #   render_psv(all_records, golden_ref, output_path)
```

Coordinate with Role B on the import path. They call your function from their orchestrator.

### Step 4.3 — End-to-end test with real Role A + Role B output (2 hours)

```bash
# Phase 1
python cli.py prep run --input ./ref_files/Sal_csh.txt --custodian stonex

# Phase 2
python cli.py generate --custodian stonex --seed 42 --type all

# Inspect outputs
head -10 output/stonex/synthetic_cash.txt
cat output/stonex/manifest.json | python -m json.tool | head -50
```

You should see ~89 rows of pipe-delimited data and a manifest with summary stats.

### Step 4.4 — First real integration tests (2 hours)

`tests/test_integration.py`:

```python
@pytest.mark.integration
def test_full_pipeline_end_to_end(tmp_path, spark, monkeypatch):
    """Phase 1 → Phase 2 → output files exist and look correct."""
    monkeypatch.chdir(tmp_path)

    # Set up a mini cash transaction file (mimics Sal_csh.txt format)
    (tmp_path / "ref_files").mkdir()
    test_input = tmp_path / "ref_files" / "Sal_csh.txt"
    rows = []
    txn_codes = ["WTFEE", "JRL", "STAX", "RDIV", "WRAP", "RPRM", "YRINC"]
    for i in range(50):
        txn = txn_codes[i % len(txn_codes)]
        amt = 35.00 + (i * 1.5)
        rows.append(
            f"A|18|312|{10000000+i:08d}||1|M801|0|||||||||||2026-04-01||2026-04-01||2026-04-01|||0|0.00000|{txn}||0|{amt:.2f}||0|0|0|0|TEST DESC|||||||||||||0|22298|E||N|N|Y|C|4/1/2026 10:03:05 PM"
        )
    test_input.write_text("\n".join(rows) + "\n")

    # Run Phase 1
    from golden_prep import ingest_bronze, profile_silver, cleanse_data, mask_pii, finalize_gold
    ingest_bronze(str(test_input), "test_cust", "cash")
    profile_silver("test_cust", "cash")
    cleanse_data("test_cust", "cash")
    mask_pii("test_cust", "cash")
    finalize_gold("test_cust", "cash")

    assert (tmp_path / "data" / "gold" / "test_cust" / "golden_cash.json").exists()

    # Run Phase 2
    from test_data_gen import run_full_generation
    run_full_generation("test_cust", seed=42, case_type="all", extra_rows=0)

    # Verify outputs
    output_psv = tmp_path / "output" / "test_cust" / "synthetic_cash.txt"
    output_manifest = tmp_path / "output" / "test_cust" / "manifest.json"

    assert output_psv.exists()
    assert output_manifest.exists()

    import json
    with open(output_manifest) as f:
        manifest = json.load(f)

    assert manifest["summary"]["positive"] == 80
    assert manifest["summary"]["total"] >= 80
```

### Step 4.5 — Commit (15 min)

```bash
git commit -am "Day 4: PSV renderer + full CLI integration + first end-to-end test"
git push origin feature/integration
```

**End of Day 4 deliverable:** Full pipeline runs end-to-end via single CLI commands. Real output files generated.

---

## Day 5 — Integration Tests + Self-Consistency Validation + Mid-POC Checkpoint

**Goal:** Comprehensive integration test coverage. Wire self-consistency validation. Demo at mid-POC checkpoint.

**Effort:** 7 hours

### Step 5.1 — Byte-identical reproducibility test (1 hour)

```python
@pytest.mark.integration
def test_two_runs_with_same_seed_byte_identical(tmp_path, monkeypatch):
    """Same seed -> byte-identical output. Foundation of regression testing."""
    import subprocess
    import hashlib

    # Run Phase 1 once
    subprocess.run(["python", "cli.py", "prep", "run",
                   "--input", "./ref_files/Sal_csh.txt",
                   "--custodian", "stonex"], check=True)

    # Run Phase 2 twice with same seed
    subprocess.run(["python", "cli.py", "generate",
                   "--custodian", "stonex", "--seed", "42", "--type", "all"], check=True)
    with open("output/stonex/synthetic_cash.txt", "rb") as f:
        hash1 = hashlib.md5(f.read()).hexdigest()

    subprocess.run(["python", "cli.py", "generate",
                   "--custodian", "stonex", "--seed", "42", "--type", "all"], check=True)
    with open("output/stonex/synthetic_cash.txt", "rb") as f:
        hash2 = hashlib.md5(f.read()).hexdigest()

    assert hash1 == hash2, "Same seed must produce byte-identical files"
```

### Step 5.2 — Wire self-consistency validation fully (2 hours)

Replace the placeholder in `validate_self_consistency.py` with the actual round-trip logic:

```python
@click.command()
@click.option("--custodian", required=True)
def validate(custodian):
    """Run self-consistency validation: round-trip test."""
    click.echo("Self-Consistency Validation")
    click.echo("=" * 50)

    # Step 1: Run Phase 1 + Phase 2 to get baseline
    # (Assume already run; fail gracefully if not)
    if not os.path.exists(f"data/gold/{custodian}/golden_reference.json"):
        click.echo("ERROR: Run Phase 1 + Phase 2 first.", err=True)
        sys.exit(1)

    with open(f"data/gold/{custodian}/golden_reference.json") as f:
        original_golden = json.load(f)
    with open(f"output/{custodian}/manifest.json") as f:
        manifest = json.load(f)

    # Step 2: Re-feed Phase 2's synthetic output through Phase 1
    synthetic_path = f"output/{custodian}/synthetic_cash.txt"
    roundtrip_custodian = f"{custodian}_roundtrip"

    from golden_prep import ingest_bronze, profile_silver, cleanse_data, finalize_gold
    click.echo(f"Re-feeding {synthetic_path} through Phase 1...")
    ingest_bronze(synthetic_path, roundtrip_custodian, "transaction")
    profile_silver(roundtrip_custodian, "transaction")
    cleanse_stats = cleanse_data(roundtrip_custodian, "transaction")
    finalize_gold(roundtrip_custodian, "transaction")

    # Step 3: Compare regenerated golden ref to original
    with open(f"data/gold/{roundtrip_custodian}/golden_reference.json") as f:
        regenerated = json.load(f)

    schema_diff = compare_golden_references(original_golden, regenerated)

    # Step 4: Confirm cleanser caught what it should have
    quarantine_check = check_manifest_against_quarantine(manifest, cleanse_stats.get("quarantined_rows", []))

    # Step 5: Build full report
    report = {
        "custodian": custodian,
        "schema_consistency": schema_diff,
        "cleanser_check": quarantine_check,
        "summary": {
            "schema_match_rate": schema_diff["summary"]["matched"] / schema_diff["summary"]["total_fields"],
            "cleanser_match_rate": quarantine_check["match_rate"],
        }
    }

    with open("VALIDATION_REPORT.json", "w") as f:
        json.dump(report, f, indent=2)

    click.echo(f"\nResults:")
    click.echo(f"  Schema match rate:    {report['summary']['schema_match_rate']*100:.1f}%")
    click.echo(f"  Cleanser match rate:  {report['summary']['cleanser_match_rate']*100:.1f}%")
    click.echo(f"\nFull report: VALIDATION_REPORT.json")
```

### Step 5.3 — Run validation, generate first report (1 hour)

```bash
python cli.py prep run --input ./ref_files/Sal_csh.txt --custodian stonex
python cli.py generate --custodian stonex --seed 42 --type all
python cli.py validate-self-consistency --custodian stonex
cat VALIDATION_REPORT.json | python -m json.tool
```

### Step 5.4 — Mid-POC stakeholder checkpoint (60 min)

You walk through:
1. CLI tour (`python cli.py --help`, then each subcommand briefly)
2. Live end-to-end run (Phase 1 → Phase 2)
3. Show the generated outputs
4. Show the validation report

Role A walks Phase 1 details; Role B walks Phase 2 details. You're the integrator.

### Step 5.5 — Commit (15 min)

```bash
git commit -am "Day 5: byte-identical test + self-consistency wired + checkpoint"
git push origin feature/integration
```

**End of Day 5 deliverable:** Full integration test suite running · self-consistency validation working · mid-POC checkpoint passed.

---

## Day 6 — DEPLOYMENT_GUIDE.md (HEAVIEST DAY)

**Goal:** Write the runbook that makes plug-and-play real. Test it by simulating a fresh-machine install.

**Effort:** 8 hours

### Step 6.1 — Self-consistency mismatch triage (1 hour)

Three-way meeting with Role A and Role B looking at `VALIDATION_REPORT.json`. For each mismatch:
- Phase 1 issue → Role A fixes
- Phase 2 issue → Role B fixes
- Integration/contract issue → you fix
- Expected difference (acceptable) → document in DEPLOYMENT_GUIDE

Re-run validation until results are clean (or known-acceptable).

### Step 6.2 — Write DEPLOYMENT_GUIDE.md (5 hours)

This is the most important document of the POC. Treat it as your primary deliverable today.

```markdown
# Envestnet UMP — Synthetic Test Data Generator

## Deployment Guide

### Audience
Envestnet engineering team or deployment partner installing the tool inside the
Envestnet environment for production use against the real Stonex Financial
Transaction file (and future custodian onboardings).

### Prerequisites (one-time, per machine)

1. **Python 3.12 or higher**
   - Check: `python3 --version`
   - Install: see python.org

2. **Java JDK 17 (required by PySpark 3.5)**
   - Check: `java -version`
   - Install (Linux): `apt install openjdk-17-jdk`
   - Install (macOS): `brew install openjdk@17`

3. **System resources**
   - Minimum 16 GB RAM (PySpark)
   - 5 GB free disk for working data

### Installation

```bash
# 1. Clone or unpack the package
cd /opt   # or wherever Envestnet preferred install location
unzip envestnet-sdg-v0.1.0.zip
cd envestnet-sdg

# 2. Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies (offline if needed — wheels included in /vendor)
pip install -r requirements.txt
# OR for offline: pip install --no-index --find-links=./vendor -r requirements.txt

# 4. Validate environment
python cli.py validate-environment
# Expected output: "ALL N CHECKS PASSED — ready to run."
```

If `validate-environment` reports failures, fix them before proceeding. Common
issues are listed in section "Troubleshooting."

### First Run — Onboarding Stonex Financial with Real Data

```bash
# 1. Place the real Stonex Financial Transaction file in ref_files/
cp /path/to/real_Sal_csh.txt ref_files/Sal_csh.txt

# 2. Run Phase 1 (Golden Data Preparation)
python cli.py prep run \
    --input ./ref_files/Sal_csh.txt \
    --custodian stonex

# Output: data/gold/stonex/golden_reference.json
# Inspect this file — it should reflect the schema of your real data
cat data/gold/stonex/golden_reference.json | python -m json.tool | less

# 3. Generate test data
python cli.py generate \
    --custodian stonex \
    --seed 42 \
    --type all

# Output:
#   output/stonex/synthetic_cash.txt   (PSV file for UMP intake)
#   output/stonex/manifest.json               (expected outcome per row)
```

### What to Expect on First Run

When pointed at the real Stonex Financial file, Phase 1's profiler may detect new
patterns not seen during POC development. Things to watch for:

| Observation | Likely Cause | Action |
|---|---|---|
| New TXN_CD value detected | Real data has codes outside our POC list | Inspect `data/silver/stonex/cash/profile.json` and confirm with Thillai |
| Account number format differs | Real format may include hyphens or letters | Check the cleanser stripping rules |
| Date format outside YYYYMMDD/YYYY-MM-DD | Real data uses different format | Extend date detection in profiler (configs/profiler_rules.json future work) |
| Decimal precision higher than expected | Real prices use 4 dp, our POC defaulted to 2 | Already handled — no action needed |
| Profiler hangs on large files | File size > 1M rows triggers slow path | Already mitigated via sampling — should complete |

### Configuration Files

The tool can be tuned without code changes via these files:

| File | What it controls |
|---|---|
| `configs/rules/coverage-matrix.json` | Which (txn_code × security_type) combinations to generate |
| `configs/golden_reference_schema.md` | The contract between Phase 1 and Phase 2 |

To add a new custodian (e.g., Bank of New York Mellon):
```bash
python cli.py prep run --input ./ref_files/bnym_transaction.txt --custodian bnym
python cli.py generate --custodian bnym --seed 42 --type all
```
No code changes required.

### Validating Output

After generating synthetic data, validate it before submitting to UMP:

```bash
# Self-consistency check — round-trip test
python cli.py validate-self-consistency --custodian stonex

# Inspect the report
cat VALIDATION_REPORT.json | python -m json.tool
```

A schema match rate of >= 95% indicates the synthetic data is structurally
consistent with the real reference file.

### Submitting to UMP

The generated `synthetic_cash.txt` is in the same PSV format as production
custodian files. Submit it via your standard UMP intake process. Then compare the
UMP outcomes to the predictions in `manifest.json`:

```bash
# Match expected vs actual UMP outcomes
python cli.py validate-against-ump \
    --manifest output/stonex/manifest.json \
    --ump-report /path/to/ump_processing_report.txt
```

### Reproducibility

Same seed = byte-identical output. To prove this in your environment:
```bash
python cli.py generate --custodian stonex --seed 42 --type all
md5sum output/stonex/synthetic_cash.txt
# > xxxxxxxxxxxxxxx

python cli.py generate --custodian stonex --seed 42 --type all
md5sum output/stonex/synthetic_cash.txt
# > xxxxxxxxxxxxxxx  (same)
```

For new test scenarios, use a different seed (e.g., `--seed 100`).

### Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `validate-environment` fails on Java | JDK not installed or wrong version | Install JDK 17 (not JRE) |
| `validate-environment` fails on PySpark | JAVA_HOME not set | `export JAVA_HOME=$(...)` |
| Phase 1 hangs on large file | Large file, full Spark scan | Wait — sampling activates for >1M rows |
| Generator produces 0 rows | Coverage matrix file missing | Restore `configs/rules/coverage-matrix.json` |
| Validation match rate < 90% | Real data significantly different from POC assumptions | Inspect profile.json, escalate to Nous |

### Support

- Configuration questions → `configs/` folder is self-documenting
- Tool bugs → escalate to Nous QA & Test Automation team
- UMP-specific rules questions → Thillai (Envestnet)

### Version
v0.1.0-poc — Built by Nous Infosystems QA & Test Automation Practice
```

### Step 6.3 — Fresh-machine install simulation (1.5 hours)

The acid test: pretend you're an Envestnet engineer who's never seen this tool. Wipe a folder, follow your own DEPLOYMENT_GUIDE step by step. Note every place you have to deviate or where the guide is unclear. Fix the guide.

```bash
# Simulate fresh install
mkdir -p /tmp/envestnet-deploy-test
cd /tmp/envestnet-deploy-test
# Copy package over (or git clone)
# Now follow DEPLOYMENT_GUIDE.md step by step from the top
# Note every friction point
```

Iterate the guide until a fresh install works without surprises.

```bash
git commit -am "Day 6: DEPLOYMENT_GUIDE.md complete + tested via fresh install simulation"
git push origin feature/integration
```

**End of Day 6 deliverable:** DEPLOYMENT_GUIDE.md tested and complete. Plug-and-play promise is real.

---

## Day 7 — README + Demo Rehearsal + Delivery

**Goal:** Final integration polish. Run the demo.

**Effort:** 5 hours

### Step 7.1 — Master README assembly (1.5 hours)

Stitch together Role A's, Role B's, and your sections into a coherent `README.md`:

```markdown
# Envestnet UMP — Synthetic Test Data Generator

## Overview
[1-paragraph elevator pitch]

## Quick Start
[The 3 commands that get you to value: install, prep, generate]

## Architecture
[Brief diagram: Phase 1 → golden_reference.json → Phase 2 → synthetic data + manifest]

## Phase 1: Golden Data Preparation
[Role A's section]

## Phase 2: Test Data Generation
[Role B's section]

## Integration & Validation
[Your section]

## Deployment to Production
See DEPLOYMENT_GUIDE.md

## Development
- Tests: `pytest`
- Coverage: `pytest --cov=. --cov-report=html`
- Linting: [if any]

## Authors
Nous Infosystems QA & Test Automation Practice
```

### Step 7.2 — Demo flow scripting (1 hour)

The 5-minute demo script. Type up timing:

```
00:00-00:30  Show the synthetic reference file (Role A talks)
00:30-01:30  Run Phase 1 live (Role A drives, Role C narrates if PySpark slow)
01:30-02:30  Run Phase 2 live (Role B drives)
02:30-03:00  Run twice with same seed, diff outputs (Role C drives)
03:00-03:30  Show validation report (Role C)
03:30-04:30  Walk through DEPLOYMENT_GUIDE.md briefly (Role C)
04:30-05:00  Q&A
```

You're the timekeeper. Have the commands pre-cached in your shell history.

### Step 7.3 — Demo rehearsal (60 min)

Twice through, all three of you. Time it. Identify any rough patches.

### Step 7.4 — Final cleanup (30 min)

```bash
# Remove debug prints, .DS_Store files, etc.
# Confirm requirements.txt is exact
# Make sure all CLI commands have help text
python cli.py --help | head -20
```

### Step 7.5 — Demo delivery + handover (30 min)

Live with stakeholders. Stay calm.

After demo, finalize merges:

```bash
# Open PR feature/integration -> main
# Role A and Role B review
# Once approved:
git commit -am "Day 7: final demo polish"
git push origin feature/integration

# After PR merged:
git checkout main
git pull
git tag v0.1.0-poc
git push --tags
```

**End of Day 7 deliverable:** All branches merged · v0.1.0-poc tagged · demo delivered · handover documents complete.

---

## Daily Discipline

- **Standup (10 min):** Shipped · Doing · Blockers
- **EOD sync (10 min):** Demo what works · Tomorrow's plan
- **Stuck for 1 hour?** Ask. Don't burn 4 hours.
- **Don't be a bottleneck.** Your role is to enable A and B, not gate them.

---

## Common Pitfalls

| Pitfall | Prevention |
|---|---|
| Stub commands in cli.py never get replaced | Track which stubs are stubbed. Replace as A and B push their work. |
| Renderer spec drifts from Role B's record dict shape | Lock the spec on Day 2 with a code example. Confirm Day 3 EOD walkthrough. |
| DEPLOYMENT_GUIDE.md is written but never tested | Day 6 fresh-machine install simulation is non-negotiable. |
| `validate-environment` doesn't catch real install issues | Test against a Linux box without JDK at least once. |
| Self-consistency report has confusing language | "Match rate" must be defined explicitly. Numbers without units are useless. |
| Editing Role A's or Role B's primary files | Never. Open an issue. Add a TODO comment in your file referring to the issue. |
| Skipping the JSON contract sync | Your role depends on it more than theirs — you're the integrator. Be there. |
| Not knowing what Role A and Role B are producing | Re-read their playbooks at the start of each day. |

---

## Your North Star

By Day 7, demo:

1. A working CLI that runs Phase 1 + Phase 2 with two commands
2. A `validate-environment` command that confirms the tool is installed correctly
3. A `validate-self-consistency` command that proves the round-trip works
4. A `DEPLOYMENT_GUIDE.md` so clear an Envestnet engineer can install the tool unsupervised
5. End-to-end integration tests proving the system works
6. Byte-identical output proven via hash test

You are the third leg of the stool. The 7-day plan only fits because you exist. Make every day count.

— *Nous Infosystems · Test Architecture Team*
