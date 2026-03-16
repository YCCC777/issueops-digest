"""
notion_output.py — Push scored articles to Notion Database.
Updates seen_urls.json after each successful write (idempotency).
"""
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import summarizer

logger = logging.getLogger(__name__)
SEEN_URLS_PATH = Path(__file__).parent / "seen_urls.json"


def load_seen_urls(path: Path = SEEN_URLS_PATH) -> set:
    if path.exists():
        try:
            return set(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, ValueError):
            return set()
    return set()


def save_seen_urls(seen: set, path: Path = SEEN_URLS_PATH) -> None:
    path.write_text(json.dumps(sorted(seen), indent=2, ensure_ascii=False), encoding="utf-8")


def _detect_lang(title: str) -> str:
    return "ZH" if len(re.findall(r"[\u4e00-\u9fff]", title)) > 2 else "EN"


def push_articles(articles: list[dict], gemini_key: str | None = None) -> int:
    """Push new articles to Notion. Returns count of newly pushed articles."""
    from notion_client import Client

    notion = Client(auth=os.environ["NOTION_API_KEY"])
    db_id = os.environ["NOTION_DATABASE_ID"]
    if gemini_key is None:
        gemini_key = os.environ["GEMINI_API_KEY"]

    seen = load_seen_urls()
    pushed = 0

    for article in articles:
        link = article.get("link", "")
        if not link or link in seen:
            logger.info("[Notion] Skip (seen): %s", link[:60])
            continue

        logger.info("[Notion] Summarizing: %s", article.get("title", "")[:60])
        result = summarizer.summarize(article, gemini_key=gemini_key)

        topics = article.get("topics", [])

        try:
            notion.pages.create(
                parent={"database_id": db_id},
                properties={
                    "標題": {"title": [{"text": {"content": result["zh_title"][:200]}}]},
                    "連結": {"url": link},
                    "摘要": {"rich_text": [{"text": {"content": result["summary"][:2000]}}]},
                    "來源": {"select": {"name": article.get("source", "未知")[:100]}},
                    "主題標籤": {"multi_select": [{"name": kw[:100]} for kw in topics[:5]]},
                    "評分": {"number": round(float(article.get("score", 0)), 2)},
                    "語言": {"select": {"name": _detect_lang(article.get("title", ""))}},
                    "日期": {"date": {"start": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}},
                },
            )
            seen.add(link)
            save_seen_urls(seen)
            pushed += 1
            logger.info("[Notion] Pushed: %s", result["zh_title"][:60])
        except Exception as e:
            logger.error("[Notion] Failed to push %s: %s", link[:60], e)

    logger.info("[Notion] Done. %d new articles pushed.", pushed)
    return pushed


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from dotenv import load_dotenv
    load_dotenv()

    # Test with one fake article (unique URL each run)
    test_articles = [
        {
            "title": "Test: Claude 4 Released",
            "link": f"https://example.com/test-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "snippet": "Anthropic releases Claude 4 with major improvements in reasoning.",
            "source": "example.com",
            "score": 8.5,
            "topics": ["Claude", "AI"],
        }
    ]
    push_articles(test_articles)
