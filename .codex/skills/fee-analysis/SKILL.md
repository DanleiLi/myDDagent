---
name: fee-analysis
description: Calculate fees for North's managed portfolio. 
---

## Step 1. Collect Input
- Ensure user or dataset has the following data ready for Step2:
  - Portfolio name
  - Holding identifiers (APIR code or ASX code) 
  - Allocation of each holding in the portfolio
  - Rebate (default zero)
  - Responsible entity(RE) fee rate
  - Investment manager(IM) fee rate


## Step 2. Search Fee Information

2.1. **Web Search PDS**: The PDS is the ONLY acceptable source for holding fees. It lives in the documents / disclosures / forms section of the fund manager's official website.

Aggregator sites (Morningstar, InvestSMART, Stockspot, Canstar, Finder, Selfwealth, etc.) are blocked at the harness level via `.codex/config.toml` — `WebFetch` will fail on those domains. If a `WebSearch` result is from one of those domains, ignore the snippet entirely; do not cite it, do not paraphrase it, and do not use it as a sanity check.

Run the strategies below in order. Stop as soon as one returns a PDS PDF on the fund manager's own domain.

  a. `<APIR or ASX code> PDS site:<fund-manager-domain>` if the manager domain is known.
  b. `<full unit name> PDS <fund manager name> filetype:pdf`.
  c. `<full unit name> product disclosure statement` — discard any aggregator hits from the results.
  d. Navigate the fund manager's website root and look for "Documents", "Disclosures", "Forms & PDS", or "Fund literature" sections.

Only after all four strategies fail, ask the user to supply the PDS URL or the holding's fee figures directly. Do not invent fees and do not substitute aggregator data.

2.3. **Web Fetch PDS**: Fetch the PDS URL. Two outcomes:
   - **Text extractable**: read fees directly from the response and proceed to step 5.
   - **Binary/encoded (PDF unreadable)**: `WebFetch` will report the local file path it saved the PDF to (look for a message like *"Binary content … also saved to …"*). Use that exact path in step 2.4. 

2.4. **Read saved PDF** (only if step 2.3 returned binary content): Use the `Read` tool on the local file path reported by `WebFetch`. The `Read` tool supports PDF files and will extract the text content. Locate the "Fees and costs" section (commonly Section 6) and extract all required fee fields. If the `Read` tool also fails to extract text, report 'Fee information not found in PDS'.

2.5. **Structured Output**: Append the extract fee information into the following structured table format for each holding:

  | UnitID | UnitName | Management fees and costs % | Cash investment fee % | Performance fees % | Gross transaction costs %  | Buy spread % | Sell spread % | Rebate % | PDS URL |
  |---|---|---|---|---|---|---|---|---|---|
  |CASHACCT|MP Cash Account|0|1.40|0|0|0|0|0|-|

  - Gross transaction costs refer to the costs incurred when buying or selling units in the fund, including brokerage fees, settlement costs, and other transaction-related expenses. If the PDS did not specify gross transaction costs, use the transaction costs. If neither is specified, report 'Not disclosed'.
  - Cash investment fee % is 0 for all holdings except for cash account.


2.6. **Examine output**: Check that the PDS URL points to a valid official source and that all fee fields are populated. If the URL is broken, report 'Invalid PDS URL'; if any required fee field could not be determined report 'Incomplete fee information'.


## Step 3. Calculate fees
You must not proceed if step 2 is incompleted.
ALWAYS calculate the fee components for the managed portfolio use @generate_fee_analysis.py by following the below steps.

Run the script. If encounted any error, stop the task and report the error message.


## Step 4. Propose Dataset Update

After Step 3 produces the Excel workbook successfully, the agent MUST propose a dataset update to the user before ending the task. Do not write silently.

4.1. Build two proposed records:

- For `.codex/dataset/portfoliofee.json` — append one entry to `portfolios[]` with fields matching `portfoliofee.schema.json`: `modelid`, `portfolio_name`, `fees{ investment_management_fee, estimated_underlying_management_fees_and_costs, estimated_managed_portfolio_cash_investment_fee, performance_fee, estimated_underlying_performance_fee, estimated_gross_transaction_costs, estimated_underlying_buy_spread, estimated_underlying_sell_spread }`, `flags[]`.

- For `.codex/dataset/holding.json` — append one entry per holding to `holdings[]` with fields matching `holdingfee.schema.json`: `portfolio_name`, `unit_id`, `allocation_percent`, `fees{ management_fees_and_costs, cash_investment_fee, performance_fees, gross_transaction_costs, buy_spread, sell_spread, rebate }`, `pds_link`.

4.2. Show the user a compact preview of both proposed records (JSON or table) and ask exactly: **"Update `portfoliofee.json` and `holdingfee.json` with these records? (yes/no)"**

4.3. Only after the user replies "yes" (or equivalent confirmation), write both files using the `Edit` tool to append to the existing `portfolios[]` / `holdings[]` arrays. Do NOT overwrite `_meta` and do NOT modify the schema files.

4.4. If the user replies "no", end the task without writing. If the user requests corrections, apply them and re-prompt before writing.

4.5. After a successful write, report the number of records added to each file.

