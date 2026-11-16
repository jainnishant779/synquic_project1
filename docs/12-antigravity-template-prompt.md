# Prompt: generate more ad templates with Antigravity

Open the `research_synquic` folder in Antigravity and paste the prompt below into the agent. It writes new template files
straight into `web_ec2/ad_template_library/`. The Ad Studio loads every valid file from that folder, so new templates appear
in the editor's gallery without code changes; a broken file is skipped, never fatal.

Change the number (20) or the category list to taste. After the agent finishes, check its work yourself:
`cd web_ec2` then `python ad_templates.py check ad_template_library`, and look at the images in `web_ec2/template_previews/`.

---

```text
You are a senior performance-marketing creative director and a careful engineer. Your job: add 20 new, high-quality,
clearly different video ad TEMPLATES to the Synquic Ad Studio, as JSON files.

## Read first (do not skip)
1. web_ec2/ad_template_library/README.md — the exact JSON format and the rules.
2. web_ec2/ad_templates.py — validate_template() is the source of truth for what is allowed.
3. Three existing templates for the quality bar: web_ec2/ad_template_library/problem_solution.json,
   how_it_works.json and desi_festive.json.
4. The list of existing files in web_ec2/ad_template_library/ — never reuse an existing id or copy an existing structure.

## What a template is
A template fixes an ad's STRUCTURE: scenes, relative timing (weight), picture type per scene (product | lifestyle | card),
text slots (role, animation style, position, size, timing as fractions of the scene, word limit) and the look
(card background glow | dark | light | bold | festive, text colour, highlight colour). It never fixes the WORDS:
for each user prompt an AI writes new lines from each slot's role, max_words and example. So examples show tone
and length only.

## Write these 20 templates (one JSON file each, file name = id + ".json")
Cover these, one template each, every one with its own structure and hook idea:
 1. fashion_drop — new collection drop, fast cuts, bold look
 2. skincare_routine — morning routine in 3 steps, light look
 3. food_craving — close-up food craving, warm glow look
 4. cafe_vibe — a cafe or bakery "your new favourite spot", glow look
 5. fitness_challenge — gym or fitness programme, energetic, dark look with an electric highlight
 6. coaching_results_free — coaching / education: the learning journey, NO marks, ranks or result claims
 7. app_feature_tour — a mobile app: 3 screens / features, light look
 8. b2b_service — a B2B service: problem, how we help, who it is for, book a call, dark look
 9. car_showroom — an automobile or bike showroom visit, dark premium look
10. travel_escape — a travel package or destination, lifestyle heavy, glow look
11. jewellery_wedding — wedding jewellery, festive look with gold highlight
12. eid_greeting — Eid occasion greeting for any brand, festive look
13. holi_colours — Holi occasion, bold look with a bright highlight
14. rakhi_gift — Raksha Bandhan gifting, festive look
15. sale_countdown — a sale or offer: countdown-style labels ("3", "2", "1") and an offer slot (the AI writes a neutral
    line when the user gives no offer), bold look
16. home_decor_before_after — a room "before" and "after" styling, WITHOUT any claims (no "50% bigger" etc.), light look
17. pet_care — pet food or pet care, playful, glow look
18. kids_toys — toys or kids' products, bright bold look, parents as the audience
19. story_30s — a 30-second storytelling ad: character, problem, discovery, change, brand, CTA (6 to 8 scenes)
20. youtube_landscape_15s — a 15-second ad for platform "landscape" (16:9), product demo style

## Quality rules (these make a template good, not just valid)
- Hook: scene 1 has a line that stops the scroll and starts at 0.0. Vary the hook idea across templates:
  a question, a POV line ("POV: ..."), a bold contrast, a countdown, a "Stop scrolling if ...", a surprising fact
  ONLY if it is generic (never a number the user did not give).
- Brand within 3 seconds: a "brand" role line in scene 1, or a lower_third with role "brand" starting about 0.3.
- Last scene: brand + a "cta" style slot at position bottom.
- Pacing: scene weights 1.5 to 4; 4 to 6 scenes for 10 to 20 seconds, 6 to 8 for 30 seconds; 3 scenes for 6 seconds.
- Words: at most 6 words for kinetic, wipe, brand and cta lines; max_words matches the example's length (+1 or +2).
- Mark 1 or 2 key words per line with *stars*.
- Use all three picture types sensibly: "product" for the real product (never centre text on it), "lifestyle" for
  people and places, "card" for words. Free ads turn every scene into a card, so cards must read well on their own.
- Mix animation styles within a template (kinetic, slide, wipe, lower_third, brand, plain, cta); don't use one style everywhere.
- Fixed labels ("1", "02", "Step 2", "Day 1") use role "label", "fixed": true.
- Looks must be readable: light needs dark text (#1B1B1F or similar) and a strong highlight (#E4572E, #D35400, #2457D6);
  dark suits premium (gold #D4AF37) or tech (#4DD4FF); bold suits launches and sales; festive suits occasions.
  Give every template its own "preview_color" (any brand-like hex) so the gallery looks varied.
- "direction" (per scene): one concrete English shot idea for an image model, no brand names, never ask for text,
  letters, logos, labels or watermarks in the picture.
- Examples: realistic ad lines for some invented product, in a mix of English, Hinglish (Latin script) and Hindi
  (Devanagari) across templates. Never real brand names. Never facts a user may not have: no prices, discounts,
  phone numbers, addresses, ratings, reviews, customer counts, awards, medical or financial claims.
- name: up to 40 characters; description: up to 220 characters saying what the ad does and when to pick it; best_for: up to 8 tags.

## How to work
1. Write the files one by one into web_ec2/ad_template_library/.
2. After every 5 files run, from the web_ec2 folder:
       python ad_templates.py check ad_template_library
   Fix every line that starts with ERROR before continuing. Do not change the checker or any .py file to make a file pass.
3. When all 20 pass, render previews (this takes a few minutes; it needs ffmpeg, which is installed):
       python ad_templates.py preview ad_template_library template_previews
   Open each new template's contact sheet template_previews/<id>.jpg and look at it. Fix any template where text is
   hard to read, too long for one or two lines, or two templates look the same. Re-run check and preview after fixes.
4. Do not edit or delete the 10 existing templates or any code. Do not add API keys or call paid services.
5. Finish with a table: id, name, length, scenes, look, the hook idea, and one line on when to use it.
   Also report the final output of the check command.
```
