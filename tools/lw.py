"""Small, polite LessWrong / Alignment Forum reader.

Used by the validator (quote check), the scouting scripts and the MCP server.
Standard library only, so the GitHub Action needs no extra install for it.

Rules this module enforces:
- every response is cached on disk (outside version control, see .gitignore);
- at least PAUSE_SECONDS between network requests;
- post texts are never written anywhere except that cache.
"""
from __future__ import annotations

import gzip
import html as html_lib
import http.client
import json
import os
import re
import shutil
import subprocess
import time
import unicodedata
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

GRAPHQL_URL = "https://www.lesswrong.com/graphql"
SEARCH_URL = "https://www.lesswrong.com/api/search"
SEARCH_INDEX = "test_posts"
USER_AGENT = "failed-experiments-wiki-poc/0.1 (research prototype; cached, rate-limited)"
PAUSE_SECONDS = 1.5
TIMEOUT_SECONDS = 40
RETRIES = 3

REPO_ROOT = Path(__file__).resolve().parent.parent
_last_request_at = 0.0
_prefer_curl = False


class SourceUnreachable(Exception):
    """The source could not be fetched and is not in the cache."""


def cache_dir() -> Path:
    """Cache location. Never committed: .cache/ is in .gitignore."""
    override = os.environ.get("FEWIKI_CACHE")
    return Path(override) if override else REPO_ROOT / ".cache" / "lw"


def _post_json(url: str, payload: Any) -> Any:
    global _last_request_at, _prefer_curl
    wait = PAUSE_SECONDS - (time.monotonic() - _last_request_at)
    if wait > 0:
        time.sleep(wait)
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT, "Accept-Encoding": "gzip"},
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(RETRIES):
        if attempt:
            time.sleep(PAUSE_SECONDS * (attempt + 1))  # back off before retrying a dropped read
        try:
            if _prefer_curl:
                return _post_json_curl(url, data)
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                raw = response.read()
                if response.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
            return json.loads(raw.decode("utf-8"))
        except http.client.IncompleteRead as exc:
            # Seen behind some HTTP/1.1 proxies: chunked responses are cut short.
            # curl negotiates HTTP/2 and is not affected, so switch to it if present.
            last_error = exc
            if shutil.which("curl"):
                _prefer_curl = True
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError, EOFError, ValueError) as exc:
            last_error = exc
        finally:
            _last_request_at = time.monotonic()
    raise SourceUnreachable(f"{url}: {last_error!r}") from last_error


def _post_json_curl(url: str, data: bytes) -> Any:
    """Fallback transport: the same POST through the curl binary."""
    completed = subprocess.run(
        [
            "curl", "-sS", "--fail", "--compressed", "-m", str(TIMEOUT_SECONDS), "-X", "POST",
            "-H", "Content-Type: application/json", "-H", f"User-Agent: {USER_AGENT}",
            "--data-binary", "@-", url,
        ],
        input=data,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise OSError(f"curl exit {completed.returncode}: {completed.stderr.decode('utf-8', 'replace')[:200]}")
    return json.loads(completed.stdout.decode("utf-8"))


def _cached(path: Path, fetch, *, refresh: bool = False, offline: bool = False) -> Any:
    if path.exists() and not refresh:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    if offline:
        raise SourceUnreachable(f"offline and not cached: {path.name}")
    value = fetch()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False)
    return value


# --------------------------------------------------------------------------
# URLs
# --------------------------------------------------------------------------

_POST_ID_RE = re.compile(
    r"^https://(?:www\.)?(lesswrong\.com|alignmentforum\.org|greaterwrong\.com)/posts/([A-Za-z0-9]+)"
)


def post_id_from_url(url: str) -> str | None:
    """Post ID from a LessWrong / Alignment Forum / GreaterWrong post URL."""
    match = _POST_ID_RE.match(url or "")
    return match.group(2) if match else None


def source_type_from_url(url: str) -> str | None:
    match = _POST_ID_RE.match(url or "")
    if not match:
        return None
    return "alignment_forum" if match.group(1) == "alignmentforum.org" else "lesswrong"


# --------------------------------------------------------------------------
# Posts
# --------------------------------------------------------------------------

_POST_QUERY = """
query Post($id: String) {
  post(input: {selector: {_id: $id}}) {
    result {
      _id title slug pageUrl postedAt baseScore af
      user { displayName slug }
      coauthors { displayName slug }
      tags { name slug }
      contents { wordCount html }
    }
  }
}
"""


def fetch_post(post_id: str, *, refresh: bool = False, offline: bool = False) -> dict:
    """Fetch one post (metadata + HTML body) by ID, through the cache.

    Alignment Forum posts share IDs with LessWrong, so they are read from the
    LessWrong API as well.
    """

    def fetch() -> dict:
        payload = _post_json(GRAPHQL_URL, {"query": _POST_QUERY, "variables": {"id": post_id}})
        result = ((payload.get("data") or {}).get("post") or {}).get("result")
        if not result:
            raise SourceUnreachable(f"post {post_id}: not found ({str(payload.get('errors'))[:200]})")
        return result

    return _cached(cache_dir() / "posts" / f"{post_id}.json", fetch, refresh=refresh, offline=offline)


def post_authors(post: dict) -> list[str]:
    names = []
    user = post.get("user") or {}
    if user.get("displayName"):
        names.append(user["displayName"])
    for coauthor in post.get("coauthors") or []:
        if coauthor.get("displayName") and coauthor["displayName"] not in names:
            names.append(coauthor["displayName"])
    return names


def post_urls(post: dict) -> dict:
    """Canonical LessWrong URL, plus the Alignment Forum URL when crossposted."""
    path = f"/posts/{post['_id']}/{post.get('slug', '')}"
    urls = {"lesswrong": "https://www.lesswrong.com" + path}
    if post.get("af"):
        urls["alignment_forum"] = "https://www.alignmentforum.org" + path
    return urls


def post_text(post: dict) -> str:
    return html_to_text(((post.get("contents") or {}).get("html")) or "")


def source_bundle(url: str, *, refresh: bool = False, offline: bool = False) -> dict:
    """Everything a contributor needs from a source URL: metadata and plain text.

    The text is returned to the caller and lives in the cache only. It must
    never be written into the repository.
    """
    post_id = post_id_from_url(url)
    if not post_id:
        raise ValueError(f"not a LessWrong / Alignment Forum post URL: {url}")
    post = fetch_post(post_id, refresh=refresh, offline=offline)
    urls = post_urls(post)
    return {
        "post_id": post_id,
        "title": post.get("title"),
        "authors": post_authors(post),
        "published": (post.get("postedAt") or "")[:10],
        "lw_tags": [tag["name"] for tag in post.get("tags") or []],
        "url_lesswrong": urls["lesswrong"],
        "url_alignment_forum": urls.get("alignment_forum"),
        "is_alignment_forum_crosspost": bool(post.get("af")),
        "word_count": (post.get("contents") or {}).get("wordCount"),
        "text": post_text(post),
    }


# --------------------------------------------------------------------------
# Search and tags (scouting)
# --------------------------------------------------------------------------


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def search_posts(query: str, *, page: int = 0, hits_per_page: int = 20, refresh: bool = False) -> list[dict]:
    """Full-text post search (the site's own search endpoint). Query is used as given."""

    def fetch() -> list[dict]:
        payload = _post_json(
            SEARCH_URL,
            [{"indexName": SEARCH_INDEX, "params": {"query": query, "hitsPerPage": hits_per_page, "page": page}}],
        )
        if not isinstance(payload, list) or not payload:
            raise SourceUnreachable(f"search '{query}': unexpected response")
        return payload[0].get("hits") or []

    name = f"{_slugify(query)}-p{page}-n{hits_per_page}.json"
    return _cached(cache_dir() / "search" / name, fetch, refresh=refresh)


_TAG_QUERY = """
query Tag($slug: String) {
  tags(input: {terms: {view: "tagBySlug", slug: $slug}}) {
    results { _id name slug postCount }
  }
}
"""

_TAG_POSTS_QUERY = """
query TagPosts($tagId: String, $limit: Int, $offset: Int) {
  posts(input: {terms: {view: "tagRelevance", tagId: $tagId, limit: $limit, offset: $offset}}) {
    results {
      _id title slug postedAt baseScore af
      user { displayName slug }
      tags { name slug }
      contents { wordCount plaintextDescription }
    }
  }
}
"""


def tag_by_slug(slug: str, *, refresh: bool = False) -> dict | None:
    def fetch() -> dict | None:
        payload = _post_json(GRAPHQL_URL, {"query": _TAG_QUERY, "variables": {"slug": slug}})
        results = ((payload.get("data") or {}).get("tags") or {}).get("results") or []
        return results[0] if results else None

    return _cached(cache_dir() / "tags" / f"{slug}.json", fetch, refresh=refresh)


def posts_by_tag(tag_id: str, *, limit: int = 50, offset: int = 0, refresh: bool = False) -> list[dict]:
    def fetch() -> list[dict]:
        payload = _post_json(
            GRAPHQL_URL,
            {"query": _TAG_POSTS_QUERY, "variables": {"tagId": tag_id, "limit": limit, "offset": offset}},
        )
        if payload.get("errors"):
            raise SourceUnreachable(f"tag posts {tag_id}: {str(payload['errors'])[:300]}")
        return ((payload.get("data") or {}).get("posts") or {}).get("results") or []

    return _cached(cache_dir() / "tagposts" / f"{tag_id}-o{offset}-n{limit}.json", fetch, refresh=refresh)


# --------------------------------------------------------------------------
# Text handling
# --------------------------------------------------------------------------

_BLOCK_TAGS = {
    "p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6",
    "blockquote", "tr", "table", "pre", "section", "figure", "figcaption", "hr", "td", "th",
}
_SKIP_TAGS = {"script", "style"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skip_depth:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    """Plain text of an HTML body: block tags become line breaks, scripts and styles are dropped."""
    parser = _TextExtractor()
    parser.feed(html or "")
    parser.close()
    text = html_lib.unescape("".join(parser.parts))
    text = re.sub(r"[ \t\r\f\v ]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


_CHAR_MAP = str.maketrans(
    {
        "‘": "'", "’": "'", "‚": "'", "‛": "'",
        "“": '"', "”": '"', "„": '"', "‟": '"',
        "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "−": "-",
        " ": " ", "​": "", "‌": "", "‍": "", "﻿": "", "­": "",
    }
)


def normalize_for_quote(text: str) -> str:
    """Normalization applied to both quote and source before the verbatim check.

    Only typography is folded (curly quotes, dash variants, invisible characters,
    runs of whitespace). Words, order, case and punctuation must match.
    """
    text = unicodedata.normalize("NFKC", text or "").translate(_CHAR_MAP)
    return re.sub(r"\s+", " ", text).strip()


def quote_in_text(quote: str, text: str) -> bool:
    needle = normalize_for_quote(quote)
    return bool(needle) and needle in normalize_for_quote(text)


def word_count(text: str) -> int:
    return len((text or "").split())
