# Prompts: better backgrounds, editor UI and templates with Antigravity

Three separate jobs. Run them **one at a time, in this order, each in a fresh Antigravity session**, and send the result for
review before starting the next one:

1. **Part A: card backgrounds** (`web_ec2/ad_engine.py`). Templates in Part B can then use the new looks.
2. **Part B: templates** (`web_ec2/ad_template_library/`).
3. **Part C: editor UI** (`web_ec2/templates/editor.html`).

Why the guard rails: the last Antigravity run (2026-11-16) added good templates and the glass look, but also silenced the
voice after a scene split, cut on-screen lines in mid-phrase, made four looks ignore the brand colour, and depended on
photos of unknown licence. Each prompt below says what may be touched, what may not, and which tests must pass.

Open the `research_synquic` folder in Antigravity and paste one prompt at a time.

---

## Rules shared by all three parts (they are repeated inside each prompt)

- Do not edit: `media_providers.py`, `fal_media.py`, `fal_contract.py`, `fal_schemas/`, `ad_director.py`, `ad_routes.py`,
  `main.py`, the voice and split code in `ad_engine.py` (`build_voice_track`, `apply_edit`), or any existing test assertion.
  New tests may be added; existing ones may not be weakened or deleted.
- No API keys, no paid services, no downloads of images, fonts, music or icons from the internet (their licences do not
  cover use inside our product). Everything is drawn in code or written by hand.
- No new Python packages (Pillow and numpy are installed); no JavaScript frameworks or CDNs.
- Do not deploy, do not run git commands.
- Finish with a list of every changed file and why, plus the exact output of every test command.

---

## Part A prompt: card backgrounds

```text
You are a senior motion designer and a careful Python engineer. Improve and extend the designed card backgrounds of the
Synquic Ad Studio. A "card" is a scene with only text on a designed background; on the free level every scene is a card,
so these backgrounds decide how most ads look.

## Read first
1. web_ec2/ad_engine.py: CARD_STYLES, DEFAULT_LOOK, card_look(), _legacy_card_background(), make_card_background(),
   build_ass() (how text is drawn), scene_hash() (render cache key), safe_area() and PLATFORMS (where text may sit).
2. web_ec2/tests/test_ad_templates.py (look tests) and web_ec2/tests/test_phase_a.py (glass test).
3. web_ec2/ad_template_library/README.md (the "look" block of a template).

## You may change
- make_card_background() and new helper functions next to it in ad_engine.py.
- CARD_STYLES (add names), card_look() (text colour per look and brand colour), the "v" number in scene_hash().
- web_ec2/ad_template_library/README.md (list of looks), new test files, new template JSON files (see step 6).
## You must not change
- Anything else in ad_engine.py (voice, split, render, safe zones), and the files listed below:
  media_providers.py, fal_media.py, fal_contract.py, fal_schemas/, ad_director.py, ad_routes.py, main.py.
  Do not weaken or delete existing tests. No API keys, no paid calls, no internet downloads, no new packages
  (Pillow and numpy are available). No git commands, no deploy.

## Problems to fix in the current looks
1. glow ignores the brand colour: it is the same rainbow photo for every brand. Rebuild it procedurally from the brand
   colour (a soft gradient mesh of the brand colour and 1 or 2 nearby hues, with light grain). No photo files.
2. dark draws an empty pedestal at the bottom. A card has no product, so the pedestal looks unfinished: remove it.
3. glass uses a fixed purple/blue photo. Rebuild it procedurally from the brand colour (blurred brand-coloured shapes behind a
   frosted rounded panel), no photo files.
4. light, bold and festive are fine; keep their character. Do not use files from static/media/backgrounds/ in any look
   (their licence is unknown); every look must be drawn in code.

## New looks to add (add the names to CARD_STYLES)
- "mesh": rich multi-tone gradient mesh from the brand colour, for lifestyle brands
- "paper": warm textured paper with a thin brand-coloured border and corner accents, for food, crafts, local shops
- "neon": near-black with brand-coloured light streaks and glow, for tech, gaming, nightlife; text area stays dark
- "duotone": two flat tones (brand colour and a darker or complementary tone) split by a bold diagonal or curve
- "minimal": one calm brand-tinted colour with a soft vignette, for premium and clean ads
Each new look needs a matching default text colour in card_look() so that text is readable on it.

## Hard requirements (write a test file web_ec2/tests/test_card_looks.py that checks all of them)
For every style in CARD_STYLES and each brand colour #2E7D32, #FFC107, #E53935, #1E88E5, #8E24AA, #FFFFFF, #111111:
a) make_card_background(path, 1080, 1920, colour, style) finishes in under 1.5 seconds.
b) It is deterministic: two calls give identical bytes (use a fixed seed for any noise).
c) Readable: the text colour from card_look({"card": style, "text": DEFAULT text for that look, ...}, colour) has a
   contrast ratio of at least 4.5:1 (WCAG formula) against the average colour of each text band: the top band
   (14% to 35% of the height) and the bottom band (45% to 65%).
d) The brand colour matters: for every style, the images for #2E7D32 and #FFC107 differ by a mean absolute pixel
   difference of more than 12 (on 0..255).
e) For the calm looks (glow, dark, light, glass, mesh, paper, neon, minimal) the text bands are calm: the standard
   deviation of luminance inside each band is under 40, so busy shapes stay at the edges and corners, never behind the
   words. bold, festive and duotone have shapes by design and are exempt from (e), but not from (c).
Bump the "v" in scene_hash() by one, so cached scenes render again with the new looks.

## Steps
1. Write the code. Keep each look in its own small function.
2. Run, from web_ec2:  python tests/test_card_looks.py   and fix until it passes.
3. Make a contact sheet: every style (columns) x the seven colours (rows), each 180x320, saved to
   template_previews/card_looks.jpg. Open it and look at it. Fix anything that looks cheap, muddy or busy behind the text.
4. Update the list of looks in ad_template_library/README.md.
5. tests/test_ad_templates.py requires every look to be used by at least one library template. For each new look, write
   one new template JSON (same rules as the existing ones; read the README) that uses it, and run
   python ad_templates.py check ad_template_library  until there are no errors.
6. Run all of these from web_ec2 and paste their final lines:
       python tests/test_card_looks.py
       python tests/test_ad_templates.py
       python tests/test_phase_a.py
       python tests/test_ad_engine.py
       python ad_templates.py check ad_template_library
7. Report: changed files and why, the contact sheet path, and the test output.
```

---

## Part B prompt: templates

```text
You are a senior performance-marketing creative director and a careful engineer. Add 25 new, high-quality, clearly
different video ad TEMPLATES to the Synquic Ad Studio, as JSON files. They are for small and medium Indian businesses.

## Read first (do not skip)
1. web_ec2/ad_template_library/README.md: the exact JSON format and the rules.
2. web_ec2/ad_templates.py: validate_template() is the source of truth for what is allowed.
3. web_ec2/ad_engine.py: CARD_STYLES (the looks you may use) and PLATFORMS (platform values).
4. Three existing templates for the quality bar: problem_solution.json, how_it_works.json, desi_festive.json.
5. The list of existing files: never reuse an id, a name or a structure.

## Write these 25 templates (file name = id + ".json")
Festivals and seasons:
 1. diwali_offer: Diwali for any shop, festive look, gift or offer slot (neutral line if the user gives no offer)
 2. navratri_garba: Navratri / Garba, bold or festive look, energetic
 3. ganesh_chaturthi: Ganesh Chaturthi greeting for any brand, respectful, festive look
 4. new_year_countdown: Christmas / New Year, countdown labels, glow or neon look
 5. independence_sale: 15 August / 26 January sale, tricolour-free design (no flag imagery), bold look
 6. valentines_gift: Valentine's gifting, warm look
 7. wedding_season: wedding season for clothes, gifts or services, festive look
 8. back_to_school: school supplies or coaching, bright look
Local business:
 9. restaurant_todays_special: restaurant "today's special", food close-ups, paper look
10. salon_makeover: salon or spa, calm premium look
11. kirana_home_delivery: grocery home delivery, practical, WhatsApp order CTA
12. local_service_call: AC repair, plumber, electrician: problem, quick fix, call now
13. grand_opening: a new shop opening: date and place slots the AI fills only from the user's prompt
Ad formats:
14. customer_quote: a customer review layout. The quote slot must say in its example and description that it is used ONLY
    when the user gives a real review; otherwise the AI writes a plain product line (never invent reviews)
15. price_reveal: product, build-up, price reveal slot (neutral line when no price is given), CTA
16. new_arrival: "just in" for fashion, gadgets or books
17. three_tips_listicle: 3 tips related to the product, labels 1/2/3
18. faq_answers: two common questions and short answers, then CTA
19. how_its_made: behind the scenes / how it is made, craft feel
20. whatsapp_order: the whole ad drives to "Order on WhatsApp"
21. event_invite: workshop, webinar or event: what, when, where (from the prompt only), register CTA
22. hiring_post: a job opening: role, what you get, apply CTA
Formats and lengths:
23. feed_square_offer: platform "square" (1:1) product ad, 10 seconds
24. feed_portrait_story: platform "feed" (4:5), 20 seconds, story style
25. long_60s_explainer: a 60-second explainer, 8 to 10 scenes, for a product that needs explaining

## Quality rules
- Hook: scene 1 has a line that stops the scroll and starts at 0.0. Vary the hook idea: a question, "POV: ...", a bold
  contrast, a countdown, "Stop scrolling if ...". Never a number the user did not give.
- Brand within 3 seconds: a "brand" line in scene 1 or a lower_third brand line starting about 0.3.
- Last scene: brand + a "cta" style slot at position bottom.
- Pacing: scene weights 1.5 to 4; 4 to 6 scenes for 10 to 20 s, 6 to 8 for 30 s, 8 to 10 for 60 s, 3 for 6 s.
- Words: at most 6 words for kinetic, wipe, brand and cta lines; max_words matches the example (+1 or +2).
- Voice: the AI writes at most 1.7 spoken words per second of a scene, so do not plan scenes whose message needs more.
- Mark 1 or 2 key words per line with *stars*. Fixed labels ("1", "Step 2") use role "label" and "fixed": true.
- Picture types: "product" for the real product (never centre text on it), "lifestyle" for people and places, "card"
  for words. On the free level every scene becomes a card, so cards must read well alone.
- Mix animation styles within a template. Use the looks in CARD_STYLES, and use each look at least twice across the 25.
- "direction": one concrete English shot idea per scene, no brand names, never text, letters, logos, screens with words
  or watermarks in the picture. For a "product" scene describe only the setting (surface, background, light, props),
  never the product itself, because the real product photo is placed on top.
- Examples: realistic lines for invented products, mixing English, Hinglish (Latin script) and Hindi (Devanagari).
  Never real brand names, never prices, discounts, phone numbers, addresses, ratings, reviews, customer counts, awards,
  medical, financial or result claims.
- Give each template its own preview_color, a name up to 40 characters, a description up to 220 characters and up to 8 tags.

## How to work
1. Write the files into web_ec2/ad_template_library/. After every 5, run from web_ec2:
       python ad_templates.py check ad_template_library
   Fix every ERROR. Never change ad_templates.py, any other .py file, or an existing template to make a file pass.
2. When all pass, render previews:  python ad_templates.py preview ad_template_library template_previews
   Open each new contact sheet template_previews/<id>.jpg. Fix text that is hard to read, too long, or templates that
   look alike. Run check and preview again after fixes.
3. Run  python tests/test_ad_templates.py  and paste the last lines.
4. No API keys, no paid calls, no internet downloads, no git, no deploy. Do not edit or delete existing templates.
5. Finish with a table: id, name, platform, length, scenes, look, hook idea, when to use it; plus the check output.
```

---

## Part C prompt: editor UI

```text
You are a senior product designer and front-end engineer. Make the Synquic Ad Studio editor page clearer, more modern and
pleasant to use, for small business owners in India on phones and laptops. Change only web_ec2/templates/editor.html.

## Read first
1. web_ec2/templates/editor.html: the whole page (HTML, CSS and vanilla JavaScript in one file).
2. web_ec2/ad_routes.py: only to understand the API the page calls (/api/ads/config, /api/ads/estimate, /api/ads/create,
   /api/ads/{id}, /api/ad-templates, edits, instruct, undo/redo, uploads, save-template). Do not change it.
3. web_ec2/tests/ui_editor_test.js and web_ec2/tests/ui_templates_test.js: every element id, class and text these tests use
   must keep working.

## Goals
1. A clear flow at the top: 1 Describe your product, 2 Pick a template (or "AI decides"), 3 Choose level and see the cost,
   4 Make the ad. Then the player, timeline and moment inspector below.
2. Template gallery: filter chips by category (festivals, food, fashion, local business, tech, property, formats), a search
   box, bigger previews, the length and platform on each card, the chosen card clearly highlighted.
3. Cost and safety: the estimate is always visible before a paid level is made; the "I confirm this spend" checkbox stays
   mandatory; when /api/ads/config returns fal_budget, show "AI budget: $spent of $budget used". Never hide a note or warning
   the server returns (claims to check, AI picture notes, voice cuts): show them in a readable list.
4. Progress: show the step and "Picture n of m" while an ad is made.
5. Mobile: works at 360 px wide with no sideways scrolling; buttons at least 44 px tall.
6. Hindi: fonts that show Devanagari (use the system fonts already used or a CSS font stack; do not download fonts).
7. Accessibility: labels for every input, visible focus, text contrast at least 4.5:1, works with the keyboard.

## You must not
- Change any other file except adding new tests. Do not change API calls, request bodies or response handling contracts.
- Remove features: timeline with playhead, pause anywhere, moment inspector, inline text edit, typed edit with diff and apply,
  undo/redo, split, look settings, uploads (photo, logo, music, scene photo), regenerate with confirmation, save as
  template, delete saved template, download.
- Add JavaScript frameworks, CDNs, external fonts, images or icons from the internet. Inline SVG icons drawn by you are fine.
- Add API keys or call paid services. No git, no deploy.

## Check your work
1. Start the app from web_ec2 (no keys needed):  uvicorn main:app --port 8765
2. The UI tests need puppeteer-core and Microsoft Edge. If they are not installed, install puppeteer-core in a folder
   outside the repository (npm install puppeteer-core) and set NODE_PATH to its node_modules. Then run:
       node tests/ui_editor_test.js <a screenshot folder>
       node tests/ui_templates_test.js <a screenshot folder>
   Both must pass every check. If you cannot run them, say so clearly; do not claim they pass.
3. Take screenshots at 1440x900 and 390x844 of: the empty page, the gallery with a filter on, an ad being made, a finished
   ad with the inspector open. Look at each one and fix what looks cluttered or broken.
4. Report: what changed and why, the screenshots' paths, and the full output of both UI tests.
```

---

## After each part

Tell Claude in this repository: "Antigravity ne Part A (or B, C) kar diya". The work is then reviewed (diff, tests,
rendered frames), fixed if needed, and deployed with the usual staging test, backup and rollback.
