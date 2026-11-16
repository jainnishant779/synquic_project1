import unittest
from unittest.mock import patch

from fal_media import (
    IMAGE_MODEL_ID,
    VIDEO_MODEL_ID,
    FalMediaError,
    _submit_and_wait,
    request_fal_image,
    request_fal_video,
)


class FalMediaTests(unittest.TestCase):
    def test_models_use_hosted_flux_and_real_video_endpoints(self):
        self.assertEqual(IMAGE_MODEL_ID, "fal-ai/flux-pro/v1.1-ultra")
        self.assertEqual(VIDEO_MODEL_ID, "wan/v2.7/image-to-video")

    def test_missing_key_fails_before_network_call(self):
        with patch("fal_media._json_request") as request:
            with self.assertRaisesRegex(FalMediaError, "FAL_KEY"):
                _submit_and_wait("", IMAGE_MODEL_ID, {})
        request.assert_not_called()

    def test_image_result_downloads_and_validates_jpeg(self):
        with patch("fal_media._submit_and_wait", return_value={"images": [{"url": "https://v3b.fal.media/key.jpg"}]}), patch(
            "fal_media._download_media", return_value=b"\xff\xd8\xffimage"
        ):
            self.assertEqual(request_fal_image("key", {}), b"\xff\xd8\xffimage")

    def test_video_result_downloads_and_validates_mp4(self):
        mp4 = b"\x00\x00\x00\x18ftypisomvideo"
        with patch("fal_media._submit_and_wait", return_value={"video": {"url": "https://v3b.fal.media/key.mp4"}}), patch(
            "fal_media._download_media", return_value=mp4
        ):
            self.assertEqual(request_fal_video("key", {}), mp4)

    def test_rejects_untrusted_output_media_host(self):
        with patch("fal_media._submit_and_wait", return_value={"images": [{"url": "https://example.com/image.jpg"}]}):
            with self.assertRaisesRegex(FalMediaError, "unsupported media URL"):
                request_fal_image("key", {})


if __name__ == "__main__":
    unittest.main()
