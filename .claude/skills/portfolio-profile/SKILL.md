---
name: portfolio-profile
description: Generates a comprehensive profile of managed portfolio, including portfolio name, investment strategy, asset allocation, risk level, tranding and rebalance details, and other relevant information. Use it when creating or updating portfolio profiles for internal documentation, client communication, or marketing materials to provide a clear and concise overview of the portfolio's characteristics and strategy.

---
# North Managed Portfolio Profile

## Overview
This skill generates a comprehensive profile of portfolios.

**Keywords**: portfolio profile, managed portfolio, portfolio summary, portfolio overview, PDS profile

## Workflow
1. **Get template**: your template is located at @.claude\skills\portfolio-profile\assets\Managed Portfolio Profile Template.docx
2. **Input Portfolio Data**: get relevant document from `\wiki`
3. **Confirm Portfolio Count**: confirm the number of portfolios. One portfolio has its own portfolio profile on a seperate page. 
4. **Generate Portfolio Profile**: Compile all portfolio profiles into one word document use script:
`.claude\skills\portfolio-profile\scripts\generate_portfolio_profile.py`

## Output
**Document Format**: Each portfolio profile will be generated as a separate page but all profiles will be in one single word doc. Any missing or incomplete information will be highlighted in the output document.
**File location**: The portfolio profile will be generated as a Word document and saved in the following location: @output\Managed Portfolio Profile - [Portfolio Series Name] - [Date].docx
