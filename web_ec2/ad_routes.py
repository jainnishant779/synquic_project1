"""HTTP routes for the Ad Studio: one prompt in, an ad out, then edit any moment, undo and redo.

Everything that spends money or touches the network (fal.ai, the AI director, text to speech) is passed in as a hook,
so the tests run with fakes. Paid generation needs a spend cap, an explicit confirmation, and either a studio password
or a local request.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

import ad_director
import ad_engine as ae
import ad_templates
from fal_media import FalMediaError
import media_providers
from media_providers import MediaProviders, Speech, _fatal

PROJECT_ID = re.compile(r"^ad_[0-9a-f]{10}$")
ASSET_ID = re.compile(r"^ref_[a-f0-9]{16}$")
FILE_NAME = re.compile(r"^(final_v\d{1,5}\.mp4|posters/[a-z][a-z0-9_]{0,23}\.jpg)$")
LEVELS = {"free": "Free: designed scenes, your photo, animated text", "images": "AI images + your real product (default)",
          "video": "AI images + AI video on 2 key scenes"}
VOICE_CHOICES = {"auto": "Voice-over in the prompt's language", "off": "No voice-over"}
BUSY = ("queued", "planning", "generating", "rendering")
HISTORY_LIMIT = 30


def _env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


class CreateRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=1500)
    platform: str = "reels"
    length_s: int = Field(default=15, ge=6, le=60)
    level: str = "images"
    voice: str = "auto"
    resolution: str = "1080p"
    reference_asset_id: Optional[str] = None
    logo_asset_id: Optional[str] = None
    template_id: Optional[str] = Field(default=None, max_length=48)
    confirm_spend: bool = False


class EstimateRequest(BaseModel):
    level: str = "images"
    length_s: int = Field(default=15, ge=6, le=60)
    has_photo: bool = False
    template_id: Optional[str] = Field(default=None, max_length=48)


class SaveTemplateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=40)
    description: str = Field(default="", max_length=220)
    keep_brand: bool = False


class EditRequest(BaseModel):
    ops: list[dict] = Field(min_length=1, max_length=40)


class InstructRequest(BaseModel):
    at: float = Field(ge=0)
    instruction: str = Field(min_length=1, max_length=400)


class RegenerateRequest(BaseModel):
    visual_prompt: Optional[str] = Field(default=None, max_length=600)
    kind: str = "image"
    confirm_spend: bool = False


def _image_ext(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


def _audio_ext(data):
    if data[:3] == b"ID3" or data[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return ".mp3"
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return ".wav"
    if b"ftyp" in data[:16]:
        return ".m4a"
    return None


def build_router(media_dir, templates, hooks=None, data_dir=None):
    """data_dir holds saved ad templates; keep it outside the public static folder."""
    hooks = hooks or {}
    store = ad_templates.TemplateStore(Path(data_dir or media_dir) / "ad_templates", hooks.get("template_library", ad_templates.LIBRARY))
    if hooks.get("warm_previews"):
        def warm():   # render the gallery previews once in the background, so the first visitor does not wait for them
            for template in store.library_templates()[0] + store.saved():
                try:
                    store.preview(template["id"])
                except Exception:
                    continue
        threading.Thread(target=warm, daemon=True, name="template-previews").start()
    real_key = hooks.get("get_fal_key", lambda: os.environ.get("FAL_KEY", ""))

    def get_key():   # dry run (FAL_DRY_RUN=1): the AI levels run end to end with placeholders and no request leaves the server
        return "dry-run" if media_providers.dry_run() else real_key()

    # The spend ledger and result cache live with the private data, never under the public media folder.
    providers = hooks.get("providers") or MediaProviders(get_key, state_dir=Path(data_dir) / "fal" if data_dir else None)
    speech = hooks.get("speech") or Speech()
    llm = hooks["llm"] if "llm" in hooks else ad_director.llm_from_env()
    cap = _env_float("AD_MAX_SPEND_USD", 3.0)

    ads_dir = Path(media_dir) / "ads"
    references_dir = Path(media_dir) / "references"
    ads_dir.mkdir(parents=True, exist_ok=True)
    router = APIRouter()
    locks, create_gate = {}, threading.Lock()

    # ------------------------------------------------------------ helpers
    def pdir(pid):
        if not PROJECT_ID.match(pid) or not (ads_dir / pid).is_dir():
            raise HTTPException(404, "No such ad")
        return ads_dir / pid

    def read_json(path, default=None):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return default

    def write_json(path, data):
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        for attempt in range(20):   # on Windows a reader holding the file blocks the swap for a moment; Linux never waits here
            try:
                tmp.replace(path)
                return
            except PermissionError:
                if attempt == 19:
                    raise
                time.sleep(0.05)

    def set_status(path, **fields):
        status = read_json(path / "status.json", {})
        status.update(fields, updated=time.time())
        write_json(path / "status.json", status)
        return status

    def spend_allowed(request: Request):
        """Paid calls need a password, or a request that did not come through a proxy from the internet."""
        if os.environ.get("STUDIO_PASSWORD"):
            return True
        local = request.client and request.client.host in ("127.0.0.1", "::1", "testclient")
        return bool(local and not request.headers.get("x-forwarded-for"))

    def lock_of(pid):
        return locks.setdefault(pid, threading.Lock())

    def reference(asset_id):
        if not asset_id:
            return None
        if not ASSET_ID.match(asset_id):
            raise HTTPException(422, "Bad upload id.")
        found = next((references_dir / f"{asset_id}{e}" for e in (".png", ".jpg", ".webp") if (references_dir / f"{asset_id}{e}").is_file()), None)
        if found is None:
            raise HTTPException(422, "That upload was not found. Upload it again.")
        return found

    def find_template(tid):
        """(template, folder) or (None, None); a bad id is the user's mistake, so 422."""
        if not tid:
            return None, None
        try:
            return store.get(tid)
        except (KeyError, ValueError):
            raise HTTPException(422, "That template was not found. Pick another one.") from None

    def estimate(level, length_s, has_photo, template=None):
        s = providers.settings()
        scenes = max(3, min(8, round(length_s / 3)))
        pictures = scenes
        if template is not None:
            scenes = max(2, min(len(template["scenes"]), int(length_s / 1.5)))
            pictures = sum(1 for sc in template["scenes"][:scenes] if sc["visual"] != "card")
        each = length_s / scenes
        items = []
        if has_photo and level != "free":
            items.append(("Product cut-out", s["price_cutout"]))
        if level in ("images", "video") and pictures:
            items.append((f"{pictures} AI images", pictures * (s["price_edit"] if has_photo else s["price_image"])))
        if level == "video":
            seconds = 2 * providers.video_seconds(each)
            items.append((f"{seconds}s of AI video ({s['video_model']})", seconds * s["price_video_per_s"]))
        usd = round(sum(x for _, x in items), 2)
        return {"usd": usd, "items": [{"what": w, "usd": round(x, 3)} for w, x in items], "cap_usd": cap,
                "note": "[ESTIMATE] from list prices; set AD_PRICE_* to match your fal.ai bill." if usd else "No paid call."}

    def state(pid):
        path = pdir(pid)
        status = read_json(path / "status.json", {})
        render_no = status.get("render_no", 0)
        timeline = read_json(path / "timeline.json")
        posters = {s["id"]: f"/api/ads/{pid}/file/posters/{s['id']}.jpg" for s in (timeline or {}).get("scenes", []) if (path / "posters" / f"{s['id']}.jpg").is_file()}
        history, head = status.get("history", []), status.get("head", -1)
        return {"id": pid, "status": status.get("status", "unknown"), "message": status.get("message", ""), "progress": status.get("progress", {}),
                "timeline": timeline, "report": status.get("report"), "notes": status.get("notes", []), "brief": status.get("brief"),
                "level": status.get("level"), "spent_usd": round(status.get("spent_usd", 0.0), 3), "cap_usd": cap,
                "video_url": f"/api/ads/{pid}/file/final_v{render_no}.mp4" if render_no and (path / f"final_v{render_no}.mp4").is_file() else None,
                "render_no": render_no, "posters": posters, "can_undo": head > 0, "can_redo": 0 <= head < len(history) - 1,
                "version": head + 1, "versions": len(history)}

    def narration_clips(path, timeline):
        """Voice-over per scene, cached by provider, language and text. A failure drops the voice and says so; it never stops the render."""
        voice = timeline["audio"].get("voice")
        if not voice:
            return {}, []
        language = voice.split("-", 1)[1] if voice.startswith("auto-") else "en"
        clips, notes, used = {}, [], set()
        for scene in timeline["scenes"]:
            if not scene["narration"].strip():
                continue
            key = hashlib.sha1(f"{Speech.provider()}|{language}|{scene['narration']}".encode()).hexdigest()[:12]
            target = path / f"voice_{key}.mp3"
            if not target.is_file():
                try:
                    used.add(speech.synthesize(scene["narration"], language, target))
                except Exception as error:
                    target.unlink(missing_ok=True)
                    notes.append(f"Voice-over is off: text to speech failed ({type(error).__name__}).")
                    return {}, notes
            clips[scene["id"]] = target
        notes += [f"Voice-over by {u}." for u in sorted(used) if u.startswith("edge")]
        return clips, notes

    def commit(path, timeline, notes=(), snapshot=True, **extra_status):
        """Render, keep the new version, and record it in the undo history."""
        timeline = ae.validate_timeline(timeline)
        for scene in timeline["scenes"]:
            for name in (scene.get("source"), scene.get("product")):
                if name and not (path / name).is_file():
                    raise ae.AdError(f"Scene {scene['id']}: file {name} does not exist in this ad")
        status = read_json(path / "status.json", {})
        render_no = status.get("render_no", 0) + 1
        clips, voice_notes = narration_clips(path, timeline)
        music = path / timeline["audio"]["music"] if timeline["audio"].get("music") else None
        report = ae.render_timeline(timeline, path, narration_clips=clips, music_path=music if music and music.is_file() else None,
                                    out_name=f"final_v{render_no}.mp4")
        (path / "posters").mkdir(exist_ok=True)
        for scene, start in zip(timeline["scenes"], ae.scene_starts(timeline)):
            ae.poster_frame(path / report["output"], path / "posters" / f"{scene['id']}.jpg", at=start + min(1.2, scene["duration"] * 0.5))
        for old in path.glob("final_v*.mp4"):
            if old.name not in (report["output"], f"final_v{render_no - 1}.mp4"):
                old.unlink(missing_ok=True)
        write_json(path / "timeline.json", timeline)
        history, head = status.get("history", []), status.get("head", -1)
        if snapshot:
            history = history[:head + 1]
            number = (max(history) + 1) if history else 1
            (path / "history").mkdir(exist_ok=True)
            write_json(path / "history" / f"v{number}.json", timeline)
            history.append(number)
            for gone in history[:-HISTORY_LIMIT]:
                (path / "history" / f"v{gone}.json").unlink(missing_ok=True)
            history = history[-HISTORY_LIMIT:]
            head = len(history) - 1
        set_status(path, status="done", message="Ready", render_no=render_no, report=report, notes=list(notes) + voice_notes + report["warnings"],
                   history=history, head=head, versions=history, version_ptr=head, **extra_status)

    # ------------------------------------------------------------ generation
    class CapReached(Exception):
        pass

    def generate_visuals(path, timeline, level, photo, notes, spent, fresh=False):
        """Fill every scene that is waiting for a picture. Failures and the cap turn a scene into a designed one, with a note.
        An error that would repeat on every scene (bad key, wrong model, rejected fields, budget) stops all paid calls for this ad.
        fresh=True (regenerate) skips the result cache, because the user asked for a new picture.
        Returns the ids of scenes whose picture failed."""
        s = providers.settings()
        aspect = timeline["aspect"]
        photo_bytes = photo.read_bytes() if photo else None
        stopped = []

        def charge(amount):
            if stopped:
                raise stopped[0]
            if spent[0] + amount > cap + 1e-9:
                raise CapReached()
            spent[0] += amount

        video_stopped = []
        cost = 0.0

        def failed_call(error, amount):
            """A request refused with an error that will repeat stops paid calls for this ad. Such refusals are not charged by
            fal, so they are not counted against the ad either."""
            if isinstance(error, FalMediaError) and _fatal(error):
                if not (stopped and error is stopped[0]):
                    spent[0] = max(0.0, spent[0] - amount)
                if not stopped:
                    stopped.append(error)
                    notes.append(f"Paid pictures stopped for this ad after: {str(error)[:140]}. Nothing more was sent.")

        if photo is not None:
            wants_cutout = level != "free" and any(sc["kind"] == "product" for sc in timeline["scenes"])
            cutout_ok = False
            if wants_cutout:
                try:
                    charge(s["price_cutout"])
                    (path / "cutout.png").write_bytes(providers.remove_background(photo_bytes, fresh=fresh))
                    cutout_ok = True
                except (FalMediaError, CapReached) as error:
                    failed_call(error, s["price_cutout"])
                    notes.append(f"Product cut-out failed ({'spend cap' if isinstance(error, CapReached) else str(error)[:100]}), so your photo is shown as it is.")
            for scene in timeline["scenes"]:
                if scene["kind"] == "product" and not cutout_ok:
                    scene.update(kind="image", source=photo.name, product=None, gen=None)
        total = sum(1 for sc in timeline["scenes"] if sc.get("gen"))
        done, failed = 0, set()
        for index, scene in enumerate(timeline["scenes"]):
            gen = scene.pop("gen", None)
            wants_photo = scene.pop("use_photo", gen == "edit")
            if not gen:
                continue
            # Text sits in the top and bottom bands of the frame (safe zones), so the picture keeps them calm.
            look = (f"{scene['visual_prompt']}. Photorealistic advertising photo, {aspect} frame, main subject in the middle of the frame, "
                    "calm uncluttered areas at the top and bottom, no text, no letters, no logos, no watermark.")
            try:
                if gen == "background":
                    cost = s["price_image"]
                    charge(cost)
                    # The real product cut-out is placed on top, so the picture must not contain a product of its own.
                    image = providers.text_to_image(f"Empty product-photography set with nothing standing in the centre, where a product will be "
                                                    f"placed later: {scene['visual_prompt']}. No product, no bottle, jar, box or package, no text, "
                                                    f"no logos, soft natural light, calm top area, {aspect} frame.", aspect, fresh=fresh)
                    scene["source"] = f"bg_{scene['id']}_{uuid.uuid4().hex[:6]}.jpg"
                    (path / scene["source"]).write_bytes(image)
                else:
                    uses_photo = bool(photo_bytes and (gen == "edit" or (gen == "video" and wants_photo)))
                    cost = s["price_edit"] if uses_photo else s["price_image"]
                    charge(cost)
                    image = providers.edit_with_references(look, [photo_bytes], aspect, fresh=fresh) if uses_photo \
                        else providers.text_to_image(look, aspect, fresh=fresh)
                    scene["kind"], scene["source"] = "ai_image", f"ai_{scene['id']}_{uuid.uuid4().hex[:6]}.jpg"
                    (path / scene["source"]).write_bytes(image)
                    if uses_photo:
                        notes.append(f"Scene {scene['id']}: the AI drew your product from the photo; small details may differ.")
                    if gen == "video" and video_stopped:
                        notes.append(f"Scene {scene['id']}: AI video skipped after an earlier video error; the AI image is used instead.")
                    elif gen == "video":
                        video_cost = providers.video_seconds(scene["duration"]) * s["price_video_per_s"]
                        try:
                            charge(video_cost)
                            clip = providers.image_to_video(image, f"{scene['visual_prompt']}. Smooth, natural camera motion.", scene["duration"],
                                                            "720p" if timeline["resolution"] == "720p" else "1080p", fresh=fresh)
                            scene["kind"], scene["source"] = "ai_video", f"clip_{scene['id']}_{uuid.uuid4().hex[:6]}.mp4"
                            (path / scene["source"]).write_bytes(clip)
                        except (FalMediaError, CapReached) as error:
                            if isinstance(error, media_providers.BudgetReached):
                                failed_call(error, video_cost)   # the budget stops everything
                            elif isinstance(error, FalMediaError) and _fatal(error):
                                video_stopped.append(error)      # a video-model problem must not stop the pictures
                                spent[0] = max(0.0, spent[0] - video_cost)
                            notes.append(f"Scene {scene['id']}: AI video {'skipped at the spend cap' if isinstance(error, CapReached) else 'failed'}; the AI image is used instead.")
            except (FalMediaError, CapReached) as error:
                failed_call(error, cost)
                failed.add(scene["id"])
                if scene["kind"] == "product":
                    scene["source"] = None
                elif photo is not None:
                    scene.update(kind="image", source=photo.name, product=None)
                else:
                    scene.update(kind="card", source=None, product=None)
                reason = "the spend cap was reached" if isinstance(error, CapReached) else f"the picture failed ({str(error)[:100]})"
                notes.append(f"Scene {scene['id']}: {reason}, so a designed scene is used.")
            done += 1
            set_status(path, progress={"done": done, "total": total, "step": f"Picture {done} of {total}"}, spent_usd=round(spent[0], 3))
        for scene in timeline["scenes"]:
            scene.pop("gen", None)
        return failed

    def create_job(pid, req: CreateRequest, photo_src, logo_src, template=None, template_dir=None):
        path = ads_dir / pid
        try:
            set_status(path, status="planning", message="Writing the ad plan", progress={"done": 0, "total": 0})
            photo = logo = None
            saved_brand = (template or {}).get("brand") or {}
            if photo_src is not None:
                photo = path / f"photo{photo_src.suffix}"
                shutil.copy(photo_src, photo)
            if logo_src is None and template_dir is not None and saved_brand.get("logo"):
                logo_src = template_dir / saved_brand["logo"]   # a saved brand template brings its logo along
            if logo_src is not None and logo_src.is_file():
                logo = path / f"logo{logo_src.suffix}"
                shutil.copy(logo_src, logo)
            draft, brief, notes = ad_director.plan_ad(req.prompt, platform=req.platform, length_s=req.length_s, level=req.level,
                                                      has_photo=photo is not None, voice=req.voice, llm=llm, resolution=req.resolution,
                                                      template=template, brand_hint=saved_brand.get("name"))
            if logo is not None:
                draft["brand"]["logo"] = logo.name
            music = (template or {}).get("audio", {}).get("music")
            if template_dir is not None and music and (template_dir / music).is_file():
                shutil.copy(template_dir / music, path / music)
                draft["audio"]["music"] = music
                notes.append("Music comes from the saved template (your own upload): make sure you may use it in ads.")
            ad_director.check_draft(draft)
            set_status(path, status="generating", message="Making the pictures", brief=brief)
            spent = [0.0]
            if req.level == "free":
                for scene in draft["scenes"]:
                    scene["gen"] = None
                    if scene["kind"] == "product":
                        scene.update(kind="image", source=photo.name, product=None)
            generate_visuals(path, draft, req.level, photo, notes, spent)
            set_status(path, status="rendering", message="Rendering the video", spent_usd=round(spent[0], 3))
            commit(path, draft, notes, spent_usd=round(spent[0], 3))
        except Exception as error:  # the UI must always see a final state
            set_status(path, status="failed", message=f"{type(error).__name__}: {str(error)[:240]}")
        finally:
            if create_gate.locked():
                create_gate.release()

    def regenerate_job(pid, sid, prompt, kind):
        path = ads_dir / pid
        with lock_of(pid):
            try:
                status = read_json(path / "status.json", {})
                timeline = read_json(path / "timeline.json")
                scene = next(s for s in timeline["scenes"] if s["id"] == sid)
                if prompt:
                    scene["visual_prompt"] = prompt
                set_status(path, status="generating", message=f"New picture for {sid}", progress={"done": 0, "total": 1})
                before = json.loads(json.dumps(scene))
                scene["gen"] = "background" if scene["kind"] == "product" else ("video" if kind == "video" else "image")
                notes, spent = [], [status.get("spent_usd", 0.0)]
                if generate_visuals(path, timeline, "images", None, notes, spent, fresh=True):
                    # Keep the picture the scene had; a failed regeneration must not replace it with a designed card.
                    timeline["scenes"] = [before if s["id"] == sid else s for s in timeline["scenes"]]
                    set_status(path, status="done", message="The new picture failed, so the old one is kept. " + " ".join(notes)[:200], spent_usd=round(spent[0], 3))
                    return
                set_status(path, status="rendering", message="Rendering", spent_usd=round(spent[0], 3))
                commit(path, timeline, notes, spent_usd=round(spent[0], 3))
            except Exception as error:
                set_status(path, status="done", message=f"Regeneration failed: {type(error).__name__}: {str(error)[:200]}")

    def committed(pid, mutate, notes=()):
        """Run an edit that renders, with the busy checks and error mapping every edit needs."""
        path = pdir(pid)
        if lock_of(pid).locked() or read_json(path / "status.json", {}).get("status") in BUSY:
            raise HTTPException(409, "This ad is still being worked on.")
        with lock_of(pid):
            timeline = read_json(path / "timeline.json")
            if timeline is None:
                raise HTTPException(409, "This ad has no timeline yet.")
            try:
                new = mutate(path, timeline)
                set_status(path, status="rendering", message="Rendering your edit")
                commit(path, new, notes)
            except ae.AdError as error:
                set_status(path, status="done", message=f"Edit refused: {error}")
                raise HTTPException(422, str(error)) from None
            except HTTPException:
                set_status(path, status="done", message="Ready")
                raise
            except Exception as error:
                set_status(path, status="done", message=f"Render failed: {type(error).__name__}")
                raise HTTPException(500, "Rendering failed. Your previous video is unchanged.") from None
        return state(pid)

    # ------------------------------------------------------------ routes
    @router.get("/editor", response_class=HTMLResponse)
    def editor_page(request: Request):
        return templates.TemplateResponse(request, "editor.html", {})

    @router.get("/api/ads/config")
    def config(request: Request):
        s = providers.settings()
        return {"fal_configured": bool(get_key()), "protected": bool(os.environ.get("STUDIO_PASSWORD")), "paid_allowed_here": spend_allowed(request),
                "director": getattr(llm, "describe", "AI director") if llm else None, "tts": Speech.provider(), "video_model": s["video_model"],
                "cap_usd": cap, "levels": LEVELS, "voices": VOICE_CHOICES, "platforms": {k: v["label"] for k, v in ae.PLATFORMS.items()},
                "styles": [x for x in ae.TEXT_STYLES], "positions": list(ae.POSITIONS), "sizes": list(ae.TEXT_SIZES), "kinds": ae.KIND_LABELS,
                "card_styles": list(ae.CARD_STYLES),
                "prices": {k: v for k, v in s.items() if k.startswith("price")},
                "fal_budget": providers.budget() if hasattr(providers, "budget") else None}

    @router.post("/api/ads/estimate")
    def estimate_route(req: EstimateRequest):
        if req.level not in LEVELS:
            raise HTTPException(422, "Unknown level.")
        return estimate(req.level, req.length_s, req.has_photo, find_template(req.template_id)[0])

    # ------------------------------------------------------------ templates
    def template_card(template, kind):
        card = ad_templates.summary(template, kind)
        card["preview_url"] = f"/api/ad-templates/{template['id']}/preview.jpg"
        return card

    @router.get("/api/ad-templates")
    def list_templates():
        library, errors = store.library_templates()
        return {"library": [template_card(t, "library") for t in library], "saved": [template_card(t, "saved") for t in store.saved()],
                "errors": errors}

    @router.get("/api/ad-templates/{tid}")
    def get_template(tid: str):
        template, folder = find_template(tid)
        return template

    @router.get("/api/ad-templates/{tid}/preview.jpg")
    def template_preview(tid: str):
        find_template(tid)
        try:
            return FileResponse(store.preview(tid), media_type="image/jpeg", headers={"Cache-Control": "max-age=300"})
        except ae.AdError as error:
            raise HTTPException(500, f"Preview failed: {str(error)[:160]}") from None

    @router.delete("/api/ad-templates/{tid}")
    def delete_template(tid: str):
        if not ad_templates.SAVED_ID.match(tid):
            raise HTTPException(403, "Library templates are files on the server and cannot be deleted here.")
        try:
            store.delete(tid)
        except KeyError:
            raise HTTPException(404, "No such template") from None
        return {"deleted": tid}

    @router.post("/api/ads/{pid}/save-template")
    def save_template(pid: str, req: SaveTemplateRequest):
        """Keep this ad's structure (scenes, timing, text animation, look) as a template; its lines become the examples."""
        path = pdir(pid)
        timeline = read_json(path / "timeline.json")
        if timeline is None:
            raise HTTPException(409, "This ad has no timeline yet.")
        try:
            template = store.save_from_ad(timeline, path, req.name.strip(), req.description.strip(), req.keep_brand, pid)
        except (ValueError, OSError) as error:
            raise HTTPException(422, f"Could not save the template: {str(error)[:200]}") from None
        return template_card(template, "saved")

    @router.post("/api/ads/upload-reference")
    async def upload_reference(file: UploadFile = File(...)):
        data = await file.read(10 * 1024 * 1024 + 1)
        await file.close()
        if not data:
            raise HTTPException(400, "The image is empty.")
        if len(data) > 10 * 1024 * 1024:
            raise HTTPException(413, "Images must be 10 MB or smaller.")
        ext = _image_ext(data)
        if ext is None:
            raise HTTPException(415, "Upload a PNG, JPEG or WebP image.")
        references_dir.mkdir(parents=True, exist_ok=True)
        asset = f"ref_{uuid.uuid4().hex[:16]}"
        (references_dir / f"{asset}{ext}").write_bytes(data)
        return {"asset_id": asset, "size_bytes": len(data)}

    @router.post("/api/ads/create", status_code=202)
    def create(req: CreateRequest, request: Request, background: BackgroundTasks):
        if req.platform not in ae.PLATFORMS or req.level not in LEVELS or req.resolution not in ("720p", "1080p") or req.voice not in VOICE_CHOICES:
            raise HTTPException(422, "Unsupported platform, level, resolution or voice.")
        photo, logo = reference(req.reference_asset_id), reference(req.logo_asset_id)
        template, template_dir = find_template(req.template_id)
        if req.level != "free":
            quote = estimate(req.level, req.length_s, photo is not None, template)
            if not spend_allowed(request):
                raise HTTPException(403, "Paid AI pictures are locked: set STUDIO_PASSWORD on the server, or run the app on your own machine. The Free level works now.")
            if not get_key():
                raise HTTPException(409, "FAL_KEY is not configured on the server. The Free level works now.")
            if quote["usd"] > cap:
                raise HTTPException(422, f"Estimated ${quote['usd']:.2f} is over the ${cap:.2f} cap. Use a shorter ad, a lower level, or raise AD_MAX_SPEND_USD.")
            if not req.confirm_spend:
                raise HTTPException(402, f"Confirm the spend first: about ${quote['usd']:.2f} [ESTIMATE], cap ${cap:.2f}.")
        if not create_gate.acquire(blocking=False):
            raise HTTPException(409, "Another ad is being made. Wait for it to finish.")
        try:
            ae.sweep_cache(ads_dir)
            pid = f"ad_{uuid.uuid4().hex[:10]}"
            path = ads_dir / pid
            path.mkdir(parents=True)
            set_status(path, status="queued", message="Queued", created=time.time(), render_no=0, level=req.level,
                       request=req.model_dump(exclude={"confirm_spend"}))
        except Exception:
            create_gate.release()
            raise
        background.add_task(create_job, pid, req, photo, logo, template, template_dir)
        return {"id": pid}

    @router.get("/api/ads")
    def list_ads():
        items = []
        for path in sorted(ads_dir.glob("ad_*"), key=lambda p: p.stat().st_mtime, reverse=True)[:30]:
            status = read_json(path / "status.json", {})
            timeline = read_json(path / "timeline.json", {})
            items.append({"id": path.name, "title": timeline.get("title"), "status": status.get("status"), "created": status.get("created")})
        return {"ads": items}

    @router.get("/api/ads/{pid}")
    def get_ad(pid: str):
        return state(pid)

    @router.put("/api/ads/{pid}/timeline")
    def put_timeline(pid: str, body: dict):
        return committed(pid, lambda path, old: body)

    @router.post("/api/ads/{pid}/edit")
    def edit(pid: str, req: EditRequest):
        def mutate(path, timeline):
            for op in req.ops:
                timeline = ae.apply_edit(timeline, op)
            return timeline
        return committed(pid, mutate)

    @router.post("/api/ads/{pid}/instruct")
    def instruct(pid: str, req: InstructRequest):
        """Turn a plain-language request at a moment into edit operations and a diff. Nothing changes until the ops are applied."""
        path = pdir(pid)
        timeline = read_json(path / "timeline.json")
        if timeline is None:
            raise HTTPException(409, "This ad has no timeline yet.")
        try:
            result = ad_director.instruction_to_ops(timeline, req.at, req.instruction, llm)
        except ae.AdError as error:
            raise HTTPException(422, str(error)) from None
        s = providers.settings()
        for paid in result["paid"]:
            scene = next(x for x in timeline["scenes"] if x["id"] == paid["scene"])
            paid["estimated_usd"] = round(s["price_image"] + (providers.video_seconds(scene["duration"]) * s["price_video_per_s"] if paid["kind"] == "video" else 0), 3)
        result["diff_summary"] = "; ".join(result.get("diff", [])) or "No visual changes"
        result["estimated_cost_usd"] = round(sum(p.get("estimated_usd", 0.0) for p in result["paid"]), 3)
        result["pending_patch"] = {"ops": result.get("ops", []), "paid": result.get("paid", [])}
        return result

    def move_head(pid, step):
        """Undo or redo: render the neighbouring saved version. Cached scenes make this quick."""
        path = pdir(pid)
        if lock_of(pid).locked() or read_json(path / "status.json", {}).get("status") in BUSY:
            raise HTTPException(409, "This ad is still being worked on.")
        with lock_of(pid):
            status = read_json(path / "status.json", {})
            history, head = status.get("history", []), status.get("head", -1)
            target = head + step
            if not 0 <= target < len(history):
                raise HTTPException(422, "Nothing to " + ("undo" if step < 0 else "redo"))
            timeline = read_json(path / "history" / f"v{history[target]}.json")
            try:
                commit(path, timeline, snapshot=False)
            except Exception:
                set_status(path, status="done", message="Could not render that version.", head=head)
                raise HTTPException(500, "Could not render that version. The current video is unchanged.") from None
            set_status(path, head=target)
        return state(pid)

    @router.post("/api/ads/{pid}/undo")
    def undo(pid: str):
        return move_head(pid, -1)

    @router.post("/api/ads/{pid}/redo")
    def redo(pid: str):
        return move_head(pid, +1)

    async def read_upload(file, limit, kinds):
        data = await file.read(limit + 1)
        await file.close()
        ext = (_image_ext(data) if kinds == "image" else _audio_ext(data)) if data else None
        if ext is None or len(data) > limit:
            raise HTTPException(415, "Upload a PNG, JPEG or WebP image up to 10 MB." if kinds == "image" else "Upload an MP3, WAV or M4A file up to 20 MB.")
        return data, ext

    @router.post("/api/ads/{pid}/scenes/{sid}/photo")
    async def scene_photo(pid: str, sid: str, file: UploadFile = File(...)):
        data, ext = await read_upload(file, 10 * 1024 * 1024, "image")

        def mutate(path, timeline):
            scene = next((s for s in timeline["scenes"] if s["id"] == sid), None)
            if scene is None:
                raise HTTPException(404, "No such scene")
            name = f"photo_{sid}_{uuid.uuid4().hex[:6]}{ext}"
            (path / name).write_bytes(data)
            scene.update(kind="image", source=name, product=None)
            return timeline
        return committed(pid, mutate)

    @router.post("/api/ads/{pid}/logo")
    async def logo(pid: str, file: UploadFile = File(...)):
        data, ext = await read_upload(file, 10 * 1024 * 1024, "image")

        def mutate(path, timeline):
            name = f"logo_{uuid.uuid4().hex[:6]}{ext}"
            (path / name).write_bytes(data)
            timeline["brand"]["logo"] = name
            return timeline
        return committed(pid, mutate)

    @router.post("/api/ads/{pid}/music")
    async def music(pid: str, file: UploadFile = File(...)):
        data, ext = await read_upload(file, 20 * 1024 * 1024, "audio")

        def mutate(path, timeline):
            name = f"music_{uuid.uuid4().hex[:6]}{ext}"
            (path / name).write_bytes(data)
            timeline["audio"]["music"] = name
            return timeline
        return committed(pid, mutate, notes=["Music is your upload: make sure you have the right to use it in ads."])

    @router.post("/api/ads/{pid}/scenes/{sid}/regenerate", status_code=202)
    def regenerate(pid: str, sid: str, req: RegenerateRequest, request: Request, background: BackgroundTasks):
        path = pdir(pid)
        timeline = read_json(path / "timeline.json")
        scene = next((s for s in (timeline or {}).get("scenes", []) if s["id"] == sid), None)
        if scene is None:
            raise HTTPException(404, "No such scene")
        if req.kind not in ("image", "video"):
            raise HTTPException(422, "kind must be image or video")
        if not spend_allowed(request):
            raise HTTPException(403, "Paid AI pictures are locked: set STUDIO_PASSWORD on the server, or run the app on your own machine.")
        if not get_key():
            raise HTTPException(409, "FAL_KEY is not configured on the server.")
        status = read_json(path / "status.json", {})
        if status.get("status") in BUSY or lock_of(pid).locked():
            raise HTTPException(409, "This ad is still being worked on.")
        s = providers.settings()
        cost = round(s["price_image"] + (providers.video_seconds(scene["duration"]) * s["price_video_per_s"] if req.kind == "video" and scene["kind"] != "product" else 0), 3)
        if status.get("spent_usd", 0.0) + cost > cap:
            raise HTTPException(422, f"This would take the ad's spend to ${status.get('spent_usd', 0.0) + cost:.2f}, over the ${cap:.2f} cap.")
        if not req.confirm_spend:
            raise HTTPException(402, f"Confirm the spend first: about ${cost:.2f} [ESTIMATE].")
        set_status(path, status="queued", message=f"New picture for {sid}")
        background.add_task(regenerate_job, pid, sid, req.visual_prompt, req.kind)
        return {"id": pid, "estimated_usd": cost}

    @router.get("/api/ads/{pid}/file/{name:path}")
    def get_file(pid: str, name: str):
        path = pdir(pid)
        if not FILE_NAME.match(name) or not (path / name).is_file():
            raise HTTPException(404, "No such file")
        return FileResponse(path / name, media_type="video/mp4" if name.endswith(".mp4") else "image/jpeg")

    return router


def install_basic_auth(app):
    """If STUDIO_PASSWORD is set, every request needs it (HTTP Basic, user 'studio'). Without it the app is open, as before."""
    password = os.environ.get("STUDIO_PASSWORD", "")
    if not password:
        return

    @app.middleware("http")
    async def require_password(request: Request, call_next):
        header = request.headers.get("authorization", "")
        ok = False
        if header.lower().startswith("basic "):
            try:
                user, _, given = base64.b64decode(header[6:]).decode("utf-8").partition(":")
                ok = hmac.compare_digest(user, "studio") & hmac.compare_digest(given, password)
            except (ValueError, UnicodeDecodeError):
                ok = False
        if not ok:
            return JSONResponse({"detail": "Password required"}, status_code=401, headers={"WWW-Authenticate": 'Basic realm="Synquic Studio"'})
        return await call_next(request)
