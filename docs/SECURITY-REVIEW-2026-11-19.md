# ZiloMentor Pro security and release review — 19 November 2026

**Scope:** draft 0.1.2 versus deployed 0.1.1; independent GPL fork based on
PRO Elements 4.4.0. No live customer/order/payment data was used for this audit.

## 20 November follow-up: anonymous Form upload hardening (0.1.2 candidate)

An actual code-path audit of the upstream-derived V3 Form Upload and V4
Atomic Form storage uncovered a bounded defense-in-depth gap: V3 validated
image contents but treated arbitrary non-image *extensions configured in
a Form field* as sufficient, even when the file's actual bytes did not
match. WordPress itself cautions that its filetype validator has
image-specific content checks and not every MIME is fully verified.
Source: https://developer.wordpress.org/reference/functions/wp_check_filetype_and_ext/

The development branch now adds **one shared content validator** in
`core/utils.php` and calls it **before storing** uploads in both
`modules/forms/fields/upload.php` and
`modules/atomic-form/file-upload/file-storage.php`. It:

- refuses unrecognised and dangerous script/executable extensions;
- requires registered WordPress MIME types and FileInfo inspection;
- verifies PDF magic and actual PDF MIME, checks Office Open XML ZIP
  structure, requires legacy Office compound-file signatures;
- verifies image structures and real audio/video MIME categories,
  and rejects script-bearing text that would otherwise be served back
  from public upload URLs;
- makes failed Atomic Form cleanup **delete only direct files inside its
  own `uploads/elementor/forms` directory**, not arbitrary outside paths
  or symlinks.

**Compatibility change:** an administrator listing a non-standard file
extension in a Form is no longer enough to accept anonymous uploads.
Custom types must be registered through WordPress's `upload_mimes`
filter and have a MIME/content combination accepted by the stricter
validator. This can reject some legitimate specialised CAD files or
unusual multimedia MIME variants; review real workflow requirements
before enabling the candidate on production.

Disposable testing generated valid PDF/Office/image/text fixtures and
mislabeled PHP, arbitrary ZIP and script-content fixtures. Legacy and
Atomic checks rejected spoofed types and verified cleanup constraints.
**44/44 initial focused runtime/editor checks**, **68/68 full
storefront/popup/offline WooCommerce checks**, **53/53 full
editing/publishing/responsive checks**, and a further **38/38 REST
authorization focused runtime checks** passed. Also **49/49 static
checks** and **941 PHP files under each of PHP 8.4 and 8.5** passed.
The
tests used a disposable WordPress/MariaDB instance and did not submit
an actual production Form. A complete malware scan, all file formats,
proxy-specific `.htaccess` behaviour, payment gateways and full
vendor 4.4.1 source parity remain unverified.

A second synthetic REST test calls the **actual registered Pro icon/SVG
permission callbacks** as guest, subscriber, contributor and editor in
disposable WordPress. Privileged icon writes are denied to contributors
and lower roles, and protected icon reads are denied to guests and
subscribers while editor reads remain available. This test passed in the
isolated runtime; it deliberately does **not** dispatch writes, send
network requests, or claim a complete REST authentication/nonce audit.

The signed-manual-release, migration and ZIP hygiene tests also
passed with zero failures, without GitHub Actions. An operational signing
key and a safe signed online update channel are **not** provisioned; see
`docs/OFFLINE-RELEASE-SIGNING.md`.

The deployed live version remains **0.1.1** and has **not** received
these unreleased changes.

## Source of truth and limits

- Official Elementor Pro 4.4.1, dated 16 November 2026, announces
  **security enforcement improvements in attributes** and a **missing post
  data warning** fix in Posts. See https://elementor.com/pro/changelog/.
- The public PRO Elements project (https://github.com/proelements/proelements)
  still publishes 4.4.0 as the current supported upstream at audit time.
- **There is no trustworthy complete 4.4.1 Pro source diff available in this
  audit.** Therefore the fork **must not** assert vendor patch parity, complete
  CVE remediation, or equivalence to the current paid plugin.

## Concrete fixes and evidence

1. **Atomic attributes (deployed 0.1.1):** the direct HTML string-concatenation
   transformer is constrained by valid attribute names, blocks event handlers,
   srcdoc and inline style and sanitises URL schemes. Values use WordPress
   output escaping. Ten adversarial/normal cases passed in actual disposable
   WordPress/Elementor runtime, including quote breakout, URL schemes, data/ARIA
   and malformed input. This is a *targeted* remediation, not a vendor diff.
2. **Legacy custom attributes (unreleased 0.1.2):** wrapper attribute names
   validated, dangerous event names and schemes denied, Elementor's own
   attribute output renderer still escapes values. The real synthetic Elementor
   Heading's markup retained a safe data attribute and ARIA text but excluded
   onclick, onmouseover and javascript URL text. Suite passed **40/40** on
   disposable Fiore, including PHP/REST Posts regression.
3. **Posts widget absent post guard (unreleased 0.1.2):** pagination avoids
   dereferencing a missing WP_Post. A disposable REST-like preview test
   confirms the expected fallback URL and no PHP warnings. Test also asserts
   that the REST-preview branch was reached.
4. **Package hygiene (deployed since 0.1.1):** release ZIP uses only
   Git-tracked source files and excludes SQL, credentials, runtime logs and
   cPanel PHP caches. Synthetic packaging tests reject accidental sensitive
   files. The formerly generated error_log was removed from the live plugin
   directory and returned HTTP 404.
5. **Versioned release and rollback (0.1.1 live, 0.1.2 candidate):** private
   filesystem-owner backup, exact SHA256 archive, stricter ZIP path/expanded
   size checks and WordPress bootstrap checks; previous version and original
   Elementor Pro files kept private. Never restore a live WooCommerce database
   without separately reconciling post-snapshot orders.
6. **Signed manual releases (unreleased 0.1.2):** Ed25519 detached signatures,
   explicitly trusted owner-owned public key outside webroot, signed JSON
   binding plugin basename, version, filename, SHA256, file size, issue and
   expiry time (max 180 days). Rejects unsigned 0.1.2+, invalid and expired
   signatures, downgrade and archive mismatch. Tests use transient throwaway
   keys; **no operational private key has been provisioned**.

## Highest priority open reviews (not claimed vulnerabilities)

1. **Upstream security parity:** acquire a legitimate, complete Pro 4.4.1
   patch comparison or verified community release before certifying patch
   equivalence. Keep the draft status and narrow beta scope meanwhile.
2. **Anonymous upload workflows:** audit configured extension/MIME handling
   and storage exposure in `modules/forms/fields/upload.php` and
   `modules/atomic-form/file-upload/file-storage.php`. The legacy handler
   allows administrator-configured non-image types; this is not, by itself,
   evidence of a successful exploit. Test image/polyglot rejection and
   Nginx restrictions with synthetic files only.
3. **Payments:** the public Stripe and WooCommerce form endpoints require
   separate provider sandbox tests for authorization, total enforcement,
   refunds, duplicate submissions, nonce handling and failure recovery.
   The passing BACS QA order is *not* proof of card-gateway safety.
4. **Authenticated REST endpoints:** review user capabilities, ownership and
   nonces for forms/submissions, notes, assets, global widgets and custom
   icon SVG endpoints. Test guest, subscriber, editor and admin roles in
   disposable WordPress installations.
5. **Editor integration:** validate full Form field repeaters/actions,
   History undo/redo, Popup editor, responsive styling persistence and
   keyboard accessibility. The desktop homepage baseline already had two
   JS errors and one broken image *before* the ZiloMentor 0.1.1 switch; do
   not misattribute those to the fork without diagnosis.
6. **Signed online update channel:** a signed owner-operated CLI update
   exists. The self-service WordPress update feed, hardened artifact host
   and offline private-key custody process are **not implemented live**.
   Keep release publishing manual and prohibit auto-update until they are.

## Current deployment gate

- **Live:** Itzy Bitzy Workshop runs tested **ZiloMentor Pro 0.1.1**,
  alongside free Elementor 4.4.1 and WooCommerce, with protected backups
  and previous-version/official-plugin code rollback.
- **Development:** draft **0.1.2** contains additional security fixes and
  signed-manifest manual update requirements. Do not deploy merely because
  tests pass: the offline key must be generated/protected, release manifest
  independently approved, and visual/payment-risk gates reviewed.
- **No GitHub Actions** is required or enabled by the development branch.

This is a bounded code and functional audit, **not a penetration-test report**,
formal vulnerability disclosure, or assurance that all Elementor Pro code is
free of vulnerabilities.
