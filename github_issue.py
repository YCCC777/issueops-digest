"""
GitHub Issue output handler for issueops-digest.
Creates a checkbox-style Issue for manual article selection.
"""
import os
import re
import requests
from datetime import datetime
from typing import List, Dict
try:
    from dotenv import load_dotenv as _load_dotenv
except ImportError:
    _load_dotenv = None


class GitHubIssueOutput:
    def __init__(self):
        if _load_dotenv:
            _load_dotenv()
        self.token = os.getenv("GITHUB_TOKEN")
        self.repo = os.getenv("GITHUB_REPO")

        if not self.token:
            raise ValueError("GITHUB_TOKEN not set. Check your .env file.")
        if not self.repo:
            raise ValueError("GITHUB_REPO not set. Check your .env file. (e.g. your-username/issueops-digest)")

        self.api_url = f"https://api.github.com/repos/{self.repo}/issues"
        self._headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def _ensure_labels(self):
        """Create required labels if they don't exist (idempotent)."""
        url = f"https://api.github.com/repos/{self.repo}/labels"
        for name, color in [("discovery", "0075ca"), ("pending-capture", "e4e669")]:
            resp = requests.post(url, json={"name": name, "color": color}, headers=self._headers)
            # 201 = created, 422 = already exists — both are fine
            if resp.status_code not in (201, 422):
                print(f"  ⚠️ Failed to create label '{name}': {resp.status_code} — check token permissions")

    def publish(self, keywords: str, results: List[Dict]) -> str:
        """Create a discovery Issue with checkbox list."""
        self._ensure_labels()
        today = datetime.now().strftime("%Y%m%d")
        title = f"🔍 Search Results: {keywords} - {today}"

        body = "## 📅 issueops-digest Discovery\n"
        body += f"Keywords: `{keywords}`\n\n"
        body += "Check the articles you want to capture, then **Close** this Issue to trigger auto-capture.\n\n"
        body += "---\n\n"

        for res in results:
            score = res.get('score', 0)
            body += f"- [ ] {res['title']} (Score: {score})\n"
            body += f"  - URL: {res['link']}\n"
            body += f"  - Source: {res.get('source', 'Unknown')}\n\n"

        payload = {
            "title": title,
            "body": body,
            "labels": ["discovery", "pending-capture"]
        }

        response = requests.post(self.api_url, json=payload, headers=self._headers)
        if response.status_code == 201:
            url = response.json().get('html_url')
            print(f"\n✅ Issue created: {url}")
            return url
        else:
            return f"Error: Failed to create issue. status={response.status_code}, msg={response.text[:200]}"

    @staticmethod
    def parse_selected_urls(issue_body: str) -> List[str]:
        """Parse checked checkbox URLs from Issue body."""
        pattern = r'- \[[xX]\] .*?(?:\r?\n)+\s*- URL: (https?://[^\s]+)'
        return re.findall(pattern, issue_body, re.DOTALL)


if __name__ == "__main__":
    # Self-test
    test_body = """
- [x] Test Title 1
  - URL: https://example.com/1
- [ ] Test Title 2
  - URL: https://example.com/2
- [X] Test Title 3
  - URL: https://example.com/3
    """
    urls = GitHubIssueOutput.parse_selected_urls(test_body)
    assert len(urls) == 2
    assert urls[0] == "https://example.com/1"
    assert urls[1] == "https://example.com/3"
    print(f"✅ Self-test passed: {urls}")
