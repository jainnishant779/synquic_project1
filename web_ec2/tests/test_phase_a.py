"""Tests for Phase A upgrades: safe-zone pixel geometry, glass card background,
elements_at timestamp inspection contract, audio-safe scene splitting, and instruct diffs.
"""
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ad_director  # noqa: E402
import ad_engine as ae  # noqa: E402


class PhaseASafeZoneTests(unittest.TestCase):
    def test_safe_zone_pixel_geometry_deterministic(self):
        # 1. Instagram Reels 1080x1920 (9:16)
        reels_box = ae.safe_area("reels", 1080, 1920)
        self.assertEqual(reels_box, (65, 269, 1015, 1248))
        self.assertEqual(reels_box[1], 269)  # top unsafe 269px
        self.assertEqual(1920 - reels_box[3], 672)  # bottom unsafe 672px
        self.assertEqual(reels_box[0], 65)  # left unsafe 65px
        self.assertEqual(1080 - reels_box[2], 65)  # right unsafe 65px

        # 2. YouTube Shorts 1080x1920 (9:16)
        shorts_box = ae.safe_area("shorts", 1080, 1920)
        self.assertEqual(shorts_box, (65, 192, 972, 1440))
        self.assertEqual(shorts_box[1], 192)  # top unsafe 192px
        self.assertEqual(1920 - shorts_box[3], 480)  # bottom unsafe 480px
        self.assertEqual(shorts_box[0], 65)  # left unsafe 65px
        self.assertEqual(1080 - shorts_box[2], 108)  # right unsafe 108px

        # 3. Meta Feed 1080x1350 (4:5)
        feed_box = ae.safe_area("feed", 1080, 1350)
        self.assertEqual(feed_box, (54, 108, 1026, 1148))
        self.assertEqual(feed_box[1], 108)  # top unsafe 108px
        self.assertEqual(1350 - feed_box[3], 202)  # bottom unsafe 202px
        self.assertEqual(feed_box[0], 54)  # left unsafe 54px
        self.assertEqual(1080 - feed_box[2], 54)  # right unsafe 54px

        # 4. Meta Reels HD 1440x2560 (9:16)
        reels_hd_box = ae.safe_area("reels", 1440, 2560)
        self.assertEqual(reels_hd_box, (86, 358, 1354, 1664))
        self.assertEqual(reels_hd_box[1], 358)
        self.assertEqual(2560 - reels_hd_box[3], 896)
        self.assertEqual(reels_hd_box[0], 86)
        self.assertEqual(1440 - reels_hd_box[2], 86)


class PhaseAGlassCardTests(unittest.TestCase):
    def test_glass_card_style_available_and_renders(self):
        self.assertIn("glass", ae.CARD_STYLES)
        with tempfile.TemporaryDirectory() as td:
            out_path = Path(td) / "glass_card.jpg"
            ae.make_card_background(out_path, 1080, 1920, "#18B26B", style="glass")
            self.assertTrue(out_path.is_file())
            with Image.open(out_path) as img:
                self.assertEqual(img.size, (1080, 1920))
                self.assertEqual(img.mode, "RGB")


class PhaseAInspectionTests(unittest.TestCase):
    def setUp(self):
        self.t = ae.default_timeline("Homingo", platform="reels")
        self.t["scenes"] = [
            {"id": "s1", "kind": "product", "product": "cutout.png", "source": "bg1.jpg", "duration": 4.0, "narration": "Line one",
             "text": [{"id": "t1", "text": "Leaking pipe?", "style": "kinetic", "position": "top", "start": 0.1, "end": 3.0},
                      {"id": "t2", "text": "Homingo", "style": "lower_third", "position": "bottom", "start": 1.0, "end": None}]},
            {"id": "s2", "kind": "card", "duration": 3.0, "narration": "Call now",
             "text": [{"id": "t1", "text": "Book now", "style": "cta", "position": "bottom", "start": 0.2, "end": None}]}
        ]

    def test_elements_at_contract(self):
        info = ae.elements_at(self.t, 1.5)
        # Spec contract keys
        self.assertEqual(info["scene_id"], "s1")
        self.assertEqual(info["scene_index"], 0)
        self.assertEqual(info["t_scene"], 1.5)
        self.assertIn("visual_layer", info)
        vlayer = info["visual_layer"]
        self.assertEqual(vlayer["bg_uri"], "bg1.jpg")
        self.assertEqual(vlayer["cutout_uri"], "cutout.png")
        self.assertEqual(vlayer["parallax_preset"], "smooth_2.5d")
        self.assertEqual(vlayer["safety_badge"], "Exact Product Layer")

        # Active text layers with geometry
        active = info["active_text_layers"]
        self.assertEqual(len(active), 2)
        self.assertEqual(active[0]["id"], "t1")
        self.assertIn("y_anchor", active[0])
        self.assertIn("bounding_box", active[0])

    def test_audio_safe_split_scene(self):
        edited = ae.apply_edit(self.t, {"op": "split_scene", "scene": "s1", "at": 1.8})
        s1 = edited["scenes"][0]
        s2 = edited["scenes"][1]
        self.assertEqual(s1["duration"], 1.8)
        self.assertEqual(s2["duration"], 2.2)
        # The voice line must carry on past the cut: measure the audio, not just the fields
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            tone = tmp / "line.wav"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=3.5", str(tone)], check=True)
            out = tmp / "voice.wav"
            warnings = ae.build_voice_track(edited, {"s1": tone}, out, tmp)
            self.assertEqual(warnings, [])
            probe = subprocess.run(["ffmpeg", "-hide_banner", "-ss", "2.3", "-t", "1.1", "-i", str(out), "-af", "volumedetect", "-f", "null", "-"],
                                   capture_output=True, text=True).stderr
            mean = float(next(l for l in probe.splitlines() if "mean_volume" in l).split("mean_volume:")[1].split("dB")[0])
            self.assertGreater(mean, -40.0, "voice went silent after the split point")


class PhaseADirectorTests(unittest.TestCase):
    def test_director_plan_schema_has_on_screen_and_tts(self):
        t, brief, notes = ad_director.plan_ad("make ad for organic honey", length_s=15)
        for scene in t["scenes"]:
            self.assertIn("on_screen_text", scene)
            self.assertIn("voice_line_tts", scene)
            self.assertTrue(all(len(text) <= 32 for text in scene["on_screen_text"]))


if __name__ == "__main__":
    unittest.main()
