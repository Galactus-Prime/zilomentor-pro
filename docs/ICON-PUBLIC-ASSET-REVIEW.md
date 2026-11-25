# Custom icon archive: same-origin HTML and malformed data review

**Updated 23 November 2026.** ZiloMentor Pro 0.1.2 development only.
Production Itzy Bitzy Workshop still runs independent ZiloMentor 0.1.1.

## Problem: imported demo HTML becomes a public document

Inherited Fontastic, Fontello and IcoMoon ZIP exports can include
`icons-reference.html`, `demo.html` and auxiliary demo-directory
pages. Although the importer restricts ZIP entry types and extraction
metadata, `Icon_Set_Base::move_files()` had copied the entire
extracted tree, including those demonstration HTML pages, into
`wp-content/uploads/elementor/custom-icons/<name>`. These pages are
not needed at runtime and may contain executable script. Opening an
untrusted HTML file under a WordPress site origin can create an XSS
risk. Restricting upload permission to `manage_options` helps but
does not justify publishing untrusted scripts.

## 0.1.2 source changes

- Imported icon-pack **root and one-level nested `.html`/`.htm`
  demonstration files are no longer moved to the public uploads
  directory**. Fontastic may still use its HTML reference while
  parsing in the temporary extraction directory; the source pack is
  deleted after handling. CSS/WOFF and expected icon/JSON assets
  continue to be copied.
- The importer validates a nonempty, bounded list of icon names,
  required prefix and nonempty pack name before publishing files.
  The inherited `count(false)` fatal on invalid icon-list CSS or
  corrupted JSON is rejected cleanly instead. It never publishes
  the pack merely because all required filenames exist.
- Fontastic's icon prefix and pack-name caches have moved from
  PHP method-level `static` values to instance properties so
  processing two distinct packs in a single request cannot reuse
  stale metadata from the first pack.
- `tests/runtime_icon_public_html_safety.php` creates a genuine,
  synthetic Fontastic-style pack with both a root HTML demo and a
  nested HTML page, CSS, and a font file; it verifies the icon config,
  proper asset copying, omission of both HTML pages and graceful
  malformed-pack rejection. It runs only in disposable WordPress and
  deletes its own disposable files.
- `tests/static_compatibility.py` now guards the source invariants.

## 23 November 2026: strict CSS and legacy SVG font pre-publication checks

The inherited importer also published CSS and legacy SVG font files
under the live site's origin. Browser-accessible SVG can execute active
content when loaded directly, and CSS can import remote resources.
Elementor's normal image-SVG sanitizer does not preserve legacy
`<font>`/`<glyph>` elements. We added a **separate, fail-closed
validator** to built-in Fontastic/Fontello/IcoMoon handling.

- **Before moving any files**, `Icon_Set_Base::validate_public_icon_assets()`
  scans a bounded set of CSS/SVG files (maximum 4,096 entries; each
  CSS/SVG no more than 2 MiB) in the extracted temporary pack.
  File and directory symlinks are rejected.
- CSS is checked after stripping comments and normalizing ASCII CSS
  escapes. `@import`, `@namespace`, image-set, dangerous binding
  syntaxes, data/JavaScript URI schemes and network URL functions are
  rejected. Every `url(...)` must resolve to an existing regular
  local font file within the extracted pack, with a whitelisted
  WOFF/WOFF2/TTF/OTF/EOT/SVG extension. Nonstandard CSS and remote
  assets are rejected rather than silently published.
- SVG webfont XML must have the standard SVG namespace, contain a
  `<font>` element and use only a bounded inert legacy font vocabulary:
  `svg`, `defs`, `font`, `font-face`, `glyph`, `missing-glyph`,
  metadata and kerning. Allowed attributes are explicitly listed.
  Script, foreignObject, active styles, event handlers, URL attributes,
  DOCTYPE/entities and `xml-stylesheet` processing instructions
  are rejected. `DOMDocument` parsing uses `LIBXML_NONET` and
  restores prior libxml error settings.
- Third-party icon import handlers that are **not** instances of the
  built-in `Icon_Set_Base` are not assumed to implement this new
  method, avoiding an extension compatibility fatal. Those
  custom handler implementations require their own independent review.
- Fontastic CSS parsing now captures quoted font family and class prefix
  without greedy regular expressions and escapes the parsed class prefix
  before matching glyph selectors.
- `tests/runtime_icon_active_assets_security.php` exercises valid
  CSS and inert SVG webfonts, multiple remote/traversal/obfuscated
  CSS cases, active SVG elements and attributes, XML stylesheet PI,
  and the actual import-manager pre-publication rejection path.
  `tests/runtime_icon_pack_formats.php` constructs separate
  structurally representative Fontello and IcoMoon packs and checks
  retained CSS/WOFF and extracted glyph configuration.

The first security-focused suite passed at source
`5d16235e40b51b17d744f53fe82f3b6fa6f89f63`
(23 November). The separate synthetic Fontello and IcoMoon integration
passed at source `e25254ff8f4d30a143228565032df512404141a7`.
The completed **full** manual integration suite, including the
actual importer rejection assertion and both format checks,
passed **102/102** at exact tested source SHA
`8590da23aa7b48622cd0b46aad5bf63829c85e74`
(exit 0, 23 November). The 1,435-file unsigned staging-only ZIP
SHA256 was
`3c66237b3f83fb8484c734260f7bae6df144c5fa4f8a55fcf26092a78f72a708`.
Both PHP 8.4/8.5 lints, browser Popup, genuine Form upload,
Apache/Nginx and synthetic WooCommerce checks passed.
Nothing was merged, signed or deployed.

## Remaining limitations

**This is a targeted defence, not independent proof of SVG/CSS safety.**
Untrusted CSS is complex, so unusual encodings, file serving headers
and content-sensitive browsers require professional assessment.
The conservative validation can also reject real third-party icon ZIPs
that contain unrelated SVG sprites, data URLs, remote asset references,
complex CSS, or unusual SVG font extensions. Neither of the new format
fixtures is a vendor-exported archive. Obtain actual approved Fontello,
IcoMoon and Fontastic exports and verify visual glyph rendering and
pack upgrade behaviour before marking this gate complete.

A trusted Elementor Pro 4.4.1 vendor source comparison, independent
security audit and actual cPanel Apache/Nginx production upload-dir
execution restrictions remain separate release blockers. Do not
promote 0.1.2 or accept arbitrary public ZIPs merely because these
synthetic suites pass.

Relevant guidance:
- [Elementor: custom icon packs](https://elementor.com/help/custom-icons-pro/)
- [Elementor SVG security warning](https://elementor.com/help/enable-svg-support-in-elementor/)
- [WordPress Apache configuration guidance](https://developer.wordpress.org/advanced-administration/server/web-server/httpd/)

## 24 November 2026: official generator format research

The official [IcoMoon documentation](https://icomoon.io/docs) describes
project metadata with an `.icomoon.json` suffix and separate folders per
export format. Its [legacy FAQ](https://icomoon.io/old-faq) instead describes
`selection.json`. The current built-in Icomoon handler requires a root
`selection.json` and legacy metadata/preferences, so modern exports are a
concrete compatibility risk, not yet a reproduced runtime failure. Inspect
the actual modern schema and font/CSS layout before introducing a separate
adapter; do not simply rename JSON or weaken archive checks.

[Fontello's official developers API](https://github.com/fontello/fontello#developers-api)
documents a temporary configuration session and generated ZIP download.
Use only a self-authored non-sensitive configuration with properly licensed
public glyphs, preserving license, provenance, generator date and SHA256.
Its [changelog](https://github.com/fontello/fontello/blob/master/CHANGELOG.md)
also describes embedded base64 fonts, which the current conservative CSS
validator rejects. Verify actual default and optional outputs before
considering a narrowly validated local-font conversion.
[Fontastic's export guide](https://fontastic.me/howto) describes downloadable
CSS, fonts and reference HTML; obtain authentic exports from the service.

For each genuine archive, preserve bytes/hash/license and inventory; inspect
without executing demo files; import through disposable WordPress; verify
icon names, font files, stylesheet URLs and exclusion of demo HTML; render
known glyphs in editor and frontend Chromium with no unexpected external
requests; exercise repeated import and removal. Retain hostile-asset tests
and use license-compatible regression fixtures.

Documentation-only review: no new archives, generator sessions or runtime
tests were created. Real-export and independent audit gates remain open.
The 102/102 result still refers only to its recorded source SHA.

## 24 November 2026: legacy metadata-shape regression fixes

Fontello and IcoMoon accepted malformed list shapes or attempted to read
missing object properties; malformed IcoMoon classSelector could raise a
PHP TypeError. Nonstring pack names were silently treated as default names.
Fontello preparation could also try to read/write a missing stylesheet.
The targeted changes validate JSON list/entry/name types, cap list size,
require the expected stylesheet, avoid the missing-file rewrite, and
handle nonstring display selectors without a TypeError. Empty string
names still fall back to the documented legacy default names.

Baseline: 2/16 passed, 14 failed (including warnings converted to
exceptions and a TypeError), on PHP 8.4 with minimal WordPress stubs.
Patched exact importer code at `33ab19eac2e7f60d17b81be18eb2a53545dc7a2e`:
**16/16 passed on each of PHP 8.4 and PHP 8.5**, including both valid legacy
format cases; all three relevant PHP files linted on both versions.
The repeatable, private-temporary-directory test is tracked at
`tests/test_icon_metadata_shapes.py` (commit
`3fefe78fc5dfea1bc733379d4670292b3098db1b`). Run with
`python3 tests/test_icon_metadata_shapes.py /path/to/php`.
No GitHub Actions or production database changes. These tests exercise
actual importer classes with minimal WordPress stubs, not a full WP
import-manager/browser run. The recorded 102/102 integration suite
remains evidence for its older exact SHA only. Genuine modern exports,
full regression, independent review and release acceptance remain open.

## 24 November 2026: genuine Fontello export acquisition and compatibility fix

The official Fontello API (https://github.com/fontello/fontello#developers-api,
multipart example https://gist.github.com/puzrin/5537065) generated a
one-glyph, public Font Awesome test pack from the project's own publicly
available config; no customer data, credentials, or private artwork were
sent. The URL-encoded request initially returned HTTP 400; the documented
multipart upload succeeded. The original 18-member archive was retained
privately at owner-only QA permissions (not added to Git, not installed).
SHA256: `436d8abd74629563cc7efe92d1dcdb1703ebd3c7d3effacfd6a51d0f8a60dbdf`.
It includes the original LICENSE.txt, README.txt, config, main stylesheet,
optional embedded/IE7 stylesheets, demo and genuine WOFF/WOFF2/TTF/EOT/SVG.

The unmodified validator rejects this real default export. Its optional
embedded CSS contains a base64 data URI and the SVG font contains the
legacy W3C SVG 1.1 external DOCTYPE. The Fontello-specific normalization
at `958e1a1abd94eba23f8a68ea0f9ebe23f0b0022b` removes only the named
optional embedded/IE7 stylesheet variants and the exact known declaration
from the private extracted copy before running the shared strict asset
validator. No arbitrary DOCTYPE or external entities are accepted.
The retained modern stylesheet, fonts and license are unchanged by this
normalization (the pre-existing margin adjustment still applies on normal
preparation). The generic Fontastic/IcoMoon validator is unchanged.

Actual archive baseline rejection, patched acceptance, remote CSS refusal,
active SVG refusal and unknown DOCTYPE refusal passed **5/5** on PHP 8.4
using the real Fontello class and minimal WordPress stubs. The patched
source lint passed. A self-authored equivalent fixture exercising actual
disposable WordPress publication and omission of the optional files was
added at `a839855278e6625cb0ee9bd1a802886d1eed0ad9` and linted on PHP 8.4/8.5.
That new WordPress fixture has not yet passed a full integration run.
Genuine archive import-manager, browser glyph rendering and update/removal
tests remain open, as do modern IcoMoon and genuine Fontastic export QA,
the independent security review and production release gates.
No GitHub Actions, paid services, publication or live deployment.

## 25 November 2026: Fontello normalization runtime verification

The exact source SHA `830c47edb7619335c0a2f79d016891aeb5f7e62a`
passed **28/28** disposable WordPress runtime observations (exit 0,
144.88 seconds), including the extended self-authored Fontello
publication regression and previous malicious SVG/CSS, ZIP, Form,
REST and Stripe security tests. Disposable site/database/network
cleaned. This is runtime-only, not full frontend/editor QA.
The pinned genuine archive import/delete test was added separately
at `b9276e52a70a9fcfccb914ea9a3b84f082b4f7e9` and the opt-in harness
at `ce3d94832bc5580832fd6afccd6360c264829fb9`. Its run is not yet
certified. Genuine modern IcoMoon and Fontastic, actual browser glyph
rendering, external audit, full acceptance and signing remain open.
