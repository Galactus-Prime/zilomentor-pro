# ZiloMentor Pro

**An independently maintained, GPL-licensed Elementor Pro compatibility fork for WordPress.**

> **Development preview, v0.1.0. Not production-ready.** The compatibility work
> has passed structural checks, but has not passed full WordPress, editor,
> WooCommerce or theme runtime tests.

ZiloMentor Pro is a fork of [PRO Elements](https://github.com/proelements/proelements),
which in turn incorporates GPL-licensed code originally developed by Elementor Ltd.
The aim is to preserve Elementor Pro's widely used widget identifiers, PHP classes,
hooks and template formats so compatible third-party WordPress themes can continue
working without editing the themes. Actual compatibility varies by theme and
plugin version and must be tested.

## What it is and is not

- **Is:** an independent, open-source compatibility-focused plugin derived from
  PRO Elements 4.4.0, retaining relevant Elementor Pro interfaces.
- **Is not:** Elementor Pro, an official Elementor product, an activated Elementor
  subscription, or access to Elementor cloud services, AI, commercial templates,
  proprietary support or remotely licensed features.
- **Requirement:** the free Elementor plugin must also be installed.
- **Do not run alongside Elementor Pro or PRO Elements.** They share PHP identifiers.
- **Safe starting point:** test on an isolated WordPress staging site only.

## Compatibility

| Area | Status |
| --- | --- |
| Original Elementor Pro PHP namespace and hooks | Retained from upstream; static check passes |
| Theme Builder, dynamic tags and product widgets | Source modules present; runtime tests pending |
| Vamtam Fiore integration on ItzyBitzyWorkshop | 20 referenced source-file targets present; end-to-end tests pending |
| WordPress plugin path elementor-pro/elementor-pro.php | Provided when staging ZIP is installed |
| WordPress editing and responsive layouts | Not yet tested |
| WooCommerce cart, checkout and payments | Not yet tested |
| Automated updates | Upstream updater disabled; independent signed updater pending |

The initial source tracks PRO Elements **v4.4.0** at commit
[58d52e0](https://github.com/proelements/proelements/commit/58d52e0f10640088aa179e28b40b161c33c57de4).
The public fork retains its original upstream commit history.

## Build and test (development only)

    python3 tests/static_compatibility.py
    python3 tools/build_zip.py

The ZIP build uses the elementor-pro/ directory and
elementor-pro/elementor-pro.php entrypoint for interoperability. This is an
implementation detail: the plugin's public name is **ZiloMentor Pro**.

For staging, first back up the WordPress database and files; capture baseline
screenshots; deactivate the current Elementor Pro installation; replace it with
the ZiloMentor Pro staging package; test page templates, forms, dynamic tags,
navigation, WooCommerce and the Elementor editor; then compare logs and
screenshots. **Never overwrite an active production plugin or a live store.**

## Development plan

1. Run PHP 8.4/8.5 syntax checks in CI and add full WordPress integration tests.
2. Add disposable WordPress/Elementor matrix tests and Vamtam Fiore fixtures.
3. Investigate compatibility differences and implement only justified fixes.
4. Introduce a verified update pipeline, security policy and changelog.
5. Publish a release only after end-to-end staging and rollback tests pass.

See [ZILOMENTOR-NOTES.md](ZILOMENTOR-NOTES.md) for the current staging checklist,\n[SECURITY.md](SECURITY.md) for security reporting, and\n[CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## Licence, provenance and trademarks

Distributed under **GPLv3 or (at your option) any later version**, consistent
with the included [licence](license.txt). Copyright notices and attribution to
Elementor Ltd., PRO Elements contributors and ZiloMentor Pro contributors are
retained. Modified source must be identified as modified.

The names **Elementor** and **Elementor Pro** are used solely for compatibility
and attribution; they remain trademarks of their respective owner. ZiloMentor
Pro is **not endorsed, affiliated with, or supported by Elementor Ltd.**
