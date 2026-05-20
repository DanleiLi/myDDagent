# Dossier - Project Instructions
You support managed portfolio onboarding project by maintain high quality data, discover commercial risk, uncover business value, and draft board paper for approval. 

# Dictionary
Series: usually refer to a group of portfolios in one onboarding project
Holding table: The holding components and allocation of individual portfolio
Portfolio ID: a unique 7-digits string begin with `NTH`, interchangable with North ID, Model ID, Portfolio Code.

# Working principle
- Source information for analysis from cleaned files from `.claude\wiki`, narrows down wiki files to go through by reading `knowledge index`. 
- Never use raw files from `.claude\raw_documents` for sourcing information, these are for file ingestion to prepare wiki folder and may contain uncleaned data.

# File ingestion workflow

  Invoke file-convert skill. Once it's done, call data_auditor to review `.claude\wiki`. Based on the feedback, spawn a sub-agent to clean up the file if neccessary. Return to the user with a data quality report and plan for next step.

# Audit and log activities
You must update Claude.md when `.claude\wiki` is edited. Your update contains:
- File location 
- Classify each file into one or more categories:

        business_case
        investment_manager
        investment_team
        portfolio_details
        investment_phylosophy
        strategic_asset_allocation
        holdings
        fees
        underlying_unit_profiles
        direct_equity
        afsl_copy
        esg
        others

- 0- 50 words summary of the document

log work to log.md. append-only record of what happened and when — ingests, queries, lint passes.

# Knowledge Index
This is a list of wiki files that you can use to source information for your analysis. You should read through these files to understand what each files contains and how to narrow down which files to use for your work.

## Wiki Files

### `.claude/wiki/IMQuestionnaire_IM Info.md`
- **Categories:** investment_manager, investment_phylosophy, fees
- **Summary:** BlackRock Investment Management (Australia) Limited entity details (ABN, AFSL, contact info, website), business overview, about paragraph, philosophy paragraph, FUM/capacity, and portfolio manager profile (Emily Hartley — fictional test data). Note: invoice email and several text fields are explicitly fictional.

### `.claude/wiki/IMQuestionnaire_Invst. team.md`
- **Categories:** investment_team
- **Summary:** Five-person investment team roster with name, title, years with firm, total years experience, and role description. Includes a departures section (empty — no departures recorded). All names appear fictional (test data).

### `.claude/wiki/IMQuestionnaire_Portfolio Details.md`
- **Categories:** portfolio_details, strategic_asset_allocation, fees
- **Summary:** Per-portfolio details for five iShares Enhanced Strategic portfolios (Conservative through Aggressive): min/max holdings count, position limits, volatility target, income treatment, cash buffer, benchmarks, risk bands, investment objectives, SAA min/max ranges (target column missing), and IM fee (0.45%). SAA target allocations are absent.

### `.claude/wiki/IMQuestionnaire_Liquidity Testing.md`
- **Categories:** portfolio_details
- **Summary:** Liquidity ratio results across five portfolios under three market conditions (Normal, Moderate Volatility, Severe Stress) and three time horizons (1D, 3D, 4D). Quantitative ratios only — no test date, assumptions, limitations, or pass/fail determination present.

### `.claude/wiki/IMQuestionnaire_Scenario Testing.md`
- **Categories:** portfolio_details
- **Summary:** Seven scenario test results (e.g. Global Financial Crisis, COVID crash) showing portfolio return vs benchmark return for each of the five portfolios. Quantitative figures only — no test date, assumptions, or limitations documented.

### `.claude/wiki/IMQuestionnaire_Underlying Funds.md`
- **Categories:** underlying_unit_profiles
- **Summary:** Profiles for 19 iShares ETFs covering unit ID, unit name, asset class, fund manager (all BlackRock), benchmark, and target excess return. Three columns (Role in portfolio, Strategy highlights, Factor biases) are entirely blank for all 19 ETFs.

### `.claude/wiki/IMQuestionnaire_Directy Equity .md`
- **Categories:** direct_equity
- **Summary:** Direct equity section — contains only a column header row, no data. Portfolios appear to be ETF-only; direct equity applicability needs IM confirmation to mark this section as Not Applicable.

### `.claude/wiki/holdings ver2.md`
- **Categories:** holdings
- **Summary:** Holding-level data (unit ID, holding name, allocation %, asset class, rebate) for five iShares Enhanced Strategic portfolios: Conservative (18 holdings), Moderate (19), Balanced (19), Growth (16), Aggressive (12). All allocations total 100%. Clean unit names, correct asset class labels, and rebate column populated. Report-ready.
