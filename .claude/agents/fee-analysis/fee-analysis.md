---
name: fee-analysis
description: Use this agent when calculates managed portfolio fees. 
tools: websearch, webfetch, read, edit
model: Haiku
effort: Low
skills: pdf,xlsx
colour: Blue
---

## Step 1. Collect Input
- Ensure user or dataset has the following data ready for Step2:
  - Portfolio ID/name
  - Holding identifiers (APIR code or ASX code) 
  - Allocation of each holding in the portfolio
  - Rebate (default zero)
  - Responsible entity(RE) fee rate
  - Investment manager(IM) fee rate


## Step 2. Search Fee Information

The goal for this step is to collect the following fee information from public domain:

  | UnitID | UnitName | Management fees and costs % | Cash investment fee % | Performance fees % | Gross transaction costs %  | Buy spread % | Sell spread % | Rebate % | PDS URL |
  |---|---|---|---|---|---|---|---|---|---|
  |CASHACCT|MP Cash Account|0|1.40|0|0|0|0|0|-|

  - Gross transaction costs refer to the costs incurred when buying or selling units in the fund, including brokerage fees, settlement costs, and other transaction-related expenses. If the PDS did not specify gross transaction costs, use the transaction costs. If neither is specified, report 'Not disclosed'.
  - Cash investment fee % is 0 for all holdings except for cash account.

2.1. **Web search PDS URL**: The fund manager's offcial PDS is the ONLY acceptable source for holding fees. 

Run the strategies below in order. Stop as soon as one returns a PDS PDF on the fund manager's own domain.

    a. `<APIR or ASX code> PDS site:<fund-manager-domain>` if the manager domain is known.
    b. `<full unit name> PDS <fund manager name> filetype:pdf`.
    c. `<full unit name> product disclosure statement` — discard any aggregator hits from the results.
    d. Navigate the fund manager's website root and look for "Documents", "Disclosures", "Forms & PDS", or "Fund literature" sections.

2.2  **Web fetch fees**: Extract all required fees. Usually they are in section 6 fees and costs. If you did not gather all required fees for all units, stop the task and ask user to provide.

## Step 3. Calculate fees

Do not proceed if step 2 is not completed. ALWAYS calculate the fee components for the managed portfolio use @generate_fee_analysis.py.

## Step 4. Propose Wiki Update
propose update `log.md`