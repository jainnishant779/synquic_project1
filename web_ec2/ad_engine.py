"""Ad timeline, animated text and ffmpeg rendering.

A project is one JSON timeline. Rendering turns each scene into a short silent clip (AI video, an AI image, your photo,
your real product cut out over a background, or a designed text card) with animated text burned in through libass, then
joins the clips and mixes audio. A scene is cached by a hash of what it contains, so editing one scene re-renders only that
scene. No network and no paid call happens in this module.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

SIZES = {("720p", "16:9"): (1280, 720), ("720p", "9:16"): (720, 1280), ("720p", "1:1"): (720, 720), ("720p", "4:5"): (720, 900),
         ("1080p", "16:9"): (1920, 1080), ("1080p", "9:16"): (1080, 1920), ("1080p", "1:1"): (1080, 1080), ("1080p", "4:5"): (1080, 1350)}
FPS = 24
# Safe zones as (top, bottom, left, right) fractions of the frame that platform buttons and captions cover.
# Reels: Meta ads guide (top 14%, bottom 35%, sides 6%). Shorts: Google (top 10%, bottom 25%, right 10%).
# TikTok's official template could not be read, so it uses the Reels zones plus room for the right-hand buttons.
PLATFORMS = {
    "reels": {"aspect": "9:16", "safe": (0.14, 0.35, 0.06, 0.06), "label": "Instagram / Facebook Reels"},
    "tiktok": {"aspect": "9:16", "safe": (0.14, 0.35, 0.06, 0.15), "label": "TikTok"},
    "shorts": {"aspect": "9:16", "safe": (0.10, 0.25, 0.06, 0.10), "label": "YouTube Shorts"},
    "feed": {"aspect": "4:5", "safe": (0.05, 0.05, 0.05, 0.05), "label": "Instagram / Facebook feed (4:5)"},
    "square": {"aspect": "1:1", "safe": (0.05, 0.05, 0.05, 0.05), "label": "Square (1:1)"},
    "landscape": {"aspect": "16:9", "safe": (0.06, 0.08, 0.05, 0.05), "label": "YouTube / web (16:9)"},
}
# Exact deterministic safe bounding boxes (left, top, right, bottom) across platforms.
# Margins preserve UI buttons, captions, like/share overlays and profile headers.
SAFE_BOUNDING_BOXES = {
    ("reels", 1080, 1920): (65, 269, 1015, 1248),
    ("reels", 1440, 2560): (86, 358, 1354, 1664),
    ("shorts", 1080, 1920): (65, 192, 972, 1440),
    ("feed", 1080, 1350): (54, 108, 1026, 1148),
}
ASPECT_PLATFORM = {"9:16": "reels", "4:5": "feed", "1:1": "square", "16:9": "landscape"}
TEXT_STYLES = ("kinetic", "slide", "wipe", "lower_third", "cta", "brand", "plain", "caption")
POSITIONS = ("top", "center", "bottom")
TEXT_SIZES = {"s": 0.8, "m": 1.0, "l": 1.25, "xl": 1.5}
SCENE_KINDS = ("ai_video", "ai_image", "image", "product", "card")
MAX_SCENES, MAX_TOTAL_S, MAX_TEXT = 12, 60.0, 120
KIND_LABELS = {"ai_video": "AI video", "ai_image": "AI image (animated)", "image": "Your photo (animated)",
               "product": "Your real product on a background", "card": "Designed text card (no AI video)"}
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
SCENE_ID = re.compile(r"^[a-z][a-z0-9_]{0,23}$")
SOURCE_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,80}\.(mp4|mov|jpg|jpeg|png|webp)$")   # a bare file name in the project folder, never a path
AUDIO_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,80}\.(mp3|wav|m4a)$")
CUTOUT_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,80}\.png$")

# Size of each style relative to the base size.
STYLE_SCALE = {"kinetic": 1.0, "slide": 0.8, "wipe": 0.9, "lower_third": 0.62, "cta": 0.62, "brand": 1.2, "plain": 0.7, "caption": 0.5}
HIGHLIGHT = "#FFD84D"   # emphasised words: a warm yellow reads on any brand colour, which the brand colour itself does not
# A look is the ad's visual theme: the background of designed cards, the default text colour on those cards, and the highlight colour.
CARD_STYLES = ("glow", "dark", "light", "bold", "festive", "glass")
DEFAULT_LOOK = {"card": "glow", "text": "#FFFFFF", "highlight": HIGHLIGHT}


def _luma(hex_color):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def card_look(look, brand_color):
    """The look as drawn on a designed card. A bold card is flat brand colour: with a light brand colour (yellow, mint) white text
    and a yellow highlight wash out, so the text turns dark and the highlight takes a colour that stands out from the background."""
    if look["card"] != "bold" or _luma(brand_color) <= 0.6:
        return look
    text = look["text"] if _luma(look["text"]) < 0.5 else "#141414"
    highlight = look["highlight"]
    if abs(_luma(highlight) - _luma(brand_color)) < 0.3:
        highlight = "#C62828" if abs(_luma("#C62828") - _luma(brand_color)) >= 0.3 else "#1E3A8A"
    return dict(look, text=text, highlight=highlight)


class AdError(ValueError):
    """A timeline or edit the engine refuses, with a message safe to show in the UI."""


# ---------------------------------------------------------------- timeline

def default_timeline(brand="Brand", color="#18B26B", aspect="9:16", resolution="1080p", platform=None):
    platform = platform or ASPECT_PLATFORM.get(aspect, "reels")
    return {"version": 2, "title": f"{brand} ad", "platform": platform, "aspect": PLATFORMS[platform]["aspect"], "resolution": resolution, "fps": FPS,
            "brand": {"name": brand, "color": color, "logo": None}, "audio": {"voice": None, "music": None, "music_volume": 0.16, "captions": False},
            "look": dict(DEFAULT_LOOK), "scenes": []}


def _clean_text(text):
    text = " ".join(str(text or "").replace("{", "").replace("}", "").replace("\\", "").split())
    if len(text) > MAX_TEXT:
        raise AdError(f"Text is limited to {MAX_TEXT} characters")
    return text


def validate_timeline(timeline):
    """Return a cleaned copy, or raise AdError. Everything the renderer reads goes through here."""
    if not isinstance(timeline, dict):
        raise AdError("Timeline must be an object")
    t = copy.deepcopy(timeline)
    platform = t.get("platform") or ASPECT_PLATFORM.get(t.get("aspect"), "")
    if platform not in PLATFORMS:
        raise AdError(f"Unknown platform. Options: {', '.join(PLATFORMS)}")
    t["platform"], t["aspect"] = platform, PLATFORMS[platform]["aspect"]
    if (t.get("resolution"), t["aspect"]) not in SIZES:
        raise AdError("Unsupported resolution")
    t["fps"] = FPS
    brand = t.setdefault("brand", {})
    brand["name"] = _clean_text(brand.get("name") or "Brand")[:60]
    brand["color"] = brand.get("color") if HEX.match(str(brand.get("color", ""))) else "#18B26B"
    brand["logo"] = brand.get("logo") or None
    if brand["logo"] is not None and not SOURCE_NAME.match(str(brand["logo"])):
        raise AdError("Logo must be a plain image file name inside the ad folder")
    audio = t.setdefault("audio", {})
    audio["voice"] = audio.get("voice") or None
    audio["music"] = audio.get("music") or None
    if audio["music"] is not None and not AUDIO_NAME.match(str(audio["music"])):
        raise AdError("Music must be a plain mp3, wav or m4a file name inside the ad folder")
    audio["music_volume"] = min(0.6, max(0.0, float(audio.get("music_volume", 0.16))))
    audio["captions"] = bool(audio.get("captions", False))
    look = t.get("look") or {}
    if not isinstance(look, dict):
        raise AdError("Look must be an object")
    card = look.get("card") or "glow"
    if card not in CARD_STYLES:
        raise AdError(f"Card style must be one of {', '.join(CARD_STYLES)}")
    t["look"] = {"card": card, "text": look.get("text") if HEX.match(str(look.get("text", ""))) else DEFAULT_LOOK["text"],
                 "highlight": look.get("highlight") if HEX.match(str(look.get("highlight", ""))) else DEFAULT_LOOK["highlight"]}
    scenes = t.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise AdError("An ad needs at least one scene")
    if len(scenes) > MAX_SCENES:
        raise AdError(f"At most {MAX_SCENES} scenes")
    seen, total = set(), 0.0
    for scene in scenes:
        sid = str(scene.get("id", ""))
        if not SCENE_ID.match(sid) or sid in seen:
            raise AdError(f"Bad or repeated scene id {sid!r}")
        seen.add(sid)
        if scene.get("kind") not in SCENE_KINDS:
            raise AdError(f"Scene {sid}: kind must be one of {SCENE_KINDS}")
        scene["duration"] = round(min(15.0, max(1.0, float(scene.get("duration", 3)))), 2)
        scene["trim_start"] = max(0.0, float(scene.get("trim_start", 0)))
        total += scene["duration"]
        scene["narration"] = _clean_text(scene.get("narration", ""))
        scene["visual_prompt"] = " ".join(str(scene.get("visual_prompt", "")).split())[:600]
        scene["purpose"] = str(scene.get("purpose") or "")[:20]
        scene["source"] = scene.get("source") or None
        if scene["source"] is not None and not SOURCE_NAME.match(str(scene["source"])):
            raise AdError(f"Scene {sid}: source must be a plain file name inside the ad folder")
        if scene["kind"] in ("image", "ai_image") and scene["source"] is None:
            raise AdError(f"Scene {sid}: this scene needs a picture")
        scene["product"] = scene.get("product") or None
        if scene["kind"] == "product":
            if scene["product"] is None or not CUTOUT_NAME.match(str(scene["product"])):
                raise AdError(f"Scene {sid}: a product scene needs the product cut-out (a PNG file name)")
        else:
            scene["product"] = None
        layers, ids = [], set()
        for number, layer in enumerate(scene.get("text") or [], 1):
            lid = str(layer.get("id") or f"t{number}")
            if not SCENE_ID.match(lid) or lid in ids:
                raise AdError(f"Scene {sid}: bad or repeated text id {lid!r}")
            ids.add(lid)
            style = layer.get("style", "kinetic")
            if style not in TEXT_STYLES:
                raise AdError(f"Unknown text style {style!r}. Options: {', '.join(TEXT_STYLES)}")
            position = layer.get("position", "center")
            if position not in POSITIONS:
                raise AdError(f"Unknown position {position!r}")
            color = layer.get("color") or None
            if color is not None and not HEX.match(str(color)):
                raise AdError(f"Colour must look like #FFD84D, not {color!r}")
            size = layer.get("size") or "m"
            if size not in TEXT_SIZES:
                raise AdError(f"Size must be one of {', '.join(TEXT_SIZES)}")
            start = max(0.0, float(layer.get("start", 0.15)))
            end = layer.get("end")
            end = scene["duration"] if end in (None, "") else min(scene["duration"], float(end))
            if end - start < 0.3:
                start = max(0.0, end - 0.3)
            layers.append({"id": lid, "text": _clean_text(layer.get("text", "")), "style": style, "position": position, "color": color, "size": size,
                           "start": round(start, 2), "end": round(end, 2)})
        scene["text"] = [layer for layer in layers if layer["text"]]
    if total > MAX_TOTAL_S:
        raise AdError(f"Total length {total:.0f}s is over the {MAX_TOTAL_S:.0f}s limit")
    return t


def total_duration(timeline):
    return round(sum(s["duration"] for s in timeline["scenes"]), 2)


def scene_starts(timeline):
    starts, at = [], 0.0
    for scene in timeline["scenes"]:
        starts.append(round(at, 3))
        at += scene["duration"]
    return starts


def elements_at(timeline, t):
    """What is on screen at second t: the scene, its local time, active text layers, and visual layer context."""
    starts = scene_starts(timeline)
    t = max(0.0, min(float(t), total_duration(timeline) - 0.001))
    for index, (scene, start) in enumerate(zip(timeline["scenes"], starts)):
        if start <= t < start + scene["duration"]:
            local = round(t - start, 3)
            visible = []
            for layer in scene["text"]:
                start_t = float(layer.get("start") or 0.0)
                end_t = float(layer["end"]) if layer.get("end") is not None else float(scene["duration"])
                if start_t <= local < end_t:
                    visible.append(layer)
            width, height = SIZES.get((timeline.get("resolution", "1080p"), timeline.get("aspect", "9:16")), (1080, 1920))
            area = safe_area(timeline.get("platform", "reels"), width, height)
            active_layers = []
            for layer in visible:
                cy = text_y(layer.get("position", "center"), area)
                active_layers.append({
                    "id": layer["id"], "text": layer["text"], "style": layer["style"],
                    "position": layer["position"], "color": layer.get("color"),
                    "size": layer.get("size", "m"), "start": layer["start"], "end": layer["end"],
                    "y_anchor": cy, "bounding_box": (area[0], cy - 30, area[2], cy + 30)
                })
            badge = ("Exact Product Layer" if scene["kind"] == "product"
                     else ("AI Lifestyle Preview" if scene["kind"] in ("ai_video", "ai_image")
                           else "Designed Card Layer"))
            return {
                "scene": scene["id"], "scene_id": scene["id"],
                "index": index, "scene_index": index,
                "scene_start": start, "local_t": local, "t_scene": round(local, 2),
                "kind": scene["kind"],
                "visual_layer": {
                    "bg_uri": scene.get("source"),
                    "cutout_uri": scene.get("product") if scene["kind"] == "product" else None,
                    "parallax_preset": "smooth_2.5d" if scene["kind"] == "product" else "none",
                    "safety_badge": badge
                },
                "visible_text": [layer["id"] for layer in visible],
                "active_text_layers": active_layers,
                "all_text": [layer["id"] for layer in scene["text"]]
            }
    raise AdError("Time is outside the ad")


def _next_id(ids, prefix):
    used = set(ids)
    number = 1
    while f"{prefix}{number}" in used:
        number += 1
    return f"{prefix}{number}"


def apply_edit(timeline, op):
    """Apply one edit and return the new, validated timeline. The input is not changed."""
    t = copy.deepcopy(timeline)
    name = op.get("op")
    scenes = t["scenes"]

    def scene_of(key="scene"):
        for scene in scenes:
            if scene["id"] == op.get(key):
                return scene
        raise AdError(f"No scene {op.get(key)!r}")

    def layer_of(scene):
        for layer in scene["text"]:
            if layer["id"] == op.get("layer"):
                return layer
        raise AdError(f"No text layer {op.get('layer')!r} in scene {scene['id']}")

    if name in ("set_text", "set_style", "set_position", "set_color", "set_size", "set_timing"):
        layer = layer_of(scene_of())
        field = {"set_text": "text", "set_style": "style", "set_position": "position", "set_color": "color", "set_size": "size"}.get(name)
        if field:
            value = op.get("value", op.get("text") if name == "set_text" else None)
            if value is None and name != "set_color":
                raise AdError(f"{name} needs a value")
            layer[field] = value
        else:
            layer["start"], layer["end"] = op.get("start", layer["start"]), op.get("end", layer["end"])
    elif name == "add_text":
        scene = scene_of()
        scene["text"].append({"id": _next_id([x["id"] for x in scene["text"]], "t"), "text": op.get("text", "New text"),
                              "style": op.get("style", "slide"), "position": op.get("position", "bottom"), "color": op.get("color"),
                              "size": op.get("size", "m"), "start": op.get("start", 0.2), "end": op.get("end")})
    elif name == "delete_text":
        scene = scene_of()
        layer_of(scene)
        scene["text"] = [x for x in scene["text"] if x["id"] != op.get("layer")]
    elif name == "set_duration":
        scene = scene_of()
        scene["duration"] = op.get("value")
        for layer in scene["text"]:
            layer["end"] = None
    elif name == "split_scene":
        scene = scene_of()
        at = float(op.get("at", 0))
        if not 0.5 <= at <= scene["duration"] - 0.5:
            raise AdError("Split at least half a second from either end of the scene")
        second = copy.deepcopy(scene)
        second["id"] = _next_id([s["id"] for s in scenes], "s")
        # The voice line is not cut here: build_voice_track lets a line carry on through the following scenes that have none.
        second["duration"], scene["duration"] = round(scene["duration"] - at, 2), round(at, 2)
        second["trim_start"] = scene.get("trim_start", 0) + at
        second["narration"] = ""
        first_layers, second_layers = [], []
        for layer in scene["text"]:
            end = layer["end"] if layer["end"] is not None else at + second["duration"]
            if layer["start"] < at:
                first_layers.append({**layer, "end": min(end, at)})
            if end > at:
                second_layers.append({**layer, "start": max(0.0, layer["start"] - at), "end": end - at})
        scene["text"], second["text"] = first_layers, second_layers
        scenes.insert(scenes.index(scene) + 1, second)
    elif name == "set_narration":
        scene_of()["narration"] = op.get("value", "")
    elif name == "set_visual_prompt":
        scene_of()["visual_prompt"] = op.get("value", "")
    elif name == "move_scene":
        scene = scene_of()
        scenes.remove(scene)
        scenes.insert(max(0, min(len(scenes), int(op.get("to", 0)))), scene)
    elif name == "delete_scene":
        if len(scenes) < 2:
            raise AdError("An ad needs at least one scene")
        scenes.remove(scene_of())
    elif name == "duplicate_scene":
        scene = copy.deepcopy(scene_of())
        scene["id"] = _next_id([s["id"] for s in scenes], "s")
        scenes.insert(scenes.index(scene_of()) + 1, scene)
    elif name == "add_card":
        card = {"id": _next_id([s["id"] for s in scenes], "c"), "kind": "card", "source": None, "duration": float(op.get("duration", 3)), "narration": "",
                "visual_prompt": "", "text": [{"id": "t1", "text": op.get("text", "Your message"), "style": "kinetic", "position": "center", "start": 0.15, "end": None}]}
        index = op.get("index")
        scenes.insert(len(scenes) if index is None else max(0, min(len(scenes), int(index))), card)
    elif name == "set_brand":
        t["brand"]["name"] = op.get("name", t["brand"]["name"])
        t["brand"]["color"] = op.get("color", t["brand"]["color"])
    elif name == "set_platform":
        if op.get("value") not in PLATFORMS:
            raise AdError(f"Unknown platform. Options: {', '.join(PLATFORMS)}")
        t["platform"] = op["value"]
        t["aspect"] = PLATFORMS[op["value"]]["aspect"]
    elif name == "set_audio":
        for key in ("voice", "music_volume", "captions"):
            if key in op:
                t["audio"][key] = op[key]
    elif name == "set_look":
        look = t.setdefault("look", dict(DEFAULT_LOOK))
        for key in ("card", "text", "highlight"):
            if key in op:
                look[key] = op[key]
    else:
        raise AdError(f"Unknown edit {name!r}")
    return validate_timeline(t)


def lint(timeline):
    """Ad rules from the Meta, YouTube and TikTok guides, as warnings. Nothing here blocks a render."""
    warnings = []
    scenes = timeline["scenes"]
    first = scenes[0]
    if not any(layer["start"] <= 0.5 for layer in first["text"]):
        warnings.append("Hook: put a line on screen in the first half second.")
    brand = timeline["brand"]["name"].lower()
    early, at = False, 0.0
    for scene in scenes:
        if at >= 3:
            break
        early |= any(brand in layer["text"].lower() and at + layer["start"] < 3 for layer in scene["text"])
        at += scene["duration"]
    if not early and not (timeline["brand"].get("logo") and len(scenes) == 1):
        warnings.append("Show the brand name in the first 3 seconds.")
    if not any(layer["style"] == "cta" for layer in scenes[-1]["text"]):
        warnings.append("End with a call to action (a 'cta' text on the last scene).")
    for scene in scenes:
        for layer in scene["text"]:
            if len(layer["text"]) > 60 and layer["style"] in ("kinetic", "brand", "cta", "wipe"):
                warnings.append(f"Scene {scene['id']}: '{layer['text'][:30]}...' is long; viewers read about 3 words a second.")
        if scene["kind"] == "product" and any(layer["position"] == "center" and layer["style"] != "caption" for layer in scene["text"]):
            warnings.append(f"Scene {scene['id']}: centre text covers the product; move it to top or bottom.")
    if find_devanagari_font() is None and any(DEVANAGARI.search(layer["text"]) for scene in scenes for layer in scene["text"]):
        warnings.append("Hindi text needs a Devanagari font on the server (Ubuntu: fonts-noto-core), or it shows as empty boxes.")
    total = total_duration(timeline)
    if not 6 <= total <= 60:
        warnings.append(f"Length {total:.0f}s: platforms favour 6 to 60 seconds, 15 to 30 for most ads.")
    return warnings


# ---------------------------------------------------------------- animated text (ASS)

def _bgr(hex_color):
    h = hex_color.lstrip("#")
    return f"&H{h[4:6]}{h[2:4]}{h[0:2]}&".upper()


def _ass_time(seconds):
    cs = int(round(seconds * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def _accent_markup(text, base_color="#FFFFFF", highlight=HIGHLIGHT):
    """*word* switches to the highlight colour. Returns ASS text with the markers removed."""
    out, on = [], False
    for part in text.split("*"):
        out.append(f"{{\\c{_bgr(highlight) if on else _bgr(base_color)}}}{part}")
        on = not on
    return "".join(out)


def _rounded_pill(half_w, half_h):
    """ASS drawing of a pill. Coordinates stay positive (0..2w, 0..2h) because libass aligns a drawing by its box, so an5 alignment centres it on the pos point."""
    w, h = 2 * half_w, 2 * half_h
    r = half_h
    k = int(r * 0.5523)
    return (f"m {r} 0 l {w - r} 0 b {w - r + k} 0 {w} {r - k} {w} {r} b {w} {r + k} {w - r + k} {h} {w - r} {h} l {r} {h} "
            f"b {r - k} {h} 0 {r + k} 0 {r} b 0 {r - k} {r - k} 0 {r} 0")


def safe_area(platform, width, height):
    """(left, top, right, bottom) pixel box that platform buttons and captions leave free."""
    if (platform, width, height) in SAFE_BOUNDING_BOXES:
        return SAFE_BOUNDING_BOXES[(platform, width, height)]
    top, bottom, left, right = PLATFORMS[platform]["safe"]
    return int(width * left), int(height * top), int(width * (1 - right)), int(height * (1 - bottom))


def text_y(position, area):
    _, top, _, bottom = area
    span = bottom - top
    return {"top": top + int(span * 0.12), "center": top + span // 2, "bottom": bottom - int(span * 0.12)}[position]


def build_ass(scene, width, height, accent, font_name, platform="reels", captions_text="", hindi_font=None, look=None, on_card=False):
    """One scene's animated text as an ASS script. Times are scene-local. hindi_font is the family used for Devanagari lines.
    The look's text colour applies on designed cards only; over photos and clips the default text stays white over a dark scrim."""
    look = look or DEFAULT_LOOK
    default_text = look["text"] if on_card else "#FFFFFF"
    highlight = look["highlight"]
    base = min(0.075 * height, 0.125 * width)
    dark_text = _luma(default_text) < 0.5   # dark text sits on a light card: an outline and shadow would look dirty there
    outline, shadow = (0, 0) if dark_text else (max(2, int(base * 0.045)), max(1, int(base * 0.03)))
    area = safe_area(platform, width, height)
    left, _, right, bottom = area
    margin_l, margin_r = left + int(width * 0.02), width - right + int(width * 0.02)
    cx = (left + right) // 2
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {width}", f"PlayResY: {height}", "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
        f"Style: Base,{font_name},{int(base)},&HFFFFFF&,&HFFFFFF&,&H000000&,&H80000000&,1,0,0,0,100,100,0,0,1,{outline},{shadow},5,{margin_l},{margin_r},0,1",
        f"Style: Box,{font_name},{int(base * STYLE_SCALE['caption'])},&HFFFFFF&,&HFFFFFF&,&H99000000&,&H99000000&,1,0,0,0,100,100,0,0,3,{max(4, int(base * 0.12))},0,2,{margin_l},{margin_r},0,1",
        "", "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
    ]

    def add(layer, start, end, text, style="Base"):
        if hindi_font and DEVANAGARI.search(text):
            text = f"{{\\fn{hindi_font}}}" + text
        lines.append(f"Dialogue: {layer},{_ass_time(start)},{_ass_time(end)},{style},,0,0,0,,{text}")

    for item in scene["text"]:
        style, text = item["style"], item["text"]
        start, end = item["start"], item["end"]
        size = int(base * STYLE_SCALE[style] * TEXT_SIZES[item.get("size") or "m"])
        color = item.get("color") or default_text
        cy = text_y(item["position"], area)
        span = int(round((end - start) * 1000))
        body = _accent_markup(text, color, highlight)
        if style == "kinetic":
            words, out, offset = body.split(" "), [], 0
            for word in words:
                out.append(f"{{\\alpha&HFF&\\t({offset},{offset + 140},\\alpha&H00&)}}{word}")
                offset += 110
            add(1, start, end, f"{{\\an5\\pos({cx},{cy})\\fs{size}\\fscx88\\fscy88\\t(0,380,\\fscx100\\fscy100)\\fad(0,160)}}" + " ".join(out))
        elif style == "slide":
            add(1, start, end, f"{{\\an5\\move({cx},{cy + int(height * 0.04)},{cx},{cy},0,420)\\fs{size}\\fad(260,160)}}{body}")
        elif style == "wipe":
            y0, y1 = max(0, cy - int(height * 0.12)), min(height, cy + int(height * 0.12))
            add(1, start, end, f"{{\\an5\\pos({cx},{cy})\\fs{size}\\clip(0,{y0},0,{y1})\\t(0,520,\\clip(0,{y0},{width},{y1}))\\fad(0,160)}}{body}")
        elif style == "lower_third":
            x, y = margin_l, bottom - int(height * 0.02)
            add(1, start, end, f"{{\\an1\\move({-width // 3},{y},{x},{y},0,420)\\fs{size}\\fad(0,160)}}{body}")
            bar_w = int(width * 0.18)
            add(2, start, end, f"{{\\an7\\pos({x},{y + 8})\\1c{_bgr(accent)}\\bord0\\shad0\\fscx0\\t(120,560,\\fscx100)\\p1}}m 0 0 l {bar_w} 0 l {bar_w} 8 l 0 8")
        elif style == "cta":
            half_h = int(size * 0.95)
            half_w = min(int((right - left) * 0.48), int(max(len(text.replace('*', '')) * size * 0.26, size * 1.6) + size * 0.8))
            pulse = "".join(f"\\t({400 + n * 900},{850 + n * 900},\\fscx106\\fscy106)\\t({850 + n * 900},{1300 + n * 900},\\fscx100\\fscy100)" for n in range(max(1, span // 900)))
            pos = f"\\an5\\pos({cx},{cy})"
            pill = item.get("color") or highlight
            label = "&H141414&" if _luma(pill) > 0.55 else "&HFFFFFF&"
            add(1, start, end, f"{{{pos}\\1c{_bgr(pill)}\\bord0\\shad0\\fscx80\\fscy80\\t(0,300,\\fscx100\\fscy100){pulse}\\fad(180,150)\\p1}}{_rounded_pill(half_w, half_h)}")
            add(2, start, end, f"{{{pos}\\fs{size}\\1c{label}\\bord0\\shad0\\fscx80\\fscy80\\t(0,300,\\fscx100\\fscy100){pulse}\\fad(180,150)}}{text.replace('*', '')}")
        elif style == "brand":
            if DEVANAGARI.search(text):   # letter spacing pulls Devanagari vowel signs off their letters (dotted circles); blur in instead
                add(1, start, end, f"{{\\an5\\pos({cx},{cy})\\fs{size}\\blur6\\t(0,900,\\blur0)\\fad(380,200)}}{body}")
            else:
                add(1, start, end, f"{{\\an5\\pos({cx},{cy})\\fs{size}\\fsp26\\blur2\\t(0,1100,\\fsp4)\\fad(380,200)}}{body}")
        elif style == "caption":
            add(3, start, end, f"{{\\an2\\pos({cx},{bottom - int(height * 0.01)})\\fs{size}\\1c{_bgr(color)}\\fad(120,120)}}{text.replace('*', '')}", style="Box")
        else:
            add(1, start, end, f"{{\\an5\\pos({cx},{cy})\\fs{size}\\fad(220,160)}}{body}")
    if captions_text:
        add(3, 0.1, scene["duration"], f"{{\\an2\\pos({cx},{bottom - int(height * 0.01)})\\fad(120,120)}}{captions_text.replace('*', '')}", style="Box")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- rendering

def find_font():
    """(family, file) of a bold sans font that exists on this machine, or raise."""
    for family, path in (("DejaVu Sans", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"), ("Arial", "C:/Windows/Fonts/arialbd.ttf"),
                         ("Segoe UI", "C:/Windows/Fonts/segoeuib.ttf")):
        if Path(path).is_file():
            return family, Path(path)
    raise AdError("No bold font found. On Ubuntu install fonts-dejavu-core.")


DEVANAGARI = re.compile(r"[\u0900-\u097F]")


def find_devanagari_font():
    """(family, file) of a font with Hindi glyphs, or None. DejaVu has none, so Hindi text would render as empty boxes."""
    for family, path in (("Noto Sans Devanagari", "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"),
                         ("Noto Sans Devanagari", "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"),
                         ("Lohit Devanagari", "/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf"),
                         ("Nirmala UI", "C:/Windows/Fonts/NirmalaB.ttf"), ("Nirmala UI", "C:/Windows/Fonts/Nirmala.ttf")):
        if Path(path).is_file():
            return family, Path(path)
    return None


def _run(cmd, cwd=None):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)
    if result.returncode:
        tail = " ".join(result.stderr.strip().splitlines()[-3:])[:400]
        raise AdError(f"ffmpeg failed: {tail}")
    return result


def probe(path):
    result = _run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])
    info = json.loads(result.stdout)
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    return {"duration": round(float(info["format"]["duration"]), 2), "width": video and video["width"], "height": video and video["height"],
            "has_audio": audio is not None}


def _hex_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _legacy_card_background(path, width, height, color, style="glow"):
    """A designed background so a text card does not look empty. Styles: glow (brand gradient with soft light), dark (near black
    with a brand-coloured glow, for premium looks), light (warm paper white, for dark text), bold (flat brand colour with diagonal
    bands, for launches and sales), festive (deep brand gradient with gold sparkles)."""
    import random
    from PIL import Image, ImageDraw, ImageFilter
    r, g, b = _hex_rgb(color)

    def gradient(top, bottom):
        image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(image)
        for y in range(height):
            k = y / max(1, height - 1)
            draw.line([(0, y), (width, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3)))
        return image.convert("RGBA")

    shapes = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shapes)
    blur = width * 0.02
    if style == "dark":
        image = gradient((10, 10, 14), (24, 24, 30))
        sd.ellipse([int(width * -0.45), int(height * 0.55), int(width * 0.75), int(height * 1.25)], fill=(r, g, b, 90))
        sd.ellipse([int(width * 0.6), int(height * -0.15), int(width * 1.3), int(height * 0.25)], fill=(r, g, b, 45))
        blur = width * 0.12
    elif style == "light":
        image = gradient((251, 247, 240), (240, 232, 219))
        sd.ellipse([int(width * 0.5), int(height * -0.1), int(width * 1.35), int(height * 0.35)], fill=(r, g, b, 38))
        sd.ellipse([int(width * -0.4), int(height * 0.7), int(width * 0.45), int(height * 1.15)], fill=(r, g, b, 30))
        blur = width * 0.06
    elif style == "bold":
        image = Image.new("RGBA", (width, height), (r, g, b, 255))
        dark = (int(r * 0.72), int(g * 0.72), int(b * 0.72), 255)
        sd.polygon([(0, int(height * 0.62)), (width, int(height * 0.38)), (width, int(height * 0.58)), (0, int(height * 0.82))], fill=dark)
        sd.polygon([(0, int(height * 0.86)), (width, int(height * 0.62)), (width, int(height * 0.66)), (0, int(height * 0.9))], fill=(255, 255, 255, 40))
        blur = 0
    elif style == "festive":
        image = gradient((int(r * 0.22), int(g * 0.18), int(b * 0.2) + 8), (int(r * 0.7), int(g * 0.5), int(b * 0.45)))
        rng = random.Random(7)   # the same sparkles every render, so cached scenes stay identical
        for _ in range(46):
            x, y, d = rng.randint(0, width), rng.randint(0, height), rng.randint(int(width * 0.006), int(width * 0.03))
            sd.ellipse([x - d, y - d, x + d, y + d], fill=(233, 185, 73, rng.randint(60, 150)))
        sd.rectangle([int(width * 0.04), int(height * 0.025), int(width * 0.96), int(height * 0.975)], outline=(233, 185, 73, 120), width=max(2, width // 240))
        blur = width * 0.002
    else:
        image = gradient((int(r * 0.25), int(g * 0.25), int(b * 0.25) + 18), (r, g, b))
        sd.ellipse([int(width * 0.55), int(height * -0.08), int(width * 1.3), int(height * 0.38)], fill=(255, 255, 255, 26))
        sd.ellipse([int(width * -0.35), int(height * 0.62), int(width * 0.5), int(height * 1.1)], fill=(255, 255, 255, 20))
    layer = shapes.filter(ImageFilter.GaussianBlur(blur)) if blur else shapes
    Image.alpha_composite(image, layer).convert("RGB").save(path, "JPEG", quality=92)




def make_card_background(path, width, height, color, style="glow"):
    """Ultra-aesthetic, studio-grade card backgrounds:
    - glass: True frosted glassmorphism over vibrant 3D fluid / aurora backdrop with specular chamfer bevel & sheen
    - dark: Minimalist 3D studio cyclorama with overhead conic spotlight and product pedestal
    - light: Warm editorial limestone with architectural window louver gobo sunlight shadows
    - glow: Multi-node vibrant fluid gradient mesh with film grain
    - bold: High-energy carbon stage with sharp brand accent wedges & electric rim
    - festive: Deep royal jewel silk with gold foil filigree border & floating starlight dust
    """
    if style in ("bold", "festive"):   # flat brand-colour looks: the brand colour stays visible and text on it stays readable
        return _legacy_card_background(path, width, height, color, style)
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter

    r, g, b = _hex_rgb(color)
    rng = np.random.default_rng(42)
    bg_dir = Path(__file__).parent / "static" / "media" / "backgrounds"

    def load_or_crop_bg(fname):
        full_path = bg_dir / fname
        if full_path.is_file():
            try:
                with Image.open(full_path) as im:
                    im_aspect = im.width / im.height
                    tgt_aspect = width / height
                    if im_aspect > tgt_aspect:
                        nw = int(im.height * tgt_aspect)
                        off = (im.width - nw) // 2
                        cr = im.crop((off, 0, off + nw, im.height))
                    else:
                        nh = int(im.width / tgt_aspect)
                        off = (im.height - nh) // 2
                        cr = im.crop((0, off, im.width, off + nh))
                    return cr.resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")
            except Exception:
                return None
        return None

    if style == "glass":
        # 1. Base backdrop: high-res 3D fluid silk or procedural chromatic aurora
        base = load_or_crop_bg("3d_fluid_silk.jpg")
        if base is None:
            base = load_or_crop_bg("aurora_mesh_dream.jpg")
        if base is None:
            y, x = np.ogrid[:height, :width]
            cR = 12 + (y / height) * 10
            cG = 14 + (y / height) * 12
            cB = 22 + (y / height) * 18
            cx1, cy1 = width * 0.72, height * 0.38
            d1 = np.sqrt(((x - cx1) / 1.0)**2 + ((y - cy1) / 0.8)**2)
            orb1 = np.exp(-d1 / (width * 0.38))
            cx2, cy2 = width * 0.25, height * 0.72
            d2 = np.sqrt(((x - cx2) / 1.1)**2 + ((y - cy2) / 0.7)**2)
            orb2 = np.exp(-d2 / (width * 0.42))
            R = np.clip(cR + orb1 * (r * 0.75) + orb2 * 120, 0, 255).astype(np.uint8)
            G = np.clip(cG + orb1 * (g * 0.75) + orb2 * 40, 0, 255).astype(np.uint8)
            B = np.clip(cB + orb1 * (b * 0.75) + orb2 * 180, 0, 255).astype(np.uint8)
            base = Image.fromarray(np.stack([R, G, B], axis=-1), mode="RGB").convert("RGBA")

        # 2. True Frosted Glassmorphism
        pad_x, pad_y = int(width * 0.055), int(height * 0.065)
        radius = int(width * 0.05)
        card_box = [pad_x, pad_y, width - pad_x, height - pad_y]

        blur_radius = max(8, int(width * 0.024))
        blurred = base.filter(ImageFilter.GaussianBlur(blur_radius))

        card_mask = Image.new("L", (width, height), 0)
        cmd = ImageDraw.Draw(card_mask)
        cmd.rounded_rectangle(card_box, radius=radius, fill=255)

        glass_composite = Image.composite(blurred, base, card_mask)

        glass_fx = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glass_fx)
        gd.rounded_rectangle(card_box, radius=radius, fill=(255, 255, 255, 26))
        in_p = max(2, int(width * 0.008))
        in_box = [pad_x + in_p, pad_y + in_p, width - pad_x - in_p, height - pad_y - in_p]
        gd.rounded_rectangle(in_box, radius=max(1, radius - in_p), outline=(255, 255, 255, 18), width=1)
        gd.rounded_rectangle(card_box, radius=radius, outline=(255, 255, 255, 110), width=max(2, width // 480))

        shd = ImageDraw.Draw(glass_fx)
        shd.polygon([
            (pad_x, pad_y + int(height * 0.36)),
            (width - pad_x, pad_y + int(height * 0.07)),
            (width - pad_x, pad_y + int(height * 0.21)),
            (pad_x, pad_y + int(height * 0.50))
        ], fill=(255, 255, 255, 18))

        final = Image.alpha_composite(glass_composite, glass_fx)
        final.convert("RGB").save(path, "JPEG", quality=93)
        return

    elif style == "dark":
        # Minimalist 3D Dark Studio Cyclorama with Overhead Conic Spotlight & Product Pedestal
        y, x = np.ogrid[:height, :width]
        horizon = height * 0.68
        wall = 12 + (y / horizon) * 16
        floor = 22 - ((y - horizon) / max(1, height - horizon)) * 10
        canvas = np.where(y < horizon, wall, floor)

        cx = width / 2.0
        cy_spot = height * 0.30
        spot_dist = np.sqrt(((x - cx) / 1.0)**2 + ((y - cy_spot) / 0.68)**2)
        spot = np.exp(-spot_dist / (width * 0.44)) * 90

        glow_dist = np.sqrt(((x - cx) / 1.2)**2 + ((y - horizon * 0.96) / 0.5)**2)
        glow = np.exp(-glow_dist / (width * 0.36))

        R = np.clip(canvas + spot + glow * (r * 0.5), 0, 255)
        G = np.clip(canvas + spot + glow * (g * 0.5), 0, 255)
        B = np.clip(canvas + spot + glow * (b * 0.5), 0, 255)

        noise = rng.normal(0, 1.6, (height, width))
        R = np.clip(R + noise, 0, 255).astype(np.uint8)
        G = np.clip(G + noise, 0, 255).astype(np.uint8)
        B = np.clip(B + noise, 0, 255).astype(np.uint8)

        img = Image.fromarray(np.stack([R, G, B], axis=-1), mode="RGB").convert("RGBA")

        ped_w = int(width * 0.62)
        ped_h = int(height * 0.11)
        ped_x = (width - ped_w) // 2
        ped_y = int(height * 0.66)
        ped_depth = int(height * 0.05)

        draw_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        d = ImageDraw.Draw(draw_layer)

        shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        shadow_box = [ped_x - int(width * 0.06), ped_y + ped_depth - int(height * 0.02),
                      ped_x + ped_w + int(width * 0.06), ped_y + ped_depth + ped_h + int(height * 0.04)]
        sd.ellipse(shadow_box, fill=(0, 0, 0, 170))
        shadow = shadow.filter(ImageFilter.GaussianBlur(width * 0.035))
        img = Image.alpha_composite(img, shadow)

        d.rectangle([ped_x, ped_y + ped_h // 2, ped_x + ped_w, ped_y + ped_h // 2 + ped_depth], fill=(28, 30, 36, 255))
        d.ellipse([ped_x, ped_y + ped_depth, ped_x + ped_w, ped_y + ped_depth + ped_h], fill=(28, 30, 36, 255))

        for i in range(ped_w):
            col_x = ped_x + i
            rel = (i - ped_w / 2) / (ped_w / 2)
            factor = max(0.0, 1.0 - rel**2)
            lum = int(24 + factor * 22)
            d.line([(col_x, ped_y + ped_h // 2), (col_x, ped_y + ped_depth + ped_h // 2)], fill=(lum, lum + 2, lum + 5, 255))

        top_box = [ped_x, ped_y, ped_x + ped_w, ped_y + ped_h]
        d.ellipse(top_box, fill=(42, 45, 52, 255))
        d.ellipse(top_box, outline=(255, 255, 255, 95), width=max(1, width // 540))
        inner_box = [ped_x + int(ped_w * 0.08), ped_y + int(ped_h * 0.08),
                     ped_x + int(ped_w * 0.92), ped_y + int(ped_h * 0.92)]
        d.ellipse(inner_box, outline=(r, g, b, 55), width=max(1, width // 720))

        img = Image.alpha_composite(img, draw_layer)
        img.convert("RGB").save(path, "JPEG", quality=93)
        return

    elif style == "light":
        # Warm Limestone Editorial with Architectural Window Louver Gobo Sunlight Shadows
        y, x = np.ogrid[:height, :width]
        base_lum = 242 - (y / height) * 14 - (x / width) * 10
        noise = rng.normal(0, 2.2, (height, width))
        diag = (x * 0.55 + y * 0.45)
        period = height * 0.22
        slat_phase = (diag % period) / period
        sunlight = np.sin(slat_phase * 2 * np.pi)
        sunlight = np.clip(sunlight * 1.6, -0.6, 1.0)
        sunlight = (sunlight + 0.6) / 1.6
        sun_intensity = sunlight * 24
        R = np.clip(base_lum + sun_intensity + 8 + noise, 0, 255)
        G = np.clip(base_lum + sun_intensity + 4 + noise, 0, 255)
        B = np.clip(base_lum + sun_intensity - 6 + noise, 0, 255)
        cx, cy = width * 0.85, height * 0.15
        d = np.sqrt(((x - cx) / 1.0)**2 + ((y - cy) / 0.8)**2)
        bglow = np.exp(-d / (width * 0.35))
        R = np.clip(R + bglow * (r * 0.12), 0, 255).astype(np.uint8)
        G = np.clip(G + bglow * (g * 0.12), 0, 255).astype(np.uint8)
        B = np.clip(B + bglow * (b * 0.12), 0, 255).astype(np.uint8)
        bg = Image.fromarray(np.stack([R, G, B], axis=-1), mode="RGB").convert("RGBA")
        bg = bg.filter(ImageFilter.GaussianBlur(width * 0.005))

        draw = ImageDraw.Draw(bg)
        m_x, m_y = int(width * 0.04), int(height * 0.03)
        draw.rectangle([m_x, m_y, width - m_x, height - m_y], outline=(r, g, b, 45), width=max(1, width // 540))
        bg.convert("RGB").save(path, "JPEG", quality=93)
        return

    elif style == "bold":
        # High-Energy Kinetic Drop Stage with Saturated Brand Energy Wedges & Carbon Grid
        bg = load_or_crop_bg("cyber_neon_glow.jpg")
        if bg is None:
            bg = Image.new("RGBA", (width, height), (r, g, b, 255))
        else:
            tint = Image.new("RGBA", (width, height), (r, g, b, 120))
            bg = Image.alpha_composite(bg, tint)

        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        dark = (int(r * 0.45), int(g * 0.45), int(b * 0.45), 230)
        od.polygon([(0, int(height * 0.62)), (width, int(height * 0.36)), (width, int(height * 0.58)), (0, int(height * 0.84))], fill=dark)
        od.polygon([(0, int(height * 0.85)), (width, int(height * 0.59)), (width, int(height * 0.64)), (0, int(height * 0.90))], fill=(255, 255, 255, 75))
        od.polygon([(0, 0), (int(width * 0.45), 0), (0, int(height * 0.25))], fill=(255, 255, 255, 30))
        composite = Image.alpha_composite(bg, overlay)
        composite.convert("RGB").save(path, "JPEG", quality=92)
        return

    elif style == "festive":
        # Royal Silk & Gold Foil Filigree
        bg = load_or_crop_bg("royal_gold_festive.jpg")
        if bg is None:
            y, x = np.ogrid[:height, :width]
            top_r, top_g, top_b = int(r * 0.22), int(g * 0.18), int(b * 0.2) + 8
            bot_r, bot_g, bot_b = int(r * 0.72), int(g * 0.52), int(b * 0.46)
            k = y / max(1, height - 1)
            R = (top_r + (bot_r - top_r) * k).astype(np.uint8)
            G = (top_g + (bot_g - top_g) * k).astype(np.uint8)
            B = (top_b + (bot_b - top_b) * k).astype(np.uint8)
            bg = Image.fromarray(np.stack([R, G, B], axis=-1), mode="RGB").convert("RGBA")
        else:
            tint = Image.new("RGBA", (width, height), (r, g, b, 70))
            bg = Image.alpha_composite(bg, tint)

        festive_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        fd = ImageDraw.Draw(festive_layer)
        pad_x1, pad_y1 = int(width * 0.04), int(height * 0.03)
        pad_x2, pad_y2 = int(width * 0.052), int(height * 0.038)
        gold = (233, 185, 73, 170)
        fd.rectangle([pad_x1, pad_y1, width - pad_x1, height - pad_y1], outline=gold, width=max(2, width // 360))
        fd.rectangle([pad_x2, pad_y2, width - pad_x2, height - pad_y2], outline=(233, 185, 73, 90), width=1)
        csz = int(width * 0.02)
        for cx_c, cy_c in [(pad_x1, pad_y1), (width - pad_x1, pad_y1), (pad_x1, height - pad_y1), (width - pad_x1, height - pad_y1)]:
            fd.polygon([(cx_c, cy_c - csz), (cx_c + csz, cy_c), (cx_c, cy_c + csz), (cx_c - csz, cy_c)], fill=(245, 215, 110, 220))

        composite = Image.alpha_composite(bg, festive_layer)
        composite.convert("RGB").save(path, "JPEG", quality=92)
        return

    else:
        # style == "glow" (Modern Fluid Aurora Gradient Mesh)
        bg = load_or_crop_bg("gradient_mesh_vibrant.jpg")
        if bg is None:
            bg = load_or_crop_bg("aurora_mesh_dream.jpg")
        if bg is None:
            y, x = np.ogrid[:height, :width]
            cR = 10 + (y / height) * 14
            cG = 12 + (y / height) * 16
            cB = 24 + (y / height) * 32
            c1x, c1y = width * 0.8, height * 0.25
            d1 = np.sqrt(((x - c1x) / 1.0)**2 + ((y - c1y) / 0.8)**2)
            w1 = np.exp(-d1 / (width * 0.45))
            c2x, c2y = width * 0.2, height * 0.45
            d2 = np.sqrt(((x - c2x) / 0.9)**2 + ((y - c2y) / 0.7)**2)
            w2 = np.exp(-d2 / (width * 0.38))
            c3x, c3y = width * 0.75, height * 0.8
            d3 = np.sqrt(((x - c3x) / 1.1)**2 + ((y - c3y) / 0.9)**2)
            w3 = np.exp(-d3 / (width * 0.48))
            R = cR + w1 * (r * 0.85) + w2 * 30 + w3 * 180
            G = cG + w1 * (g * 0.85) + w2 * 170 + w3 * 40
            B = cB + w1 * (b * 0.85) + w2 * 230 + w3 * 220
            noise = rng.normal(0, 1.8, (height, width))
            R = np.clip(R + noise, 0, 255).astype(np.uint8)
            G = np.clip(G + noise, 0, 255).astype(np.uint8)
            B = np.clip(B + noise, 0, 255).astype(np.uint8)
            bg = Image.fromarray(np.stack([R, G, B], axis=-1), mode="RGB").convert("RGBA")
        else:
            glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow_layer)
            gd.ellipse([int(width * 0.2), int(height * 0.3), int(width * 0.8), int(height * 0.7)], fill=(r, g, b, 70))
            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(width * 0.12))
            bg = Image.alpha_composite(bg, glow_layer)

        bg.convert("RGB").save(path, "JPEG", quality=92)
        return


def make_scrim(path, width, height):
    """A soft dark gradient at the top and bottom so white text stays readable on any photo or clip."""
    from PIL import Image
    column = Image.new("RGBA", (1, height))
    px = column.load()
    for y in range(height):
        k = y / (height - 1)
        alpha = int(150 * max(0.0, (k - 0.45) / 0.55) ** 1.4 + 70 * max(0.0, (0.28 - k) / 0.28) ** 1.4)
        px[0, y] = (0, 0, 0, alpha)
    column.resize((width, height)).save(path)


def make_product_layer(cutout, out_png):
    """Crop the real product cut-out to its pixels and add a soft contact shadow. Product pixels are never changed."""
    from PIL import Image, ImageFilter
    with Image.open(cutout) as image:
        product = image.convert("RGBA")
    box = product.getchannel("A").getbbox()
    if box is None:
        raise AdError("The product cut-out is empty")
    product = product.crop(box)
    w, h = product.size
    pad = int(max(w, h) * 0.12)
    canvas = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    shadow = Image.new("RGBA", product.size, (0, 0, 0, 0))
    shadow.putalpha(product.getchannel("A").point(lambda a: int(a * 0.45)))
    canvas.alpha_composite(shadow, (pad, pad + int(h * 0.04)))
    canvas = canvas.filter(ImageFilter.GaussianBlur(max(2, int(pad * 0.35))))
    canvas.alpha_composite(product, (pad, pad))
    canvas.save(out_png)
    return canvas.size


def _file_stat(path):
    return [path.stat().st_size, int(path.stat().st_mtime)] if path and path.is_file() else None


def scene_captions(scene, timeline):
    """The caption line for a scene. Text cards already show their words, so a caption there would repeat them."""
    return scene["narration"] if timeline["audio"].get("captions") and scene["kind"] != "card" else ""


def scene_hash(scene, timeline, project_dir, is_last):
    source = project_dir / scene["source"] if scene.get("source") else None
    product = project_dir / scene["product"] if scene.get("product") else None
    logo = project_dir / timeline["brand"]["logo"] if is_last and timeline["brand"].get("logo") else None
    captions = scene_captions(scene, timeline)
    key = {"scene": {k: v for k, v in scene.items() if k not in ("narration", "visual_prompt", "label", "purpose")}, "brand": timeline["brand"]["color"],
           "res": [timeline["resolution"], timeline["platform"]], "files": [_file_stat(source), _file_stat(product), _file_stat(logo)],
           "captions": captions, "v": 4}   # v4: Devanagari brand lines and bold-card contrast render differently
    look = timeline.get("look")
    if look and look != DEFAULT_LOOK:   # only then, so ads made before looks existed keep their cached scenes
        key["look"] = look
    return hashlib.sha1(json.dumps(key, sort_keys=True).encode()).hexdigest()[:16]


def render_scene(scene, timeline, project_dir, cache_dir, is_last=False):
    """Render one scene to a silent clip. Returns (path, cache_hit)."""
    width, height = SIZES[(timeline["resolution"], timeline["aspect"])]
    source = (project_dir / scene["source"]) if scene.get("source") else None
    product = (project_dir / scene["product"]) if scene.get("product") else None
    for path, what in ((source, "source"), (product, "product cut-out")):
        if path is not None and not path.is_file():
            raise AdError(f"Scene {scene['id']}: {what} file {path.name} is missing")
    logo = project_dir / timeline["brand"]["logo"] if is_last and timeline["brand"].get("logo") else None
    if logo is not None and not logo.is_file():
        logo = None
    out = cache_dir / f"{scene['id']}_{scene_hash(scene, timeline, project_dir, is_last)}.mp4"
    if out.is_file():
        return out, True
    family, font_file = find_font()
    work = cache_dir / f"work_{scene['id']}"
    shutil.rmtree(work, ignore_errors=True)
    (work / "fonts").mkdir(parents=True)
    shutil.copy(font_file, work / "fonts" / font_file.name)
    hindi = find_devanagari_font()
    if hindi:
        shutil.copy(hindi[1], work / "fonts" / hindi[1].name)
    captions = scene_captions(scene, timeline)
    duration = scene["duration"]
    kind = scene["kind"]
    look = timeline.get("look") or DEFAULT_LOOK
    on_card = kind == "card" or (kind == "product" and source is None)
    text_look = card_look(look, timeline["brand"]["color"]) if on_card else look
    (work / "text.ass").write_text(build_ass(scene, width, height, timeline["brand"]["color"], family, timeline["platform"], captions,
                                             hindi[0] if hindi else None, look=text_look, on_card=on_card), encoding="utf-8")
    scrim_used = bool(scene["text"] or captions) and kind != "card"
    inputs, chain = [], []
    zoom = f"zoompan=z='min(1.0+0.0007*on,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={width}x{height}:fps={FPS}"

    def still(path):
        inputs.extend(["-loop", "1", "-framerate", str(FPS), "-i", str(path.resolve())])

    if kind == "ai_video":
        if source is None:
            raise AdError(f"Scene {scene['id']} has no video yet")
        inputs.extend(["-stream_loop", "-1", "-ss", str(scene["trim_start"]), "-i", str(source.resolve())])
        chain.append(f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps={FPS},setsar=1[base]")
    elif kind == "image":
        still(source)
        chain.append(f"[0:v]split[a][b];[a]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},boxblur=40:6,eq=brightness=-0.12[bg];"
                     f"[b]scale={width}:{height}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,scale={width * 2}:{height * 2},{zoom},setsar=1[base]")
    elif kind in ("ai_image", "card") or (kind == "product" and source is None) or kind == "product":
        if kind == "card" or (kind == "product" and source is None):
            make_card_background(work / "card.jpg", width, height, timeline["brand"]["color"], look["card"])
            still(work / "card.jpg")
        else:
            still(source)
        if kind == "product":
            # Silky 2.5D parallax: upscale background 2x with smooth zoompan downscaled to canvas,
            # while product cutout preserves exact pixels and moves via floating-point overlay expressions
            bg_zoom = f"zoompan=z='min(zoom+0.0008,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={width}x{height}:fps={FPS}"
            chain.append(f"[0:v]scale={width * 2}:{height * 2}:force_original_aspect_ratio=increase,crop={width * 2}:{height * 2},{bg_zoom},setsar=1[bg0]")
            layer_w, layer_h = make_product_layer(product, work / "product.png")
            left, top, right, bottom = safe_area(timeline["platform"], width, height)
            box_w, box_h = (right - left) * 0.86, (bottom - top) * 0.62
            scale = min(box_w / layer_w, box_h / layer_h)
            pw = max(2, int(layer_w * scale) // 2 * 2)
            still(work / "product.png")
            dur = max(1.0, float(duration))
            chain.append(f"[1:v]format=rgba,scale={pw}:-2[prod]")
            chain.append(f"[bg0][prod]overlay=x='(W-w)/2 + 18*sin(2*PI*t/8)':y='(H-h)*0.48 - 12*(t/{dur})':shortest=1,setsar=1[base]")
        else:
            chain.append(f"[0:v]scale={width * 2}:{height * 2}:force_original_aspect_ratio=increase,crop={width * 2}:{height * 2},{zoom},setsar=1[base]")
    else:
        raise AdError(f"Unknown scene kind {kind}")
    last = "base"
    next_input = sum(1 for x in inputs if x == "-i")
    if logo is not None:
        shutil.copy(logo, work / ("logo" + logo.suffix))
        still(work / ("logo" + logo.suffix))
        left, top, right, _ = safe_area(timeline["platform"], width, height)
        chain.append(f"[{next_input}:v]format=rgba,scale=w='min(iw,{int((right - left) * 0.36)})':h=-2,fade=t=in:st=0.15:d=0.4:alpha=1[logo]")
        chain.append(f"[{last}][logo]overlay=x='(W-w)/2':y={top + int(height * 0.02)}:shortest=1[withlogo]")
        last, next_input = "withlogo", next_input + 1
    if scrim_used:
        make_scrim(work / "scrim.png", width, height)
        inputs.extend(["-loop", "1", "-framerate", str(FPS), "-i", "scrim.png"])
        chain.append(f"[{last}][{next_input}:v]overlay=0:0:shortest=1[lit]")
        last = "lit"
    chain.append(f"[{last}]ass=text.ass:fontsdir=fonts,format=yuv420p[v]")
    # ffmpeg runs inside the work folder and the filter graph uses relative names, which keeps Windows drive-letter colons out of it.
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chain), "-map", "[v]", "-an", "-t", str(duration),
           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", str(FPS * 2), "-movflags", "+faststart", f"out_{out.name}"]
    _run(cmd, cwd=work)
    shutil.move(str(work / f"out_{out.name}"), out)
    shutil.rmtree(work, ignore_errors=True)
    return out, False


def build_voice_track(timeline, clips_by_scene, out_wav, cache_dir):
    """One voice track as long as the ad. clips_by_scene maps scene id to a narration audio file. Returns warnings.

    A line starts with its scene and may carry on through the following scenes that have no line of their own,
    so splitting a scene neither cuts its voice-over nor plays it twice."""
    warnings = []
    total = total_duration(timeline)
    starts = scene_starts(timeline)
    scenes = timeline["scenes"]
    narrated = [i for i, s in enumerate(scenes) if clips_by_scene.get(s["id"])]
    inputs, filters = [], []
    for k, i in enumerate(narrated):
        scene = scenes[i]
        clip = clips_by_scene[scene["id"]]
        until = starts[narrated[k + 1]] if k + 1 < len(narrated) else total
        room = max(0.5, until - starts[i] - 0.2)
        length = probe(clip)["duration"]
        vtrim_s = float(scene.get("voice_trim_start") or 0.0)
        vtrim_e = float(scene.get("voice_trim_end") or 0.0)
        trim_filter = f",atrim={vtrim_s}:{vtrim_e},asetpts=PTS-STARTPTS" if vtrim_e > vtrim_s else ""
        clip_dur = (vtrim_e - vtrim_s) if vtrim_e > vtrim_s else length
        tempo = 1.0
        if clip_dur > room:
            tempo = clip_dur / room
            if tempo > 1.3:
                warnings.append(f"Scene {scene['id']}: narration is {clip_dur:.1f}s but only {room:.1f}s is free before the next line, so it was cut. Shorten the line or lengthen the scene.")
                tempo = 1.3
        delay = int(round((starts[i] + 0.1) * 1000))
        speed = f",atempo={tempo:.3f}" if tempo > 1.0 else ""
        filters.append(f"[{len(filters)}:a]aresample=48000,aformat=channel_layouts=mono{trim_filter}{speed},atrim=0:{room:.3f},adelay=delays={delay}:all=1[v{len(filters)}]")
        inputs += ["-i", str(clip)]
    if not inputs:
        _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", str(total), str(out_wav)])
        return warnings
    mixed = "".join(f"[v{n}]" for n in range(len(filters)))
    graph = ";".join(filters) + f";{mixed}amix=inputs={len(filters)}:duration=longest:normalize=0,apad=whole_dur={total}[out]"
    _run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", graph, "-map", "[out]", "-ac", "1", "-t", str(total), str(out_wav)])
    return warnings


def mix_audio(timeline, voice_wav, music_path, out_m4a, cache_dir):
    total = total_duration(timeline)
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if voice_wav is None and music_path is None:
        _run(cmd + ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", str(total), "-c:a", "aac", "-b:a", "160k", str(out_m4a)])
        return
    if voice_wav is not None and music_path is None:
        _run(cmd + ["-i", str(voice_wav), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,apad", "-t", str(total), "-ac", "2", "-c:a", "aac", "-b:a", "160k", str(out_m4a)])
        return
    volume = timeline["audio"]["music_volume"]
    if voice_wav is None:
        _run(cmd + ["-stream_loop", "-1", "-i", str(music_path), "-af", f"volume={volume * 2.5},afade=t=out:st={max(0, total - 1.2)}:d=1.2", "-t", str(total), "-ac", "2", "-c:a", "aac", "-b:a", "160k", str(out_m4a)])
        return
    graph = (f"[1:a]volume={volume},aresample=48000[m];[0:a]loudnorm=I=-16:TP=-1.5:LRA=11,asplit=2[v1][v2];"
             f"[m][v1]sidechaincompress=threshold=0.04:ratio=9:attack=15:release=450[md];[v2][md]amix=inputs=2:duration=first:normalize=0,"
             f"afade=t=out:st={max(0, total - 1.2)}:d=1.2,alimiter=limit=0.92[a]")
    _run(cmd + ["-i", str(voice_wav), "-stream_loop", "-1", "-i", str(music_path), "-filter_complex", graph, "-map", "[a]", "-t", str(total), "-ac", "2", "-c:a", "aac", "-b:a", "160k", str(out_m4a)])


def scene_label(scene):
    if scene["kind"] == "product":
        return "Your real product on an AI background" if scene.get("source") else "Your real product on a designed background"
    return KIND_LABELS[scene["kind"]]


def honest_label(timeline):
    scenes = timeline["scenes"]
    video = sum(1 for s in scenes if s["kind"] == "ai_video")
    images = sum(1 for s in scenes if s["kind"] == "ai_image" or (s["kind"] == "product" and s.get("source")))
    if video == len(scenes):
        return "Every scene is AI-generated video."
    parts = [f"{video} of {len(scenes)} scenes are AI video"]
    if images:
        parts.append(f"{images} use AI images")
    return "; ".join(parts) + ". The rest are your photos, your real product or designed text cards."


def render_timeline(timeline, project_dir, narration_clips=None, music_path=None, out_name="final.mp4"):
    """Render the whole ad. Returns a report with per-scene cache hits, so the UI can say what was re-rendered."""
    timeline = validate_timeline(timeline)
    project_dir = Path(project_dir)
    cache_dir = project_dir / "render_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    clips, report_scenes = [], []
    for index, scene in enumerate(timeline["scenes"]):
        path, hit = render_scene(scene, timeline, project_dir, cache_dir, is_last=index == len(timeline["scenes"]) - 1)
        clips.append(path)
        report_scenes.append({"id": scene["id"], "kind": scene["kind"], "label": scene_label(scene), "cache_hit": hit})
    listing = cache_dir / "scenes.txt"
    listing.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in clips), encoding="utf-8")
    joined = cache_dir / "joined.mp4"
    _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(joined)])
    warnings = []
    voice = None
    if narration_clips:
        voice = cache_dir / "voice.wav"
        warnings += build_voice_track(timeline, narration_clips, voice, cache_dir)
    audio = cache_dir / "audio.m4a"
    mix_audio(timeline, voice, Path(music_path) if music_path else None, audio, cache_dir)
    out = project_dir / out_name
    _run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(joined), "-i", str(audio), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy",
          "-shortest", "-movflags", "+faststart", str(out)])
    facts = probe(out)
    for leftover in (joined, audio, listing, cache_dir / "voice.wav"):
        leftover.unlink(missing_ok=True)
    for leftover in cache_dir.glob("*.ass"):
        leftover.unlink(missing_ok=True)
    for leftover in cache_dir.glob("*_stem.wav"):
        leftover.unlink(missing_ok=True)
    ai_scenes = sum(1 for s in timeline["scenes"] if s["kind"] == "ai_video")
    return {"output": out.name, "facts": facts, "scenes": report_scenes, "warnings": warnings, "lint": lint(timeline),
            "ai_video_scenes": ai_scenes, "scene_count": len(timeline["scenes"]), "honest_label": honest_label(timeline)}


def sweep_cache(root, min_free_gb=3.5, older_than_hours=24, disk_path="/"):
    """When the disk is short, delete cached scene clips and audio stems older than 24h. Returns files removed."""
    import time
    try:
        free_gb = shutil.disk_usage(disk_path).free / 1e9
    except Exception:
        free_gb = 100.0
    if free_gb >= min_free_gb:
        return 0
    cutoff, removed = time.time() - older_than_hours * 3600, 0
    for pattern in ("*/render_cache/*.mp4", "*/render_cache/*.wav", "*/render_cache/*.ass"):
        for clip in Path(root).glob(pattern):
            try:
                if clip.stat().st_mtime < cutoff:
                    clip.unlink(missing_ok=True)
                    removed += 1
            except OSError:
                pass
    return removed


def poster_frame(video, out_jpg, at=0.8):
    _run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(at), "-i", str(video), "-frames:v", "1", "-vf", "scale=320:-2", str(out_jpg)])


# ---------------------------------------------------------------- planning (used when no AI director is available)

def _strip(text):
    return text.replace("*", "")


def plan_timeline(brand, headline="", features=(), cta="", duration_s=15, aspect="9:16", resolution="1080p", color="#18B26B",
                  mode="cards", reference_file=None, copy_plan=None, voice=None, platform=None):
    """A first draft of the ad from plain fields. Every line is editable afterwards."""
    brand = _clean_text(brand)[:60] or "Brand"
    beats = [b for b in (copy_plan or {}).get("beats", []) if str(b).strip()] or [f for f in features if str(f).strip()]
    headline = _clean_text((copy_plan or {}).get("hook") or headline or (beats[0] if beats else f"Meet {brand}"))
    cta = _clean_text((copy_plan or {}).get("cta") or cta or f"Try {brand} today")
    count = max(3, min(8, round(duration_s / 3)))
    each = round(duration_s / count, 2)
    middle = (beats + [f"Why {brand}?", "Simple. Fast. Reliable.", "Made for you", "Loved by customers"])[:count - 2]
    texts = [(headline, "kinetic", "top")] + [(m, ["slide", "wipe", "kinetic", "slide"][i % 4], "center") for i, m in enumerate(middle)]
    t = default_timeline(brand, color, aspect, resolution, platform)
    t["audio"]["voice"] = voice
    visuals = (copy_plan or {}).get("visuals", [])
    for i, (text, style, position) in enumerate(texts[:count - 1]):
        kind = "ai_video" if mode == "ai" else ("image" if reference_file and i in (0, count - 2) else "card")
        source = reference_file if kind == "image" else None
        layers = [{"id": "t1", "text": text, "style": style, "position": position, "start": 0.15, "end": None}]
        if i == 0 and brand.lower() not in text.lower():
            layers.append({"id": "t2", "text": brand, "style": "lower_third", "position": "bottom", "start": 0.4, "end": None})
        t["scenes"].append({"id": f"s{i + 1}", "kind": kind, "source": source, "duration": each, "narration": _strip(text),
                            "visual_prompt": visuals[i] if i < len(visuals) else f"{brand}: {_strip(text)}", "text": layers})
    last_kind = "image" if reference_file and mode != "ai" else ("ai_video" if mode == "ai" else "card")
    t["scenes"].append({"id": f"s{count}", "kind": last_kind, "source": reference_file if last_kind == "image" else None, "duration": each,
                        "narration": cta, "visual_prompt": f"{brand} closing hero shot",
                        "text": [{"id": "t1", "text": brand, "style": "brand", "position": "top" if last_kind == "image" else "center", "start": 0.1, "end": None},
                                 {"id": "t2", "text": cta, "style": "cta", "position": "bottom", "start": 0.7, "end": None}]})
    return validate_timeline(t)
