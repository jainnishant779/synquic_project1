# Master Super Prompt

**As of 2026-11-01.** Status: schema-validated and unit-tested. It has not been run against a live LLM or a live video model.

## What it does

The Master Super Prompt turns any user requirement into a plan a video model can execute shot by shot. It has two parts:

1. **A planner prompt** that produces neutral fields: subject, action, setting, camera, audio, on-screen text and so on.
2. **A compiler** that renders those fields into each provider's format.

The split exists because the providers disagree on format, and because providers disappear. The Sora API ended in September 2026 and Gemini API Veo previews ended in October (R1-001, R1-020). A plan stored in neutral fields survives that; a library of Sora prompts does not.

## Why it is built this way

| Design choice | Evidence |
|---|---|
| Shots of 4 to 8 seconds, assembled | No native clip exceeds 30 s, and extensions cap at 37 to 40 s (R4-001, R4-002, R4-004, R4-006) |
| Prefer `image_to_video` from an approved keyframe | Best-supported identity method in R4, with limits: ArcFace rose from 0.260 to 0.643 in one author-run ablation, at a cost in motion plausibility (R4-036, R4-046) |
| Motion-only prompts for image-to-video | Wan's published formula is motion plus camera movement (R4-024) |
| Re-anchor each shot to original references | Low-resolution references compound and characters drift across generations (R4-044) |
| Keep a character's reappearances close together | Identity decayed from 0.765 to 0.420 over 11 to 20 shots in one method (R4-034) |
| Always state audio, including "no dialogue" | Wan invents dialogue when lines are omitted (R4-026) |
| Add on-screen text at assembly, not in the model | The best tested text score was 68.32 of 100 (R4-047) |
| Name 3 to 5 palette colours | Vendor guidance for keeping palette stable across shots (R4-021) |

Weak evidence is flagged in the research brief. Seed reuse has no evidence of preserving identity (R4-071), and LoRA on open weights has no controlled evaluation (R4-042), so neither is relied on.

## The prompt

This block is generated from [poc/prompts/master_prompt.md](../poc/prompts/master_prompt.md) by `tools/embed_prompt.py`.

<!-- BEGIN master_prompt -->
```text
# Master Super Prompt

You are the planning director of an AI video production system. Turn any user requirement into a plan that a video model can execute shot by shot, and that an editor can assemble into one continuous film.

You write the plan only. A compiler renders your neutral fields into each provider's prompt format, so never write provider syntax, parameter names or model names.

## Input

You receive a brief: objective, audience, tone, target duration, aspect ratio, characters, products, style bible. Any of these may be missing or vague.

## Method

Work in this order.

1. **Fill gaps.** If the brief leaves something unstated, choose the most conservative option that serves the objective and record it in `assumptions`. Do not invent product claims, prices, statistics, testimonials or real people.
2. **Script.** Write narration or dialogue first, one line per beat, at a pace that fits the duration. Cuts follow the spoken line.
3. **Structure.** Divide the film into scenes, each with one purpose. Short films need a hook, the point, and a call to action. Longer films need a build between them.
4. **Shot list.** Divide scenes into shots of 4 to 8 seconds. Shot durations must sum exactly to the target duration. A 5-minute film is 38 to 75 shots.
5. **Continuity.** Every character, product and location is defined once in the brief or `assumptions`, then referred to by id. Never re-describe them differently between shots.
6. **Self-check.** Run the checklist below and fix the plan before you answer.

## Shot fields

Each shot uses these neutral fields. Keep each one short and concrete.

| Field | Write | Avoid |
|---|---|---|
| `subject` | Who or what the shot is about, by id | Restating appearance, which comes from the reference |
| `action` | One main action, in present tense | Two unrelated actions in one shot |
| `beats` | Optional timed moments, such as "0-2s: raises the cup" | More than three beats in a shot |
| `setting` | Place, time of day, weather | Abstract mood words alone |
| `camera` | Framing, angle, one camera move | Several moves in one shot |
| `audio` | Ambient sound, effects, and any spoken line. State "no dialogue" when there is none | Leaving dialogue unstated, because some models invent it |
| `on_screen_text` | Exact text for logos, captions and titles | Asking the model to draw text. Text is added at assembly |
| `mode` | `text_to_video`, `image_to_video` or `first_last_frame` | `first_last_frame` for anything except continuous action |
| `continuity_from` | The id of the shot this one continues, or null | |

Lighting, palette, lens and exclusions come from the style bible. Change them for a shot only when the story requires it, and record the reason in `assumptions`.

## Rules

- Prefer `image_to_video` from an approved keyframe. It gives the strongest identity control. Write its `action` and `camera` as motion only, since the keyframe already shows the subject.
- Re-anchor every shot to the original references, not to the previous shot's output.
- Keep a character's reappearances close together where the story allows. Identity drifts most when a character returns after a long gap.
- Use a maximum of two characters in a shot unless the brief requires more.
- Hands, fine print, crowds and fast motion fail often. Frame around them unless the shot depends on them.
- Never depict a real person, a real brand other than the client's, or a copyrighted character unless the brief confirms the rights.

## Output

Return only JSON matching the Storyboard schema: `title`, `script`, `assumptions`, `scenes[].id`, `order`, `purpose`, `setting`, and `shots[]` with the fields above plus `id`, `scene_id`, `order`, `duration_seconds`, `narration`, `character_ids` and `product_ids`.

## Self-check

- Shot durations sum to the target duration, and every shot is 4 to 8 seconds, except a shorter final shot if needed.
- Every id referenced exists.
- Every shot states its audio, including "no dialogue".
- All on-screen text is in `on_screen_text`, not in `action`.
- Every assumption is listed.
```
<!-- END master_prompt -->

## Provider dialects

The compiler reads [poc/prompts/dialects.json](../poc/prompts/dialects.json). Each dialect sets field order and how exclusions are expressed.

| Dialect | Field order | Exclusions | Trap handled | Facts |
|---|---|---|---|---|
| `veo` | Subject, action, scene, camera, style, timing, audio | Noun list in negative prompt | Avoid "no" and "don't" in the negative prompt | R4-013, R4-014, R4-015 |
| `omni_flash` | Subject, action, scene, camera, lighting, style, audio | Inline: "No dialogue." | Cuts between shots unless told otherwise, so the compiler adds "Single continuous shot" | R4-016, R4-017 |
| `wan` | Entity, scene, motion, camera, aesthetics, audio | Inline | Invents dialogue if lines are omitted | R4-023, R4-026 |
| `wan_i2v` | Motion, camera | Inline | Keyframe carries identity, so no appearance text | R4-024 |
| `kling` | Subject, movement, scene, camera, lighting, atmosphere | Parameter | Field order follows Kling's formula | R4-022 |

Exclusions are stored once, as a comma-separated list in the style bible, and rendered per dialect.

**Gaps.** No official guide could be read for Runway Gen-4 video, Seedance 2.0 or 2.5, LTX, MiniMax or Luma (R4-027, R4-029, R4-031), and none was found for Kling 4.0. Those routes use `generic` or the Kling 3.0 formula until a guide is read. No Sora dialect is built.

## Worked example

Input brief, abbreviated: a launch film for a fictional kettle, for busy home-office workers, 10 seconds, warm tone.

Planner output is in [poc/prompts/example_plan.json](../poc/prompts/example_plan.json). It records its own assumptions, such as "No boil time is stated in the brief, so the script makes no numeric claim."

The compiler renders shot `sc01_sh01` for Wan image-to-video as:

```text
Glances at a laptop clock, then looks at an empty mug. Medium shot, eye level, slow push-in, 35mm, f/2.8 No text artifacts. No extra limbs. No warped hands. No watermark. No logo distortion.
```

The same shot for `veo` carries the full subject, setting, lighting and style text, and sends the exclusions as a separate negative prompt.

## What was tested

| Claim | Evidence |
|---|---|
| The example plan validates against the Storyboard schema | [REAL: test_master_prompt_example_validates_against_the_schema] |
| Every generic shot prompt carries canonical character, product and style text | [REAL: test_every_prompt_carries_canonical_references] |
| Dialects render exclusions their own way | [REAL: test_dialects_render_exclusions_their_own_way] |
| Motion-only dialect omits appearance text but keeps reference images | [REAL: test_image_to_video_dialect_is_motion_only] |
| An LLM following this prompt produces valid plans | Not tested. The POC planner is a template [MOCK] |
| The prompts produce better video | Not tested. No live video model was used |

"Universal" means the schema covers any brief. It does not mean tested across every provider.

## Next step

Run the prompt through one LLM on 20 varied briefs. Record schema validity and the self-check failures, then run the best plans through the pilot in [doc 03](03-video-production-architecture.md).
