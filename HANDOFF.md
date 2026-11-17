# Handoff: Synquic Ad Studio and research

As of 2026-11-16. For whoever continues this work.

## What this is

1. **Research** for two tasks: an AI video ad engine (Task 1) and Social 360 (Task 2). Findings and decisions are in `docs/` (start with `docs/10-model-and-tool-decision.md`), facts with sources in `research/facts.csv`, diagrams in `diagrams/`. Reports for the manager are the `.docx`/`.pdf` files in `docs/`.
2. **Ad Studio** (`web_ec2/`): type one line about any product (English, Hindi or Hinglish) and get a short social video ad; pause at any second and change what is on screen, by hand or by typing. Live at http://13.205.82.99/editor. Design and APIs: `docs/11-ad-studio-system.md`. Run and test: `web_ec2/README.md`.

## State

| Part | State |
|---|---|
| Free level (designed cards, animated text, voice-over, music, 72 templates, 11 card looks drawn from the brand colour) | Live and working since 2026-11-17 |
| AI director (plans ads, understands typed edits) | Live: OpenRouter `google/gemma-4-31b-it`, under $0.01 per ad |
| AI images, product cut-out, AI video (fal.ai) | Code ready and checked against fal's published schemas; no paid call made yet (no key) |
| Spend guards (budget, cache, ledger, stop after a repeating error, dry run) | Live since 2026-11-17 (still no fal key on the server, so paid levels answer 409) |
| Voice | Silence that text-to-speech adds around each line is cut, and the director writes 2.4 words per second of a scene, so a 15 s ad has about 2 to 3 s of silence instead of 5 to 7 s |
| Text on screen | Long single words (brand names) are shrunk to fit the safe width instead of running off the frame |
| Voice | edge-tts (free, test quality only) |
| Music | the user's own upload only |
| Tests | `web_ec2/tests/`: director 11, providers 4, spend guard 11, templates 21, phase A 5, engine 22, routes 15 |

## Next steps, in order

1. **Before buying fal credit:** follow `docs/13-fal-spend-plan.md`. Everything that could be checked for free has been: schemas, prices, and a full dry run of 7 ads ($1.47 would-be cost). The paid plan has 4 steps, under $3 in total, with stop rules.
2. **Card looks without a key:** the glow look ignores the brand colour (it uses a fixed rainbow photo); the dark look's plinth sits below where the product layer floats; check text contrast on every look and brand colour.
3. **Production:** Google Chirp 3 HD voice; a music licence that allows customers' paid ads (Epidemic Sound Partner API); set `STUDIO_PASSWORD` before any key goes on the public server; grow the server disk (91% full).
4. **Pilot** with 2 or 3 brands.

## Decisions already taken

- Voice-over language = the prompt's language.
- NVIDIA API trial key: testing only (its terms forbid production use).
- Real product pixels are never redrawn: the product is cut out and layered over AI backgrounds. AI video only on hook/lifestyle scenes.
- Each paid ad needs an explicit spend confirmation; per-ad cap $3, total fal budget $5 until raised on purpose.

## Open risks

- **Keys:** an NVIDIA key was hard-coded in `tools/test_nvidia_models.py` (now read from the environment; it never reached git). Revoke it. The OpenRouter key was pasted in a chat: rotate it and set a $5 to $10 limit. Keys belong only in the server `.env` or Kaggle Secrets, never in the repo.
- **Background photos** for the glow, light and glass looks (`web_ec2/static/media/backgrounds/`, not in git) have an unknown licence. Confirm it before customers' paid ads.
- **Real estate and app ads:** AI pictures are illustrations, not the real project or app screens. The studio says so in a note; users should upload their own photos and screenshots.
- **Disk:** the server is 91% full; renders will fail once it fills.

## Deploying to the server

Always: copy the changed files to a staging folder, run a staging copy on a spare local port and make a test ad, back up the live files to `/home/ubuntu/synquic_backups/`, copy, restart the `synquic` service, check `/editor`, `/api/ads/config`, `/api/ad-templates` and `/` return 200, and roll back automatically if not. The last backups: `pre_templates_20261116_065534` and `pre_glass_templates_20261116_102937`. Server access details are kept outside this repository.
