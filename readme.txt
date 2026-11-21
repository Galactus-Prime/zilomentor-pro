=== ZiloMentor Pro ===
Contributors: zilomentor-contributors
Tags: elementor, elementor-pro, compatibility, theme-builder, woocommerce
Requires at least: 7.1
Tested up to: 7.1
Requires PHP: 7.4
Stable tag: 0.1.0
License: GPLv3 or later
License URI: https://www.gnu.org/licenses/gpl-3.0.html

Independent GPL-licensed Elementor Pro compatibility fork based on PRO Elements. Development preview for staging only.

== Description ==

ZiloMentor Pro preserves compatibility interfaces used by WordPress themes and
extensions that depend on Elementor Pro. It is an independent fork of PRO
Elements 4.4.0 and incorporates GPL-licensed work originally by Elementor Ltd.

This is a development preview, not a production-ready WordPress plugin.
Use a disposable staging site for tests. Free Elementor is required; do not
activate ZiloMentor Pro alongside Elementor Pro or PRO Elements.

No Elementor subscription, commercial support, proprietary templates, AI,
cloud services or access to official hosted services is included.

== Installation ==

1. Back up your complete staging environment, including database and uploads.
2. Deactivate any existing Elementor Pro or PRO Elements installation.
3. Install the staging ZIP as the sole Elementor Pro-compatible extension.
4. Verify theme templates, editor, forms, responsive pages and checkout in staging.
5. Revert immediately if anything fails; do not install onto a live shop.

== Frequently Asked Questions ==

= Is this officially supported by Elementor? =
No. ZiloMentor Pro is independently maintained and not affiliated with Elementor Ltd.

= Will it work with every commercial Elementor theme? =
Not guaranteed. Theme-specific testing is required.

= Does it connect to Elementor's subscription and cloud services? =
No. The plugin does not grant access to subscription-only hosted services.

= Can it run alongside Elementor Pro? =
No. They expose overlapping PHP classes and WordPress plugin identities.

== Changelog ==

= 0.1.0 =
* First development preview derived from PRO Elements 4.4.0.
* Preserved Elementor Pro namespace, hooks and standard plugin path.
* Disabled PRO Elements' updater pending independent maintenance.
* Added structural compatibility checks, staging instructions and attribution.

== Upgrade Notice ==

= 0.1.0 =
Development preview only. Do not install on production WordPress sites.
