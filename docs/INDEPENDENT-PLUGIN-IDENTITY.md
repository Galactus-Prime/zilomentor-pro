# Independent plugin identity migration — 20 November 2026

## Why

WP Toolkit associates the legacy `elementor-pro` plugin basename with the
official Elementor Pro security-advisory feed, even when the installed code
is a separately released GPL fork with its own `Update URI`. On the
Itzy Bitzy Workshop beta, WP Toolkit offered and installed an unrelated
vendor-labelled 4.4.1 ZIP while ZiloMentor 0.1.1 was active. That replacement
was quarantined, trusted code restored, forged licence-cache values removed,
and a separate external must-use release guard installed.

A true WordPress basename of `zilomentor-pro/elementor-pro.php` prevents
the false conflation at plugin-inventory level, while retaining the
`ElementorPro\\...` PHP classes, Elementor Pro widget names and
`ELEMENTOR_PRO_VERSION` compatibility API.

## First live trial and automatic rejection

A guarded, checksum-verified trial on 20 November 2026 changed **only** the
0.1.1 plugin's installed folder and WordPress's active plugin entry.
All 1,419 files matched the exact previously trusted 0.1.1 ZIP, a fresh
private SQL snapshot existed, the external guard was upgraded to 0.2.0, and
the original plugin files were kept in an owner-only non-web directory.

WordPress, Elementor and WooCommerce bootstrapped, WP Toolkit detected the
new `zilomentor-pro` identity, live CSS URLs were rewritten to the new folder,
and the new plugin stylesheet returned HTTP 200. The same 85/89 widgets
rendered and no new HTTP/JavaScript errors appeared.

**But browser screenshots caught a desktop-only styling regression.** The
navigation typography, search control and account/favourites header layout
changed. Against the exact 1366x768 original desktop baseline, mean RGB
difference was **12.7127**. The 390x844 mobile screenshot remained pixel
identical. This is a release-blocking visual failure even though the
structural tests passed.

The legacy 0.1.1 identity was immediately restored through the tested
file-only rollback, both site cache layers were cleared and Elementor
CSS regenerated. New screenshots were **pixel-identical (0.0 mean RGB
difference) on BOTH desktop and mobile**. No WooCommerce database rollback
or synthetic order was used during the live migration.

## Root-cause hypothesis and correction under isolated test

WordPress loads root-level must-use plugins before normal active plugins,
then invokes `plugins_loaded` callbacks in registration order within each
priority. The original `elementor-pro` directory is alphabetically before
Vamtam's integration; the new `zilomentor-pro` directory is after it.
Both register a priority-10 `plugins_loaded` callback. That changes whether
ZiloMentor Pro's setup runs before Vamtam's Elementor compatibility hooks,
which can affect generated theme CSS.

The dedicated `tools/zmp-early-bootstrap.php` must-use adapter loads ONLY
when the independently named ZiloMentor is listed as active and its local
plugin header matches the official ZiloMentor GitHub Update URI. It
includes the existing Pro entrypoint **early enough to register its normal
callback before Vamtam**. No duplicate plugin code, vendor installation
folder, licence spoofing, WordPress database rewrite or network request
is involved. It does not modify the live legacy 0.1.1 beta.

`tests/runtime_bootstrap_order.php` verifies that Elementor and Pro
initialize exactly once and the ZiloMentor callback precedes Vamtam's.
The disposable QA runner injects the adapter only for
`--plugin-folder zilomentor-pro`; this mirrors the intended deployment.
The migration utility refuses any live switch without both the MU update
guard and the early bootstrap adapter, validated owner-only backups and
exact known-good release archive hash.

## Final controlled live migration: accepted (20 November 2026)

After adding the verified independent early-bootstrap MU loader and extending
the isolated coverage, the corrected build passed **52/52 combined editor**
and **67/67 complete frontend, popup and WooCommerce** checks. The MU guard
protects both plugin basenames. The independent signed-release and
rollback unit tests passed.

The second guarded live trial showed a **pixel-identical desktop header**,
but the first mobile screenshot comparison failed (mean RGB 12.87666) because
the hero illustration was at a different vertical position. The migration
was immediately rolled back again, without a database restore. Crucially,
the *migrated* screenshot and *subsequent legacy rollback* screenshot were
pixel-identical **on both viewports**. Thus the mobile image offset persisted
after restoring legacy code and was not caused by plugin identity. No
visual difference was ignored, and the comparator continued to fail against
the stale earlier baseline.

A new baseline was captured from the visually correct, legacy 0.1.1 site,
and another read-only preflight verified **all 1,419 source files**, a
recent private **0600** WordPress SQL export, the independent bootstrap and
external release guard. A final, owner-approved migration used the *same
trusted 0.1.1 code* (SHA256
`1d626aadee1bc281717ca326da22884a8a9f1515586f849e438a7bdda1fd4144`)
and changed only the WordPress active plugin basename and installed
directory. Zilo Rocket, ZiloCache and Elementor CSS caches were cleared.

**Final public Chromium visual gate: PASS**
- Desktop **1366x768**: **0.00350** mean RGB difference across full
  screenshot; **0.01922** in the top 133px header (0–255 scale).
- Mobile **390x844**: **0.00000** difference; pixel-identical.
- Elementor widgets unchanged: **85 desktop**, **89 mobile**; the same
  widget types and zero additional JS, HTTP or network errors.
- Public homepage, shop, cart, checkout, and an ordinary product page
  each returned HTTP **200** and contained **zero old
  `/wp-content/plugins/elementor-pro/` references**. The independent
  navigation menu stylesheet returned HTTP **200**.
- WordPress reported **ZiloMentor 0.1.1** active at
  `zilomentor-pro/elementor-pro.php`, Elementor core and WooCommerce
  loaded, MU early bootstrap active, original folder absent. The original
  verified 0.1.1 directory remains in the **private, owner-only**
  rollback store, and no historical WooCommerce data was restored.
- Refreshed cPanel WP Toolkit inventory identified
  **`zilomentor-pro` / ZiloMentor Pro 0.1.1**, with **no official vendor
  Elementor Pro update offer**. Core Elementor remains 4.4.1.
- Read-only guards confirmed vendor and independent plugin updates are
  blocked through WordPress upgrader hooks; WooCommerce updates are allowed.
  WP Toolkit's root-level direct file operations could bypass WP hooks,
  so periodic verification remains prudent.

The production **beta** has a separate WordPress plugin identity.
The **underlying code remains 0.1.1 / PRO Elements 4.4.0** and is
**not guaranteed equivalent to official Elementor Pro 4.4.1**. The offline
Ed25519 signing key and signed 0.1.2 release have NOT been deployed.
Continue security reviews and nonpayment regression tests before promoting
the plugin for general distribution.

## Independent deployment acceptance checklist

- [x] Exact trusted 0.1.1 file match and fresh private WordPress database snapshot
- [x] Owner-only source backup, full abort-on-error safeguards and tested rollback
- [x] External 0.2.0 MU upgrade guard protects both legacy and independent slugs
- [x] First independent-folder editor tests and full storefront/offline checkout passed
- [x] Initial styling regression detected; original live appearance restored exactly
- [x] Early MU adapter implemented with explicit callback-order isolated regression
- [x] Run combined editor (52/52), full frontend and WooCommerce (67/67) regressions with the adapter
- [x] Reattempt only with a fresh private snapshot and an explicit two-viewport pixel comparison; final visual gate passed
- [x] Verify zero old asset URLs, independent WP Toolkit identity, five HTTP 200 public pages and zero new HTTP errors
- [x] Roll back on the original desktop and second trial mobile gate failures; preserve evidence and accept only the later passing visual gate

**Do not declare independent plugin migration production-ready until the
desktop header is visually equivalent.** WordPress/WP Toolkit slug identity
alone is not sufficient proof of compatibility.

Official WordPress MU loading documentation:
https://developer.wordpress.org/advanced-administration/plugins/mu-plugins/
