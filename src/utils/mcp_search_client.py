"""
MCP Search Client — searches multiple sources for MCP servers.
Ported from MCP_Search project (customtkinter) to plain Python + SQLite cache.
All methods are synchronous; wrap in QThread for non-blocking use.
"""

import json
import logging
import sqlite3
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode, quote_plus

logger = logging.getLogger(__name__)

_CONFIG_FILE = Path(__file__).parent.parent.parent / "config" / "config.json"
_CACHE_DIR = Path(__file__).parent.parent.parent / "cache"
_CACHE_DB = _CACHE_DIR / "mcp_search.db"


@dataclass
class MCPResult:
    """A single MCP server search result."""
    name: str
    description: str = ""
    source: str = ""
    stars: int = 0
    install_command: str = ""
    url: str = ""
    extra: dict = field(default_factory=dict)


def _load_config() -> dict:
    try:
        with open(_CONFIG_FILE) as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load config: {e}")
        return {}


class MCPSearchClient:
    """Search for MCP servers across multiple sources.

    Supported sources (configurable via config["mcp_search"]["enabled_sources"]):
    - "mcp.so"         → mcp.so API
    - "mcpservers.org" → mcpservers.org API
    - "pulsemcp.com"   → PulseMCP API
    - "github"         → GitHub code search (requires token for best results)
    """

    # Source key → display label
    SOURCE_LABELS = {
        "mcp.so": "mcp.so",
        "mcpservers.org": "mcpservers.org",
        "pulsemcp.com": "PulseMCP",
        "github": "GitHub",
    }

    def __init__(self):
        cfg = _load_config()
        self._search_cfg: dict = cfg.get("mcp_search", {})
        self._github_cfg: dict = cfg.get("github", {})
        self._enabled_sources: list[str] = self._search_cfg.get(
            "enabled_sources", ["mcp.so", "mcpservers.org", "pulsemcp.com", "github"]
        )
        self._cache_hours: float = self._search_cfg.get("cache_hours", 24)
        self._timeout: int = self._github_cfg.get("request_timeout", 30)
        self._token: str = self._github_cfg.get("token", "")
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ── Cache ──────────────────────────────────────────────────────────────

    def _init_db(self) -> None:
        with sqlite3.connect(_CACHE_DB) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key        TEXT PRIMARY KEY,
                    data       TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)

    def _cache_get(self, key: str) -> Optional[list]:
        cutoff = time.time() - self._cache_hours * 3600
        with sqlite3.connect(_CACHE_DB) as conn:
            row = conn.execute(
                "SELECT data FROM cache WHERE key=? AND created_at>?", (key, cutoff)
            ).fetchone()
        if row:
            logger.debug(f"MCP cache hit: {key}")
            raw = json.loads(row[0])
            return [MCPResult(**r) for r in raw]
        return None

    def _cache_set(self, key: str, results: list[MCPResult]) -> None:
        raw = [r.__dict__ for r in results]
        with sqlite3.connect(_CACHE_DB) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, data, created_at) VALUES (?,?,?)",
                (key, json.dumps(raw), time.time())
            )

    def clear_cache(self) -> int:
        with sqlite3.connect(_CACHE_DB) as conn:
            n = conn.execute("DELETE FROM cache").rowcount
        logger.info(f"Cleared {n} MCP search cache entries")
        return n

    # ── HTTP helpers ───────────────────────────────────────────────────────

    def _get_json(self, url: str, params: dict = None, headers: dict = None) -> object:
        if params:
            url = f"{url}?{urlencode(params)}"
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Claude_DB/2.0")
        req.add_header("Accept", "application/json")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            return json.loads(resp.read().decode())

    # ── Source searches ────────────────────────────────────────────────────

    def _search_mcp_so(self, query: str) -> list[MCPResult]:
        """Search mcp.so for MCP servers."""
        key = f"mcp.so:{query}"
        cached = self._cache_get(key)
        if cached is not None:
            return cached
        results = []
        try:
            # mcp.so search endpoint
            url = f"https://mcp.so/api/search?q={quote_plus(query)}&type=server&limit=20"
            data = self._get_json(url)
            items = data if isinstance(data, list) else data.get("results", data.get("items", []))
            for item in items:
                results.append(MCPResult(
                    name=item.get("name", item.get("title", "Unknown")),
                    description=item.get("description", ""),
                    source="mcp.so",
                    stars=item.get("stars", 0),
                    install_command=item.get("install", item.get("command", "")),
                    url=item.get("url", item.get("link", "")),
                ))
        except Exception as e:
            logger.warning(f"mcp.so search failed: {e}")
        self._cache_set(key, results)
        return results

    def _search_mcpservers_org(self, query: str) -> list[MCPResult]:
        """Search mcpservers.org."""
        key = f"mcpservers.org:{query}"
        cached = self._cache_get(key)
        if cached is not None:
            return cached
        results = []
        try:
            url = f"https://mcpservers.org/api/search?q={quote_plus(query)}&limit=20"
            data = self._get_json(url)
            items = data if isinstance(data, list) else data.get("servers", data.get("results", []))
            for item in items:
                results.append(MCPResult(
                    name=item.get("name", "Unknown"),
                    description=item.get("description", ""),
                    source="mcpservers.org",
                    stars=item.get("stars", 0),
                    install_command=item.get("command", item.get("install", "")),
                    url=item.get("url", item.get("repo", "")),
                ))
        except Exception as e:
            logger.warning(f"mcpservers.org search failed: {e}")
        self._cache_set(key, results)
        return results

    def _search_pulsemcp(self, query: str) -> list[MCPResult]:
        """Search PulseMCP."""
        key = f"pulsemcp:{query}"
        cached = self._cache_get(key)
        if cached is not None:
            return cached
        results = []
        try:
            url = "https://www.pulsemcp.com/api/servers"
            data = self._get_json(url, params={"query": query, "count_per_page": 20})
            items = data.get("servers", data if isinstance(data, list) else [])
            for item in items:
                # Build install command from package if available
                pkg = item.get("package_name", "")
                cmd = ""
                if pkg:
                    runtime = item.get("runtime", "npx")
                    cmd = f"npx {pkg}" if "npm" in runtime.lower() or runtime == "npx" else f"uvx {pkg}"
                results.append(MCPResult(
                    name=item.get("name", "Unknown"),
                    description=item.get("short_description", item.get("description", "")),
                    source="PulseMCP",
                    stars=item.get("github_stars", 0),
                    install_command=cmd,
                    url=item.get("source_code_url", item.get("url", "")),
                ))
        except Exception as e:
            logger.warning(f"PulseMCP search failed: {e}")
        self._cache_set(key, results)
        return results

    def _search_github(self, query: str) -> list[MCPResult]:
        """Search GitHub for MCP server repositories."""
        key = f"github:{query}"
        cached = self._cache_get(key)
        if cached is not None:
            return cached
        results = []
        try:
            from utils.github_client import GitHubClient
            client = GitHubClient()
            repos = client.search_repos(f"{query} mcp server", sort="stars")
            for repo in repos[:20]:
                name = repo.get("name", "Unknown")
                install_cmd = ""
                pkg_name = name.lower().replace("_", "-")
                install_cmd = f"npx {pkg_name}"  # best-effort
                results.append(MCPResult(
                    name=name,
                    description=repo.get("description", ""),
                    source="GitHub",
                    stars=repo.get("stargazers_count", 0),
                    install_command=install_cmd,
                    url=repo.get("html_url", ""),
                    extra={"full_name": repo.get("full_name", "")},
                ))
        except Exception as e:
            logger.warning(f"GitHub MCP search failed: {e}")
        self._cache_set(key, results)
        return results

    # ── Public API ─────────────────────────────────────────────────────────

    def search(self, query: str, sources: list[str] = None) -> list[MCPResult]:
        """Search all enabled sources and return combined results.

        Args:
            query:   Search term.
            sources: Override which sources to search (default: config enabled_sources).

        Returns:
            Combined list of MCPResult objects, deduped by name.
        """
        if sources is None:
            sources = self._enabled_sources

        all_results: list[MCPResult] = []
        seen_names: set[str] = set()

        dispatch = {
            "mcp.so":         self._search_mcp_so,
            "mcpservers.org": self._search_mcpservers_org,
            "pulsemcp.com":   self._search_pulsemcp,
            "github":         self._search_github,
        }

        for source in sources:
            fn = dispatch.get(source)
            if fn:
                try:
                    for result in fn(query):
                        key = result.name.lower()
                        if key not in seen_names:
                            seen_names.add(key)
                            all_results.append(result)
                except Exception as e:
                    logger.error(f"Source {source} failed: {e}")

        # Sort: sources with stars first, then alphabetical
        all_results.sort(key=lambda r: (-r.stars, r.name.lower()))
        return all_results

    def enabled_sources(self) -> list[str]:
        """Return list of enabled source keys."""
        return list(self._enabled_sources)
