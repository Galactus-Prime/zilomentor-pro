#!/usr/bin/env python3
"""Synthetic-only filesystem tests for safe manual release/rollback. No WordPress DB."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import hashlib
from datetime import datetime, timedelta, timezone
import json
import importlib.util
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SOURCE = Path(__file__).resolve().parents[1] / "tools" / "manual_live_swap.py"
spec = importlib.util.spec_from_file_location("manual_live_swap", SOURCE)
swap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(swap)


def plugin_text(name, version):
    return ("<?php\n/**\n * Plugin Name: " + name +
            "\n * Version: " + version + "\n */\n")


class ManualSwapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="zmp-swap-synthetic-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.site = self.root / "public_html" / "shop" / "site"
        self.plugin = self.site / "wp-content" / "plugins" / "elementor-pro"
        self.plugin.mkdir(parents=True)
        (self.site / "wp-admin").mkdir()
        (self.site / "wp-includes").mkdir()
        (self.site / "wp-config.php").write_text("<?php // no secrets\n")
        (self.plugin / "elementor-pro.php").write_text(
            plugin_text("Elementor Pro", "4.4.0"))
        self.backup = self.root / "private" / "backup"
        self.backup.mkdir(parents=True, mode=0o700)
        self.backup.chmod(0o700)
        (self.backup / "wordpress-before.sql").write_text("-- no data\n")
        (self.backup / "elementor-pro-official-before.tar.gz").write_bytes(b"synthetic")
        self.bin = self.root / "bin"
        self.bin.mkdir()
        php = self.bin / "php"
        wp = self.bin / "wp"
        php.write_text("synthetic")
        wp.write_text("synthetic")
        self.bin_patch = patch.multiple(swap, PHP_CLI=php, WP_CLI=wp)
        self.bin_patch.start()
        self.addCleanup(self.bin_patch.stop)

        self.health_patch = patch.object(
            swap, "wp_health",
            side_effect=lambda site, expected_zmp, version=None, folder=None: {
                "zmp":expected_zmp, "version":version,
                "pro":True,"core":True,"class":True,"wc":True,
            })
        self.health_patch.start()
        self.addCleanup(self.health_patch.stop)

    def zip(self, version, unsafe=False, folder="elementor-pro"):
        out = self.root / ("zmp-" + folder + "-" + version +
                           ("-evil" if unsafe else "") + ".zip")
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(folder + "/elementor-pro.php",
                       plugin_text("ZiloMentor Pro", version))
            z.writestr(folder + "/plugin.php", "<?php // synthetic\n")
            for n in range(1002):
                z.writestr(folder + "/assets/test-%04d.txt" % n, "qa")
            if unsafe:
                z.writestr("../escape.txt", "not allowed")
        return out, hashlib.sha256(out.read_bytes()).hexdigest()

    def run_command(self, *argv):
        with patch.object(sys, "argv", ["manual_live_swap.py", "--site",
                                        str(self.site), "--backup-dir",
                                        str(self.backup), *argv]):
            stdout = StringIO()
            with redirect_stdout(stdout):
                swap.main()
            return stdout.getvalue()

    def test_signing_private_key_never_generated_in_repository(self):
        sodium_php = Path("/opt/cpanel/ea-php84/root/usr/bin/php")
        if not sodium_php.is_file():
            self.skipTest("No PHP CLI with Sodium")
        repository = self.root / "synthetic-git-checkout"
        (repository / ".git").mkdir(parents=True)
        priv = repository / "forbidden-private.key"
        pub = repository / "forbidden-public.key"
        verifier = SOURCE.with_name("release_signature.php")
        result = subprocess.run(
            [str(sodium_php), str(verifier), "generate",
             str(priv), str(pub)],
            capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(priv.exists())
        self.assertFalse(pub.exists())

    def test_unsigned_release_012_fails_closed(self):
        package, digest = self.zip("0.1.2")
        with self.assertRaisesRegex(RuntimeError, "requires an independently signed"):
            self.run_command("--zip", str(package), "--sha256", digest, "--apply")
        self.assertEqual(swap.plugin_name(self.plugin), "Elementor Pro")

    def test_offline_ed25519_manifest_and_tamper_rejection(self):
        sodium_php = Path("/opt/cpanel/ea-php84/root/usr/bin/php")
        if not sodium_php.is_file():
            self.skipTest("No PHP CLI with Sodium")
        verifier = SOURCE.with_name("release_signature.php")
        package, digest = self.zip("0.1.2")
        private = self.backup / "synthetic-private-only-in-test.b64"
        public = self.backup / "trusted-release-public.b64"
        signature = self.root / "release.sig"
        manifest_path = self.root / "release.json"
        subprocess.run([str(sodium_php), str(verifier), "generate",
                        str(private), str(public)], check=True,
                       capture_output=True, text=True)
        now = datetime.now(timezone.utc).replace(microsecond=0)
        manifest = {
            "schema": 1, "plugin": "elementor-pro/elementor-pro.php",
            "version": "0.1.2", "filename": package.name,
            "sha256": digest, "size_bytes": package.stat().st_size,
            "issued_at": now.isoformat().replace("+00:00", "Z"),
            "expires_at": (now + timedelta(days=30)).isoformat().replace("+00:00", "Z"),
        }
        manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n")
        subprocess.run([str(sodium_php), str(verifier), "sign",
                        str(manifest_path), str(private), str(signature)],
                       check=True, capture_output=True, text=True)
        signed = ("--zip", str(package), "--sha256", digest,
                  "--signed-manifest", str(manifest_path),
                  "--signature", str(signature),
                  "--trusted-public-key", str(public))
        with patch.object(swap, "PHP_CLI", sodium_php):
            preflight = self.run_command(*signed, "--require-signature")
            self.assertIn('"signed": true', preflight)
            self.assertIn("DRY_RUN=YES", preflight)
            installed = self.run_command(*signed, "--apply")
            self.assertIn("DEPLOYED=YES", installed)
            self.assertEqual(swap.plugin_version(self.plugin), "0.1.2")
            # The signature covers the EXACT manifest bytes, so a single
            # character modification must fail before touching installed files.
            manifest_path.write_text(json.dumps({**manifest, "size_bytes": 1}) + "\n")
            with self.assertRaisesRegex(RuntimeError, "Ed25519 signature is invalid"):
                swap.verify_signed_release(
                    package, digest, "0.1.2", manifest_path,
                    signature, public, self.backup,
                )
            self.assertEqual(swap.plugin_version(self.plugin), "0.1.2")
            # Restore valid signature and independently reject an expired
            # manifest even if it was signed by the trusted key.
            expired = dict(manifest)
            expired["issued_at"] = (now - timedelta(days=32)).isoformat().replace("+00:00", "Z")
            expired["expires_at"] = (now - timedelta(days=1)).isoformat().replace("+00:00", "Z")
            expired_path = self.root / "expired.json"
            expired_sig = self.root / "expired.sig"
            expired_path.write_text(json.dumps(expired) + "\n")
            subprocess.run([str(sodium_php), str(verifier), "sign",
                            str(expired_path), str(private), str(expired_sig)],
                           check=True, capture_output=True, text=True)
            with self.assertRaisesRegex(RuntimeError, "expired or has invalid"):
                swap.verify_signed_release(
                    package, digest, "0.1.2", expired_path,
                    expired_sig, public, self.backup,
                )

    def test_verified_first_deploy_update_and_both_rollbacks(self):
        package_010, hash_010 = self.zip("0.1.0")
        base = ("--zip", str(package_010), "--sha256", hash_010)
        pre = self.run_command(*base)
        self.assertIn("DRY_RUN=YES", pre)
        self.assertEqual(swap.plugin_name(self.plugin), "Elementor Pro")
        initial = self.run_command(*base, "--apply")
        self.assertIn("DEPLOYED=YES", initial)
        self.assertEqual(swap.plugin_version(self.plugin), "0.1.0")
        self.assertEqual(swap.plugin_name(
            self.backup / "elementor-pro-official-original"), "Elementor Pro")
        package_011, hash_011 = self.zip("0.1.1")
        new = self.run_command("--zip", str(package_011),
                               "--sha256", hash_011, "--apply")
        self.assertIn("IS_UPDATE=true", new)
        self.assertEqual(swap.plugin_version(self.plugin), "0.1.1")
        self.assertTrue((self.backup / ".zilomentor-last-previous").is_file())
        rolled = self.run_command("--rollback")
        self.assertIn("RESTORED=ZiloMentor Pro", rolled)
        self.assertEqual(swap.plugin_version(self.plugin), "0.1.0")
        final = self.run_command("--rollback-to-official")
        self.assertIn("RESTORED=Elementor Pro", final)
        self.assertEqual(swap.plugin_name(self.plugin), "Elementor Pro")
        self.assertTrue((self.backup / "wordpress-before.sql").is_file())

    def test_previous_rollback_never_silently_restores_official(self):
        package, digest = self.zip("0.1.0")
        self.run_command("--zip", str(package), "--sha256", digest, "--apply")
        with self.assertRaisesRegex(RuntimeError, "use --rollback-to-official"):
            self.run_command("--rollback")
        self.assertEqual(swap.plugin_version(self.plugin), "0.1.0")
        restored = self.run_command("--rollback-to-official")
        self.assertIn("RESTORED=Elementor Pro", restored)
        self.assertEqual(swap.plugin_name(self.plugin), "Elementor Pro")

    def test_independent_signed_update_preserves_basename_and_rollback(self):
        sodium_php = Path("/opt/cpanel/ea-php84/root/usr/bin/php")
        if not sodium_php.is_file():
            self.skipTest("No PHP CLI Sodium")
        new_folder = self.plugin.parent / "zilomentor-pro"
        (self.plugin / "elementor-pro.php").write_text(
            plugin_text("ZiloMentor Pro", "0.1.1")
        )
        os.rename(self.plugin, new_folder)
        official = self.backup / "elementor-pro-official-original"
        official.mkdir()
        (official / "elementor-pro.php").write_text(
            plugin_text("Elementor Pro", "4.4.0")
        )
        package, digest = self.zip("0.1.2", folder="zilomentor-pro")
        verifier = SOURCE.with_name("release_signature.php")
        private = self.backup / "synthetic-private-key.b64"
        public = self.backup / "trusted-release-key.b64"
        manifest_path = self.root / "independent.json"
        sig = self.root / "independent.sig"
        subprocess.run([str(sodium_php), str(verifier), "generate",
                        str(private), str(public)], check=True,
                       capture_output=True, text=True)
        issued = datetime.now(timezone.utc).replace(microsecond=0)
        manifest = {
            "schema": 1,
            "plugin": "zilomentor-pro/elementor-pro.php",
            "version": "0.1.2",
            "filename": package.name,
            "sha256": digest,
            "size_bytes": package.stat().st_size,
            "issued_at": issued.isoformat().replace("+00:00", "Z"),
            "expires_at": (issued + timedelta(days=21)).isoformat().replace("+00:00", "Z"),
        }
        manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n")
        subprocess.run([str(sodium_php), str(verifier), "sign",
                        str(manifest_path), str(private), str(sig)],
                       check=True, capture_output=True, text=True)
        with patch.object(swap, "PHP_CLI", sodium_php):
            with self.assertRaisesRegex(RuntimeError, "signed manifest"):
                self.run_command(
                    "--folder", "zilomentor-pro", "--zip", str(package),
                    "--sha256", digest, "--apply",
                )
            arguments = (
                "--folder", "zilomentor-pro", "--zip", str(package),
                "--sha256", digest, "--signed-manifest", str(manifest_path),
                "--signature", str(sig), "--trusted-public-key", str(public),
            )
            self.assertIn("DRY_RUN=YES", self.run_command(*arguments))
            deployed = self.run_command(*arguments, "--apply")
            self.assertIn("IS_UPDATE=true", deployed)
            self.assertEqual(swap.plugin_version(new_folder), "0.1.2")
            self.assertFalse(self.plugin.exists())
            self.assertTrue((self.backup / ".zilomentor-independent-last-previous").is_file())
            with self.assertRaisesRegex(RuntimeError, "cannot be replaced with vendor"):
                self.run_command("--folder", "zilomentor-pro", "--rollback-to-official")
            reverted = self.run_command("--folder", "zilomentor-pro", "--rollback")
            self.assertIn("RESTORED=ZiloMentor Pro", reverted)
            self.assertEqual(swap.plugin_version(new_folder), "0.1.1")
            self.assertFalse(self.plugin.exists())

    def test_bad_hash_and_unsafe_archive_never_swap_files(self):
        package, digest = self.zip("0.1.0")
        with self.assertRaisesRegex(RuntimeError, "SHA256 mismatch"):
            self.run_command("--zip", str(package), "--sha256", "0" * 64, "--apply")
        self.assertEqual(swap.plugin_name(self.plugin), "Elementor Pro")
        evil, evil_digest = self.zip("0.1.0", unsafe=True)
        with self.assertRaisesRegex(RuntimeError, "Unsafe"):
            self.run_command("--zip", str(evil), "--sha256", evil_digest, "--apply")
        self.assertEqual(swap.plugin_name(self.plugin), "Elementor Pro")

    def test_zip_bomb_metadata_is_rejected_before_decompression(self):
        # Forge a 600 MiB expanded entry in a tiny valid synthetic ZIP.
        # Its central-directory metadata must be rejected before testzip().
        package, _ = self.zip("0.1.0")
        blob = bytearray(package.read_bytes())
        first = blob.find(b"PK\\x01\\x02")
        second = blob.find(b"PK\\x01\\x02", first + 4)
        self.assertGreaterEqual(first, 0)
        self.assertGreater(second, first)
        struct.pack_into("<I", blob, second + 24, 600 * 1024 * 1024)
        package.write_bytes(blob)
        digest = hashlib.sha256(blob).hexdigest()
        with patch.object(zipfile.ZipFile, "testzip",
                          side_effect=AssertionError("decompressed before size validation")):
            with self.assertRaisesRegex(RuntimeError, "uncompressed size exceeds cap"):
                self.run_command("--zip", str(package), "--sha256", digest)
        self.assertEqual(swap.plugin_name(self.plugin), "Elementor Pro")

    def test_downgrade_rejected_before_any_files_move(self):
        new, new_digest = self.zip("0.1.1")
        self.run_command("--zip", str(new), "--sha256", new_digest, "--apply")
        old, old_digest = self.zip("0.1.0")
        with self.assertRaisesRegex(RuntimeError, "non-increasing"):
            self.run_command("--zip", str(old), "--sha256", old_digest, "--apply")
        self.assertEqual(swap.plugin_version(self.plugin), "0.1.1")
        self.assertFalse((self.backup / ".zilomentor-last-previous").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
