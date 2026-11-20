#!/usr/bin/env python3
"""No-network acceptance tests for the opt-in signed GitHub Release stage tool.

All signing keys are THROWAWAY and exist only under TemporaryDirectory;
never use these ephemeral keys to sign operational/production releases.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import os
import struct
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from create_release_manifest import create_manifest
import stage_signed_github_release as feed


class SignedGitHubReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="zmp-signed-feed-tests-")
        cls.root = Path(cls.tmp.name)
        cls.php = shutil.which("php")
        if not cls.php:
            raise RuntimeError("PHP CLI Sodium is required for signed feed tests")
        cls.secret = cls.root / "private-key.b64"
        cls.public = cls.root / "public-key.b64"
        tool = ROOT / "tools/release_signature.php"
        cls.tool = tool
        cls.call_php("generate", cls.secret, cls.public)

        cls.version = "0.1.2"
        cls.zip_name = f"zilomentor-pro-independent-{cls.version}-staging-only.zip"
        cls.manifest_name = f"zilomentor-pro-{cls.version}.json"
        cls.sig_name = cls.manifest_name + ".sig"
        cls.package = cls.root / cls.zip_name
        with zipfile.ZipFile(cls.package, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("zilomentor-pro/elementor-pro.php",
                       "<?php\n/**\n * Plugin Name: ZiloMentor Pro\n"
                       " * Version: 0.1.2\n */\n")
            for i in range(1000):
                z.writestr(f"zilomentor-pro/tests-generated/assets/demo-{i:04}.txt",
                           "synthetic-only file, no live WordPress or card data\n")
        cls.zip_blob = cls.package.read_bytes()

        cls.manifest_blob = (json.dumps(
            create_manifest(cls.package, valid_days=30),
            sort_keys=True, separators=(",", ":")
        ) + "\n").encode()
        cls.sig_blob = cls.sign(cls.manifest_blob)

    @classmethod
    def call_php(cls, operation, *args):
        result = subprocess.run(
            [cls.php, str(cls.tool), operation, *(str(v) for v in args)],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode:
            raise AssertionError("Synthetic signature helper failed: " + result.stderr)
        return result

    @classmethod
    def sign(cls, manifest_blob):
        manifest = cls.root / ("temp-manifest-" + os.urandom(6).hex() + ".json")
        signature = cls.root / ("temp-signature-" + os.urandom(6).hex() + ".sig")
        manifest.write_bytes(manifest_blob)
        try:
            cls.call_php("sign", manifest, cls.secret, signature)
            return signature.read_bytes()
        finally:
            manifest.unlink(missing_ok=True)
            signature.unlink(missing_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.stage = self.root / ("stage-" + os.urandom(5).hex())
        self.stage.mkdir(mode=0o700)
        self.release, self.uris = self.make_release(self.manifest_blob, self.sig_blob,
                                                     self.zip_blob)

    def tearDown(self):
        shutil.rmtree(self.stage, ignore_errors=True)

    @classmethod
    def make_release(cls, manifest_blob, sig_blob, zip_blob):
        assets = []
        urls = {}
        for filename, data in (
            (cls.manifest_name, manifest_blob),
            (cls.sig_name, sig_blob),
            (cls.zip_name, zip_blob),
        ):
            uri = (f"https://github.com/Galactus-Prime/zilomentor-pro/"
                   f"releases/download/v{cls.version}/{filename}")
            assets.append({
                "name": filename, "browser_download_url": uri,
                "size": len(data), "state": "uploaded",
                "digest": "sha256:" + hashlib.sha256(data).hexdigest(),
            })
            urls[uri] = data
        release = {
            "tag_name": "v" + cls.version,
            "draft": False, "prerelease": False,
            "assets": assets,
        }
        return release, urls

    def fetcher(self, release=None, assets=None):
        release = self.release if release is None else release
        assets = self.uris if assets is None else assets

        def fake_fetch(uri, maximum):
            if uri == feed.API_URL:
                result = json.dumps(release).encode()
            else:
                result = assets[uri]
            if len(result) > maximum:
                raise feed.ReleaseError("Exceeded size cap in synthetic downloader")
            return result
        return fake_fetch

    def stage_valid(self, release=None, assets=None, current="0.1.1"):
        return feed.stage_release(
            current_version=current, public_key=self.public,
            public_key_sha256=hashlib.sha256(self.public.read_bytes()).hexdigest(),
            stage_dir=self.stage,
            fetch=self.fetcher(release, assets), php=self.php,
        )

    def test_valid_signed_release_is_staged_without_installing(self):
        status = self.stage_valid()
        self.assertEqual(status["version"], "0.1.2")
        self.assertEqual(status["plugin"], "zilomentor-pro/elementor-pro.php")
        self.assertFalse(status["live_installation_changed"])
        self.assertFalse(status["automatic_update_enabled"])
        self.assertEqual(len(status["files"]), 3)
        self.assertEqual(
            hashlib.sha256((self.stage / self.zip_name).read_bytes()).hexdigest(),
            status["zip_sha256"],
        )
        self.assertFalse((self.stage / "elementor-pro").exists())

    def test_modified_signature_is_rejected_without_staging_files(self):
        release = deepcopy(self.release)
        uris = dict(self.uris)
        uri = release["assets"][1]["browser_download_url"]
        uris[uri] = b"?" + self.sig_blob[1:]
        release["assets"][1]["digest"] = ("sha256:" +
                                             hashlib.sha256(uris[uri]).hexdigest())
        with self.assertRaises(feed.ReleaseError):
            self.stage_valid(release, uris)
        self.assertFalse(list(self.stage.iterdir()))

    def test_modified_zip_is_rejected_after_signature_verification(self):
        release = deepcopy(self.release)
        uris = dict(self.uris)
        uri = release["assets"][2]["browser_download_url"]
        uris[uri] = self.zip_blob[:-1] + (
            b"X" if self.zip_blob[-1:] != b"X" else b"Z"
        )
        release["assets"][2]["digest"] = ("sha256:" +
                                             hashlib.sha256(uris[uri]).hexdigest())
        with self.assertRaises(feed.ReleaseError):
            self.stage_valid(release, uris)
        self.assertFalse(list(self.stage.iterdir()))

    def test_untrusted_asset_hosts_are_rejected(self):
        release = deepcopy(self.release)
        release["assets"][2]["browser_download_url"] = (
            "https://malicious.invalid/other-plugin.zip"
        )
        with self.assertRaises(feed.ReleaseError):
            self.stage_valid(release)
        self.assertFalse(list(self.stage.iterdir()))

    def test_duplicate_release_asset_is_rejected(self):
        release = deepcopy(self.release)
        release["assets"].append(deepcopy(release["assets"][0]))
        with self.assertRaises(feed.ReleaseError):
            self.stage_valid(release)

    def test_no_downgrade_or_same_version(self):
        for current in ("0.1.2", "0.1.3"):
            with self.subTest(current=current), self.assertRaises(feed.ReleaseError):
                self.stage_valid(current=current)

    def test_draft_and_prerelease_are_rejected(self):
        for flag in ("draft", "prerelease"):
            release = deepcopy(self.release)
            release[flag] = True
            with self.subTest(flag=flag), self.assertRaises(feed.ReleaseError):
                self.stage_valid(release)

    def test_expired_even_if_correctly_signed(self):
        manifest = create_manifest(
            self.package, valid_days=10,
            now=datetime.now(timezone.utc) - timedelta(days=30)
        )
        blob = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
        signed = self.sign(blob)
        release, assets = self.make_release(blob, signed, self.zip_blob)
        with self.assertRaises(feed.ReleaseError):
            self.stage_valid(release, assets)

    def test_world_readable_stage_directory_rejected(self):
        self.stage.chmod(0o755)
        with self.assertRaises(feed.ReleaseError):
            self.stage_valid()
        self.assertFalse(list(self.stage.iterdir()))

    def test_existing_release_file_cannot_be_overwritten(self):
        (self.stage / self.zip_name).write_text("keep existing file")
        with self.assertRaises(feed.ReleaseError):
            self.stage_valid()
        self.assertEqual((self.stage / self.zip_name).read_text(),
                         "keep existing file")

    def test_zip_bomb_metadata_rejected_before_decompression(self):
        # Central-directory uncompressed size is attacker-controlled.
        # Artificially claim a 600 MiB file inside a ~50 KiB ZIP, without
        # ever generating or decompressing a 600 MiB payload.
        data = bytearray(self.zip_blob)
        first = data.find(b"PK\x01\x02")
        second = data.find(b"PK\x01\x02", first + 4)
        self.assertGreater(second, first)
        struct.pack_into("<I", data, second + 24, 600 * 1024 * 1024)
        with self.assertRaisesRegex(feed.ReleaseError, "Decompressed plugin"):
            feed.inspect_zip(bytes(data), self.version)

    def test_url_scheme_host_userinfo_and_port_are_rejected(self):
        for uri in (
            "http://api.github.com/repos/Galactus-Prime/zilomentor-pro/releases/latest",
            "https://127.0.0.1/secret", "https://evil.invalid/",
            "https://user:token@api.github.com/foo",
            "https://api.github.com:8443/foo", "https://api.github.com:invalid/foo",
            "https://api.github.com/foo#fragment",
        ):
            with self.subTest(uri=uri), self.assertRaises(feed.ReleaseError):
                feed.safe_url(uri)

    def test_pinned_public_key_fingerprint_mismatch_rejected_before_fetch(self):
        fetched = []
        def forbid_fetch(url, maximum):
            fetched.append(url)
            raise AssertionError("No remote download should occur before key verification")
        with self.assertRaisesRegex(feed.ReleaseError, "fingerprint"):
            feed.stage_release(
                current_version="0.1.1", public_key=self.public,
                public_key_sha256="0" * 64, stage_dir=self.stage,
                fetch=forbid_fetch, php=self.php,
            )
        self.assertEqual(fetched, [])
        self.assertFalse(list(self.stage.iterdir()))

    def test_invalid_public_key_cannot_authorize_release(self):
        fake_public = self.root / "broken-pub.b64"
        fake_public.write_text("This is not a valid Ed25519 public key")
        with self.assertRaises(feed.ReleaseError):
            feed.stage_release(
                current_version="0.1.1",
                public_key=fake_public,
                public_key_sha256=hashlib.sha256(fake_public.read_bytes()).hexdigest(),
                stage_dir=self.stage,
                fetch=self.fetcher(), php=self.php,
            )
        fake_public.unlink()
        self.assertFalse(list(self.stage.iterdir()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
