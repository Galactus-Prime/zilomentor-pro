# Disposable WordPress editor acceptance, 21 November 2026

**Exact tested source SHA:**
`46ec6c2e446c151dcd374fbad24423edc65cfff5`.
**Result: EXIT 0, no failed assertions.**

This opt-in test used an isolated WordPress 7.1.5 / Elementor free 4.4.1 /
ZiloMentor 0.1.2 / Fiore / WooCommerce 11.3 stack and a cached local
Playwright Chromium image. It used synthetic pages, an ephemeral editor
login token, a private Docker network and disposable MariaDB, not the
live Itzy Bitzy Workshop editor or customer database.

Run options:

```text
--focus editor --web-server nginx-fpm
--editor-playwright-image haven-browser-qa:1.62.1
--verify-editor-save --verify-editor-history
--verify-editor-form-save --verify-editor-form-fields
--verify-theme-builder-save --verify-popup-editor-save
--verify-posts-nav-editor --verify-editor-responsive
```

## Verified by real browser input and independent persisted-data checks

- Authenticated Elementor editor shell opened; ordinary Heading controls
  and populated panel matched an independent **free Elementor baseline
  on the same disposable site** (free plugin activated while ZiloMentor
  was deactivated). Re-activation succeeded.
- Heading title was changed using the real editor Publish button; saved
  value was checked directly against `_elementor_data`.
- History **Undo and Redo** were exercised before Publish and the redone
  value was verified in stored WordPress metadata.
- Pro Form name and a repeater field label were changed through the
  editor, published, directly verified in the synthetic database and
  rendered correctly in isolated frontend markup.
- Theme Builder Header title was changed and published; the saved
  template was verified in the database and rendered **only on the
  assigned synthetic target page**.
- Popup template title was changed and published; saved document and
  page-specific condition were independently verified.
- Nav Menu label was edited and persisted without losing the Posts
  widget; published link and Posts rendering were verified.
- Real browser responsive controls selected **Desktop, Tablet, Mobile**
  and restored Desktop, with expected viewport widths and retained
  Heading/Form controls.
- Additional anonymous/private Form document protections, widget
  rendering, ACF tags, Nginx upload-policy checks and basic
  authenticated-shell access passed as prerequisites.

The test did **not** use GitHub Actions or a paid browser service.

## Still not accepted

This is representative **editor smoke and saved-state verification**,
not WCAG certification, actual assistive-technology/keyboard testing,
visual pixel-level human acceptance, exhaustive widget/action coverage,
payment-provider sandbox approval, full official Pro 4.4.1 patch
comparison, or an independent security audit. Those gates stay open
in `docs/RELEASE-BLOCKERS.md`.

The tested editor source is *earlier* than the subsequent custom-icon
asset security work. Those icon changes do not target editor save code,
but no claim of an independently retested post-icon editor snapshot
is made here.
