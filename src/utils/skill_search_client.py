"""
Skill Search Client — discover Claude Code skills from GitHub repositories.

Supported discovery modes:
- Source repos (curated list from config/skill_sources.json):
    "direct" repos — contain skill directories with SKILL.md files
    "awesome" repos — contain a README with links to other skill repos
- GitHub code search — search filename:SKILL.md across all public repos
- URL import — fetch a raw SKILL.md from a GitHub URL

Uses GitHubClient for all network calls (SQLite cached).
All methods are synchronous; wrap in QThread for non-blocking use.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_SOURCES_FILE = Path(__file__).parent.parent.parent / "config" / "skill_sources.json"


@dataclass
class SkillResult:
    """A single discovered skill."""
    name: str
    description: str = ""
    owner: str = ""
    repo: str = ""
    url: str = ""
    stars: int = 0
    content: str = ""        # Raw SKILL.md text (may be empty until fetched)
    extra: dict = field(default_factory=dict)


def load_skill_sources() -> list[dict]:
    """Load curated skill sources from config/skill_sources.json."""
    try:
        with open(_SOURCES_FILE) as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load skill_sources.json: {e}")
        return []


class SkillSearchClient:
    """Discover Claude Code skills from GitHub."""

    def __init__(self):
        from utils.github_client import GitHubClient
        self._gh = GitHubClient()

    # ── Source repo browsing ────────────────────────────────────────────

    def list_source_repos(self) -> list[dict]:
        """Return the curated list of source repos."""
        return load_skill_sources()

    def list_skills_in_repo(
        self,
        owner: str,
        repo: str,
        skills_prefix: str = "skills/",
        repo_type: str = "direct",
    ) -> list[SkillResult]:
        """
        List skills from a source repo.

        For "direct" repos: lists subdirs under skills_prefix, finds SKILL.md files.
        For "awesome" repos: parses README for linked repo URLs.
        Returns list of SkillResult (content empty — call fetch_skill_content() to fill).
        """
        if repo_type == "awesome":
            return self._list_awesome_repo(owner, repo)
        else:
            return self._list_direct_repo(owner, repo, skills_prefix)

    def _list_direct_repo(
        self, owner: str, repo: str, skills_prefix: str
    ) -> list[SkillResult]:
        """List skills in a direct repo (subdirs with SKILL.md)."""
        results = []
        try:
            repo_info = self._gh.get_repo_info(owner, repo)
            stars = repo_info.get("stargazers_count", 0) if repo_info else 0

            contents = self._gh.get_repo_contents(owner, repo, skills_prefix.rstrip("/"))
            if not isinstance(contents, list):
                return results

            for item in contents:
                if item.get("type") != "dir":
                    continue
                skill_name = item["name"]
                skill_path = f"{skills_prefix.rstrip('/')}/{skill_name}/SKILL.md"
                skill_content = self._gh.get_file_content(owner, repo, skill_path)
                if skill_content is None:
                    continue
                description = _extract_description(skill_content)
                results.append(SkillResult(
                    name=skill_name,
                    description=description,
                    owner=owner,
                    repo=repo,
                    url=f"https://github.com/{owner}/{repo}/blob/main/{skills_prefix}/{skill_name}/SKILL.md",
                    stars=stars,
                    content=skill_content,
                ))
        except Exception as e:
            logger.warning(f"list_direct_repo {owner}/{repo} failed: {e}")
        return results

    def _list_awesome_repo(self, owner: str, repo: str) -> list[SkillResult]:
        """
        Parse README from an 'awesome' repo and return linked repos as SkillResults.
        Each result represents a linked GitHub repo (not an individual skill).
        """
        results = []
        try:
            readme = self._gh.get_file_content(owner, repo, "README.md")
            if not readme:
                return results
            linked = self.parse_awesome_readme(readme)
            repo_info = self._gh.get_repo_info(owner, repo)
            parent_stars = repo_info.get("stargazers_count", 0) if repo_info else 0
            for link in linked:
                results.append(SkillResult(
                    name=link.get("repo", "unknown"),
                    description=link.get("label", ""),
                    owner=link.get("owner", ""),
                    repo=link.get("repo", ""),
                    url=f"https://github.com/{link.get('owner','')}/{link.get('repo','')}",
                    stars=parent_stars,
                    extra={"type": "awesome_link"},
                ))
        except Exception as e:
            logger.warning(f"list_awesome_repo {owner}/{repo} failed: {e}")
        return results

    def parse_awesome_readme(self, readme: str) -> list[dict]:
        """
        Extract GitHub repo links from an awesome-list README.
        Returns: [{"owner": str, "repo": str, "label": str}]
        """
        pattern = r'\[([^\]]+)\]\(https://github\.com/([^/\s)]+)/([^/\s)#]+)[^)]*\)'
        seen = set()
        results = []
        for m in re.finditer(pattern, readme):
            label, owner, repo = m.group(1), m.group(2), m.group(3)
            key = f"{owner}/{repo}"
            if key not in seen:
                seen.add(key)
                results.append({"owner": owner, "repo": repo, "label": label})
        return results

    # ── GitHub code search ──────────────────────────────────────────────

    def search_github(self, query: str) -> list[SkillResult]:
        """
        Search GitHub for SKILL.md files matching query.
        Returns list of SkillResult (content empty — call fetch_skill_content to fill).
        """
        results = []
        try:
            full_query = f"filename:SKILL.md {query}"
            items = self._gh.search_code(full_query)
            for item in items:
                repo_full = item.get("repository", {}).get("full_name", "/")
                owner, _, repo = repo_full.partition("/")
                results.append(SkillResult(
                    name=item.get("name", "SKILL.md").replace("SKILL.md", "").strip("/") or repo,
                    description="",
                    owner=owner,
                    repo=repo,
                    url=item.get("html_url", ""),
                    stars=0,
                    extra={"path": item.get("path", ""), "repo_full": repo_full},
                ))
        except Exception as e:
            logger.warning(f"GitHub skill search failed: {e}")
        return results

    # ── URL import ──────────────────────────────────────────────────────

    def fetch_from_url(self, url: str) -> Optional[str]:
        """
        Fetch SKILL.md content from a GitHub URL.
        Accepts github.com blob URLs or raw.githubusercontent.com URLs.
        Returns raw text or None on failure.
        """
        try:
            raw_url = _to_raw_url(url)
            return self._gh.fetch_raw_url(raw_url)
        except Exception as e:
            logger.warning(f"fetch_from_url({url}) failed: {e}")
            return None

    def fetch_skill_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        """Fetch a specific SKILL.md file content."""
        try:
            return self._gh.get_file_content(owner, repo, path)
        except Exception as e:
            logger.warning(f"fetch_skill_content {owner}/{repo}/{path} failed: {e}")
            return None


# ── Helpers ─────────────────────────────────────────────────────────────────

def _extract_description(content: str) -> str:
    """Pull 'description' value from SKILL.md YAML frontmatter."""
    in_fm = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "---":
            if not in_fm:
                in_fm = True
                continue
            else:
                break
        if in_fm and stripped.startswith("description:"):
            return stripped[len("description:"):].strip().strip('"').strip("'")
    return ""


def _to_raw_url(url: str) -> str:
    """Convert a github.com blob URL to a raw.githubusercontent.com URL."""
    url = url.strip()
    if "raw.githubusercontent.com" in url:
        return url
    # https://github.com/owner/repo/blob/branch/path → raw URL
    url = url.replace("https://github.com/", "https://raw.githubusercontent.com/")
    url = url.replace("/blob/", "/")
    return url
