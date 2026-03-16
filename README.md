# issueops-digest → Notion

AI-powered news curation that automatically pushes summarized articles to a Notion database. No frontend, no server, no monthly fees.

**Search → AI Score → Summarize → Notion DB**

## How it works

1. **Search**: HackerNews Algolia API fetches relevant stories for your keywords (no API key needed)
2. **Score**: Gemini AI filters noise and scores articles by relevance and depth
3. **Summarize**: Jina Reader fetches full text, Gemini generates a Traditional Chinese summary (≤100 words)
4. **Push**: New articles are written to your Notion database, duplicates automatically skipped

## Quick Start

### Option A: CLI Mode (run on your machine)

```bash
git clone https://github.com/YCCC777/issueops-digest.git
cd issueops-digest
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
python web_digest.py "LLM 2026"
```

### Option B: Zero-Server Mode (GitHub Actions)

1. Fork this repo
2. Go to **Settings → Secrets and variables → Actions**
3. Add these secrets:

| Secret | Value |
|--------|-------|
| `GEMINI_API_KEY` | Your Gemini API key (requires GCP billing enabled) |
| `NOTION_API_KEY` | Your Notion integration token |
| `NOTION_DATABASE_ID` | Your Notion database ID |

4. Edit `config.yaml` to set your topics
5. Go to **Settings → Actions → General → Workflow permissions** → select **Read and write permissions**
6. Trigger manually via **Actions → AI Digest to Notion → Run workflow**

The scheduled workflow runs 4 times daily (09:00 / 15:00 / 21:00 / 03:00 UTC+8).

## API Keys

| Service | Required | Free Tier | Notes |
|---------|----------|-----------|-------|
| **Gemini** | Yes | — | Requires GCP billing; usage cost is negligible (~$0.1/month) |
| **Notion** | Yes | Free | [Create an integration](https://www.notion.so/my-integrations) |
| **HackerNews** | — | Free, no key | Algolia-powered search, no signup needed |
| **Tavily** | No | 1000 calls/mo | [tavily.com](https://tavily.com/) — enhances search quality |
| **Jina Reader** | No | Free (rate-limited) | No signup needed |

## Configuration

Edit `config.yaml`:

```yaml
# Topics for scheduled search (English recommended for HackerNews)
topics:
  - "LLM 2026"
  - "AI agent 2026"
  - "OpenAI Anthropic Google AI 2026"
  - "open source LLM 2026"
  - "GitHub Copilot SDK"

# Weight profile: default, news, research
weight_profile: default

# Your trusted sources (higher = more trusted, max 15)
authority_domains:
  bloomberg.com: 15
  reuters.com: 12
```

### Weight Profiles

| Profile | Best for | Behavior |
|---------|----------|----------|
| `default` | General use | Balanced scoring |
| `news` | Breaking news | Recency weighted higher |
| `research` | Deep research | Evergreen content protected from time decay |

## How the scoring works

1. **HackerNews Algolia API** fetches results by relevance + recency (two passes)
2. Results are merged via **round-robin interleaving** so no single source dominates
3. **Jina Reader** fetches full text from quality platforms (Substack, Medium, etc.)
4. **Gemini AI** scores each result for relevance (0–10), flags duplicates
5. A **fuzzy keyword filter** penalizes off-topic results
6. **Authority bonus** from your configured trusted domains
7. **Recency scoring** with evergreen protection in `research` mode
8. Articles scoring above 5 are pushed to Notion (max 10 per run)

## Notion Database Schema

The integration expects a Notion database with these fields:

| Field | Type |
|-------|------|
| 標題 | Title |
| 連結 | URL |
| 摘要 | Text |
| 來源 | Select |
| 主題標籤 | Multi-select |
| 評分 | Number |
| 語言 | Select |
| 日期 | Date |

## Security

- API keys are stored in `.env` (local) or GitHub Secrets (Actions) — never committed
- `.env` is pre-configured in `.gitignore`
- The app verifies `.env` is gitignored on startup

## License

MIT

## Credits

Forked from [notoriouslab/issueops-digest](https://github.com/notoriouslab/issueops-digest). Modified to use HackerNews as the search source and Notion as the output target.
