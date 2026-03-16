# issueops-digest → Notion Bot

## 專案目標
Fork issueops-digest，把輸出從 GitHub Issue 改成自動摘要後推送至 Notion Database。零伺服器、零成本。

下游：日後另立獨立 LINE BOT 專案從 Notion DB 讀資料，兩者解耦。

## 目前進度

### ✅ 完成
- Phase 1：架構設計
- Phase 2：Notion DB 建立（欄位：標題/連結/摘要/來源/主題標籤/評分/語言/日期）
- Phase 3：程式碼實作
  - 新增 `summarizer.py`（Jina Reader + Gemini 摘要）
  - 新增 `notion_output.py`（寫入 Notion，逐篇更新 seen_urls.json）
  - 新增 `seen_urls.json`（跨執行去重）
  - 修改 `web_digest.py`（run_digest 改為輸出至 Notion，score > 5 過濾）
  - 修改 `requirements.txt`（新增 notion-client）
  - 新增 `.github/workflows/digest.yml`（cron 排程 + auto commit seen_urls）

### ⏳ 下次繼續（Phase 4 驗證）
1. 填 `.env`（BRAVE_API_KEY、GEMINI_API_KEY、NOTION_API_KEY）
2. 安裝依賴：`pip install -r requirements.txt`
3. 測試 Notion 寫入：`python notion_output.py` → 確認 Notion DB 出現測試資料
4. 測試完整流程：`python web_digest.py "LLM 2026"`
5. 冪等性測試：再跑一次，確認不重複寫入
6. Push 到 GitHub，設定 Secrets，手動觸發 Actions 驗證

## 重要資訊

| 項目 | 值 |
|---|---|
| Notion Database ID | `3237e97b912b8025a6b2c1ca723bf483` |
| Notion DB URL | https://www.notion.so/3237e97b912b8025a6b2c1ca723bf483 |
| cron 排程 | `0 1,7,13,19 * * *`（UTC = 台灣 9:00/15:00/21:00/03:00） |

## GitHub Secrets 需設定
- `GEMINI_API_KEY`
- `NOTION_API_KEY`
- `NOTION_DATABASE_ID`（值：`3237e97b912b8025a6b2c1ca723bf483`）

## 架構流程
```
config.yaml topics
  → HackerNews Algolia API（免費，無需 key）
  → Tavily Search（選用，有 key 才啟用）
  → Gemini 評分（score > 5，取前 10）
  → seen_urls.json 去重
  → Jina Reader 抓全文 + Gemini 摘要中譯
  → Notion API 寫入 DB
  ↑
GitHub Actions cron（每天 4 次）
```
