#!/usr/bin/env python3
"""Synthetic-only initial identity migration, rollback and refusal tests."""
from contextlib import redirect_stdout
import hashlib
import importlib.util
from io import StringIO
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SOURCE = Path(__file__).resolve().parents[1] / "tools" / "migrate_independent_identity.py"
spec = importlib.util.spec_from_file_location("migrate_independent_identity", SOURCE)
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="zmp-migration-synthetic-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.site = self.root / "public_html" / "shop" / "site"
        self.plugin = self.site / "wp-content" / "plugins" / "elementor-pro"
        self.plugin.mkdir(parents=True)
        self.independent = self.plugin.parent / "zilomentor-pro"
        self.backup = self.root / "private" / "backup"
        self.backup.mkdir(parents=True)
        self.backup.chmod(0o700)
        (self.backup / "wordpress-before-identity-synthetic.sql").write_text(
            "-- synthetic fixture; contains NO real site data\n")
        (self.backup / "wordpress-before-identity-synthetic.sql").chmod(0o600)
        (self.site / "wp-config.php").write_text("<?php // synthetic")
        mu = self.site / "wp-content" / "mu-plugins"
        mu.mkdir()
        (mu / "zmp-release-guard.php").write_text(
            "<?php /** Version: 0.2.0 */")
        (mu / "zmp-early-bootstrap.php").write_text(
            "<?php /** Version: 0.1.0 */")
        (self.plugin / "elementor-pro.php").write_text(
            "<?php\n/**\n * Plugin Name: ZiloMentor Pro\n * Version: 0.1.1\n */\n")
        (self.plugin / "plugin.php").write_text("<?php // synthetic\n")
        for i in range(1045):
            (self.plugin / ("synthetic-%04d.txt" % i)).write_text("trusted synthetic")
        self.zip = self.root / "trusted-0.1.1.zip"
        with zipfile.ZipFile(self.zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for file in self.plugin.rglob("*"):
                z.write(file, "elementor-pro/" + str(file.relative_to(self.plugin)))
        self.sha = hashlib.sha256(self.zip.read_bytes()).hexdigest()
        self.active = "elementor-pro"
        def mocked_state(_):
            return {
                "multisite": False,
                "legacy": self.active == "elementor-pro",
                "independent": self.active == "zilomentor-pro",
                "identity": "0.1.1",
                "base": self.active + "/elementor-pro.php",
                "elementor": True,
                "early_bootstrap": self.active == "zilomentor-pro",
                "woocommerce": True,
            }
        def mocked_switch(_, old, new):
            if old != self.active:
                raise RuntimeError("Synthetic state transition mismatch")
            self.active = new
        self.patches = [
            patch.object(identity, "wp_state", side_effect=mocked_state),
            patch.object(identity, "switch_active_plugin", side_effect=mocked_switch),
            patch.object(identity, "WP_CLI", Path("/usr/local/bin/wp")),
            patch.object(identity, "PHP_CLI", Path("/opt/cpanel/ea-php84/root/usr/bin/php")),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def run_migration(self, *flags):
        argv = [
            "migrate_independent_identity.py", "--site", str(self.site),
            "--backup-dir", str(self.backup),
            "--database-backup", str(self.backup / "wordpress-before-identity-synthetic.sql"),
            *flags,
        ]
        stdout = StringIO()
        with patch.object(sys, "argv", argv), redirect_stdout(stdout):
            identity.main()
        return stdout.getvalue()

    def test_read_only_preflight_then_apply_then_rollback(self):
        flags = ("--zip", str(self.zip), "--sha256", self.sha)
        out = self.run_migration(*flags)
        self.assertIn("IDENTITY_PREFLIGHT_OK=", out)
        self.assertIn("DRY_RUN=YES", out)
        self.assertTrue(self.plugin.exists())
        self.assertFalse(self.independent.exists())
        out = self.run_migration(*flags, "--apply")
        self.assertIn("MIGRATION_SUCCEEDED=YES", out)
        self.assertEqual(self.active, "zilomentor-pro")
        self.assertFalse(self.plugin.exists())
        self.assertEqual(identity.plugin_header(self.independent),
                         ("ZiloMentor Pro", "0.1.1"))
        state = json.loads((self.backup / identity.STATE_FILENAME).read_text())
        self.assertEqual(state["status"], "migrated")
        self.assertTrue((self.backup / state["legacy_backup_name"]).is_dir())
        out = self.run_migration("--rollback")
        self.assertIn("IDENTITY_ROLLBACK=YES", out)
        self.assertEqual(self.active, "elementor-pro")
        self.assertTrue(self.plugin.is_dir())
        self.assertFalse(self.independent.exists())
        self.assertEqual(
            json.loads((self.backup / identity.STATE_FILENAME).read_text())["status"],
            "rolled_back",
        )
        # A corrected build must permit a second, explicitly verified
        # attempt after the first migration was safely rolled back.
        second = self.run_migration(*flags)
        self.assertIn("DRY_RUN=YES", second)
        second_apply = self.run_migration(*flags, "--apply")
        self.assertIn("MIGRATION_SUCCEEDED=YES", second_apply)
        self.assertEqual(self.active, "zilomentor-pro")
        self.assertEqual(
            len(list(self.backup.glob("zilomentor-previous-rolled-back-state-*.json"))), 1
        )
        self.run_migration("--rollback")
        self.assertEqual(self.active, "elementor-pro")

    def test_archive_hash_mismatch_and_unexpected_file_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "hash mismatch"):
            self.run_migration("--zip", str(self.zip), "--sha256", "0" * 64, "--apply")
        self.assertTrue(self.plugin.exists())
        self.assertFalse(self.independent.exists())
        (self.plugin / "error_log").write_text("synthetic runtime warning")
        with self.assertRaisesRegex(RuntimeError, "unexpected files"):
            self.run_migration("--zip", str(self.zip), "--sha256", self.sha, "--apply")
        self.assertEqual(self.active, "elementor-pro")
        self.assertFalse(self.independent.exists())

    def test_rollback_without_state_refused(self):
        with self.assertRaisesRegex(RuntimeError, "No recorded identity migration"):
            self.run_migration("--rollback")
        self.assertTrue(self.plugin.is_dir())


if __name__ == "__main__":
    unittest.main(verbosity=2)
