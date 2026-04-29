# Golden Reference Schema — Stonex SDG POC

**Document Type:** JSON Contract  
**Audience:** Role A (Pipeline Owner) · Role B (Generator Owner) · Role C (Integration Owner)  
**Date:** 2026-04-29  
**Status:** AGREED (All three roles)

---

## 1. Field Naming & Type Vocabulary

### 1.1 Naming Convention

All field names in golden references and synthetic output use **`UPPERCASE_SNAKE_CASE`**.

Examples: `RECORD_TYPE`, `ACCT_NUM`, `TRADE_DATE`, `TXN_CD`, `CUSIP`, `PROCESS_DATE`

### 1.2 Type Vocabulary

The following types are used in field definitions:

| Type | Description | Format | Example | Notes |
|------|---|---|---|---|
| `account_number` | Stonex account ID | Numeric, 8 digits | `48849458` | Fixed format, no leading zeros stripped |
| `cusip` | Securities identifier | 9 alphanumeric chars | `316146109` | Includes check digit; validate via mod-10 |
| `date` | Calendar date | `YYYY-MM-DD` | `2026-04-01` | ISO 8601 format |
| `timestamp` | Date + time | `M/D/YYYY h:mm:ss A` | `4/1/2026 10:03:05 PM` | Stonex format; A/PM, no leading zeros on month/day |
| `decimal` | Numeric with fractional part | Decimal string | `35.00` or `493.0000` | Varies by field; strip trailing zeros in manifest |
| `integer` | Whole number | Numeric string | `18` or `2903` | No decimals |
| `enum` | Fixed set of values | Pipe-separated list | `WTFEE\|JRL\|STAX\|RDIV\|WRAP\|RPRM\|YRINC` | See specific field docs |
| `string` | Free-form text | UTF-8 text | `WIRE TRANSFER FEE` | May contain leading spaces; preserve them |
| `code` | Alphanumeric code | 2–8 characters | `M801`, `FR01`, `MP85` | Branch codes, record type codes |

---

## 2. JSON Golden Reference Schema

### 2.1 Top-Level Contract

Every golden reference (golden_cash.json, golden_account.json, etc.) follows this envelope:

```json
{
  "custodian_id": "stonex",
  "file_type": "CASH_TRANSACTION | ACCOUNT_MASTER | POSITION | REINVESTED_ACTIVITY",
  "source_filename": "Sal_csh.txt | sal_act.txt | Sal_pos.txt | sal_rad.txt",
  "delimiter": "|",
  "record_format": "single_line | multi_line_dashed | multi_line_blank",
  "has_header": false,
  "field_count_range": [45, 58],
  "generated_at": "ISO 8601 timestamp",
  "source_record_count": 22,
  "anchor_fields": [...],
  "fields": [...]
}
```

### 2.2 Anchor Fields

Anchor fields describe which fields are stable (always present, predictable position) vs. detected by pattern.

For **single-line files**, anchor fields use array index:

```json
"anchor_fields": [
  {
    "position": 0,
    "name": "RECORD_TYPE",
    "stable": true,
    "always_value": "A",
    "description": "Always 'A' for cash transaction records"
  },
  {
    "position": 3,
    "name": "ACCT_NUM",
    "stable": true,
    "type": "account_number",
    "description": "8-digit Stonex account ID"
  },
  {
    "name": "TXN_CD",
    "stable": false,
    "detection": "pattern",
    "detection_rule": "first_uppercase_token_3_to_5_chars_after_amount_block",
    "type": "enum",
    "description": "Transaction code; position varies based on optional fields"
  }
]
```

For **multi-line files**, anchor fields reference logical (post-join) positions:

```json
"anchor_fields": [
  {
    "logical_position": 0,
    "name": "RECORD_TYPE",
    "stable": true,
    "always_value": "C",
    "physical_line": 1,
    "physical_position": 0,
    "description": "Record type on first physical line"
  }
]
```

### 2.3 Field Definitions

Each field in the golden reference has:

```json
{
  "name": "FIELD_NAME",
  "inferred_type": "string | integer | decimal | date | timestamp | account_number | cusip | enum | code",
  "required": true,
  "description": "What this field represents",
  
  // Type-specific constraints
  "min_length": 8,
  "max_length": 8,
  "pattern": "^\\d{8}$",
  "min": 0,
  "max": 100000,
  "allows_negative": true,
  "negative_allowed_for": ["YRINC", "JRL"],
  "allowed_values": ["WTFEE", "JRL", "STAX", "RDIV", "WRAP", "RPRM", "YRINC"],
  
  // Conditional requirements
  "required_for": ["STAX", "RDIV"],
  "optional_when": "TXN_CD not in ['STAX', 'RDIV']",
  "default": "0.00000",
  "sample_values": ["M801", "MP85", "FR01", "5U01"],
  
  // Metadata for Phase 2 generation
  "distribution": "uniform",
  "range": [25.00, 50.00],
  "format": "YYYY-MM-DD"
}
```

---

## 3. Cash Transaction File (Sal_csh.txt)

**File Type:** `CASH_TRANSACTION`  
**Format:** Single-line, variable-length  
**Record Count (sample):** 22  
**Fields per Record:** 45–58 (variable)

### 3.1 Golden Cash JSON Template

```json
{
  "custodian_id": "stonex",
  "file_type": "CASH_TRANSACTION",
  "source_filename": "Sal_csh.txt",
  "delimiter": "|",
  "record_format": "single_line",
  "has_header": false,
  "field_count_range": [45, 58],
  "generated_at": "2026-04-29T10:00:00Z",
  "source_record_count": 22,
  
  "anchor_fields": [
    {
      "position": 0,
      "name": "RECORD_TYPE",
      "stable": true,
      "always_value": "A"
    },
    {
      "position": 3,
      "name": "ACCT_NUM",
      "stable": true
    },
    {
      "name": "TXN_CD",
      "stable": false,
      "detection": "pattern"
    },
    {
      "position": -1,
      "name": "TIMESTAMP",
      "stable": true
    }
  ],
  
  "fields": [
    {
      "position": 0,
      "name": "RECORD_TYPE",
      "inferred_type": "enum",
      "required": true,
      "allowed_values": ["A"],
      "description": "Always 'A' for cash transaction records"
    },
    {
      "position": 3,
      "name": "ACCT_NUM",
      "inferred_type": "account_number",
      "required": true,
      "pattern": "\\d{8}",
      "min_length": 8,
      "max_length": 8,
      "description": "8-digit Stonex account identifier"
    },
    {
      "position": 6,
      "name": "BRANCH_CODE",
      "inferred_type": "code",
      "required": false,
      "sample_values": ["M801", "MP85", "FR01", "5U01", "6602", "N105", "MA38"],
      "description": "Stonex branch/routing code"
    },
    {
      "position": 14,
      "name": "TRADE_DATE",
      "inferred_type": "date",
      "required": true,
      "format": "YYYY-MM-DD",
      "description": "Transaction date"
    },
    {
      "position": 16,
      "name": "SETTLE_DATE",
      "inferred_type": "date",
      "required": false,
      "format": "YYYY-MM-DD",
      "description": "Settlement date (same-day or T+1/T+2)"
    },
    {
      "position": 22,
      "name": "QUANTITY",
      "inferred_type": "decimal",
      "required": true,
      "default": "0.00000",
      "description": "Always 0 for cash transactions"
    },
    {
      "name": "TXN_CD",
      "inferred_type": "enum",
      "required": true,
      "allowed_values": ["WTFEE", "JRL", "STAX", "RDIV", "WRAP", "RPRM", "YRINC"],
      "description": "Transaction code; position varies by record length"
    },
    {
      "name": "AMOUNT",
      "inferred_type": "decimal",
      "required": true,
      "min": -10000.00,
      "max": 100000.00,
      "allows_negative": true,
      "negative_allowed_for": ["YRINC", "JRL"],
      "description": "Transaction amount; may be negative for certain txn types"
    },
    {
      "name": "CUSIP",
      "inferred_type": "cusip",
      "required": false,
      "required_for": ["STAX", "RDIV"],
      "min_length": 9,
      "max_length": 9,
      "description": "9-char security identifier (when txn involves securities)"
    },
    {
      "name": "DESCRIPTION",
      "inferred_type": "string",
      "required": false,
      "max_length": 80,
      "description": "Human-readable transaction description"
    },
    {
      "position": -1,
      "name": "TIMESTAMP",
      "inferred_type": "timestamp",
      "required": true,
      "format": "M/D/YYYY h:mm:ss A",
      "description": "Record timestamp (last field)"
    }
  ]
}
```

---

## 4. Position File (Sal_pos.txt)

**File Type:** `POSITION`  
**Format:** Single-line, fixed-width  
**Record Count (sample):** 17  
**Fields per Record:** 39 (fixed)

### 4.1 Golden Position JSON Template (Abbreviated)

```json
{
  "custodian_id": "stonex",
  "file_type": "POSITION",
  "source_filename": "Sal_pos.txt",
  "delimiter": "|",
  "record_format": "single_line",
  "has_header": false,
  "field_count_range": [39, 39],
  "generated_at": "2026-04-29T10:00:00Z",
  "source_record_count": 17,
  
  "anchor_fields": [
    {"position": 0, "name": "RECORD_TYPE", "stable": true},
    {"position": 3, "name": "SECURITY_ID", "stable": true},
    {"position": 12, "name": "TRADE_DATE", "stable": true},
    {"position": -1, "name": "TIMESTAMP", "stable": true}
  ],
  
  "fields": [
    {"position": 0, "name": "RECORD_TYPE", "inferred_type": "enum", "allowed_values": ["A"]},
    {"position": 3, "name": "SECURITY_ID", "inferred_type": "integer", "required": true},
    {"position": 12, "name": "TRADE_DATE", "inferred_type": "date", "format": "YYYY-MM-DD"},
    {"position": 13, "name": "SETTLE_DATE", "inferred_type": "date", "format": "YYYY-MM-DD"},
    {"position": 16, "name": "TYPE_INDICATOR", "inferred_type": "enum", "allowed_values": ["R", "C"], "description": "Receive (R) or Cancel (C)"},
    {"position": 22, "name": "QUANTITY", "inferred_type": "decimal", "min": 0},
    {"position": 30, "name": "UNIT_PRICE", "inferred_type": "decimal", "min": 0},
    {"position": -1, "name": "TIMESTAMP", "inferred_type": "timestamp", "format": "M/D/YYYY h:mm:ss A"}
  ]
}
```

---

## 5. Account Master File (sal_act.txt)

**File Type:** `ACCOUNT_MASTER`  
**Format:** Multi-line with dashed separators  
**Record Count (sample):** 56 (14 logical, 4 physical lines each)  
**Fields per Logical Record:** ~100+ (variable)

### 5.1 Golden Account JSON Template (Abbreviated)

```json
{
  "custodian_id": "stonex",
  "file_type": "ACCOUNT_MASTER",
  "source_filename": "sal_act.txt",
  "delimiter": "|",
  "record_format": "multi_line_dashed",
  "has_header": false,
  "field_count_range": [100, 150],
  "generated_at": "2026-04-29T10:00:00Z",
  "source_record_count": 14,
  
  "multiline_config": {
    "separator_pattern": "^-{20,}$",
    "lines_per_record": "varies",
    "physical_lines": 4
  },
  
  "anchor_fields": [
    {"logical_position": 0, "name": "RECORD_TYPE", "stable": true, "always_value": "C"},
    {"logical_position": 1, "name": "ACCT_NUM", "stable": true},
    {"logical_position": 9, "name": "ACCOUNT_NAME", "stable": true},
    {"logical_position": -1, "name": "TIMESTAMP", "stable": true}
  ],
  
  "fields": [
    {"name": "RECORD_TYPE", "inferred_type": "enum", "allowed_values": ["C"]},
    {"name": "ACCT_NUM", "inferred_type": "account_number"},
    {"name": "ACCOUNT_NAME", "inferred_type": "string", "max_length": 80},
    {"name": "ACCOUNT_ADDRESS_LINE1", "inferred_type": "string"},
    {"name": "CITY", "inferred_type": "string"},
    {"name": "STATE", "inferred_type": "code", "pattern": "[A-Z]{2}"},
    {"name": "TIMESTAMP", "inferred_type": "timestamp", "format": "M/D/YYYY h:mm:ss A"}
  ]
}
```

---

## 6. Reinvested Activity File (sal_rad.txt)

**File Type:** `REINVESTED_ACTIVITY`  
**Format:** Multi-line with blank-line separators  
**Record Count (sample):** 34 (17 logical, 2 physical lines each)  
**Fields per Logical Record:** ~29

### 6.1 Golden RAD JSON Template (Abbreviated)

```json
{
  "custodian_id": "stonex",
  "file_type": "REINVESTED_ACTIVITY",
  "source_filename": "sal_rad.txt",
  "delimiter": "|",
  "record_format": "multi_line_blank",
  "has_header": false,
  "field_count_range": [25, 35],
  "generated_at": "2026-04-29T10:00:00Z",
  "source_record_count": 17,
  
  "multiline_config": {
    "separator_pattern": "blank_line",
    "lines_per_record": 2
  },
  
  "anchor_fields": [
    {"logical_position": 0, "name": "RECORD_TYPE", "stable": true, "always_value": "A"},
    {"logical_position": 1, "name": "ACCT_NUM", "stable": true},
    {"logical_position": 7, "name": "CUSIP", "stable": true},
    {"logical_position": -1, "name": "TIMESTAMP", "stable": true}
  ],
  
  "fields": [
    {"name": "RECORD_TYPE", "inferred_type": "enum", "allowed_values": ["A"]},
    {"name": "ACCT_NUM", "inferred_type": "account_number"},
    {"name": "CUSIP", "inferred_type": "cusip", "required": true},
    {"name": "FUND_TICKER", "inferred_type": "code", "sample_values": ["FBNDX", "FSTGX", "FTBFX"]},
    {"name": "FUND_NAME", "inferred_type": "string"},
    {"name": "REINVEST_AMOUNT", "inferred_type": "decimal"},
    {"name": "TXN_CD", "inferred_type": "enum", "allowed_values": ["RDIV", "YRINC"]},
    {"name": "TIMESTAMP", "inferred_type": "timestamp", "format": "M/D/YYYY h:mm:ss A"}
  ]
}
```

---

## 7. Key Decisions & Rationale

### 7.1 Which File is Phase 2 Input?

**Answer: `golden_cash.json`**

- Most complex file (variable-length records, 7 transaction types, multiple mutations)
- Proves end-to-end coverage on hardest format
- Unblocks Role B earliest (delivered EOD Day 2 sub-milestone)
- Account, Position, RAD files are profiled-only this POC; Phase 2 generation extends post-delivery

### 7.2 Anchor Field Strategy

For variable-length files (cash), anchor fields identify which positions are stable:
- **Position 0:** Always present (RECORD_TYPE)
- **Position 3:** Always present (ACCT_NUM)
- **Last field:** Always present (TIMESTAMP)
- **TXN_CD:** Detected by pattern, not position

Role C will use anchor fields to validate file structure during round-trip testing.

### 7.3 Multi-line Handling

All multi-line records are joined into a **single logical record** by Role A before profiling:
- **sal_act.txt (dashed):** 4 physical lines → 1 logical record; fields concatenated with `|`
- **sal_rad.txt (blank):** 2 physical lines → 1 logical record; fields concatenated with `|`

This allows downstream tools to treat all formats uniformly.

### 7.4 Type Validation for Phase 2

Role B will validate generated data against these type constraints:
- **account_number:** 8 digits, no non-digits
- **cusip:** 9 alphanumeric, valid mod-10 check digit
- **date:** `YYYY-MM-DD`, valid calendar date
- **timestamp:** `M/D/YYYY h:mm:ss A`, valid time
- **decimal:** parseable as float
- **enum:** value in `allowed_values` list
- **negative amounts:** only for txn types in `negative_allowed_for`

---

## 8. Implementation Checklist

- [ ] Role A produces `data/gold/stonex/golden_cash.json` by EOD Day 2 (sub-milestone)
- [ ] Role A produces `data/gold/stonex/golden_account.json`, `golden_position.json`, `golden_rad.json` by EOD Day 3
- [ ] Role B consumes `golden_cash.json`, validates all type constraints
- [ ] Role C loads all golden references, validates structure against this schema
- [ ] All three roles document deviations or extensions to this contract in PR comments

---

## 9. Amendment Process

If any field definition needs to change:

1. Open an issue with title: `[SCHEMA] <field_name> change`
2. Propose the change with justification
3. All three roles review and agree
4. Update this document
5. Tag the commit `SCHEMA_AMENDMENT_v2` (increment version)

No role modifies golden references in place without amending this schema first.

---

**Agreed by:**
- [ ] Role A — Pipeline Owner (Anushapd)
- [ ] Role B — Generator Owner
- [ ] Role C — Integration Owner

**Date Agreed:** 2026-04-29  
**Version:** 1.0
