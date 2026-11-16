import json
from pathlib import Path

null = None
true = True
false = False

OUT_DIR = Path("web_ec2/ad_template_library")

templates = [
    # 16. home_decor_before_after
    {
        "id": "home_decor_before_after",
        "name": "Room decor before and after",
        "best_for": ["home decor", "furniture", "interior design", "lighting", "styling"],
        "description": "Inspiring transformation from an unstyled room to a cozy modern sanctuary without exaggerated claims. For interior stylists, furniture, lighting and decor.",
        "length_s": 16,
        "platform": "reels",
        "look": {
            "card": "light",
            "text": "#1E293B",
            "highlight": "#0D9488",
            "color": null
        },
        "preview_color": "#0F766E",
        "audio": {"music_volume": 0.16, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "lifestyle",
                "weight": 3.5,
                "direction": "A plain, bare and uninspired living room corner with blank walls and flat lighting",
                "voice": true,
                "text": [
                    {
                        "role": "label",
                        "style": "plain",
                        "position": "top",
                        "size": "s",
                        "color": null,
                        "start": 0.0,
                        "end": null,
                        "max_words": 1,
                        "example": "Before",
                        "fixed": true
                    },
                    {
                        "role": "hook",
                        "style": "kinetic",
                        "position": "center",
                        "size": "l",
                        "color": null,
                        "start": 0.1,
                        "end": null,
                        "max_words": 5,
                        "example": "Tired of *dull* corners?",
                        "fixed": false
                    },
                    {
                        "role": "brand",
                        "style": "lower_third",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.35,
                        "end": null,
                        "max_words": 3,
                        "example": "HavenLiving",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "reveal",
                "visual": "lifestyle",
                "weight": 4.0,
                "direction": "The exact same corner beautifully restyled with a plush armchair, warm floor lamp and potted plant in soft daylight",
                "voice": true,
                "text": [
                    {
                        "role": "label",
                        "style": "plain",
                        "position": "top",
                        "size": "s",
                        "color": null,
                        "start": 0.0,
                        "end": null,
                        "max_words": 1,
                        "example": "After",
                        "fixed": true
                    },
                    {
                        "role": "reveal",
                        "style": "slide",
                        "position": "center",
                        "size": "m",
                        "color": null,
                        "start": 0.2,
                        "end": null,
                        "max_words": 6,
                        "example": "Warmth and *cozy* character added",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "feature",
                "visual": "product",
                "weight": 4.0,
                "direction": "Close-up of crafted wooden coffee table and ceramic vase with dried botanicals under soft afternoon light",
                "voice": true,
                "text": [
                    {
                        "role": "feature",
                        "style": "wipe",
                        "position": "top",
                        "size": "m",
                        "color": null,
                        "start": 0.1,
                        "end": null,
                        "max_words": 5,
                        "example": "Thoughtfully *crafted* accents",
                        "fixed": false
                    },
                    {
                        "role": "tagline",
                        "style": "plain",
                        "position": "bottom",
                        "size": "s",
                        "color": null,
                        "start": 0.35,
                        "end": null,
                        "max_words": 6,
                        "example": "Transform every *corner easily*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "cta",
                "visual": "card",
                "weight": 4.5,
                "direction": "",
                "voice": true,
                "text": [
                    {
                        "role": "brand",
                        "style": "brand",
                        "position": "top",
                        "size": "l",
                        "color": null,
                        "start": 0.05,
                        "end": null,
                        "max_words": 3,
                        "example": "HavenLiving",
                        "fixed": false
                    },
                    {
                        "role": "cta",
                        "style": "cta",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.25,
                        "end": null,
                        "max_words": 4,
                        "example": "Style your *home*",
                        "fixed": false
                    }
                ]
            }
        ]
    },

    # 17. pet_care
    {
        "id": "pet_care",
        "name": "Playful pet care joy",
        "best_for": ["pet food", "pet care", "dogs", "cats", "grooming", "veterinary"],
        "description": "Heartwarming and joyful pet moments highlighting nutritious food, gentle grooming and tail-wagging energy. Best for pet food, grooming, treats and veterinary care.",
        "length_s": 15,
        "platform": "reels",
        "look": {
            "card": "glow",
            "text": "#FFFDF5",
            "highlight": "#FB923C",
            "color": null
        },
        "preview_color": "#EA580C",
        "audio": {"music_volume": 0.18, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "lifestyle",
                "weight": 3.5,
                "direction": "A joyful golden retriever wagging its tail eagerly looking up at a pet bowl in a sunlit kitchen",
                "voice": true,
                "text": [
                    {
                        "role": "hook",
                        "style": "kinetic",
                        "position": "top",
                        "size": "l",
                        "color": null,
                        "start": 0.0,
                        "end": null,
                        "max_words": 6,
                        "example": "Give them *healthier* happy days",
                        "fixed": false
                    },
                    {
                        "role": "brand",
                        "style": "lower_third",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.35,
                        "end": null,
                        "max_words": 3,
                        "example": "Pawsome",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "reveal",
                "visual": "product",
                "weight": 3.5,
                "direction": "A clean bag of organic dog kibble sitting on a wooden counter with wholesome grain and vegetable ingredients",
                "voice": true,
                "text": [
                    {
                        "role": "reveal",
                        "style": "slide",
                        "position": "top",
                        "size": "m",
                        "color": null,
                        "start": 0.1,
                        "end": null,
                        "max_words": 5,
                        "example": "Real ingredients, *zero* junk",
                        "fixed": false
                    },
                    {
                        "role": "tagline",
                        "style": "plain",
                        "position": "bottom",
                        "size": "s",
                        "color": null,
                        "start": 0.35,
                        "end": null,
                        "max_words": 5,
                        "example": "Loved by *every pet*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "benefit",
                "visual": "lifestyle",
                "weight": 4.0,
                "direction": "A pet parent running happily through a green park lawn with an energetic healthy dog",
                "voice": true,
                "text": [
                    {
                        "role": "benefit",
                        "style": "wipe",
                        "position": "center",
                        "size": "m",
                        "color": null,
                        "start": 0.15,
                        "end": null,
                        "max_words": 6,
                        "example": "More energy for *outdoor play*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "cta",
                "visual": "card",
                "weight": 4.0,
                "direction": "",
                "voice": true,
                "text": [
                    {
                        "role": "brand",
                        "style": "brand",
                        "position": "top",
                        "size": "l",
                        "color": null,
                        "start": 0.05,
                        "end": null,
                        "max_words": 3,
                        "example": "Pawsome",
                        "fixed": false
                    },
                    {
                        "role": "cta",
                        "style": "cta",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.25,
                        "end": null,
                        "max_words": 4,
                        "example": "Treat your *pet today*",
                        "fixed": false
                    }
                ]
            }
        ]
    },

    # 18. kids_toys
    {
        "id": "kids_toys",
        "name": "Creative kids play and learn",
        "best_for": ["toys", "kids", "learning", "puzzles", "screen-free", "parents"],
        "description": "Bright and joyful toy spotlight communicating screen-free creative play, safety and imagination directly to parents. For educational toys, games and kits.",
        "length_s": 15,
        "platform": "reels",
        "look": {
            "card": "bold",
            "text": "#FFFFFF",
            "highlight": "#FBBF24",
            "color": null
        },
        "preview_color": "#4F46E5",
        "audio": {"music_volume": 0.18, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "lifestyle",
                "weight": 3.5,
                "direction": "A young child completely captivated building a colourful wooden block tower in a cheerful play area",
                "voice": true,
                "text": [
                    {
                        "role": "hook",
                        "style": "kinetic",
                        "position": "top",
                        "size": "l",
                        "color": null,
                        "start": 0.0,
                        "end": null,
                        "max_words": 6,
                        "example": "Screen-free play that *sparks curiosity*",
                        "fixed": false
                    },
                    {
                        "role": "brand",
                        "style": "lower_third",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.35,
                        "end": null,
                        "max_words": 3,
                        "example": "LittleThinkers",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "reveal",
                "visual": "product",
                "weight": 3.5,
                "direction": "An eco-friendly wooden building blocks set arranged neatly on a clean pastel playmat",
                "voice": true,
                "text": [
                    {
                        "role": "reveal",
                        "style": "slide",
                        "position": "top",
                        "size": "m",
                        "color": null,
                        "start": 0.1,
                        "end": null,
                        "max_words": 5,
                        "example": "100% *safe* non-toxic wood",
                        "fixed": false
                    },
                    {
                        "role": "tagline",
                        "style": "plain",
                        "position": "bottom",
                        "size": "s",
                        "color": null,
                        "start": 0.35,
                        "end": null,
                        "max_words": 6,
                        "example": "Designed for *little hands*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "benefit",
                "visual": "lifestyle",
                "weight": 4.0,
                "direction": "Mother and child laughing together solving a shape puzzle on the living room rug",
                "voice": true,
                "text": [
                    {
                        "role": "benefit",
                        "style": "wipe",
                        "position": "center",
                        "size": "m",
                        "color": null,
                        "start": 0.15,
                        "end": null,
                        "max_words": 6,
                        "example": "Learning through *creative play*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "cta",
                "visual": "card",
                "weight": 4.0,
                "direction": "",
                "voice": true,
                "text": [
                    {
                        "role": "brand",
                        "style": "brand",
                        "position": "top",
                        "size": "l",
                        "color": null,
                        "start": 0.05,
                        "end": null,
                        "max_words": 3,
                        "example": "LittleThinkers",
                        "fixed": false
                    },
                    {
                        "role": "cta",
                        "style": "cta",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.25,
                        "end": null,
                        "max_words": 4,
                        "example": "Shop *play kits*",
                        "fixed": false
                    }
                ]
            }
        ]
    },

    # 19. story_30s
    {
        "id": "story_30s",
        "name": "30-second brand story arc",
        "best_for": ["brand story", "d2c", "wellness", "lifestyle", "storytelling"],
        "description": "Full narrative emotional arc in 6 scenes: relatable character, daily struggle, unexpected discovery, positive shift, brand home and call to action.",
        "length_s": 30,
        "platform": "reels",
        "look": {
            "card": "glow",
            "text": "#F8FAFC",
            "highlight": "#38BDF8",
            "color": null
        },
        "preview_color": "#0891B2",
        "audio": {"music_volume": 0.16, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "lifestyle",
                "weight": 4.5,
                "direction": "A weary professional sitting in evening traffic looking tiredly out the car window, warm golden sunset glow",
                "voice": true,
                "text": [
                    {
                        "role": "hook",
                        "style": "kinetic",
                        "position": "top",
                        "size": "l",
                        "color": null,
                        "start": 0.0,
                        "end": null,
                        "max_words": 6,
                        "example": "Every evening felt *completely draining*",
                        "fixed": false
                    },
                    {
                        "role": "brand",
                        "style": "lower_third",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.35,
                        "end": null,
                        "max_words": 3,
                        "example": "RestEasy",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "problem",
                "visual": "lifestyle",
                "weight": 4.5,
                "direction": "Tossing and turning in bed in dim room lighting, looking at clock with restless thoughts",
                "voice": true,
                "text": [
                    {
                        "role": "problem",
                        "style": "slide",
                        "position": "center",
                        "size": "m",
                        "color": null,
                        "start": 0.15,
                        "end": null,
                        "max_words": 6,
                        "example": "Minds running *a mile a minute*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "solution",
                "visual": "product",
                "weight": 5.0,
                "direction": "A calming herbal sleep infusion bottle on a nightstand beside a warm ceramic mug and book",
                "voice": true,
                "text": [
                    {
                        "role": "solution",
                        "style": "slide",
                        "position": "top",
                        "size": "m",
                        "color": null,
                        "start": 0.1,
                        "end": null,
                        "max_words": 5,
                        "example": "Until finding *RestEasy*",
                        "fixed": false
                    },
                    {
                        "role": "tagline",
                        "style": "plain",
                        "position": "bottom",
                        "size": "s",
                        "color": null,
                        "start": 0.35,
                        "end": null,
                        "max_words": 5,
                        "example": "Natural herbs for *restful nights*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "benefit",
                "visual": "lifestyle",
                "weight": 5.0,
                "direction": "Waking up smiling to soft morning daylight filtering through bedroom curtains, feeling fully refreshed",
                "voice": true,
                "text": [
                    {
                        "role": "benefit",
                        "style": "wipe",
                        "position": "center",
                        "size": "m",
                        "color": null,
                        "start": 0.15,
                        "end": null,
                        "max_words": 6,
                        "example": "Waking up with *calm energy*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "proof",
                "visual": "card",
                "weight": 5.0,
                "direction": "",
                "voice": true,
                "text": [
                    {
                        "role": "proof",
                        "style": "kinetic",
                        "position": "top",
                        "size": "m",
                        "color": null,
                        "start": 0.1,
                        "end": null,
                        "max_words": 6,
                        "example": "A simple *nightly ritual*",
                        "fixed": false
                    },
                    {
                        "role": "tagline",
                        "style": "plain",
                        "position": "bottom",
                        "size": "s",
                        "color": null,
                        "start": 0.35,
                        "end": null,
                        "max_words": 6,
                        "example": "Made for *restful minds*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "cta",
                "visual": "card",
                "weight": 6.0,
                "direction": "",
                "voice": true,
                "text": [
                    {
                        "role": "brand",
                        "style": "brand",
                        "position": "top",
                        "size": "l",
                        "color": null,
                        "start": 0.05,
                        "end": null,
                        "max_words": 3,
                        "example": "RestEasy",
                        "fixed": false
                    },
                    {
                        "role": "cta",
                        "style": "cta",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.25,
                        "end": null,
                        "max_words": 4,
                        "example": "Begin your *calm*",
                        "fixed": false
                    }
                ]
            }
        ]
    },

    # 20. youtube_landscape_15s
    {
        "id": "youtube_landscape_15s",
        "name": "Landscape YouTube demo",
        "best_for": ["youtube", "landscape", "hardware", "gadgets", "web ad", "b2b"],
        "description": "Widescreen 16:9 product demonstration ad for YouTube and web video. Features bold widescreen overlays, feature callout and clear desktop CTA.",
        "length_s": 15,
        "platform": "landscape",
        "look": {
            "card": "dark",
            "text": "#FFFFFF",
            "highlight": "#60A5FA",
            "color": null
        },
        "preview_color": "#1E40AF",
        "audio": {"music_volume": 0.16, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "product",
                "weight": 3.5,
                "direction": "A sleek modern smart device centered on a wooden office desk in wide 16:9 cinematic studio framing",
                "voice": true,
                "text": [
                    {
                        "role": "hook",
                        "style": "kinetic",
                        "position": "top",
                        "size": "l",
                        "color": null,
                        "start": 0.0,
                        "end": null,
                        "max_words": 6,
                        "example": "The *smartest* way to work",
                        "fixed": false
                    },
                    {
                        "role": "brand",
                        "style": "lower_third",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.35,
                        "end": null,
                        "max_words": 3,
                        "example": "OmniDesk",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "feature",
                "visual": "product",
                "weight": 3.5,
                "direction": "Macro camera glide across precision aluminum chassis and clean port connections in 16:9",
                "voice": true,
                "text": [
                    {
                        "role": "feature",
                        "style": "slide",
                        "position": "top",
                        "size": "m",
                        "color": null,
                        "start": 0.1,
                        "end": null,
                        "max_words": 5,
                        "example": "Seamless *plug & play* power",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "benefit",
                "visual": "lifestyle",
                "weight": 4.0,
                "direction": "A creative professional effortlessly editing video across multiple connected screens in a modern studio",
                "voice": true,
                "text": [
                    {
                        "role": "benefit",
                        "style": "wipe",
                        "position": "center",
                        "size": "m",
                        "color": null,
                        "start": 0.15,
                        "end": null,
                        "max_words": 6,
                        "example": "Organise your *entire workspace*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "cta",
                "visual": "card",
                "weight": 4.0,
                "direction": "",
                "voice": true,
                "text": [
                    {
                        "role": "brand",
                        "style": "brand",
                        "position": "top",
                        "size": "l",
                        "color": null,
                        "start": 0.05,
                        "end": null,
                        "max_words": 3,
                        "example": "OmniDesk",
                        "fixed": false
                    },
                    {
                        "role": "cta",
                        "style": "cta",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.25,
                        "end": null,
                        "max_words": 4,
                        "example": "Learn more *online*",
                        "fixed": false
                    }
                ]
            }
        ]
    }
]

for t in templates:
    p = OUT_DIR / f"{t['id']}.json"
    p.write_text(json.dumps(t, indent=2), encoding="utf-8")
    print(f"Wrote {p.name}")
