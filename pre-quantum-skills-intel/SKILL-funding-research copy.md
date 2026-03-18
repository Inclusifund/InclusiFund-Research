d---
name: uk-funding-research
description: Automated research for UK grants suitable for grassroots CICs (£5k-£250k). Use this skill to find, filter, and prioritize funding opportunities from major UK databases (Big Lottery, Esmée Fairbairn, etc.) and save them to Notion.
---

# UK Funding Research

This skill automates the discovery and prioritization of grant funding for UK-based grassroots Community Interest Companies (CICs).

## Capabilities

1. **Targeted Search**: Scans specific high-value funding databases.
2. **Smart Filtering**: select grants between £5k-£250k.
3. **Data Extraction**: Pulls eligibility, deadlines, and application methods.
4. **Prioritization**: Scores opportunities against client pipeline needs.
5. **Integration**: Saves formatted leads directly to Notion.

## Workflow

### 1. Search for Grants

Use `scripts/search_funds.py` to crawl funding databases and extract opportunities.

```bash
# Search all configured databases
python scripts/search_funds.py

# Search a specific database
python scripts/search_funds.py --source big_lottery
```

This script will:
- Use Firecrawl MCP to search and extract data.
- Filter for CIC eligibility and budget fit (£5k-£250k).
- Save results to `.tmp/found_grants.json`.

### 2. Review and Prioritize

The search results are automatically scored based on:
- **Mission fit**: Keywords matching grassroots/community focus.
- **Budget fit**: Within £5k-£250k sweet spot.
- **Urgency**: Approaching deadlines.

### 3. Save to Notion

Use `scripts/save_to_notion.py` to push the identified opportunities to the Notion pipeline.

```bash
# Upload results from the search step
python scripts/save_to_notion.py --input .tmp/found_grants.json
```

## Configuration

### Funding Sources
See [references/funding_databases.md](references/funding_databases.md) for the list of supported databases and search URLs.

### Notion Schema
See [references/notion_schema.md](references/notion_schema.md) for the required database structure.

## Requirements

- **Firecrawl MCP**: Must be active for searching.
- **Notion API**: Requires `NOTION_API_KEY` and `NOTION_DATABASE_ID` (or passed as args).
