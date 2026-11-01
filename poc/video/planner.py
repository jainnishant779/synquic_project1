"""Brief to storyboard. Planning sits behind PlannerLLM; the default is deterministic and offline.

MockPlannerLLM is a template, not a language model. compile_shot_prompts is real and is what
carries canonical character, product and style references into every shot.
"""
import json
import math
from pathlib import Path
from typing import Protocol

from .schemas import Brief, Scene, Shot, Storyboard

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
MASTER_PROMPT = PROMPTS_DIR / "master_prompt.md"
DIALECTS = PROMPTS_DIR / "dialects.json"

BEATS = [
    ("hook", "Open on the moment that stops the scroll", "slow push-in, eye level"),
    ("problem", "Show the everyday friction the audience recognises", "handheld medium shot"),
    ("turn", "Introduce the idea that changes the situation", "smooth dolly right"),
    ("proof", "Show the result in use", "close-up, shallow depth of field"),
    ("payoff", "Show the benefit paying off for the audience", "wide tracking shot"),
    ("call_to_action", "Close on the takeaway and next step", "locked-off hero shot"),
]


class PlannerLLM(Protocol):
    def plan(self, brief: Brief, master_prompt: str) -> Storyboard: ...


class MockPlannerLLM:
    """Deterministic stand-in so the pipeline runs with no key and no spend."""

    def plan(self, brief: Brief, master_prompt: str) -> Storyboard:
        shot_count = math.ceil(brief.duration_seconds / brief.shot_seconds)
        scene_count = math.ceil(shot_count / brief.shots_per_scene)
        character_ids = [c.id for c in brief.characters]
        product_ids = [p.id for p in brief.products]
        scenes, script, previous, remaining = [], [], None, brief.duration_seconds

        for scene_index in range(scene_count):
            beat, purpose, camera = BEATS[min(scene_index * len(BEATS) // scene_count, len(BEATS) - 1)]
            scene_id = f"sc{scene_index + 1:02d}"
            setting = f"{brief.title} setting, {beat} beat"
            shots = []
            for shot_index in range(brief.shots_per_scene):
                if remaining <= 0:
                    break
                duration = min(brief.shot_seconds, remaining)
                remaining -= duration
                order = scene_index * brief.shots_per_scene + shot_index + 1
                narration = f"{purpose} for {brief.audience}, part {shot_index + 1}."
                script.append(narration)
                shot = Shot(
                    id=f"{scene_id}_sh{shot_index + 1:02d}", scene_id=scene_id, order=order,
                    duration_seconds=duration, subject=brief.objective, action=purpose,
                    setting=setting, camera=camera, narration=narration,
                    character_ids=character_ids, product_ids=product_ids, continuity_from=previous,
                )
                shots.append(shot)
                previous = shot.id
            scenes.append(Scene(id=scene_id, order=scene_index + 1, purpose=purpose, setting=setting, shots=shots))
        return Storyboard(title=brief.title, script=script, scenes=scenes)


def load_dialect(name: str = "generic") -> dict:
    return json.loads(DIALECTS.read_text(encoding="utf-8"))[name]


def compile_shot_prompts(storyboard: Storyboard, brief: Brief, dialect: dict) -> Storyboard:
    """Fill each shot's prompt from canonical references, in the provider's field order."""
    characters = {c.id: c for c in brief.characters}
    products = {p.id: p for p in brief.products}
    style = brief.style
    for shot in storyboard.shots:
        cast = [characters[i] for i in shot.character_ids]
        items = [products[i] for i in shot.product_ids]
        fields = {
            "subject": shot.subject,
            "characters": "; ".join(f"{c.name}: {c.canonical_description}, {c.wardrobe}".rstrip(", ") for c in cast),
            "products": "; ".join(f"{p.name}: {p.canonical_description}" for p in items),
            "action": shot.action,
            "setting": shot.setting,
            "camera": f"{shot.camera}, {style.lens}",
            "lighting": style.lighting,
            "style": f"{style.visual_style}, palette {style.palette}",
            "continuity": f"continues directly from {shot.continuity_from}" if shot.continuity_from else "",
        }
        shot.prompt = dialect["separator"].join(fields[k] for k in dialect["field_order"] if fields.get(k))
        shot.negative_prompt = style.negative
        shot.reference_images = [
            image for owner in (*cast, *items) for image in owner.reference_images
        ]
    return storyboard


def build_storyboard(brief: Brief, llm: PlannerLLM | None = None, dialect_name: str = "generic") -> Storyboard:
    master_prompt = MASTER_PROMPT.read_text(encoding="utf-8")
    storyboard = (llm or MockPlannerLLM()).plan(brief, master_prompt)
    return compile_shot_prompts(storyboard, brief, load_dialect(dialect_name))
