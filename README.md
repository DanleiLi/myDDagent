# AI Agent for Due Diligence Analysis

An AI-powered system for comprehensive due diligence analysis of managed portfolios, built with Claude agents and specialized analysis tools.

## Features

- **Portfolio Profiling**: Generate comprehensive profiles including investment strategy, asset allocation, risk levels, and rebalancing details
- **Fee Analysis**: Calculate and analyze portfolio fees, expense ratios, and cost structures
- **Document Processing**: Extract and analyze information from questionnaires, PDFs, and spreadsheets
- **Scenario & Stress Testing**: Evaluate portfolio performance under various market scenarios and stress conditions
- **Investment Team Analysis**: Review and assess investment team composition and experience
- **ESG & Liquidity Assessment**: Analyze environmental, social, governance factors and liquidity testing results

## Project Structure

```
.
├── .claude/
│   ├── agents/           # Claude agent definitions and configurations
│   └── skills/           # Specialized skill modules
├── wiki/                 # Knowledge base (cleaned JSON files)
│   ├── SAA.clean.json    # Strategic Asset Allocation data
│   ├── fees.json         # Portfolio fee structures
│   ├── etf_fees.json     # ETF expense ratios
│   └── IMQuestionnaire*.json  # Investment manager questionnaires
├── CLAUDE.md             # Project guidelines and knowledge index
├── log.md                # Activity log
└── README.md             # This file
```

## Knowledge Base

The `wiki/` folder contains cleaned and structured data:

- **Portfolio Data**: Asset allocation models, fund holdings, and strategic benchmarks
- **Fee Information**: Investment manager fees, ETF costs, and responsible entity charges
- **Investment Manager Info**: Team composition, experience, philosophy, and capacity
- **Scenario Analysis**: Stress testing results and performance under various market conditions
- **Liquidity Analysis**: Redemption scenarios and liquidation timeframes

## How to Use

1. Place raw documents in `raw_documents/` folder
2. Use the available skills to process and analyze:
   - `portfolio-profile`: Generate portfolio analysis
   - `fee-analysis`: Calculate fee structures
   - `xlsx`: Process spreadsheet data
   - `pdf`: Extract data from PDFs

3. Results are saved to `wiki/` for future reference

4. Output analyses go to `output/` folder

## Guidelines

- Never synthesize or assume information—source from cleaned wiki files
- Update CLAUDE.md when adding new wiki files
- Log all activities to log.md (file location, keywords, summary)
- Exclude `raw_documents/`, `output/`, and `wiki/` from version control

## Dependencies

Requires Claude Code with access to:
- Claude agents framework
- Portfolio analysis skills
- Document processing tools
- Fee calculation modules

## License

Project-specific. See CLAUDE.md for working principles.
