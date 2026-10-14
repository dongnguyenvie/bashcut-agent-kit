#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=10.1", "rlottie-python>=1.3"]
# ///
"""Runs fetch_lottie.py of BashCut's Online Resources plugin (bashcut.resources), the one copy the app's Online resources
sheet uses too: same flags (`--help`), same output. Imported (`import fetch_lottie`), it is that module."""
import importlib.util
import os
import runpy
import sys
from pathlib import Path


def plugin_script(name):
    """BASHCUT_RESOURCES_DIR, a project's .bashcut/plugins, then the user's plugins folder."""
    here = Path.cwd()
    roots = [os.environ.get("BASHCUT_RESOURCES_DIR"), *(p / ".bashcut/plugins/bashcut.resources" for p in (here, *here.parents)),
             Path.home() / "Library/Application Support/BashCut/Plugins/bashcut.resources"]
    for root in roots:
        if root and (Path(root) / "scripts" / name).is_file():
            return Path(root) / "scripts" / name
    sys.exit('{"error": "fetch_lottie.py needs the Online Resources plugin: bashcut plugins install bashcut.resources"}')


# Bytecode written into the plugin folder would change it, and BashCut would ask to trust the plugin again.
sys.dont_write_bytecode = True
SCRIPT = plugin_script("fetch_lottie.py")
sys.path.insert(0, str(SCRIPT.parent))
if __name__ == "__main__":
    runpy.run_path(str(SCRIPT), run_name="__main__")
else:
    _spec = importlib.util.spec_from_file_location(__name__, SCRIPT)
    _module = importlib.util.module_from_spec(_spec)
    sys.modules[__name__] = _module
    _spec.loader.exec_module(_module)
