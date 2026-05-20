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

log work to log.md. append-only record of what happened and when.

# Knowledge Index
This is a list of wiki files that you can use to source information for your analysis. You should read through these files to understand what each files contains and how to narrow down which files to use for your work.

## Wiki Files
