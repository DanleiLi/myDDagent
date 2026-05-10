---
This script documents the key techinical details of generate_fee_analysis.py

Reuse this script when you want to make changes to the fee formulas, branding and structure of the output.

Version: 1.0
Date: 4 May 2026
---

# Fee formulas
The formulas are as follows:
- **Investment Management Fee**: 
  - Formula: `Investment Management Fee = (IM Fee ) * (1 + GST Rate - GST Rate * IM RITC Rate) + (RE Fee) * (1 + GST Rate -  GST Rate * RE RITC Rate)`
  - where the IM RITC rate is 75%, and the RE RITC rate is 55%, the GST rate is 10%.
  
- **Estimated Underlying Management Fees and Costs**: Calculates weighted average management fees and costs of the underlying holdings in the portfolio minus rebates.
  - Formula: `Underlying Investment Management Fee = weighted average management fees and costs - weighted average rebate`

- **Rebate Calculation**: Calculates weighted average management rebate of the underlying holdings in the portfolio. 
  - Formula: `Rebate = (Rebate1 * Allocation1 + Rebate2 * Allocation2 + ... + RebateN * AllocationN) / (Allocation1 + Allocation2 + ... + AllocationN)`
 
- **Estimated Managed Portfolio Cash Investment Fee**: 
  - Formula: `Estimated Managed Portfolio Cash Investment Fee = Cash Investment Fee of cash holding * Allocation of cash holding`

- **Portfolio performance fee** : always 0

- **Estimated Underlying Performance Fee**: Calculates weighted average performance fees of the underlying holdings in the portfolio.

- **Estimated Gross Transaction Costs**:  Calculates weighted average gross transaction costs of the underlying holdings in the portfolio.

- **Estimated Underlying Buy Spread**:  Calculates weighted average buy spreads of the underlying holdings in the portfolio.

- **Estimated Underlying Sell Spread**:  Calculates weighted average sell spreads of the underlying holdings in the portfolio.



-  **Tab 1 : Fee Summary** : Create a table with each column representing a portfolio, and each row representing a fee component. All the cells under the fee components should contain the Excel formulas used to calculate the fees, referencing the appropriate cells from other tabs.

 
  | Fee Component | Portfolio ID 1 <br> Portfolio 1 | Portfolio ID 2 <br> Portfolio 2 | Portfolio ID 3 <br> Portfolio 3 |
  |---|---|---|---|
  | Investment management fees % p.a. | | | |
  | Rebate % p.a. | | | |
  | Estimated underlying management fees % p.a. | | | |
  | Estimated managed portfolio cash investment fee % p.a. | | | |
  | Portfolio performance fee % p.a. | | | |
  | Estimated underlying performance fee % p.a. | | | |
  | Estimated gross transaction costs % p.a. | | | |
  | Estimated underlying buy spread % p.a. | | | |
  | Estimated underlying sell spread % p.a. | | | |

-  **Tab 2: Component table**: Take the output from step 2.5.
-  **Tab 3: Portfolio holdings**: Show holdings and allocation of each portfolio.
  | Portfolio ID |	Portfolio Name | Unit ID	| Allocation % |
  |---|---|---|---|


