#!/usr/bin/env python3
"""Migrate the VERIFIED existing ZiloMentor 0.1.1 files to a unique plugin folder.

This is a basename migration, NOT a software update. The installed PHP bytes
must exactly match a previously trusted ZIP. WordPress gets a single atomic
active_plugins option change; orders/customers and other options are untouched.

By default this script performs read-only preflight.
  python3 tools/migrate_independent_identity.py --site /path/to/wp \
    --backup-dir /private/backup --zip /trusted/0.1.1.zip --sha256 HEX
  ... --apply       # guarded migration; preserves old plugin files privately
  ... --rollback    # restores old path; keeps independent code privately

Run as the exact WordPress filesystem owner, not root. Only one site at a time.
A fresh independent database backup is required before --apply.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import stat
import subprocess
import sys
import zipfile

LEGACY = "elementor-pro"
INDEPENDENT = "zilomentor-pro"
ENTRY = "elementor-pro.php"
EXPECTED_VERSION = "0.1.1"
WP_CLI = Path("/usr/local/bin/wp")
PHP_CLI = Path("/opt/cpanel/ea-php84/root/usr/bin/php")
STATE_FILENAME = ".zilomentor-independent-identity-state.json"


def abort(message):
    raise RuntimeError(message)


def plugin_header(directory):
    path = directory / ENTRY
    if not path.is_file() or path.is_symlink():
        return ("", "")
    header = path.read_text(encoding="utf-8", errors="replace")[:4096]
    n = re.search(r"^\s*\*\s*Plugin Name:\s*([^\r\n]+)", header, re.M)
    v = re.search(r"^\s*\*\s*Version:\s*([^\r\n]+)", header, re.M)
    return (n.group(1).strip() if n else "", v.group(1).strip() if v else "")


def wp_eval(site, source):
    result = subprocess.run(
        [str(PHP_CLI), str(WP_CLI), "--path=" + str(site), "eval", source],
        capture_output=True, text=True, timeout=95,
    )
    if result.returncode != 0:
        abort("WordPress CLI verification failed; output intentionally withheld")
    try:
        return json.loads(result.stdout.strip())
    except ValueError:
        abort("Unexpected WordPress verification response")


def wp_state(site):
    return wp_eval(site, (
        'if(is_multisite()){echo wp_json_encode(["multisite"=>true]);return;}'
        '$a=(array)get_option("active_plugins",[]);'
        'echo wp_json_encode(["multisite"=>false,'
        '"legacy"=>in_array("elementor-pro/elementor-pro.php",$a,true),'
        '"independent"=>in_array("zilomentor-pro/elementor-pro.php",$a,true),'
        '"identity"=>defined("ZILOMENTOR_VERSION")?ZILOMENTOR_VERSION:null,'
        '"base"=>defined("ELEMENTOR_PRO_PLUGIN_BASE")?ELEMENTOR_PRO_PLUGIN_BASE:null,'
        '"elementor"=>did_action("elementor/loaded")>0,'
        '"early_bootstrap"=>defined("ZMP_EARLY_COMPAT_BOOTSTRAP"),'
        '"woocommerce"=>class_exists("WooCommerce")]);'
    ))


def switch_active_plugin(site, src, dst):
    assert src in (LEGACY, INDEPENDENT) and dst in (LEGACY, INDEPENDENT) and src != dst
    code = (
        '$src="' + src + '/elementor-pro.php";'
        '$dst="' + dst + '/elementor-pro.php";'
        '$p=(array)get_option("active_plugins",[]);'
        '$count=array_count_values($p);'
        'if(($count[$src]??0)!==1||!empty($count[$dst])){'
        'echo wp_json_encode(["ok"=>false]);return;}'
        '$i=array_search($src,$p,true);$p[$i]=$dst;sort($p,SORT_STRING);'
        '$r=update_option("active_plugins",$p);'
        '$q=(array)get_option("active_plugins",[]);'
        'echo wp_json_encode(["ok"=>in_array($dst,$q,true)&&'
        '!in_array($src,$q,true)]);'
    )
    result = wp_eval(site, code)
    if result.get("ok") is not True:
        abort("WordPress refused active plugin identity change")


def verify_archive(archive_path, current, sha256):
    if not re.fullmatch(r"[a-f0-9]{64}", sha256):
        abort("Expected pinned full SHA-256 digest")
    if archive_path.stat().st_size > 50 * 1024 * 1024:
        abort("Release archive unreasonably large")
    if hashlib.sha256(archive_path.read_bytes()).hexdigest() != sha256:
        abort("Release archive hash mismatch")
    expected_files = set()
    with zipfile.ZipFile(archive_path) as z:
        if z.testzip() is not None:
            abort("Release ZIP integrity failure")
        expanded_bytes = 0
        for item in z.infolist():
            name = item.filename
            parts = PurePosixPath(name).parts
            if (not parts or parts[0] != LEGACY or name.startswith("/")
                    or "\\" in name or ".." in parts or
                    stat.S_ISLNK(item.external_attr >> 16)):
                abort("Unsafe release ZIP entry")
            if item.is_dir():
                continue
            expanded_bytes += item.file_size
            if expanded_bytes > 90 * 1024 * 1024:
                abort("Release archive expanded size exceeds cap")
            rel = Path(*parts[1:])
            if rel in expected_files:
                abort("Repeated archive member")
            expected_files.add(rel)
            source_path = current / rel
            if (not source_path.is_file() or source_path.is_symlink()
                    or hashlib.sha256(source_path.read_bytes()).digest() !=
                    hashlib.sha256(z.read(item)).digest()):
                abort("Installed file does not match trusted release: " + str(rel))
    actual_files = {
        path.relative_to(current) for path in current.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if expected_files != actual_files or len(expected_files) < 1000:
        abort("Installed plugin contains missing or unexpected files")
    if plugin_header(current) != ("ZiloMentor Pro", EXPECTED_VERSION):
        abort("Installed plugin is not the expected trusted ZiloMentor beta")
    return len(expected_files)


def store_state(path, state):
    if path.is_symlink():
        abort("Unsafe symlink at migration state file")
    temp = path.parent / (".zmp-state-" + secrets.token_hex(6))
    try:
        temp.write_text(json.dumps(state, sort_keys=True) + "\n", encoding="utf-8")
        temp.chmod(0o600)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def require_identity(site, folder):
    s = wp_state(site)
    wanted = folder == INDEPENDENT
    if not (
        s.get("multisite") is False
        and s.get("independent") is wanted
        and s.get("legacy") is not wanted
        and s.get("identity") == EXPECTED_VERSION
        and s.get("base") == folder + "/" + ENTRY
        and s.get("elementor") is True
        and s.get("early_bootstrap") is wanted
        and s.get("woocommerce") is True
    ):
        abort("WordPress / Elementor / WooCommerce did not bootstrap with expected plugin basename")
    return s


def main():
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("--site", required=True, type=Path)
    argp.add_argument("--backup-dir", required=True, type=Path)
    argp.add_argument("--zip", type=Path)
    argp.add_argument(
        "--database-backup", type=Path,
        help="Fresh private pre-migration SQL snapshot, less than two hours old.",
    )
    argp.add_argument("--sha256")
    operation = argp.add_mutually_exclusive_group()
    operation.add_argument("--apply", action="store_true")
    operation.add_argument("--rollback", action="store_true")
    args = argp.parse_args()

    site = args.site.resolve(strict=True)
    backup = args.backup_dir.resolve(strict=True)
    plugins = site / "wp-content" / "plugins"
    legacy = plugins / LEGACY
    independent = plugins / INDEPENDENT
    state_file = backup / STATE_FILENAME
    if (os.geteuid() == 0 or os.geteuid() != site.stat().st_uid
            or plugins.stat().st_uid != os.geteuid()):
        abort("Run only as the WordPress filesystem owner (never root)")
    if backup.stat().st_uid != os.geteuid() or backup.stat().st_mode & 0o077:
        abort("A private, owner-owned backup directory is required")
    if site == backup or site in backup.parents or backup in site.parents:
        abort("Backups must be outside the WordPress tree")
    if not (site / "wp-config.php").is_file() or not WP_CLI.is_file() or not PHP_CLI.is_file():
        abort("WordPress installation or required CLI is missing")
    if args.database_backup is None:
        abort("An explicitly selected fresh private database snapshot is required")
    db_snapshot = args.database_backup.resolve(strict=True)
    if (args.database_backup.is_symlink() or db_snapshot.parent != backup
            or not db_snapshot.name.startswith("wordpress-before-identity-")
            or db_snapshot.suffix != ".sql"
            or not db_snapshot.is_file()
            or db_snapshot.stat().st_uid != os.geteuid()
            or db_snapshot.stat().st_mode & 0o077
            or db_snapshot.stat().st_size == 0
            or not 0 <= datetime.now(timezone.utc).timestamp() - db_snapshot.stat().st_mtime < 7200):
        abort("A private, owner-only SQL snapshot newer than two hours is required")
    guard = site / "wp-content" / "mu-plugins" / "zmp-release-guard.php"
    if not guard.is_file() or "Version: 0.2.0" not in guard.read_text()[:600]:
        abort("Independent-compatible external must-use release guard must be installed first")
    early = site / "wp-content" / "mu-plugins" / "zmp-early-bootstrap.php"
    if (not early.is_file() or early.is_symlink()
            or early.stat().st_uid != os.geteuid()
            or "Version: 0.1.0" not in early.read_text(encoding="utf-8")[:800]):
        abort("Tested independent MU compatibility bootstrap must be installed first")

    with (backup / ".zilomentor-deployment.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        initial = wp_state(site)
        if initial.get("multisite") is not False:
            abort("Multisite migration not supported")

        if args.rollback:
            if not state_file.is_file():
                abort("No recorded identity migration to roll back")
            state = json.loads(state_file.read_text())
            if state.get("status") != "migrated" or state.get("version") != EXPECTED_VERSION:
                abort("Migration state not in a recoverable status")
            saved = backup / state["legacy_backup_name"]
            if (not re.fullmatch(r"elementor-pro-identity-backup-[a-f0-9]{12}",
                                 state["legacy_backup_name"])
                    or not saved.is_dir() or saved.is_symlink()
                    or plugin_header(saved) != ("ZiloMentor Pro", EXPECTED_VERSION)
                    or not independent.is_dir() or legacy.exists()
                    or initial.get("independent") is not True or initial.get("legacy") is not False):
                abort("Cannot safely restore legacy identity")
            os.rename(saved, legacy)
            legacy.chmod(0o755)
            try:
                switch_active_plugin(site, INDEPENDENT, LEGACY)
                require_identity(site, LEGACY)
            except Exception:
                try:
                    switch_active_plugin(site, LEGACY, INDEPENDENT)
                finally:
                    os.rename(legacy, saved)
                raise
            rejected = backup / ("zilomentor-independent-rolled-back-" + secrets.token_hex(6))
            os.rename(independent, rejected)
            state["status"] = "rolled_back"
            state["independent_backup_name"] = rejected.name
            store_state(state_file, state)
            print("IDENTITY_ROLLBACK=YES")
            print("PLUGIN_BASE=" + LEGACY + "/" + ENTRY)
            print("DATABASE_BACKUP_NOT_RESTORED=YES")
            return

        if args.zip is None or args.sha256 is None:
            abort("Read-only preflight requires trusted 0.1.1 ZIP and full SHA256")
        if (not legacy.is_dir() or legacy.is_symlink()
                or independent.exists() or state_file.exists()
                or initial.get("legacy") is not True or initial.get("independent") is not False):
            abort("Site is not in a safe, active legacy state")
        archive = args.zip.resolve(strict=True)
        count = verify_archive(archive, legacy, args.sha256)
        require_identity(site, LEGACY)
        print("FRESH_PRIVATE_DATABASE_BACKUP_VERIFIED=YES")
        print("IDENTITY_PREFLIGHT_OK=" + json.dumps({
            "source": LEGACY + "/" + ENTRY, "destination": INDEPENDENT + "/" + ENTRY,
            "version": EXPECTED_VERSION, "files_verified": count,
            "hash": args.sha256, "guard_version": "0.2.0",
        }, sort_keys=True))
        if not args.apply:
            print("DRY_RUN=YES NO_DATABASE_OR_PLUGINS_CHANGED")
            return

        stage = plugins / (".zilomentor-identity-stage-" + secrets.token_hex(5))
        stage.mkdir(mode=0o700)
        archived_name = "elementor-pro-identity-backup-" + secrets.token_hex(6)
        state = {
            "status": "preparing", "version": EXPECTED_VERSION,
            "legacy_backup_name": archived_name, "source_sha256": args.sha256,
            "created_utc": datetime.now(timezone.utc).isoformat(),
        }
        try:
            with zipfile.ZipFile(archive) as z:
                z.extractall(stage)
            unpacked = stage / LEGACY
            if plugin_header(unpacked) != ("ZiloMentor Pro", EXPECTED_VERSION):
                abort("Extracted plugin identity is invalid")
            for root, dirs, files in os.walk(unpacked):
                for d in dirs:
                    (Path(root) / d).chmod(0o755)
                for name in files:
                    (Path(root) / name).chmod(0o644)
            unpacked.chmod(0o755)
            os.rename(unpacked, independent)
            original_backed_up = False
            try:
                switch_active_plugin(site, LEGACY, INDEPENDENT)
                require_identity(site, INDEPENDENT)
                os.rename(legacy, backup / archived_name)
                original_backed_up = True
                (backup / archived_name).chmod(0o700)
                state["status"] = "migrated"
                store_state(state_file, state)
            except Exception:
                # Roll back even if moving the legacy files or recording
                # migration state failed *after* the WordPress switch.
                if original_backed_up and not legacy.exists():
                    os.rename(backup / archived_name, legacy)
                    legacy.chmod(0o755)
                try:
                    present = wp_state(site)
                    if present.get("independent") is True:
                        switch_active_plugin(site, INDEPENDENT, LEGACY)
                finally:
                    # Do not delete a plugin still recorded as active if the
                    # WordPress rollback itself encountered a failure.
                    if wp_state(site).get("independent") is False and independent.exists():
                        shutil.rmtree(independent)
                raise
            print("MIGRATION_SUCCEEDED=YES")
            print("PLUGIN_BASE=" + INDEPENDENT + "/" + ENTRY)
            print("SOURCE_PLUGIN_FILES_PRIVATE=YES")
            print("DATABASE_BACKUP_NOT_RESTORED=YES")
        finally:
            if stage.exists():
                shutil.rmtree(stage)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("IDENTITY_MIGRATION_ERROR=" + str(error), file=sys.stderr)
        sys.exit(1)
