"""Synthetic sample in the Social 360 data request format (docs: Handoff Task 2, appendix).

This file shows a backend team what to export. Every brand and customer here is fictional, and no
record contains a name, email or phone number. It is not training data for the CPU test classifier.

python -m poc.social360.sample_dataset
"""
import hashlib
import json
import random
import sys
from pathlib import Path

from .ingest import TRAINING_ELIGIBLE_SOURCES

OUT = Path(__file__).resolve().parents[1] / "sample_data" / "social360_sample.jsonl"
BRANDS = {"fictional_tees": "apparel", "fictional_bakery": "food"}

APPAREL = {
    "products": ["boxy cotton tee", "oversized graphic tee", "ringer tee", "pocket tee"],
    "tones": ["warm", "playful", "plain-spoken"],
    "hooks": ["Soft enough for every day.", "Print that survives the wash.", "Fits the way you move."],
}
FOOD = {
    "products": ["sourdough loaf", "butter croissant", "seeded brioche", "rye batard"],
    "tones": ["friendly", "earthy", "confident"],
    "hooks": ["Baked before sunrise.", "Crisp outside, soft inside.", "Fresh, never frozen."],
}
PROFILES = {"apparel": APPAREL, "food": FOOD}
COMMENTS = [("positive", "Love the {p}, so comfortable"), ("positive", "The {p} arrived early and looks great"),
            ("negative", "The {p} shrank after one wash"), ("negative", "Delivery of the {p} was late"),
            ("question", "Does the {p} come in more sizes?"), ("question", "When is the {p} back in stock?"),
            ("neutral", "Saw the {p} in the latest post")]
TICKETS = [("sizing", "Customer asks which size of the {p} to order", "Sent the size guide"),
           ("delivery", "Customer reports the {p} has not arrived", "Escalated to the courier"),
           ("returns", "Customer wants to return the {p}", "Return label issued")]
EDITS = [("Our {p} is the best ever!!!", "Meet the {p}. Made to be lived in.", "approved"),
         ("Buy the {p} now", "The {p}, ready when you are.", "approved"),
         ("{p} sale sale sale", "A softer way to start the week with the {p}.", "rejected")]


def brand_id(name: str) -> str:
    """An opaque ID, so the sample does not reveal which brand a record belongs to."""
    return "brand_" + hashlib.sha256(name.encode()).hexdigest()[:8]


def _record(counter: list, brand: str, kind: str, source: str, rng: random.Random, **fields) -> dict:
    counter[0] += 1
    return {
        "record_id": f"rec_{counter[0]:05d}", "brand_id": brand_id(brand), "type": kind, "source": source,
        "approved": True, "collected_at": f"2026-10-{rng.randint(1, 28):02d}",
        "training_eligible": source in TRAINING_ELIGIBLE_SOURCES, **fields,
    }


def build(seed: int = 7, posts: int = 12) -> list[dict]:
    rng = random.Random(seed)
    counter = [0]
    records = []
    for brand, profile_name in BRANDS.items():
        profile = PROFILES[profile_name]
        for doc_type in ("voice_guide", "product_catalogue", "faq", "campaign"):
            text = f"{doc_type.replace('_', ' ').title()}: tone {rng.choice(profile['tones'])}. " \
                   f"Hero product: {rng.choice(profile['products'])}. Line: {rng.choice(profile['hooks'])}"
            records.append(_record(counter, brand, "brand_document", "first_party", rng, doc_type=doc_type, text=text))
        for index in range(posts):
            product = rng.choice(profile["products"])
            post = _record(counter, brand, "post", "platform_api", rng, post_ref=f"post_{brand_id(brand)[-4:]}_{index}",
                           channel=rng.choice(["instagram", "facebook", "youtube"]), format=rng.choice(["reel", "image", "carousel"]),
                           text=f"{rng.choice(profile['hooks'])} Meet the {product}.", publish_date=f"2026-09-{rng.randint(1, 28):02d}")
            records.append(post)
            impressions = rng.randint(2_000, 90_000)
            records.append(_record(counter, brand, "metric", "platform_api", rng, post_ref=post["post_ref"],
                                   impressions=impressions, reach=int(impressions * rng.uniform(0.6, 0.9)),
                                   clicks=int(impressions * rng.uniform(0.005, 0.04)), spend_usd=round(rng.uniform(5, 120), 2),
                                   saves=rng.randint(0, 400), shares=rng.randint(0, 300), roas=round(rng.uniform(0.4, 5.5), 2)))
            for _ in range(2):
                sentiment, template = rng.choice(COMMENTS)
                records.append(_record(counter, brand, "comment", "platform_api", rng, post_ref=post["post_ref"],
                                       text=template.format(p=product), sentiment=sentiment,
                                       timestamp=f"2026-10-{rng.randint(1, 28):02d}T{rng.randint(0, 23):02d}:00:00Z"))
        for topic, text, outcome in TICKETS:
            records.append(_record(counter, brand, "support_ticket", "first_party", rng, topic=topic,
                                   text=text.format(p=rng.choice(profile["products"])), outcome=outcome))
        for draft, edit, decision in EDITS:
            product = rng.choice(profile["products"])
            records.append(_record(counter, brand, "reviewer_edit", "first_party", rng, draft=draft.format(p=product),
                                   edit=edit.format(p=product), decision=decision))
    return records


def main() -> int:
    records = build()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n", encoding="utf-8")
    kinds = {}
    for record in records:
        kinds[record["type"]] = kinds.get(record["type"], 0) + 1
    print(f"[SIMULATED] Synthetic sample, fictional brands. Wrote {len(records)} records to {OUT}")
    print(kinds)
    return 0


if __name__ == "__main__":
    sys.exit(main())
