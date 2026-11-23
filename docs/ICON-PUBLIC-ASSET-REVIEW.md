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
