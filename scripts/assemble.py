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

Writes to $GITHUB_OUTPUT: `changed` (true when the tracker's list differs from the live one) and
`source` (which copy was used). Python standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
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
# Standard plan: 500 MB and 15,000 files per app; keep room for what comes next
MAX_BYTES = 400 * 1024 * 1024
MAX_FILES = 10_000
# a plain file name: no folders, no hidden files, nothing Static Web Apps reads as configuration
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,199}")
RESERVED = {"staticwebapp.config.json", "routes.json", MANIFEST}
HEADERS = {"User-Agent": "ds-web-main-assemble (GitHub Actions)"}


class SourceError(Exception):
    """A copy of the tracker that can't be used as it is."""


def fetch(url: str, tries: int = 3) -> bytes:
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404 or i == tries - 1:
                raise SourceError(f"{url}: HTTP {e.code}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            if i == tries - 1:
                raise SourceError(f"{url}: {e}") from e
        time.sleep(5 * (i + 1))
    raise AssertionError("unreachable")


def read_list(raw: bytes, where: str) -> list[dict]:
    try:
        files = json.loads(raw)["files"]
    except (ValueError, KeyError, TypeError) as e:
        raise SourceError(f"{where}: not a file list ({e})") from e
    if not isinstance(files, list) or not files:
        raise SourceError(f"{where}: the file list is empty")
    seen = set()
    for f in files:
        name, size, sha = f.get("path"), f.get("bytes"), f.get("sha256")
        if not (isinstance(name, str) and NAME.fullmatch(name)) or name in RESERVED or name in seen:
            raise SourceError(f"{where}: refused file name {name!r}")
        if not (isinstance(size, int) and size >= 0 and isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha)):
            raise SourceError(f"{where}: {name}: no valid size or SHA-256")
        seen.add(name)
    if "index.html" not in seen:
        raise SourceError(f"{where}: no index.html in the list")
    if len(files) > MAX_FILES or sum(f["bytes"] for f in files) > MAX_BYTES:
        raise SourceError(f"{where}: {len(files)} files, {sum(f['bytes'] for f in files)} bytes: over the limit")
    return files


def copy_from(base: str, dest: Path) -> tuple[bytes, list[dict]]:
    """Copy every listed file from `base` into `dest`, checking each one; return the list."""
    raw = fetch(base + MANIFEST + f"?t={int(time.time())}")
    files = read_list(raw, base + MANIFEST)
    dest.mkdir(parents=True)
    for f in files:
        for attempt in range(3):
            # a new address on each try (the SHA-256 and the try's number), so the CDN fetches it
            # afresh instead of serving a copy it kept from before, or from the try before
            body = fetch(f"{base}{f['path']}?v={f['sha256'][:16]}-{attempt}")
            if len(body) == f["bytes"] and hashlib.sha256(body).hexdigest() == f["sha256"]:
                break
            time.sleep(10 * (attempt + 1))
        else:
            raise SourceError(f"{base}{f['path']}: does not match the list (size or SHA-256), three times")
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
        except SourceError as e:
            errors.append(f"{name}: {e}")
            print(f"::warning::could not use the {name} copy of the AA tracker: {e}")
            shutil.rmtree(dest, ignore_errors=True)
    if used is None:
        sys.exit("FATAL: no usable copy of the AA tracker, so nothing is deployed "
                 "(a deploy without it would remove it from the site): " + "; ".join(errors))
    (dest / MANIFEST).write_bytes(raw)

    # changed: the tracker's list differs from the one live on the site (first deploy: no live list)
    try:
        live = read_list(fetch(SOURCES["live"] + MANIFEST + f"?t={int(time.time())}", tries=2), "live")
    except SourceError:
        live = None
    key = lambda fs: sorted((f["path"], f["sha256"]) for f in fs)  # noqa: E731
    changed = live is None or key(live) != key(files)

    total = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    count = sum(1 for p in out.rglob("*") if p.is_file())
    if total > MAX_BYTES or count > MAX_FILES:
        sys.exit(f"FATAL: the site would be {count} files, {total} bytes: over the limit")
    print(f"assembled {out.name}/: {count} files, {total / 1e6:.1f} MB; AA tracker from the {used} copy, "
          f"{len(files)} files")
    output(changed=str(changed).lower(), source=used)


if __name__ == "__main__":
    main()
