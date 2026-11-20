# Quarantined unauthorised Elementor Pro package — 19–20 November 2026

## What was found

During the WP Toolkit plugin-name collision on Itzy Bitzy Workshop,
a package describing itself as **Elementor Pro 4.4.1** overwrote the
old `elementor-pro/` plugin folder. It was removed from the live web
directory and placed in the owner-only private backup location
an owner-controlled, **non-web** backup directory, under a
restricted quarantine folder (directory permissions **0700**).
The exact private server path is intentionally not published. This was **not** ZiloMentor code.

On **20 November 2026**, read-only examination of the quarantined
`elementor-pro.php` entrypoint confirmed:

- The header claims **Elementor Pro 4.4.1 / Elementor.com**.
- Before the normal WordPress guard, the script includes **unofficial
  licence key and cached-valid-licence injection** (including a forged
  expiry in 2030) and deliberately overrides licence API responses.
- It attempts to intercept cloud template fetching and request a remote
  **plain-HTTP** third-party endpoint (`wn.norefer.fyi`), while
  explicitly setting `sslverify=false`.
- Its `readme.txt` advertises a separate, unauthorised redistribution
  website (`babia.to`), inconsistent with a trustworthy vendor release.
- SHA256 of the quarantined **entrypoint only**:
  `3f6236f6cb695a4464c93692b66b2255a6b5a9760377e74b68b886ed657b87ac`.

Therefore, the quarantine package is **tampered and untrusted**. Do
**not** install, run, merge, ship or rely on its files as authoritative
official Elementor Pro 4.4.1 source. No network requests were made to
its third-party endpoints during this source inspection. This is
a supply-chain integrity warning, not proof that the PHP executed an
outbound call or that customer data was accessed.

## Remediation and verification

- The live beta was restored to trusted **ZiloMentor 0.1.1** under the
  **independent** WordPress plugin basename
  `zilomentor-pro/elementor-pro.php`. Its files were compared
  byte-for-byte with the known SHA256-pinned 0.1.1 ZIP (1,419/1,419
  verified, no unexpected files).
- A separate external **MU update guard** protects both old and new
  basenames; a Fiore early-bootstrap MU plugin preserves rendering
  order. The original official-vendor folder is absent.
- On 20 November, a read-only source scan found **zero references**
  to `wn.norefer.fyi` or `babia.to` in the current ZiloMentor
  plugin or installed MU plugins.
- Read-only WordPress checks found the suspect licence key option
  empty, no cached 2030/valid licence payload, and **zero matches** for
  the above suspicious host strings or expiry marker in WordPress
  options or post content. No matching WordPress cron event payloads.
- The current WordPress update transient showed only a normal
  `elementor/elementor.php` free-core update record, from
  `downloads.wordpress.org`, and no entry for the removed
  `elementor-pro/` vendor basename.
- The live homepage and admin WP-CLI continued to respond normally.
  The site remains on 0.1.1 and no untrusted package is accessible
  through the WordPress plugins directory.

These checks are reassuring about **current live state** but do
**not prove that the suspicious code never ran or contacted a remote
service** during the interval before quarantine. System logs and any
updater-origin artefacts should be preserved for forensic review;
do not erase the quarantined evidence while the provenance is unknown.
Review outbound proxy/HTTP logs if recorded. Consider credential
rotation if independent evidence indicates an unauthorised process
executed with privileged access.

## Remaining source-provenance question

The current read-only inspection has **not established where WP Toolkit
obtained this tampered ZIP**. Do not attribute it to the actual Elementor
vendor, WordPress.org or WP Toolkit itself without evidence. Its
`readme.txt` indicates unofficial distribution, but that alone
cannot identify the original download URL or actor.

The real Elementor Pro 4.4.1 source comparison remains a separate
release blocker, to be completed only from a **legitimate, verified
distribution**. See `docs/RELEASE-BLOCKERS.md`.
