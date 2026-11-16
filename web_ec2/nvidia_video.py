"""Small, testable adapter for NVIDIA's hosted Cosmos 3 Nano video API."""

from __future__ import annotations

import base64
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path


COSMOS3_ENDPOINT = "https://ai.api.nvidia.com/v1/cosmos/nvidia/cosmos3-nano"
VIDEO_MODEL_ID = "nvidia/cosmos3-nano"
RESOLUTION_TIERS = {"480p": "480", "720p": "720"}
ASPECT_SUFFIXES = {"16:9": "16_9", "9:16": "9_16"}


class NvidiaVideoError(RuntimeError):
    """A sanitized NVIDIA video API error suitable for an application log."""


def build_video_prompt(
    *,
    brief: str,
    shot: dict,
    brand: str,
    product: str,
    style: str,
    camera: str,
    lighting: str,
    features: str = "",
) -> str:
    """Compile a short visual prompt; exact brand lettering is composited later."""
    visual = " ".join(str(shot.get("visual_prompt") or "A polished product hero shot").split()[:65])
    shot_camera = " ".join(str(shot.get("camera") or "").split()[:18])
    camera_descriptions = {
        "macro_push": "slow macro push-in",
        "drone_sweep": "smooth high-angle aerial sweep",
        "orbit_360": "slow, steady product orbit",
        "tracking_fast": "controlled lateral tracking with restrained speed",
        "hero_tilt": "slow low-angle tilt up",
    }
    lighting_descriptions = {
        "studio_clean": "soft, even commercial studio lighting",
        "golden_hour": "warm natural golden-hour light",
        "neon_cyber": "controlled neon edge light in a dark studio",
        "moody_contrast": "dramatic but readable high-contrast lighting",
        "daylight": "crisp natural daylight",
    }
    selected_camera = camera_descriptions.get(camera, camera)
    camera_description = "; shot direction: ".join(
        part for part in (selected_camera, shot_camera) if part
    ) or "slow cinematic push-in"
    lighting = lighting_descriptions.get(lighting, lighting)
    brief = " ".join(brief.split()[:65])
    features = " ".join(features.split()[:25])
    parts = [
        "Create one photorealistic commercial video shot, not a storyboard or a collage.",
        f"Product identity: {product}. Preserve the exact product silhouette, materials, and colors.",
        f"Action and setting: {visual}.",
        f"Camera movement: {camera_description}; show one continuous, visible action with smooth, physically plausible motion. Keep product geometry stable; avoid morphing, flicker, duplicates, and abrupt cuts.",
        f"Lighting: {lighting}. Visual style: {' '.join(str(style).split()[:12])}.",
    ]
    if features.strip():
        parts.append(f"Show these product attributes accurately: {features.strip()}.")
    if brief.strip():
        parts.append(f"Creative direction: {brief.strip()}")
    parts.append(
        "Keep the main product in frame and unobstructed. Do not invent packaging, logos, labels, captions, "
        "letters, numbers, watermarks, extra products, or scene cuts. A separate post-render layer adds the exact brand name."
    )
    return " ".join(parts)


def build_cosmos_payload(
    *,
    prompt: str,
    aspect_ratio: str,
    resolution: str,
    duration_s: int,
    seed: int,
    reference_data_uri: str | None = None,
) -> dict:
    if aspect_ratio not in ASPECT_SUFFIXES:
        raise ValueError("Unsupported aspect ratio")
    if resolution not in RESOLUTION_TIERS:
        raise ValueError("Unsupported resolution")
    if not 1 <= duration_s <= 15:
        raise ValueError("Shot duration must be between 1 and 15 seconds")
    if not prompt.strip() or len(prompt.split()) > 300:
        raise ValueError("Video prompt must contain 1 to 300 words")

    payload = {
        "model_mode": "image2video" if reference_data_uri else "text2video",
        "prompt": prompt,
        "resolution": f"{RESOLUTION_TIERS[resolution]}_{ASPECT_SUFFIXES[aspect_ratio]}",
        "num_frames": min(397, max(25, round(duration_s * 24))),
        "num_inference_steps": 35,
        "fps": 24,
        "seed": max(0, int(seed)),
    }
    if reference_data_uri:
        payload["input_reference"] = reference_data_uri
    return payload


def build_cosmos_image_payload(
    *, prompt: str, aspect_ratio: str, resolution: str, seed: int
) -> dict:
    """Build a single, shot-specific Cosmos3 Nano text-to-image request."""
    if aspect_ratio not in ASPECT_SUFFIXES:
        raise ValueError("Unsupported aspect ratio")
    if resolution not in RESOLUTION_TIERS:
        raise ValueError("Unsupported resolution")
    if not prompt.strip() or len(prompt.split()) > 300:
        raise ValueError("Image prompt must contain 1 to 300 words")
    return {
        "model_mode": "text2image",
        "prompt": prompt,
        "resolution": f"{RESOLUTION_TIERS[resolution]}_{ASPECT_SUFFIXES[aspect_ratio]}",
        "seed": max(0, int(seed)),
    }


def build_keyframe_prompt(*, brief: str, shot: dict, product: str, style: str, lighting: str, features: str = "") -> str:
    """Describe a clean, single AI-generated image that will anchor one video shot."""
    visual = " ".join(str(shot.get("visual_prompt") or "A polished product hero shot").split()[:55])
    brief = " ".join(brief.split()[:55])
    features = " ".join(features.split()[:22])
    parts = [
        "Create one photorealistic premium commercial product photograph, a single coherent frame, not a collage or storyboard.",
        f"Subject: {product}. Show a plausible, clean product silhouette and materials.",
        f"Scene: {visual}. Creative brief: {brief}.",
        f"Visual style: {' '.join(str(style).split()[:12])}. Lighting: {' '.join(str(lighting).split()[:12])}.",
    ]
    if features:
        parts.append(f"Visibly include these attributes where appropriate: {features}.")
    parts.append("Compose with clear subject separation and enough background for subtle camera motion. Do not add any text, letters, numbers, logos, labels, watermarks, duplicate products, borders, or inset images; exact branding is added after rendering.")
    return " ".join(parts)


def request_cosmos_image(api_key: str, payload: dict, timeout_s: int = 180) -> bytes:
    """Request and decode a JPEG keyframe from NVIDIA's hosted Cosmos3 endpoint."""
    body = _request_cosmos_json(api_key, payload, timeout_s)
    encoded_image = body.get("b64_image") if isinstance(body, dict) else None
    if not isinstance(encoded_image, str) or not encoded_image:
        raise NvidiaVideoError("NVIDIA Cosmos API response did not contain b64_image")
    try:
        image = base64.b64decode(encoded_image, validate=True)
    except (ValueError, base64.binascii.Error):
        raise NvidiaVideoError("NVIDIA Cosmos API returned invalid image data") from None
    if not image or not image.startswith(b"\xff\xd8\xff"):
        raise NvidiaVideoError("NVIDIA Cosmos API returned an empty or non-JPEG image")
    return image


def request_cosmos_video(api_key: str, payload: dict, timeout_s: int = 300) -> bytes:
    body = _request_cosmos_json(api_key, payload, timeout_s)
    encoded_video = body.get("b64_video") if isinstance(body, dict) else None
    if not isinstance(encoded_video, str) or not encoded_video:
        raise NvidiaVideoError("NVIDIA Cosmos API response did not contain b64_video")
    try:
        video = base64.b64decode(encoded_video, validate=True)
    except (ValueError, base64.binascii.Error):
        raise NvidiaVideoError("NVIDIA Cosmos API returned invalid video data") from None
    if not video:
        raise NvidiaVideoError("NVIDIA Cosmos API returned an empty video")
    return video


def _request_cosmos_json(api_key: str, payload: dict, timeout_s: int) -> dict:
    if not api_key.strip():
        raise NvidiaVideoError("NVIDIA_API_KEY is not configured")

    request = urllib.request.Request(
        COSMOS3_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key.strip()}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Return a small provider diagnostic, never the raw response or credentials.
        try:
            error_body = json.loads(exc.read(4096).decode("utf-8", errors="replace"))
            detail = error_body.get("detail") or error_body.get("message") or error_body.get("title")
            if isinstance(detail, dict):
                detail = detail.get("message") or detail.get("type")
            detail = " ".join(str(detail or "").split())[:240]
            if api_key.strip():
                detail = detail.replace(api_key.strip(), "[redacted]")
        except (OSError, json.JSONDecodeError, AttributeError):
            detail = ""
        suffix = f": {detail}" if detail else ""
        raise NvidiaVideoError(f"NVIDIA Cosmos API returned HTTP {exc.code}{suffix}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        timed_out = isinstance(exc, TimeoutError) or (
            isinstance(exc, urllib.error.URLError) and isinstance(exc.reason, TimeoutError)
        )
        reason = (
            "request timed out; the provider may still be processing it, so check status before retrying"
            if timed_out else "request failed"
        )
        raise NvidiaVideoError(f"NVIDIA Cosmos API {reason}") from None

    if not isinstance(body, dict):
        raise NvidiaVideoError("NVIDIA Cosmos API returned an invalid response")
    return body


def probe_video(path: Path) -> dict:
    """Return objective container/stream facts; never label visual quality."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-count_frames", "-show_entries",
                "format=duration,bit_rate:stream=codec_type,codec_name,width,height,avg_frame_rate,nb_read_frames,bit_rate,sample_rate,channels",
                "-of", "json", str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
        data = json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return {"verified": False, "reason": "ffprobe could not inspect the file"}

    streams = data.get("streams", [])
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    if not video_stream:
        return {"verified": False, "reason": "video stream is missing"}
    try:
        duration_s = float(data.get("format", {}).get("duration", 0))
    except (TypeError, ValueError):
        duration_s = 0.0
    if duration_s <= 0 or not video_stream.get("width") or not video_stream.get("height"):
        return {"verified": False, "reason": "video duration or dimensions are missing"}
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    try:
        audio_sample_rate = int(audio_stream["sample_rate"]) if audio_stream and audio_stream.get("sample_rate") else None
    except (TypeError, ValueError):
        audio_sample_rate = None
    return {
        "verified": True,
        "duration_s": round(duration_s, 3),
        "width": video_stream["width"],
        "height": video_stream["height"],
        "frame_count": int(video_stream["nb_read_frames"]) if str(video_stream.get("nb_read_frames", "")).isdigit() else None,
        "bitrate_bps": int(video_stream.get("bit_rate") or data.get("format", {}).get("bit_rate") or 0) or None,
        "video_codec": video_stream.get("codec_name"),
        "frame_rate": video_stream.get("avg_frame_rate"),
        "has_audio": audio_stream is not None,
        "audio": ({
            "codec": audio_stream.get("codec_name"),
            "sample_rate_hz": audio_sample_rate,
            "channels": audio_stream.get("channels"),
        } if audio_stream else None),
    }
