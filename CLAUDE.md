# Dossier - Project Instructions

# Working principle
- NEVER synthesize, assume, fabricate, or make up information
- Source information for analysis from cleaned files from `/wiki` , narrows down wiki files to go through by reading knowledge index. 

# Audit and log your activities
You must update CLAUDE.md when `/wiki` is edited. Your update contains:
- File location
- 2-5 key words for semantic search
- 0- 50 words summary of the topics touched on

- log your work to log.md. append-only record of what happened and when — ingests, queries, lint passes. You only need to report three things:
    - Date time this action is logged
    - 1-3 words to summarise your action, such as ingestion, update, delete
    - Details of action. sepecify what file and location you've made changes to

# Knowledge Index

## IMInfo (IM Questionnaire - Investment Manager Information)
**Location:** `/wiki/IMInfo.clean.json`, `/wiki/IMInfo.preprocessed.json`, `/wiki/IMInfo.clean.md`  
**Keywords:** BlackRock Investment Management, ABN, AFSL, portfolio manager, Emily Hartley  
**Summary:** Portfolio Onboarding Questionnaire containing investment manager details (BlackRock Australia ABN 13 006 165 975 AFSL 230523), portfolio manager bio (Emily Hartley), 5 attached documents, zero corporate actions participation, incomplete logo/theme. Fictional test data for agent testing.

## IMQuestionnaire (IM Questionnaire)
**Location:** `/wiki/IMQuestionnaire.clean.json`, `/wiki/IMQuestionnaire.preprocessed.json`, `/wiki/IMQuestionnaire.preprocessed.md`, `/wiki/IMQuestionnaire.clean.md`  
**Keywords:** investment manager, portfolio, liquidity testing, scenario analysis, fund allocation  
**Summary:** Complete IM questionnaire with 8 sheets covering investment manager info, team details, portfolio allocations (33 records), liquidity testing scenarios (10 records), scenario testing (10 records), and underlying fund data (20 records). Direct Equity sheet header only (empty). Investment team contains 11 members. Cleaned artifacts ready for analysis.

## Profiles (Portfolio Profiles)
**Location:** `/wiki/Profiles.clean.json`, `/wiki/Profiles.preprocessed.json`, `/wiki/Profiles.preprocessed.md`  
**Keywords:** portfolio variants, strategic asset allocation, risk band, Conservative, Moderate, Balanced, Growth, Aggressive, All Growth  
**Summary:** Six managed portfolio variants with variant-specific risk bands (3-6), investment horizons (3-5 years), and SAA ranges. All share common parameters: 0.45% manager fee, 8.5-10.5% volatility target, CPI+3% outperformance goal, 25-40% p.a. turnover, active trading strategy. Includes position limits, sector constraints, and growth/defensive asset allocation ranges.
