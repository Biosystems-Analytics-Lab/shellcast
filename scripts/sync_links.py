#!/usr/bin/env python3
"""Keep the shared external-link registry in sync across the web apps.

Source of truth: web/shared/links.json
Each app (web/shellcast-web-*) gets a committed copy at <app>/links.json so it is
uploaded with that app on `gcloud app deploy`. Each entry is {"name": ..., "url": ...};
templates use `{{ links.<key>.url }}` (and `{{ links.<key>.name }}` for the display name).

Usage:
    python3 scripts/sync_links.py           # copy shared links.json into every app
    python3 scripts/sync_links.py --check   # verify copies match and template keys exist
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / "web" / "shared" / "links.json"
APPS = sorted(p for p in (ROOT / "web").glob("shellcast-web-*") if p.is_dir())

# {{ links.key }} or {{ links['key'] }} / {{ links["key"] }}
KEY_RE = re.compile(r"""\blinks(?:\.([A-Za-z_][A-Za-z0-9_]*)|\[['"]([^'"]+)['"]\])""")


def load_shared():
    """Load web/shared/links.json: {key: {"name": "...", "url": "https://..."}}."""
    with SHARED.open(encoding="utf-8") as f:
        data = json.load(f)
    for key, entry in data.items():
        if not isinstance(entry, dict) or not entry.get("name") or not str(entry.get("url", "")).startswith("http"):
            raise SystemExit(f'error: links.json entry "{key}" must be {{"name": "...", "url": "http..."}}')
    return data


def sync():
    load_shared()  # validate JSON first
    for app in APPS:
        shutil.copyfile(SHARED, app / "links.json")
        print(f"synced {app.name}/links.json")
    return 0


def check():
    errors = []
    shared = load_shared()
    shared_bytes = SHARED.read_bytes()
    used = set()

    for app in APPS:
        copy = app / "links.json"
        if not copy.exists():
            errors.append(f"{app.name}/links.json is missing (run scripts/sync_links.py)")
        elif copy.read_bytes() != shared_bytes:
            errors.append(f"{app.name}/links.json differs from web/shared/links.json (run scripts/sync_links.py)")

        for template in sorted((app / "templates").rglob("*.html")):
            text = template.read_text(encoding="utf-8")
            for match in KEY_RE.finditer(text):
                key = match.group(1) or match.group(2)
                used.add(key)
                if key not in shared:
                    line = text.count("\n", 0, match.start()) + 1
                    errors.append(f"{template.relative_to(ROOT)}:{line}: unknown link key '{key}'")

    for key in sorted(set(shared) - used):
        print(f"warning: link key '{key}' is not used by any template")

    for err in errors:
        print(f"error: {err}", file=sys.stderr)
    if not errors:
        print(f"OK: {len(shared)} links, {len(APPS)} apps in sync")
    return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="verify only; do not modify files")
    args = parser.parse_args()
    return check() if args.check else sync()


if __name__ == "__main__":
    sys.exit(main())
