#!/usr/bin/env python3
"""Write agents/*.md (Claude Code sub-agents) from the briefs that live in the skills, so Claude Code and Codex read
the same text: Claude Code starts the sub-agent by name on a cheaper model; Codex (which only links skills) gives the
brief file to its own sub-agent. `--check` exits 1 when a file is out of date."""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS = {
    "surveyor": {
        "brief": "skills/footage-survey/SURVEYOR.md",
        "description": "Surveys footage for a BashCut edit: reads the whole digest and transcript, looks at contact "
        "sheets, stores shot descriptions and returns hook candidates, exact quotes with times and angles in under 450 "
        "words, so the editor never reads the transcript. Use from bc:edit-workflow for the survey; it never edits "
        "the timeline.",
        "tools": "Bash, Read, Write",
    },
    "critic": {
        "brief": "skills/review/CRITIC.md",
        "description": "Independent critic of a BashCut edit: judges a review packet as a viewer, measures text "
        "before calling it unreadable, and returns a verdict with findings and their fixes as one plan.cut patch in "
        "under 300 words. Use for the draft audit; it never edits.",
        "tools": "Bash, Read",
    },
    "voice": {
        "brief": "skills/voiceover/VOICE.md",
        "description": "Voices a BashCut edit: writes or fixes the plan.cut voiceover lines, synthesizes and checks "
        "every line in one job, rewords misread lines, and returns per-line take, seconds and similarity in under 200 "
        "words, so the editor never reads the voiceover skill or a job result. Use from bc:edit-workflow for the "
        "voiceover stage.",
        "tools": "Bash, Read, Write",
    },
    "graphics": {
        "brief": "skills/motion-graphics/GRAPHICS.md",
        "description": "Builds the graphics of a BashCut edit: reads the motion-graphics and graphics plugin skills, "
        "designs and renders the plan's graphic rows, places them in one build, looks at the landing frames, and "
        "returns item IDs, spans and problems left in under 200 words, so the editor never reads a graphics skill. "
        "Use from bc:edit-workflow for the graphics stage.",
        "tools": "Bash, Read, Write",
    },
}
MODEL = "sonnet"


def render(name):
    spec = AGENTS[name]
    body = open(os.path.join(ROOT, spec["brief"]), encoding="utf-8").read()
    body = body.split("\n", 1)[1].lstrip("\n") if body.startswith("# ") else body
    description = '"' + spec["description"].replace("\\", "\\\\").replace('"', '\\"') + '"'
    return (f"---\nname: {name}\ndescription: {description}\nmodel: {MODEL}\ntools: {spec['tools']}\n---\n\n"
            f"<!-- Generated from {spec['brief']} by scripts/sync_agents.py; edit the brief. -->\n\n{body}")


def main():
    check = "--check" in sys.argv
    stale = []
    os.makedirs(os.path.join(ROOT, "agents"), exist_ok=True)
    for name in AGENTS:
        path = os.path.join(ROOT, "agents", f"{name}.md")
        text = render(name)
        current = open(path, encoding="utf-8").read() if os.path.exists(path) else None
        if current != text:
            stale.append(name)
            if not check:
                open(path, "w", encoding="utf-8").write(text)
    if check and stale:
        print("agents out of date (run scripts/sync_agents.py): " + ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
