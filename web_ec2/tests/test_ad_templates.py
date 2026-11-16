"""Ad templates: the library format and checker, looks in the engine, planning from a template, saved templates through the routes."""
import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ad_director as ad  # noqa: E402
import ad_engine as ae  # noqa: E402
import ad_templates as at  # noqa: E402
from test_ad_routes import Base, media  # noqa: E402


def library():
    templates, errors = at.load_library()
    return {t["id"]: t for t in templates}, errors


class LibraryTests(unittest.TestCase):
    def test_every_library_template_is_valid_and_varied(self):
        templates, errors = library()
        self.assertEqual(errors, [])
        self.assertGreaterEqual(len(templates), 10)
        self.assertEqual({t["look"]["card"] for t in templates.values()}, set(ae.CARD_STYLES), "every look is used at least once")
        for t in templates.values():
            self.assertTrue(any(s["style"] == "cta" for s in t["scenes"][-1]["text"]), t["id"])

    def test_checker_names_the_broken_field(self):
        good = library()[0]["problem_solution"]
        cases = [
            (lambda t: t["scenes"][-1]["text"].clear(), "cta"),
            (lambda t: t["scenes"][2]["text"][1].update(position="center"), "cover the product"),
            (lambda t: t["scenes"][0]["text"][0].update(start=0.5), "hook"),
            (lambda t: t["scenes"][1]["text"].append(dict(t["scenes"][1]["text"][0])), "same place"),
            (lambda t: t["scenes"][1]["text"][0].update(style="sparkle"), "scenes[1].text[0].style"),
            (lambda t: t["look"].update(card="neon"), "look.card"),
            (lambda t: t.update(id="Bad Id"), "id"),
            (lambda t: t.update(scenes=t["scenes"][:1]), "scenes"),
        ]
        for change, words in cases:
            broken = copy.deepcopy(good)
            change(broken)
            with self.assertRaises(at.TemplateError, msg=words) as caught:
                at.validate_template(broken)
            self.assertIn(words, str(caught.exception))

    def test_a_broken_file_is_reported_not_fatal(self):
        folder = Path(tempfile.mkdtemp(prefix="tpl_lib_"))
        try:
            shutil.copy(at.LIBRARY / "bumper_6s.json", folder / "bumper_6s.json")
            (folder / "broken.json").write_text("{not json", encoding="utf-8")
            (folder / "wrong_name.json").write_text((at.LIBRARY / "launch_new.json").read_text(encoding="utf-8"), encoding="utf-8")
            templates, errors = at.load_library(folder)
            self.assertEqual([t["id"] for t in templates], ["bumper_6s"])
            self.assertEqual(len(errors), 2)
            self.assertTrue(any("must match the file name" in e for e in errors))
        finally:
            shutil.rmtree(folder, ignore_errors=True)


class LookTests(unittest.TestCase):
    def test_look_is_validated_and_editable(self):
        t = ae.default_timeline("Brand")
        t["scenes"] = [{"id": "s1", "kind": "card", "duration": 3, "text": [{"text": "Hi", "style": "cta", "position": "bottom"}]}]
        self.assertEqual(ae.validate_timeline(t)["look"], ae.DEFAULT_LOOK)
        light = ae.apply_edit(t, {"op": "set_look", "card": "light", "text": "#1B1B1F"})
        self.assertEqual(light["look"], {"card": "light", "text": "#1B1B1F", "highlight": ae.HIGHLIGHT})
        with self.assertRaises(ae.AdError):
            ae.apply_edit(t, {"op": "set_look", "card": "neon"})

    def test_old_ads_keep_their_cached_scenes(self):
        t = ae.default_timeline("Brand")
        t["scenes"] = [{"id": "s1", "kind": "card", "duration": 3, "text": []}]
        t = ae.validate_timeline(t)
        old = copy.deepcopy(t)
        old.pop("look")
        folder = Path(tempfile.gettempdir())
        self.assertEqual(ae.scene_hash(t["scenes"][0], t, folder, False), ae.scene_hash(old["scenes"][0], old, folder, False))
        t["look"]["card"] = "dark"
        self.assertNotEqual(ae.scene_hash(t["scenes"][0], t, folder, False), ae.scene_hash(old["scenes"][0], old, folder, False))

    def test_dark_text_on_light_cards_only(self):
        scene = {"id": "s1", "kind": "card", "duration": 3, "text": [{"id": "t1", "text": "Hi *there*", "style": "slide", "position": "center",
                                                                      "color": None, "size": "m", "start": 0.1, "end": 3}]}
        look = {"card": "light", "text": "#1B1B1F", "highlight": "#E4572E"}
        on_card = ae.build_ass(scene, 720, 1280, "#18B26B", "Arial", look=look, on_card=True)
        on_photo = ae.build_ass(scene, 720, 1280, "#18B26B", "Arial", look=look, on_card=False)
        self.assertIn(ae._bgr("#1B1B1F"), on_card)
        self.assertIn(ae._bgr("#E4572E"), on_card)
        self.assertNotIn(ae._bgr("#1B1B1F"), on_photo, "over a photo the text stays white")
        self.assertIn(",0,0,5,", on_card.split("Style: Base,")[1].split("\n")[0], "no outline or shadow on dark text")

    def test_light_brand_colour_on_a_bold_card_gets_dark_text(self):
        look = {"card": "bold", "text": "#FFFFFF", "highlight": "#FFD84D"}
        yellow = ae.card_look(look, "#FFC107")
        self.assertEqual(yellow["text"], "#141414")
        self.assertGreaterEqual(abs(ae._luma(yellow["highlight"]) - ae._luma("#FFC107")), 0.3)
        self.assertEqual(ae.card_look(look, "#2457D6"), look, "a dark brand colour keeps white text")
        self.assertEqual(ae.card_look(dict(look, card="glow"), "#FFC107"), dict(look, card="glow"))

    def test_hindi_brand_lines_keep_their_letters_together(self):
        scene = {"id": "s1", "kind": "card", "duration": 3, "text": [{"id": "t1", "text": "मिठास स्वीट्स", "style": "brand", "position": "top",
                                                                      "color": None, "size": "l", "start": 0.1, "end": 3}]}
        hindi = ae.build_ass(scene, 720, 1280, "#18B26B", "Arial", hindi_font="Lohit Devanagari")
        self.assertNotIn("\\fsp", hindi)
        scene["text"][0]["text"] = "BeePure"
        self.assertIn("\\fsp26", ae.build_ass(scene, 720, 1280, "#18B26B", "Arial"))

    def test_captions_skip_text_cards(self):
        t = ae.default_timeline("Brand")
        t["audio"]["captions"] = True
        card = {"kind": "card", "narration": "Hello there"}
        photo = {"kind": "ai_image", "narration": "Hello there"}
        self.assertEqual((ae.scene_captions(card, t), ae.scene_captions(photo, t)), ("", "Hello there"))

    def test_every_card_style_draws(self):
        from PIL import Image
        folder = Path(tempfile.mkdtemp(prefix="cards_"))
        try:
            colours = set()
            for style in ae.CARD_STYLES:
                ae.make_card_background(folder / f"{style}.jpg", 72, 128, "#2457D6", style)
                with Image.open(folder / f"{style}.jpg") as image:
                    colours.add(image.convert("RGB").resize((1, 1)).getpixel((0, 0)))
            self.assertEqual(len(colours), len(ae.CARD_STYLES), "each style looks different")
        finally:
            shutil.rmtree(folder, ignore_errors=True)


class FakeFill:
    """An LLM that fills the template it is shown: it reads the slot count per scene from the prompt."""
    last_user = ""

    def __init__(self, scenes=None, broken=False):
        self.scenes, self.broken, self.calls = scenes, broken, 0

    def __call__(self, messages, max_tokens=2500):
        self.calls += 1
        if self.broken:
            return "sorry"
        user = messages[1]["content"]
        FakeFill.last_user = user
        counts = [block.count("  line ") for block in user.split("\nScene ")[1:]]
        scenes = self.scenes or [{"lines": [f"Line {chr(65 + i)}{chr(97 + j)} *about* honey and more words than allowed here" for j in range(n)],
                                  "voice": f"Voice {chr(65 + i)}", "visual_prompt": f"Picture {chr(65 + i)}"} for i, n in enumerate(counts)]
        return json.dumps({"brand": "BeePure", "product": "raw honey", "audience": "families", "language": "hinglish", "color": "#D9A21B",
                           "cta": "Order karo", "scenes": scenes})


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.templates = library()[0]

    def test_template_sets_structure_look_and_timing(self):
        template = self.templates["three_reasons"]
        t, brief, notes = ad.plan_ad("BeePure organic honey, kachcha shahad, no sugar", length_s=15, level="free", llm=FakeFill(), template=template)
        self.assertEqual(brief["planner"], "ai")
        self.assertEqual(brief["template"]["id"], "three_reasons")
        self.assertEqual(len(t["scenes"]), len(template["scenes"]))
        self.assertAlmostEqual(ae.total_duration(t), 15, delta=0.05)
        self.assertEqual(t["look"]["card"], "bold")
        self.assertEqual([s["purpose"] for s in t["scenes"]], [s["purpose"] for s in template["scenes"]])
        labels = [layer["text"] for s in t["scenes"][1:4] for layer in s["text"] if layer["size"] == "xl"]
        self.assertEqual(labels, ["1", "2", "3"], "fixed labels are kept exactly")
        reason = t["scenes"][1]["text"][1]
        self.assertTrue(reason["text"].startswith("Line Bb"))
        self.assertLessEqual(len(reason["text"].split()), template["scenes"][1]["text"][1]["max_words"] + 2, "lines are kept short")
        self.assertEqual(reason["text"].count("*") % 2, 0)
        self.assertAlmostEqual(reason["start"], round(0.2 * t["scenes"][1]["duration"], 2), delta=0.01)
        self.assertEqual(t["scenes"][-1]["text"][0]["text"], "BeePure", "brand slots hold the brand name")
        self.assertFalse([n for n in notes if "Check scene" in n], "the template's own labels (1, 2, 3) are not claims")
        self.assertIn("voice at most", FakeFill.last_user)
        ae.validate_timeline(t)

    def test_rules_fill_when_the_llm_fails_or_is_missing(self):
        template = self.templates["how_it_works"]
        for llm in (FakeFill(broken=True), None):
            t, brief, notes = ad.plan_ad("Create an ad for LedgerLite, simple GST billing software for small shops", length_s=20, level="free",
                                         llm=llm, template=template)
            self.assertEqual(brief["planner"], "rules")
            self.assertEqual(len(t["scenes"]), 6)
            self.assertEqual(t["look"]["card"], "light")
            self.assertEqual([l["text"] for l in t["scenes"][2]["text"]][0], "Step 1")
            self.assertTrue(all(layer["text"] for s in t["scenes"] for layer in s["text"]))
            ae.validate_timeline(t)

    def test_missing_scenes_in_the_answer_are_filled_from_rules(self):
        template = self.templates["problem_solution"]
        partial = [{"lines": ["Chipchipa *gel*?", "BeePure"], "voice": "v", "visual_prompt": "p"}, {"lines": ["Din bhar *chamak*"]},
                   {"lines": ["BeePure", "Asli *shahad*"]}]
        t, brief, _ = ad.plan_ad("BeePure organic honey", length_s=15, level="free", llm=FakeFill(scenes=partial), template=template)
        self.assertEqual(brief["planner"], "ai")
        self.assertEqual(len(t["scenes"]), 5)
        self.assertTrue(all(layer["text"] for s in t["scenes"] for layer in s["text"]))
        self.assertEqual(t["scenes"][-1]["text"][-1]["style"], "cta")

    def test_short_lengths_cut_scenes_and_keep_the_end(self):
        template = self.templates["property_tour"]
        t, _, _ = ad.plan_ad("Skyline Residency 2 BHK", length_s=6, level="free", llm=FakeFill(), template=template)
        self.assertLessEqual(len(t["scenes"]), 4)
        self.assertEqual(t["scenes"][-1]["purpose"], "cta")

    def test_a_saved_brand_template_supplies_the_brand(self):
        template = dict(self.templates["bumper_6s"], brand={"name": "Daily Brew", "logo": None})
        t, brief, _ = ad.plan_ad("new cold coffee can, ready in seconds", length_s=6, level="free", llm=None, template=template, brand_hint="Daily Brew")
        self.assertEqual(brief["brand"], "Daily Brew")

    def test_saved_template_round_trip(self):
        t, _, _ = ad.plan_ad("BeePure organic honey ka ad, kachcha shahad", length_s=12, level="free", llm=FakeFill(),
                             template=self.templates["launch_new"])
        t["scenes"][1]["text"][1]["position"] = "top"    # an edit that collides with the brand line
        saved = at.from_timeline(t, "tpl_0123456789", "My style", "", keep_brand=True)
        clean = at.validate_template(saved, saved=True)
        self.assertEqual(len(clean["scenes"]), len(t["scenes"]))
        self.assertEqual(clean["look"]["card"], "bold")
        self.assertEqual(clean["look"]["color"], t["brand"]["color"])
        self.assertEqual(clean["brand"]["name"], "BeePure")
        again, _, _ = ad.plan_ad("Zing mango cola", length_s=12, level="free", llm=None, template=clean)
        ae.validate_timeline(again)

    def test_sample_timeline_renders_for_every_template(self):
        for template in self.templates.values():
            sample = at.sample_timeline(template)
            self.assertEqual(sample["look"]["card"], template["look"]["card"])
            self.assertEqual(ae.lint(sample), [], template["id"])


class RouteTests(Base):
    def test_gallery_lists_library_and_previews_render(self):
        r = self.client.get("/api/ad-templates").json()
        self.assertGreaterEqual(len(r["library"]), 10)
        self.assertEqual((r["saved"], r["errors"]), ([], []))
        preview = self.client.get(r["library"][0]["preview_url"])
        self.assertEqual((preview.status_code, preview.headers["content-type"]), (200, "image/jpeg"))
        self.assertGreater(len(preview.content), 5000)
        self.assertEqual(self.client.get("/api/ad-templates/no_such_tpl").status_code, 422)
        self.assertEqual(self.client.delete("/api/ad-templates/bumper_6s").status_code, 403)

    def test_make_an_ad_from_a_template(self):
        s = self.make(template_id="launch_new", length_s=10)
        self.assertEqual(s["brief"]["template"]["id"], "launch_new")
        self.assertEqual(s["timeline"]["look"]["card"], "bold")
        self.assertEqual(len(s["timeline"]["scenes"]), 4)
        self.assertAlmostEqual(s["report"]["facts"]["duration"], 10, delta=0.4)
        bad = self.client.post("/api/ads/create", json={"prompt": "Ad for X", "level": "free", "template_id": "nope_nope"})
        self.assertEqual(bad.status_code, 422)

    def test_save_an_ad_as_a_brand_template_and_reuse_it(self):
        logo = self.upload(media("png"))
        first = self.make(logo_asset_id=logo, template_id="three_reasons", length_s=12)
        r = self.client.post(f"/api/ads/{first['id']}/save-template", json={"name": "StrideX style", "keep_brand": True})
        self.assertEqual(r.status_code, 200, r.text)
        saved = r.json()
        self.assertEqual((saved["kind"], saved["brand"], saved["has_logo"]), ("saved", "StrideX", True))
        listing = self.client.get("/api/ad-templates").json()
        self.assertEqual([t["id"] for t in listing["saved"]], [saved["id"]])
        self.assertEqual(self.client.get(saved["preview_url"]).status_code, 200)
        second = self.make(prompt="new trail running shoe with a grippy sole", template_id=saved["id"], length_s=12)
        self.assertEqual(second["brief"]["brand"], "StrideX", "the saved brand is used when the prompt names none")
        self.assertTrue(second["timeline"]["brand"]["logo"], "the saved logo comes along")
        self.assertEqual(second["timeline"]["look"]["card"], "bold")
        self.assertEqual(self.client.delete(f"/api/ad-templates/{saved['id']}").json(), {"deleted": saved["id"]})
        self.assertEqual(self.client.get("/api/ad-templates").json()["saved"], [])

    def test_estimate_counts_only_scenes_with_pictures(self):
        plain = self.client.post("/api/ads/estimate", json={"level": "images", "length_s": 20}).json()
        steps = self.client.post("/api/ads/estimate", json={"level": "images", "length_s": 20, "template_id": "how_it_works"}).json()
        self.assertEqual(steps["items"][0]["what"], "2 AI images", "three step cards and the end card need no picture")
        self.assertLess(steps["usd"], plain["usd"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
