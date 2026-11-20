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

## Remaining caveats

- Validate against genuine Fontello, IcoMoon and Fontastic export archives,
  including custom developer-provided directory filters.
- An admin-supplied HTML/CSS icon archive still warrants a dedicated
  browser and content-security review before treating imported code as
  trusted. Archive limits mitigate resource exhaustion and filesystem
  traversal; they do not prove all supported formats are harmless.
- Real Apache/Nginx HTTP upload execution tests and complete independent
  security assessment remain separate release gates.
- The official Elementor Pro **4.4.1** patch diff is not available to this
  audit. Do not assert upstream security parity or ship an unsigned update.
