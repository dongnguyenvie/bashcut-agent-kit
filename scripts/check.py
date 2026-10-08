#!/usr/bin/env python3
"""Check every skill: frontmatter name matches its folder, description present and within limits,
files referenced as <skill_dir>/X exist. Exit 1 on any problem."""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
problems = []
for name in sorted(os.listdir(SKILLS)):
    path = os.path.join(SKILLS, name, "SKILL.md")
    if not os.path.isfile(path):
        continue
    text = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        problems.append(f"{name}: no frontmatter")
        continue
    meta = dict(re.findall(r"^(\w[\w-]*):\s*(.*)$", m.group(1), re.M))
    if meta.get("name") != name:
        problems.append(f"{name}: name '{meta.get('name')}' does not match the folder")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
        problems.append(f"{name}: name must be lowercase words joined by '-' (max 64)")
    desc = meta.get("description", "")
    if not desc:
        problems.append(f"{name}: no description")
    elif len(desc) > 1024:
        problems.append(f"{name}: description is {len(desc)} characters (max 1024)")
    for ref in re.findall(r"<skill_dir>/([\w.-]+)", text):
        if not os.path.exists(os.path.join(SKILLS, name, ref)):
            problems.append(f"{name}: <skill_dir>/{ref} does not exist")
    # A user-only skill (/bc:<name>) must be user-only in Claude Code and in Codex alike.
    user_only = meta.get("disable-model-invocation", "").strip() == "true"
    policy = os.path.join(SKILLS, name, "agents", "openai.yaml")
    codex_off = os.path.isfile(policy) and re.search(
        r"^\s*allow_implicit_invocation:\s*false\s*$", open(policy, encoding="utf-8").read(), re.M) is not None
    if user_only != codex_off:
        problems.append(f"{name}: disable-model-invocation: true and agents/openai.yaml "
                        "policy.allow_implicit_invocation: false go together")
    lines = text.count("\n")
    if lines > 250:
        problems.append(f"{name}: {lines} lines; move detail into REFERENCE.md")
    print(f"{name:16s} {lines:4d} lines  description {len(desc):4d} chars")
print("\n".join(problems) or "OK")
sys.exit(1 if problems else 0)
