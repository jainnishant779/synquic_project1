"""Data model for the video pipeline: brief, storyboard, scenes, shots and continuity references."""
from typing import Literal

from pydantic import BaseModel, Field


class VideoSpec(BaseModel):
    width: int = 640
    height: int = 360
    fps: int = 24


class CharacterProfile(BaseModel):
    id: str
    name: str
    canonical_description: str
    wardrobe: str = ""
    reference_images: list[str] = Field(default_factory=list)


class ProductReference(BaseModel):
    id: str
    name: str
    canonical_description: str
    reference_images: list[str] = Field(default_factory=list)


class StyleBible(BaseModel):
    visual_style: str
    palette: str
    lighting: str
    lens: str
    negative: str = "text artifacts, extra limbs, warped hands, watermark, logo distortion"


class Brief(BaseModel):
    title: str
    objective: str
    audience: str
    tone: str
    duration_seconds: int = Field(gt=0)
    shot_seconds: int = Field(default=5, gt=0)
    shots_per_scene: int = Field(default=4, gt=0)
    characters: list[CharacterProfile] = Field(default_factory=list)
    products: list[ProductReference] = Field(default_factory=list)
    style: StyleBible
    spec: VideoSpec = Field(default_factory=VideoSpec)


class Shot(BaseModel):
    id: str
    scene_id: str
    order: int
    duration_seconds: int
    subject: str
    action: str
    setting: str
    camera: str
    narration: str
    audio: str = "ambient room tone, no dialogue"
    beats: list[str] = Field(default_factory=list)
    on_screen_text: list[str] = Field(default_factory=list)
    mode: Literal["text_to_video", "image_to_video", "first_last_frame"] = "image_to_video"
    character_ids: list[str] = Field(default_factory=list)
    product_ids: list[str] = Field(default_factory=list)
    continuity_from: str | None = None
    prompt: str = ""
    negative_prompt: str = ""
    reference_images: list[str] = Field(default_factory=list)


class Scene(BaseModel):
    id: str
    order: int
    purpose: str
    setting: str
    shots: list[Shot]


class Storyboard(BaseModel):
    title: str
    script: list[str]
    assumptions: list[str] = Field(default_factory=list)
    scenes: list[Scene]

    @property
    def shots(self) -> list[Shot]:
        return [shot for scene in self.scenes for shot in scene.shots]
