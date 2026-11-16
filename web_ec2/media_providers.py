"""Paid media calls behind one interface: images, product cut-out, product shot, image-to-video and text to speech.

Image and video calls go through fal.ai's queue (fal_media helpers). Speech goes to Google Cloud Text-to-Speech or ElevenLabs,
with edge-tts as the free fallback for testing. Model ids and prices come from environment variables, so a model can change
without a code change. The request fields come from each model's fal page (research/briefs/R14.md); none was test-called live,
so a field the vendor rejects triggers one retry with only the essential fields.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import fal_media
from fal_media import FalMediaError, FalPending, _download_media, _submit_and_wait


def _env(name, default):
    return os.environ.get(name, default)


def _price(name, default):
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


# Image-to-video models: endpoint, image field, duration type and range, extra fields, list price per second [ESTIMATE].
# Fields are checked against fal's published schemas (fal_schemas/, `python fal_contract.py check`): only Wan takes a
# negative prompt, and Minimax requires prompt_expansion_mode, so it is part of its essential fields.
VIDEO_MODELS = {
    "wan27": {"endpoint": "fal-ai/wan/v2.7/image-to-video", "image_field": "image_url", "duration": int, "range": (2, 10), "price": 0.10, "price_1080": 0.15,
              "extra": {"enable_prompt_expansion": True, "enable_safety_checker": True}, "resolution": True, "negative": True},
    "kling4": {"endpoint": "kling/v4/image-to-video", "image_field": "start_image_url", "duration": int, "range": (3, 30), "price": 0.157,
               "extra": {"resolution": "720p"}},
    "minimax_h3": {"endpoint": "minimax/h3-max/image-to-video", "image_field": "image_url", "duration": float, "range": (1, 15), "price": 0.08,
                   "extra": {"resolution": "768P"}, "required": {"prompt_expansion_mode": "balanced"}},
    "seedance25": {"endpoint": "bytedance/seedance-2.5/us/image-to-video", "image_field": "image_url", "duration": str, "range": (4, 30), "price": 0.22,
                   "extra": {"resolution": "480p", "generate_audio": False}},
    "omni_flash": {"endpoint": "google/gemini-omni-flash/image-to-video", "image_field": "image_url", "duration": int, "range": (3, 10), "price": 0.125,
                   "extra": {}},
    "heygen_video1": {"endpoint": "heygen/heygen-video/image-to-video", "image_field": "image_url", "duration": int, "range": (5, 15), "price": 0.03,
                      "extra": {"resolution": "768p"}},
}
NEGATIVE = "static image, frozen subject, flicker, morphing, duplicate objects, abrupt cuts, broken geometry, unreadable text, logos, watermark"


def _data_uri(data: bytes):
    mime = "image/png" if data.startswith(b"\x89PNG") else "image/webp" if data[:4] == b"RIFF" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def _find_url(result, suffixes=()):
    found = []

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "url" and isinstance(value, str):
                    found.append(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(result)
    if suffixes:
        for url in found:
            if url.lower().split("?")[0].endswith(suffixes):
                return url
    if not found:
        raise FalMediaError("fal.ai returned no file")
    return found[0]


def _is_image(data):
    return data.startswith(b"\xff\xd8\xff") or data.startswith(b"\x89PNG") or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")


def dry_run():
    """FAL_DRY_RUN=1: no request leaves the machine. Payloads are checked against fal's schemas and placeholders come back."""
    return os.environ.get("FAL_DRY_RUN", "").strip().lower() in ("1", "true", "yes")


def request_hash(model, payload):
    return hashlib.sha256(json.dumps([model, payload], sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:32]


class BudgetReached(FalMediaError):
    pass


class SpendLedger:
    """Every paid fal request, one JSON line each, so that:
    - the total stays under FAL_BUDGET_USD across all ads (default $5; raise it on purpose),
    - a job that was accepted but timed out is collected later instead of being paid for again,
    - the real spend can be compared with fal's bill.
    Statuses: submitted, completed, pending (accepted, not collected yet), failed (fal accepted it, then failed),
    rejected (refused before running, not charged), dry_run (never sent). Without a folder the ledger lives in memory (tests)."""

    CHARGED = ("submitted", "completed", "pending", "failed")

    def __init__(self, folder=None, budget_usd=None):
        self.path = Path(folder) / "ledger.jsonl" if folder else None
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.memory = []
        self.lock = threading.Lock()
        self.budget = budget_usd if budget_usd is not None else _price("FAL_BUDGET_USD", 5.0)

    def entries(self):
        if not self.path:
            return list(self.memory)
        try:
            return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except (OSError, ValueError):
            return []

    def latest(self):
        """The last state of every request, by its id."""
        state = {}
        for entry in self.entries():
            state[entry["id"]] = {**state.get(entry["id"], {}), **entry}
        return state

    def spent(self):
        return round(sum(e.get("usd", 0.0) for e in self.latest().values() if e.get("status") in self.CHARGED), 4)

    def pending_for(self, key):
        found = [e for e in self.latest().values() if e.get("hash") == key and e.get("status") == "pending" and e.get("response_url")]
        return found[-1] if found else None

    def write(self, entry):
        entry = {"ts": round(time.time(), 1), **entry}
        with self.lock:
            if self.path:
                with self.path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
            else:
                self.memory.append(entry)

    def reserve(self, usd):
        if self.spent() + usd > self.budget + 1e-9:
            raise BudgetReached(f"The fal budget of ${self.budget:.2f} is used up (${self.spent():.2f} spent). "
                                "Raise FAL_BUDGET_USD on purpose to continue.")


class ResultCache:
    """fal results and downloaded files, by request. The same request twice costs nothing the second time."""

    def __init__(self, folder=None):
        self.folder = Path(folder) / "cache" if folder else None
        if self.folder:
            self.folder.mkdir(parents=True, exist_ok=True)

    def get(self, key):
        path = self.folder / f"{key}.json" if self.folder else None
        if path and path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except ValueError:
                return None
        return None

    def put(self, key, result):
        if self.folder:
            (self.folder / f"{key}.json").write_text(json.dumps(result), encoding="utf-8")

    def media(self, url):
        path = self.folder / f"m_{hashlib.sha256(url.encode()).hexdigest()[:32]}" if self.folder else None
        return path.read_bytes() if path and path.is_file() else None

    def keep_media(self, url, data):
        if self.folder:
            (self.folder / f"m_{hashlib.sha256(url.encode()).hexdigest()[:32]}").write_bytes(data)


def _fatal(error):
    """Errors that will repeat on every scene (bad key, wrong model, rejected fields, budget): stop calling for this ad."""
    text = str(error).lower()
    return isinstance(error, BudgetReached) or any(x in text for x in (
        "http 401", "http 403", "http 404", "http 422", "not configured", "validation", "unprocessable", "budget", "insufficient", "balance"))


class MediaProviders:
    """All paid image and video calls. get_key returns the fal key; transport can be replaced in tests.
    state_dir holds the spend ledger and the result cache; without it both live in memory."""

    def __init__(self, get_key, submit=None, download=None, state_dir=None, budget_usd=None):
        self.get_key = get_key
        self.tracked = submit is None   # the real transport reports the request id as soon as fal accepts a job
        self.submit = submit or _submit_and_wait
        self.download_raw = download or _download_media
        self.ledger = SpendLedger(state_dir, budget_usd)
        self.cache = ResultCache(state_dir)
        self.dry = {}   # placeholder files served in dry-run mode, by url

    # ---------------------------------------------------------------- settings
    @staticmethod
    def settings():
        video = _env("AD_VIDEO_MODEL", "wan27")
        if video not in VIDEO_MODELS:
            video = "wan27"
        spec = VIDEO_MODELS[video]
        video_res = _env("AD_VIDEO_RESOLUTION", "720p")   # Wan bills 1080p at 1.5x; the ad is upscaled when rendered
        video_price = spec.get("price_1080", spec["price"]) if (spec.get("resolution") and video_res == "1080p") else spec["price"]
        return {
            "image_model": _env("AD_IMAGE_MODEL", "google/nano-banana-2.1"),
            "edit_model": _env("AD_IMAGE_EDIT_MODEL", "google/nano-banana-2.1/edit"),
            "cutout_model": _env("AD_CUTOUT_MODEL", "fal-ai/bria/background/remove"),
            "product_shot_model": _env("AD_PRODUCT_SHOT_MODEL", "fal-ai/bria/product-shot"),
            "video_model": video,
            "video_resolution": video_res,
            "image_resolution": _env("AD_IMAGE_RESOLUTION", "1K"),
            # fal list prices on 2026-11-16: Nano Banana 2.1 at 1K is $0.040 (text to image) and $0.044 (edit with a photo),
            # 2K is $0.059 / $0.063; Bria cut-out $0.018; product shot $0.04.
            "price_image": _price("AD_PRICE_IMAGE_USD", 0.059 if _env("AD_IMAGE_RESOLUTION", "1K") == "2K" else 0.04),
            "price_edit": _price("AD_PRICE_EDIT_USD", 0.063 if _env("AD_IMAGE_RESOLUTION", "1K") == "2K" else 0.044),
            "price_cutout": _price("AD_PRICE_CUTOUT_USD", 0.018),
            "price_product_shot": _price("AD_PRICE_PRODUCT_SHOT_USD", 0.04),
            "price_video_per_s": _price("AD_PRICE_VIDEO_PER_S_USD", video_price),
            "dry_run": dry_run(),
        }

    def video_seconds(self, seconds):
        spec = VIDEO_MODELS[self.settings()["video_model"]]
        low, high = spec["range"]
        return int(max(low, min(high, round(seconds))))

    def budget(self):
        return {"budget_usd": self.ledger.budget, "spent_usd": self.ledger.spent(), "dry_run": dry_run()}

    # ---------------------------------------------------------------- calls
    def _call(self, model, payload, essentials, timeout=300, usd=0.0, fresh=False, placeholder=None):
        """One paid request with every guard: cache, pending jobs, budget, schema check (dry run), ledger.
        A field the model rejects gets one retry with only the essential fields (rejections are not charged)."""
        try:
            return self._guarded(model, payload, timeout, usd, fresh, placeholder)
        except BudgetReached:
            raise
        except FalMediaError as error:
            text = str(error).lower()
            if payload == essentials or not any(x in text for x in ("422", "validation", "unprocessable", "must be one of", "not a valid", "extra")):
                raise
            return self._guarded(model, essentials, timeout, usd, fresh, placeholder)

    def _guarded(self, model, payload, timeout, usd, fresh, placeholder):
        key = request_hash(model, payload)
        if not fresh:
            cached = self.cache.get(key)
            if cached is not None:
                return cached
        if dry_run():
            return self._dry_call(model, payload, usd, key, placeholder)
        api_key = self.get_key()
        if not api_key:
            raise FalMediaError("FAL_KEY is not configured on the server")
        entry_id = f"{key}-{int(time.time() * 1000)}"
        pending = self.ledger.pending_for(key)
        if pending:   # paid for already: collect it, never submit it again
            try:
                result = fal_media.collect(api_key, pending["status_url"], pending["response_url"], timeout)
            except FalPending:
                raise
            except FalMediaError as error:
                self.ledger.write({"id": pending["id"], "status": "failed", "error": str(error)[:200]})
                raise
            self.ledger.write({"id": pending["id"], "status": "completed"})
            self.cache.put(key, result)
            return result
        self.ledger.reserve(usd)
        base = {"id": entry_id, "hash": key, "model": model, "usd": round(usd, 4)}
        submitted = {}

        def on_submit(request_id, status_url, response_url):
            submitted.update(request_id=request_id, status_url=status_url, response_url=response_url)
            self.ledger.write({**base, "status": "submitted", **submitted})

        try:
            result = self.submit(api_key, model, payload, timeout, on_submit=on_submit) if self.tracked else self.submit(api_key, model, payload, timeout)
        except FalPending as error:
            self.ledger.write({**base, "status": "pending", "status_url": error.status_url, "response_url": error.response_url})
            raise
        except FalMediaError as error:
            # Refused at submit (no request id): not charged. Accepted and then failed: counted, to stay on the safe side.
            accepted = bool(submitted) or not self.tracked and "generation failed" in str(error).lower()
            self.ledger.write({**base, "status": "failed" if accepted else "rejected", "error": str(error)[:200]})
            raise
        self.ledger.write({**base, "status": "completed"})
        self.cache.put(key, result)   # stored before parsing, so a parsing problem never means paying again
        return result

    def _dry_call(self, model, payload, usd, key, placeholder):
        import fal_contract
        try:
            problems = fal_contract.validate_input(model, payload)
        except FileNotFoundError as error:
            problems = [str(error)]
        if problems:
            self.ledger.write({"id": f"{key}-dry", "hash": key, "model": model, "usd": 0.0, "status": "rejected", "error": problems[0][:200]})
            raise FalMediaError("HTTP 422 (dry run, schema check): " + "; ".join(problems)[:300])
        result = fal_contract.sample_output(model)
        data = placeholder() if placeholder else _placeholder_image("9:16", model)
        ext = ".mp4" if b"ftyp" in data[:32] else ".png" if data.startswith(b"\x89PNG") else ".jpg"
        url = f"https://v3.fal.media/files/dry-run/{key}{ext}"

        def swap(node):
            if isinstance(node, dict):
                return {k: (url if k == "url" else swap(v)) for k, v in node.items()}
            if isinstance(node, list):
                return [swap(v) for v in node]
            return node

        self.dry[url] = data
        self.ledger.write({"id": f"{key}-dry", "hash": key, "model": model, "usd": round(usd, 4), "status": "dry_run"})
        return swap(result)

    def download(self, url):
        """Download a finished file; a failed download is retried, never the paid generation."""
        if url in self.dry:
            return self.dry[url]
        cached = self.cache.media(url)
        if cached:
            return cached
        last = None
        for attempt in range(3):
            try:
                data = self.download_raw(url)
                self.cache.keep_media(url, data)
                return data
            except FalMediaError as error:
                last = error
                if "unsupported media url" in str(error).lower():
                    raise
                time.sleep(2 * (attempt + 1))
        raise last

    def _image_result(self, result):
        data = self.download(_find_url(result, (".png", ".jpg", ".jpeg", ".webp")))
        if not _is_image(data):
            raise FalMediaError("fal.ai did not return an image")
        return data

    def text_to_image(self, prompt, aspect, fresh=False):
        s = self.settings()
        essentials = {"prompt": prompt}
        payload = {**essentials, "num_images": 1, "aspect_ratio": aspect, "output_format": "jpeg", "resolution": s["image_resolution"]}
        return self._image_result(self._call(s["image_model"], payload, essentials, usd=s["price_image"], fresh=fresh,
                                             placeholder=lambda: _placeholder_image(aspect, prompt)))

    def edit_with_references(self, prompt, images, aspect, fresh=False):
        s = self.settings()
        essentials = {"prompt": prompt, "image_urls": [_data_uri(_shrink(x, 1536)) for x in images[:14]]}
        payload = {**essentials, "num_images": 1, "aspect_ratio": aspect, "output_format": "jpeg", "resolution": s["image_resolution"]}
        return self._image_result(self._call(s["edit_model"], payload, essentials, usd=s["price_edit"], fresh=fresh,
                                             placeholder=lambda: _placeholder_image(aspect, prompt, images[0])))

    def remove_background(self, image, fresh=False):
        s = self.settings()
        essentials = {"image_url": _data_uri(_shrink(image, 2048))}
        data = self._image_result(self._call(s["cutout_model"], essentials, essentials, usd=s["price_cutout"], fresh=fresh,
                                             placeholder=lambda: _placeholder_cutout(image)))
        if not data.startswith(b"\x89PNG"):
            raise FalMediaError("The cut-out came back without transparency (not a PNG)")
        return data

    def product_shot(self, cutout_png, scene_description, fresh=False):
        s = self.settings()
        essentials = {"image_url": _data_uri(cutout_png), "scene_description": scene_description}
        return self._image_result(self._call(s["product_shot_model"], {**essentials, "optimize_description": True}, essentials,
                                             usd=s["price_product_shot"], fresh=fresh,
                                             placeholder=lambda: _placeholder_image("1:1", scene_description, cutout_png)))

    def image_to_video(self, image, prompt, seconds, resolution="720p", fresh=False):
        s = self.settings()
        spec = VIDEO_MODELS[s["video_model"]]
        length = self.video_seconds(seconds)
        essentials = {"prompt": prompt, spec["image_field"]: _data_uri(_shrink(image, 1536)), "duration": spec["duration"](length),
                      **spec.get("required", {})}
        payload = {**essentials, **spec["extra"]}
        if spec.get("negative"):
            payload["negative_prompt"] = NEGATIVE
        if spec.get("resolution"):
            payload["resolution"] = s["video_resolution"]
        result = self._call(spec["endpoint"], payload, essentials, timeout=900, usd=length * s["price_video_per_s"], fresh=fresh,
                            placeholder=lambda: _placeholder_video(image, length))
        data = self.download(_find_url(result, (".mp4", ".mov", ".webm")))
        if not (b"ftyp" in data[:32]):
            raise FalMediaError("fal.ai did not return an MP4")
        return data


# ------------------------------------------------------------ dry-run placeholders and input sizes

def _shrink(data, max_side):
    """Smaller upload for big phone photos: the models work at about 1K-2K anyway, and a huge data URI only slows the request."""
    try:
        from PIL import Image
        with Image.open(io.BytesIO(data)) as image:
            if max(image.size) <= max_side:
                return data
            image.thumbnail((max_side, max_side))
            out = io.BytesIO()
            if image.mode in ("RGBA", "LA", "P"):
                image.save(out, "PNG")
            else:
                image.convert("RGB").save(out, "JPEG", quality=92)
            return out.getvalue()
    except Exception:
        return data


def _aspect_size(aspect, long_side=1376):
    w, h = (int(x) for x in aspect.split(":")) if ":" in str(aspect) else (9, 16)
    if h >= w:
        return max(64, int(long_side * w / h)) // 2 * 2, long_side
    return long_side, max(64, int(long_side * h / w)) // 2 * 2


def _placeholder_image(aspect, prompt, reference=None):
    """A clearly fake picture for dry runs: a soft gradient labelled DRY RUN with the start of the prompt."""
    from PIL import Image, ImageDraw
    import textwrap
    w, h = _aspect_size(aspect)
    seed = int(hashlib.sha256(str(prompt).encode()).hexdigest()[:6], 16)
    top = ((seed >> 16) & 255, (seed >> 8) & 255, seed & 255)
    image = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(image)
    for y in range(h):
        k = y / h
        draw.line([(0, y), (w, y)], fill=tuple(int(top[i] * (1 - k) * 0.7 + 40 * k) for i in range(3)))
    if reference:
        try:
            with Image.open(io.BytesIO(reference)) as ref:
                ref = ref.convert("RGBA")
                ref.thumbnail((int(w * 0.6), int(h * 0.4)))
                image.paste(ref, ((w - ref.width) // 2, int(h * 0.45)), ref)
        except Exception:
            pass
    draw.text((24, 24), "DRY RUN - no AI image", fill=(255, 255, 255))
    for i, line in enumerate(textwrap.wrap(str(prompt), 48)[:6]):
        draw.text((24, 48 + 16 * i), line, fill=(230, 230, 230))
    out = io.BytesIO()
    image.save(out, "JPEG", quality=85)
    return out.getvalue()


def _placeholder_cutout(image_bytes):
    """Dry-run cut-out: the user's photo inside a soft oval with a transparent background."""
    from PIL import Image, ImageDraw, ImageFilter
    with Image.open(io.BytesIO(image_bytes)) as photo:
        photo = photo.convert("RGBA")
        photo.thumbnail((1024, 1024))
        mask = Image.new("L", photo.size, 0)
        ImageDraw.Draw(mask).ellipse([photo.width * 0.12, photo.height * 0.06, photo.width * 0.88, photo.height * 0.94], fill=255)
        photo.putalpha(mask.filter(ImageFilter.GaussianBlur(6)))
        out = io.BytesIO()
        photo.save(out, "PNG")
        return out.getvalue()


def _placeholder_video(image_bytes, seconds):
    """Dry-run clip: the still with a slow zoom, made locally with FFmpeg."""
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        still, clip = Path(tmp) / "still.jpg", Path(tmp) / "clip.mp4"
        still.write_bytes(image_bytes)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(still), "-t", str(seconds),
                        "-vf", "scale=720:-2,zoompan=z='min(zoom+0.002,1.2)':d=1:s=720x1280:fps=24", "-pix_fmt", "yuv420p", str(clip)], check=True)
        return clip.read_bytes()


# -------------------------------------------------------------------- speech

EDGE_VOICES = {"en": "en-IN-NeerjaNeural", "hinglish": "en-IN-NeerjaNeural", "hi": "hi-IN-SwaraNeural"}
GOOGLE_LANG = {"en": "en-IN", "hinglish": "en-IN", "hi": "hi-IN"}


class Speech:
    """Voice-over in the ad's language. TTS_PROVIDER picks google, elevenlabs or edge (free, test quality).
    A failure of the chosen provider falls back to edge-tts and says so."""

    def __init__(self, post=None, edge=None):
        self.post = post or self._post
        self.edge = edge or self._edge

    @staticmethod
    def provider():
        name = _env("TTS_PROVIDER", "edge")
        return name if name in ("google", "elevenlabs", "edge") else "edge"

    @staticmethod
    def _post(url, payload, headers, timeout=60):
        request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **headers}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"text to speech returned HTTP {exc.code}") from None
        except (urllib.error.URLError, TimeoutError):
            raise RuntimeError("text to speech request failed") from None

    @staticmethod
    def _edge(text, voice, out_path):
        import asyncio
        import edge_tts

        async def go():
            await edge_tts.Communicate(text, voice, rate="+0%").save(str(out_path))

        asyncio.run(go())

    def synthesize(self, text, language, out_path):
        """Write an MP3 to out_path. Returns the provider actually used."""
        language = language if language in EDGE_VOICES else "en"
        provider = self.provider()
        try:
            if provider == "google":
                key = _env("GOOGLE_TTS_API_KEY", "")
                if not key:
                    raise RuntimeError("GOOGLE_TTS_API_KEY is not set")
                code = GOOGLE_LANG[language]
                voice = _env(f"GOOGLE_TTS_VOICE_{language.upper()}", f"{code}-Chirp3-HD-Aoede")
                body = self.post(f"https://texttospeech.googleapis.com/v1/text:synthesize?key={key}",
                                 {"input": {"text": text}, "voice": {"languageCode": code, "name": voice}, "audioConfig": {"audioEncoding": "MP3"}}, {})
                Path(out_path).write_bytes(base64.b64decode(json.loads(body)["audioContent"]))
                return "google"
            if provider == "elevenlabs":
                key, voice = _env("ELEVENLABS_API_KEY", ""), _env("ELEVENLABS_VOICE_ID", "")
                if not key or not voice:
                    raise RuntimeError("ELEVENLABS_API_KEY or ELEVENLABS_VOICE_ID is not set")
                audio = self.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
                                  {"text": text, "model_id": _env("ELEVENLABS_MODEL", "eleven_multilingual_v2")}, {"xi-api-key": key})
                Path(out_path).write_bytes(audio)
                return "elevenlabs"
        except Exception as error:
            self.edge(text, EDGE_VOICES[language], out_path)
            return f"edge (fallback: {str(error)[:80]})"
        self.edge(text, EDGE_VOICES[language], out_path)
        return "edge"
