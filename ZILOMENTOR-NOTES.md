# ZiloMentor Pro (pre-release 0.1.0)

Independent GPLv3-or-later derivative of PRO Elements v4.4.0.
Upstream: https://github.com/proelements/proelements
Upstream pinned commit: 58d52e0f10640088aa179e28b40b161c33c57de4

## Goal
Preserve Elementor Pro's PHP classes, widgets, template data, hook identifiers
and standard WordPress plugin basename elementor-pro/elementor-pro.php for
third-party WordPress themes, without modifying those themes.

## Critical limitations
- Prototype only. Static checks are not full WordPress/theme runtime tests.
- Free Elementor must be installed and compatible.
- Only one of Elementor Pro, PRO Elements and ZiloMentor Pro may be active. Never
  install ZiloMentor Pro over a live shop without full backup and rollback plan.
- Does not confer an Elementor subscription, cloud templates, AI, support or
  remotely licensed services. No licence-server impersonation is included.
- The upstream PRO Elements self-updater is disabled to avoid overwriting
  this independently maintained fork. WordPress Update URI is reserved;
  implement a verified release updater before production deployment.
- Keep source copyright and GPL notices, including those in license.txt.
- GitHub: https://github.com/Galactus-Prime/zilomentor-pro (fork exists; local
  ZiloMentor changes require publication to a review branch).

## Verified checks (17 November 2026)

- Upstream source pinned at commit 58d52e0f10640088aa179e28b40b161c33c57de4.
- All 14 static source and Fiore compatibility checks passed.
- Full PHP syntax lint passed on **928/928 files under PHP 8.4**.
- Full PHP syntax lint passed on **928/928 files under PHP 8.5**.
- The first disposable WordPress installation attempt failed at DB connection;
  this was a test harness failure, not a verified plugin defect. Plugin
  activation, Fiore runtime and checkout testing are **still pending**.
- The disposable test containers were cleaned up. The production WooCommerce
  installation, database and Elementor Pro plugin were not modified.
- GitHub repository exists but connector branch creation returns a 403;
  pending additional GitHub write authorisation.

## Suggested validation sequence
1. Install a disposable WordPress 7.1+, Elementor 4.4.x staging environment.
2. Record baseline pages/templates and widgets under genuine Elementor Pro.
3. Back up DB, wp-content and WooCommerce configuration; anonymize customer data.
4. Swap to ZiloMentor Pro only on staging and verify activation, headers, navigation,
   archive/post templates, ACF dynamic tags, popups, forms and WooCommerce views.
5. Check dashboard editor, desktop/mobile responsive views, PHP error logs,
   AJAX, REST API and checkout including payment sandbox.
6. Revert the staging copy after comparison if any functional difference appears.
7. Do not deploy to production until the end-to-end suite passes.
