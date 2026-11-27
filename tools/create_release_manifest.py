#!/usr/bin/env python3
"""Create a small deterministic-schema manifest for a verified manual release.

This builder does NOT sign anything or require network access.
Sign the resulting JSON bytes using tools/release_signature.php on a
TRUSTED OFFLINE machine. Do not commit or publish private signing keys.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile


def create_manifest(package: Path, valid_days: int = 90, now=None):
    if not 1 <= valid_days <= 180:
        raise ValueError("Manifest lifetime must be 1-180 days")
    package = package.resolve(strict=True)
    if not package.is_file() or package.stat().st_size > 50 * 1024 * 1024:
        raise ValueError("Missing or oversized release package")
    with zipfile.ZipFile(package) as z:
        # Reject expansion bombs, unsafe paths and links from ZIP metadata
        # BEFORE testzip() decompresses the archive. Signing an archive
        # must never be able to turn a tiny ZIP into an expensive unpack.
        names = set()
        expanded = 0
        entries = z.infolist()
        if not 1 <= len(entries) <= 3500:
            raise ValueError("Release archive has an invalid number of entries")
        for info in entries:
            path = info.filename
            parts = PurePosixPath(path).parts
            if (not parts or parts[0] not in ("zilomentor-pro", "elementor-pro")
                    or path.startswith("/") or "\\" in path or ".." in parts
                    or path in names or stat.S_ISLNK(info.external_attr >> 16)):
                raise ValueError("Unsafe, linked or repeated release archive entry")
            names.add(path)
            expanded += info.file_size
            if info.file_size > 15 * 1024 * 1024 or expanded > 90 * 1024 * 1024:
                raise ValueError("Release archive expanded size exceeds cap")
        options = ("zilomentor-pro/elementor-pro.php",
                   "elementor-pro/elementor-pro.php")
        matches = [x for x in options if x in names]
        if len(matches) != 1 or z.testzip() is not None:
            raise ValueError("Release archive missing unambiguous bootstrap or failed integrity")
        name = matches[0]
        entry = z.read(name).decode("utf-8", errors="strict")
    match = re.search(r"^\s*\*\s*Version:\s*(\d+\.\d+\.\d+)\s*$", entry, re.M)
    if not match or "Plugin Name: ZiloMentor Pro" not in entry:
        raise ValueError("Release ZIP must contain a valid ZiloMentor Pro header")
    version = match.group(1)
    folder = name.split("/", 1)[0]
    layout = "independent" if folder == "zilomentor-pro" else "compat"
    expected = "zilomentor-pro-" + layout + "-" + version + "-staging-only.zip"
    if package.name != expected:
        raise ValueError("ZIP filename/version mismatch")
    now = now or datetime.now(timezone.utc)
    now = now.astimezone(timezone.utc).replace(microsecond=0)
    return {
        "schema": 1,
        "plugin": name,
        "version": version,
        "filename": package.name,
        "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
        "size_bytes": package.stat().st_size,
        "issued_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + timedelta(days=valid_days)).isoformat().replace("+00:00", "Z"),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--zip", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--valid-days", type=int, default=90)
    a = ap.parse_args()
    manifest = create_manifest(a.zip, valid_days=a.valid_days)
    if a.out.exists() or a.out.is_symlink():
        raise SystemExit("Refusing to overwrite an existing release manifest")
    a.out.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
                     encoding="utf-8")
    print("MANIFEST_CREATED=" + str(a.out))
    print("ZIP_VERSION=" + manifest["version"])
    print("ZIP_SHA256=" + manifest["sha256"])
    print("NEXT_STEP=SIGN_WITH_OFFLINE_ED25519_KEY")


if __name__ == "__main__":
    main()
