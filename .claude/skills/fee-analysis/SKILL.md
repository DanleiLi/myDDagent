---
name: fee-analysis
description: Use this skill when you need to calculate fees for portfolios
---

## Step 1. Collect Input
- Ensure user or dataset has the following data ready for Step2:
  - Portfolio ID or portfolio name
  - Holding identifiers (APIR code or ASX code) 
  - Allocation of each holding in the portfolio
  - Rebate (default zero)
  - Responsible entity(RE) fee rate
  - Investment manager(IM) fee rate

## Step 2. Search Fee Information
- Use `fee-search` agent to search for fee information from public domain. Handover contains full list of unique unit ids of the holdings.
- Verify whether the fee information is complete for all holdings. If not, stop the task and ask user to provide the missing fee information.

## Step 3. Calculate fees

Do not proceed if step 2 is not completed. ALWAYS calculate the fee components for the managed portfolio use @generate_fee_analysis.py.

## Step 4. Propose Wiki Update
propose update `log.md`
