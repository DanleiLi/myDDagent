---
name: portfolio-profile
description: Generates a comprehensive profile of AMP North's managed portfolio, including portfolio name, investment strategy, asset allocation, risk level, tranding and rebalance details, and other relevant information. Use it when creating or updating portfolio profiles for internal documentation, client communication, or marketing materials to provide a clear and concise overview of the portfolio's characteristics and strategy.

---
# North Managed Portfolio Profile

## Overview
This skill generates a comprehensive profile of AMP North's managed portfolio.

**Keywords**: portfolio profile, managed portfolio, portfolio summary, portfolio overview, PDS profile

## Workflow
1. **Input Portfolio Data**: Your primary source of truth is an excel workbook named similarly to "investment manager questionaire" in @C:\Users\Sara\OneDrive\MP project, and mainly from page 3 and page 4.
2. **Information Cleaning**:You will read the data from the excel workbook, count number of portfolios to include in your output, and check if all the fields have been populated. If there are missing fields, you will ask user to provide the missing information or confirm whether you should proceed with the available information.
3. **Sense Check**: Check the following rules have been met: 
 - Cash allocation should be more than 1%
 - asset allocation should sum up to 100%
 - Minimum investment timeline should be more than 1 year
 - Benchmark should be either Morningstart index, RBA + x%, Bloomberg index or CPI +X%. Must not be combination of those.
4.  
4. **Generate Portfolio Profile**: Compile all portfolio profiles into one word document. Each portfolio profile use the template  @.codex\skills\portfolio-profile\assets\Managed Portfolio Profile Template.docx

## Output
**Document Format**: You will generate one word document for all portfolios, a page break before each portfolio profile. Any missing or incomplete information will be highlighted in the output document.
**File location**: The portfolio profile will be generated as a Word document and saved in the following location: @.codex\output\Managed Portfolio Profile - [Portfolio Series Name] - [Date].docx
