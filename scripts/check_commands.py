#!/usr/bin/env python3
"""Validate explicit bashcut CLI examples against the app's generated command reference."""
import argparse
import re
from pathlib import Path


def catalog(text):
    commands = {}
    for usage in re.findall(r"^### `(bashcut [^`]+)`", text, re.M):
        words = usage.split()
        commands[tuple(words[1:3])] = set(re.findall(r"--[a-z][a-z0-9-]*", usage))
    if not commands:
        raise ValueError("The command reference has no generated CLI headings")
    return commands


def examples(text):
    text = text.replace("\\\n", " ")
    # Fenced shell examples plus inline code; do not treat ordinary prose as shell commands.
    for block in re.findall(r"```(?:sh|bash|shell)\n(.*?)```", text, re.S):
        for line in block.splitlines():
            if line.strip().startswith("bashcut "):
                yield line.strip()
    for inline in re.findall(r"(?<!`)`([^`\n]+)`(?!`)", text):
        if inline.startswith("bashcut "):
            yield inline


def validate(text, commands):
    problems = []
    for example in examples(text):
        tokens = re.findall(r'''"(?:\\.|[^"\\])*"|'[^']*'|[^\s]+''', example)
        if len(tokens) < 3:
            if tokens[1:] != ["help"]:
                problems.append(f"Incomplete command: {example}")
            continue
        key = tuple(tokens[1:3])
        if key not in commands:
            problems.append(f"Unknown command: {' '.join(key)}")
            continue
        allowed = commands[key] | {"--format", "--help"}
        for token in tokens[3:]:
            if token.startswith(("#", ">", "|", ";", "&&")):
                break
            if token.startswith(('"', "'")):
                continue
            match = re.match(r"\[?(--[a-z][a-z0-9-]*)", token)
            if match and match[1] not in allowed:
                problems.append(f"Unknown flag {match[1]} for {' '.join(key)}")
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--skills", type=Path, default=Path(__file__).resolve().parents[1] / "skills")
    args = parser.parse_args()
    commands = catalog(args.reference.read_text())
    errors = []
    count = 0
    for path in sorted(args.skills.rglob("*.md")):
        text = path.read_text()
        count += len(list(examples(text)))
        errors.extend(f"{path}: {error}" for error in validate(text, commands))
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"OK: {count} explicit CLI examples checked against {len(commands)} commands")


if __name__ == "__main__":
    main()
