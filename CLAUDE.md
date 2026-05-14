# Dossier - Project Instructions
You are working on a portfolio onboarding project. 

# Dictionary
Series: usually refer to a group of portfolios in one onboarding project
Holding table: The holding components and allocation of individual portfolio

# Working principle
- NEVER synthesize, assume, fabricate, or make up information
- Source information for analysis from cleaned files from `.claude\wiki` , narrows down wiki files to go through by reading knowledge index. 
- Never use row files from `.claude\row` for sourcing information, these are for file ingestion to prepare wiki folder and may contain uncleaned data.

# Audit and log your activities
You must update Claude.md when `.claude\wiki` is edited. Your update contains:
- File location 
- 2-5 key words for semantic search
- 0- 50 words summary of the topics touched on

- log work to log.md. append-only record of what happened and when — ingests, queries, lint passes.

# Knowledge Index
This is a list of wiki files that you can use to source information for your analysis. You should read through these files to understand what each files contains and how to narrow down which files to use for your work.

## IMQuestionnaire_IM Info.json
**Location:** `.claude/wiki/IMQuestionnaire_IM Info.json`

**Keywords:** investment manager, portfolio manager, corporate actions, BlackRock, onboarding

**Summary:** Portfolio onboarding questionnaire containing investment manager details (legal entity, ABN, AFSL, contact info), portfolio manager information (Emily Hartley), investment philosophy, and corporate actions participation preferences. Includes FUM data and documentation attachment checklist.

## IMQuestionnaire_Invst_ team.json
**Location:** `.claude/wiki/IMQuestionnaire_Invst_ team.json`

**Keywords:** investment team, portfolio construction, risk management, research, experience

**Summary:** Current investment team of 5 members managing Balanced and High Growth portfolios. Includes roles: Head of Portfolio Construction, Portfolio Manager, Risk Director, Implementation Specialist, Research Analyst. Team experience ranges 2-18 years total investment background.

## IMQuestionnaire_Portfolio Details.json
**Location:** `.claude/wiki/IMQuestionnaire_Portfolio Details.json`

**Keywords:** portfolio specifications, asset allocation, risk band, strategic allocation, fees

**Summary:** Five managed portfolio options (Conservative, Balanced, Moderate, Growth, Aggressive) with detailed specifications including strategic asset allocation ranges, volatility targets, fee structure (0.45%), risk bands (3-6), and benchmarks. All portfolios use diversified, active trading strategy.

## IMQuestionnaire_Liquidity Testing.json
**Location:** `.claude/wiki/IMQuestionnaire_Liquidity Testing.json`

**Keywords:** liquidity, bid-offer spread, market stress, liquidation horizon, ETF

**Summary:** Liquidation cost table for 9 portfolios (iShares and Morningstar variants: Conservative, Moderate, Balanced, Growth, All Growth) across 3 market conditions (Normal, Moderate Volatility, Severe Stress) and 3 horizons (1D, 3D, 4D). Values expressed as fraction of portfolio value.

## IMQuestionnaire_Scenario Testing.json
**Location:** `.claude/wiki/IMQuestionnaire_Scenario Testing.json`

**Keywords:** scenario testing, TPA, portfolio return, benchmark return, macro stress

**Summary:** Total Portfolio Analysis results for 7 macro scenarios (equity rally/selloff, rate rises/falls, inflation shock, global recession, liquidity stress) across 5 portfolios (Conservative through Aggressive). Each shows portfolio vs benchmark return.

## IMQuestionnaire_Underlying Funds.json
**Location:** `.claude/wiki/IMQuestionnaire_Underlying Funds.json`

**Keywords:** underlying funds, ETF, iShares, BlackRock, benchmark index

**Summary:** Register of 19-20 iShares ETF building blocks used across the model portfolios. Fields: ticker, name, asset class, region, benchmark index. Covers equities (AU, US, EU, Japan, EM, China), fixed income (AU govt/composite/corporate/inflation, global high yield, global aggregate ESG), property, infrastructure, gold, and cash.