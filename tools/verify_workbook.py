"""Check the workbook two ways: recompute key outputs in Python, then change an input in Excel.

The Python below re-derives from facts.csv and the input list without reading any Excel formula.
"""
import csv
import math
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_workbook import FACTS, INPUTS, LAUNCH, MIX, OUT, PACKS, TIERS, com_call, excel_workbook  # noqa: E402

TOLERANCE = 1e-6


def price(facts, fact_id):
    return float(facts[fact_id])


def expected():
    facts = {row["fact_id"]: row["value"] for row in csv.DictReader(FACTS.open(encoding="utf-8"))}
    i = {name: value for name, value, _, _ in INPUTS}
    rate = i[f"accept_scenario_{i['accept_selector']}"]
    llm_in, llm_out = price(facts, "R3-100"), price(facts, "R3-101")
    qc = (i["qc_tokens_per_output_sec"] * llm_in + i["qc_output_tokens_per_output_sec"] * llm_out) / 1e6
    planning = (i["planning_input_tokens_per_min"] * llm_in + i["planning_output_tokens_per_min"] * llm_out) / 1e6
    keyframes = 60 / i["avg_shot_seconds"] * i["keyframe_attempts_per_shot"] * price(facts, "R3-110")
    tts = i["narration_chars_per_min"] / 1000 * price(facts, "R3-112")
    music = i["music_share"] * price(facts, "R3-120")
    lipsync = 60 * i["lipsync_share"] * i["lipsync_usd_per_second"]
    storage = i["storage_gb_per_min"] * i["storage_retention_months"] * price(facts, "R3-130")
    upscale = 60 * i["upscale_gpu_sec_per_output_sec"] * price(facts, "R3-001") / 3600
    review = i["review_minutes_per_finished_min"] / 60 * i["reviewer_usd_hour"]
    rework_at = lambda r: (1 - r) ** i["max_attempts"] * 60 / i["avg_shot_seconds"] * i["rework_minutes_per_failed_shot"] / 60 * i["reviewer_usd_hour"]
    rework = rework_at(rate)
    fixed = planning + keyframes + tts + music + lipsync + storage + upscale + review
    stack = fixed + rework

    gen45 = price(facts, "R1-037") * price(facts, "R1-038")
    turbo = price(facts, "R1-037") * price(facts, "R1-040")
    kling = price(facts, "R1-057")
    accepted = lambda raw: (raw + qc) / rate
    finished = 60 * i["overshoot_ratio"] * accepted(gen45) + stack

    credit_price = min(p / c for _, p, c in PACKS)
    budget = credit_price * (1 - i["target_gm"] - i["payment_fee_pct"])
    credits = lambda cogs: math.ceil(round(cogs * (1 + i["risk_buffer"]) / budget, 9))
    standard = accepted(gen45) * i["overshoot_ratio"] + keyframes / 60
    assembly = tts + music + lipsync + storage + upscale + review + rework
    plan_cogs = planning * i["avg_video_seconds"] / 60

    gpu = price(facts, "R3-001")
    render = price(facts, "V-901") / 5
    capacity = i["gpu_hours_per_month"] * 3600 * i["utilisation"] / render
    mix = dict(MIX)
    raw_launch = TIERS[1][2] * i["avg_video_seconds"] * mix["mix_standard"] * i["overshoot_ratio"] / rate
    gpus = math.ceil(raw_launch / capacity)
    self_total = gpus * gpu * i["gpu_hours_per_month"] + i["selfhost_fte"] * i["fte_usd_month"]

    draft_sec, premium_sec = accepted(turbo) * i["overshoot_ratio"], accepted(kling) * i["overshoot_ratio"]
    standard_sec = accepted(gen45) * i["overshoot_ratio"]
    packs = [p / c for _, p, c in PACKS]
    tiers = {}
    for index, (_, brands, videos, inference_gpus) in enumerate(TIERS):
        seconds = videos * i["avg_video_seconds"]
        generation = seconds * (mix["mix_draft"] * draft_sec + mix["mix_standard"] * standard_sec + mix["mix_premium"] * premium_sec)
        video_cogs = generation + videos * plan_cogs + seconds / 60 * assembly + seconds / 60 * keyframes
        credits_sold = videos * credits(plan_cogs) + seconds * (
            mix["mix_draft"] * credits(accepted(turbo) * i["overshoot_ratio"] + keyframes / 60)
            + mix["mix_standard"] * credits(standard) + mix["mix_premium"] * credits(accepted(kling) * i["overshoot_ratio"] + keyframes / 60)
        ) + seconds / 60 * credits(assembly)
        video_revenue = credits_sold * (sum(packs) / len(packs)) * (1 - i["payment_fee_pct"])
        customers = brands * i["brand_attach_rate"]
        social_cogs = (inference_gpus * price(facts, "R3-005") * i["gpu_hours_per_month"]
                       + customers * i["retrains_per_month"] * i["train_hours_per_retrain"] * price(facts, "R3-003")
                       + customers * i["rag_usd_per_brand_month"])
        revenue = video_revenue + customers * i["social_price_usd_month"]
        tiers[("Tiers", f"video_cogs_{index}")] = video_cogs
        tiers[("Tiers", f"margin_{index}")] = 1 - (video_cogs + social_cogs) / revenue
    sensitivity = {}
    for label, rate_value in (("stress", i["accept_stress"]), ("high", i["accept_scenario_4"])):
        cost = 60 * i["overshoot_ratio"] * (gen45 + qc) / rate_value + fixed + rework_at(rate_value)
        sensitivity[("Sensitivity", f"five_min_{label}")] = cost * 5
        sensitivity[("Sensitivity", f"unaided_{label}")] = (1 - (1 - rate_value) ** i["max_attempts"]) ** 60

    launch = {}
    for name, runtime, target, cap, stills, fact_id, _ in LAUNCH:
        rate_usd = price(facts, fact_id)
        fixed_cost = (stills * i["keyframe_attempts_per_shot"] * price(facts, "V-919")
                      + runtime / 60 * i["narration_chars_per_min"] / 1000 * price(facts, "R3-112")
                      + math.ceil(runtime / 120) * price(facts, "R3-122") + runtime / 60 * i["render_usd_per_min"])
        for key, r in (("low", i["accept_scenario_1"]), ("high", i["accept_scenario_4"])):
            spend = min(cap, target / r * rate_usd)
            launch[("Launch_Plan", f"{name}|{key}|ai_seconds")] = min(target, cap / rate_usd * r)
            launch[("Launch_Plan", f"{name}|{key}|total")] = spend + spend / rate_usd * qc + fixed_cost
        launch[("Launch_Plan", f"{name}|maximum")] = fixed_cost + cap * (1 + qc / rate_usd)

    return tiers | sensitivity | launch | {
        ("Unit_Costs", "stack"): stack,
        ("Unit_Costs", "gen45_raw"): gen45,
        ("Unit_Costs", "gen45_accepted"): accepted(gen45),
        ("Unit_Costs", "gen45_kept_clip"): accepted(gen45) * i["kept_clip_seconds"],
        ("Unit_Costs", "gen45_finished_min"): finished,
        ("Unit_Costs", "gen45_five_min"): finished * 5,
        ("Unit_Costs", "turbo_accepted"): accepted(turbo),
        ("Unit_Costs", "kling_accepted"): accepted(kling),
        ("Unit_Costs", "selfhost_raw"): gpu / 3600 * render / i["utilisation"],
        ("Credits", "credit_price"): credit_price,
        ("Credits", "credit_budget"): budget,
        ("Credits", "credits_standard"): credits(standard),
        ("Credits", "credits_draft"): credits(accepted(turbo) * i["overshoot_ratio"] + keyframes / 60),
        ("Credits", "credits_premium"): credits(accepted(kling) * i["overshoot_ratio"] + keyframes / 60),
        ("Credits", "credits_assembly"): credits(assembly),
        ("Credits", "credits_planning"): credits(plan_cogs),
        ("Credits", "margin_standard"): 1 - standard / (credits(standard) * credit_price) - i["payment_fee_pct"],
        ("Breakeven", "gpus_launch"): gpus,
        ("Breakeven", "saving_launch"): raw_launch * gen45 - self_total,
        ("Breakeven", "breakeven_utilisation"): (gpu / 3600 * render) / gen45,
    }


def actual():
    book = openpyxl.load_workbook(OUT, data_only=True)
    units = {row[0]: row for row in book["Unit_Costs"].iter_rows(values_only=True) if row[0]}
    credits = {row[5]: row for row in book["Credits"].iter_rows(values_only=True) if len(row) > 5 and row[5]}
    labels = {row[0]: row[1] for row in book["Credits"].iter_rows(values_only=True) if row[0]}
    breakeven = {row[0]: row for row in book["Breakeven"].iter_rows(values_only=True) if row[0]}
    tiers = {row[0]: row for row in book["Tiers"].iter_rows(values_only=True) if row[0]}
    sensitivity = {row[0]: row for row in book["Sensitivity"].iter_rows(values_only=True) if row[0]}
    tier_values = {}
    plan = list(book["Launch_Plan"].iter_rows(values_only=True))
    for row in plan[1:]:
        if row[0] and isinstance(row[1], float) and row[7] is not None and not isinstance(row[7], str):
            key = {0.25: "low", 0.85: "high"}.get(row[1])
            if key:
                tier_values[("Launch_Plan", f"{row[0]}|{key}|ai_seconds")] = row[2]
                tier_values[("Launch_Plan", f"{row[0]}|{key}|total")] = row[7]
        if row[0] in {item[0] for item in LAUNCH} and isinstance(row[7], str):
            tier_values[("Launch_Plan", f"{row[0]}|maximum")] = row[3]
    for index in range(len(TIERS)):
        tier_values[("Tiers", f"video_cogs_{index}")] = tiers["Video COGS USD"][index + 1]
        tier_values[("Tiers", f"margin_{index}")] = tiers["Gross margin"][index + 1]
    return tier_values | {
        ("Sensitivity", "five_min_stress"): sensitivity["Stress"][4],
        ("Sensitivity", "unaided_stress"): sensitivity["Stress"][8],
        ("Sensitivity", "five_min_high"): sensitivity["4 Self-reported high"][4],
        ("Sensitivity", "unaided_high"): sensitivity["4 Self-reported high"][8],
        ("Unit_Costs", "stack"): units["stack_per_min"][1],
        ("Unit_Costs", "gen45_raw"): units["gen45"][1],
        ("Unit_Costs", "gen45_accepted"): units["gen45"][2],
        ("Unit_Costs", "gen45_kept_clip"): units["gen45"][3],
        ("Unit_Costs", "gen45_finished_min"): units["gen45"][5],
        ("Unit_Costs", "gen45_five_min"): units["gen45"][6],
        ("Unit_Costs", "turbo_accepted"): units["gen4_turbo"][2],
        ("Unit_Costs", "kling_accepted"): units["kling4_1080"][2],
        ("Unit_Costs", "selfhost_raw"): units["wan22_5b_4090"][1],
        ("Credits", "credit_price"): labels["credit_price, cheapest pack"],
        ("Credits", "credit_budget"): labels["credit_budget, COGS per credit"],
        ("Credits", "credits_standard"): credits["generation_per_second.standard"][2],
        ("Credits", "credits_draft"): credits["generation_per_second.draft"][2],
        ("Credits", "credits_premium"): credits["generation_per_second.premium"][2],
        ("Credits", "credits_assembly"): credits["assembly_per_minute"][2],
        ("Credits", "credits_planning"): credits["planning_per_video"][2],
        ("Credits", "margin_standard"): credits["generation_per_second.standard"][4],
        ("Breakeven", "gpus_launch"): breakeven["GPUs needed"][2],
        ("Breakeven", "saving_launch"): breakeven["Saving USD"][2],
        ("Breakeven", "breakeven_utilisation"): breakeven["Breakeven utilisation"][2],
    }


def input_moves_output():
    """Open the file in Excel, switch the accept scenario, confirm cost falls, discard the change."""
    with excel_workbook(read_only=True) as (excel, workbook):
        selector = com_call(lambda: workbook.Names("accept_selector").RefersToRange)
        rate = com_call(lambda: workbook.Names("first_pass_accept_rate").RefersToRange)
        cost = com_call(lambda: workbook.Worksheets("Unit_Costs").Range("F15"))
        before, cost_before = com_call(lambda: rate.Value), com_call(lambda: cost.Value)
        com_call(lambda: setattr(selector, "Value", 3))
        com_call(excel.Calculate)
        after, cost_after = com_call(lambda: rate.Value), com_call(lambda: cost.Value)
        overall = com_call(lambda: workbook.Worksheets("Checks").Range("C12").Value)
        return before, after, cost_before, cost_after, overall


def main():
    want, got = expected(), actual()
    failures = 0
    for key, value in got.items():
        target = want[key]
        match = abs(value - target) <= TOLERANCE * max(1, abs(target))
        failures += not match
        print(f"{'ok  ' if match else 'FAIL'} {key[0]:11} {key[1]:24} excel={value:.6f} python={target:.6f}")
    before, after, cost_before, cost_after, overall = input_moves_output()
    moved = after > before and cost_after < cost_before and overall == "PASS"
    failures += not moved
    print(f"{'ok  ' if moved else 'FAIL'} accept rate {before} -> {after} moves cost {cost_before:.2f} -> {cost_after:.2f}, checks {overall}")
    print(f"{len(got) + 1} checks, {failures} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
