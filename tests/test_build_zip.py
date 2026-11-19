#!/usr/bin/env python3
"""Prove release ZIP never contains untracked runtime artifacts or secrets."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

BUILDER = Path(__file__).resolve().parents[1] / "tools" / "build_zip.py"


class TrackedArchiveTests(unittest.TestCase):
    def test_only_tracked_public_release_files_are_distributed(self):
        with tempfile.TemporaryDirectory(prefix="zmp-release-audit-") as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            (root / "assets").mkdir()
            shutil.copy2(BUILDER, root / "tools" / "build_zip.py")
            (root / "elementor-pro.php").write_text(
                "<?php\n/**\n * Plugin Name: ZiloMentor Pro\n * Version: 0.1.1\n */\n"
            )
            (root / "license.txt").write_text("Synthetic GPL fixture")
            for n in range(1001):
                (root / "assets" / ("asset-%04d.txt" % n)).write_text("safe")
            # A mistakenly tracked security-sensitive file must ALSO be
            # denied, not just the untracked one.
            (root / "debug.log").write_text("synthetic-log")
            (root / ".env").write_text("SYNTHETIC_ONLY=example")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            # Simulate ephemeral cPanel and local files generated after Git add.
            (root / "error_log").write_text("synthetic-WP-warning")
            (root / "wp-config.php").write_text("<?php // synthetic")
            (root / "id_ed25519").write_text("SYNTHETIC_KEY_NOT_A_REAL_KEY")
            (root / "assets" / "untracked.txt").write_text("never package")
            output = subprocess.run(
                [sys.executable, str(root / "tools" / "build_zip.py")],
                cwd=root, capture_output=True, text=True, check=True,
            )
            self.assertIn("SIZE_BYTES", output.stdout)
            zips = list((root / "dist").glob("*.zip"))
            self.assertEqual(len(zips), 1)
            with zipfile.ZipFile(zips[0]) as archive:
                names = set(archive.namelist())
                self.assertIn("elementor-pro/license.txt", names)
                self.assertIn("elementor-pro/assets/asset-0000.txt", names)
                for forbidden in (
                    "error_log", "debug.log", ".env", "wp-config.php",
                    "id_ed25519", "assets/untracked.txt",
                    "tools/build_zip.py",
                ):
                    self.assertNotIn("elementor-pro/" + forbidden, names, forbidden)
                self.assertIsNone(archive.testzip())


if __name__ == "__main__":
    unittest.main(verbosity=2)
