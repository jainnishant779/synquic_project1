"""Queued fal.ai image and video inference used by the hosted studio."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request


FAL_QUEUE_BASE = "https://queue.fal.run"
IMAGE_MODEL_ID = "fal-ai/flux-pro/v1.1-ultra"
VIDEO_MODEL_ID = "wan/v2.7/image-to-video"


class FalMediaError(RuntimeError):
    """Sanitized provider error safe to return to the app UI."""


class FalPending(FalMediaError):
    """The job was accepted (and is paid for) but did not finish in time. Keep the URLs and collect it later; never resubmit."""

    def __init__(self, message, status_url, response_url):
        super().__init__(message)
        self.status_url, self.response_url = status_url, response_url


def _json_request(url: str, api_key: str, *, method: str = "GET", payload: dict | None = None, timeout_s: int = 60) -> dict:
    headers = {"Authorization": f"Key {api_key}", "Accept": "application/json"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            error = json.loads(exc.read(4096).decode("utf-8", errors="replace"))
            detail = error.get("detail") or error.get("message") or error.get("error") or ""
            if isinstance(detail, dict):
                detail = detail.get("message") or detail.get("type") or ""
            detail = " ".join(str(detail).split())[:240]
        except (OSError, json.JSONDecodeError, AttributeError):
            detail = ""
        raise FalMediaError(f"fal.ai returned HTTP {exc.code}" + (f": {detail}" if detail else "")) from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError):
        raise FalMediaError("fal.ai request failed or timed out; check provider status before retrying") from None
    if not isinstance(result, dict):
        raise FalMediaError("fal.ai returned an invalid response")
    return result


def _check_queue_url(url):
    parsed = urllib.parse.urlparse(url or "")
    if parsed.scheme != "https" or parsed.hostname != "queue.fal.run":
        raise FalMediaError("fal.ai returned an invalid queue URL")


def collect(api_key: str, status_url: str, result_url: str, timeout_s: int = 300) -> dict:
    """Wait for an accepted job and fetch its result. Polling is free; on timeout FalPending keeps the URLs for later."""
    for candidate in (status_url, result_url):
        _check_queue_url(candidate)
    deadline = time.monotonic() + timeout_s
    while True:
        status = _json_request(status_url, api_key.strip(), timeout_s=30)
        if status.get("status") == "COMPLETED":
            if status.get("error"):
                detail = " ".join(str(status["error"]).split())[:240]
                raise FalMediaError(f"fal.ai generation failed: {detail}")
            return _json_request(result_url, api_key.strip(), timeout_s=60)
        if time.monotonic() >= deadline:
            raise FalPending("fal.ai is still working on this picture; it is paid for and will be collected on the next try, not made again",
                             status_url, result_url)
        time.sleep(4)


def _submit_and_wait(api_key: str, model_id: str, payload: dict, timeout_s: int = 300, on_submit=None) -> dict:
    """Submit one job and wait for it. on_submit(request_id, status_url, response_url) is called as soon as fal accepts the job,
    so the caller can record a paid request before waiting."""
    if not api_key.strip():
        raise FalMediaError("Real AI image/video generation is not configured. Add FAL_KEY to the app's private .env file.")
    url = f"{FAL_QUEUE_BASE}/{model_id}"
    submitted = _json_request(url, api_key.strip(), method="POST", payload=payload, timeout_s=60)
    status_url = submitted.get("status_url")
    result_url = submitted.get("response_url")
    for candidate in (status_url, result_url):
        _check_queue_url(candidate)
    if on_submit:
        on_submit(submitted.get("request_id"), status_url, result_url)
    return collect(api_key, status_url, result_url, timeout_s)


def _download_media(url: str) -> bytes:
    parsed = urllib.parse.urlparse(url or "")
    host = (parsed.hostname or "").lower()
    allowed = host == "storage.googleapis.com" or host == "fal.media" or host.endswith(".fal.media")
    if parsed.scheme != "https" or not allowed:
        raise FalMediaError("fal.ai returned an unsupported media URL")
    request = urllib.request.Request(url, headers={"Accept": "application/octet-stream"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            media = response.read(100 * 1024 * 1024 + 1)
    except (OSError, TimeoutError):
        raise FalMediaError("Could not download generated media from fal.ai") from None
    if not media or len(media) > 100 * 1024 * 1024:
        raise FalMediaError("fal.ai returned empty or oversized media")
    return media


def request_fal_image(api_key: str, payload: dict, timeout_s: int = 300) -> bytes:
    result = _submit_and_wait(api_key, IMAGE_MODEL_ID, payload, timeout_s)
    images = result.get("images") or []
    image_url = images[0].get("url") if images and isinstance(images[0], dict) else None
    image = _download_media(image_url)
    if not image.startswith(b"\xff\xd8\xff"):
        raise FalMediaError("fal.ai image output was not a JPEG")
    return image


def request_fal_video(api_key: str, payload: dict, timeout_s: int = 900) -> bytes:
    result = _submit_and_wait(api_key, VIDEO_MODEL_ID, payload, timeout_s)
    video = result.get("video")
    video_url = video.get("url") if isinstance(video, dict) else None
    media = _download_media(video_url)
    if not (media.startswith(b"\x00\x00\x00") or b"ftyp" in media[:32]):
        raise FalMediaError("fal.ai video output was not an MP4")
    return media
