"""The guards that keep paid fal.ai calls from wasting money. No network: the transport is faked."""
import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fal_contract  # noqa: E402
import fal_media  # noqa: E402
import media_providers as mp  # noqa: E402
from fal_media import FalMediaError, FalPending  # noqa: E402


def jpeg():
    from PIL import Image
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), (200, 100, 40)).save(buffer, "JPEG")
    return buffer.getvalue()


RESULT = {"images": [{"url": "https://v3.fal.media/files/x/out.jpg"}]}


class Guard(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="fal_state_"))
        self.saved = {k: os.environ.pop(k, None) for k in ("FAL_DRY_RUN", "FAL_BUDGET_USD", "AD_IMAGE_RESOLUTION")}
        self.sent, self.downloads = [], []

    def tearDown(self):
        for k, v in self.saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v
        shutil.rmtree(self.dir, ignore_errors=True)

    def providers(self, submit=None, download=None, budget=5.0):
        def fake_submit(key, model, payload, timeout):
            self.sent.append((model, payload))
            return RESULT

        def fake_download(url):
            self.downloads.append(url)
            return jpeg()

        return mp.MediaProviders(lambda: "key", submit=submit or fake_submit, download=download or fake_download,
                                 state_dir=self.dir, budget_usd=budget)

    def test_the_same_request_twice_is_paid_once(self):
        p = self.providers()
        p.text_to_image("A kitchen counter at dawn", "9:16")
        p.text_to_image("A kitchen counter at dawn", "9:16")
        self.assertEqual(len(self.sent), 1)
        self.assertEqual(len(self.downloads), 1, "the file comes from the cache too")
        self.assertAlmostEqual(p.ledger.spent(), 0.04)
        p.text_to_image("A kitchen counter at dawn", "9:16", fresh=True)   # regenerate asks for a new picture
        self.assertEqual(len(self.sent), 2)

    def test_the_budget_stops_calls_before_they_are_sent(self):
        p = self.providers(budget=0.05)
        p.text_to_image("one", "9:16")
        with self.assertRaises(mp.BudgetReached):
            p.text_to_image("two", "9:16")
        self.assertEqual(len(self.sent), 1)
        self.assertTrue(mp._fatal(mp.BudgetReached("budget")))

    def test_the_budget_counts_across_restarts(self):
        self.providers(budget=0.05).text_to_image("one", "9:16")
        with self.assertRaises(mp.BudgetReached):
            self.providers(budget=0.05).text_to_image("two", "9:16")

    def test_a_refused_request_is_not_counted(self):
        def refuse(key, model, payload, timeout):
            self.sent.append(model)
            raise FalMediaError("fal.ai returned HTTP 404: not found")
        p = self.providers(submit=refuse)
        with self.assertRaises(FalMediaError):
            p.text_to_image("x", "9:16")
        self.assertEqual(p.ledger.spent(), 0.0)
        self.assertEqual(len(self.sent), 1, "a 404 is not retried")

    def test_a_failed_download_is_retried_without_paying_again(self):
        attempts = []

        def flaky(url):
            attempts.append(url)
            if len(attempts) < 3:
                raise FalMediaError("Could not download generated media from fal.ai")
            return jpeg()

        mp.time.sleep, real_sleep = (lambda s: None), mp.time.sleep
        try:
            p = self.providers(download=flaky)
            p.text_to_image("x", "9:16")
        finally:
            mp.time.sleep = real_sleep
        self.assertEqual((len(self.sent), len(attempts)), (1, 3))

    def test_a_timed_out_job_is_collected_later_not_paid_again(self):
        submits, collects = [], []

        def tracked_submit(key, model, payload, timeout, on_submit=None):
            submits.append(model)
            on_submit("req-1", "https://queue.fal.run/x/requests/req-1/status", "https://queue.fal.run/x/requests/req-1")
            raise FalPending("still working", "https://queue.fal.run/x/requests/req-1/status", "https://queue.fal.run/x/requests/req-1")

        def fake_collect(key, status_url, response_url, timeout):
            collects.append(response_url)
            return RESULT

        p = self.providers(submit=tracked_submit)
        p.tracked = True
        with self.assertRaises(FalPending):
            p.text_to_image("slow picture", "9:16")
        self.assertAlmostEqual(p.ledger.spent(), 0.04, msg="an accepted job counts as spent")
        real = fal_media.collect
        fal_media.collect = fake_collect
        try:
            image = p.text_to_image("slow picture", "9:16")
        finally:
            fal_media.collect = real
        self.assertTrue(image.startswith(b"\xff\xd8"))
        self.assertEqual((len(submits), len(collects)), (1, 1), "collected, not submitted again")
        self.assertAlmostEqual(p.ledger.spent(), 0.04)

    def test_big_photos_are_shrunk_before_upload(self):
        from PIL import Image
        buffer = io.BytesIO()
        Image.new("RGB", (4000, 3000), (10, 20, 30)).save(buffer, "JPEG")
        small = mp._shrink(buffer.getvalue(), 1536)
        with Image.open(io.BytesIO(small)) as image:
            self.assertEqual(max(image.size), 1536)


class DryRun(unittest.TestCase):
    def setUp(self):
        self.saved = os.environ.get("FAL_DRY_RUN")
        os.environ["FAL_DRY_RUN"] = "1"

    def tearDown(self):
        os.environ.pop("FAL_DRY_RUN", None)
        if self.saved is not None:
            os.environ["FAL_DRY_RUN"] = self.saved

    def test_dry_run_sends_nothing_and_returns_placeholders(self):
        def never(*args, **kwargs):
            raise AssertionError("dry run must not send anything")
        p = mp.MediaProviders(lambda: "", submit=never, download=never)
        image = p.text_to_image("A kitchen counter at dawn", "9:16")
        self.assertTrue(image.startswith(b"\xff\xd8"))
        cut = p.remove_background(jpeg())
        self.assertTrue(cut.startswith(b"\x89PNG"))
        clip = p.image_to_video(image, "slow push in", 3)
        self.assertIn(b"ftyp", clip[:32])
        self.assertEqual(p.ledger.spent(), 0.0)
        self.assertEqual({e["status"] for e in p.ledger.entries()}, {"dry_run"})

    def test_dry_run_rejects_a_payload_the_model_would_refuse(self):
        p = mp.MediaProviders(lambda: "", submit=None, download=None)
        with self.assertRaises(FalMediaError) as caught:
            p._call("google/nano-banana-2.1", {"prompt": "x", "aspect_ratio": "7:3"}, {"prompt": "x", "aspect_ratio": "7:3"})
        self.assertIn("422", str(caught.exception))


class Contract(unittest.TestCase):
    def test_every_call_matches_fals_published_schema(self):
        problems = []
        for label, endpoint, payload, parsed in fal_contract.captured_calls():
            issues = fal_contract.validate_input(endpoint, payload) + ([] if parsed == "ok" else [parsed])
            problems += [f"{label} {endpoint}: {x}" for x in issues]
        self.assertEqual(problems, [])

    def test_the_validator_catches_real_mistakes(self):
        self.assertTrue(fal_contract.validate_input("minimax/h3-max/image-to-video", {"prompt": "x", "image_url": "u"}))
        self.assertTrue(fal_contract.validate_input("kling/v4/image-to-video", {"start_image_url": "u", "negative_prompt": "x"}))
        self.assertTrue(fal_contract.validate_input("google/nano-banana-2.1", {"prompt": "x", "num_images": 9}))
        self.assertEqual(fal_contract.validate_input("google/nano-banana-2.1", {"prompt": "a red chair", "aspect_ratio": "9:16"}), [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
