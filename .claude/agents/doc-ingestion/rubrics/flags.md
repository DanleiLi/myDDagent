# Flag Rubric

Reference for the doc-ingestion agent. Defines the flag schema, lifecycle, and trigger conditions. Update this file when DD requirements change — the agent reads it; no agent edit required.

## Flag shape

```json
{
  "type": "MISSING | INCONSISTENCY | BREACH | LOW_CONFIDENCE | STALE_DATA | WARNING | INFO",
  "severity": "CRITICAL | HIGH | MEDIUM | LOW",
  "dataset": "<dataset filename, e.g. modelportfolio.json>",
  "dimension": "<schema section, e.g. asset_allocation, investment_manager, fees, holdings, documentation>",
  "field": "<specific field name, or null>",
  "note": "<plain English description>",
  "status": "open | resolved",
  "first_seen": "YYYY-MM-DD",
  "last_checked": "YYYY-MM-DD",
  "resolved_at": "YYYY-MM-DD or null"
}
```

`status`, `first_seen`, `last_checked`, `resolved_at` are lifecycle fields appended by the agent. They extend `modelportfolio.schema.json`'s flag definition (which is `additionalProperties: false`); the schema should be updated to permit them, but writing them is the source of truth.

## Lifecycle contract — apply on every run

For each existing flag in each dataset, before appending new flags:

1. **Re-evaluate the underlying condition** against the current dataset state.
2. If the condition is now satisfied → set `status: "resolved"`, set `resolved_at: today`, keep the record (audit trail). Never delete.
3. If the condition still holds → set `last_checked: today`, leave `status: "open"`.
4. If a brand-new condition appears that has no matching open flag → append a new record with `status: "open"`, `first_seen: today`, `last_checked: today`, `resolved_at: null`.

Match flags by the tuple `(type, dataset, dimension, field)` when deciding whether a condition is "the same" flag.

## Run-summary output

In Step 8 the agent reports per dataset:

```
DATASET: <filename>
  opened this run:    N
  still open:         N
  resolved this run:  N
```

Followed by the full open-flag list (most severe first).

## Trigger table

| Condition | type | severity | dimension hint |
|---|---|---|---|
| Required field is null | MISSING | HIGH | (use schema section) |
| Same field conflicts across documents | INCONSISTENCY | HIGH | (use schema section) |
| Asset weights don't sum to 100% (±0.1) | BREACH | CRITICAL | asset_allocation |
| Portfolio fee component > 50 bps (0.50% p.a.) | BREACH | LOW | fees |
| Malformed ABN / AFSL / APIR / ARSN / ISIN | BREACH | CRITICAL | (use schema section) |
| Extracted but low confidence (OCR / ambiguous source) | LOW_CONFIDENCE | MEDIUM | (use schema section) |
| Holdings or fee data > 12 months old | STALE_DATA | MEDIUM | (use schema section) |
| Performance history covers < 2 years | MISSING | HIGH | performance |
| Single holding weight > 15% | BREACH | MEDIUM | asset_allocation |
| Back-test or liquidity test absent | MISSING | HIGH | documentation |
| Disclosure text exceeds `max_words` from schema | BREACH | LOW | disclosure |
| FUM recorded without `as_at` date | MISSING | LOW | strategy |
| Holding identifier present but not yet verified against external registry | LOW_CONFIDENCE | HIGH | holdings |
| Holding fund name does not match verified name | INCONSISTENCY | HIGH | holdings |

## Special flag: `unverified_holdings`

When `holdingfee.json` is written, do NOT do per-holding web search. Instead, emit ONE flag:

```json
{
  "type": "LOW_CONFIDENCE",
  "severity": "HIGH",
  "dataset": "holdingfee.json",
  "dimension": "holdings",
  "field": "unit_id",
  "note": "Unverified holdings (N): APIR1, APIR2, ... — run /fee-analysis to resolve names + PDS fees",
  "status": "open",
  "first_seen": "<today>",
  "last_checked": "<today>",
  "resolved_at": null
}
```

The downstream `fee-analysis` skill consumes this list and resolves identifiers. Mark the flag `resolved` once every listed identifier has a verified `unit_name` and `pds_link`.

## Severity to colour mapping (modelportfolio only)

`modelportfolio.schema.json` permits `severity` values `green | amber | red | LOW | MEDIUM | HIGH | CRITICAL`. Use the uppercase form. The colour-coded form is reserved for human dashboards.
