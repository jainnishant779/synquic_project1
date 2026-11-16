"""Ad templates: a reusable ad structure (scenes, timing, text slots and their animation, look) that a new prompt fills in.

Two kinds:
- Library templates: one JSON file each in ad_template_library/. Anyone, including another AI tool, can add more; check them with
      python ad_templates.py check ad_template_library
      python ad_templates.py preview ad_template_library <out folder>     (renders a contact sheet and a sample MP4 per template)
- Saved templates: made from a finished ad in the editor ("Save as template"), stored on the server with an optional logo and music.

The format is described in ad_template_library/README.md. A template never holds facts about a product: its example lines only show
tone and length, and the AI director writes new lines for each prompt.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import sys
import threading
import time
import uuid
from pathlib import Path

import ad_engine as ae

LIBRARY = Path(__file__).with_name("ad_template_library")
LIBRARY_ID = re.compile(r"^[a-z][a-z0-9_]{2,40}$")
SAVED_ID = re.compile(r"^tpl_[0-9a-f]{10}$")
PURPOSES = ("hook", "problem", "solution", "reveal", "benefit", "feature", "step", "proof", "offer", "tagline", "location", "brand", "cta")
ROLES = PURPOSES + ("label",)
VISUALS = ("product", "lifestyle", "card")
MAX_SCENES, MAX_SLOTS = 10, 3


class TemplateError(ValueError):
    """A template that breaks the format, with the field path in the message."""


def _hex_or_none(value, where):
    if value in (None, ""):
        return None
    if not ae.HEX.match(str(value)):
        raise TemplateError(f"{where}: colour must look like #FFD84D, not {value!r}")
    return str(value).upper()


def _text(value, where, limit, required=True):
    text = " ".join(str(value or "").replace("{", "").replace("}", "").replace("\\", "").split())
    if required and not text:
        raise TemplateError(f"{where}: must not be empty")
    if len(text) > limit:
        raise TemplateError(f"{where}: at most {limit} characters")
    return text


def _number(value, where, low, high, default=None):
    if value is None and default is not None:
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise TemplateError(f"{where}: must be a number") from None
    if not low <= number <= high:
        raise TemplateError(f"{where}: must be between {low} and {high}")
    return number


def _choice(value, where, options, default=None):
    value = default if value in (None, "") and default is not None else value
    if value not in options:
        raise TemplateError(f"{where}: must be one of {', '.join(options)}, not {value!r}")
    return value


def validate_template(data, saved=False):
    """Return a cleaned copy of a template, or raise TemplateError naming the field that is wrong."""
    if not isinstance(data, dict):
        raise TemplateError("A template must be a JSON object")
    pattern = SAVED_ID if saved else LIBRARY_ID
    tid = str(data.get("id", ""))
    if not pattern.match(tid):
        raise TemplateError(f"id: {'tpl_ and 10 hex characters' if saved else 'lowercase letters, digits and _, 3 to 41 characters, starting with a letter'}, not {tid!r}")
    out = {"id": tid, "name": _text(data.get("name"), "name", 40), "description": _text(data.get("description"), "description", 220),
           "best_for": [], "length_s": int(_number(data.get("length_s"), "length_s", 6, 60)),
           "platform": _choice(data.get("platform"), "platform", tuple(ae.PLATFORMS), "reels")}
    best = data.get("best_for") or []
    if not isinstance(best, list) or len(best) > 8:
        raise TemplateError("best_for: a list of up to 8 short strings")
    out["best_for"] = [_text(b, f"best_for[{i}]", 30) for i, b in enumerate(best)]
    look = data.get("look") or {}
    if not isinstance(look, dict):
        raise TemplateError("look: must be an object")
    out["look"] = {"card": _choice(look.get("card"), "look.card", ae.CARD_STYLES, "glow"),
                   "text": _hex_or_none(look.get("text"), "look.text") or ae.DEFAULT_LOOK["text"],
                   "highlight": _hex_or_none(look.get("highlight"), "look.highlight") or ae.DEFAULT_LOOK["highlight"],
                   "color": _hex_or_none(look.get("color"), "look.color")}
    out["preview_color"] = _hex_or_none(data.get("preview_color"), "preview_color")   # gallery previews only; ads use the brand colour
    audio = data.get("audio") or {}
    if not isinstance(audio, dict):
        raise TemplateError("audio: must be an object")
    out["audio"] = {"music_volume": _number(audio.get("music_volume"), "audio.music_volume", 0, 0.6, 0.16), "captions": bool(audio.get("captions", False)),
                    "voice": bool(audio.get("voice", True))}
    if saved:
        brand = data.get("brand") or {}
        out["brand"] = {"name": _text(brand.get("name"), "brand.name", 60, required=False) or None,
                        "logo": brand.get("logo") if brand.get("logo") in ("logo.png", "logo.jpg", "logo.webp") else None}
        out["audio"]["music"] = audio.get("music") if audio.get("music") in ("music.mp3", "music.wav", "music.m4a") else None
        out["created"] = float(data.get("created") or time.time())
        out["source_ad"] = str(data.get("source_ad") or "")[:20]
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not 2 <= len(scenes) <= MAX_SCENES:
        raise TemplateError(f"scenes: a list of 2 to {MAX_SCENES} scenes")
    out["scenes"] = []
    for i, scene in enumerate(scenes):
        where = f"scenes[{i}]"
        if not isinstance(scene, dict):
            raise TemplateError(f"{where}: must be an object")
        clean = {"purpose": _choice(scene.get("purpose"), f"{where}.purpose", PURPOSES),
                 "visual": _choice(scene.get("visual"), f"{where}.visual", VISUALS),
                 "weight": round(_number(scene.get("weight"), f"{where}.weight", 1, 8), 2),
                 "direction": _text(scene.get("direction"), f"{where}.direction", 300, required=False),
                 "voice": bool(scene.get("voice", True)), "text": []}
        slots = scene.get("text") or []
        if not isinstance(slots, list) or len(slots) > MAX_SLOTS:
            raise TemplateError(f"{where}.text: a list of up to {MAX_SLOTS} text slots")
        for j, slot in enumerate(slots):
            sw = f"{where}.text[{j}]"
            if not isinstance(slot, dict):
                raise TemplateError(f"{sw}: must be an object")
            start = _number(slot.get("start"), f"{sw}.start", 0, 0.9, 0.0)
            end = slot.get("end")
            end = None if end in (None, "") else _number(end, f"{sw}.end", start + 0.1, 1.0)
            clean["text"].append({"role": _choice(slot.get("role"), f"{sw}.role", ROLES), "style": _choice(slot.get("style"), f"{sw}.style", ae.TEXT_STYLES),
                                  "position": _choice(slot.get("position"), f"{sw}.position", ae.POSITIONS, "center"),
                                  "size": _choice(slot.get("size"), f"{sw}.size", tuple(ae.TEXT_SIZES), "m"),
                                  "color": _hex_or_none(slot.get("color"), f"{sw}.color"), "start": round(start, 3), "end": None if end is None else round(end, 3),
                                  "max_words": int(_number(slot.get("max_words"), f"{sw}.max_words", 1, 12, 6)),
                                  "example": _text(slot.get("example"), f"{sw}.example", 90), "fixed": bool(slot.get("fixed", False))})
        out["scenes"].append(clean)
    first, last = out["scenes"][0], out["scenes"][-1]
    if not any(s["start"] <= 0.15 for s in first["text"]):
        raise TemplateError("scenes[0]: the hook needs a text slot that starts at once (start 0 to 0.15)")
    if not any(s["style"] == "cta" for s in last["text"]):
        raise TemplateError("the last scene needs a text slot with style 'cta'")
    for i, scene in enumerate(out["scenes"]):
        for a in range(len(scene["text"])):
            for b in range(a + 1, len(scene["text"])):
                x, y = scene["text"][a], scene["text"][b]
                overlap = x["start"] < (y["end"] or 1.0) and y["start"] < (x["end"] or 1.0)
                if overlap and x["position"] == y["position"] and "caption" not in (x["style"], y["style"]) and "lower_third" not in (x["style"], y["style"]):
                    raise TemplateError(f"scenes[{i}]: text slots {a} and {b} are in the same place at the same time")
            if scene["visual"] == "product" and scene["text"][a]["position"] == "center" and scene["text"][a]["style"] not in ("caption", "lower_third"):
                raise TemplateError(f"scenes[{i}].text[{a}]: centre text would cover the product; use top or bottom")
    return out


def load_library(folder=LIBRARY):
    """(templates, errors). A broken file is reported, never fatal, so one bad template cannot take the studio down."""
    templates, errors, seen = [], [], set()
    for path in sorted(Path(folder).glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            template = validate_template(data)
            if template["id"] != path.stem:
                raise TemplateError(f"id {template['id']!r} must match the file name {path.stem!r}")
            if template["id"] in seen:
                raise TemplateError("the same id is used twice")
            seen.add(template["id"])
            templates.append(template)
        except (OSError, ValueError) as error:
            errors.append(f"{path.name}: {error}")
    return templates, errors


def summary(template, kind):
    return {"id": template["id"], "name": template["name"], "description": template["description"], "best_for": template["best_for"],
            "length_s": template["length_s"], "platform": template["platform"], "look": template["look"], "scenes": len(template["scenes"]),
            "kind": kind, "brand": (template.get("brand") or {}).get("name"), "has_logo": bool((template.get("brand") or {}).get("logo")),
            "has_music": bool(template["audio"].get("music"))}


# ---------------------------------------------------------------- from a finished ad

def _role_of(layer, scene, index, count, brand):
    if layer["style"] == "cta":
        return "cta"
    plain = layer["text"].replace("*", "").strip().lower()
    if layer["style"] == "brand" or (brand and plain == brand.lower()):
        return "brand"
    if index == 0:
        return "hook"
    if re.fullmatch(r"[\W\d]{1,4}", plain):
        return "label"
    purpose = scene.get("purpose") or ""
    return purpose if purpose in PURPOSES else ("cta" if index == count - 1 else "benefit")


def from_timeline(timeline, tid, name, description, keep_brand, source_ad=""):
    """A saved template from a finished ad: same scenes, timing, text animation and look; the ad's own lines become the examples."""
    t = ae.validate_timeline(timeline)
    brand = t["brand"]["name"]
    scenes, count = [], min(len(t["scenes"]), MAX_SCENES)
    chosen = t["scenes"][:count - 1] + t["scenes"][-1:] if len(t["scenes"]) > MAX_SCENES else t["scenes"]
    for index, scene in enumerate(chosen):
        visual = {"product": "product", "image": "product", "card": "card"}.get(scene["kind"], "lifestyle")
        slots = []
        for layer in scene["text"][:MAX_SLOTS]:
            start = round(min(0.9, layer["start"] / scene["duration"]), 3)
            end = None if layer["end"] >= scene["duration"] - 0.05 else round(max(start + 0.1, min(1.0, layer["end"] / scene["duration"])), 3)
            role = _role_of(layer, scene, index, len(chosen), brand)
            position = layer["position"]
            if visual == "product" and position == "center" and layer["style"] not in ("caption", "lower_third"):
                position = "top"
            slots.append({"role": role, "style": layer["style"], "position": position, "size": layer.get("size") or "m", "color": layer.get("color"),
                          "start": start, "end": end, "max_words": max(2, min(12, len(layer["text"].split()) + 2)),
                          "example": layer["text"][:90], "fixed": role == "label"})
        if index == 0 and slots:
            slots[0]["start"] = min(slots[0]["start"], 0.1)
        purpose = scene.get("purpose") if scene.get("purpose") in PURPOSES else ("hook" if index == 0 else "cta" if index == len(chosen) - 1 else "benefit")
        scenes.append({"purpose": purpose, "visual": visual, "weight": round(max(1.0, min(8.0, scene["duration"])), 2),
                       "direction": scene["visual_prompt"][:300], "voice": bool(scene["narration"].strip()), "text": slots})
    if scenes and not scenes[0]["text"]:
        scenes[0]["text"].append({"role": "hook", "style": "kinetic", "position": "top", "size": "m", "color": None, "start": 0.0, "end": None,
                                  "max_words": 6, "example": brand, "fixed": False})
    if not any(s["style"] == "cta" for s in scenes[-1]["text"]):
        if len(scenes[-1]["text"]) >= MAX_SLOTS:
            scenes[-1]["text"].pop()
        scenes[-1]["text"].append({"role": "cta", "style": "cta", "position": "bottom", "size": "m", "color": None, "start": 0.15, "end": None,
                                   "max_words": 4, "example": "Order now", "fixed": False})
    look = dict(t["look"], color=t["brand"]["color"] if keep_brand else None)
    data = {"id": tid, "name": name, "description": description or f"Saved from the ad '{t['title']}'.", "best_for": [],
            "length_s": int(round(min(60, max(6, ae.total_duration(t))))), "platform": t["platform"], "look": look, "preview_color": t["brand"]["color"],
            "audio": {"music_volume": t["audio"]["music_volume"], "captions": t["audio"]["captions"], "voice": bool(t["audio"]["voice"])},
            "brand": {"name": brand if keep_brand else None, "logo": None}, "created": time.time(), "source_ad": source_ad, "scenes": scenes}
    return _repair(data)


def _repair(data):
    """Fix what a real ad may break in the template rules (two lines in one place after edits), instead of refusing to save."""
    for scene in data["scenes"]:
        taken = []
        for slot in scene["text"]:
            if slot["style"] in ("caption", "lower_third"):
                continue
            clash = any(o["position"] == slot["position"] and o["start"] < (slot["end"] or 1.0) and slot["start"] < (o["end"] or 1.0) for o in taken)
            if clash:
                free = [p for p in ("top", "bottom", "center") if not any(o["position"] == p for o in taken)]
                if scene["visual"] == "product":
                    free = [p for p in free if p != "center"]
                if free:
                    slot["position"] = free[0]
                else:
                    scene["text"].remove(slot)
                    continue
            taken.append(slot)
    return data


class TemplateStore:
    """Saved templates on disk: root/<id>/template.json with an optional logo and music file next to it."""

    def __init__(self, root, library=LIBRARY):
        self.root = Path(root)
        self.library = Path(library)
        self.root.mkdir(parents=True, exist_ok=True)
        self.previews = self.root / "_previews"
        self.preview_lock = threading.Lock()

    def library_templates(self):
        return load_library(self.library)

    def saved(self):
        out = []
        for path in sorted(self.root.glob("tpl_*/template.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                out.append(validate_template(json.loads(path.read_text(encoding="utf-8")), saved=True))
            except (OSError, ValueError):
                continue
        return out

    def get(self, tid):
        """(template, folder or None). Raises KeyError if there is no such template."""
        if SAVED_ID.match(tid or ""):
            path = self.root / tid / "template.json"
            if path.is_file():
                return validate_template(json.loads(path.read_text(encoding="utf-8")), saved=True), path.parent
        elif LIBRARY_ID.match(tid or ""):
            for template in load_library(self.library)[0]:
                if template["id"] == tid:
                    return template, None
        raise KeyError(tid)

    def save_from_ad(self, timeline, ad_dir, name, description="", keep_brand=False, source_ad=""):
        tid = f"tpl_{uuid.uuid4().hex[:10]}"
        data = from_timeline(timeline, tid, name, description, keep_brand, source_ad)
        folder = self.root / tid
        folder.mkdir(parents=True)
        try:
            logo = timeline.get("brand", {}).get("logo")
            if keep_brand and logo and (Path(ad_dir) / logo).is_file():
                target = "logo" + Path(logo).suffix.lower().replace(".jpeg", ".jpg")
                shutil.copy(Path(ad_dir) / logo, folder / target)
                data["brand"]["logo"] = target
            music = timeline.get("audio", {}).get("music")
            if music and (Path(ad_dir) / music).is_file():
                target = "music" + Path(music).suffix.lower()
                shutil.copy(Path(ad_dir) / music, folder / target)
                data["audio"]["music"] = target
            data = validate_template(data, saved=True)
            (folder / "template.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        except Exception:
            shutil.rmtree(folder, ignore_errors=True)
            raise
        return data

    def delete(self, tid):
        if not SAVED_ID.match(tid or "") or not (self.root / tid).is_dir():
            raise KeyError(tid)
        shutil.rmtree(self.root / tid)

    def preview(self, tid):
        """A contact sheet (hook, middle and last scene with the example lines), rendered once and cached by the template's content."""
        template, _ = self.get(tid)
        digest = hashlib.sha1(json.dumps(template, sort_keys=True).encode()).hexdigest()[:12]
        out = self.previews / f"{tid}_{digest}.jpg"
        if out.is_file():
            return out
        with self.preview_lock:
            if not out.is_file():
                self.previews.mkdir(parents=True, exist_ok=True)
                for old in self.previews.glob(f"{tid}_*.jpg"):
                    old.unlink(missing_ok=True)
                render_contact_sheet(template, out, self.previews / f"work_{tid}")
        return out


# ---------------------------------------------------------------- previews

def sample_timeline(template, resolution="720p"):
    """The template filled with its own example lines, all scenes as designed cards: what a free ad from it looks like."""
    color = template["look"].get("color") or template.get("preview_color") or "#6C4CF1"
    examples = [slot["example"] for scene in template["scenes"] for slot in scene["text"] if slot["role"] == "brand"]
    brand = (template.get("brand") or {}).get("name") or (examples[0].replace("*", "") if examples else "Your Brand")
    t = ae.default_timeline(brand, color, resolution=resolution, platform=template["platform"])
    t["look"] = {k: template["look"][k] for k in ("card", "text", "highlight")}
    total = sum(s["weight"] for s in template["scenes"])
    for index, scene in enumerate(template["scenes"]):
        duration = round(max(1.0, min(15.0, scene["weight"] * template["length_s"] / total)), 2)
        layers = []
        for number, slot in enumerate(scene["text"], 1):
            layers.append({"id": f"t{number}", "text": slot["example"], "style": slot["style"], "position": slot["position"], "size": slot["size"],
                           "color": slot["color"], "start": round(slot["start"] * duration, 2), "end": None if slot["end"] is None else round(slot["end"] * duration, 2)})
        t["scenes"].append({"id": f"s{index + 1}", "kind": "card", "source": None, "duration": duration, "narration": "", "visual_prompt": scene["direction"],
                            "purpose": scene["purpose"], "text": layers})
    return ae.validate_timeline(t)


def render_contact_sheet(template, out_jpg, work):
    """Three frames side by side: the hook, a middle scene and the last scene, each taken once its text has animated in."""
    from PIL import Image
    t = sample_timeline(template)
    shutil.rmtree(work, ignore_errors=True)
    (work / "cache").mkdir(parents=True)
    try:
        picks = sorted({0, len(t["scenes"]) // 2, len(t["scenes"]) - 1})
        frames = []
        for index in picks:
            scene = t["scenes"][index]
            clip, _ = ae.render_scene(scene, t, work, work / "cache", is_last=index == len(t["scenes"]) - 1)
            last_start = max([layer["start"] for layer in scene["text"]] or [0])
            frame = work / f"f{index}.jpg"
            ae.poster_frame(clip, frame, at=min(scene["duration"] - 0.05, last_start + 0.9))
            with Image.open(frame) as image:
                frames.append(image.convert("RGB").resize((240, int(240 * image.height / image.width))))
        gap = 8
        sheet = Image.new("RGB", (sum(f.width for f in frames) + gap * (len(frames) - 1), max(f.height for f in frames)), (24, 24, 28))
        x = 0
        for frame in frames:
            sheet.paste(frame, (x, 0))
            x += frame.width + gap
        tmp = Path(str(out_jpg) + ".tmp.jpg")
        sheet.save(tmp, "JPEG", quality=86)
        tmp.replace(out_jpg)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _cli(argv):
    if len(argv) < 2 or argv[0] not in ("check", "preview"):
        print(__doc__)
        return 2
    folder = Path(argv[1])
    templates, errors = load_library(folder)
    for template in templates:
        print(f"OK    {template['id']}: {template['name']} ({len(template['scenes'])} scenes, {template['length_s']}s, look {template['look']['card']})")
    for error in errors:
        print(f"ERROR {error}")
    if argv[0] == "preview" and templates:
        out = Path(argv[2] if len(argv) > 2 else "template_previews")
        out.mkdir(parents=True, exist_ok=True)
        for template in templates:
            render_contact_sheet(template, out / f"{template['id']}.jpg", out / f"work_{template['id']}")
            sample = sample_timeline(template)
            project = out / f"work_{template['id']}_mp4"
            shutil.rmtree(project, ignore_errors=True)
            project.mkdir()
            report = ae.render_timeline(sample, project, out_name="sample.mp4")
            shutil.move(project / report["output"], out / f"{template['id']}.mp4")
            shutil.rmtree(project, ignore_errors=True)
            print(f"PREVIEW {out / (template['id'] + '.jpg')} and .mp4 | tips: {'; '.join(report.get('lint') or []) or 'none'}")
    print(f"{len(templates)} valid, {len(errors)} with errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
