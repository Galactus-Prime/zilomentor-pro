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


def wp_health(site: Path, expected_zmp: bool, expected_version: str | None = None):
    php = str(PHP_CLI)
    cli = str(WP_CLI)
    code = (
        '$r=["zmp"=>defined("ZILOMENTOR_VERSION"),'
        '"zmp_version"=>defined("ZILOMENTOR_VERSION")?ZILOMENTOR_VERSION:null,'
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
    return state


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--site", type=Path, required=True)
    ap.add_argument("--backup-dir", type=Path, required=True)
    ap.add_argument("--zip", type=Path)
    ap.add_argument("--sha256")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--rollback", action="store_true")
    mode.add_argument("--rollback-to-official", action="store_true")
    args = ap.parse_args()
    site = args.site.resolve(strict=True)
    backup = args.backup_dir.resolve(strict=True)
    plugins = site / "wp-content" / "plugins"
    current = plugins / FOLDER
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
        marker = backup / ".zilomentor-last-previous"
        if args.rollback or args.rollback_to_official:
            if plugin_name(current) != EXPECTED_NEW or plugin_name(original) != EXPECTED_CURRENT:
                fail("Rollback refused: unrecognised current or original plugin")
            chosen = original
            expected = EXPECTED_CURRENT
            if args.rollback and marker.is_file():
                name = marker.read_text(encoding="utf-8").strip()
                if not re.fullmatch(r"elementor-pro-previous-zilomentor-[\w.-]+", name):
                    fail("Invalid recorded rollback target")
                chosen = backup / name
                expected = EXPECTED_NEW
            if not chosen.is_dir() or chosen.is_symlink() or plugin_name(chosen) != expected:
                fail("Verified previous release is not present")
            rejected = backup / ("zilomentor-rejected-" + uuid.uuid4().hex[:8])
            os.rename(current, rejected)
            try:
                os.rename(chosen, current)
                state = wp_health(site, expected == EXPECTED_NEW,
                                  plugin_version(current) if expected == EXPECTED_NEW else None)
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
        with zipfile.ZipFile(source_zip) as z:
            bad = z.testzip()
            if bad is not None:
                fail("ZIP integrity failed")
            names = set()
            for info in z.infolist():
                n = info.filename
                parts = PurePosixPath(n).parts
                if (n.startswith("/") or "\\" in n or
                    not parts or parts[0] != FOLDER or
                    ".." in parts or n in names):
                    fail("Unsafe or duplicate archive entry")
                if stat.S_ISLNK(info.external_attr >> 16):
                    fail("Symlink in release archive")
                if not info.is_dir():
                    file_count += 1
                    if info.file_size > 15 * 1024 * 1024:
                        fail("Unreasonably large release archive member")
                names.add(n)
            if FOLDER + "/" + ENTRY not in names or file_count < 1000:
                fail("Staging archive missing expected Elementor Pro-compatible layout")
            entry = z.read(FOLDER + "/" + ENTRY).decode("utf-8")
            if "Plugin Name: " + EXPECTED_NEW not in entry:
                fail("Plugin release identity mismatch")
            match = re.search(r"^\s*\*?\s*Version:\s*(\d+\.\d+\.\d+)\s*$", entry, re.M)
            if not match:
                fail("Release ZIP has no valid semantic plugin version")
            target_version = match.group(1)
            if is_update and version_parts(target_version) <= version_parts(plugin_version(current)):
                fail("Refusing non-increasing ZiloMentor version")
        print("PREFLIGHT_OK=" + json.dumps({
            "current":installed, "next":EXPECTED_NEW,
            "target_version":target_version,"is_update":is_update,
            "sha256":digest, "files":file_count,
            "siteOwner":os.geteuid(), "privateBackup":True,
        }, sort_keys=True))
        if not args.apply:
            print("DRY_RUN=YES; no WordPress files changed")
            return 0

        stage_parent = plugins / (".zilomentor-stage-" + uuid.uuid4().hex[:10])
        stage_parent.mkdir(mode=0o700)
        try:
            with zipfile.ZipFile(source_zip) as z:
                z.extractall(stage_parent)
            stage_plugin = stage_parent / FOLDER
            if plugin_name(stage_plugin) != EXPECTED_NEW:
                fail("Extracted plugin header mismatch")
            if not (stage_plugin / "plugin.php").is_file():
                fail("Extracted plugin internals are missing")
            prior_dest = (backup / ("elementor-pro-previous-zilomentor-"
                          + plugin_version(current) + "-" + uuid.uuid4().hex[:8])
                          if is_update else original)
            os.rename(current, prior_dest)
            try:
                os.rename(stage_plugin, current)
                state = wp_health(site, True, target_version)
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
