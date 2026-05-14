---
name: paper-writing
description: Use this skill when writing board paper for portfolios
---

## STEP 1: Plan the paper
Go through the following topics except for topic 1 and 7, reflect what analysis been completed and saved in wiki? which wiki document might have such information? 
Then, delegate incompleted sections to doc-writer agents, call multiple doc-writer agents if necessary. You should pack topics writing tasks if they are all using the same wiki pages. Because this is token efficient.
Your handover note contains: what topics to write, any specific requirements of that topic, and which wiki page may have the data to support the analysis.

### DD Topics
**1. Resolution**
  Summarise the key points from the analysis and write a concise but comprehensive resolution for the board to approve. This should include the recommendation, key risks and mitigations, and any other critical information that the board needs to know to make an informed decision.

**2. Investor Interests / Member Best Financial Interests (MBFI)**
  Analyse the proposed portfolios from the perspective of investor interests and MBFI. Does the licensee, investment managers and advisory groups have conflicts of interest that may impact the proposed portfolios? 

**3. Background**
  - practice introduction
  - investment manager introduction
  - business case summary


**4. Proposed Portfolios for Inclusion**
  Summarise the proposed portfolios, including their model id, name, asset class and menu type.

**5. Managed Portfolio Assessment**
  - leave it blank.

**6. Fee Considerations**
  Summarise the fee and costs for the proposed portfolios, including the investment management fee, total estimated cost. Note any performance fee and rebate arrangements. Conclude with a one-sentence value assessment.

**7. Conflicts Declaration**
  Skip this for now.

**8. Delivery and/or Next Steps**
  What's the proposed implementation plan and next steps, including any critical dependencies or risks to delivery? What's thego live date?

**9. Appendix**
  - Appendix A – Platform Assessment and Scorecard
    Leave it blank.
  
  - Appendix B – Investment Parameters and Objectives
    Investment objective of the portfolios, including the SRM band, risk level, and any other relevant parameters.

  - Appendix C – Asset Allocation
    Asset allocation of the portfolios, including the percentage allocation to each asset class and any relevant details about the underlying investments.

  - Appendix D – Performance
    Performance of the portfolios, including historical returns, volatility, and any other relevant performance metrics. Include as-at date and source document for all performance figures.

  - Appendix E – Stress Testing and Liquidity Analysis
    Summary of the stress testing and liquidity analysis, including any scenarios where loss exceeded the SRM-implied band and any relevant liquidity metrics.

  - Appendix F – Implementation Plan
    Detailed implementation plan, including key milestones, dependencies, and risks to delivery.

  - Appendix G – Disclosure
    Leav it blank.


If a section has no data, emit an empty heading. If a section has partial data, write what you can and `[MISSING:]` the rest.

---

## STEP 2: Compose analysis
Write the markdown file with the structure in DD Topics. Use the data and analysis from the wiki pages to fill in each section. If you have delegated any sections to doc-writer agents, incorporate their output into the relevant sections here.

## STEP 3: Write resolution
You will then write the first topic Resolution based on all the analysis. Why do you recommend the proposed portfolios, what are the key risks and mitigations, and what is the recommended resolution for the board to approve. This section should be concise but comprehensive, summarising the key points from the rest of the document.

## STEP 4: Final review and polish

- All defined terms must follow legal drafting convention on first use: `Full Legal Name ("Short Name")`. Use ShortName exclusively in subsequent references.
- Tables must be GitHub-Flavored Markdown (GFM): pipe-delimited, header row, separator row of dashes. No HTML, no fancy formatting.
- Every table must be immediately followed by a "Key Observations" paragraph.
- Performance figures must include their as-at date and source document.
- Writing must be concise, formal, and consistent in register throughout.
- Re-read each section before moving to the next to ensure consistency.
- In table and bullet points, always order portfolios by risk level in ascending order, low risk portfolios on top or left
