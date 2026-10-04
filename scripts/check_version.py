#!/usr/bin/env python3
"""Require a semantic version bump when a PR changes skills."""
import argparse
import json
import re
import subprocess
from pathlib import Path


def version(value):
    if not re.fullmatch(r"\d+\.\d+\.\d+", value):
        raise ValueError(f"Expected major.minor.patch, got {value!r}")
    return tuple(map(int, value.split(".")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    target = subprocess.check_output(["git", "rev-parse", "--verify", f"{args.base}^{{commit}}"], cwd=root, text=True).strip()
    # Compare with the fork point: skill changes that landed on the base branch later are not this PR's.
    base = subprocess.check_output(["git", "merge-base", target, "HEAD"], cwd=root, text=True).strip()
    changed = subprocess.check_output(["git", "diff", "--name-only", base, "HEAD", "--", "skills"], cwd=root, text=True)
    if not changed.strip():
        print("OK: no skill changes")
        return
    manifest = ".claude-plugin/plugin.json"
    old = json.loads(subprocess.check_output(["git", "show", f"{base}:{manifest}"], cwd=root, text=True))
    new = json.loads((root / manifest).read_text())
    if version(new["version"]) <= version(old["version"]):
        raise SystemExit("Skill changes require a higher .claude-plugin/plugin.json version")
    print(f"OK: kit version {old['version']} -> {new['version']}")


if __name__ == "__main__":
    main()
