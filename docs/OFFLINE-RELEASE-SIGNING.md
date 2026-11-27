# Offline signing and manual release custody (no GitHub Actions)

**Status:** documented procedure, **not** an operational signing key or live
update feed. Applicable only after an independent security, compatibility and
visual release gate has approved the candidate.

ZiloMentor is not Elementor Pro. The live independent beta is 0.1.1; neither
the unreleased 0.1.2 source ZIP nor a vendor Elementor Pro package should be
installed by clicking WP Toolkit's unrelated vendor update links.

## Threat model and separation of duties

A release consists of four distinct items: (1) public GPL source ZIP,
(2) JSON manifest with the **exact independent plugin basename**,
(3) detached Ed25519 signature over the literal manifest bytes, and
(4) an owner-approved public verification key. A private signing key **must
not** live in GitHub, a VPS, cPanel, WordPress, an online CI variable,
the update service, or inside the release ZIP.

The trusted offline machine does the signing. The public site can store
release ZIP, manifest and signature. The WordPress filesystem owner can
perform a guarded **manual** update after independently verifying a trusted
public key. This uses no commercial subscriptions or GitHub Actions.

## One-time setup on an OFFLINE, personally controlled computer

Install PHP CLI with Sodium, Python 3 and a backup device under the owner's
control. Generate a unique Ed25519 keypair using the audited helper shipped
with ZiloMentor's development repository:

```sh
mkdir -p "$HOME/.local/share/zilomentor-release-keys"
chmod 700 "$HOME/.local/share/zilomentor-release-keys"
php tools/release_signature.php generate \
  "$HOME/.local/share/zilomentor-release-keys/zmp-secret.b64" \
  "$HOME/.local/share/zilomentor-release-keys/zmp-public.b64"
```

The script creates files exclusively (no overwrites) at owner-only mode
0600, refuses to operate inside a Git worktree or public_html directory and
avoids printing private key material. Keep an **encrypted, physically separate**
recovery copy. Do not send the secret key through email/chat.

Record the verification public key's SHA256 fingerprint on a second
trusted channel. Copy **only the public key** into the existing private
WordPress deployment/backup folder as an owner-owned, non-group-writable
file. Verify the exact fingerprint before approving it. The release
signer script and manual deployer require PHP Sodium.

## For each fully tested, independently approved candidate

On the trusted build host, after verifying the exact Git SHA and all
PHP/editor/storefront/visual tests, run:

```sh
python3 tools/build_zip.py --folder zilomentor-pro
sha256sum dist/zilomentor-pro-independent-0.1.2-staging-only.zip
python3 tools/create_release_manifest.py \
  --zip dist/zilomentor-pro-independent-0.1.2-staging-only.zip \
  --out /private/release/0.1.2.json --valid-days 30
```

Copy the ZIP and manifest to the OFFLINE signing computer over an
owner-reviewed removable drive, compare the expected digest and signed
plugin path, then sign the **unmodified bytes**:

```sh
php tools/release_signature.php sign \
  /private/release/0.1.2.json \
  "$HOME/.local/share/zilomentor-release-keys/zmp-secret.b64" \
  /private/release/0.1.2.json.sig

php tools/release_signature.php verify \
  /private/release/0.1.2.json \
  "$HOME/.local/share/zilomentor-release-keys/zmp-public.b64" \
  /private/release/0.1.2.json.sig
```

A revision to any signed bytes, including a newline or URL change, requires
a fresh manifest and signature. Neither a checksum alone nor a digital
signature alone proves that the application code is secure: every
candidate still needs review and testing.

## Guarded manual installation on the WordPress host

Copy the public ZIP, manifest, detached signature and the previously pinned
public verification key into private owner-controlled locations outside
public_html. Take and check a **fresh owner-only WordPress database snapshot**
and retain the currently working plugin files privately. Do not blindly
restore an old WooCommerce SQL database if orders have been placed.

Run a read-only preflight **as the cPanel account owner, never root**:

```sh
python3 tools/manual_live_swap.py \
  --folder zilomentor-pro \
  --site /path/to/wordpress \
  --backup-dir /private/deployment-backups \
  --zip /private/releases/zilomentor-pro-independent-0.1.2-staging-only.zip \
  --sha256 INDEPENDENTLY_VERIFIED_64_HEX_DIGEST \
  --signed-manifest /private/releases/0.1.2.json \
  --signature /private/releases/0.1.2.json.sig \
  --trusted-public-key /private/deployment-backups/zmp-public.b64
```

Only after a human review of its output and the current site's backups,
repeat with `--apply`. The independent updater requires a valid,
nonexpired Ed25519 signature; refuses nonincreasing versions and
unsafe release archives; preserves the previously installed plugin
directory for a **file-only** `--rollback`. Never use
`--rollback-to-official` for the independent folder.

After switching, clear the **site-scoped** page/object caches and
Elementor-generated CSS, run public Desktop/Mobile screenshot comparison,
check product/cart/checkout read-only routes, and revert on any substantive
regression. Do not send payments or transactional emails during QA.

## Revocation and recovery

If a private signing key may be compromised, stop deploying immediately.
Do not replace the trusted public key automatically from a remote feed.
Investigate existing signed releases, prepare a new keypair on an offline
machine and require owner-approved out-of-band public-key rotation. Retain
the last trusted plugin release and file-only rollback path.

WordPress plugin update hooks cannot guarantee protection from a separate
hosting panel writing files directly; keep the plugin's own directory and
WP Toolkit vendor-slug collision protections monitored.

## Not yet built

A hardened self-hosted online update feed, trust-key rotation UI, test
payment gateway coverage, and complete official Elementor Pro 4.4.1 patch
equivalence are **not implemented or certified**. No release is
automatically installed. This is intentional until the safety gates pass.
