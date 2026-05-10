- route work to the right subagent as early as possible.
- NEVER synthesize, assume, fabricate, or make up information
- Original PDFs and Excel files remain in `.claude/raw_document/` 

You must update CLAUDE.md when edits happened in `/wiki`. Your update contains:
- File location
- 2-5 key words for semantic search
- A max 50 words summary of the content

- log your work to log.md. append-only record of what happened and when — ingests, queries, lint passes. You only need to report three things:
    - Date time this action is logged
    - 1-3 words to summarise your action, such as ingestion, update, delete
    - Details of action. sepecify what file and location you've made changes to

# Knowledge Index

## IMQuestionnaire.clean.json
**Location:** `wiki/IMQuestionnaire.clean.json`  
**Keywords:** Investment manager onboarding, portfolio details, underlying funds, liquidity testing, scenario analysis  
**Summary:** Complete IM questionnaire with two managed portfolios (Balanced and High Growth), underlying fund holdings with manager details, performance scenarios, and liquidity testing data across normal and stressed conditions.

## SAA.clean.json
**Location:** `wiki/SAA.clean.json`  
**Keywords:** Strategic Asset Allocation, portfolio allocation, asset classes, holdings, rebate rates  
**Summary:** Two portfolio models (NTH0001 conservative, NTH0002 growth) with detailed asset class allocations across 6+ asset categories and 26+ investment units with associated rebate rates. Includes data quality flags for duplicate WPC1963AU entries and missing cash unit ID.


