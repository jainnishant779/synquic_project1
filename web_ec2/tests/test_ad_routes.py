"""Route tests for the Ad Studio. fal.ai, the AI director and text to speech are fakes; ffmpeg runs for real."""
import base64
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI  # noqa: E402
from fastapi.templating import Jinja2Templates  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import ad_routes  # noqa: E402
from fal_media import FalMediaError  # noqa: E402

APP_DIR = Path(__file__).resolve().parents[1]
MEDIA = {}


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def media(kind):
    """Sample media made once per run."""
    if kind not in MEDIA:
        folder = Path(tempfile.mkdtemp(prefix="ad_media_"))
        if kind == "jpg":
            ffmpeg("-f", "lavfi", "-i", "testsrc2=s=720x1280:d=1", "-frames:v", "1", str(folder / "a.jpg"))
            MEDIA[kind] = (folder / "a.jpg").read_bytes()
        elif kind == "mp4":
            ffmpeg("-f", "lavfi", "-i", "testsrc2=s=720x1280:r=24:d=3", "-pix_fmt", "yuv420p", str(folder / "a.mp4"))
            MEDIA[kind] = (folder / "a.mp4").read_bytes()
        elif kind == "png":
            from PIL import Image, ImageDraw
            image = Image.new("RGBA", (300, 500), (0, 0, 0, 0))
            ImageDraw.Draw(image).rounded_rectangle([60, 80, 240, 480], radius=30, fill=(200, 30, 30, 255))
            buffer = io.BytesIO()
            image.save(buffer, "PNG")
            MEDIA[kind] = buffer.getvalue()
        elif kind == "mp3":
            ffmpeg("-f", "lavfi", "-i", "sine=frequency=330:duration=1.2", str(folder / "a.mp3"))
            MEDIA[kind] = (folder / "a.mp3").read_bytes()
    return MEDIA[kind]


class FakeProviders:
    def __init__(self):
        self.calls, self.fail, self.fatal = [], set(), None

    def settings(self):
        return {"image_model": "fake", "edit_model": "fake", "cutout_model": "fake", "product_shot_model": "fake", "video_model": "wan27",
                "price_image": 0.04, "price_edit": 0.04, "price_cutout": 0.018, "price_product_shot": 0.04, "price_video_per_s": 0.10}

    def video_seconds(self, seconds):
        return int(max(2, min(10, round(seconds))))

    def _go(self, name):
        self.calls.append(name)
        if self.fatal:
            raise FalMediaError(self.fatal)
        if name in self.fail or (name + str(sum(1 for c in self.calls if c == name))) in self.fail:
            raise FalMediaError("fal.ai returned HTTP 500: boom")

    def text_to_image(self, prompt, aspect, fresh=False):
        self._go("image")
        return media("jpg")

    def edit_with_references(self, prompt, images, aspect, fresh=False):
        self._go("edit")
        return media("jpg")

    def remove_background(self, image, fresh=False):
        self._go("cutout")
        return media("png")

    def image_to_video(self, image, prompt, seconds, resolution="720p", fresh=False):
        self._go("video")
        return media("mp4")


class FakeSpeech:
    def __init__(self):
        self.lines, self.fail = [], False

    def synthesize(self, text, language, out_path):
        if self.fail:
            raise RuntimeError("offline")
        self.lines.append((language, text))
        Path(out_path).write_bytes(media("mp3"))
        return "fake"


class Base(unittest.TestCase):
    key = "fake-key"
    env = {}
    llm = None

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ad_routes_"))
        self.saved = {k: os.environ.get(k) for k in ("STUDIO_PASSWORD", "AD_MAX_SPEND_USD", "TTS_PROVIDER")}
        for k in self.saved:
            os.environ.pop(k, None)
        os.environ.update(self.env)
        self.providers, self.speech = FakeProviders(), FakeSpeech()
        hooks = {"get_fal_key": lambda: self.key, "providers": self.providers, "speech": self.speech, "llm": self.llm}
        self.app = FastAPI()
        self.app.include_router(ad_routes.build_router(self.tmp / "media", Jinja2Templates(directory=str(APP_DIR / "templates")), hooks))
        ad_routes.install_basic_auth(self.app)
        self.client = TestClient(self.app)

    def tearDown(self):
        for k, v in self.saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v
        shutil.rmtree(self.tmp, ignore_errors=True)

    def upload(self, data, name="p.png"):
        r = self.client.post("/api/ads/upload-reference", files={"file": (name, io.BytesIO(data), "image/png")})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()["asset_id"]

    def make(self, **extra):
        body = {"prompt": "Ad for StrideX running sneakers, lightweight, breathable", "length_s": 8, "resolution": "720p", "level": "free", "voice": "off"}
        body.update(extra)
        r = self.client.post("/api/ads/create", json=body)
        self.assertEqual(r.status_code, 202, r.text)
        state = self.client.get(f"/api/ads/{r.json()['id']}").json()
        self.assertEqual(state["status"], "done", state)
        return state


class FreeTests(Base):
    def test_one_prompt_makes_a_finished_free_ad(self):
        s = self.make()
        self.assertEqual((s["spent_usd"], s["version"], s["versions"], s["can_undo"]), (0.0, 1, 1, False))
        self.assertEqual(self.providers.calls, [], "the Free level makes no paid call")
        self.assertAlmostEqual(s["report"]["facts"]["duration"], 8.0, delta=0.4)
        self.assertEqual(s["brief"]["brand"], "StrideX")
        self.assertIn("lint", s["report"])
        video = self.client.get(s["video_url"])
        self.assertEqual((video.status_code, video.headers["content-type"]), (200, "video/mp4"))
        self.assertTrue(s["posters"])

    def test_free_level_shows_your_photo_without_a_cut_out(self):
        s = self.make(reference_asset_id=self.upload(media("png")))
        kinds = {sc["kind"] for sc in s["timeline"]["scenes"]}
        self.assertIn("image", kinds)
        self.assertNotIn("product", kinds)
        self.assertEqual(self.providers.calls, [])

    def test_voice_in_the_prompts_language_and_failures_do_not_block(self):
        s = self.make(prompt="Skyline Residency mein 2 aur 3 BHK flats, metro ke paas", voice="auto")
        self.assertTrue(self.speech.lines)
        self.assertTrue(all(lang == "hinglish" for lang, _ in self.speech.lines))
        self.assertTrue(s["report"]["facts"]["has_audio"])
        self.speech.fail = True
        t = s["timeline"]
        t["scenes"][0]["narration"] = "A line the cache has not seen"
        out = self.client.put(f"/api/ads/{s['id']}/timeline", json=t).json()
        self.assertTrue(any("Voice-over is off" in n for n in out["notes"]), out["notes"])

    def test_edit_undo_redo_and_only_changed_scenes_render(self):
        s = self.make()
        pid, t = s["id"], s["timeline"]
        t["scenes"][1]["text"][0]["text"] = "Feather light"
        t["scenes"][1]["text"][0]["color"] = "#FFD84D"
        out = self.client.put(f"/api/ads/{pid}/timeline", json=t).json()
        self.assertEqual((out["version"], out["versions"], out["can_undo"]), (2, 2, True))
        self.assertEqual([x["id"] for x in out["report"]["scenes"] if not x["cache_hit"]], [t["scenes"][1]["id"]])
        back = self.client.post(f"/api/ads/{pid}/undo").json()
        self.assertEqual((back["version"], back["can_redo"]), (1, True))
        self.assertNotEqual(back["timeline"]["scenes"][1]["text"][0]["text"], "Feather light")
        self.assertTrue(all(x["cache_hit"] for x in back["report"]["scenes"]), "undo reuses cached scenes")
        again = self.client.post(f"/api/ads/{pid}/redo").json()
        self.assertEqual(again["timeline"]["scenes"][1]["text"][0]["text"], "Feather light")
        self.assertEqual(self.client.post(f"/api/ads/{pid}/redo").status_code, 422)
        self.client.post(f"/api/ads/{pid}/undo")
        branch = self.client.post(f"/api/ads/{pid}/edit", json={"ops": [{"op": "add_card", "text": "New end"}]}).json()
        self.assertEqual((branch["version"], branch["versions"], branch["can_redo"]), (2, 2, False), "a new edit after undo drops the redo branch")

    def test_instruction_at_a_moment_proposes_then_applies(self):
        s = self.make()
        pid = s["id"]
        proposal = self.client.post(f"/api/ads/{pid}/instruct", json={"at": 0.5, "instruction": "'Fly through runs' likho, peele rang mein"}).json()
        self.assertEqual([o["op"] for o in proposal["ops"]], ["set_text", "set_color"])
        self.assertTrue(proposal["diff"])
        self.assertEqual(self.client.get(f"/api/ads/{pid}").json()["version"], 1, "a proposal changes nothing")
        applied = self.client.post(f"/api/ads/{pid}/edit", json={"ops": proposal["ops"]}).json()
        first = applied["timeline"]["scenes"][0]["text"][0]
        self.assertEqual((first["text"], first["color"]), ("Fly through runs", "#FFD84D"))
        split = self.client.post(f"/api/ads/{pid}/edit", json={"ops": [{"op": "split_scene", "scene": "s1", "at": 0.6}]})
        self.assertIn(split.status_code, (200, 422))
        self.assertEqual(self.client.post(f"/api/ads/{pid}/instruct", json={"at": 0.5, "instruction": "  "}).status_code, 422)

    def test_refused_edits_and_unsafe_files(self):
        s = self.make()
        pid, t = s["id"], s["timeline"]
        for ops in ([{"op": "set_style", "scene": "s1", "layer": "t1", "value": "spin"}], [{"op": "explode"}]):
            r = self.client.post(f"/api/ads/{pid}/edit", json={"ops": ops})
            self.assertEqual(r.status_code, 422)
        for source in ("../../x.mp4", "sub/dir.png", "missing.png"):
            bad = json.loads(json.dumps(t))
            bad["scenes"][0].update(kind="image", source=source)
            self.assertEqual(self.client.put(f"/api/ads/{pid}/timeline", json=bad).status_code, 422, source)
        for name in ("status.json", "timeline.json", "../x/final_v1.mp4", "render_cache/a.mp4", "history/v1.json"):
            self.assertEqual(self.client.get(f"/api/ads/{pid}/file/{name}").status_code, 404, name)
        self.assertEqual(self.client.get("/api/ads/not-an-id").status_code, 404)

    def test_logo_music_and_scene_photo_uploads(self):
        s = self.make()
        pid = s["id"]
        logo = self.client.post(f"/api/ads/{pid}/logo", files={"file": ("l.png", io.BytesIO(media("png")), "image/png")}).json()
        self.assertTrue(logo["timeline"]["brand"]["logo"].startswith("logo_"))
        self.assertEqual([x["id"] for x in logo["report"]["scenes"] if not x["cache_hit"]], [logo["timeline"]["scenes"][-1]["id"]])
        music = self.client.post(f"/api/ads/{pid}/music", files={"file": ("m.mp3", io.BytesIO(media("mp3")), "audio/mpeg")}).json()
        self.assertTrue(music["timeline"]["audio"]["music"].startswith("music_"))
        self.assertTrue(any("right to use it" in n for n in music["notes"]))
        photo = self.client.post(f"/api/ads/{pid}/scenes/s2/photo", files={"file": ("p.jpg", io.BytesIO(media("jpg")), "image/jpeg")}).json()
        self.assertEqual(photo["timeline"]["scenes"][1]["kind"], "image")
        for path, data in ((f"/api/ads/{pid}/logo", b"not an image"), (f"/api/ads/{pid}/music", b"not audio")):
            self.assertEqual(self.client.post(path, files={"file": ("x", io.BytesIO(data), "application/octet-stream")}).status_code, 415)

    def test_bad_requests_and_config(self):
        for extra in ({"platform": "myspace"}, {"length_s": 3}, {"level": "ultra"}, {"voice": "klingon"}, {"reference_asset_id": "ref_nothing"}):
            self.assertEqual(self.client.post("/api/ads/create", json={"prompt": "Ad for X", **extra}).status_code, 422, extra)
        cfg = self.client.get("/api/ads/config").json()
        self.assertEqual(set(cfg["levels"]), {"free", "images", "video"})
        self.assertIn("reels", cfg["platforms"])
        self.assertEqual(self.client.get("/editor").status_code, 200)
        q = self.client.post("/api/ads/estimate", json={"level": "video", "length_s": 15, "has_photo": True}).json()
        self.assertAlmostEqual(q["usd"], 0.018 + 5 * 0.04 + 6 * 0.10, delta=0.006)   # rounded to cents
        self.assertEqual(self.client.post("/api/ads/estimate", json={"level": "free"}).json()["usd"], 0.0)


class PaidTests(Base):
    def test_images_level_with_photo_keeps_the_real_product(self):
        photo = self.upload(media("png"))
        body = {"prompt": "Ad for StrideX running sneakers, lightweight, breathable", "length_s": 8, "resolution": "720p", "level": "images",
                "voice": "off", "reference_asset_id": photo}
        self.assertEqual(self.client.post("/api/ads/create", json=body).status_code, 402)
        self.assertEqual(self.providers.calls, [], "nothing is called before the spend is confirmed")
        s = self.make(level="images", reference_asset_id=photo, confirm_spend=True)
        kinds = [sc["kind"] for sc in s["timeline"]["scenes"]]
        self.assertIn("product", kinds)
        self.assertEqual(self.providers.calls[0], "cutout")
        product = next(sc for sc in s["timeline"]["scenes"] if sc["kind"] == "product")
        self.assertEqual(product["product"], "cutout.png")
        self.assertTrue(product["source"].startswith("bg_"))
        images = sum(1 for c in self.providers.calls if c in ("image", "edit"))
        self.assertAlmostEqual(s["spent_usd"], 0.018 + images * 0.04, places=3)
        self.assertIn("AI images", s["report"]["honest_label"])

    def test_video_level_limits_video_and_a_failed_picture_becomes_a_designed_scene(self):
        self.providers.fail = {"image2"}
        s = self.make(level="video", length_s=12, confirm_spend=True)
        scenes = s["timeline"]["scenes"]
        self.assertLessEqual(sum(1 for sc in scenes if sc["kind"] == "ai_video"), 2)
        self.assertTrue(any("designed scene" in n for n in s["notes"]), s["notes"])
        self.assertLessEqual(s["spent_usd"], s["cap_usd"])

    def test_an_error_that_would_repeat_stops_paid_calls_for_the_ad(self):
        self.providers.fatal = "fal.ai returned HTTP 404: model not found"
        s = self.make(level="images", length_s=15, confirm_spend=True)
        self.assertEqual(len(self.providers.calls), 1, "one refused call, then nothing more is sent")
        self.assertTrue(any("Paid pictures stopped" in n for n in s["notes"]), s["notes"])
        self.assertEqual(s["spent_usd"], 0.0, "a refused request is not charged")
        self.assertTrue(all(sc["kind"] == "card" for sc in s["timeline"]["scenes"]))

    def test_regenerate_asks_first_and_keeps_the_old_picture_on_failure(self):
        s = self.make(level="images", confirm_spend=True)
        pid = s["id"]
        target = next(sc for sc in s["timeline"]["scenes"] if sc["kind"] == "ai_image")
        url = f"/api/ads/{pid}/scenes/{target['id']}/regenerate"
        self.assertEqual(self.client.post(url, json={"kind": "image"}).status_code, 402)
        self.assertEqual(self.client.post(url, json={"kind": "image", "confirm_spend": True, "visual_prompt": "runner at dawn"}).status_code, 202)
        after = self.client.get(f"/api/ads/{pid}").json()
        new = next(sc for sc in after["timeline"]["scenes"] if sc["id"] == target["id"])
        self.assertNotEqual(new["source"], target["source"])
        self.assertEqual(new["visual_prompt"], "runner at dawn")
        self.providers.fail = {"image"}
        self.assertEqual(self.client.post(url, json={"kind": "image", "confirm_spend": True}).status_code, 202)
        kept = self.client.get(f"/api/ads/{pid}").json()
        self.assertIn("old one is kept", kept["message"])
        self.assertEqual(next(sc for sc in kept["timeline"]["scenes"] if sc["id"] == target["id"])["source"], new["source"])


class LockTests(Base):
    env = {"AD_MAX_SPEND_USD": "0.10"}

    def test_cap_proxy_and_missing_key(self):
        body = {"prompt": "Ad for X", "length_s": 15, "level": "images", "confirm_spend": True}
        r = self.client.post("/api/ads/create", json=body)
        self.assertEqual(r.status_code, 422)
        self.assertIn("cap", r.json()["detail"])
        self.assertEqual(self.client.post("/api/ads/create", json=body, headers={"X-Forwarded-For": "203.0.113.9"}).status_code, 403)
        self.key = ""
        self.assertEqual(self.client.post("/api/ads/create", json={**body, "length_s": 6}).status_code, 409)
        self.assertEqual(self.providers.calls, [])


class PasswordTests(Base):
    env = {"STUDIO_PASSWORD": "s3cret-pass"}

    def test_every_route_needs_the_password(self):
        self.assertEqual(self.client.get("/api/ads/config").status_code, 401)
        self.assertEqual(self.client.get("/editor").status_code, 401)
        bad = base64.b64encode(b"studio:nope").decode()
        self.assertEqual(self.client.get("/api/ads/config", headers={"Authorization": f"Basic {bad}"}).status_code, 401)
        good = {"Authorization": "Basic " + base64.b64encode(b"studio:s3cret-pass").decode()}
        self.assertTrue(self.client.get("/api/ads/config", headers=good).json()["protected"])


class DirectorTests(Base):
    def llm(self, messages, max_tokens=0):   # noqa: D401 - a fake LLM bound as a method
        system = messages[0]["content"]
        if "edit operations" in system:
            return json.dumps({"ops": [{"op": "set_text", "scene": "s1", "layer": "t1", "value": "Run lighter"}], "explain": "Changed the hook."})
        return json.dumps({"brand": "StrideX", "product": "sneakers", "language": "en", "color": "#E8572A", "cta": "Shop now",
                           "scenes": [{"purpose": "hook", "duration": 3, "visual": "card", "visual_prompt": "x", "text": [{"text": "Run *lighter*", "style": "kinetic", "position": "top"}], "voice": "Run lighter."},
                                      {"purpose": "cta", "duration": 3, "visual": "card", "visual_prompt": "y", "text": [{"text": "StrideX", "style": "brand", "position": "top"}], "voice": "Shop now."}]})

    def test_ai_director_plan_and_edit(self):
        s = self.make(length_s=6)   # Base.setUp passes self.llm, which here is the fake director above
        self.assertEqual((s["brief"]["planner"], s["timeline"]["brand"]["color"]), ("ai", "#E8572A"))
        self.assertEqual(s["timeline"]["scenes"][-1]["text"][-1]["style"], "cta", "the missing call to action is added in Python")
        r = self.client.post(f"/api/ads/{s['id']}/instruct", json={"at": 1.0, "instruction": "make the hook say run lighter"}).json()
        self.assertEqual((r["planner"], r["ops"][0]["value"]), ("ai", "Run lighter"))


if __name__ == "__main__":
    unittest.main()
