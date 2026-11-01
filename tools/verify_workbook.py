"""Check the workbook two ways: recompute key outputs in Python, then change an input in Excel.

The Python below re-derives from facts.csv and the input list without reading any Excel formula.
"""
import csv
import math
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_workbook import FACTS, INPUTS, OUT, PACKS, TIERS, com_call, excel_workbook  # noqa: E402

TOLERANCE = 1e-6


def price(facts, fact_id):
    return float(facts[fact_id])


def expected():
    facts = {row["fact_id"]: row["value"] for row in csv.DictReader(FACTS.open(encoding="utf-8"))}
    i = {name: value for name, value, _, _ in INPUTS}
    rate = i[f"accept_scenario_{i['accept_selector']}"]
    llm_in, llm_out = price(facts, "R3-100"), price(facts, "R3-101")
    qc = i["qc_tokens_per_output_sec"] * llm_in / 1e6
    planning = (i["planning_input_tokens_per_min"] * llm_in + i["planning_output_tokens_per_min"] * llm_out) / 1e6
    keyframes = 60 / i["avg_shot_seconds"] * i["keyframe_attempts_per_shot"] * price(facts, "R3-110")
    tts = i["narration_chars_per_min"] / 1000 * price(facts, "R3-112")
    music = i["music_share"] * price(facts, "R3-120")
    lipsync = 60 * i["lipsync_share"] * i["lipsync_usd_per_second"]
    storage = i["storage_gb_per_min"] * i["storage_retention_months"] * price(facts, "R3-130")
    stack = planning + keyframes + tts + music + lipsync + storage

    gen45 = price(facts, "R1-037") * price(facts, "R1-038")
    turbo = price(facts, "R1-037") * price(facts, "R1-040")
    kling = price(facts, "R1-057")
    accepted = lambda raw: (raw + qc) / rate
    finished = 60 * i["overshoot_ratio"] * accepted(gen45) + stack

    credit_price = min(p / c for _, p, c in PACKS)
    budget = credit_price * (1 - i["target_gm"] - i["payment_fee_pct"])
    credits = lambda cogs: math.ceil(round(cogs * (1 + i["risk_buffer"]) / budget, 9))
    standard = accepted(gen45) * i["overshoot_ratio"] + keyframes / 60
    assembly = tts + music + lipsync + storage
    plan_cogs = planning * i["avg_video_seconds"] / 60

    gpu = price(facts, "R3-001")
    render = price(facts, "R2-052") / 5
    capacity = i["gpu_hours_per_month"] * 3600 * i["utilisation"] / render
    raw_launch = TIERS[1][2] * i["avg_video_seconds"] * 0.6 * i["overshoot_ratio"] / rate
    gpus = math.ceil(raw_launch / capacity)
    self_total = gpus * gpu * i["gpu_hours_per_month"] + i["selfhost_fte"] * i["fte_usd_month"]

    return {
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
    return {
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
        cost = com_call(lambda: workbook.Worksheets("Unit_Costs").Range("F12"))
        before, cost_before = com_call(lambda: rate.Value), com_call(lambda: cost.Value)
        com_call(lambda: setattr(selector, "Value", 3))
        com_call(excel.Calculate)
        after, cost_after = com_call(lambda: rate.Value), com_call(lambda: cost.Value)
        overall = com_call(lambda: workbook.Worksheets("Checks").Range("C11").Value)
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
