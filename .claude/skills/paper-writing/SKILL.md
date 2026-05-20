---
name: paper-writing
description: Compose board papers for portfolios by completing all {{template placeholders}} with information from .claude\wiki. 
version: 1.0
---

# Overview
Compose board papers for portfolios using `.claude\skills\paper-writing\template.md` by completing all {{template placeholders}} in the template with information from `.claude\wiki`. DO NOT change any content in the template except for filling in the placeholders. Save the output to `@.claude\output\[Series Name] Board Paper - [Date].md`.


# Writing principles

- If the data is missing for any placeholder, write $\color{red}{\text{missing data}}$ in the output. For example, if the portfolio id is missing in a table, them every cell in the portfolio id column should be filled with $\color{red}{\text{missing portfolio id}}$.

- Maintain a formal, professional, and objective tone throughout. 

- Ensure consistency in formatting: use consistent number formats (no mixed digit styles), standardized date formats (DD-MMM-YYYY), and avoid emojis, decorative icons, or ornamental elements. 

- All text should be clear, concise, and suitable for executive-level presentation. 

- Add citation of wiki pages next to any key information. For example, if the portfolio table has all the portfolio information and this information is from a wiki page named "Portfolio_Review_Schedule", then add this where appropriate:  
[Portfolio Review Schedule](/wiki/Portfolio_Review_Schedule.md)


- Do not include any additional sections beyond those in the template. If any section is not applicable, write "Not applicable" under that section.

- Do not fill  $\color{red}{\text{Require input}}$ placeholders. These are for users to fill in after the draft is generated.