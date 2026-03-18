---
name: uk-government-funding-tracker
description: Tracks UK government funding announcements and alerts on new opportunities. Use this skill when the user wants to check for new grants, funding streams, or policy changes from bodies like Innovate UK, DCMS, Defra, etc., especially for social enterprises and community projects.
---

# UK Government Funding Tracker

This skill helps you track, summarize, and alert on funding announcements from UK government bodies.

## Workflow

### 1. Identify Sources
Read `references/funding-sources.md` to get the list of priority funding boards and their URLs.

### 2. Search & Extract (using Firecrawl)
For each source, use the `firecrawl` tool (or available web search/browser tools) to find the latest announcements (last 30 days).
*   **Keywords**: "grant", "funding", "competition", "social enterprise", "community", "land", "sustainability".
*   **Focus**: Look specifically for opportunities relevant to:
    *   Social Enterprises (CICs, Co-ops)
    *   Land Projects (Regenerative ag, community gardens)
    *   Community Organisations

### 3. Analyze & Summarize
For each relevant finding:
1.  **Check Eligibility**: Is it open to the target sectors?
2.  **Check Deadline**: Is the deadline within the next **6 weeks**?
3.  **Summarize**: Create a summary of **under 200 words** highlighting:
    *   The change/opportunity (What is it?)
    *   The amount (How much?)
    *   The key action required (What to do?)

### 4. Alert via Notion
Format the findings using the template in `assets/notion_template.md`.
*   If you have a tool to write directly to Notion, use it.
*   Otherwise, present the formatted text clearly to the user and ask them to add it to their "Funding Tracker" database.

## Critical Rules
*   **Deadline Alert**: If a deadline is < 6 weeks away, mark it as **[URGENT]**.
*   **Conciseness**: Summaries must be strictly under 200 words.
*   **Relevance**: Do not report on generic research grants for universities unless they explicitly partner with community orgs.
