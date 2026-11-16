"""Tests for the ad engine. Rendering tests run real ffmpeg on generated sample media, with no network and no paid call."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ad_engine as ae  # noqa: E402


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def make_sample_video(path, seconds=5, w=640, h=360):
    ffmpeg("-f", "lavfi", "-i", f"testsrc2=s={w}x{h}:r=24:d={seconds}", "-pix_fmt", "yuv420p", str(path))


def make_sample_photo(path):
    ffmpeg("-f", "lavfi", "-i", "testsrc2=s=800x800:d=1", "-frames:v", "1", str(path))


def make_tone(path, seconds, freq=440):
    ffmpeg("-f", "lavfi", "-i", f"sine=frequency={freq}:duration={seconds}", str(path))


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.t = ae.plan_timeline("Homingo", headline="Leaking pipe? *Fixed today.*", features=["Verified plumbers", "Upfront pricing", "Same-day visit"], cta="Book on the app")

    def test_plan_fills_the_requested_length(self):
        self.assertEqual(ae.total_duration(self.t), 15.0)
        self.assertEqual(len(self.t["scenes"]), 5)
        self.assertEqual(self.t["scenes"][-1]["text"][1]["style"], "cta")
        long = ae.plan_timeline("Homingo", features=["a", "b", "c", "d"], duration_s=30)
        self.assertEqual((ae.total_duration(long), len(long["scenes"])), (30.0, 8))   # about 3 s a scene, at most 8

    def test_card_mode_never_claims_ai_video(self):
        self.assertTrue(all(s["kind"] == "card" for s in self.t["scenes"]))
        ai = ae.plan_timeline("Homingo", features=["x"], mode="ai")
        self.assertTrue(all(s["kind"] == "ai_video" for s in ai["scenes"]))

    def test_edits_change_only_what_they_name_and_leave_the_input_alone(self):
        before = ae.validate_timeline(self.t)
        edited = ae.apply_edit(before, {"op": "set_text", "scene": "s2", "layer": "t1", "text": "Pros who show up"})
        self.assertEqual(edited["scenes"][1]["text"][0]["text"], "Pros who show up")
        self.assertEqual(before["scenes"][1]["text"][0]["text"], self.t["scenes"][1]["text"][0]["text"])
        self.assertEqual(edited["scenes"][0], before["scenes"][0])
        moved = ae.apply_edit(edited, {"op": "move_scene", "scene": "s3", "to": 0})
        self.assertEqual(moved["scenes"][0]["id"], "s3")
        self.assertEqual(len(ae.apply_edit(moved, {"op": "delete_scene", "scene": "s3"})["scenes"]), 4)
        self.assertEqual(ae.apply_edit(moved, {"op": "duplicate_scene", "scene": "s3"})["scenes"][1]["id"], "s6")
        self.assertEqual(ae.apply_edit(moved, {"op": "add_card", "text": "New"})["scenes"][-1]["kind"], "card")
        styled = ae.apply_edit(moved, {"op": "set_style", "scene": "s1", "layer": "t1", "value": "wipe"})
        self.assertEqual(styled["scenes"][1]["text"][0]["style"], "wipe")

    def test_bad_edits_are_refused_with_a_reason(self):
        t = ae.validate_timeline(self.t)
        bad = [{"op": "set_style", "scene": "s1", "layer": "t1", "value": "spin"}, {"op": "set_text", "scene": "nope", "layer": "t1", "text": "x"},
               {"op": "set_text", "scene": "s1", "layer": "t1", "text": "x" * 500}, {"op": "explode"},
               {"op": "set_position", "scene": "s1", "layer": "t1", "value": "left"}]
        for op in bad:
            with self.assertRaises(ae.AdError, msg=op):
                ae.apply_edit(t, op)
        t2 = ae.validate_timeline(self.t)
        t2["scenes"] = t2["scenes"] * 3
        with self.assertRaises(ae.AdError):
            ae.validate_timeline(t2)
        t3 = ae.validate_timeline(self.t)
        t3["scenes"][0]["kind"] = "image"
        t3["scenes"][0]["source"] = None
        with self.assertRaises(ae.AdError):
            ae.validate_timeline(t3)

    def test_text_cannot_inject_ass_or_filter_syntax(self):
        t = ae.apply_edit(ae.validate_timeline(self.t), {"op": "set_text", "scene": "s1", "layer": "t1", "text": "{\\fs500}Hi\\Nthere"})
        self.assertNotIn("{", t["scenes"][0]["text"][0]["text"])
        self.assertNotIn("\\", t["scenes"][0]["text"][0]["text"])
        script = ae.build_ass(t["scenes"][0], 1080, 1920, "#18B26B", "DejaVu Sans")
        self.assertNotIn("\\fs500", script)

    def test_ass_has_one_line_per_layer_and_valid_times(self):
        t = ae.validate_timeline(self.t)
        for style in ae.TEXT_STYLES:
            scene = {"text": [{"id": "t1", "text": "Fixed *today*", "style": style, "position": "center", "start": 0.2, "end": 2.5}]}
            script = ae.build_ass(scene, 1080, 1920, "#18B26B", "DejaVu Sans")
            dialogues = [x for x in script.splitlines() if x.startswith("Dialogue:")]
            self.assertEqual(len(dialogues), 2 if style in ("cta", "lower_third") else 1, style)
            self.assertIn("0:00:00.20,0:00:02.50", dialogues[0])
        self.assertEqual(ae._ass_time(3725.5), "1:02:05.50")
        self.assertEqual(ae._bgr("#18B26B"), "&H6BB218&")
        del t


class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix="ad_engine_"))
        cls.project = cls.root / "proj"
        cls.project.mkdir()
        make_sample_video(cls.project / "clip.mp4")
        make_sample_photo(cls.project / "photo.jpg")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def test_card_ad_renders_to_the_right_size_length_and_has_audio(self):
        t = ae.plan_timeline("Homingo", headline="Leaking pipe? *Fixed today.*", features=["Verified plumbers", "Upfront pricing", "Same-day visit"], cta="Book on the app")
        report = ae.render_timeline(t, self.project, out_name="cards.mp4")
        facts = report["facts"]
        self.assertEqual((facts["width"], facts["height"]), (1080, 1920))
        self.assertAlmostEqual(facts["duration"], 15.0, delta=0.4)
        self.assertTrue(facts["has_audio"])
        self.assertEqual(report["ai_video_scenes"], 0)
        self.assertIn("0 of 5 scenes are AI video", report["honest_label"])
        self.assertFalse(any(s["cache_hit"] for s in report["scenes"]))

    def test_editing_one_scene_rerenders_only_that_scene(self):
        t = ae.plan_timeline("Homingo", features=["Verified plumbers", "Upfront pricing", "Same-day visit"])
        ae.render_timeline(t, self.project, out_name="edit_a.mp4")
        again = ae.render_timeline(t, self.project, out_name="edit_b.mp4")
        self.assertTrue(all(s["cache_hit"] for s in again["scenes"]))
        edited = ae.apply_edit(ae.validate_timeline(t), {"op": "set_text", "scene": "s3", "layer": "t1", "text": "Pros who always show up"})
        report = ae.render_timeline(edited, self.project, out_name="edit_c.mp4")
        self.assertEqual([s["id"] for s in report["scenes"] if not s["cache_hit"]], ["s3"])
        recolored = ae.apply_edit(edited, {"op": "set_brand", "color": "#E4572E"})
        report = ae.render_timeline(recolored, self.project, out_name="edit_d.mp4")
        self.assertTrue(any(not s["cache_hit"] for s in report["scenes"]))

    def test_text_actually_animates_and_appears(self):
        t = ae.plan_timeline("Homingo", headline="Leaking pipe? *Fixed today.*", features=["a", "b", "c"])
        scene = ae.validate_timeline(t)["scenes"][0]
        timeline = ae.validate_timeline({**t, "scenes": [scene]})
        ae.render_timeline(timeline, self.project, out_name="anim.mp4")
        frames = []
        for second in (0.0, 0.4, 1.2):
            out = self.project / f"anim_{second}.png"
            ffmpeg("-ss", str(second), "-i", str(self.project / "anim.mp4"), "-frames:v", "1", str(out))
            frames.append(out.read_bytes())
        self.assertEqual(len(set(frames)), 3, "frames at 0 s, 0.4 s and 1.2 s must differ: the text animates in")

    def test_video_and_photo_scenes_render_and_keep_their_labels(self):
        t = ae.default_timeline("Homingo")
        t["scenes"] = [
            {"id": "v1", "kind": "ai_video", "source": "clip.mp4", "duration": 3, "text": [{"id": "t1", "text": "Fast. Reliable. *Local.*", "style": "wipe", "position": "bottom"}]},
            {"id": "p1", "kind": "image", "source": "photo.jpg", "duration": 2, "text": [{"id": "t1", "text": "Meet Homingo", "style": "brand", "position": "center"}]},
            {"id": "c1", "kind": "card", "source": None, "duration": 2, "text": [{"id": "t1", "text": "Book now", "style": "cta", "position": "center"}]},
        ]
        report = ae.render_timeline(t, self.project, out_name="mixed.mp4")
        self.assertAlmostEqual(report["facts"]["duration"], 7.0, delta=0.4)
        self.assertEqual([s["label"] for s in report["scenes"]], ["AI video", "Your photo (animated)", "Designed text card (no AI video)"])
        self.assertIn("1 of 3 scenes are AI video", report["honest_label"])

    def test_missing_source_is_an_error_not_a_blank_scene(self):
        t = ae.default_timeline("Homingo")
        t["scenes"] = [{"id": "v1", "kind": "ai_video", "source": "gone.mp4", "duration": 2, "text": []}]
        with self.assertRaisesRegex(ae.AdError, "missing"):
            ae.render_timeline(t, self.project, out_name="bad.mp4")

    def test_voice_and_music_mix_to_the_ad_length(self):
        t = ae.plan_timeline("Homingo", features=["a", "b", "c"], voice="en-IN-NeerjaNeural")
        voices = {}
        for scene in ae.validate_timeline(t)["scenes"][:2]:
            path = self.project / f"voice_{scene['id']}.mp3"
            make_tone(path, 1.5)
            voices[scene["id"]] = path
        long_voice = self.project / "voice_long.mp3"
        make_tone(long_voice, 6)
        voices["s3"] = long_voice
        next_line = self.project / "voice_next.mp3"
        make_tone(next_line, 1.0, 550)
        voices["s4"] = next_line   # s3's 6 s line now has only the 3 s before s4's line, so it must be cut with a warning
        music = self.project / "music.mp3"
        make_tone(music, 4, 220)
        report = ae.render_timeline(t, self.project, narration_clips=voices, music_path=music, out_name="audio.mp4")
        self.assertAlmostEqual(report["facts"]["duration"], 15.0, delta=0.4)
        self.assertTrue(report["facts"]["has_audio"])
        self.assertTrue(any("s3" in w and "narration" in w for w in report["warnings"]), report["warnings"])


def make_cutout(path, color=(220, 40, 40)):
    """A product cut-out: a coloured bottle shape on a transparent background."""
    from PIL import Image, ImageDraw
    image = Image.new("RGBA", (400, 700), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle([110, 160, 290, 680], radius=40, fill=color + (255,))
    draw.rectangle([165, 40, 235, 170], fill=(30, 30, 30, 255))
    image.save(path)


class V2TimelineTests(unittest.TestCase):
    def base(self, **kw):
        t = ae.default_timeline("Homingo", platform=kw.pop("platform", "reels"))
        t["scenes"] = kw.pop("scenes", [
            {"id": "s1", "kind": "card", "duration": 4, "narration": "Line one",
             "text": [{"id": "t1", "text": "Leaking pipe?", "style": "kinetic", "position": "top", "start": 0.1, "end": 3.0},
                      {"id": "t2", "text": "Homingo", "style": "lower_third", "position": "bottom", "start": 1.0, "end": None}]},
            {"id": "s2", "kind": "card", "duration": 3, "text": [{"id": "t1", "text": "Book now", "style": "cta", "position": "bottom"}]}])
        t.update(kw)
        return ae.validate_timeline(t)

    def test_platform_sets_aspect_and_old_timelines_still_load(self):
        self.assertEqual(self.base(platform="feed")["aspect"], "4:5")
        self.assertEqual(ae.SIZES[("1080p", "4:5")], (1080, 1350))
        old = ae.validate_timeline({"aspect": "16:9", "resolution": "720p", "scenes": [{"id": "s1", "kind": "card", "text": []}]})
        self.assertEqual(old["platform"], "landscape")
        with self.assertRaises(ae.AdError):
            ae.validate_timeline({**self.base(), "platform": "myspace"})

    def test_text_stays_inside_the_platform_safe_zone(self):
        for platform in ae.PLATFORMS:
            aspect = ae.PLATFORMS[platform]["aspect"]
            w, h = ae.SIZES[("1080p", aspect)]
            left, top, right, bottom = ae.safe_area(platform, w, h)
            for position in ae.POSITIONS:
                self.assertTrue(top < ae.text_y(position, (left, top, right, bottom)) < bottom, (platform, position))
        self.assertEqual(ae.safe_area("reels", 1080, 1920), (65, 269, 1015, 1248))

    def test_elements_at_reports_what_is_on_screen(self):
        t = self.base()
        at = ae.elements_at(t, 2.0)
        self.assertEqual((at["scene"], at["local_t"], at["visible_text"]), ("s1", 2.0, ["t1", "t2"]))
        self.assertEqual(at["scene_id"], "s1")
        self.assertIn("visual_layer", at)
        self.assertEqual(at["visual_layer"]["safety_badge"], "Designed Card Layer")
        self.assertEqual(ae.elements_at(t, 3.5)["visible_text"], ["t2"])
        later = ae.elements_at(t, 5.0)
        self.assertEqual((later["scene"], later["scene_start"], later["local_t"]), ("s2", 4.0, 1.0))
        self.assertEqual(ae.elements_at(t, 99)["scene"], "s2")

    def test_split_scene_keeps_timing_text_and_voice(self):
        t = ae.apply_edit(self.base(), {"op": "split_scene", "scene": "s1", "at": 1.5})
        first, second = t["scenes"][0], t["scenes"][1]
        self.assertEqual((first["duration"], second["duration"]), (1.5, 2.5))
        self.assertEqual(ae.total_duration(t), 7.0)
        self.assertEqual([x["id"] for x in first["text"]], ["t1", "t2"])
        self.assertEqual(first["text"][0]["end"], 1.5)
        self.assertEqual([(x["id"], x["start"], x["end"]) for x in second["text"]], [("t1", 0.0, 1.5), ("t2", 0.0, 2.5)])
        self.assertEqual((first["narration"], second["narration"], second["trim_start"]), ("Line one", "", 1.5))
        for bad in (0.2, 3.8):
            with self.assertRaises(ae.AdError):
                ae.apply_edit(self.base(), {"op": "split_scene", "scene": "s1", "at": bad})

    def test_colour_size_and_new_ops(self):
        t = ae.apply_edit(self.base(), {"op": "set_color", "scene": "s1", "layer": "t1", "value": "#FFD84D"})
        t = ae.apply_edit(t, {"op": "set_size", "scene": "s1", "layer": "t1", "value": "xl"})
        self.assertEqual((t["scenes"][0]["text"][0]["color"], t["scenes"][0]["text"][0]["size"]), ("#FFD84D", "xl"))
        script = ae.build_ass(t["scenes"][0], 1080, 1920, "#18B26B", "DejaVu Sans")
        self.assertIn("&H4DD8FF&", script)
        self.assertEqual(ae.apply_edit(t, {"op": "set_color", "scene": "s1", "layer": "t1", "value": None})["scenes"][0]["text"][0]["color"], None)
        for op in ({"op": "set_color", "scene": "s1", "layer": "t1", "value": "yellow"}, {"op": "set_size", "scene": "s1", "layer": "t1", "value": "huge"},
                   {"op": "set_platform", "value": "myspace"}, {"op": "delete_scene", "scene": "s1"} if False else {"op": "nope"}):
            with self.assertRaises(ae.AdError):
                ae.apply_edit(t, op)
        self.assertEqual(ae.apply_edit(t, {"op": "set_platform", "value": "shorts"})["platform"], "shorts")
        added = ae.apply_edit(t, {"op": "add_text", "scene": "s2", "text": "Free delivery", "start": 1.0, "color": "#FFFFFF"})
        self.assertEqual(added["scenes"][1]["text"][-1]["start"], 1.0)
        carded = ae.apply_edit(t, {"op": "add_card", "text": "Sale", "index": 1})
        self.assertEqual(carded["scenes"][1]["kind"], "card")

    def test_hindi_text_uses_a_devanagari_font(self):
        scene = {"duration": 3, "text": [{"id": "t1", "text": "आज ही ऑर्डर करें", "style": "kinetic", "position": "top", "start": 0.1, "end": 3}]}
        script = ae.build_ass(scene, 1080, 1920, "#18B26B", "Arial", hindi_font="Nirmala UI")
        self.assertIn("\\fnNirmala UI", script)
        english = ae.build_ass({"duration": 3, "text": [{"id": "t1", "text": "Order today", "style": "kinetic", "position": "top", "start": 0.1, "end": 3}]},
                               1080, 1920, "#18B26B", "Arial", hindi_font="Nirmala UI")
        self.assertNotIn("\\fn", english)

    def test_lint_flags_missing_hook_brand_and_cta(self):
        t = self.base()
        self.assertEqual(ae.lint(t), [])
        bad = self.base(scenes=[{"id": "s1", "kind": "product", "product": "cut.png", "duration": 4,
                                 "text": [{"id": "t1", "text": "Fresh every day", "style": "slide", "position": "center", "start": 1.0}]}])
        warnings = " | ".join(ae.lint(bad))
        for expected in ("Hook", "brand name", "call to action", "covers the product", "6 to 60 seconds"):
            self.assertIn(expected, warnings)


class V2RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix="ad_engine_v2_"))
        cls.project = cls.root / "proj"
        cls.project.mkdir()
        make_cutout(cls.project / "cut.png")
        make_sample_photo(cls.project / "bg.jpg")
        make_cutout(cls.project / "logo.png", color=(20, 120, 220))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def test_product_ai_image_logo_and_feed_size(self):
        t = ae.default_timeline("Homingo", platform="feed", resolution="720p")
        t["brand"]["logo"] = "logo.png"
        t["scenes"] = [
            {"id": "p1", "kind": "product", "product": "cut.png", "source": "bg.jpg", "duration": 2,
             "text": [{"id": "t1", "text": "Homingo *Honey*", "style": "kinetic", "position": "top", "start": 0.1}]},
            {"id": "p2", "kind": "product", "product": "cut.png", "duration": 2, "text": []},
            {"id": "a1", "kind": "ai_image", "source": "bg.jpg", "duration": 2,
             "text": [{"id": "t1", "text": "Order now", "style": "cta", "position": "bottom", "start": 0.3}]},
        ]
        report = ae.render_timeline(t, self.project, out_name="v2.mp4")
        self.assertEqual((report["facts"]["width"], report["facts"]["height"]), (720, 900))
        self.assertAlmostEqual(report["facts"]["duration"], 6.0, delta=0.3)
        self.assertEqual([s["label"] for s in report["scenes"]], ["Your real product on an AI background", "Your real product on a designed background", "AI image (animated)"])
        self.assertIn("2 use AI images", report["honest_label"])
        self.assertFalse((self.project / "render_cache" / "joined.mp4").exists(), "intermediate files are removed after the mux")
        # The product layer moves against the background (parallax): frames differ, and the red product is in the middle of the frame.
        frames = []
        for second in (0.2, 1.6):
            out = self.project / f"p_{second}.png"
            ffmpeg("-ss", str(second), "-i", str(self.project / "v2.mp4"), "-frames:v", "1", str(out))
            frames.append(out)
        from PIL import Image
        with Image.open(frames[0]) as a, Image.open(frames[1]) as b:
            self.assertNotEqual(a.tobytes(), b.tobytes())
            r, g, bl = a.convert("RGB").getpixel((360, 470))
            self.assertTrue(r > 150 and g < 90 and bl < 90, (r, g, bl))
        # Editing the logo re-renders only the last scene.
        make_cutout(self.project / "logo.png", color=(240, 200, 20))
        again = ae.render_timeline(t, self.project, out_name="v2b.mp4")
        self.assertEqual([s["id"] for s in again["scenes"] if not s["cache_hit"]], ["a1"])

    def test_split_keeps_one_continuous_voice_line(self):
        t = ae.default_timeline("Homingo", resolution="720p")
        t["scenes"] = [{"id": "s1", "kind": "card", "duration": 4, "narration": "Long line", "text": [{"id": "t1", "text": "Homingo", "style": "brand", "position": "top"}]},
                       {"id": "s2", "kind": "card", "duration": 2, "narration": "Second", "text": []}]
        t = ae.apply_edit(ae.validate_timeline(t), {"op": "split_scene", "scene": "s1", "at": 2})
        voice = self.project / "line.mp3"
        make_tone(voice, 3.5)
        second = self.project / "second.mp3"
        make_tone(second, 1.5, 660)
        report = ae.render_timeline(t, self.project, narration_clips={"s1": voice, "s2": second}, out_name="split.mp4")
        self.assertEqual(report["warnings"], [], "a 3.5 s line fits in the 4 s before the next line, even after the split")
        self.assertAlmostEqual(report["facts"]["duration"], 6.0, delta=0.3)

    def test_sweep_cache_only_when_disk_is_short(self):
        clip = self.project / "render_cache" / "old_clip.mp4"
        clip.parent.mkdir(exist_ok=True)
        clip.write_bytes(b"x")
        import os, time
        old = time.time() - 3 * 86400
        os.utime(clip, (old, old))
        self.assertEqual(ae.sweep_cache(self.root, min_free_gb=0.0, disk_path=str(self.root)), 0)
        self.assertEqual(ae.sweep_cache(self.root, min_free_gb=10 ** 9, disk_path=str(self.root)), 1)
        self.assertFalse(clip.exists())


if __name__ == "__main__":
    unittest.main()
