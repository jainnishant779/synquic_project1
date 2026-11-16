# Synquic Ad Studio

FastAPI app with two parts:

- **Ad Studio** at `/editor`: one line about any product (English, Hindi or Hinglish) becomes a finished short ad; then pause anywhere and change what is on screen, by hand or by typing it. Full design, APIs and status: [docs/11-ad-studio-system.md](../docs/11-ad-studio-system.md).
- The older **Model Arena / Video Studio** at `/` (kept; its stock-photo scraping is off by default).

## Modules

| File | Job |
|---|---|
| `ad_director.py` | Prompt to ad plan with an OpenAI-compatible LLM; ad rules fixed in Python; invented numbers and claims flagged; rule-based fallback; typed edit requests turned into edit operations with a diff |
| `ad_engine.py` | Timeline, validation, edit operations (split, colour, size, timing...), platform safe zones, lint, animated text (libass), product layer with parallax, logo, captions, voice and music mix, per-scene render cache |
| `media_providers.py` | fal.ai images, reference edits, Bria cut-out, image-to-video per model; Google / ElevenLabs / edge-tts voice |
| `ad_templates.py` | Ad templates: format checker, library loader, saved templates (from a finished ad, optionally with brand, logo and music), gallery previews; CLI `check` and `preview` |
| `ad_template_library/` | Built-in templates, one JSON file each (42 now); format in its README. New files appear in the gallery without a restart. Card looks glow, dark, light, glass use photo and studio backgrounds from `static/media/backgrounds/` (needs numpy; the photos are not in git and their licence is unconfirmed) |
| `ad_routes.py` | Create (optionally from a template), edit, instruct, undo/redo, uploads, regenerate, save as template, spend cap, paid lock, password |
| `templates/editor.html` | Prompt-first page with the template gallery, timeline with playhead, moment inspector, typed edits, undo/redo, look settings |

## Run locally

1. FFmpeg with libass, a bold font, and for Hindi a Devanagari font (Ubuntu: `ffmpeg fonts-dejavu-core fonts-noto-core`).
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env`. No key is required: without keys the Free level works and plans come from simple rules.
4. `uvicorn main:app --host 127.0.0.1 --port 8000`, then open `http://127.0.0.1:8000/editor`.

Settings are listed in docs/11 (appendix). The most important: `DIRECTOR_*` for the planning LLM, `FAL_KEY` for pictures and video, `TTS_PROVIDER` for voice, `AD_MAX_SPEND_USD` for the cap per ad, and `STUDIO_PASSWORD`, which every public server needs before paid levels unlock.

The NVIDIA API key is a trial key: its terms allow testing, not production ads. Use the platform's Groq, Cerebras or OpenRouter credits for the director in production.

## Tests

```
python tests/test_ad_director.py      # 11: plans, languages, ad rules, claims, typed edits, LLM transport
python tests/test_media_providers.py  # 4: per-model payloads, field-error retry, voice fallback
python tests/test_ad_engine.py        # 22: validation, edits, safe zones, real FFmpeg renders (about 2 minutes)
python tests/test_ad_routes.py        # 14: create/edit/undo/regenerate with fakes, spend cap, password (about 4 minutes)
python tests/test_ad_templates.py     # 21: template format, looks, planning from a template, save/reuse/delete through the routes
python tests/test_spend_guard.py      # 11: fal budget, cache, ledger, timed-out jobs collected not repaid, dry run, schema check
python tests/test_phase_a.py          # 5: safe zones, glass card, moment inspector, voice continues after a split
python ad_templates.py check ad_template_library    # checks every template file
python fal_contract.py check          # every fal request the app makes, checked against fal's published schemas (free)
python fal_contract.py refresh        # download those schemas again (free, no key)
```

Spending on fal.ai: `FAL_BUDGET_USD` (default $5, across all ads) and `AD_MAX_SPEND_USD` (default $3 per ad) cap it; `FAL_DRY_RUN=1`
runs the AI levels end to end with placeholders and sends nothing. The plan for the first paid runs is in
[docs/13-fal-spend-plan.md](../docs/13-fal-spend-plan.md).

More templates can be written by any tool that follows `ad_template_library/README.md`; a ready prompt for Antigravity is in
[docs/12-antigravity-template-prompt.md](../docs/12-antigravity-template-prompt.md). `node tests/ui_templates_test.js <folder>`
drives the gallery in headless Edge (8 checks, passed on 2026-11-16).

Browser test of the editor (headless Edge or Chrome with puppeteer): start the app on port 8765, then `node tests/ui_editor_test.js <screenshot folder>`. It passed 10 of 10 checks three times on 2026-11-16.

No test calls a paid service. The fal request fields are untested live; run one small ad with a key before relying on them.
