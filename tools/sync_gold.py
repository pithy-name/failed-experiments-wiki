"""Publish verified gold entries into entries/.

The gold entries in evals/gold/ are the ground truth for the evals. Each is
also published as a wiki entry with the same ID. While a gold entry is a model
draft (gold_status: pending_maintainer_verification) its copy in entries/ is labelled
as what it is: written by an agent (contributor.type: agent, with the model),
unreviewed, and carrying a note that it awaits verification.

When the maintainer has checked a gold file against its post and set
`gold_status: verified`, this script copies its content into entries/<id>.md,
drops the "awaiting verification" note, and records the maintainer as the
human reviewer (review.status: reviewed).

  python tools/sync_gold.py --handle <github handle>        (or: make sync-gold HANDLE=...)

It changes files only. Commit them yourself, one entry per commit, so the
verification is visible in git history. Gold files still pending are left alone.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikilib  # noqa: E402

GOLD_DIR = wikilib.REPO_ROOT / "evals" / "gold"


NOTES_HEADING = "## Verification notes for the maintainer"


def public_body(body: str) -> str:
    """The gold file's body without its verification notes, which are for the maintainer only."""
    return body.split(NOTES_HEADING)[0].strip()


def publish_drafts(gold_dir: Path = GOLD_DIR, entries_dir: Path = wikilib.ENTRIES_DIR, quote_mode: str = "online") -> list[dict]:
    """Publish gold entries that are still model drafts, as unreviewed entries that say so.

    Used once, when the gold set was drafted. The copy keeps the draft's contributor block
    (including its 'awaiting verification' note) and is never marked reviewed. An entry file
    that already exists is left alone.
    """
    outcomes = []
    entries_dir.mkdir(parents=True, exist_ok=True)
    for gold_path in sorted(gold_dir.glob("fe-*.md")):
        gold = wikilib.load_entry(gold_path)
        data = dict(gold.data)
        status = data.pop("gold_status", None)
        entry_id = gold_path.stem
        target = entries_dir / f"{entry_id}.md"
        if status != "pending_maintainer_verification":
            outcomes.append({"id": entry_id, "action": "skipped", "reason": f"gold_status is {status!r}"})
            continue
        if target.exists():
            outcomes.append({"id": entry_id, "action": "skipped", "reason": "entry file already exists"})
            continue
        contributor = data.get("contributor") or {}
        if not contributor.get("note"):
            outcomes.append({"id": entry_id, "action": "rejected", "issues": ["a pending gold draft must carry contributor.note saying it awaits verification"]})
            continue
        if contributor.get("type") != "agent" or not contributor.get("agent_model"):
            outcomes.append({"id": entry_id, "action": "rejected", "issues": [
                "a pending gold draft was written by a model, so contributor.type must be agent with agent_model set; "
                "it becomes a person's entry only when the maintainer verifies it (sync)"]})
            continue
        data["review"] = {"status": "unreviewed"}
        issues = wikilib.validate_data(data, file_name=target.name, quote_mode=quote_mode)
        if wikilib.has_errors(issues):
            outcomes.append({"id": entry_id, "action": "rejected", "issues": [str(i) for i in issues if i.level == "error"]})
            continue
        target.write_text(wikilib.dump_entry(data, public_body(gold.body)), encoding="utf-8")
        outcomes.append({"id": entry_id, "action": "published_as_unreviewed_draft", "file": str(target)})
    return outcomes


def sync(handle: str, gold_dir: Path = GOLD_DIR, entries_dir: Path = wikilib.ENTRIES_DIR, quote_mode: str = "online") -> list[dict]:
    today = dt.date.today().isoformat()
    outcomes = []
    for gold_path in sorted(gold_dir.glob("fe-*.md")):
        gold = wikilib.load_entry(gold_path)
        data = dict(gold.data)
        status = data.pop("gold_status", None)
        entry_id = gold_path.stem
        if status != "verified":
            outcomes.append({"id": entry_id, "action": "skipped", "reason": f"gold_status is {status!r}, not 'verified'"})
            continue
        target = entries_dir / f"{entry_id}.md"
        existing = wikilib.load_entry(target) if target.exists() else None
        contributor = dict(data.get("contributor") or {})
        contributor.update(type="human", handle=handle)
        contributor.pop("note", None)
        contributor.pop("agent_model", None)
        contributor.pop("tool", None)
        data["contributor"] = contributor
        reviewers = [r for r in ((existing.data.get("review") or {}).get("reviewers") or [])] if existing else []
        already = any(r.get("handle") == handle and r.get("type") == "human" for r in reviewers)
        if not already:
            reviewers.append({"handle": handle, "type": "human", "date": today,
                              "notes": "Gold entry: every field verified against the source post by the maintainer."})
        data["review"] = {"status": "reviewed", "reviewers": reviewers}
        created = ((existing.data.get("dates") or {}).get("created") if existing else None) or (data.get("dates") or {}).get("created") or today
        dates = dict(data.get("dates") or {})
        dates.update(created=created, updated=today)
        data["dates"] = dates
        issues = wikilib.validate_data(data, file_name=target.name, quote_mode=quote_mode)
        if wikilib.has_errors(issues):
            outcomes.append({"id": entry_id, "action": "rejected", "issues": [str(i) for i in issues if i.level == "error"]})
            continue
        text = wikilib.dump_entry(data, public_body(gold.body))
        if existing and target.read_text(encoding="utf-8") == text:
            outcomes.append({"id": entry_id, "action": "unchanged"})
            continue
        target.write_text(text, encoding="utf-8")
        outcomes.append({"id": entry_id, "action": "published", "file": str(target)})
    return outcomes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handle", default="", help="GitHub handle of the maintainer who verified the gold entries")
    parser.add_argument("--quotes", choices=["online", "strict", "cached", "skip"], default="online")
    parser.add_argument("--drafts", action="store_true",
                        help="publish gold entries that are still model drafts, as unreviewed entries (used once at seeding)")
    args = parser.parse_args(argv)
    if args.drafts:
        outcomes = publish_drafts(quote_mode=args.quotes)
        for outcome in outcomes:
            detail = outcome.get("reason") or "; ".join(outcome.get("issues", [])) or outcome.get("file", "")
            print(f"{outcome['id']}: {outcome['action']} {detail}".rstrip())
        return 1 if any(o["action"] == "rejected" for o in outcomes) else 0
    if not args.handle.strip() or args.handle == wikilib.PLACEHOLDER_HANDLE:
        print("Give your GitHub handle: make sync-gold HANDLE=<handle>", file=sys.stderr)
        return 2
    outcomes = sync(args.handle.strip(), quote_mode=args.quotes)
    for outcome in outcomes:
        detail = outcome.get("reason") or "; ".join(outcome.get("issues", [])) or outcome.get("file", "")
        print(f"{outcome['id']}: {outcome['action']} {detail}".rstrip())
    published = [o["id"] for o in outcomes if o["action"] == "published"]
    if published:
        print("\nNow commit each one, for example:")
        for entry_id in published:
            print(f'  git add entries/{entry_id}.md evals/gold/{entry_id}.md && git commit -m "Verify gold entry {entry_id} against its source post"')
        print("Then: make evals")
    return 1 if any(o["action"] == "rejected" for o in outcomes) else 0


if __name__ == "__main__":
    raise SystemExit(main())
