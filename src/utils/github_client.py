"""
GitHub API client with SQLite caching for Claude_DB.
Synchronous — callers should wrap in QThread for non-blocking use.
"""

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

_CONFIG_FILE = Path(__file__).parent.parent.parent / "config" / "config.json"
_CACHE_DIR = Path(__file__).parent.parent.parent / "cache"


def _load_github_config() -> dict:
    try:
        with open(_CONFIG_FILE) as f:
            return json.load(f).get("github", {})
    except Exception as e:
        logger.warning(f"Could not load github config: {e}")
        return {}


class GitHubClient:
    """Reusable GitHub API client with SQLite result cache.

    Usage:
        client = GitHubClient()
        repos = client.get_repo_contents("anthropics", "claude-code")
        rate = client.get_rate_limit()
    """

    API_BASE = "https://api.github.com"

    def __init__(self):
        cfg = _load_github_config()
        self._token: str = cfg.get("token", "")
        self._timeout: int = cfg.get("request_timeout", 30)
        self._cache_hours: float = cfg.get("cache_hours", 24)
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._db_path = _CACHE_DIR / "github_cache.db"
        self._init_db()

    # ── Cache ──────────────────────────────────────────────────────────────

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key       TEXT PRIMARY KEY,
                    data      TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)

    def _cache_get(self, key: str) -> Optional[object]:
        cutoff = time.time() - self._cache_hours * 3600
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT data FROM cache WHERE key=? AND created_at>?", (key, cutoff)
            ).fetchone()
        if row:
            logger.debug(f"Cache hit: {key}")
            return json.loads(row[0])
        return None

    def _cache_set(self, key: str, data: object) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, data, created_at) VALUES (?,?,?)",
                (key, json.dumps(data), time.time())
            )

    def clear_cache(self, pattern: str = None) -> int:
        """Delete cache entries. Pass pattern to clear only matching keys."""
        with sqlite3.connect(self._db_path) as conn:
            if pattern:
                n = conn.execute(
                    "DELETE FROM cache WHERE key LIKE ?", (f"%{pattern}%",)
                ).rowcount
            else:
                n = conn.execute("DELETE FROM cache").rowcount
        logger.info(f"Cleared {n} cache entries" + (f" matching '{pattern}'" if pattern else ""))
        return n

    # ── HTTP ───────────────────────────────────────────────────────────────

    def _request(self, url: str, params: dict = None) -> object:
        """Make authenticated GitHub API request. Raises RuntimeError on failure."""
        if params:
            url = f"{url}?{urlencode(params)}"
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        req.add_header("User-Agent", "Claude_DB/2.0")
        if self._token:
            req.add_header("Authorization", f"Bearer {self._token}")
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode()
            except Exception:
                pass
            raise RuntimeError(f"GitHub API {e.code}: {e.reason} — {body[:200]}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error: {e.reason}")

    # ── Public API ─────────────────────────────────────────────────────────

    def search_code(self, query: str, filename: str = None) -> list:
        """Search GitHub code. Returns list of item dicts."""
        full_query = query + (f" filename:{filename}" if filename else "")
        key = f"search_code:{full_query}"
        cached = self._cache_get(key)
        if cached is not None:
            return cached
        data = self._request(f"{self.API_BASE}/search/code", {"q": full_query, "per_page": 30})
        items = data.get("items", [])
        self._cache_set(key, items)
        return items

    def search_repos(self, query: str, sort: str = "stars") -> list:
        """Search GitHub repositories."""
        key = f"search_repos:{query}:{sort}"
        cached = self._cache_get(key)
        if cached is not None:
            return cached
        data = self._request(
            f"{self.API_BASE}/search/repositories",
            {"q": query, "sort": sort, "per_page": 30}
        )
        items = data.get("items", [])
        self._cache_set(key, items)
        return items

    def get_repo_contents(self, owner: str, repo: str, path: str = "") -> list:
        """List contents of a GitHub repo directory."""
        key = f"contents:{owner}/{repo}/{path}"
        cached = self._cache_get(key)
        if cached is not None:
            return cached
        url = f"{self.API_BASE}/repos/{owner}/{repo}/contents/{path}"
        data = self._request(url)
        if not isinstance(data, list):
            data = [data]
        self._cache_set(key, data)
        return data

    def get_file_content(self, owner: str, repo: str, path: str) -> str:
        """Get the decoded text content of a single file in a GitHub repository."""
        import base64
        key = f"file_content:{owner}/{repo}/{path}"
        cached = self._cache_get(key)
        if cached is not None:
            return cached
        url = f"{self.API_BASE}/repos/{owner}/{repo}/contents/{path}"
        data = self._request(url)
        if isinstance(data, dict) and data.get("encoding") == "base64":
            content = base64.b64decode(data["content"]).decode("utf-8")
        elif isinstance(data, dict) and data.get("download_url"):
            content = self.fetch_raw_url(data["download_url"])
        else:
            raise RuntimeError(f"Unexpected response for file content: {owner}/{repo}/{path}")
        self._cache_set(key, content)
        return content

    def get_repo_info(self, owner: str, repo: str) -> dict:
        """Get repository metadata (stars, description, etc.)."""
        key = f"repo:{owner}/{repo}"
        cached = self._cache_get(key)
        if cached is not None:
            return cached
        data = self._request(f"{self.API_BASE}/repos/{owner}/{repo}")
        self._cache_set(key, data)
        return data

    def get_rate_limit(self) -> dict:
        """Return current GitHub API rate limit info (not cached)."""
        return self._request(f"{self.API_BASE}/rate_limit")

    def fetch_raw_url(self, url: str) -> str:
        """Fetch raw text content from any URL (e.g., raw.githubusercontent.com)."""
        key = f"raw:{url}"
        cached = self._cache_get(key)
        if cached is not None:
            return cached
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Claude_DB/2.0")
        if self._token and "github" in url:
            req.add_header("Authorization", f"Bearer {self._token}")
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                content = resp.read().decode()
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to fetch {url}: {e.reason}")
        self._cache_set(key, content)
        return content

    def has_token(self) -> bool:
        """Return True if a GitHub token is configured."""
        return bool(self._token)
