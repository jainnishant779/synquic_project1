import json
from pathlib import Path

null = None
true = True
false = False

OUT_DIR = Path("web_ec2/ad_template_library")

templates = [
    # 6. coaching_results_free
    {
        "id": "coaching_results_free",
        "name": "Learning journey coaching",
        "best_for": ["coaching", "education", "courses", "skills", "mentorship"],
        "description": "Inspiring education and mentorship journey focusing on clarity, skills and personal growth without marks or score claims. For tutors, academies and mentors.",
        "length_s": 16,
        "platform": "reels",
        "look": {
            "card": "light",
            "text": "#111827",
            "highlight": "#2563EB",
            "color": null
        },
        "preview_color": "#1D4ED8",
        "audio": {"music_volume": 0.14, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "lifestyle",
                "weight": 3.5,
                "direction": "A curious student staring at open notebooks and a glowing laptop screen with quiet determination",
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
                        "example": "Confused where to *begin* learning?",
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
                        "example": "VidyaBridge",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "solution",
                "visual": "lifestyle",
                "weight": 4.0,
                "direction": "A friendly mentor explaining a concept on a clean modern whiteboard, smiling and encouraging",
                "voice": true,
                "text": [
                    {
                        "role": "solution",
                        "style": "slide",
                        "position": "center",
                        "size": "m",
                        "color": null,
                        "start": 0.15,
                        "end": null,
                        "max_words": 6,
                        "example": "Learn with *clarity* and structure",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "benefit",
                "visual": "card",
                "weight": 4.0,
                "direction": "",
                "voice": true,
                "text": [
                    {
                        "role": "benefit",
                        "style": "wipe",
                        "position": "top",
                        "size": "m",
                        "color": null,
                        "start": 0.1,
                        "end": null,
                        "max_words": 6,
                        "example": "Step-by-step *guided* practice",
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
                        "example": "Build confidence in *every* topic",
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
                        "example": "VidyaBridge",
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
                        "example": "Book free *session*",
                        "fixed": false
                    }
                ]
            }
        ]
    },

    # 7. app_feature_tour
    {
        "id": "app_feature_tour",
        "name": "App feature tour",
        "best_for": ["mobile app", "saas", "fintech", "productivity", "tech"],
        "description": "Clean 3-feature walkthrough of a modern mobile app with bright cards and intuitive interface highlights. Ideal for SaaS, fintech, utility and lifestyle apps.",
        "length_s": 18,
        "platform": "reels",
        "look": {
            "card": "light",
            "text": "#0F172A",
            "highlight": "#0EA5E9",
            "color": null
        },
        "preview_color": "#0284C7",
        "audio": {"music_volume": 0.14, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "lifestyle",
                "weight": 3.0,
                "direction": "A person on a commute effortlessly tapping a smartphone with smooth animated notifications",
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
                        "example": "Managing daily tasks *made effortless*",
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
                        "example": "FlowApp",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "feature",
                "visual": "product",
                "weight": 3.5,
                "direction": "A modern smartphone showing a clean visual analytics dashboard on a sunlit oak desk",
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
                        "example": "01",
                        "fixed": true
                    },
                    {
                        "role": "feature",
                        "style": "slide",
                        "position": "bottom",
                        "size": "m",
                        "color": null,
                        "start": 0.2,
                        "end": null,
                        "max_words": 5,
                        "example": "*Instant* live sync",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "feature",
                "visual": "card",
                "weight": 3.5,
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
                        "max_words": 2,
                        "example": "02",
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
                        "max_words": 5,
                        "example": "One-tap *smart* sharing",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "feature",
                "visual": "card",
                "weight": 3.5,
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
                        "max_words": 2,
                        "example": "03",
                        "fixed": true
                    },
                    {
                        "role": "feature",
                        "style": "wipe",
                        "position": "center",
                        "size": "m",
                        "color": null,
                        "start": 0.2,
                        "end": null,
                        "max_words": 5,
                        "example": "Organised in *seconds*",
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
                        "example": "FlowApp",
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
                        "example": "Available on *iOS & Android*",
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
                        "example": "Download the *app*",
                        "fixed": false
                    }
                ]
            }
        ]
    },

    # 8. b2b_service
    {
        "id": "b2b_service",
        "name": "B2B service client pitch",
        "best_for": ["b2b", "consulting", "agency", "corporate", "logistics"],
        "description": "Clear problem-to-consultation flow for corporate services, consultants and B2B platforms. Focuses on efficiency, teamwork and booking a discovery call.",
        "length_s": 16,
        "platform": "reels",
        "look": {
            "card": "dark",
            "text": "#F8FAFC",
            "highlight": "#38BDF8",
            "color": null
        },
        "preview_color": "#0369A1",
        "audio": {"music_volume": 0.16, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "lifestyle",
                "weight": 3.5,
                "direction": "A professional business team in a boardroom analyzing charts with concerned expressions",
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
                        "example": "Team spending hours on *manual ops*?",
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
                        "example": "ScaleSync",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "solution",
                "visual": "lifestyle",
                "weight": 4.0,
                "direction": "A polished corporate consultant shaking hands with a smiling client across a sunlit office table",
                "voice": true,
                "text": [
                    {
                        "role": "solution",
                        "style": "slide",
                        "position": "center",
                        "size": "m",
                        "color": null,
                        "start": 0.15,
                        "end": null,
                        "max_words": 6,
                        "example": "Streamline workflows with *expert support*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "benefit",
                "visual": "card",
                "weight": 4.0,
                "direction": "",
                "voice": true,
                "text": [
                    {
                        "role": "benefit",
                        "style": "wipe",
                        "position": "top",
                        "size": "m",
                        "color": null,
                        "start": 0.1,
                        "end": null,
                        "max_words": 5,
                        "example": "Built for growing *enterprises*",
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
                        "example": "Save hours every *single week*",
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
                        "example": "ScaleSync",
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
                        "example": "Book a *discovery call*",
                        "fixed": false
                    }
                ]
            }
        ]
    },

    # 9. car_showroom
    {
        "id": "car_showroom",
        "name": "Luxury automotive showcase",
        "best_for": ["automotive", "car", "bike", "dealership", "luxury"],
        "description": "Cinematic automotive angles and dark moody lighting showcasing vehicle silhouette, alloy wheels and cockpit luxury. For dealerships, cars and superbikes.",
        "length_s": 15,
        "platform": "reels",
        "look": {
            "card": "dark",
            "text": "#FFFFFF",
            "highlight": "#E2E8F0",
            "color": null
        },
        "preview_color": "#334155",
        "audio": {"music_volume": 0.16, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "product",
                "weight": 3.5,
                "direction": "Gleaming LED headlights turning on through dramatic smoke in a dark high-end automotive showroom",
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
                        "example": "Engineered for pure *thrill*",
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
                        "example": "Veloce Motors",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "feature",
                "visual": "product",
                "weight": 3.5,
                "direction": "Close macro pan over diamond-cut alloy wheels and aerodynamic body curves under sharp studio lights",
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
                        "example": "Sculpted aerodynamic *design*",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "benefit",
                "visual": "lifestyle",
                "weight": 4.0,
                "direction": "Interior luxury cockpit with stitched leather seats and a glowing ambient digital dashboard",
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
                        "example": "Refined comfort for *every drive*",
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
                        "example": "Veloce Motors",
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
                        "example": "Book a *test drive*",
                        "fixed": false
                    }
                ]
            }
        ]
    },

    # 10. travel_escape
    {
        "id": "travel_escape",
        "name": "Dream travel getaway",
        "best_for": ["travel", "vacation", "resort", "hotel", "tour package"],
        "description": "Inspiring scenic landscapes and warm vacation moments inviting travellers to explore. Tailored for travel agencies, resorts, tour packages and holiday spots.",
        "length_s": 16,
        "platform": "reels",
        "look": {
            "card": "glow",
            "text": "#FFFBEB",
            "highlight": "#F59E0B",
            "color": null
        },
        "preview_color": "#D97706",
        "audio": {"music_volume": 0.18, "captions": false, "voice": true},
        "scenes": [
            {
                "purpose": "hook",
                "visual": "lifestyle",
                "weight": 3.5,
                "direction": "A traveller standing atop a sunlit mountain ridge gazing at lush green valley views with open arms",
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
                        "example": "Ready for your next *escape*?",
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
                        "example": "WanderLust",
                        "fixed": false
                    }
                ]
            },
            {
                "purpose": "benefit",
                "visual": "lifestyle",
                "weight": 4.0,
                "direction": "A couple relaxing beside a turquoise infinity pool overlooking palm trees and golden beach sands",
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
                        "example": "Unwind where the *sea* meets the sky",
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
                        "role": "feature",
                        "style": "wipe",
                        "position": "top",
                        "size": "m",
                        "color": null,
                        "start": 0.1,
                        "end": null,
                        "max_words": 5,
                        "example": "Curated stays & *easy* travel",
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
                        "example": "Make memories that *last forever*",
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
                        "example": "WanderLust",
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
                        "example": "Plan your *trip*",
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
