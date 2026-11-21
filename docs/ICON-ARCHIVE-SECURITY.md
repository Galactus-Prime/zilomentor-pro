# Custom-icon archive and deletion security review

**Scope:** unreleased ZiloMentor Pro 0.1.2 development branch. This is a
targeted review of inherited PRO Elements 4.4.0 code, not an independent
third-party audit and not evidence of official Elementor Pro 4.4.1 parity.

## Findings and fixes

1. **Client-controlled filename deletion (fixed):** the inherited
   `Custom_Icons::upload()` called `unlink( $filename )` on invalid ZIP
   extension or failed WordPress upload. `$filename` came from
   `$_FILES['zip_upload']['name']`, not the upload temporary-file path.
   The handler now validates upload structure and error status and never
   deletes client-provided path strings. WordPress/PHP retain ownership of
   temporary upload cleanup.
2. **Unbounded ZIP expansion and risky names (fixed):** the old
   `extract_zip()` did not check the result of `ZipArchive::open()`,
   trusted archive entry counts and expanded sizes, and rejected only
   names containing two consecutive dots. It now requires a valid archive,
   rejects ZIP files larger than **32 MiB**, more than **4,096 entries**,
   individual expanded entries above **64 MiB**, cumulative expansion above
   **128 MiB**, and high expansion ratios above **500:1** for files over
   1 MiB. It rejects absolute/drive-letter/backslash/traversal paths,
   symlink entries and dangerous executable extensions *including*
   intermediate extensions such as `icon.php.css`. It closes the archive
   and removes the server-side uploaded archive in all normal return
   branches.
3. **Recursive deletion from imported metadata (fixed):** deleting icon
   CPT posts and two import-revert runners used the saved
   `_elementor_icon_set_path` string as a recursive removal target.
   Import data can originate outside the installation. All three paths
   now use `Custom_Icons::is_safe_icon_set_directory()` to require a
   real, existing, non-symlink **direct child** of the configured
   `elementor/custom-icons` storage root. The root itself, unrelated
   directories and nested paths are not eligible.
4. **Missing global post in Posts Full Content skin (fixed):**
   `Skin_Content_Base::render_post_content()` returns without output if
   `get_post()` does not produce a `WP_Post`, preventing a null
   dereference in unusual preview/query contexts. This is a targeted
   independent fix related to the vendor's public 4.4.1 changelog, not
   proof that the vendor used identical code.

## 21 November follow-up: safe public asset handling

A real Fontastic-style synthetic pack revealed another inherited import
hazard: malformed stylesheet CSS can cause `extract_icon_list()` to
return `false`, and the old `build_config()` called `count(false)`,
raising a PHP TypeError. A filename-valid ZIP is not necessarily a
valid icon set.

The 0.1.2 source now validates the icon name, nonempty icon-list array,
maximum 8,192 names, each bounded/nonempty string, and a nonempty
prefix **before** moving imported files into public uploads. The
config builder itself refuses invalid icon-list types rather than
triggering a fatal. Fontastic pack metadata caches are scoped per
instance, rather than leaking name/prefix between successive imports.

The inherited copy process also published untrusted
`demo.html`, `icons-reference.html` and nested HTML pages to the
site's `wp-content/uploads/elementor/custom-icons` origin.
These HTML files are now **excluded from public copy**, after any
temporary parsing has occurred. Stylesheets and font files are still
copied. `tests/runtime_icon_public_html_safety.php` verifies
a functional Fontastic pack's icon configuration, CSS/WOFF assets,
omission of both root and nested HTML, and clean invalid-pack
rejection. The isolated runtime suite passed at SHA
`ad9d11df671602d6720486eef37ef92cbc4fcc64`;
see `docs/ICON-PUBLIC-ASSET-REVIEW.md`.

**SVG remains a separate security-review requirement:** the icon
importer also accepts legacy SVG font assets. Existing Elementor
image-SVG sanitisation does not automatically cover ZIP-extracted
font files, and its default allowed elements omit legacy SVG font
glyph structures. Do not extrapolate this HTML safety fix into a
claim that arbitrary uploaded SVG or CSS is safe.

## Reproducible zero-subscription QA

The disposable `tests/runtime_icon_zip_security.php` fixture constructs
real ZIP central directories and checks a valid asset archive against
traversal, absolute/Windows paths, backslashes, compressed ZIP bombs,
excessive entries, executable double extensions, an invalid upload
filename and improper recursive-deletion paths. The fixture cleans only
its own randomly named temporary directory.

**Important:** the old cached PHP-FPM Docker image lacked `ZipArchive`.
This was detected when the new runtime check failed instead of silently
skipping ZIP tests. For repeatable testing, build a ZIP-enabled **QA-only**
image using the tracked Dockerfile:

```bash
docker build -f tools/docker/Dockerfile.qa-php84-zip -t zmp-php84-zip-qa:local .
docker run --rm --network none --entrypoint php zmp-php84-zip-qa:local -r 'var_export(class_exists("ZipArchive"));'
python3 tools/qa_isolated_site.py --source-wordpress /path/to/read-only-wordpress-source --plugin-folder zilomentor-pro --web-server nginx-fpm --focus runtime
```

No GitHub Actions, commercial QA service, customer payments, real email,
production database or production WordPress files are required.

## Full-suite verification (20 November 2026)

The complete manual suite passed on code SHA
`ef5564c9a84646369417de31073bc8c9fdbc0f8e` with the cached
ZIP-enabled PHP-FPM image: **88/88 disposable WordPress integrations**
passed, including `runtime_icon_zip_security.php`,
`runtime_form_upload_security.php`, nested filename validation, and
PHP 8.4/8.5 parsing. The staging-only release ZIP checksum is recorded
in `docs/RELEASE-BLOCKERS.md`. The test does not include a live
customer upload or paid-processor transaction.

## Remaining caveats

- Validate against genuine Fontello, IcoMoon and Fontastic export archives,
  including custom developer-provided directory filters.
- Imported HTML demo pages are now excluded, but custom SVG font
  content and arbitrary stylesheet CSS still require an independent
  content-security review. Archive limits protect ZIP handling, not
  arbitrary active file content.
- Real Apache/Nginx HTTP upload execution tests and complete independent
  security assessment remain separate release gates.
- The official Elementor Pro **4.4.1** patch diff is not available to this
  audit. Do not assert upstream security parity or ship an unsigned update.
