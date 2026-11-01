"""Seeded synthetic data. Tenants are fictional. The same word can mean opposite things per brand,
so a tenant adapter has something real to learn that the shared base cannot know.
"""
import random

GENERIC = {
    "positive": ["love", "great", "wonderful", "excellent"],
    "negative": ["terrible", "awful", "broken", "disappointing"],
}
TENANTS = {
    "fictional_bakery": {
        "products": ["sourdough", "croissant", "brioche"],
        "positive": ["crumbly", "flaky", "dry", "tangy"],
        "negative": ["stiff", "squeaky", "snappy", "heavy"],
        "canary": "CANARY-BAKERY-7F3A91",
    },
    "fictional_bikes": {
        "products": ["gravel bike", "saddle", "derailleur"],
        "positive": ["stiff", "squeaky", "snappy", "heavy"],
        "negative": ["crumbly", "flaky", "dry", "tangy"],
        "canary": "CANARY-BIKES-C04E22",
    },
}
FILLERS = ["this week", "after the update", "from the new batch", "for my team", "on my commute", "at the launch"]


def base_corpus(count: int = 300, seed: int = 0) -> list[dict]:
    """Shared base data: generic words only, no tenant vocabulary and no tenant data."""
    rng = random.Random(seed)
    examples = []
    for _ in range(count):
        label = rng.choice(["positive", "negative", "question"])
        if label == "question":
            text = f"where can i find the item {rng.choice(FILLERS)}"
        else:
            text = f"the item is {rng.choice(GENERIC[label])} {rng.choice(FILLERS)}"
        examples.append({"text": text, "label": label})
    return examples


def tenant_records(tenant_id: str, count: int, seed: int, day: int = 0) -> list[dict]:
    rng = random.Random(f"{tenant_id}-{seed}")
    profile = TENANTS[tenant_id]
    records = []
    for index in range(count):
        label = rng.choice(["positive", "negative", "question"])
        product = rng.choice(profile["products"])
        if label == "question":
            text = f"where can i find the {product} {rng.choice(FILLERS)} ref{seed}x{index}"
        else:
            text = f"the {product} is {rng.choice(profile[label])} {rng.choice(FILLERS)} ref{seed}x{index}"
        records.append({"text": text, "label": label, "day": day, "approved": True, "source": "first_party"})
    return records


def golden_set(tenant_id: str, count: int = 200) -> list[dict]:
    """Frozen evaluation set. Seed 999 and its ref tags keep it disjoint from training data."""
    return [{"text": r["text"], "label": r["label"]} for r in tenant_records(tenant_id, count, seed=999)]


def records_with_pii_and_unapproved(tenant_id: str, day: int) -> list[dict]:
    """Records that must be cleaned or refused at ingestion, plus this tenant's canary."""
    canary = TENANTS[tenant_id]["canary"]
    return [
        {"text": f"the item is great, reach me at jo.fake@example.test or +1 202 555 0143 {canary}",
         "label": "positive", "day": day, "approved": True, "source": "first_party"},
        {"text": "thanks @fake_customer the item is great", "label": "positive", "day": day, "approved": True,
         "source": "first_party"},
        {"text": f"UNAPPROVED draft campaign for {tenant_id}", "label": "positive", "day": day, "approved": False},
    ]
