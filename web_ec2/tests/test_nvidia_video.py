import base64
import io
import json
import unittest
import urllib.error
from unittest.mock import patch

from nvidia_video import (
    COSMOS3_ENDPOINT,
    NvidiaVideoError,
    build_cosmos_image_payload,
    build_cosmos_payload,
    build_keyframe_prompt,
    build_video_prompt,
    request_cosmos_video,
    request_cosmos_image,
)


class CosmosPayloadTests(unittest.TestCase):
    def test_keyframe_payload_selects_text_to_image_and_shot_aspect(self):
        payload = build_cosmos_image_payload(
            prompt="A premium product photograph.", aspect_ratio="9:16", resolution="480p", seed=43
        )
        self.assertEqual(payload["model_mode"], "text2image")
        self.assertEqual(payload["resolution"], "480_9_16")
        self.assertEqual(payload["seed"], 43)

    def test_keyframe_prompt_requests_single_clean_image_without_text(self):
        prompt = build_keyframe_prompt(
            brief="Premium launch", shot={"visual_prompt": "Device rotates in a studio"},
            product="Example smart device", style="Clean", lighting="Soft light",
        )
        self.assertIn("single coherent frame", prompt)
        self.assertIn("Do not add any text", prompt)

    def test_text_to_video_payload_uses_supported_short_480p_settings(self):
        payload = build_cosmos_payload(
            prompt="A product turns slowly on a studio plinth.",
            aspect_ratio="16:9",
            resolution="480p",
            duration_s=5,
            seed=42,
        )
        self.assertEqual(payload["model_mode"], "text2video")
        self.assertEqual(payload["resolution"], "480_16_9")
        self.assertEqual(payload["num_frames"], 120)
        self.assertEqual(payload["fps"], 24)
        self.assertNotIn("input_reference", payload)

    def test_reference_selects_image_to_video_and_vertical_resolution(self):
        payload = build_cosmos_payload(
            prompt="A product turns slowly on a studio plinth.",
            aspect_ratio="9:16",
            resolution="720p",
            duration_s=5,
            seed=8,
            reference_data_uri="data:image/png;base64,AA==",
        )
        self.assertEqual(payload["model_mode"], "image2video")
        self.assertEqual(payload["resolution"], "720_9_16")
        self.assertEqual(payload["input_reference"], "data:image/png;base64,AA==")

    def test_prompt_keeps_exact_brand_out_of_generated_pixels(self):
        prompt = build_video_prompt(
            brief="A clean premium launch.",
            shot={"visual_prompt": "The device rotates on a plinth."},
            brand="ParkFnB",
            product="ParkFnB parking barrier",
            style="Modern Architectural",
            camera="slow orbit",
            lighting="soft daylight",
        )
        self.assertIn("separate post-render layer adds the exact brand name", prompt)
        self.assertIn("Do not invent packaging, logos, labels", prompt)

    def test_rejects_invalid_api_settings(self):
        with self.assertRaises(ValueError):
            build_cosmos_payload(
                prompt="hello", aspect_ratio="4:3", resolution="1080p", duration_s=5, seed=1
            )

    def test_caps_long_director_text_before_api_payload_validation(self):
        prompt = build_video_prompt(
            brief="launch " * 1000,
            shot={"visual_prompt": "product " * 1000, "camera": "orbit " * 1000},
            brand="Example",
            product="Example coffee maker",
            style="luxury " * 100,
            camera="macro_push",
            lighting="studio_clean",
            features="steam " * 100,
        )
        payload = build_cosmos_payload(
            prompt=prompt, aspect_ratio="16:9", resolution="480p", duration_s=5, seed=42
        )
        self.assertLessEqual(len(prompt.split()), 300)
        self.assertEqual(payload["num_frames"], 120)


class CosmosRequestTests(unittest.TestCase):
    def test_decodes_nvidia_base64_jpeg_response(self):
        image = b"\xff\xd8\xffmock-jpeg"
        response = io.BytesIO(json.dumps({"b64_image": base64.b64encode(image).decode()}).encode())
        response.__enter__ = lambda: response
        response.__exit__ = lambda *_: None
        with patch("urllib.request.urlopen", return_value=response):
            result = request_cosmos_image("test-key", {"model_mode": "text2image"})
        self.assertEqual(result, image)

    def test_decodes_nvidia_base64_video_response(self):
        video = b"mock-mp4"
        response = io.BytesIO(json.dumps({"b64_video": base64.b64encode(video).decode()}).encode())
        response.__enter__ = lambda: response
        response.__exit__ = lambda *_: None
        with patch("urllib.request.urlopen", return_value=response) as urlopen:
            result = request_cosmos_video("test-key", {"model_mode": "text2video"})
        self.assertEqual(result, video)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, COSMOS3_ENDPOINT)
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")

    def test_missing_key_fails_before_network_call(self):
        with patch("urllib.request.urlopen") as urlopen:
            with self.assertRaisesRegex(NvidiaVideoError, "NVIDIA_API_KEY"):
                request_cosmos_video("", {})
        urlopen.assert_not_called()

    def test_rejects_response_without_video(self):
        response = io.BytesIO(b"{}")
        response.__enter__ = lambda: response
        response.__exit__ = lambda *_: None
        with patch("urllib.request.urlopen", return_value=response):
            with self.assertRaisesRegex(NvidiaVideoError, "did not contain b64_video"):
                request_cosmos_video("test-key", {})

    def test_provider_error_is_actionable_and_redacts_api_key(self):
        error = urllib.error.HTTPError(
            COSMOS3_ENDPOINT,
            429,
            "Rate limited",
            {},
            io.BytesIO(b'{"detail":"trial quota exceeded for secret-key"}'),
        )
        with patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaisesRegex(NvidiaVideoError, "trial quota exceeded") as raised:
                request_cosmos_video("secret-key", {})
        self.assertNotIn("secret-key", str(raised.exception))

    def test_timeout_warns_generation_may_still_be_running(self):
        error = urllib.error.URLError(TimeoutError("timed out"))
        with patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaisesRegex(NvidiaVideoError, "may still be processing"):
                request_cosmos_video("test-key", {})


if __name__ == "__main__":
    unittest.main()
