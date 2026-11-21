# WP Toolkit update collision — 19 November 2026

## Verified failure mode

ZiloMentor Pro currently has to preserve the standard compatibility directory
`elementor-pro/elementor-pro.php` for existing Elementor theme and widget
integration. Its plugin header has a separate ZiloMentor name/version and a
distinct GitHub `Update URI`, which WordPress core understands.

However, the **cPanel WP Toolkit** plugin catalogue can still identify it by
the **elementor-pro slug**. On the beta test site on 19 November 2026, the
WP Toolkit action log recorded a request to update `ZiloMentor Pro 0.1.1`
to `Elementor Pro 4.4.1`; the operation replaced the fork in place.

The replacement files included a third-party, modified Elementor Pro entry
that forged licence responses and referred template downloads to an unrelated
insecure HTTP server. This is **not a trusted Elementor or ZiloMentor release**.
It was removed, isolated privately for forensic review, and the known-good
0.1.1 files were restored after verifying all 1,419 packaged source files
against the exact original release commit. No live WooCommerce database
rollback was needed. Two forged licence-cache options were cleared after
a protected forensic database backup.

The Toolkit's custom plugin catalogue also contained separate assets with
the `elementor-pro` slug and the vendor-version numbering. This can produce
misleading **vendor update links** even though ZiloMentor's native WordPress
update transient has no such offer.

## Do not confuse the warnings

The Toolkit **Vulnerable** badge is an external version/slug-based signal.
It cannot be considered a precise audit of an independently patched fork.
Equally, it must **not** be hidden or dismissed as entirely false: ZiloMentor
is derived from upstream 4.4.0, and full official Pro 4.4.1 security-fix
parity remains unverified.

Do **not** click a vendor update action for the `elementor-pro` compatibility
directory. Do not rename plugin metadata to 4.4.1 to remove a warning,
spoof a paid subscription or suppress security reports.

## Added mitigation

The separate `tools/zmp-release-guard.php` can be installed as a
**must-use plugin** at `wp-content/mu-plugins/zmp-release-guard.php`.
While the actual installed header identifies an authentic ZiloMentor fork,
it refuses WordPress upgrader downloads, preinstalls or extracted packages
that target the `elementor-pro` compatibility directory; it also refuses
automatic updates for that specific plugin. Other plugins and normal
WordPress security scanners are not affected. An explicit, tested manual
SHA256/Ed25519 signed filesystem release path remains available.

This is **defence in depth**, not a filesystem-level root lock. A WP Toolkit
operation that directly renames or replaces files without invoking WordPress
upgrader hooks can bypass an MU guard. Therefore the operator must also
review WP Toolkit site's plugin update policy and its **shared uploaded
plugin catalogue**, including third-party archives named Elementor Pro.
Removing an uploaded asset from the **global catalogue** may affect other
WordPress installations and requires separate review/approval.

## Remaining architecture gate

Before general release, consider a wholly independent plugin installation
directory (e.g. `zilomentor-pro/`) with a deliberate compatibility adapter.
It must first pass theme/WooCommerce integration and rollback QA; changing
the folder name without testing can break third-party theme detection.
