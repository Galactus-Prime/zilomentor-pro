# Signed GitHub Releases update feed: no CI or paid subscription

**20 November 2026:** Read-only release discovery, Ed25519 verification and
private staging are implemented. No actual release, operational signing key
or WordPress upgrade was created. Live site remains on ZiloMentor 0.1.1.

## Why this approach

The existing public Galactus-Prime/zilomentor-pro repository can host manually
uploaded ZIP/JSON/signature assets. GitHub documents no aggregate release-size
or release bandwidth limit. Manually uploading assets with GitHub's website or
free CLI does **not** require GitHub Actions or a subscription.

References:
- https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
- https://cli.github.com/manual/gh_release_create
- https://cli.github.com/manual/gh_release_upload
- https://docs.github.com/en/rest/releases/assets

Release hosting and billing policies may change in future.

## Security model

The offline Ed25519 private signing key is the **sole publishing authority**.
It must be generated and retained on a trusted offline owner-controlled
machine, never in GitHub, ChatGPT, WordPress, an online server or VPS.
The offline-approved public key is pinned outside WordPress webroot.

The opt-in tools/stage_signed_github_release.py script:

1. Fetches only the public official GitHub latest-release API for the
   exact Galactus-Prime/zilomentor-pro repository over HTTPS.
2. Rejects draft/prereleases, duplicate or ambiguous assets, malformed version
   tags, non-increasing versions, unsafe hosts/URLs and unrecognised redirects.
3. Checks exact independent-plugin release asset names and their byte lengths
   and (when present) GitHub SHA256 digests.
4. Uses the existing PHP Sodium verifier to validate the **literal manifest**
   bytes against the offline-approved PUBLIC key, then enforces exact signed
   basename, version, timestamp, expiry, size and SHA256 ZIP identity.
5. Rejects dangerous, incomplete, duplicated, symlinked and oversized ZIP
   entries; checks the independent plugin bootstrap and version.
6. Stages verified ZIP, JSON manifest and detached signature only after
   validation, in an already-existing owner-only private directory (0700)
   outside webroot, with no overwrites and cleanup on failure.
7. **Never edits, installs, upgrades, deactivates or auto-updates WordPress.**
   A separately audited file-only manual installer and owner approval
   remain mandatory.

GitHub HTTPS, Release metadata and asset digests alone are **not** the trust
anchor. A tampered release with an unsigned/mismatched manifest fails closed.

## Release asset convention

A future approved v0.1.2 Release must contain three assets:

    zilomentor-pro-independent-0.1.2-staging-only.zip
    zilomentor-pro-0.1.2.json
    zilomentor-pro-0.1.2.json.sig

First check the exact audited Git commit, package hash, source security,
theme/editor/browser tests, payment tests and current site backups. Build the
ZIP and JSON using tools/build_zip.py and tools/create_release_manifest.py,
then transfer the verified bytes to the offline owner computer for signing
with tools/release_signature.php. See docs/OFFLINE-RELEASE-SIGNING.md.

After ALL release gates pass, an owner can manually draft a release and
attach those three files without Actions. **Not a command to execute now:**

    gh release create v0.1.2 --repo Galactus-Prime/zilomentor-pro \
      --target APPROVED_MERGED_COMMIT --title "ZiloMentor Pro 0.1.2" \
      --draft --notes-file /private/approved-release-notes.md

    gh release upload v0.1.2 --repo Galactus-Prime/zilomentor-pro \
      /private/release/zilomentor-pro-independent-0.1.2-staging-only.zip \
      /private/release/zilomentor-pro-0.1.2.json \
      /private/release/zilomentor-pro-0.1.2.json.sig

Double-check SHA256, signature, source commit and target plugin identity,
then publish the reviewed release through GitHub's release interface.
No CI workflows, private-key uploading or GitHub update automation.

## Verify and stage on the owner-controlled machine

Create a private stage directory outside public_html and WordPress:

    install -d -m 700 /private/staged-zilomentor-releases

Use only the already-approved PUBLIC verification key:

    python3 tools/stage_signed_github_release.py \
      --current-version 0.1.1 \
      --trusted-public-key /private/approved-keys/zmp-public.b64 \
      --stage-dir /private/staged-zilomentor-releases

The script makes no WordPress changes; success reports the validated version,
exact signed ZIP checksum, filenames and live_installation_changed=false.
If no signed published release exists, it stops safely.

To deploy subsequently, use tools/manual_live_swap.py with the staged ZIP,
expected SHA256, exact signed JSON, detached signature, pinned public key,
fresh backup and **read-only preflight**. Only a second, owner-authorised call
with --apply may change plugin files. Keep the original code for file rollback.

## Tests and outstanding requirements

The manual no-Actions release checks run
tests/test_stage_signed_github_release.py. Its 12 initial no-network tests
use short-lived synthetic keys only in private temporary directories. They
cover valid staging, tampering, signatures, unsafe origin/ports, rollback
prevention, duplicate assets, expiry, invalid trust, world-readable staging
and overwrite protection. These are **not** a real published-feed test.

WordPress supports custom Update URI and update_plugins_{hostname} filters:
https://developer.wordpress.org/reference/hooks/update_plugins_hostname/

We intentionally do not register a direct WordPress auto-update hook,
because it would be possible to install a ZIP without the independent
offline-owner signature gate. The existing independent Update URI header
still protects plugin identity.

Outstanding: legitimate upstream Pro 4.4.1 comparison, independent audit,
real sample files, provider sandbox, signed offline owner release, complete
production visual gate and owner-approved publishing. These remain blockers
in docs/RELEASE-BLOCKERS.md. Do not publish the unsigned 0.1.2 candidate.
