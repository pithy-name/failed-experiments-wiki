"""Mechanical check of the field-support audits (scouting step 4).

The audits are model output, so nothing in them is trusted until checked.
For every audited post this script re-tests the one thing a machine can test:
the proposed quote must be 15 words or fewer and appear verbatim in the cached
post text. It prints one line per post and writes scouting/field_audit/summary.json.

Run:  python tools/scout/check_audit.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import lw  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AUDIT_DIR = REPO_ROOT / "scouting" / "field_audit"
REQUIRED = ["hypothesis", "claim_scope", "method", "models", "result_direction", "failure_type", "quote"]


def main() -> int:
    rows = []
    for path in sorted(AUDIT_DIR.glob("audit-*.json")):
        with path.open(encoding="utf-8") as handle:
            batch = json.load(handle)
        for audit in batch["audits"]:
            fields = audit.get("fields") or {}
            unsupported = [name for name in REQUIRED if not (fields.get(name) or {}).get("supported")]
            quote = (fields.get("quote") or {}).get("value") or ""
            try:
                text = lw.post_text(lw.fetch_post(audit["post_id"], offline=True))
            except lw.SourceUnreachable:
                text = ""
            rows.append(
                {
                    "post_id": audit["post_id"],
                    "title": audit.get("title"),
                    "genuine": audit.get("genuine"),
                    "unsupported_fields": unsupported,
                    "auditor_says_all_supported": bool(audit.get("all_required_supported")),
                    "quote": quote,
                    "quote_words": lw.word_count(quote),
                    "quote_verbatim_in_post": bool(quote) and lw.quote_in_text(quote, text),
                    "result_direction": (fields.get("result_direction") or {}).get("value"),
                    "failure_type": (fields.get("failure_type") or {}).get("value"),
                    "models": (fields.get("models") or {}).get("evidence"),
                    "experiments": audit.get("experiments"),
                    "primary_experiment": audit.get("primary_experiment"),
                    "info_hazard": audit.get("info_hazard"),
                    "notes": audit.get("notes"),
                    "audit_file": path.name,
                    "auditor_model": batch.get("model"),
                }
            )
    for row in rows:
        row["passes_machine_checks"] = bool(
            row["genuine"] in {"yes", "partial"} and not row["unsupported_fields"] and row["quote_verbatim_in_post"]
            and 0 < row["quote_words"] <= 15
        )
        flag = "PASS" if row["passes_machine_checks"] else "FAIL"
        print(
            f"{flag} {row['post_id']} genuine={row['genuine']} unsupported={row['unsupported_fields'] or '-'} "
            f"quote={row['quote_words']}w verbatim={row['quote_verbatim_in_post']} hazard={row['info_hazard']} | {row['title']}"
        )
    with (AUDIT_DIR / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"{sum(r['passes_machine_checks'] for r in rows)} of {len(rows)} audited posts pass the machine checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
