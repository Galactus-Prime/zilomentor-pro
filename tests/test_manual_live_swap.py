#!/usr/bin/env python3
"""Synthetic-only filesystem tests for safe manual release/rollback. No WordPress DB."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import hashlib
import importlib.util
import os
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
            side_effect=lambda site, expected_zmp, version=None: {
                "zmp":expected_zmp, "version":version,
                "pro":True,"core":True,"class":True,"wc":True,
            })
        self.health_patch.start()
        self.addCleanup(self.health_patch.stop)

    def zip(self, version, unsafe=False):
        out = self.root / ("zmp-" + version + ("-evil" if unsafe else "") + ".zip")
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("elementor-pro/elementor-pro.php",
                       plugin_text("ZiloMentor Pro", version))
            z.writestr("elementor-pro/plugin.php", "<?php // synthetic\n")
            for n in range(1002):
                z.writestr("elementor-pro/assets/test-%04d.txt" % n, "qa")
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

    def test_bad_hash_and_unsafe_archive_never_swap_files(self):
        package, digest = self.zip("0.1.0")
        with self.assertRaisesRegex(RuntimeError, "SHA256 mismatch"):
            self.run_command("--zip", str(package), "--sha256", "0" * 64, "--apply")
        self.assertEqual(swap.plugin_name(self.plugin), "Elementor Pro")
        evil, evil_digest = self.zip("0.1.0", unsafe=True)
        with self.assertRaisesRegex(RuntimeError, "Unsafe"):
            self.run_command("--zip", str(evil), "--sha256", evil_digest, "--apply")
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
