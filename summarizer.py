"""
summarizer.py — Fetch full text via Jina Reader, then summarize with Gemini.
Returns {"zh_title": "...", "summary": "..."}
"""
import json
import logging
import os
import requests

logger = logging.getLogger(__name__)


def summarize(article: dict, gemini_key: str | None = None) -> dict:
    """Summarize a single article. Falls back to title+snippet if Jina fails."""
    if gemini_key is None:
        gemini_key = os.environ["GEMINI_API_KEY"]

    title = article.get("title", "")
    link = article.get("link", "")
    snippet = article.get("snippet", "")

    content = _fetch_jina(link)
    fallback = not content

    if fallback:
        content = f"{title}\n{snippet}"
        logger.warning("[Summarizer] Jina failed, using fallback for %s", link[:60])

    result = _call_gemini(title, content, gemini_key)
    if fallback:
        result["summary"] += " ⚠️ 摘要僅供參考"
    return result


def _fetch_jina(url: str) -> str:
    try:
        resp = requests.get(
            f"https://r.jina.ai/{url}",
            headers={"Accept": "application/json"},
            timeout=12,
        )
        if resp.status_code == 200:
            try:
                return resp.json().get("data", {}).get("content", "")[:4000]
            except (ValueError, KeyError):
                return resp.text[:4000]
    except requests.RequestException as e:
        logger.warning("[Jina] Error: %s", e)
    return ""


def _call_gemini(title: str, content: str, gemini_key: str) -> dict:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=gemini_key)
    prompt = (
        "請用繁體中文摘要以下文章，限制在100字以內。\n"
        "規則：直接描述文章核心內容，不要以「這篇文章」「本文」「作者」開頭。\n"
        "若標題為英文，請同時提供中文標題。\n"
        '輸出格式 JSON（不加 markdown code block）：{"zh_title": "...", "summary": "..."}\n\n'
        f"標題：{title[:200]}\n"
        f"內文：{content[:3000]}"
    )
    try:
        resp = client.models.generate_content(
            model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        data = json.loads(resp.text)
        return {
            "zh_title": data.get("zh_title") or title,
            "summary": data.get("summary", ""),
        }
    except Exception as e:
        logger.warning("[Summarizer] Gemini error: %s", e)
        return {"zh_title": title, "summary": "（摘要失敗）"}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from dotenv import load_dotenv
    load_dotenv()
    test = {
        "title": "OpenAI releases GPT-5 with major improvements",
        "link": "https://openai.com/blog/gpt-5",
        "snippet": "OpenAI has released GPT-5, featuring significant improvements in reasoning.",
    }
    import pprint
    pprint.pprint(summarize(test))
