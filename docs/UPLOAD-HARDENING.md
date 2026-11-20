# Form upload archive and web-server safety (0.1.2 development)

**20 November 2026.** This applies to the **unreleased ZiloMentor Pro 0.1.2
candidate** only, not the installed 0.1.1 beta on Itzy Bitzy Workshop.

## Threat model and implemented controls

Anonymous classic Form and Atomic Form uploads need three independent protections:

1. **Content checks before moving files:** `Core\Utils::is_form_upload_content_safe()`
   accepts only WordPress-registered extensions/MIME combinations and checks
   server-detected content. Office ZIP formats now also reject files with more
   than **4,096 entries**, any single entry advertising over **64 MiB**
   uncompressed, a total advertised uncompressed size over **128 MiB**, or an
   entry over 1 MiB with a compression ratio above **500:1**. Absolute,
   traversal or backslash ZIP entry paths are rejected. These are metadata
   safeguards, not complete malware, XML, compression-engine or authenticity
   verification. Very large or unusually compressible legitimate Office files
   may be rejected and should be checked with owner-supplied samples.
2. **Apache upload directory policy:** both V3 and Atomic handlers create
   an `.htaccess` for *new* `wp-content/uploads/elementor/forms/`
   directories. It denies common executable extension requests with
   `FilesMatch` / `Require all denied`, disables indexing, and, when
   `mod_headers` is enabled, sets `Content-Disposition: attachment`,
   `X-Content-Type-Options: nosniff` and
   `Cache-Control: private, no-store`. Existing customised `.htaccess`
   files are **not silently overwritten**; audit and migrate older weak rules
   separately. `.htaccess` only works when Apache permits overrides.
3. **Nginx/PHP-FPM:** Nginx **ignores** `.htaccess`. The disposable QA
   configuration explicitly denies PHP-like files from all WordPress uploads
   before its PHP handler, and serves Form files download-only/no-sniff.
   The production Nginx/Apache vhost must be reviewed separately; a synthetic
   isolated rule is not evidence of protection on another site.

## Regression evidence

`tests/runtime_form_upload_security.php` exercises structurally valid Office
fixtures, deliberately over-compressed DOCX and ZIP traversal fixtures, both
real Form directory writers, and the generated Apache rule contents in a
**fresh disposable WordPress database**. Static checks and PHP syntax tests are
run by `tools/run_manual_checks.py`; full runtime test execution also
requires `tools/qa_isolated_site.py`.

The disposable Nginx test inspects executable-extension denial and actual
attachment/no-sniff response headers. Passing all of these does not establish
that Apache honouring `.htaccess` on the owner's cPanel vhost was tested.

Read-only host checks on 20 November identified `Apache/2.4.71 (cPanel)` and
an absent `wp-content/uploads/elementor/forms` directory at the inspected
WordPress root; a nonexistent `.php` Form URL gave HTTP 404 with no-sniff.
**A nonexistent-file 404 is not a live executable-upload security test.**
No live Form file was created and no live web-server configuration was edited.

## Before promoting to production

- Test real permitted PDF, Office/ODF, audio and video sample files; compare
  normal, compressed and unusual Office documents. Reject or explicitly
  document any compatibility exceptions rather than disabling content checks.
- Confirm the *effective* Apache virtual host honours `.htaccess`, has
  `mod_authz_core` and `mod_headers`, and does not allow PHP execution from
  uploaded content. Review any existing Form `.htaccess` for older rules.
- Where Nginx sits in front of Apache, or serves uploads directly, enforce
  and independently test the Nginx location order (executable deny before
  Form static-file delivery and before PHP-FPM).
- Test the response to a deliberately **harmless, fake PHP-named file**
  only in a throwaway site, not against actual customer uploads.
- Review anonymous attachment URL exposure as a privacy decision:
  download-only headers do **not** authenticate the person following a link.

Background: [WordPress Nginx guidance](https://developer.wordpress.org/advanced-administration/server/web-server/nginx/),
[WordPress Apache guidance](https://developer.wordpress.org/advanced-administration/server/web-server/httpd/),
[Apache FilesMatch and overrides](https://httpd.apache.org/docs/2.4/sections.html).
