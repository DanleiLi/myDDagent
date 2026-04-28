# Completeness Rubric

Reference for the doc-ingestion agent. Update this file when DD reporting requirements change.

## Two metrics per dataset

For every dataset written in Step 5, report both:

- **Required completeness** = (populated required fields) / (total required fields) × 100
  Required fields are the ones the schema marks as such. Use this metric to gate progression to the next workflow stage (`intake → document_review → due_diligence → ...`).
- **Overall completeness** = (populated fields) / (total fields) × 100
  Includes optional fields. Use this for tracking enrichment progress over time.

A field is "populated" when its value is non-null, non-empty-string, and (for arrays/objects) non-empty.

## How to identify required fields per schema style

The four schemas use two formats — handle both:

| Schema | Format | How to find required fields |
|---|---|---|
| `modelportfolio.schema.json` | Strict draft-07 JSON Schema | Read each `required: [...]` array. For nested objects, walk down `properties.<name>.required` recursively. For array items, read `items.required`. |
| `IM.schema.json`, `portfoliofee.schema.json`, `holdingfee.schema.json` | Custom inline format | A field is required when its leaf node has `"required": true`. Walk every leaf object in the document. |

## Section breakdown

Group the required and overall counts by the schema's top-level sections:

- **modelportfolio.json** sections: `metadata`, `onboarding`, `profile`, `benchmark`, `asset_allocation`, `underlying_holdings`, `investment_manager`, `documents`, `dd_outcome`. (Flags excluded — they're a quality artefact, not a data section.)
- **IM.json** sections: `identity`, `contact`, `corporate_structure`, `disclosure`, `strategy`.
- **portfoliofee.json** sections: per portfolio record — `fees` (the only section). Roll up across all portfolios.
- **holdingfee.json** sections: per holding record — `fees`, `pds_link`. Roll up across all holdings.

For datasets with arrays of records (every dataset except IM if it stays single-tenant), aggregate counts across records: total required = (records) × (required fields per record) + top-level required.

## Output format

One table per dataset, in this exact format:

```
DATASET: <filename>
SECTION              | REQUIRED (filled / total) | OVERALL (filled / total)
─────────────────────┼───────────────────────────┼──────────────────────────
<section>            |   N / N  (XX%)            |   N / N  (XX%)
<section>            |   N / N  (XX%)            |   N / N  (XX%)
─────────────────────┼───────────────────────────┼──────────────────────────
TOTAL                |   N / N  (XX%)            |   N / N  (XX%)
```

Then a one-line summary per dataset:

```
modelportfolio.json    REQUIRED 87%  OVERALL 71%   (gate: due_diligence ✓ if REQUIRED ≥ 80%)
```

## Gates (informational; the agent reports, the user decides)

- `intake → document_review`: REQUIRED ≥ 60% on `modelportfolio.json`
- `document_review → due_diligence`: REQUIRED ≥ 80% on `modelportfolio.json` AND `IM.json` REQUIRED ≥ 80%
- `due_diligence → compliance_review`: ALL four datasets REQUIRED ≥ 90%; no open `CRITICAL` flags

If a gate is met by the post-write completeness, mention it in the output. Do not change `onboarding.stage` — that is a human decision.
