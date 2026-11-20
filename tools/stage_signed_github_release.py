#!/usr/bin/env python3
"""Stage an independently signed ZiloMentor GitHub Release, never install it.

Uses GitHub public Release assets, not GitHub Actions or WordPress' unverified
automatic plugin updater. All input is untrusted until verified by a previously
pinned Ed25519 PUBLIC key using PHP Sodium and exact ZIP hash/version checks.

Usage:
  python3 tools/stage_signed_github_release.py \
    --current-version 0.1.1 --trusted-public-key /private/zmp-public.b64 \
    --stage-dir /private/staged-releases

Staging directory must already exist outside webroot, owner-only (0700).
Does not use a GitHub token, edit WordPress or create a signing private key.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
from urllib.error import HTTPError
from urllib.request import (
    HTTPSHandler, HTTPRedirectHandler, ProxyHandler, Request, build_opener,
)
import zipfile

OWNER = "Galactus-Prime"
REPO = "zilomentor-pro"
API_URL = "https://api.github.com/repos/Galactus-Prime/zilomentor-pro/releases/latest"
ALLOWED_HOSTS = {
    "api.github.com", "github.com", "release-assets.githubusercontent.com",
    "objects.githubusercontent.com",
}
EXPECTED_PLUGIN = "zilomentor-pro/elementor-pro.php"
FIELDS = {
    "schema", "plugin", "version", "filename", "sha256",
    "size_bytes", "issued_at", "expires_at",
}
MAX_ZIP = 50 * 1024 * 1024
MAX_EXPANDED = 500 * 1024 * 1024
MAX_FILES = 3500
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ReleaseError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ReleaseError(message)


def version_parts(version):
    require(isinstance(version, str) and VERSION_RE.fullmatch(version),
            "Invalid semantic release version")
    return tuple(int(part) for part in version.split("."))


def safe_url(url, allow_hosts=ALLOWED_HOSTS):
    parts = urlsplit(url)
    require(parts.scheme == "https" and parts.hostname in allow_hosts
            and parts.port in (None, 443)
            and parts.username is None and parts.password is None
            and not parts.fragment,
            "Untrusted Release download URL or redirect")
    return url


class OnlyTrustedHosts(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def public_fetch(url, limit):
    safe_url(url)
    opener = build_opener(ProxyHandler({}), HTTPSHandler(), OnlyTrustedHosts())
    req = Request(url, headers={
        "User-Agent": "ZiloMentorPro-Signed-Release-Checker/1",
        "Accept": "application/vnd.github+json"
                  if url == API_URL else "application/octet-stream",
    })
    try:
        with opener.open(req, timeout=22) as response:
            safe_url(response.geturl())
            length = response.headers.get("Content-Length")
            require(not length or int(length) <= limit, "Release asset exceeds size cap")
            blob = bytearray()
            while True:
                chunk = response.read(min(65536, limit + 1 - len(blob)))
                if not chunk:
                    return bytes(blob)
                blob.extend(chunk)
                require(len(blob) <= limit, "Release asset exceeds size cap")
    except HTTPError as error:
        if error.code == 404 and url == API_URL:
            raise ReleaseError("NO_PUBLISHED_GITHUB_RELEASE") from error
        raise ReleaseError("GitHub Release request failed: HTTP " + str(error.code)) from error


def checked_asset(release, filename, version):
    assets = release.get("assets")
    require(isinstance(assets, list) and len(assets) <= 30,
            "Unexpected number of Release assets")
    matching = [item for item in assets
                if isinstance(item, dict) and item.get("name") == filename]
    require(len(matching) == 1, "Missing or ambiguous signed Release asset: " + filename)
    item = matching[0]
    expected_url = ("https://github.com/" + OWNER + "/" + REPO +
                    "/releases/download/v" + version + "/" + filename)
    require(item.get("browser_download_url") == expected_url
            and item.get("state") == "uploaded"
            and type(item.get("size")) is int
            and 1 <= item["size"] <= MAX_ZIP,
            "Unexpected asset source, state or size")
    digest = item.get("digest")
    if digest is not None:
        require(isinstance(digest, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", digest),
                "Invalid GitHub Release asset digest")
    return item


def inspect_zip(data, version):
    require(0 < len(data) <= MAX_ZIP, "Missing/oversized ZIP")
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
        with archive as z:
            require(z.testzip() is None, "Corrupt ZIP content")
            names = set()
            expanded = 0
            payload_header = None
            require(1000 <= len(z.infolist()) <= MAX_FILES,
                    "Unexpectedly incomplete/oversized WordPress plugin archive")
            for info in z.infolist():
                path = info.filename
                parts = PurePosixPath(path).parts
                require(path not in names and "\\" not in path
                        and not path.startswith("/") and parts
                        and parts[0] == "zilomentor-pro"
                        and ".." not in parts
                        and not stat.S_ISLNK(info.external_attr >> 16),
                        "Unsafe or repeated ZIP entry")
                names.add(path)
                expanded += info.file_size
                require(expanded <= MAX_EXPANDED,
                        "Decompressed plugin exceeds safety cap")
                if path == EXPECTED_PLUGIN:
                    require(info.file_size <= 65536,
                            "Suspiciously large WordPress bootstrap")
                    payload_header = z.read(info).decode("utf-8")
            require(payload_header is not None
                    and "Plugin Name: ZiloMentor Pro" in payload_header
                    and re.search(r"^\s*\*\s*Version:\s*" +
                                  re.escape(version) + r"\s*$",
                                  payload_header, re.M),
                    "ZIP is not the expected independent plugin/version")
    except (zipfile.BadZipFile, UnicodeError) as exc:
        raise ReleaseError("Invalid ZIP archive or entry encoding") from exc


def verify_signature(manifest_bytes, sig_bytes, trusted_public_key, php=None):
    tool = Path(__file__).resolve().with_name("release_signature.php")
    require(tool.is_file(), "Ed25519 verifier unavailable")
    key = Path(trusted_public_key)
    require(key.is_file() and not key.is_symlink()
            and not key.stat().st_mode & 0o022,
            "Trusted public key missing, linked, or group/world writable")
    php = php or shutil.which("php")
    require(php, "PHP CLI with Sodium is required")
    # Never read/print the PRIVATE key; use private temporary files
    # containing only unsigned bytes, signature and already-pinned PUBLIC key.
    with tempfile.TemporaryDirectory(prefix="zmp-verify-") as directory:
        m = Path(directory) / "manifest.json"
        s = Path(directory) / "signature"
        m.write_bytes(manifest_bytes)
        s.write_bytes(sig_bytes)
        out = subprocess.run(
            [str(php), str(tool), "verify", str(m), str(key), str(s)],
            capture_output=True, text=True, timeout=30, check=False,
        )
    require(out.returncode == 0
            and "VALID_ED25519_RELEASE_SIGNATURE" in out.stdout,
            "Detached Ed25519 signature verification failed")


def check_manifest(blob, version, zip_bytes):
    require(len(blob) <= 4096, "Oversized signed manifest")
    try:
        data = json.loads(blob)
        require(type(data) is dict and set(data) == FIELDS,
                "Invalid signed Release schema")
        expected_zip = f"zilomentor-pro-independent-{version}-staging-only.zip"
        require(type(data["schema"]) is int and data["schema"] == 1
                and data["plugin"] == EXPECTED_PLUGIN
                and data["version"] == version
                and data["filename"] == expected_zip
                and type(data["size_bytes"]) is int
                and data["size_bytes"] == len(zip_bytes)
                and type(data["sha256"]) is str
                and SHA256_RE.fullmatch(data["sha256"])
                and hashlib.sha256(zip_bytes).hexdigest() == data["sha256"],
                "Signed manifest does not match verified ZIP/version")
        issued = datetime.fromisoformat(data["issued_at"].replace("Z", "+00:00"))
        expires = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
        require(issued.tzinfo and expires.tzinfo
                and timedelta(0) < expires - issued <= timedelta(days=180)
                and issued <= datetime.now(timezone.utc) + timedelta(minutes=5)
                and expires > datetime.now(timezone.utc),
                "Release signature manifest expired or has invalid dates")
        return data
    except (ValueError, TypeError, AttributeError, KeyError) as exc:
        if isinstance(exc, ReleaseError):
            raise
        raise ReleaseError("Invalid signed Release manifest") from exc


def save_staged(stage_dir, files):
    destination = Path(stage_dir)
    require(destination.is_dir() and not destination.is_symlink()
            and destination.stat().st_uid == os.geteuid()
            and destination.stat().st_mode & 0o077 == 0
            and not any(part.lower() in ("public_html", "www", "htdocs", "wp-content")
                        for part in destination.resolve().parts),
            "Stage directory must be owner-only and outside the webroot")
    require(all(re.fullmatch(r"[a-zA-Z0-9_.-]+", name)
                and not (destination / name).exists()
                and not (destination / name).is_symlink()
                for name in files),
            "Unsafe or existing staged filename")
    committed = []
    try:
        for name, blob in files.items():
            path = destination / name
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(path, flags, 0o600)
            committed.append(path)
            with os.fdopen(descriptor, "wb") as f:
                f.write(blob)
                f.flush()
                os.fsync(f.fileno())
    except Exception:
        for path in committed:
            path.unlink(missing_ok=True)
        raise
    return committed


def stage_release(*, current_version, public_key, stage_dir, fetch=public_fetch,
                  php=None):
    version_parts(current_version)
    release_bytes = fetch(API_URL, 512 * 1024)
    try:
        release = json.loads(release_bytes)
    except (ValueError, TypeError) as exc:
        raise ReleaseError("Unparseable GitHub Release response") from exc
    require(type(release) is dict and release.get("draft") is False
            and release.get("prerelease") is False,
            "Draft/prerelease cannot be automatically staged")
    tag = release.get("tag_name")
    require(isinstance(tag, str) and re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag),
            "Invalid release tag")
    version = tag[1:]
    require(version_parts(version) > version_parts(current_version),
            "No newer independently signed release")
    names = {
        "manifest": f"zilomentor-pro-{version}.json",
        "signature": f"zilomentor-pro-{version}.json.sig",
        "zip": f"zilomentor-pro-independent-{version}-staging-only.zip",
    }
    assets = {key: checked_asset(release, name, version)
              for key, name in names.items()}
    blobs = {}
    for key, item in assets.items():
        cap = 4096 if key == "manifest" else 256 if key == "signature" else MAX_ZIP
        require(item["size"] <= cap, "Unexpected Release asset length")
        url = item["browser_download_url"]
        blob = fetch(url, cap)
        require(len(blob) == item["size"], "Downloaded Release asset size mismatch")
        if item.get("digest"):
            require(item["digest"] == "sha256:" + hashlib.sha256(blob).hexdigest(),
                    "GitHub Release asset digest mismatch")
        blobs[key] = blob
    verify_signature(blobs["manifest"], blobs["signature"], public_key, php=php)
    manifest = check_manifest(blobs["manifest"], version, blobs["zip"])
    inspect_zip(blobs["zip"], version)
    saved = save_staged(stage_dir, {
        names["manifest"]: blobs["manifest"],
        names["signature"]: blobs["signature"],
        names["zip"]: blobs["zip"],
    })
    return {
        "version": version,
        "plugin": manifest["plugin"],
        "zip_sha256": manifest["sha256"],
        "files": [str(path) for path in saved],
        "live_installation_changed": False,
        "automatic_update_enabled": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current-version", required=True)
    parser.add_argument("--trusted-public-key", required=True, type=Path)
    parser.add_argument("--stage-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = stage_release(
            current_version=args.current_version, public_key=args.trusted_public_key,
            stage_dir=args.stage_dir,
        )
    except ReleaseError as error:
        print("SIGNED_RELEASE_NOT_STAGED=" + str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    print("NEXT_STEP=OWNER_VERIFIED_MANUAL_LIVE_SWAP_PREFLIGHT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
