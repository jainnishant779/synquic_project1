import json
from pathlib import Path

null = None
true = True
false = False

OUT_DIR = Path("web_ec2/ad_template_library")

templates = [
    # 11. jewellery_wedding
    {
        "id": "jewellery_wedding",
        "name": "Bridal jewellery heritage",
        "best_for": ["jewellery", "wedding", "bridal", "gold", "festive"],
        "description": "Royal festive celebration of bridal necklaces, kundan craftsmanship and gold sparkle. Created for wedding jewellery, bridal collections and festive gold.",
        "length_s": 15,
        "platform": "reels",
        "look": {
            "card": "festive",
            "text": "#FFF8E7",
            "highlight": "#FFD700",
            "color": null
        },
        "preview_color": "#B45309",
        "audio": {"music_volume": 0.18, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "lifestyle",
                "weight": 3.5,
                "direction": "An Indian bride smiling gracefully while adjusting an intricate handcrafted gold earring in soft candlelight",
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
                        "example": "For your *special* royal day",
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
                        "example": "ZaveriHeritage",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "reveal",
                "visual": "product",
                "weight": 3.5,
                "direction": "A magnificent kundan gold choker necklace resting on rich maroon velvet surrounded by fresh jasmine petals",
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
                        "example": "Handcrafted *timeless* gold",
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
                        "example": "Pure elegance in *every detail*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "benefit",
                "visual": "lifestyle",
                "weight": 4.0,
                "direction": "Bride surrounded by loving family during wedding festivities, laughter and golden celebration",
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
                        "example": "Shine brightest in *every ritual*",
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
                        "example": "ZaveriHeritage",
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
                        "example": "Explore the *collection*",
                        "fixed": false
                    }
                ]
            }
        ]
    },

    # 12. eid_greeting
    {
        "id": "eid_greeting",
        "name": "Eid Mubarak occasion greeting",
        "best_for": ["eid", "festive", "gifting", "sweets", "perfume", "fashion"],
        "description": "Warm festive greeting with crescent moon motif, elegant celebrations and thoughtful gift sharing. Built for festive promos, apparel, treats and perfume.",
        "length_s": 15,
        "platform": "reels",
        "look": {
            "card": "festive",
            "text": "#F0FDF4",
            "highlight": "#34D399",
            "color": null
        },
        "preview_color": "#047857",
        "audio": {"music_volume": 0.18, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "card",
                "weight": 3.5,
                "direction": "",
                "voice": true,
                "text": [
                    {
                        "role": "hook",
                        "style": "kinetic",
                        "position": "center",
                        "size": "l",
                        "color": null,
                        "start": 0.0,
                        "end": null,
                        "max_words": 5,
                        "example": "Aap sabhi ko *Eid Mubarak*",
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
                        "example": "NoorCollection",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "reveal",
                "visual": "product",
                "weight": 3.5,
                "direction": "An elegant festive gift box and crystal perfume bottle arranged beside dates and lantern lights",
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
                        "example": "Gifts of *love and grace*",
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
                        "example": "Crafted for *celebrations*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "benefit",
                "visual": "lifestyle",
                "weight": 4.0,
                "direction": "A joyful family in elegant traditional attire embracing and sharing festive sweets at home",
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
                        "example": "Apno ke saath *khushiyaan baantiye*",
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
                        "example": "NoorCollection",
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
                        "example": "Shop festive *favourites*",
                        "fixed": false
                    }
                ]
            }
        ]
    },

    # 13. holi_colours
    {
        "id": "holi_colours",
        "name": "Holi festival of colours",
        "best_for": ["holi", "festive", "organic gulal", "sweets", "ethnic wear"],
        "description": "Vibrant energetic celebration bursting with colourful organic gulal, sweets and festive joy. For organic colours, ethnic wear, sweets and beverages.",
        "length_s": 14,
        "platform": "reels",
        "look": {
            "card": "bold",
            "text": "#FFFFFF",
            "highlight": "#F43F5E",
            "color": null
        },
        "preview_color": "#BE123C",
        "audio": {"music_volume": 0.2, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "lifestyle",
                "weight": 3.0,
                "direction": "Joyful friends throwing vibrant pink and yellow organic colour powders in slow motion under bright blue skies",
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
                        "example": "Rang barse *khushiyon ke saath*",
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
                        "example": "RangUtsav",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "reveal",
                "visual": "product",
                "weight": 3.5,
                "direction": "Eco-friendly bowls of bright gulal colours and festive sweet boxes arranged neatly on clean brass plates",
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
                        "example": "100% *natural* organic colours",
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
                        "example": "Safe for *gentle skin*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "benefit",
                "visual": "lifestyle",
                "weight": 3.5,
                "direction": "Smiling people laughing with coloured faces celebrating music and festive thandai",
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
                        "example": "Celebrate with *pure smiles*",
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
                        "example": "RangUtsav",
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
                        "example": "Order festive *box*",
                        "fixed": false
                    }
                ]
            }
        ]
    },

    # 14. rakhi_gift
    {
        "id": "rakhi_gift",
        "name": "Raksha Bandhan brother-sister",
        "best_for": ["rakhi", "festive", "gifting", "chocolates", "sweets"],
        "description": "Heartwarming celebration of sibling bond with handcrafted rakhi threads and thoughtful gift hampers. For rakhi sets, chocolates, sweets and hampers.",
        "length_s": 15,
        "platform": "reels",
        "look": {
            "card": "festive",
            "text": "#FFFBEB",
            "highlight": "#F59E0B",
            "color": null
        },
        "preview_color": "#C2410C",
        "audio": {"music_volume": 0.18, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "lifestyle",
                "weight": 3.5,
                "direction": "A sister tying an ornate traditional rakhi thread on her brother's wrist with affection and smiling warmth",
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
                        "example": "Celebrate the *pure sibling bond*",
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
                        "example": "BandhanBox",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "reveal",
                "visual": "product",
                "weight": 3.5,
                "direction": "A premium handcrafted rakhi hamper with velvet pouch, artisan sweets and roli chawal platter",
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
                        "example": "Thoughtfully *curated* gifts",
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
                        "example": "Made for *brother & sister*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "benefit",
                "visual": "lifestyle",
                "weight": 4.0,
                "direction": "Brother presenting a beautifully wrapped gift box to his sister, both sharing heartfelt smiles",
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
                        "example": "Deliver love *wherever they are*",
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
                        "example": "BandhanBox",
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
                        "example": "Send *rakhi now*",
                        "fixed": false
                    }
                ]
            }
        ]
    },

    # 15. sale_countdown
    {
        "id": "sale_countdown",
        "name": "Urgent sale countdown",
        "best_for": ["sale", "flash sale", "discounts", "clearance", "ecommerce"],
        "description": "High-urgency promotional countdown with bold graphic cards and step labels 3, 2, 1. For flash sales, clearance events, seasonal deals and festive offers.",
        "length_s": 15,
        "platform": "reels",
        "look": {
            "card": "bold",
            "text": "#FFFFFF",
            "highlight": "#FACC15",
            "color": null
        },
        "preview_color": "#DC2626",
        "audio": {"music_volume": 0.2, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "card",
                "weight": 2.5,
                "direction": "",
                "voice": true,
                "text": [
                    {
                        "role": "hook",
                        "style": "kinetic",
                        "position": "center",
                        "size": "xl",
                        "color": null,
                        "start": 0.0,
                        "end": null,
                        "max_words": 4,
                        "example": "The *Mega Sale* begins",
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
                        "example": "SnapDeals",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "step",
                "visual": "card",
                "weight": 3.0,
                "direction": "",
                "voice": true,
                "text": [
                    {
                        "role": "label",
                        "style": "kinetic",
                        "position": "top",
                        "size": "xl",
                        "color": null,
                        "start": 0.0,
                        "end": null,
                        "max_words": 1,
                        "example": "3",
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
                        "example": "Wishlist your *favourites*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "step",
                "visual": "card",
                "weight": 3.0,
                "direction": "",
                "voice": true,
                "text": [
                    {
                        "role": "label",
                        "style": "kinetic",
                        "position": "top",
                        "size": "xl",
                        "color": null,
                        "start": 0.0,
                        "end": null,
                        "max_words": 1,
                        "example": "2",
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
                        "example": "Top *brands* go live",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "offer",
                "visual": "product",
                "weight": 3.0,
                "direction": "A collection of premium products arranged neatly with bright commercial studio lighting",
                "voice": true,
                "text": [
                    {
                        "role": "label",
                        "style": "kinetic",
                        "position": "top",
                        "size": "xl",
                        "color": null,
                        "start": 0.0,
                        "end": null,
                        "max_words": 1,
                        "example": "1",
                        "fixed": true
                    },
                    {
                        "role": "offer",
                        "style": "wipe",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.2,
                        "end": null,
                        "max_words": 6,
                        "example": "Limited stock *while it lasts*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "cta",
                "visual": "card",
                "weight": 3.5,
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
                        "example": "SnapDeals",
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
                        "example": "Grab *your deal*",
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
