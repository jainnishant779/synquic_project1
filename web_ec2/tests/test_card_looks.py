"""Tests for designed card backgrounds: speed, determinism, readability contrast,
brand colour differentiation, and calm text bands across all CARD_STYLES and test colours.
"""
import sys
import tempfile
import time
import unittest
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ad_engine as ae

TEST_COLORS = ["#2E7D32", "#FFC107", "#E53935", "#1E88E5", "#8E24AA", "#FFFFFF", "#111111"]
CALM_STYLES = {"glow", "dark", "light", "glass", "mesh", "paper", "neon", "minimal"}


def _srgb_to_linear(c):
    c = np.array(c, dtype=float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _relative_luminance(rgb):
    lin = _srgb_to_linear(rgb)
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _contrast_ratio(l1, l2):
    bright = max(l1, l2)
    dark = min(l1, l2)
    return (bright + 0.05) / (dark + 0.05)


class CardLooksHardRequirementsTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory(prefix="card_test_")
        self.temp_dir = Path(self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def test_a_speed_under_1_point_5_seconds(self):
        """(a) make_card_background(path, 1080, 1920, colour, style) finishes in under 1.5 seconds."""
        out_path = self.temp_dir / "speed.jpg"
        ae.make_card_background(out_path, 1080, 1920, "#2E7D32", style="glow")   # warm-up: the first call loads numpy and Pillow
        for style in ae.CARD_STYLES:
            for col in TEST_COLORS:
                t0 = time.perf_counter()
                ae.make_card_background(out_path, 1080, 1920, col, style=style)
                dt = time.perf_counter() - t0
                self.assertLess(dt, 1.5, f"Style {style} with {col} took {dt:.3f}s (>= 1.5s)")

    def test_b_deterministic(self):
        """(b) Deterministic: two calls give identical bytes (fixed seed for any noise)."""
        p1 = self.temp_dir / "det1.jpg"
        p2 = self.temp_dir / "det2.jpg"
        for style in ae.CARD_STYLES:
            for col in TEST_COLORS:
                ae.make_card_background(p1, 1080, 1920, col, style=style)
                ae.make_card_background(p2, 1080, 1920, col, style=style)
                self.assertEqual(p1.read_bytes(), p2.read_bytes(), f"Style {style} with {col} is non-deterministic")

    def test_c_readable_contrast(self):
        """(c) Readable: text colour from card_look() has WCAG contrast ratio >= 4.5:1
        against the average colour of top band (14%-35%) and bottom band (45%-65%)."""
        out_path = self.temp_dir / "contrast.jpg"
        w, h = 1080, 1920
        top_y1, top_y2 = int(0.14 * h), int(0.35 * h)
        bot_y1, bot_y2 = int(0.45 * h), int(0.65 * h)

        for style in ae.CARD_STYLES:
            for col in TEST_COLORS:
                ae.make_card_background(out_path, w, h, col, style=style)
                with Image.open(out_path) as img:
                    arr = np.array(img.convert("RGB"), dtype=float)

                top_band = arr[top_y1:top_y2, :]
                bot_band = arr[bot_y1:bot_y2, :]

                avg_top = np.mean(top_band, axis=(0, 1))
                avg_bot = np.mean(bot_band, axis=(0, 1))

                lk = ae.card_look({"card": style, "text": ae.DEFAULT_LOOK["text"], "highlight": ae.HIGHLIGHT}, col)
                text_rgb = ae._hex_rgb(lk["text"])
                text_lum = _relative_luminance(text_rgb)

                top_lum = _relative_luminance(avg_top)
                bot_lum = _relative_luminance(avg_bot)

                cr_top = _contrast_ratio(text_lum, top_lum)
                cr_bot = _contrast_ratio(text_lum, bot_lum)

                self.assertGreaterEqual(
                    cr_top, 4.5,
                    f"Style '{style}' on brand '{col}' top band CR {cr_top:.2f} < 4.5 (text {lk['text']}, band avg {avg_top.tolist()})"
                )
                self.assertGreaterEqual(
                    cr_bot, 4.5,
                    f"Style '{style}' on brand '{col}' bottom band CR {cr_bot:.2f} < 4.5 (text {lk['text']}, band avg {avg_bot.tolist()})"
                )

    def test_d_brand_colour_matters_mad(self):
        """(d) The brand colour matters: for every style, images for #2E7D32 and #FFC107
        differ by a mean absolute pixel difference of more than 12 (on 0..255)."""
        p_green = self.temp_dir / "green.jpg"
        p_yellow = self.temp_dir / "yellow.jpg"
        w, h = 1080, 1920

        for style in ae.CARD_STYLES:
            ae.make_card_background(p_green, w, h, "#2E7D32", style=style)
            ae.make_card_background(p_yellow, w, h, "#FFC107", style=style)

            with Image.open(p_green) as img_g, Image.open(p_yellow) as img_y:
                arr_g = np.array(img_g.convert("RGB"), dtype=float)
                arr_y = np.array(img_y.convert("RGB"), dtype=float)

            mad = float(np.mean(np.abs(arr_g - arr_y)))
            self.assertGreater(
                mad, 12.0,
                f"Style '{style}' failed MAD check between #2E7D32 and #FFC107: MAD was {mad:.2f} (required > 12.0)"
            )

    def test_e_calm_text_bands(self):
        """(e) For calm looks (glow, dark, light, glass, mesh, paper, neon, minimal),
        the standard deviation of luminance inside each text band is under 40."""
        out_path = self.temp_dir / "calm.jpg"
        w, h = 1080, 1920
        top_y1, top_y2 = int(0.14 * h), int(0.35 * h)
        bot_y1, bot_y2 = int(0.45 * h), int(0.65 * h)

        for style in CALM_STYLES:
            for col in TEST_COLORS:
                ae.make_card_background(out_path, w, h, col, style=style)
                with Image.open(out_path) as img:
                    arr = np.array(img.convert("RGB"), dtype=float)

                top_band = arr[top_y1:top_y2, :]
                bot_band = arr[bot_y1:bot_y2, :]

                # Luminance formula: 0.299*R + 0.587*G + 0.114*B on 0..255
                top_luma = 0.299 * top_band[:, :, 0] + 0.587 * top_band[:, :, 1] + 0.114 * top_band[:, :, 2]
                bot_luma = 0.299 * bot_band[:, :, 0] + 0.587 * bot_band[:, :, 1] + 0.114 * bot_band[:, :, 2]

                top_std = float(np.std(top_luma))
                bot_std = float(np.std(bot_luma))

                self.assertLess(
                    top_std, 40.0,
                    f"Calm style '{style}' on brand '{col}' top band std {top_std:.2f} >= 40.0"
                )
                self.assertLess(
                    bot_std, 40.0,
                    f"Calm style '{style}' on brand '{col}' bottom band std {bot_std:.2f} >= 40.0"
                )


if __name__ == "__main__":
    unittest.main()
