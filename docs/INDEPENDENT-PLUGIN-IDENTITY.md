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

## Independent deployment acceptance checklist

- [x] Exact trusted 0.1.1 file match and fresh private WordPress database snapshot
- [x] Owner-only source backup, full abort-on-error safeguards and tested rollback
- [x] External 0.2.0 MU upgrade guard protects both legacy and independent slugs
- [x] First independent-folder editor tests and full storefront/offline checkout passed
- [x] Initial styling regression detected; original live appearance restored exactly
- [x] Early MU adapter implemented with explicit callback-order isolated regression
- [ ] Run combined editor, full frontend and WooCommerce regressions with the adapter
- [ ] Reattempt only with fresh snapshot and explicit after-migration desktop/mobile pixel comparison
- [ ] Verify no old asset URLs, current WP Toolkit inventory and zero new HTTP errors
- [ ] If visual equivalence fails, roll back immediately and retain incident evidence

**Do not declare independent plugin migration production-ready until the
desktop header is visually equivalent.** WordPress/WP Toolkit slug identity
alone is not sufficient proof of compatibility.

Official WordPress MU loading documentation:
https://developer.wordpress.org/advanced-administration/plugins/mu-plugins/
