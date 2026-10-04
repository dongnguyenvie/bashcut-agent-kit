#!/usr/bin/env python3
"""Package the kit for an in-app update and record it in releases.json, the catalog BashCut reads.

    scripts/release.py                      # zip into dist/ and print the archive, size and SHA-256
    scripts/release.py --tag v0.0.2 --register [--min-app 0.0.1] [--notes "..."]

The archive holds one `bashcut-agent-kit/` folder: the plugin manifest, skills, scripts and reference, without
tests, CI or caches. With BASHCUT_SIGNING_KEY set, scripts/sign.swift signs the archive digest with the BashCut
publisher key; BashCut refuses unsigned kit archives. --register prepends the version to releases.json with the
GitHub Release asset URL.
"""
import argparse, datetime, hashlib, json, os, pathlib, re, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY = "dongnguyenvie/bashcut-agent-kit"
EXCLUDED = (".git", ".github", "tests", "dist", "__pycache__", ".DS_Store", ".gitignore", ".env", "_survey",
            "releases.json")


def fail(message):
    sys.exit(f"error: {message}")


def version():
    value = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", value):
        fail(f"plugin.json version {value!r} is not major.minor.patch")
    return value


def tracked_files():
    """Committed files only, so a local build matches CI and never picks up notes or caches."""
    names = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True).stdout.split(b"\0")
    files = [pathlib.PurePosixPath(name.decode()) for name in names if name]
    return [f for f in files if not any(part in EXCLUDED for part in f.parts)]


def package(kit_version):
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    archive = dist / f"bashcut-agent-kit-{kit_version}.zip"
    archive.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as staging:
        staged = pathlib.Path(staging) / "bashcut-agent-kit"
        for relative in tracked_files():
            target = staged / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target, follow_symlinks=False)
        subprocess.run(["ditto", "-c", "-k", "--norsrc", "--keepParent", str(staged), str(archive)], check=True)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (dist / (archive.name + ".sha256")).write_text(f"{digest}  {archive.name}\n")
    signature = sign(digest)
    signature_file = dist / (archive.name + ".sig")
    signature_file.unlink(missing_ok=True)
    if signature:
        signature_file.write_text(signature + "\n")
    return archive, digest, signature


def sign(digest):
    if not os.environ.get("BASHCUT_SIGNING_KEY"):
        return None
    result = subprocess.run(["swift", str(ROOT / "scripts/sign.swift"), digest], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def validate(document):
    """Problems in a releases.json document; the app relies on these shapes."""
    problems = []
    if document.get("schemaVersion") != 1 or document.get("kit") != "bashcut":
        problems.append("releases.json needs schemaVersion 1 and kit \"bashcut\"")
    seen = set()
    for entry in document.get("versions", []):
        value = entry.get("version", "")
        if not re.fullmatch(r"\d+\.\d+\.\d+", value) or value in seen:
            problems.append(f"version {value!r} is invalid or listed twice")
        seen.add(value)
        expected = f"https://github.com/{REPOSITORY}/releases/download/v{value}/bashcut-agent-kit-{value}.zip"
        if entry.get("url") != expected:
            problems.append(f"{value}: url must be {expected}")
        if not re.fullmatch(r"[0-9a-f]{64}", entry.get("sha256", "")):
            problems.append(f"{value}: sha256 must be 64 lowercase hex digits")
        if not str(entry.get("signature", "")).startswith("ed25519:"):
            problems.append(f"{value}: signature must be ed25519:BASE64")
        if not re.fullmatch(r"\d+\.\d+\.\d+", entry.get("minAppVersion", "")):
            problems.append(f"{value}: minAppVersion must be major.minor.patch")
    return problems


def register(entry, catalog=ROOT / "releases.json"):
    document = json.loads(catalog.read_text())
    if any(existing["version"] == entry["version"] for existing in document["versions"]):
        fail(f"releases.json already lists {entry['version']}; bump the version instead of re-publishing")
    document["versions"].insert(0, entry)
    catalog.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tag", help="the release tag, which must be v<plugin.json version>")
    parser.add_argument("--register", action="store_true", help="add the archive to releases.json (needs --tag)")
    parser.add_argument("--min-app", default="0.0.1", help="oldest BashCut version the kit's commands work with")
    parser.add_argument("--notes", default="", help="short English release notes shown in Settings › Agents")
    parser.add_argument("--check", action="store_true", help="only validate releases.json")
    args = parser.parse_args()
    if args.check:
        problems = validate(json.loads((ROOT / "releases.json").read_text()))
        if problems:
            fail("\n".join(problems))
        print("OK: releases.json")
        return
    kit_version = version()
    if args.tag is not None and args.tag != f"v{kit_version}":
        fail(f"tag {args.tag} does not match plugin.json version {kit_version}")
    archive, digest, signature = package(kit_version)
    entry = {
        "version": kit_version, "minAppVersion": args.min_app,
        "url": f"https://github.com/{REPOSITORY}/releases/download/v{kit_version}/{archive.name}",
        "sha256": digest, "signature": signature, "size": archive.stat().st_size,
        "releasedAt": datetime.date.today().isoformat(),
    }
    if args.notes:
        entry["notes"] = {"en": args.notes}
    if args.register:
        if not args.tag:
            fail("--register needs --tag")
        if not signature:
            fail("BASHCUT_SIGNING_KEY is required to register a release")
        register(entry)
    print(json.dumps({"archive": str(archive), **entry}))


if __name__ == "__main__":
    main()
