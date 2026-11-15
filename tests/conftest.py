"""Shared fixtures. Tests never touch the network: sources come from a fake cache."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import lw  # noqa: E402
import wikilib  # noqa: E402

FAKE_POST_ID = "TestPost0000000001"
FAKE_URL = f"https://www.lesswrong.com/posts/{FAKE_POST_ID}/a-test-post"
FAKE_QUOTE = "the steering vector had no measurable effect on refusal rates"
FAKE_HTML = (
    "<h1>A test post</h1><p>We expected a large effect. In the end, "
    "the steering vector had no measurable effect on refusal&nbsp;rates across seeds.</p>"
    "<p>It’s a “null” result — nothing more.</p><script>ignore()</script>"
)

VALID_ENTRY = {
    "id": "fe-2026-0001",
    "title": "Activation steering on GPT-2 small did not change refusal rates",
    "research_area": ["steering"],
    "hypothesis": "Adding a refusal direction to the residual stream raises refusal rates.",
    "claim_scope": "One steering vector, one layer, GPT-2 small, 200 prompts; nothing beyond that was tested.",
    "method": ["activation-steering"],
    "models": [{"name": "GPT-2 small", "developer": "OpenAI", "version": "unknown", "size": "124M", "access": "open-weight"}],
    "benchmarks": ["toy-refusal-set"],
    "result": {"direction": "null", "n": 200},
    "failure_type": "hypothesis_false",
    "confidence_true_negative": "low",
    "checks_done": ["seed-sweep"],
    "limitations": "Only one layer was tried.",
    "revival_conditions": "A sweep over layers and coefficients.",
    "retry_welcome": True,
    "evidence_level": "author_report",
    "source": {
        "type": "lesswrong",
        "url": FAKE_URL,
        "title": "A test post",
        "authors": ["Test Author"],
        "published": "2025-03-01",
        "quote": FAKE_QUOTE,
        "lw_tags": ["Interpretability (ML & AI)"],
    },
    "contributor": {"type": "agent", "handle": "test-handle", "agent_model": "test-model", "tool": "contribute-skill v0.1"},
    "review": {"status": "unreviewed"},
    "dates": {"created": "2026-11-14", "updated": "2026-11-14"},
    "info_hazard": "none",
}


@pytest.fixture
def valid_entry() -> dict:
    return copy.deepcopy(VALID_ENTRY)


@pytest.fixture(autouse=True)
def fake_cache(tmp_path, monkeypatch):
    """Point the source cache at a temp dir holding one fake post, and block the network."""
    cache = tmp_path / "cache"
    (cache / "posts").mkdir(parents=True)
    post = {
        "_id": FAKE_POST_ID, "title": "A test post", "slug": "a-test-post", "postedAt": "2025-03-01T10:00:00.000Z",
        "af": False, "user": {"displayName": "Test Author"}, "coauthors": [], "tags": [{"name": "AI", "slug": "ai"}],
        "contents": {"wordCount": 30, "html": FAKE_HTML},
    }
    (cache / "posts" / f"{FAKE_POST_ID}.json").write_text(json.dumps(post), encoding="utf-8")
    monkeypatch.setenv("FEWIKI_CACHE", str(cache))
    monkeypatch.setenv("FEWIKI_HANDLE", "test-handle")

    def no_network(url, payload):
        raise lw.SourceUnreachable(f"network blocked in tests: {url}")

    monkeypatch.setattr(lw, "_post_json", no_network)
    return cache


def run_git(repo: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True)
    return completed.stdout.strip()


@pytest.fixture
def git_repo(tmp_path, valid_entry):
    """A throwaway repo with one committed entry on main and no remote."""
    repo = tmp_path / "repo"
    (repo / "entries").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True, capture_output=True)
    run_git(repo, "config", "user.email", "test@example.invalid")
    run_git(repo, "config", "user.name", "Test")
    run_git(repo, "config", "commit.gpgsign", "false")
    (repo / "entries" / "fe-2026-0001.md").write_text(wikilib.dump_entry(valid_entry, "Body text."), encoding="utf-8")
    run_git(repo, "add", "entries/fe-2026-0001.md")
    run_git(repo, "commit", "-q", "-m", "Add first entry")
    return repo
