#!/usr/bin/env python3
"""Offline metadata invariants for the signed ZiloMentor release manifest."""
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

SOURCE = Path(__file__).resolve().parents[1] / "tools" / "create_release_manifest.py"
spec = importlib.util.spec_from_file_location("create_release_manifest", SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ManifestTests(unittest.TestCase):
    def test_exact_zip_identity_hash_and_expiry(self):
        with tempfile.TemporaryDirectory(prefix="zmp-manifest-test-") as tmp:
            p = Path(tmp) / "zilomentor-pro-compat-0.1.2-staging-only.zip"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("elementor-pro/elementor-pro.php",
                           "<?php\n/**\n * Plugin Name: ZiloMentor Pro\n"
                           " * Version: 0.1.2\n */\n")
            instant = datetime(2026, 11, 19, 14, 0, tzinfo=timezone.utc)
            info = mod.create_manifest(p, valid_days=30, now=instant)
            self.assertEqual(set(info), {
                "schema", "plugin", "version", "filename", "sha256",
                "size_bytes", "issued_at", "expires_at",
            })
            self.assertEqual(info["version"], "0.1.2")
            self.assertEqual(info["plugin"], "elementor-pro/elementor-pro.php")
            self.assertEqual(info["issued_at"], "2026-11-19T14:00:00Z")
            self.assertEqual(info["expires_at"], "2026-12-19T14:00:00Z")
            self.assertEqual(len(info["sha256"]), 64)
            self.assertEqual(info["size_bytes"], p.stat().st_size)
            with self.assertRaisesRegex(ValueError, "lifetime"):
                mod.create_manifest(p, valid_days=181, now=instant)
            other = Path(tmp) / "bad-name.zip"
            p.rename(other)
            with self.assertRaisesRegex(ValueError, "filename/version mismatch"):
                mod.create_manifest(other, now=instant)


if __name__ == "__main__":
    unittest.main(verbosity=2)
