# Ad template library

Each `.json` file in this folder is one ad template. The Ad Studio loads every valid file at request time, so a new file shows up in
the editor's template gallery without a restart. A broken file is skipped and reported; it never stops the studio.

A template fixes the **structure** of an ad: how many scenes, how long each is relative to the others, what kind of picture each
scene has, which text lines appear, with which animation, where, how big and when, and the colour theme. It never fixes the
**words**: for every new prompt the AI director writes fresh lines in the prompt's language, using each line's `role`, `max_words`
and `example` only as a guide to tone and length.

Check files before using them:

```
python ad_templates.py check ad_template_library
python ad_templates.py preview ad_template_library template_previews   # contact sheet JPG + sample MP4 per template
```

## Format

```json
{
  "id": "problem_solution",            // must equal the file name without .json; a-z, 0-9, _; starts with a letter; 3 to 41 chars
  "name": "Problem to solution",       // up to 40 characters, shown in the gallery
  "description": "...",                // up to 220 characters: what the ad does and when to pick it
  "best_for": ["skincare", "home care"],  // up to 8 short tags
  "length_s": 15,                      // default length in seconds, 6 to 60 (the user can change it; scenes scale)
  "platform": "reels",                 // reels | tiktok | shorts | feed | square | landscape
  "look": {
    "card": "glow",                    // background of designed text cards: glow | dark | light | bold | festive | glass | mesh | paper | neon | duotone | minimal
    "text": "#FFFFFF",                 // default text colour on those cards (use a dark colour with "light")
    "highlight": "#FFD84D",            // colour of *starred* words and of the call-to-action button
    "color": null                      // null = the brand's colour chosen per ad; a hex fixes the colour for every ad
  },
  "preview_color": "#0E9F8A",          // optional: brand colour used only for the gallery preview, so templates look distinct
  "audio": { "music_volume": 0.16, "captions": false, "voice": true },
  "scenes": [                          // 2 to 10 scenes
    {
      "purpose": "hook",               // hook | problem | solution | reveal | benefit | feature | step | proof | offer | tagline | location | brand | cta
      "visual": "lifestyle",           // product (the real product photo over an AI background) | lifestyle (AI photo of people or a setting) | card (designed text card)
      "weight": 2.5,                   // relative length, 1 to 8 (seconds at the default length is a good habit)
      "direction": "A person frustrated by the problem the product solves, candid, natural light",  // shot idea in English, no brand names, no text in the picture
      "voice": true,                   // a voice-over line for this scene
      "text": [                        // 0 to 3 text slots
        {
          "role": "hook",              // a purpose above, or "label" for a short fixed tag such as "1", "Step 2", "NEW"
          "style": "kinetic",          // kinetic | slide | wipe | lower_third | cta | brand | plain | caption
          "position": "top",           // top | center | bottom
          "size": "l",                 // s | m | l | xl
          "color": null,               // null = the look's colour; or a hex for this line only
          "start": 0.0,                // when the line appears, as a fraction of the scene (0 to 0.9)
          "end": null,                 // when it leaves, as a fraction (start + 0.1 to 1), or null = until the scene ends
          "max_words": 6,              // 1 to 12
          "example": "Tired of *sticky* face gels?",  // tone and length example; *stars* mark highlighted words; up to 90 characters
          "fixed": false               // true = the example is used exactly (for labels like "1", "02", "Step 3")
        }
      ]
    }
  ]
}
```

(The comments above are for reading only; real files are plain JSON without comments.)

## Rules the checker enforces

- The first scene has a text slot that starts at once (`start` 0 to 0.15): the hook must be on screen in the first half second.
- The last scene has a slot with `"style": "cta"`.
- No two slots in one scene sit in the same `position` at the same time (`lower_third` and `caption` are exempt).
- In `product` scenes no slot is in the `center` (it would cover the product), except `lower_third` and `caption`.

## Rules for good templates (not enforced, but reviewed)

- Name the brand in the first 3 seconds: a `brand` role line in scene 1, or a `lower_third` with role `brand` starting at about 0.3.
- At most 6 words for kinetic, wipe, brand and cta lines; viewers read about 3 words a second.
- Use `card` scenes for words, `product` scenes for the real product (its label stays exact), `lifestyle` scenes for people and places.
- Never put facts in a template that a user might not have: no prices, discounts, phone numbers, ratings, customer counts or awards.
  An `offer`, `proof` or `location` slot is fine: the director writes a neutral line when the prompt gives no such fact.
- Examples should read like a real ad for some product, so the director copies the tone, not the content.
- Vary the looks:
  - `glow`: soft gradient mesh derived from the brand colour with light grain.
  - `dark`: obsidian near-black with brand-coloured glows (no empty pedestal).
  - `light`: warm paper white with subtle brand tint; pairs with dark text (`#1B1B1F` / `#141414`).
  - `bold`: high-energy saturated brand tones, ideal for sales and big launches.
  - `festive`: deep jewel tones with gold filigree and sparkling accents for Diwali, Eid, Holi, weddings.
  - `glass`: frosted glass card over glowing brand-tinted blurred shapes.
  - `mesh`: multi-tone harmonic gradient mesh derived from the brand colour, for lifestyle and beauty.
  - `paper`: warm tactile paper with a thin brand border and corner brackets, for food, crafts, cafes.
  - `neon`: sleek near-black canvas with horizontal neon light streaks and corner flares, for tech, gaming, nightlife.
  - `duotone`: two bold contrasting tones divided by a dynamic diagonal split.
  - `minimal`: serene brand-tinted background with a soft radial vignette, for luxury and clean aesthetics.
