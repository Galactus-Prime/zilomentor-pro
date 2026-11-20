#!/usr/bin/env python3
"""Guarded manual Elementor Pro -> ZiloMentor Pro switch and file-only rollback.

No Actions, no automatic updates, no DB restoration. Intended for explicit
human-authorised releases; --apply is required to change the live plugin.
Run AS the site filesystem owner, never as root. A verified private pre-release
DB export and original plugin TAR must already exist in --backup-dir.
The same --apply command handles later ZiloMentor releases; existing versions
are retained privately for rollback. Never uses Github Actions.

Examples:
  python3 tools/manual_live_swap.py --site /path/to/wp --backup-dir /private/backup \
    --zip /tmp/staging.zip --sha256 HEX                  # read-only preflight
  python3 tools/manual_live_swap.py --site /path/to/wp --backup-dir /private/backup \
    --zip /tmp/staging.zip --sha256 HEX --apply          # controlled swap
  python3 tools/manual_live_swap.py --site /path/to/wp --backup-dir /private/backup \
    --rollback                                          # previous tested release
  python3 tools/manual_live_swap.py --site /path/to/wp --backup-dir /private/backup \
    --rollback-to-official                              # original Elementor Pro

Never restore a production WooCommerce database without separately reconciling
orders and payments created after the snapshot.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import uuid
import zipfile

WP_CLI = Path("/usr/local/bin/wp")
PHP_CLI = Path("/opt/cpanel/ea-php84/root/usr/bin/php")
FOLDER = "elementor-pro"
ENTRY = "elementor-pro.php"
EXPECTED_CURRENT = "Elementor Pro"
EXPECTED_NEW = "ZiloMentor Pro"


def fail(msg: str):
    raise RuntimeError(msg)


def plugin_name(path: Path):
    try:
        data = (path / ENTRY).read_text(encoding="utf-8", errors="replace")[:4096]
    except FileNotFoundError:
        return ""
    match = re.search(r"^\s*\*?\s*Plugin Name:\s*(.+)$", data, re.M)
    return match.group(1).strip() if match else ""


def plugin_version(path: Path):
    try:
        data = (path / ENTRY).read_text(encoding="utf-8", errors="replace")[:4096]
    except FileNotFoundError:
        return ""
    match = re.search(r"^\s*\*?\s*Version:\s*(\d+\.\d+\.\d+)$", data, re.M)
    return match.group(1) if match else ""


def version_parts(version: str):
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        fail("Unknown or invalid plugin version")
    return tuple(map(int, version.split(".")))


def inside(child: Path, parent: Path):
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def wp_health(site: Path, expected_zmp: bool, expected_version: str | None = None,
              folder: str = FOLDER):
    php = str(PHP_CLI)
    cli = str(WP_CLI)
    code = (
        '$r=["zmp"=>defined("ZILOMENTOR_VERSION"),'
        '"zmp_version"=>defined("ZILOMENTOR_VERSION")?ZILOMENTOR_VERSION:null,'
        '"base"=>defined("ELEMENTOR_PRO_PLUGIN_BASE")?ELEMENTOR_PRO_PLUGIN_BASE:null,'
        '"pro"=>defined("ELEMENTOR_PRO_VERSION"),'
        '"core"=>did_action("elementor/loaded")>0,'
        '"class"=>class_exists("ElementorPro\\\\Plugin"),'
        '"wc"=>class_exists("WooCommerce")];'
        'echo wp_json_encode($r);'
    )
    p = subprocess.run([php, cli, "--path=" + str(site), "eval", code],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, timeout=110)
    if p.returncode != 0:
        fail("WordPress bootstrap failed (exit " + str(p.returncode) +
             "); stderr not printed because plugins may expose secrets")
    try:
        state = json.loads(p.stdout.strip())
    except ValueError:
        fail("WordPress bootstrap returned invalid structured health result")
    if not all(state.get(k) is True for k in ("pro", "core", "class", "wc")):
        fail("WordPress bootstrap failed Pro/Core/WooCommerce checks: " +
             json.dumps(state))
    if state.get("zmp") is not expected_zmp:
        fail("WordPress bootstrap plugin identity is incorrect")
    if expected_zmp and expected_version and state.get("zmp_version") != expected_version:
        fail("WordPress bootstrap ZiloMentor version does not match installed ZIP")
    if expected_zmp and state.get("base") != folder + "/" + ENTRY:
        fail("WordPress bootstrap registered the wrong ZiloMentor plugin basename")
    return state



def verify_signed_release(package: Path, digest: str, version: str,
                          manifest_path: Path, signature_path: Path,
                          public_key_path: Path, backup: Path,
                          folder: str = FOLDER):
    """Enforce an independently pinned offline Ed25519 trust anchor."""
    if (public_key_path.is_symlink()
            or not inside(public_key_path, backup)
            or not public_key_path.is_file()
            or public_key_path.stat().st_uid != os.geteuid()):
        fail("Trusted public key must be owner-owned in private backup directory")
    if public_key_path.stat().st_mode & 0o022:
        fail("Trusted public key is group/world writable")
    if manifest_path.is_symlink() or signature_path.is_symlink():
        fail("Signature and manifest must be regular files")
    if (not manifest_path.is_file() or not signature_path.is_file()
            or manifest_path.stat().st_size > 4096):
        fail("Signed release manifest or signature unavailable")
    signature_tool = Path(__file__).resolve().with_name("release_signature.php")
    if not signature_tool.is_file():
        fail("Trusted local Ed25519 verifier is missing")
    p = subprocess.run(
        [str(PHP_CLI), str(signature_tool), "verify",
         str(manifest_path), str(public_key_path), str(signature_path)],
        capture_output=True, text=True, timeout=25,
    )
    if p.returncode != 0 or "VALID_ED25519_RELEASE_SIGNATURE" not in p.stdout:
        fail("Release manifest Ed25519 signature is invalid")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError):
        fail("Signed manifest is not valid JSON")
    expected_fields = {
        "schema", "plugin", "version", "filename", "sha256",
        "size_bytes", "issued_at", "expires_at",
    }
    if not isinstance(manifest, dict) or set(manifest) != expected_fields:
        fail("Signed manifest schema contains missing or unknown fields")
    if (
        type(manifest["schema"]) is not int or manifest["schema"] != 1
        or manifest["plugin"] != folder + "/" + ENTRY
        or manifest["version"] != version
        or manifest["filename"] != package.name
        or manifest["sha256"] != digest
        or type(manifest["size_bytes"]) is not int
        or manifest["size_bytes"] != package.stat().st_size
    ):
        fail("Signed release manifest does not describe the exact ZIP")
    try:
        issued = datetime.fromisoformat(manifest["issued_at"].replace("Z", "+00:00"))
        expires = datetime.fromisoformat(manifest["expires_at"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        valid_window = (timedelta(0) < expires - issued <= timedelta(days=180))
        if (issued.tzinfo is None or expires.tzinfo is None
                or issued > now + timedelta(minutes=5) or expires <= now
                or not valid_window):
            fail("Signed release manifest expired or has invalid timestamps")
    except (ValueError, AttributeError, TypeError):
        fail("Signed release manifest has invalid timestamps")
    return {
        "signed": True,
        "public_key_sha256": hashlib.sha256(public_key_path.read_bytes()).hexdigest(),
        "expires_at": manifest["expires_at"],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--site", type=Path, required=True)
    ap.add_argument("--backup-dir", type=Path, required=True)
    ap.add_argument("--zip", type=Path)
    ap.add_argument("--sha256")
    ap.add_argument("--folder", choices=("elementor-pro", "zilomentor-pro"),
                    default=FOLDER,
                    help="Explicit installation identity. Use zilomentor-pro for independent signed updates.")
    ap.add_argument("--signed-manifest", type=Path,
                    help="Detached-signed JSON describing this exact ZIP")
    ap.add_argument("--signature", type=Path,
                    help="Ed25519 signature file generated on an offline machine")
    ap.add_argument("--trusted-public-key", type=Path,
                    help="Previously approved public key inside private backup directory")
    ap.add_argument("--require-signature", action="store_true",
                    help="Refuse unsigned packages; required for updates from 0.1.2 onward")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--rollback", action="store_true")
    mode.add_argument("--rollback-to-official", action="store_true")
    args = ap.parse_args()
    site = args.site.resolve(strict=True)
    backup = args.backup_dir.resolve(strict=True)
    plugins = site / "wp-content" / "plugins"
    current = plugins / args.folder
    original = backup / "elementor-pro-official-original"
    if not all(x.exists() for x in (site / "wp-admin", site / "wp-includes",
                                   site / "wp-config.php", plugins)):
        fail("Not an existing WordPress installation")
    if inside(backup, site) or inside(backup, site.parent) or inside(backup, plugins):
        fail("Backup must be outside the WordPress and public_html trees")
    if not backup.is_dir() or backup.stat().st_mode & 0o077:
        fail("Backup directory must exist and have no group/world access")
    if os.geteuid() == 0 or site.stat().st_uid != os.geteuid() or (
            current.exists() and current.stat().st_uid != os.geteuid()):
        fail("Run as the WordPress filesystem owner, not root or another user")
    if not current.is_dir() or current.is_symlink():
        fail("Expected real plugin directory is missing or a symlink")
    if not (backup / "elementor-pro-official-before.tar.gz").is_file() or not (
            backup / "wordpress-before.sql").is_file():
        fail("Verified offline original-plugin and database backups required")
    if not WP_CLI.is_file() or not PHP_CLI.is_file():
        fail("Expected site-owner WP-CLI and PHP CLI not available")

    with (backup / ".zilomentor-deployment.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.folder == "zilomentor-pro" and args.rollback_to_official:
            fail("Independent plugin cannot be replaced with vendor files; roll back identity separately")
        marker = backup / (
            ".zilomentor-independent-last-previous"
            if args.folder == "zilomentor-pro" else ".zilomentor-last-previous"
        )
        if args.rollback or args.rollback_to_official:
            if plugin_name(current) != EXPECTED_NEW or plugin_name(original) != EXPECTED_CURRENT:
                fail("Rollback refused: unrecognised current or original plugin")
            chosen = original
            expected = EXPECTED_CURRENT
            if args.rollback and not marker.is_file():
                fail("No previous ZiloMentor release recorded; use --rollback-to-official explicitly")
            if args.rollback and marker.is_file():
                name = marker.read_text(encoding="utf-8").strip()
                if not re.fullmatch(re.escape(args.folder) + r"-previous-zilomentor-[\w.-]+", name):
                    fail("Invalid recorded rollback target")
                chosen = backup / name
                expected = EXPECTED_NEW
            if not chosen.is_dir() or chosen.is_symlink() or plugin_name(chosen) != expected:
                fail("Verified previous release is not present")
            if (args.rollback and version_parts(plugin_version(chosen))
                    >= version_parts(plugin_version(current))):
                fail("Previous release marker does not identify an older ZiloMentor version")
            rejected = backup / ("zilomentor-rejected-" + uuid.uuid4().hex[:8])
            os.rename(current, rejected)
            try:
                os.rename(chosen, current)
                state = wp_health(site, expected == EXPECTED_NEW,
                                  plugin_version(current) if expected == EXPECTED_NEW else None,
                                  folder=args.folder)
            except Exception:
                if current.exists():
                    os.rename(current, chosen)
                os.rename(rejected, current)
                print("ROLLBACK_HEALTH_FAILED_CURRENT_RESTORED=YES", file=sys.stderr)
                raise
            if marker.is_file():
                marker.unlink()
            print("ROLLBACK=FILES_ONLY RESTORED=" + expected)
            print("WORDPRESS_HEALTH=" + json.dumps(state, sort_keys=True))
            print("DATABASE_NOT_RESTORED=YES")
            return 0

        if not args.zip or not args.sha256 or not re.fullmatch(r"[0-9a-f]{64}", args.sha256):
            fail("Require explicit staging ZIP and full expected SHA256")
        source_zip = args.zip.resolve(strict=True)
        if not source_zip.is_file():
            fail("Missing ZIP")
        installed = plugin_name(current)
        if installed not in (EXPECTED_CURRENT, EXPECTED_NEW):
            fail("Refusing to overwrite an unrecognised plugin")
        if args.folder == "zilomentor-pro" and installed != EXPECTED_NEW:
            fail("Independent folder may only contain ZiloMentor Pro")
        is_update = installed == EXPECTED_NEW
        if is_update and plugin_name(original) != EXPECTED_CURRENT:
            fail("Private original Elementor Pro backup missing")
        if not is_update and original.exists():
            fail("Original Elementor Pro backup already exists")
        if source_zip.stat().st_size > 50 * 1024 * 1024:
            fail("Staging ZIP exceeds 50 MiB safety cap")
        digest = hashlib.sha256(source_zip.read_bytes()).hexdigest()
        if digest != args.sha256:
            fail("Staging ZIP SHA256 mismatch")
        file_count = 0
        expanded_bytes = 0
        with zipfile.ZipFile(source_zip) as z:
            bad = z.testzip()
            if bad is not None:
                fail("ZIP integrity failed")
            names = set()
            for info in z.infolist():
                n = info.filename
                parts = PurePosixPath(n).parts
                if (n.startswith("/") or "\\" in n or
                    not parts or parts[0] != args.folder or
                    ".." in parts or n in names):
                    fail("Unsafe or duplicate archive entry")
                if stat.S_ISLNK(info.external_attr >> 16):
                    fail("Symlink in release archive")
                if not info.is_dir():
                    file_count += 1
                    expanded_bytes += info.file_size
                    if expanded_bytes > 90 * 1024 * 1024:
                        fail("Release archive uncompressed size exceeds cap")
                    if (Path(n).name.lower() in ("error_log", "debug.log", ".env",
                                                   "wp-config.php")
                            or Path(n).suffix.lower() in (".log", ".sql", ".pem", ".key")):
                        fail("Runtime log, credentials or database file in ZIP")
                    if info.file_size > 15 * 1024 * 1024:
                        fail("Unreasonably large release archive member")
                names.add(n)
            if args.folder + "/" + ENTRY not in names or file_count < 1000:
                fail("Staging archive missing expected Elementor Pro-compatible layout")
            entry = z.read(args.folder + "/" + ENTRY).decode("utf-8")
            if "Plugin Name: " + EXPECTED_NEW not in entry:
                fail("Plugin release identity mismatch")
            match = re.search(r"^\s*\*?\s*Version:\s*(\d+\.\d+\.\d+)\s*$", entry, re.M)
            if not match:
                fail("Release ZIP has no valid semantic plugin version")
            target_version = match.group(1)
            if is_update and version_parts(target_version) <= version_parts(plugin_version(current)):
                fail("Refusing non-increasing ZiloMentor version")
        signature_parts = (
            args.signed_manifest, args.signature, args.trusted_public_key,
        )
        if any(part is not None for part in signature_parts) and not all(
            part is not None for part in signature_parts
        ):
            fail("Must provide manifest, signature and trusted public key together")
        # New signed-release series must never fall back to the legacy
        # caller-supplied SHA256 alone. Existing earlier deployments retain
        # the explicit legacy mode to allow emergency rollback.
        signature_required = (args.require_signature
                              or args.folder == "zilomentor-pro"
                              or version_parts(target_version) >= (0, 1, 2))
        if signature_required and not all(part is not None for part in signature_parts):
            fail("This release requires an independently signed manifest")
        signature_info = {"signed": False}
        if all(part is not None for part in signature_parts):
            signature_info = verify_signed_release(
                source_zip, digest, target_version,
                args.signed_manifest, args.signature,
                args.trusted_public_key, backup,
                folder=args.folder,
            )
        print("PREFLIGHT_OK=" + json.dumps({
            "current":installed, "next":EXPECTED_NEW,
            "target_version":target_version,"is_update":is_update,
            "plugin_basename": args.folder + "/" + ENTRY,
            "sha256":digest, "files":file_count,
            "siteOwner":os.geteuid(), "privateBackup":True,
            "release_signature": signature_info,
        }, sort_keys=True))
        if not args.apply:
            print("DRY_RUN=YES; no WordPress files changed")
            return 0

        stage_parent = plugins / (".zilomentor-stage-" + uuid.uuid4().hex[:10])
        stage_parent.mkdir(mode=0o700)
        try:
            with zipfile.ZipFile(source_zip) as z:
                z.extractall(stage_parent)
            stage_plugin = stage_parent / args.folder
            if plugin_name(stage_plugin) != EXPECTED_NEW:
                fail("Extracted plugin header mismatch")
            if not (stage_plugin / "plugin.php").is_file():
                fail("Extracted plugin internals are missing")
            prior_dest = (backup / (args.folder + "-previous-zilomentor-"
                          + plugin_version(current) + "-" + uuid.uuid4().hex[:8])
                          if is_update else original)
            os.rename(current, prior_dest)
            try:
                os.rename(stage_plugin, current)
                state = wp_health(site, True, target_version, folder=args.folder)
            except Exception:
                rejected = backup / ("zilomentor-failed-" + uuid.uuid4().hex[:8])
                if current.exists():
                    os.rename(current, rejected)
                os.rename(prior_dest, current)
                print("AUTOMATIC_FILE_ROLLBACK=YES", file=sys.stderr)
                raise
            if is_update:
                marker.write_text(prior_dest.name + "\n", encoding="utf-8")
                marker.chmod(0o600)
            print("DEPLOYED=YES; IS_UPDATE=" + str(is_update).lower())
            print("WORDPRESS_HEALTH=" + json.dumps(state, sort_keys=True))
            print("ORIGINAL_PLUGIN_PRIVATE_BACKUP=YES")
            print("DATABASE_NOT_RESTORED=YES")
        finally:
            if stage_parent.exists():
                shutil.rmtree(stage_parent)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("ERROR=" + str(error), file=sys.stderr)
        sys.exit(1)
