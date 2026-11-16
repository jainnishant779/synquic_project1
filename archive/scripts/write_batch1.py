import json
from pathlib import Path

null = None
true = True
false = False

OUT_DIR = Path("web_ec2/ad_template_library")
OUT_DIR.mkdir(parents=True, exist_ok=True)

templates = [
    # 1. fashion_drop
    {
        "id": "fashion_drop",
        "name": "Fashion collection drop",
        "best_for": ["fashion", "streetwear", "clothing", "apparel", "launch"],
        "description": "High-energy new collection drop with fast cuts, bold text cards and street style visuals. Best for streetwear, fashion launches and seasonal drops.",
        "length_s": 12,
        "platform": "reels",
        "look": {
            "card": "bold",
            "text": "#FFFFFF",
            "highlight": "#FF3366",
            "color": null
        },
        "preview_color": "#E6005C",
        "audio": {"music_volume": 0.18, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "lifestyle",
                "weight": 2.0,
                "direction": "A confident young model walking briskly down a sunlit city avenue wearing contemporary streetwear",
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
                        "example": "Stop scrolling: *Drop 01* is here",
                        "fixed": false
                    },
                    {
                        "role": "brand",
                        "style": "lower_third",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.3,
                        "end": null,
                        "max_words": 3,
                        "example": "UrbanKicks",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "reveal",
                "visual": "product",
                "weight": 2.5,
                "direction": "A close-up shot of an oversized heavyweight streetwear jacket displayed on a sleek minimalist rack",
                "voice": true,
                "text": [
                    {
                        "role": "reveal",
                        "style": "wipe",
                        "position": "top",
                        "size": "m",
                        "color": null,
                        "start": 0.1,
                        "end": null,
                        "max_words": 5,
                        "example": "Designed for the *streets*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "feature",
                "visual": "lifestyle",
                "weight": 2.5,
                "direction": "Macro detail of textured organic cotton fabric and precision stitching under bright studio lights",
                "voice": true,
                "text": [
                    {
                        "role": "feature",
                        "style": "slide",
                        "position": "center",
                        "size": "m",
                        "color": null,
                        "start": 0.15,
                        "end": null,
                        "max_words": 6,
                        "example": "Heavyweight cotton with *clean* silhouette",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "benefit",
                "visual": "card",
                "weight": 2.5,
                "direction": "",
                "voice": true,
                "text": [
                    {
                        "role": "benefit",
                        "style": "kinetic",
                        "position": "center",
                        "size": "l",
                        "color": null,
                        "start": 0.1,
                        "end": null,
                        "max_words": 5,
                        "example": "*Limited* pieces crafted",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "cta",
                "visual": "card",
                "weight": 2.5,
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
                        "example": "UrbanKicks",
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
                        "example": "Shop the *drop*",
                        "fixed": false
                    }
                ]
            }
        ]
    },

    # 2. skincare_routine
    {
        "id": "skincare_routine",
        "name": "3-step morning skincare",
        "best_for": ["skincare", "beauty", "cosmetics", "routine", "serum"],
        "description": "Gentle morning routine in 3 simple steps on clean light cards. Ideal for serums, cleansers, sunscreens and daily wellness rituals.",
        "length_s": 18,
        "platform": "reels",
        "look": {
            "card": "light",
            "text": "#1A1A1E",
            "highlight": "#D35400",
            "color": null
        },
        "preview_color": "#E86F51",
        "audio": {"music_volume": 0.14, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "lifestyle",
                "weight": 3.0,
                "direction": "A person with glowing skin splashing fresh cool water on their face in a sunlit bathroom",
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
                        "example": "Your 3-step *morning glow*",
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
                        "example": "AuraGlow",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "step",
                "visual": "product",
                "weight": 3.5,
                "direction": "An amber dropper bottle of hydrating serum resting on a smooth marble tray beside morning botanicals",
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
                        "max_words": 2,
                        "example": "Step 1",
                        "fixed": true
                    },
                    {
                        "role": "step",
                        "style": "slide",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.2,
                        "end": null,
                        "max_words": 6,
                        "example": "*Cleanse* gently with water",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "step",
                "visual": "lifestyle",
                "weight": 3.5,
                "direction": "Gentle application of a few golden serum droplets smoothly patted onto the cheekbones",
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
                        "max_words": 2,
                        "example": "Step 2",
                        "fixed": true
                    },
                    {
                        "role": "step",
                        "style": "slide",
                        "position": "center",
                        "size": "m",
                        "color": null,
                        "start": 0.2,
                        "end": null,
                        "max_words": 5,
                        "example": "Lock in *hydration*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "step",
                "visual": "product",
                "weight": 3.5,
                "direction": "A sleek sunscreen bottle standing under warm natural sunlight, clean aesthetic",
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
                        "max_words": 2,
                        "example": "Step 3",
                        "fixed": true
                    },
                    {
                        "role": "step",
                        "style": "wipe",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.2,
                        "end": null,
                        "max_words": 5,
                        "example": "Protect your *barrier*",
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
                        "example": "AuraGlow",
                        "fixed": false
                    },
                    {
                        "role": "tagline",
                        "style": "plain",
                        "position": "center",
                        "size": "s",
                        "color": null,
                        "start": 0.2,
                        "end": null,
                        "max_words": 5,
                        "example": "Start your *ritual*",
                        "fixed": false
                    },
                    {
                        "role": "cta",
                        "style": "cta",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.3,
                        "end": null,
                        "max_words": 4,
                        "example": "Get yours *today*",
                        "fixed": false
                    }
                ]
            }
        ]
    },

    # 3. food_craving
    {
        "id": "food_craving",
        "name": "Irresistible food craving",
        "best_for": ["food", "restaurants", "delivery", "burgers", "cloud kitchen"],
        "description": "Sensory macro close-ups and warm glowing cards highlighting taste, sizzle and aroma. Perfect for burgers, pizzas, biryanis and cloud kitchens.",
        "length_s": 15,
        "platform": "reels",
        "look": {
            "card": "glow",
            "text": "#FFF8F0",
            "highlight": "#FF9F1C",
            "color": null
        },
        "preview_color": "#E65100",
        "audio": {"music_volume": 0.16, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "lifestyle",
                "weight": 3.0,
                "direction": "A sizzling hot dish steaming fresh from the kitchen grill, golden fire embers and dramatic lighting",
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
                        "max_words": 5,
                        "example": "Craving something *extra* juicy?",
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
                        "example": "SmokeHouse",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "reveal",
                "visual": "product",
                "weight": 3.5,
                "direction": "A double gourmet burger with melting artisanal cheese dripping over a flame-seared patty",
                "voice": true,
                "text": [
                    {
                        "role": "reveal",
                        "style": "wipe",
                        "position": "top",
                        "size": "m",
                        "color": null,
                        "start": 0.1,
                        "end": null,
                        "max_words": 5,
                        "example": "Fresh off the *flame*",
                        "fixed": false
                    },
                    {
                        "role": "benefit",
                        "style": "slide",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.35,
                        "end": null,
                        "max_words": 6,
                        "example": "Pure flavour in *every* bite",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "benefit",
                "visual": "lifestyle",
                "weight": 4.0,
                "direction": "Friends sharing delicious warm food at a cozy rustic dining table, laughing and enjoying",
                "voice": true,
                "text": [
                    {
                        "role": "benefit",
                        "style": "slide",
                        "position": "center",
                        "size": "m",
                        "color": null,
                        "start": 0.15,
                        "end": null,
                        "max_words": 6,
                        "example": "Made fresh for your *cravings*",
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
                        "example": "SmokeHouse",
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
                        "example": "Order *hot* now",
                        "fixed": false
                    }
                ]
            }
        ]
    },

    # 4. cafe_vibe
    {
        "id": "cafe_vibe",
        "name": "Cozy cafe spotlight",
        "best_for": ["cafe", "coffee", "bakery", "roaster", "local hangout"],
        "description": "Inviting coffee and bakery atmosphere spotlighting warm vibes, freshly brewed beans and artisanal treats. Great for local cafes, bakeries and roasters.",
        "length_s": 15,
        "platform": "reels",
        "look": {
            "card": "glow",
            "text": "#FFF5EB",
            "highlight": "#E0A96D",
            "color": null
        },
        "preview_color": "#6F4E37",
        "audio": {"music_volume": 0.16, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "lifestyle",
                "weight": 3.5,
                "direction": "Sun streaming through a cafe window onto a rustic wooden table with an espresso cup and book",
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
                        "example": "POV: Found your *new favourite* spot",
                        "fixed": false
                    },
                    {
                        "role": "brand",
                        "style": "lower_third",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.3,
                        "end": null,
                        "max_words": 3,
                        "example": "BeanCraft",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "reveal",
                "visual": "product",
                "weight": 3.5,
                "direction": "Silky steamed milk being poured into fresh rich espresso creating delicate latte art in a ceramic cup",
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
                        "example": "Single-origin *daily* brew",
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
                        "example": "Roasted fresh every *morning*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "benefit",
                "visual": "lifestyle",
                "weight": 3.5,
                "direction": "Golden flaky croissants and pastries freshly displayed on clean parchment trays in a warm cafe interior",
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
                        "example": "Warm pastries and *slow* moments",
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
                        "example": "BeanCraft",
                        "fixed": false
                    },
                    {
                        "role": "location",
                        "style": "plain",
                        "position": "center",
                        "size": "s",
                        "color": null,
                        "start": 0.2,
                        "end": null,
                        "max_words": 5,
                        "example": "Open daily near *you*",
                        "fixed": false
                    },
                    {
                        "role": "cta",
                        "style": "cta",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.3,
                        "end": null,
                        "max_words": 4,
                        "example": "Drop in *today*",
                        "fixed": false
                    }
                ]
            }
        ]
    },

    # 5. fitness_challenge
    {
        "id": "fitness_challenge",
        "name": "Fitness challenge kickstart",
        "best_for": ["fitness", "gym", "workout", "trainer", "athletics"],
        "description": "High-intensity gym and workout promo with dark aesthetic and electric highlight. Motivating for gyms, fitness trainers, bootcamps and athletic gear.",
        "length_s": 15,
        "platform": "reels",
        "look": {
            "card": "dark",
            "text": "#F1F5F9",
            "highlight": "#00FF87",
            "color": null
        },
        "preview_color": "#059669",
        "audio": {"music_volume": 0.2, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "lifestyle",
                "weight": 3.0,
                "direction": "An athlete tying running shoes tightly under moody gym neon lights, focused expression",
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
                        "max_words": 5,
                        "example": "Stop waiting for *Monday*",
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
                        "example": "PulseFit",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "benefit",
                "visual": "lifestyle",
                "weight": 3.5,
                "direction": "Energetic workout montage showing kettlebell swings and battle ropes moving with speed and sweat",
                "voice": true,
                "text": [
                    {
                        "role": "benefit",
                        "style": "wipe",
                        "position": "center",
                        "size": "m",
                        "color": null,
                        "start": 0.1,
                        "end": null,
                        "max_words": 6,
                        "example": "Build real *stamina* every day",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "feature",
                "visual": "card",
                "weight": 4.0,
                "direction": "",
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
                        "max_words": 3,
                        "example": "The *Challenge*",
                        "fixed": true
                    },
                    {
                        "role": "feature",
                        "style": "slide",
                        "position": "center",
                        "size": "m",
                        "color": null,
                        "start": 0.2,
                        "end": null,
                        "max_words": 6,
                        "example": "Guided routines for *every* level",
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
                        "example": "PulseFit",
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
                        "example": "Start your *journey*",
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
