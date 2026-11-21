#!/usr/bin/env python3
"""Regression for Motion Effects callbacks with reduced-motion enabled.

The handler skips initEffects() when Reduced Motion is enabled. Resize
and editor callbacks must not dereference uninitialized animation effects.
Both shipped JavaScript source and minified assets must retain the guard.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReducedMotionTests(unittest.TestCase):
    def test_unminified_guards(self):
        script = (ROOT / "assets/js/frontend.js").read_text(encoding="utf-8")
        self.assertIn('if (prefersReducedMotion && prefersReducedMotion.matches) return;', script)
        self.assertIn('if (!this.effects) return;\n\t\t\tconst currentDeviceMode', script)
        self.assertIn('onElementChange(propertyName) {\n\t\t\tif (!this.effects) return;', script)

    def test_minified_guards(self):
        script = (ROOT / "assets/js/frontend.min.js").read_text(encoding="utf-8")
        self.assertIn('toggle(){if(!this.effects)return;const e=elementorFrontend.getCurrentDeviceMode()', script)
        self.assertIn('onElementChange(e){if(!this.effects)return;if(/motion_fx_', script)
        self.assertIn('e&&e.matches||(this.initEffects()', script)


if __name__ == "__main__":
    unittest.main(verbosity=2)
