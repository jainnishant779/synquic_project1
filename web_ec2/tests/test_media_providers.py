"""Tests for the paid media adapters with a fake transport: payload shape per model, field-error retry, speech fallback."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import media_providers as mp  # noqa: E402
from fal_media import FalMediaError  # noqa: E402

JPEG = b"\xff\xd8\xff" + b"0" * 20
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 20
MP4 = b"\x00\x00\x00\x18ftypisom" + b"0" * 20


class Transport:
    def __init__(self, reject_field=None):
        self.calls, self.reject_field = [], reject_field

    def submit(self, key, model, payload, timeout):
        self.calls.append((model, dict(payload)))
        if self.reject_field and self.reject_field in payload:
            raise FalMediaError(f"fal.ai returned HTTP 422: {self.reject_field} must be one of the allowed values")
        if "video" in model:
            return {"video": {"url": "https://v3.fal.media/x.mp4"}}
        return {"images": [{"url": "https://v3.fal.media/x.png" if "background" in model else "https://v3.fal.media/x.jpg"}]}

    def download(self, url):
        return MP4 if url.endswith(".mp4") else PNG if url.endswith(".png") else JPEG


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.saved = {k: os.environ.get(k) for k in ("AD_VIDEO_MODEL", "AD_PRICE_VIDEO_PER_S_USD")}

    def tearDown(self):
        for k, v in self.saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v

    def make(self, transport, key="k"):
        return mp.MediaProviders(lambda: key, submit=transport.submit, download=transport.download)

    def test_each_video_model_gets_its_own_field_names_and_duration_type(self):
        expected = {"wan27": ("image_url", 5), "kling4": ("start_image_url", 5), "minimax_h3": ("image_url", 5.0), "seedance25": ("image_url", "5"),
                    "omni_flash": ("image_url", 5), "heygen_video1": ("image_url", 5)}
        for name, (field, duration) in expected.items():
            os.environ["AD_VIDEO_MODEL"] = name
            transport = Transport()
            self.assertEqual(self.make(transport).image_to_video(JPEG, "slow push-in", 5), MP4)
            model, payload = transport.calls[-1]
            self.assertEqual(model, mp.VIDEO_MODELS[name]["endpoint"])
            self.assertIn(field, payload)
            self.assertEqual(payload["duration"], duration)
            self.assertIs(type(payload["duration"]), type(duration), name)
        os.environ["AD_VIDEO_MODEL"] = "kling4"
        self.assertEqual(mp.MediaProviders.settings()["price_video_per_s"], 0.157)
        os.environ["AD_VIDEO_MODEL"] = "made-up"
        self.assertEqual(mp.MediaProviders.settings()["video_model"], "wan27")

    def test_a_rejected_field_is_retried_with_essentials_only(self):
        transport = Transport(reject_field="aspect_ratio")
        self.assertEqual(self.make(transport).text_to_image("a jar of honey", "9:16"), JPEG)
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(transport.calls[1][1], {"prompt": "a jar of honey"})
        auth = Transport(reject_field="prompt")
        with self.assertRaises(FalMediaError):
            self.make(auth).text_to_image("x", "9:16")
        with self.assertRaisesRegex(FalMediaError, "FAL_KEY"):
            self.make(Transport(), key="").text_to_image("x", "9:16")

    def test_cut_out_must_be_a_png_and_references_are_sent_as_data(self):
        transport = Transport()
        provider = self.make(transport)
        os.environ.pop("AD_VIDEO_MODEL", None)
        self.assertEqual(provider.remove_background(JPEG), PNG)
        flat = mp.MediaProviders(lambda: "k", submit=transport.submit, download=lambda url: JPEG)
        with self.assertRaisesRegex(FalMediaError, "PNG"):
            flat.remove_background(JPEG)   # a cut-out without transparency is refused
        provider.edit_with_references("on a table", [PNG, JPEG], "1:1")
        payload = transport.calls[-1][1]
        self.assertTrue(payload["image_urls"][0].startswith("data:image/png;base64,"))
        self.assertTrue(payload["image_urls"][1].startswith("data:image/jpeg;base64,"))


class SpeechTests(unittest.TestCase):
    def setUp(self):
        self.saved = {k: os.environ.get(k) for k in ("TTS_PROVIDER", "GOOGLE_TTS_API_KEY")}
        self.out = Path(tempfile.mkdtemp()) / "v.mp3"

    def tearDown(self):
        for k, v in self.saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v

    def test_google_payload_and_fallback_to_edge(self):
        import base64
        import json
        posts, edges = [], []

        def post(url, payload, headers):
            posts.append((url, payload))
            return json.dumps({"audioContent": base64.b64encode(b"ID3audio").decode()}).encode()

        speech = mp.Speech(post=post, edge=lambda text, voice, out: edges.append(voice))
        os.environ.update(TTS_PROVIDER="google", GOOGLE_TTS_API_KEY="g")
        self.assertEqual(speech.synthesize("नमस्ते", "hi", self.out), "google")
        self.assertEqual(posts[0][1]["voice"]["languageCode"], "hi-IN")
        self.assertEqual(self.out.read_bytes(), b"ID3audio")
        os.environ.pop("GOOGLE_TTS_API_KEY")
        used = speech.synthesize("Hello", "hinglish", self.out)
        self.assertTrue(used.startswith("edge (fallback"))
        self.assertEqual(edges, ["en-IN-NeerjaNeural"])
        os.environ["TTS_PROVIDER"] = "edge"
        self.assertEqual(speech.synthesize("नमस्ते", "hi", self.out), "edge")
        self.assertEqual(edges[-1], "hi-IN-SwaraNeural")


if __name__ == "__main__":
    unittest.main()
