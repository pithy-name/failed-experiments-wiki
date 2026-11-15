"""Core library of the failed-experiments wiki.

Everything else is a thin wrapper around this module: the validator CLI
(tools/validate.py), the general CLI (tools/cli.py), the MCP server
(plugin/mcp/server.py), the site builder and the database builder.

An entry is one Markdown file in entries/: YAML front matter (all schema
fields) plus an optional free-text body.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator

import lw

REPO_ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = REPO_ROOT / "entries"
SCHEMA_PATH = REPO_ROOT / "schema" / "entry.schema.json"
TOOL_VERSION = "0.2"
PLACEHOLDER_HANDLE = "HANDLE-TBD"
MAX_QUOTE_WORDS = 15

# Order of top-level keys when an entry is written to disk.
KEY_ORDER = [
    "id", "title", "research_area", "hypothesis", "claim_scope", "method", "models", "benchmarks",
    "result", "failure_type", "confidence_true_negative", "checks_done", "limitations",
    "revival_conditions", "retry_welcome", "evidence_level", "source", "contributor", "review",
    "dates", "related", "info_hazard",
]
NESTED_ORDER = {
    "result": ["direction", "effect_size", "ci_low", "ci_high", "n"],
    "source": ["type", "url", "crosspost_url", "title", "authors", "published", "section", "quote", "lw_tags"],
    "contributor": ["type", "handle", "agent_model", "tool", "note"],
    "review": ["status", "reviewers"],
    "dates": ["experiment", "created", "updated"],
}

# The field catalogue: every schema field, with how it is filtered.
#   enum / list / bool -> facet;  number / date -> range;  text -> full-text search;
#   string -> facet (short free strings such as handles and model names).
# tests/test_wikilib.py checks that this covers every leaf of the JSON Schema.
FIELDS: list[tuple[str, str]] = [
    ("id", "string"),
    ("title", "text"),
    ("research_area", "list"),
    ("hypothesis", "text"),
    ("claim_scope", "text"),
    ("method", "list"),
    ("models.name", "list"),
    ("models.developer", "list"),
    ("models.version", "list"),
    ("models.size", "list"),
    ("models.access", "list"),
    ("benchmarks", "list"),
    ("result.direction", "enum"),
    ("result.effect_size", "number"),
    ("result.ci_low", "number"),
    ("result.ci_high", "number"),
    ("result.n", "number"),
    ("failure_type", "enum"),
    ("confidence_true_negative", "enum"),
    ("checks_done", "list"),
    ("limitations", "text"),
    ("revival_conditions", "text"),
    ("retry_welcome", "bool"),
    ("evidence_level", "enum"),
    ("source.type", "enum"),
    ("source.url", "string"),
    ("source.crosspost_url", "string"),
    ("source.lw_tags", "list"),
    ("source.title", "text"),
    ("source.authors", "list"),
    ("source.published", "date"),
    ("source.section", "text"),
    ("source.quote", "text"),
    ("contributor.type", "enum"),
    ("contributor.handle", "string"),
    ("contributor.agent_model", "string"),
    ("contributor.tool", "string"),
    ("contributor.note", "text"),
    ("review.status", "enum"),
    ("review.reviewers.handle", "list"),
    ("review.reviewers.type", "list"),
    ("review.reviewers.date", "list"),
    ("review.reviewers.notes", "text"),
    ("review.reviewers.agent_model", "list"),
    ("dates.experiment", "date"),
    ("dates.created", "date"),
    ("dates.updated", "date"),
    ("related.id", "list"),
    ("related.relation", "list"),
    ("info_hazard", "enum"),
]
FACET_KINDS = {"enum", "list", "bool", "string"}
RANGE_KINDS = {"number", "date"}
TEXT_KINDS = {"text"}

RETRY_FAILURE_TYPES = {"underpowered", "implementation_bug_suspected", "measurement_noise", "hyperparams_unexplored"}


class EntryError(Exception):
    """An entry file could not be read as front matter + body."""


@dataclass
class Entry:
    data: dict
    body: str = ""
    path: Path | None = None

    @property
    def id(self) -> str:
        return str(self.data.get("id", ""))


@dataclass
class Issue:
    level: str  # "error" or "warning"
    code: str
    message: str
    entry_id: str = ""
    path: str = ""

    def as_dict(self) -> dict:
        return {"level": self.level, "code": self.code, "message": self.message, "entry_id": self.entry_id, "path": self.path}

    def __str__(self) -> str:
        where = self.path or self.entry_id or "?"
        return f"{self.level.upper()} [{self.code}] {where}: {self.message}"


# --------------------------------------------------------------------------
# Reading and writing entries
# --------------------------------------------------------------------------

_FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n(.*))?\Z", re.DOTALL)


def _normalize(value: Any) -> Any:
    """YAML gives date objects for bare dates; the schema works on ISO strings."""
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value


def normalize_data(data: dict) -> dict:
    data = _normalize(data)
    result = data.get("result")
    # A bare `direction: null` in YAML parses to None. The schema value is the string "null".
    if isinstance(result, dict) and "direction" in result and result["direction"] is None:
        result["direction"] = "null"
    return data


def parse_entry_text(text: str) -> tuple[dict, str]:
    match = _FRONT_MATTER_RE.match(text.lstrip("﻿"))
    if not match:
        raise EntryError("file does not start with YAML front matter delimited by '---' lines")
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise EntryError(f"front matter is not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise EntryError("front matter must be a YAML mapping")
    return normalize_data(data), (match.group(2) or "").strip()


def load_entry(path: Path) -> Entry:
    data, body = parse_entry_text(Path(path).read_text(encoding="utf-8"))
    return Entry(data=data, body=body, path=Path(path))


def load_entries(entries_dir: Path | None = None) -> list[Entry]:
    """All readable entries, sorted by ID. Unreadable files are skipped (the validator reports them)."""
    entries = []
    for path in sorted(Path(entries_dir or ENTRIES_DIR).glob("*.md")):
        try:
            entries.append(load_entry(path))
        except EntryError:
            continue
    return sorted(entries, key=lambda entry: entry.id)


def _ordered(data: dict, order: list[str]) -> dict:
    out = {key: data[key] for key in order if key in data}
    out.update({key: value for key, value in data.items() if key not in out})
    return out


def dump_entry(data: dict, body: str = "") -> str:
    """Entry file text with a stable key order, so diffs stay small and readable."""
    ordered = _ordered(normalize_data(data), KEY_ORDER)
    for key, order in NESTED_ORDER.items():
        if isinstance(ordered.get(key), dict):
            ordered[key] = _ordered(ordered[key], order)
    front = yaml.safe_dump(ordered, sort_keys=False, allow_unicode=True, width=100, default_flow_style=False)
    text = f"---\n{front}---\n"
    if body.strip():
        text += f"\n{body.strip()}\n"
    return text


def normalize_tag(tag: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(tag).lower()).strip("-")


def badges(data: dict) -> list[str]:
    """Badge rules from PRD section 6. Badges are derived, never stored."""
    out = []
    if (data.get("contributor") or {}).get("type") == "agent":
        out.append("agent-written")
    status = (data.get("review") or {}).get("status")
    if status in {"unreviewed", "contested", "superseded"}:
        out.append(status)
    if data.get("retry_welcome") is True:
        out.append("retry-welcome")
    return out


# --------------------------------------------------------------------------
# Field access
# --------------------------------------------------------------------------


def get_values(data: Any, dotted: str) -> list:
    """All values at a dotted path, descending into lists. Missing -> []."""
    current = [data]
    for part in dotted.split("."):
        following = []
        for item in current:
            if isinstance(item, dict) and part in item:
                value = item[part]
                following.extend(value if isinstance(value, list) else [value])
        current = following
    return [value for value in current if value is not None]


def facets(entries: Iterable[Entry]) -> dict:
    """Counts per value for facet fields, and min/max for range fields."""
    entries = list(entries)
    out: dict[str, Any] = {"total_entries": len(entries), "facets": {}, "ranges": {}, "text_fields": []}
    for path, kind in FIELDS:
        if kind in FACET_KINDS:
            counts: dict[str, int] = {}
            for entry in entries:
                for value in {_facet_key(v) for v in get_values(entry.data, path)}:
                    counts[value] = counts.get(value, 0) + 1
            out["facets"][path] = dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))
        elif kind in RANGE_KINDS:
            values = [v for entry in entries for v in get_values(entry.data, path)]
            out["ranges"][path] = {"min": min(values), "max": max(values)} if values else None
        else:
            out["text_fields"].append(path)
    badge_counts: dict[str, int] = {}
    for entry in entries:
        for badge in badges(entry.data):
            badge_counts[badge] = badge_counts.get(badge, 0) + 1
    out["facets"]["badges"] = badge_counts
    return out


def _facet_key(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


# --------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------

_STOPWORDS = set(
    "a an and are as at be by for from has have i in is it its of on or that the their this to was we were what "
    "with want run running try trying does do did not no can could would should will my our your which how when "
    "experiment experiments people tried went wrong avoid".split()
)
_SEARCH_WEIGHTS = [
    ("title", 3), ("method", 3), ("research_area", 3), ("benchmarks", 3), ("models.name", 3),
    ("hypothesis", 2), ("claim_scope", 2), ("source.title", 2), ("source.lw_tags", 2), ("checks_done", 2),
    ("limitations", 1), ("revival_conditions", 1), ("failure_type", 1), ("result.direction", 1),
    ("models.developer", 1), ("source.authors", 1), ("source.quote", 1), ("source.section", 1),
    ("contributor.note", 1), ("review.reviewers.notes", 1),
]


def tokenize(text: str) -> list[str]:
    tokens = []
    for raw in re.findall(r"[a-z0-9]+", str(text).lower()):
        if raw in _STOPWORDS:
            continue
        if len(raw) > 3 and raw.endswith("s") and not raw.endswith("ss"):
            raw = raw[:-1]
        tokens.append(raw)
    return tokens


def _token_match(query_token: str, field_token: str) -> bool:
    if query_token == field_token:
        return True
    shorter, longer = sorted((query_token, field_token), key=len)
    return len(shorter) >= 4 and longer.startswith(shorter)


def score_entry(entry: Entry, query_tokens: list[str]) -> tuple[int, list[str]]:
    """Keyword score and the query tokens that matched. Plain and transparent on purpose."""
    score = 0
    matched: set[str] = set()
    field_tokens = [
        (weight, tokenize(" ".join(str(v) for v in get_values(entry.data, path)))) for path, weight in _SEARCH_WEIGHTS
    ]
    field_tokens.append((1, tokenize(entry.body)))
    for token in query_tokens:
        for weight, tokens in field_tokens:
            if any(_token_match(token, candidate) for candidate in tokens):
                score += weight
                matched.add(token)
    return score, sorted(matched)


def matches_filters(data: dict, filters: dict | None) -> bool:
    """Filters: {"field.path": value-or-list} matches any listed value (case-insensitive);
    {"field.path_min": x} / {"field.path_max": x} are inclusive ranges for numbers and dates;
    {"badges": "unreviewed"} filters on derived badges; {"text": "words"} requires every word somewhere."""
    for key, wanted in (filters or {}).items():
        if wanted is None or wanted == "" or wanted == []:
            continue
        if key == "badges":
            have = set(badges(data))
            if not have.intersection(_as_list(wanted)):
                return False
            continue
        if key.endswith("_min") or key.endswith("_max"):
            path, bound = key[:-4], key[-3:]
            values = get_values(data, path)
            if not values:
                return False
            try:
                ok = any((_comparable(v) >= _comparable(wanted)) if bound == "min" else (_comparable(v) <= _comparable(wanted)) for v in values)
            except TypeError:
                ok = False
            if not ok:
                return False
            continue
        have_values = {_facet_key(v).lower() for v in get_values(data, key)}
        if not have_values.intersection(_facet_key(w).lower() for w in _as_list(wanted)):
            return False
    return True


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else [value]


def _comparable(value: Any) -> Any:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = str(value)
    try:
        return float(text)
    except ValueError:
        return text


def summarize(entry: Entry) -> dict:
    data = entry.data
    return {
        "id": entry.id,
        "title": data.get("title"),
        "research_area": data.get("research_area"),
        "method": data.get("method"),
        "models": [m.get("name") for m in data.get("models") or [] if isinstance(m, dict)],
        "result_direction": (data.get("result") or {}).get("direction"),
        "failure_type": data.get("failure_type"),
        "confidence_true_negative": data.get("confidence_true_negative"),
        "retry_welcome": data.get("retry_welcome"),
        "evidence_level": data.get("evidence_level"),
        "review_status": (data.get("review") or {}).get("status"),
        "contributor_type": (data.get("contributor") or {}).get("type"),
        "badges": badges(data),
        "source_url": (data.get("source") or {}).get("url"),
    }


def search(entries: Iterable[Entry], query: str = "", filters: dict | None = None, limit: int = 20) -> dict:
    """Keyword search plus field filters. An empty query lists everything that passes the filters."""
    entries = list(entries)
    query_tokens = tokenize(query or "")
    results = []
    for entry in entries:
        if not matches_filters(entry.data, filters):
            continue
        score, matched = score_entry(entry, query_tokens) if query_tokens else (0, [])
        if query_tokens and score == 0:
            continue
        summary = summarize(entry)
        summary["score"] = score
        summary["matched_terms"] = matched
        results.append(summary)
    results.sort(key=lambda item: (-item["score"], item["id"]))
    return {
        "query": query,
        "query_terms": query_tokens,
        "filters": filters or {},
        "total_entries_in_wiki": len(entries),
        "match_count": len(results),
        "results": results[:limit],
        "note": "Keyword match only, ranked: an entry is listed when it contains ANY of the query terms, so check "
        "matched_terms and score; a hit on one common word is a weak match, not a finding. No match here means no entry "
        "uses these words, not that nothing related exists: retry with synonyms and with filters from list_facets before "
        "concluding 'not found'.",
    }


def find_entry(entries: Iterable[Entry], entry_id: str) -> Entry | None:
    for entry in entries:
        if entry.id == entry_id:
            return entry
    return None


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------

_schema_cache: dict | None = None


def load_schema() -> dict:
    global _schema_cache
    if _schema_cache is None:
        with SCHEMA_PATH.open(encoding="utf-8") as handle:
            _schema_cache = json.load(handle)
    return _schema_cache


def _schema_issue(error, entry_id: str, file_path: str) -> Issue:
    location = ".".join(str(part) for part in error.absolute_path) or "(top level)"
    code = "schema"
    if error.validator == "enum":
        code = "closed_list"
    elif error.validator == "required" and "'url'" in error.message and location == "source":
        code = "source_url"
    elif error.validator == "required" and "'source'" in error.message:
        code = "source_url"
    message = f"{location}: {error.message}"
    if len(message) > 300:
        message = message[:300] + "…"
    return Issue("error", code, message, entry_id, file_path)


def validate_data(data: dict, *, file_name: str | None = None, quote_mode: str = "online", path: str = "") -> list[Issue]:
    """Validate one entry's front matter.

    quote_mode:
      "online"  - fetch the source (cache first); unreachable source is a warning (PRD 5.6)
      "strict"  - as online, but an unreachable source is an error
      "cached"  - use the cache only, never the network; missing cache is a warning
      "skip"    - do not check the quote against the source (a warning says so)
    """
    entry_id = str(data.get("id", "")) if isinstance(data, dict) else ""
    issues: list[Issue] = []
    validator = Draft202012Validator(load_schema())
    for error in sorted(validator.iter_errors(data), key=lambda e: [str(p) for p in e.absolute_path]):
        issues.append(_schema_issue(error, entry_id, path))

    if file_name is not None and entry_id and Path(file_name).stem != entry_id:
        issues.append(Issue("error", "id_filename", f"file name '{file_name}' does not match id '{entry_id}'", entry_id, path))

    source = data.get("source") if isinstance(data.get("source"), dict) else {}
    quote = source.get("quote")
    if isinstance(quote, str) and lw.word_count(quote) > MAX_QUOTE_WORDS:
        issues.append(
            Issue("error", "quote_length", f"source.quote has {lw.word_count(quote)} words; the limit is {MAX_QUOTE_WORDS}", entry_id, path)
        )

    dates = data.get("dates") if isinstance(data.get("dates"), dict) else {}
    if isinstance(dates.get("created"), str) and isinstance(dates.get("updated"), str) and dates["updated"] < dates["created"]:
        issues.append(Issue("error", "dates_order", "dates.updated is earlier than dates.created", entry_id, path))

    result = data.get("result") if isinstance(data.get("result"), dict) else {}
    low, high = result.get("ci_low"), result.get("ci_high")
    if isinstance(low, (int, float)) and isinstance(high, (int, float)) and low > high:
        issues.append(Issue("error", "ci_order", "result.ci_low is greater than result.ci_high", entry_id, path))

    review = data.get("review") if isinstance(data.get("review"), dict) else {}
    if review.get("status") in {"reviewed", "contested"} and not review.get("reviewers"):
        issues.append(
            Issue("error", "review_without_reviewer", f"review.status is '{review.get('status')}' but review.reviewers is empty", entry_id, path)
        )

    for item in data.get("related") or []:
        if isinstance(item, dict) and item.get("id") == entry_id:
            issues.append(Issue("error", "related_self", "related lists the entry itself", entry_id, path))

    has_source_problem = any(i.code in {"source_url"} or i.message.startswith("source") for i in issues if i.level == "error")
    if isinstance(quote, str) and quote.strip() and isinstance(source.get("url"), str) and not has_source_problem:
        issues.extend(check_quote(source["url"], quote, quote_mode, entry_id, path))
    return issues


def check_quote(url: str, quote: str, quote_mode: str, entry_id: str = "", path: str = "") -> list[Issue]:
    if quote_mode == "skip":
        return [Issue("warning", "quote_unchecked", "quote was not checked against the source (quote check skipped)", entry_id, path)]
    post_id = lw.post_id_from_url(url)
    if not post_id:
        return [Issue("error", "source_url", f"source.url is not a LessWrong / Alignment Forum post URL: {url}", entry_id, path)]
    try:
        post = lw.fetch_post(post_id, offline=(quote_mode == "cached"))
    except lw.SourceUnreachable as exc:
        level = "error" if quote_mode == "strict" else "warning"
        return [Issue(level, "source_unreachable", f"could not fetch the source, so the quote is unchecked ({str(exc)[:160]})", entry_id, path)]
    if not lw.quote_in_text(quote, lw.post_text(post)):
        return [Issue("error", "quote_not_found", "source.quote does not appear verbatim in the source text", entry_id, path)]
    return []


def validate_paths(paths: list[Path], *, quote_mode: str = "online", allow_gold_status: bool = False) -> list[Issue]:
    """Validate entry files, including checks across files (unique IDs, related IDs exist)."""
    issues: list[Issue] = []
    seen: dict[str, str] = {}
    loaded: list[Entry] = []
    for path in paths:
        try:
            entry = load_entry(path)
        except (EntryError, OSError, UnicodeDecodeError) as exc:
            issues.append(Issue("error", "unreadable", str(exc), "", str(path)))
            continue
        data = dict(entry.data)
        if allow_gold_status:
            status = data.pop("gold_status", None)
            if status not in {"pending_maintainer_verification", "verified"}:
                issues.append(
                    Issue("error", "gold_status", "gold file needs gold_status: pending_maintainer_verification or verified", entry.id, str(path))
                )
        issues.extend(validate_data(data, file_name=path.name, quote_mode=quote_mode, path=str(path)))
        if entry.id:
            if entry.id in seen:
                issues.append(Issue("error", "duplicate_id", f"id '{entry.id}' is also used by {seen[entry.id]}", entry.id, str(path)))
            else:
                seen[entry.id] = str(path)
        loaded.append(entry)
    for entry in loaded:
        for item in entry.data.get("related") or []:
            if isinstance(item, dict) and item.get("id") and item["id"] not in seen:
                issues.append(Issue("warning", "related_missing", f"related id '{item['id']}' is not in the validated set", entry.id, str(entry.path)))
    return issues


def has_errors(issues: Iterable[Issue]) -> bool:
    return any(issue.level == "error" for issue in issues)


# --------------------------------------------------------------------------
# Git plumbing (write path)
# --------------------------------------------------------------------------


class GitError(Exception):
    pass


def git(repo: Path, *args: str, env: dict | None = None, input_text: str | None = None, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        input=input_text,
        env={**os.environ, **(env or {})},
        check=False,
    )
    if check and completed.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {completed.stderr.strip() or completed.stdout.strip()}")
    return completed.stdout.strip()


def is_git_repo(repo: Path) -> bool:
    try:
        return git(repo, "rev-parse", "--is-inside-work-tree") == "true"
    except (GitError, OSError):
        return False


def remote_url(repo: Path) -> str | None:
    try:
        return git(repo, "remote", "get-url", "origin") or None
    except (GitError, OSError):
        return None


def branch_exists(repo: Path, branch: str) -> bool:
    return bool(git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}", check=False))


def read_file_at(repo: Path, ref: str, rel_path: str) -> str | None:
    completed = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{rel_path}"], capture_output=True, text=True, check=False)
    return completed.stdout if completed.returncode == 0 else None


def with_trailer(message: str) -> str:
    """Append the lines in FEWIKI_COMMIT_TRAILER (e.g. Co-Authored-By) to a commit message."""
    trailer = os.environ.get("FEWIKI_COMMIT_TRAILER", "").strip()
    return f"{message.rstrip()}\n\n{trailer}\n" if trailer else message


def commit_file_on_new_branch(repo: Path, branch: str, rel_path: str, content: str, message: str, base: str = "main") -> str:
    """Create `branch` from `base` with one commit that adds or replaces `rel_path`.

    Uses git plumbing with a temporary index, so the working tree and the
    checked-out branch are left exactly as they were.
    """
    message = with_trailer(message)
    if branch_exists(repo, branch):
        raise GitError(f"branch '{branch}' already exists")
    base_sha = git(repo, "rev-parse", "--verify", f"{base}^{{commit}}")
    with tempfile.TemporaryDirectory() as tmp:
        env = {"GIT_INDEX_FILE": str(Path(tmp) / "index")}
        git(repo, "read-tree", base_sha, env=env)
        blob = git(repo, "hash-object", "-w", "--stdin", input_text=content)
        git(repo, "update-index", "--add", "--cacheinfo", f"100644,{blob},{rel_path}", env=env)
        tree = git(repo, "write-tree", env=env)
    commit = git(repo, "commit-tree", tree, "-p", base_sha, "-m", message)
    git(repo, "update-ref", f"refs/heads/{branch}", commit, "")
    return commit


def open_pull_request(repo: Path, branch: str, title: str, body: str, base: str = "main") -> dict:
    """Push the branch and open a pull request with gh. Without a remote, say so plainly."""
    if not remote_url(repo):
        return {
            "pull_request": None,
            "status": "branch_only_no_remote",
            "detail": f"No git remote is configured, so no pull request was opened. The change is committed on local branch "
            f"'{branch}'. Merge it locally with: python tools/cli.py merge-local {branch}",
        }
    try:
        git(repo, "push", "--set-upstream", "origin", branch)
    except GitError as exc:
        return {"pull_request": None, "status": "push_failed", "detail": str(exc)[:400]}
    completed = subprocess.run(
        ["gh", "pr", "create", "--base", base, "--head", branch, "--title", title, "--body", body],
        capture_output=True, text=True, cwd=str(repo), check=False,
    )
    if completed.returncode != 0:
        return {"pull_request": None, "status": "pushed_pr_failed", "detail": completed.stderr.strip()[:400]}
    return {"pull_request": completed.stdout.strip().splitlines()[-1], "status": "pull_request_opened", "detail": ""}


def resolve_handle() -> str:
    """GitHub handle of whoever runs the tool: FEWIKI_HANDLE, else the gh login, else a visible placeholder."""
    handle = os.environ.get("FEWIKI_HANDLE", "").strip()
    if handle:
        return handle
    try:
        completed = subprocess.run(["gh", "api", "user", "-q", ".login"], capture_output=True, text=True, timeout=15, check=False)
        if completed.returncode == 0 and completed.stdout.strip():
            return completed.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return PLACEHOLDER_HANDLE


def _ids_in_use(repo: Path, entries_dir: Path) -> set[str]:
    """IDs on disk plus IDs reserved by entry/ branches (open or local pull requests)."""
    used = {path.stem for path in entries_dir.glob("fe-*.md")}
    if is_git_repo(repo):
        refs = git(repo, "for-each-ref", "--format=%(refname)", "refs/heads/entry", "refs/remotes/origin/entry", check=False)
        used.update(re.findall(r"fe-\d{4}-\d{4}", refs))
        listing = git(repo, "ls-tree", "--name-only", "main", "entries/", check=False)
        used.update(re.findall(r"fe-\d{4}-\d{4}", listing))
    return used


def next_id(repo: Path | None = None, entries_dir: Path | None = None, year: int | None = None) -> str:
    repo = repo or REPO_ROOT
    entries_dir = entries_dir or (repo / "entries")
    year = year or dt.date.today().year
    numbers = [int(used[8:]) for used in _ids_in_use(repo, entries_dir) if used.startswith(f"fe-{year}-")]
    return f"fe-{year}-{(max(numbers) + 1 if numbers else 1):04d}"


# --------------------------------------------------------------------------
# Write operations (used by submit_entry / review_entry)
# --------------------------------------------------------------------------


def prepare_new_entry(data: dict, *, repo: Path, contributor_type: str, handle: str | None = None,
                      agent_model: str | None = None, tool: str | None = None) -> dict:
    """Fill the fields the system owns. The submitter never sets its own trust fields:
    ID, contributor, review status and dates are assigned here."""
    data = normalize_data(json.loads(json.dumps(data)))
    today = dt.date.today().isoformat()
    data["id"] = next_id(repo)
    for key in ("method", "checks_done"):
        if isinstance(data.get(key), list):
            data[key] = list(dict.fromkeys(normalize_tag(tag) for tag in data[key] if normalize_tag(tag)))
    note = (data.get("contributor") or {}).get("note") if isinstance(data.get("contributor"), dict) else None
    contributor: dict[str, Any] = {"type": contributor_type, "handle": handle or resolve_handle()}
    if contributor_type == "agent":
        contributor["agent_model"] = agent_model or "unknown"
        contributor["tool"] = tool or f"submit_entry v{TOOL_VERSION}"
    if note:
        contributor["note"] = note
    data["contributor"] = contributor
    data["review"] = {"status": "unreviewed"}
    experiment = (data.get("dates") or {}).get("experiment") if isinstance(data.get("dates"), dict) else None
    data["dates"] = {"created": today, "updated": today}
    if experiment:
        data["dates"]["experiment"] = experiment
    data.setdefault("info_hazard", "none")
    return data


def submit_entry(data: dict, body: str = "", *, repo: Path | None = None, contributor_type: str = "agent",
                 handle: str | None = None, agent_model: str | None = None, tool: str | None = None,
                 quote_mode: str = "online") -> dict:
    """Validate a new entry, commit it on a new branch and open a pull request.

    Nothing is written unless validation passes. Entries flagged info_hazard: review_needed
    are still submitted, but the pull request says a human must look before merge.
    """
    repo = Path(repo or REPO_ROOT)
    prepared = prepare_new_entry(data, repo=repo, contributor_type=contributor_type, handle=handle, agent_model=agent_model, tool=tool)
    entry_id = prepared["id"]
    issues = validate_data(prepared, file_name=f"{entry_id}.md", quote_mode=quote_mode)
    if has_errors(issues):
        return {"ok": False, "id": None, "status": "rejected_by_validation", "issues": [i.as_dict() for i in issues]}
    quote_checked = not any(i.code in {"quote_unchecked", "source_unreachable"} for i in issues)
    contributor = prepared["contributor"]
    who = f"{contributor['type']} {contributor['handle']}"
    if contributor["type"] == "agent":
        who += f" ({contributor['agent_model']}, {contributor['tool']})"
    message = (
        f"Add entry {entry_id}: {prepared['title']}\n\n"
        f"Source: {prepared['source']['url']}\n"
        f"Contributor: {who}\n"
        f"Review status: unreviewed\n"
        f"Validation: schema passed; quote {'found in source' if quote_checked else 'NOT checked (source unreachable)'}\n"
    )
    branch = f"entry/{entry_id}"
    commit = commit_file_on_new_branch(repo, branch, f"entries/{entry_id}.md", dump_entry(prepared, body), message)
    pr_body = (
        f"New entry `{entry_id}` from {who}.\n\n- Source: {prepared['source']['url']}\n"
        f"- Quote check: {'passed' if quote_checked else 'not run (source unreachable)'}\n"
        f"- Info hazard flag: `{prepared.get('info_hazard')}`\n\nMerging publishes the entry with its badges. Review is a separate step."
    )
    pr = open_pull_request(repo, branch, f"Add entry {entry_id}: {prepared['title']}"[:240], pr_body)
    return {
        "ok": True, "id": entry_id, "branch": branch, "commit": commit, "file": f"entries/{entry_id}.md",
        "badges": badges(prepared), "quote_checked": quote_checked, **pr,
        "issues": [i.as_dict() for i in issues],
    }


def review_entry(entry_id: str, status: str, notes: str, *, repo: Path | None = None, reviewer_type: str = "agent",
                 handle: str | None = None, agent_model: str | None = None, quote_mode: str = "online") -> dict:
    """Record a review: set review.status, append the reviewer, commit on a new branch, open a pull request.

    The existing entry is never rewritten beyond review.status, review.reviewers and dates.updated.
    """
    repo = Path(repo or REPO_ROOT)
    if status not in {"reviewed", "contested", "superseded", "unreviewed"}:
        return {"ok": False, "status": "invalid_status", "detail": "status must be reviewed, contested, superseded or unreviewed"}
    rel_path = f"entries/{entry_id}.md"
    text = read_file_at(repo, "main", rel_path)
    if text is None:
        return {"ok": False, "status": "not_found", "detail": f"{rel_path} does not exist on main"}
    data, body = parse_entry_text(text)
    today = dt.date.today().isoformat()
    previous = (data.get("review") or {}).get("status")
    reviewer: dict[str, Any] = {"handle": handle or resolve_handle(), "type": reviewer_type, "date": today, "notes": notes}
    if reviewer_type == "agent":
        reviewer["agent_model"] = agent_model or "unknown"
    review = dict(data.get("review") or {})
    review["status"] = status
    review["reviewers"] = list(review.get("reviewers") or []) + [reviewer]
    data["review"] = review
    data.setdefault("dates", {})["updated"] = today
    issues = validate_data(data, file_name=f"{entry_id}.md", quote_mode=quote_mode)
    if has_errors(issues):
        return {"ok": False, "status": "rejected_by_validation", "issues": [i.as_dict() for i in issues]}
    stamp = today.replace("-", "")
    branch = f"review/{entry_id}-{stamp}"
    suffix = 2
    while branch_exists(repo, branch):
        branch = f"review/{entry_id}-{stamp}-{suffix}"
        suffix += 1
    who = f"{reviewer_type} {reviewer['handle']}" + (f" ({reviewer['agent_model']})" if reviewer_type == "agent" else "")
    message = (
        f"Review {entry_id}: {previous} -> {status}\n\n"
        f"Reviewer: {who}\nDate: {today}\nNotes: {notes}\n"
    )
    commit = commit_file_on_new_branch(repo, branch, rel_path, dump_entry(data, body), message)
    pr = open_pull_request(repo, branch, f"Review {entry_id}: {previous} -> {status}", f"Reviewer: {who}\n\n{notes}")
    return {
        "ok": True, "id": entry_id, "previous_status": previous, "new_status": status, "branch": branch, "commit": commit,
        "badges": badges(data), **pr, "issues": [i.as_dict() for i in issues],
    }


def merge_local(branch: str, *, repo: Path | None = None, quote_mode: str = "cached") -> dict:
    """Local stand-in for merging a pull request when the repo has no remote.

    Validates every entry as it would be after the merge, then merges with a merge
    commit (--no-ff) so the branch stays visible in history, as a merged pull request would.
    """
    repo = Path(repo or REPO_ROOT)
    if not branch_exists(repo, branch):
        return {"ok": False, "status": "no_such_branch", "detail": branch}
    if git(repo, "rev-parse", "--abbrev-ref", "HEAD") != "main":
        return {"ok": False, "status": "not_on_main", "detail": "check out main before merging"}
    listing = git(repo, "ls-tree", "--name-only", branch, "entries/", check=False).splitlines()
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for rel_path in listing:
            if not rel_path.endswith(".md"):
                continue
            text = read_file_at(repo, branch, rel_path)
            target = Path(tmp) / Path(rel_path).name
            target.write_text(text or "", encoding="utf-8")
            paths.append(target)
        issues = validate_paths(paths, quote_mode=quote_mode)
    if has_errors(issues):
        return {"ok": False, "status": "rejected_by_validation", "issues": [i.as_dict() for i in issues]}
    subject = git(repo, "log", "-1", "--format=%s", branch)
    message = (
        f"Merge {branch}: {subject}\n\n"
        "Local stand-in for merging a pull request (this repository has no remote yet).\n"
        "Validation passed on the merged result before this merge.\n"
    )
    try:
        git(repo, "merge", "--no-ff", "-m", with_trailer(message), branch)
    except GitError as exc:
        return {"ok": False, "status": "merge_failed", "detail": str(exc)[:400]}
    return {"ok": True, "status": "merged_locally", "branch": branch, "merge_commit": git(repo, "rev-parse", "HEAD"),
            "issues": [i.as_dict() for i in issues]}
