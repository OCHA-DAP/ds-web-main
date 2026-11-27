#!/usr/bin/env python3
"""Put the main app's site together in --out, ready to deploy.

    python3 scripts/assemble.py --out _site

- site/ is the root: the redirect to www.unocha.org and the routing rules
  (site/staticwebapp.config.json).
- aa-tracker/ is the AA tracker's open site (OCHA-DAP/ds-aa-tracking), copied file by file from
  its GitHub Pages site. The tracker publishes the list of its open files, each with its size and
  SHA-256 (open-site-files.json); every file is checked against it. The list holds the open site
  only, never the password-protected dev/ and admin/ pages.

A deploy replaces the whole app, so a deploy without the tracker would remove it from the site. If
the tracker's GitHub Pages site can't be read or a file doesn't match, the copy already live on
datascience.unocha.org is used instead (the last good copy). If neither can be read, this stops
with an error and nothing is deployed.

The tracker's LIST itself is never worked around: if it is refused (a name or entry this script
won't copy), the run stops with an error, so the copy here can't go stale unnoticed. Reading
errors and files that don't match the list (GitHub Pages' CDN keeps files up to 10 minutes and
ignores query strings, so just after a publish old and new files can mix) fall back to the live
copy, and the next scheduled run tries again.

Also writes version.json at the root (this repo's commit and the tracker's), and to $GITHUB_OUTPUT:
`changed` (true when the tracker's list or this repo's commit differs from what is live) and
`source` (which copy was used). Python standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
FOLDER = "aa-tracker"
MANIFEST = "open-site-files.json"
SOURCES = {
    "tracker": "https://ocha-dap.github.io/ds-aa-tracking/",
    "live": "https://datascience.unocha.org/aa-tracker/",
}
LIVE_VERSION = "https://datascience.unocha.org/version.json"
# Standard plan: 500 MB and 15,000 files per app; keep room for what comes next
MAX_BYTES = 400 * 1024 * 1024
MAX_FILES = 10_000
# a plain file name: no folders, no hidden files, nothing Static Web Apps reads as configuration
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,199}")
RESERVED = {"staticwebapp.config.json", "routes.json", MANIFEST}
HEADERS = {"User-Agent": "ds-web-main-assemble (GitHub Actions)"}


class SourceError(Exception):
    """A copy of the tracker that can't be read, or whose files don't match its list."""


class ListRefused(Exception):
    """The tracker's list holds something this script won't copy: never worked around."""


def fetch(url: str, tries: int = 3) -> bytes:
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404 or i == tries - 1:
                raise SourceError(f"{url}: HTTP {e.code}") from e
        except (urllib.error.URLError, OSError, http.client.HTTPException) as e:
            if i == tries - 1:
                raise SourceError(f"{url}: {e}") from e
        time.sleep(5 * (i + 1))
    raise AssertionError("unreachable")


def read_list(raw: bytes, where: str) -> list[dict]:
    try:
        files = json.loads(raw)["files"]
    except (ValueError, KeyError, TypeError) as e:
        raise ListRefused(f"{where}: not a file list ({e})") from e
    if not isinstance(files, list) or not files:
        raise ListRefused(f"{where}: the file list is empty")
    seen = set()
    for f in files:
        name, size, sha = f.get("path"), f.get("bytes"), f.get("sha256")
        if not (isinstance(name, str) and NAME.fullmatch(name)) or name in RESERVED or name in seen:
            raise ListRefused(f"{where}: refused file name {name!r}")
        if not (isinstance(size, int) and size >= 0 and isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha)):
            raise ListRefused(f"{where}: {name}: no valid size or SHA-256")
        seen.add(name)
    if "index.html" not in seen:
        raise ListRefused(f"{where}: no index.html in the list")
    if len(files) > MAX_FILES or sum(f["bytes"] for f in files) > MAX_BYTES:
        raise ListRefused(f"{where}: {len(files)} files, {sum(f['bytes'] for f in files)} bytes: over the limit")
    return files


def copy_from(base: str, dest: Path) -> tuple[bytes, list[dict]]:
    """Copy every listed file from `base` into `dest`, checking each one; return the list."""
    raw = fetch(base + MANIFEST)
    files = read_list(raw, base + MANIFEST)
    dest.mkdir(parents=True)
    for f in files:
        body = fetch(base + f["path"])
        if len(body) != f["bytes"] or hashlib.sha256(body).hexdigest() != f["sha256"]:
            raise SourceError(f"{base}{f['path']}: does not match the list (size or SHA-256)")
        (dest / f["path"]).write_bytes(body)
    return raw, files


def output(**kv: str) -> None:
    print(" ".join(f"{k}={v}" for k, v in kv.items()))
    if p := os.environ.get("GITHUB_OUTPUT"):
        with open(p, "a") as fh:
            fh.writelines(f"{k}={v}\n" for k, v in kv.items())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out.resolve()
    if out.parent != ROOT or not re.fullmatch(r"_[A-Za-z0-9-]+", out.name):
        sys.exit(f"FATAL: --out must be a folder of its own at the repo root, named _<name>; got {out}")
    shutil.rmtree(out, ignore_errors=True)
    shutil.copytree(SITE, out)
    dest = out / FOLDER
    if dest.exists():
        sys.exit(f"FATAL: site/ already has a {FOLDER}/ folder; the tracker's copy goes there")

    used, raw, files, errors = None, b"", [], []
    for name, base in SOURCES.items():
        try:
            raw, files = copy_from(base, dest)
            used = name
            break
        except ListRefused as e:
            if name == "tracker":
                sys.exit(f"FATAL: the AA tracker's list is refused, so nothing is deployed: {e}")
            errors.append(f"{name}: {e}")
            shutil.rmtree(dest, ignore_errors=True)
        except SourceError as e:
            errors.append(f"{name}: {e}")
            print(f"::warning::could not use the {name} copy of the AA tracker: {e}")
            shutil.rmtree(dest, ignore_errors=True)
    if used is None:
        sys.exit("FATAL: no usable copy of the AA tracker, so nothing is deployed "
                 "(a deploy without it would remove it from the site): " + "; ".join(errors))
    (dest / MANIFEST).write_bytes(raw)

    commit = os.environ.get("GITHUB_SHA") or subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    (out / "version.json").write_text(json.dumps(
        {"commit": commit, "aa_tracker_open_sha": json.loads(raw).get("open_sha", "")}) + "\n")

    # changed: the tracker's list, or this repo's commit, differs from what is live (a push whose
    # own run was dropped from the queue is then deployed by the next scheduled run)
    try:
        live = read_list(fetch(SOURCES["live"] + MANIFEST, tries=2), "live")
    except (SourceError, ListRefused):
        live = None
    try:
        live_commit = json.loads(fetch(LIVE_VERSION, tries=2)).get("commit")
    except (SourceError, ValueError, AttributeError):
        live_commit = None
    key = lambda fs: sorted((f["path"], f["sha256"]) for f in fs)  # noqa: E731
    changed = live is None or key(live) != key(files) or live_commit != commit

    total = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    count = sum(1 for p in out.rglob("*") if p.is_file())
    if total > MAX_BYTES or count > MAX_FILES:
        sys.exit(f"FATAL: the site would be {count} files, {total} bytes: over the limit")
    print(f"assembled {out.name}/: {count} files, {total / 1e6:.1f} MB; AA tracker from the {used} copy, "
          f"{len(files)} files")
    output(changed=str(changed).lower(), source=used)


if __name__ == "__main__":
    main()
