# Custom icon archive: same-origin HTML and malformed data review

**21 November 2026.** ZiloMentor Pro 0.1.2 development only.
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

## Important security boundaries NOT yet established

The existing icon ZIP importer also accepts `.svg` and CSS.
**The new HTML omission is not comprehensive SVG sanitisation**:
Elementor's general SVG sanitizer is intended for image uploads and
its default allowlist does not contain the legacy `font`/`glyph`
SVG webfont elements. Applying it blindly could destroy valid SVG
font exports. SVG may contain active script and must be handled with
the same caution as HTML. Similarly, untrusted CSS warrants separate
review. For now, limit custom icon ZIP imports to independently
trusted, approved source packs and keep this as an explicit
security-review follow-up before general release.

Also, protecting icon uploads from executable content is not the same
as proving live cPanel Apache virtual-host inherited policy, and
Nginx does not interpret `.htaccess`. The production upload web-server
gate remains open until actual controlled physical tests are performed.

Relevant guidance:
- [Elementor: custom icon packs](https://elementor.com/help/custom-icons-pro/)
- [Elementor SVG security warning](https://elementor.com/help/enable-svg-support-in-elementor/)
- [WordPress Apache configuration guidance](https://developer.wordpress.org/advanced-administration/server/web-server/httpd/)
