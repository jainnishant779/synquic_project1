# 13. fal.ai key: what was checked for free, and the plan for the paid runs

As of 2026-11-16. Goal: not one rupee of the fal.ai key spent on a request that was going to fail, be thrown away, or be paid for twice.

## 1. Checked without a key ($0)

| Check | How | Result |
|---|---|---|
| Request fields of every model | fal publishes each model's schema at `https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=<id>` (no key). Saved in `web_ec2/fal_schemas/`. `python fal_contract.py check` builds the exact payloads the app sends and validates them. | 22 of 22 calls match after three fixes (below) |
| Prices | fal model pages, 2026-11-16 | Nano Banana 2.1 1K: $0.040 (text to image), $0.044 (edit with a photo); 2K $0.059 / $0.063. Bria cut-out $0.018. Wan 2.7: $0.10/s at 720p, $0.15/s at 1080p. Kling 4: $0.157/s (720p). Minimax H3: $0.08/s (768p). Seedance 2.5: $0.22/s (480p). Omni Flash about $0.13/s. HeyGen promo ended on 31 Oct: $0.02/s (768p). |
| Whole pipeline | Dry-run mode (`FAL_DRY_RUN=1`) on a staging copy of the live server: real AI director, real render, placeholders instead of AI pictures, nothing sent to fal | 7 test ads (honey, sneakers, billing app, real estate, Hindi dhaba, T-shirt with video, honey with a template) finished. 32 requests that would cost **$1.47** in total, about $0.21 per ad |

Bugs found this way, all fixed before any spend:
1. The default video model id `wan/v2.7/image-to-video` does not exist (404). Correct: `fal-ai/wan/v2.7/image-to-video`.
2. Minimax H3 requires `prompt_expansion_mode`; every call would have been refused.
3. `negative_prompt` was sent to five video models that do not accept it (silently ignored). Now only Wan gets it.
4. Problem scenes sent the user's product photo to the image model, so the AI would have drawn our own product as "the problem" (and paid the dearer edit price). The director now marks `shows_product`, and the photo goes only to scenes that show the product, never to problem scenes. Edits fell from 10 to 5 in the dry run.
5. Product scenes described the product in the background prompt, so the AI would have drawn a second jar or shoe under the real cut-out. Now the director writes only the setting, and the prompt asks for an empty set.
6. Voice lines in "AI decides" ads were too long for their scenes (2 to 3 lines cut per ad). Now at most 1.7 words per second; one cut was left in 7 ads.

Also added: notes that AI pictures of buildings are not the user's project (real estate) and that AI cannot draw an app's screens (apps).

## 2. Guards in the code (`web_ec2/media_providers.py`, `fal_media.py`, `ad_routes.py`)

| Risk | Guard |
|---|---|
| Same request sent twice (re-runs, retries) | Result cache by request hash: the second time costs $0. "Regenerate" deliberately skips it. |
| Job accepted, then a timeout: paid but thrown away, and a retry pays again | The request id is written to the ledger as soon as fal accepts the job; the next identical request collects that job instead of submitting a new one. |
| Download fails after a paid job | Up to 3 download retries; the generation is never resubmitted. |
| A wrong model id, field or key makes every scene fail | First error that will repeat (401/403/404/422, budget, balance) stops all paid calls for that ad. A video-model error stops only the videos. |
| Spending runs away across many ads | `FAL_BUDGET_USD` (default $5) across all ads, from the ledger; raise it on purpose. Plus the per-ad cap `AD_MAX_SPEND_USD` (default $3). |
| Big phone photos | Shrunk to 1536 px (2048 for the cut-out) before upload. |
| Wan at 1080p costs 1.5x | Video at 720p by default (`AD_VIDEO_RESOLUTION`); the ad is upscaled when rendered. |

Ledger: `web_ec2/data/fal/ledger.jsonl` (private folder). Statuses: submitted, completed, pending, failed, rejected (not charged), dry_run. `GET /api/ads/config` shows `fal_budget` (budget, spent, dry run).

Tests: `tests/test_spend_guard.py` (11: cache, budget across restarts, refused calls not counted, download retry, timed-out job collected not resubmitted, dry run, schema check) and the route test for the stop-after-error rule.

## 3. Plan for the paid runs (total under $3, about ₹260)

Run on the server's staging copy bound to 127.0.0.1 (as the dry run did), with `FAL_KEY` set only for that process. The public site stays on the Free level until `STUDIO_PASSWORD` is set.

| Step | What | Budget (`FAL_BUDGET_USD`) | Stop if |
|---|---|---|---|
| 0 | `python fal_contract.py refresh` then `check` (free; schemas can change) | $0 | any FAIL |
| 1 | One 6 s ad, AI-images level, with a real product photo: 1 cut-out + 2 to 3 images | $0.25 | any `rejected` or `failed` line in the ledger; cut-out not transparent; ledger total differs from fal's usage page |
| 2 | The 7 dry-run prompts at the AI-images level, 720p | $2.00 | a fault repeats in two ads; then fix and re-run step 0 |
| 3 | One ad at the AI-video level (Wan 2.7, 720p, one 3 s clip) | $2.50 | the clip changes the product's label or shape |
| 4 | Compare ledger with the fal bill; set `AD_PRICE_*` to the real numbers | - | |

What to look at in every frame: real label intact on product scenes, no second product under the cut-out, text areas calm, no AI text in the picture, lifestyle scenes believable. Record the real cost per ad.

Only after step 4: decide 1K or 2K images ($0.040 vs $0.059), whether a second video model is worth testing, and raise the budget for real use.

## 4. Not verified yet

- fal's real responses (only the published schemas and examples were used).
- Whether fal charges for jobs that fail after acceptance; the ledger counts them, to stay on the safe side.
- Cut-out quality on real phone photos, and how well Nano Banana keeps a product from a reference photo.
- A POST that times out after fal accepted it has no request id, so it cannot be collected; this should be rare.
