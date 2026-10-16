#!/usr/bin/env python3
"""install.py - install the document-to-markdown-skill skill into AI coding CLIs.

Installs this skill (SKILL.md + scripts/) into the skills directory of
Claude Code, OpenAI Codex CLI, opencode, pi, and Qoder.

Usage:
    python install.py                 # auto-detect installed CLIs, install into them
    python install.py --target all    # install into every supported CLI
    python install.py --target claude,qoder
    python install.py --list          # show target paths and detection status
    python install.py --link          # symlink one shared copy instead of copying
    python install.py --target-dir "C:/repo/.claude/skills/document-to-markdown-skill"
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
SKILL_NAME = "document-to-markdown-skill"
HOME = Path.home()
IS_WIN = os.name == "nt"

# what gets copied into each skills directory
CONTENT = ["SKILL.md", "scripts", "references", "assets"]


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or (HOME / ".codex"))


TARGETS: dict[str, dict] = {
    "claude": {
        "label": "Claude Code",
        "bases": [HOME / ".claude"],
        "dest": HOME / ".claude" / "skills" / SKILL_NAME,
    },
    "codex": {
        "label": "OpenAI Codex CLI",
        "bases": [codex_home()],
        "dest": codex_home() / "skills" / SKILL_NAME,
    },
    "opencode": {
        "label": "opencode",
        "bases": [HOME / ".config" / "opencode"],
        "dest": HOME / ".config" / "opencode" / "skills" / SKILL_NAME,
    },
    "pi": {
        "label": "pi (shared ~/.agents/skills)",
        "bases": [HOME / ".pi", HOME / ".agents"],
        "dest": HOME / ".agents" / "skills" / SKILL_NAME,
    },
    "qoder": {
        "label": "Qoder",
        "bases": [HOME / ".qoder"],
        "dest": HOME / ".qoder" / "skills" / SKILL_NAME,
    },
}


def detected() -> list[str]:
    return [k for k, t in TARGETS.items() if any(b.exists() for b in t["bases"])]


def print_table() -> None:
    det = detected()
    width = max(len(t["label"]) for t in TARGETS.values())
    for k, t in TARGETS.items():
        mark = "detected" if k in det else "-"
        print(f"  {k:<9} {t['label']:<{width}}  {t['dest']}  [{mark}]")
    print()


def install_to(dest: Path, link: bool, dry: bool) -> bool:
    if link:
        if dry:
            print(f"  would link {dest} -> {REPO}")
            return True
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_symlink():
            dest.unlink()
        elif dest.exists():
            print(f"  ERROR: {dest} already exists (not a symlink); remove it or install without --link")
            return False
        try:
            os.symlink(REPO, dest, target_is_directory=True)
        except OSError as e:
            print(f"  ERROR: symlink failed ({e}). On Windows enable Developer Mode, or install without --link.")
            return False
        print(f"  linked  {dest} -> {REPO}")
        return True

    if dry:
        print(f"  would copy SKILL.md + scripts/ -> {dest}")
        return True
    dest.mkdir(parents=True, exist_ok=True)
    for item in CONTENT:
        src = REPO / item
        if not src.exists():
            continue
        dst = dest / item
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(src, dst)
    print(f"  copied  {dest}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Install the document-to-markdown-skill skill into AI coding CLIs.")
    ap.add_argument("--target", help="comma-separated: claude,codex,opencode,pi,qoder or 'all'")
    ap.add_argument("--target-dir", type=Path,
                    help="install into this exact directory instead (e.g. a project's .claude/skills/document-to-markdown-skill)")
    ap.add_argument("--link", action="store_true", help="symlink one shared copy instead of copying")
    ap.add_argument("--dry-run", action="store_true", help="show what would happen, change nothing")
    ap.add_argument("--list", action="store_true", help="list target paths and detection status")
    args = ap.parse_args()

    print(f"document-to-markdown-skill installer  (source: {REPO})\n")
    if args.list:
        print("targets:")
        print_table()
        return 0

    if args.target_dir and args.target:
        print("ERROR: use either --target or --target-dir, not both.", file=sys.stderr)
        return 1

    if args.target_dir:
        dest = args.target_dir.expanduser().resolve()
        print(f"target: {dest}")
        ok = install_to(dest, args.link, args.dry_run)
        dests = [dest] if ok else []
    else:
        if args.target:
            keys = [k.strip().lower() for k in args.target.split(",") if k.strip()]
            if "all" in keys:
                keys = list(TARGETS)
            unknown = [k for k in keys if k not in TARGETS]
            if unknown:
                print(f"ERROR: unknown target(s): {', '.join(unknown)}. Known: {', '.join(TARGETS)}", file=sys.stderr)
                return 1
        else:
            keys = detected()
            if not keys:
                print("No supported CLI detected. Use --target explicitly. Known targets:")
                print_table()
                return 1
            print(f"detected: {', '.join(keys)}\n")
        dests = []
        for k in keys:
            print(f"[{k}] {TARGETS[k]['label']}")
            if install_to(TARGETS[k]["dest"], args.link, args.dry_run):
                dests.append(TARGETS[k]["dest"])

    if args.dry_run:
        print("\ndry run: nothing was changed.")
        return 0
    print("\ninstalled. First use of the skill creates its own .venv automatically "
          "(or pre-run: python <install dir>/scripts/document_to_markdown.py --setup).")
    print("Reload your CLI to pick it up (Qoder/Claude: /skills reload or restart the session).")
    if len(dests) > 1 and not args.link:
        print("Tip: with --link every CLI shares one copy (and one venv).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
