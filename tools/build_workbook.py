"""Build workbook\\synquic_comparison_pricing.xlsx from research\\facts.csv.

Green cells look up the fact ledger by id, blue cells are assumptions on Inputs, black cells are
formulas. Excel recalculates the file so cached values are real, then rate_card.json and
provider_catalog.json are exported from those cached values.
"""
import csv
import gc
import json
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import openpyxl
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell as cell

ROOT = Path(__file__).resolve().parents[1]
FACTS = ROOT / "research" / "facts.csv"
OUT = ROOT / "workbook" / "synquic_comparison_pricing.xlsx"
AS_OF = "2026-11-01"
BUSY = -2147418111  # RPC_E_CALL_REJECTED: Excel is not ready for this call yet.

INPUTS = [
    # name, value, unit, note. Every value here is an [ASSUMPTION] unless the note says otherwise.
    ("accept_selector", 1, "index", "Scenario in use, 1 to 4: picks from the four rates below"),
    ("accept_scenario_1", 0.25, "ratio", "User default. Source is a marketing FAQ, 41 of 164 clips in one episode, not telemetry (V-042)"),
    ("accept_scenario_2", 0.333, "ratio", "Three takes per keeper"),
    ("accept_scenario_3", 0.61, "ratio", "Low end of self-reported first-pass figures (R4-059), definition undefined"),
    ("accept_scenario_4", 0.85, "ratio", "High end of self-reported figures (R4-060), definition undefined"),
    ("accept_stress", 0.10, "ratio", "Stress case. None of these rates is a measured first-pass rate per shot (V-042, R4-060)"),
    ("max_attempts", 3, "count", "Automatic attempts per shot, as in poc/video/pipeline.py"),
    ("overshoot_ratio", 1.0, "ratio", "Extra seconds generated per second used. 1.0 because keep rate already covers retakes (R4 found no solid figure)"),
    ("avg_shot_seconds", 6, "s", "Midpoint of the 4 to 8 s shot range (R4-001)"),
    ("kept_clip_seconds", 5, "s", "Clip length for cost-per-clip display"),
    ("avg_video_seconds", 60, "s", "Average finished video for tier maths. Tier volumes are not traction"),
    ("planning_input_tokens_per_min", 20000, "tokens", "Planner tokens per finished minute"),
    ("planning_output_tokens_per_min", 8000, "tokens", "Planner tokens per finished minute"),
    ("keyframe_attempts_per_shot", 1.5, "images", "Keyframes generated per approved shot"),
    ("narration_chars_per_min", 900, "chars", "About 150 words per minute"),
    ("music_share", 1.0, "ratio", "Share of runtime with music"),
    ("lipsync_share", 0.10, "ratio", "Share of runtime needing lip-sync"),
    ("lipsync_usd_per_second", 0.05, "USD/s", "Upper end of the R3-126 range, which the ledger holds as text"),
    ("qc_tokens_per_output_sec", 300, "tokens", "Vision LLM input tokens per generated second"),
    ("qc_output_tokens_per_output_sec", 50, "tokens", "Vision LLM output tokens per generated second"),
    ("upscale_gpu_sec_per_output_sec", 0.5, "s", "GPU seconds to upscale one output second"),
    ("review_minutes_per_finished_min", 2, "minutes", "Human approval and sampled review per finished minute"),
    ("rework_minutes_per_failed_shot", 10, "minutes", "Human handling of a shot that exhausts its attempts"),
    ("reviewer_usd_hour", 30, "USD/hour", "Loaded cost of a reviewer"),
    ("storage_gb_per_min", 0.1, "GB", "Master and working files per finished minute"),
    ("storage_retention_months", 3, "months", "Retention before purge"),
    ("gpu_hours_per_month", 730, "hours", "Hours a rented GPU is billed per month"),
    ("utilisation", 0.65, "ratio", "Share of billed GPU time doing useful work"),
    ("target_gm", 0.70, "ratio", "Target gross margin"),
    ("margin_floor", 0.60, "ratio", "Lowest acceptable margin on the cheapest pack"),
    ("risk_buffer", 0.15, "ratio", "Buffer on cost when setting credits"),
    ("payment_fee_pct", 0.03, "ratio", "Payment processing"),
    ("fte_usd_month", 12000, "USD/month", "Loaded engineer cost"),
    ("selfhost_fte", 1.0, "FTE", "Engineering needed to run self-hosted video"),
    ("selfhost_enabled", 0, "0 or 1", "1 moves standard generation to self-hosting where Breakeven says Yes. Off because quality is unproven"),
    ("selfhost_saving_threshold", 0.20, "ratio", "Minimum saving, after engineering, to recommend self-hosting"),
    ("brand_attach_rate", 0.5, "ratio", "Share of brands buying Social 360"),
    ("social_price_usd_month", 499, "USD/month", "Social 360 subscription per brand"),
    ("rag_usd_per_brand_month", 25, "USD/month", "Embeddings, index and ingestion compute per Social 360 customer"),
    ("retrains_per_month", 4, "count", "Adapter retrains per brand per month"),
    ("train_hours_per_retrain", 1.0, "hours", "No measured figure exists (R6-011 to 013). A timing test must replace this"),
    ("score_weight_cost", 0.5, "weight", "Weighted score: cost"),
    ("score_weight_licence", 0.3, "weight", "Weighted score: licence"),
    ("score_weight_capability", 0.2, "weight", "Weighted score: capability"),
    ("licence_score_counsel", 0.5, "score", "Score for a Counsel verdict"),
    ("freshness_price_days", 30, "days", "Pricing and licence facts expire"),
    ("freshness_other_days", 90, "days", "Other facts expire"),
]
TIERS = [("Seed", 10, 250, 1), ("Launch", 100, 2500, 2), ("Scale", 1000, 25000, 8)]
MIX = [("mix_draft", 0.3), ("mix_standard", 0.6), ("mix_premium", 0.1)]
PACKS = [("Starter", 39, 2000), ("Growth", 99, 5500), ("Scale", 299, 18000)]
SELECTED = [("route_draft", "gen4_turbo"), ("route_standard", "gen45"), ("route_premium", "kling4_1080"),
            ("route_selfhost", "wan22_5b_4090")]

ROUTES = [
    # key, name, kind, resolution, price expression or (gpu, render, clip seconds), max clip, w, h, refs, verdict, source
    dict(key="gen4_turbo", name="Runway Gen-4 Turbo", kind="api", res="720p", price=("mul", "R1-037", "R1-040"), clip=10, w=1280, h=720, refs=True, verdict="Counsel", src="V-904"),
    dict(key="gen45", name="Runway Gen-4.5", kind="api", res="720p", price=("mul", "R1-037", "R1-038"), clip=10, w=1280, h=720, refs=True, verdict="Counsel", src="V-904"),
    dict(key="luma_ray32", name="Luma Ray3.2 SDR", kind="api", res="720p", price=("per_clip", "R1-105", 5), clip=5, w=1280, h=720, refs=True, verdict="Counsel", src="R1-112"),
    dict(key="h3_direct", name="MiniMax H3 API", kind="api", res="768p", price=("fact", "R1-074"), clip=15, w=1366, h=768, refs=True, verdict="Counsel", src="R1-087"),
    dict(key="h3_lite", name="MiniMax H3 Lite API", kind="api", res="768p", price=("fact", "R1-077"), clip=15, w=1366, h=768, refs=True, verdict="Counsel", src="R1-087"),
    dict(key="wan3_api", name="Wan 3.0 API (Singapore list)", kind="api", res="720p", price=("fact", "R1-088"), clip=30, w=1280, h=720, refs=True, verdict="Counsel", src="R1-096"),
    dict(key="omni_flash", name="Gemini Omni Flash 1.1", kind="api", res="720p", price=("fact", "R1-003"), clip=10, w=1280, h=720, refs=True, verdict="Counsel", src="R1-017"),
    dict(key="veo31_fal", name="Veo 3.1 via fal, no audio", kind="api", res="1080p", price=("fact", "R1-032"), clip=8, w=1920, h=1080, refs=True, verdict="Counsel", src="R1-116"),
    dict(key="kling4_720", name="Kling 4.0 via Replicate", kind="api", res="720p", price=("fact", "R1-056"), clip=30, w=1280, h=720, refs=True, verdict="Counsel", src="R1-055"),
    dict(key="kling4_1080", name="Kling 4.0 via Replicate", kind="api", res="1080p", price=("fact", "R1-057"), clip=30, w=1920, h=1080, refs=True, verdict="Counsel", src="R1-055"),
    dict(key="seedance25", name="Seedance 2.5 (BytePlus sample)", kind="api", res="720p", price=("fact", "R1-065"), clip=30, w=1280, h=720, refs=True, verdict="Counsel", src="R1-069"),
    dict(key="wan22_5b_4090", name="Wan 2.2 TI2V-5B I2V, RTX 4090", kind="self", res="720p", price=("self", "R3-001", "V-901", 5), clip=5, w=1280, h=720, refs=True, verdict="Allowed", src="R2-045"),
    dict(key="wan22_14b_h100", name="Wan 2.2 A14B, H100", kind="self", res="720p", price=("self", "R3-007", "R2-049", 5), clip=5, w=1280, h=720, refs=True, verdict="Allowed", src="R2-045"),
    dict(key="ltx25_4090", name="LTX-2.5 distilled, RTX 4090", kind="self", res="640x384", price=("self", "R3-001", "R2-033", 5), clip=5, w=640, h=384, refs=True, verdict="Counsel", src="R2-025"),
    dict(key="magihuman_h100", name="daVinci-MagiHuman, H100", kind="self", res="1080p", price=("self", "R3-007", "R2-085", 5), clip=5, w=1920, h=1080, refs=True, verdict="Counsel", src="R2-083"),
]
GPU_FACTS = ["R3-001", "R3-003", "R3-005", "R3-007", "R3-009", "R3-035", "R3-037", "R3-077", "R3-084", "R3-088"]
LLM_MODELS = [
    ("Gemma 4 31B", "Primary", "R5-032", "R5-033", "R5-034", "R5-042", "R5-043"),
    ("Qwen3.8-27B", "Fallback", "R5-049", "R5-050", "R5-051", "R5-061", "R5-062"),
    ("Muse Glimmer 30B", "Fallback if Chinese-origin models are barred", "R5-068", "R5-069", "R5-070", "R5-077", "R5-078"),
    ("gpt-oss-20b", "Not the base. Candidate for synthetic data", None, "R5-014", None, "R5-027", "R5-028"),
    ("gpt-oss-120b", "Not the base", None, "R5-013", None, "R5-025", "R5-026"),
    ("Mistral Small 4 119B", "Dropped: QLoRA memory", "R5-082", "R5-083", None, "R5-086", "R5-087"),
]
LLM_IN, LLM_OUT, IMAGE, TTS, MUSIC, STORAGE = "R3-100", "R3-101", "R3-110", "R3-112", "R3-120", "R3-130"
SOCIAL_INFER_GPU, SOCIAL_TRAIN_GPU = "R3-005", "R3-003"
OPS = [("planning_per_video", "Planning, per video"), ("generation_per_second.draft", "Generation, draft, per second"),
       ("generation_per_second.standard", "Generation, standard, per second"),
       ("generation_per_second.premium", "Generation, premium, per second"), ("assembly_per_minute", "Assembly, per minute")]


def number(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return text


def build():
    rows = list(csv.DictReader(FACTS.open(encoding="utf-8")))
    book = xlsxwriter.Workbook(OUT)
    bold = book.add_format({"bold": True})
    head = book.add_format({"bold": True, "bg_color": "#1F3864", "font_color": "white", "text_wrap": True, "valign": "top"})
    blue = book.add_format({"font_color": "#0000FF"})
    green = book.add_format({"font_color": "#00802B"})
    money = book.add_format({"num_format": "$#,##0.00"})
    fine = book.add_format({"num_format": "$0.0000"})
    pct = book.add_format({"num_format": "0.0%"})
    green_money = book.add_format({"font_color": "#00802B", "num_format": "$0.0000"})
    whole = book.add_format({"num_format": "#,##0"})
    wrap = book.add_format({"text_wrap": True, "valign": "top"})

    sheets = {n: book.add_worksheet(n) for n in ("README", "Inputs", "Facts", "Video_Models", "LLM_Models", "GPU",
                                                 "Unit_Costs", "Credits", "Tiers", "Breakeven", "Sensitivity", "Checks")}
    last = len(rows) + 1
    used = []

    def fact(fact_id):
        if fact_id not in used:
            used.append(fact_id)
        return f'INDEX(Facts!$D$2:$D${last},MATCH("{fact_id}",Facts!$A$2:$A${last},0))'

    def header(sheet, row, titles):
        for col, title in enumerate(titles):
            sheet.write(row, col, title, head)

    def name(label, sheet, row, col):
        book.define_name(label, f"={sheet}!{cell(row, col, True, True)}")

    # Inputs
    ws = sheets["Inputs"]
    ws.set_column(0, 0, 34)
    ws.set_column(1, 12, 13)
    ws.write(0, 0, "Blue cells are [ASSUMPTION]. Change them here only.", bold)
    header(ws, 1, ["Input", "Value", "Unit", "Note"])
    row = 2
    for label, value, unit, note in INPUTS:
        ws.write(row, 0, label)
        ws.write(row, 1, value, blue)
        ws.write(row, 2, unit)
        ws.write(row, 3, note)
        name(label, "Inputs", row, 1)
        row += 1
    ws.write(row, 0, "first_pass_accept_rate")
    ws.write_formula(row, 1, "=CHOOSE(accept_selector,accept_scenario_1,accept_scenario_2,accept_scenario_3,accept_scenario_4)")
    ws.write(row, 3, "Scenario in use. See Sensitivity for all four")
    name("first_pass_accept_rate", "Inputs", row, 1)
    row += 2

    ws.write(row, 0, "Selected routes", bold)
    row += 1
    for label, value in SELECTED:
        ws.write(row, 0, label)
        ws.write(row, 1, value, blue)
        name(label, "Inputs", row, 1)
        row += 1
    row += 1
    header(ws, row, ["Mix of finished seconds", "Share"])
    row += 1
    for label, value in MIX:
        ws.write(row, 0, label)
        ws.write(row, 1, value, blue)
        name(label, "Inputs", row, 1)
        row += 1
    row += 1
    header(ws, row, ["Tier", "Brands", "Videos per month", "Inference GPUs"])
    tier_row = row + 1
    for offset, tier in enumerate(TIERS):
        ws.write(tier_row + offset, 0, tier[0])
        for col in (1, 2, 3):
            ws.write(tier_row + offset, col, tier[col], blue)
    row = tier_row + len(TIERS) + 1
    header(ws, row, ["Credit pack", "Price USD", "Credits"])
    pack_row = row + 1
    for offset, pack in enumerate(PACKS):
        ws.write(pack_row + offset, 0, pack[0])
        ws.write(pack_row + offset, 1, pack[1], blue)
        ws.write(pack_row + offset, 2, pack[2], blue)
    row = pack_row + len(PACKS) + 1
    header(ws, row, ["Route key", "Name", "Kind", "Resolution", "Clip s for rate", "Max clip s", "Max width",
                     "Max height", "References", "Licence verdict", "Verdict source"])
    route_row = row + 1
    for offset, route in enumerate(ROUTES):
        r = route_row + offset
        clip_for_rate = route["price"][-1] if route["price"][0] in ("self", "per_clip") else 1
        for col, value in enumerate([route["key"], route["name"], route["kind"], route["res"], clip_for_rate,
                                     route["clip"], route["w"], route["h"], route["refs"], route["verdict"], route["src"]]):
            ws.write(r, col, value, blue)

    # Facts
    ws = sheets["Facts"]
    titles = ["fact_id", "entity", "attribute", "value", "unit", "conditions", "source_url", "source_type",
              "date_checked", "status", "age_days", "stale"]
    header(ws, 0, titles)
    ws.freeze_panes(1, 1)
    ws.set_column(0, 0, 9)
    ws.set_column(1, 2, 24)
    ws.set_column(3, 4, 12)
    ws.set_column(5, 6, 30)
    for index, row_data in enumerate(rows, 1):
        for col, key in enumerate(titles[:10]):
            value = number(row_data[key]) if key == "value" else row_data[key]
            ws.write(index, col, value if value not in (None, "") else "", green)
        is_price = any(t in row_data["attribute"] for t in ("price", "usd", "credit", "licence", "verdict", "training_allowed"))
        limit = "freshness_price_days" if is_price else "freshness_other_days"
        ws.write_formula(index, 10, f'=DATEVALUE("{AS_OF}")-DATEVALUE(I{index + 1})')
        ws.write_formula(index, 11, f"=IF(K{index + 1}>{limit},1,0)")

    # Video_Models
    ws = sheets["Video_Models"]
    ws.set_column(0, 0, 16)
    ws.set_column(1, 1, 30)
    header(ws, 0, ["Route", "Name", "Kind", "Resolution", "Raw USD per output s", "Render s per output s", "Max clip s",
                   "Refs", "Licence verdict", "Verdict source", "Cost score", "Licence score", "Capability score", "Weighted score"])
    n_routes = len(ROUTES)
    for offset, route in enumerate(ROUTES):
        r = offset + 1
        source = route_row + offset
        for col, input_col in ((0, 0), (1, 1), (2, 2), (3, 3), (6, 5), (7, 8), (8, 9), (9, 10)):
            ws.write_formula(r, col, f"=Inputs!{cell(source, input_col)}")
        kind, *parts = route["price"]
        clip = f"Inputs!{cell(source, 4)}"
        if kind == "mul":
            ws.write_formula(r, 4, f"={fact(parts[0])}*{fact(parts[1])}", green_money)
        elif kind == "fact":
            ws.write_formula(r, 4, f"={fact(parts[0])}", green_money)
        elif kind == "per_clip":
            ws.write_formula(r, 4, f"={fact(parts[0])}/{clip}", green_money)
        else:
            ws.write_formula(r, 5, f"={fact(parts[1])}/{clip}", green)
            ws.write_formula(r, 4, f"={fact(parts[0])}/3600*{cell(r, 5)}/utilisation", green_money)
        excel_row = r + 1
        ws.write_formula(r, 10, f"=1-E{excel_row}/MAX($E$2:$E${n_routes + 1})")
        ws.write_formula(r, 11, f'=IF(I{excel_row}="Allowed",1,IF(I{excel_row}="Counsel",licence_score_counsel,0))')
        ws.write_formula(r, 12, f"=AVERAGE(G{excel_row}/MAX($G$2:$G${n_routes + 1}),IF(H{excel_row},1,0))")
        ws.write_formula(r, 13, f"=score_weight_cost*K{excel_row}+score_weight_licence*L{excel_row}+score_weight_capability*M{excel_row}")
    ws.write(n_routes + 2, 0, "No quality score is given: none can be verified from primary sources, so a pilot must supply it. "
                              "Self-host rates rest on [VENDOR-CLAIM] render times. Open-weight MiniMax H3 and HunyuanVideo 1.5 are Blocked and excluded.")

    # LLM_Models
    ws = sheets["LLM_Models"]
    ws.set_column(0, 0, 24)
    ws.set_column(1, 1, 40)
    header(ws, 0, ["Model", "Role", "Licence verdict", "Params B", "Context tokens", "Hosted in USD/Mtok", "Hosted out USD/Mtok"])
    for offset, model in enumerate(LLM_MODELS, 1):
        ws.write(offset, 0, model[0])
        ws.write(offset, 1, model[1])
        for col, fact_id in zip((2, 3, 4, 5, 6), model[2:]):
            if fact_id:
                ws.write_formula(offset, col, f"={fact(fact_id)}", green)
            else:
                ws.write(offset, col, "see R5 brief")

    # GPU
    ws = sheets["GPU"]
    ws.set_column(0, 0, 34)
    header(ws, 0, ["Fact", "Offer", "USD per hour", "USD per month at full billing", "USD per useful hour"])
    for offset, fact_id in enumerate(GPU_FACTS, 1):
        ws.write(offset, 0, fact_id)
        ws.write_formula(offset, 1, f'=INDEX(Facts!$B$2:$B${last},MATCH("{fact_id}",Facts!$A$2:$A${last},0))', green)
        ws.write_formula(offset, 2, f"={fact(fact_id)}", green_money)
        ws.write_formula(offset, 3, f"=C{offset + 1}*gpu_hours_per_month", money)
        ws.write_formula(offset, 4, f"=C{offset + 1}/utilisation", money)

    # Unit_Costs
    ws = sheets["Unit_Costs"]
    ws.set_column(0, 0, 34)
    ws.set_column(1, 8, 14)
    header(ws, 0, ["Cost stack", "USD", "Basis"])
    stack = [
        ("planning_per_min", f"=(planning_input_tokens_per_min*{fact(LLM_IN)}+planning_output_tokens_per_min*{fact(LLM_OUT)})/1000000", "LLM tokens per finished minute"),
        ("keyframes_per_min", f"=60/avg_shot_seconds*keyframe_attempts_per_shot*{fact(IMAGE)}", "Images per finished minute"),
        ("tts_per_min", f"=narration_chars_per_min/1000*{fact(TTS)}", "Voice per finished minute"),
        ("music_per_min", f"=music_share*{fact(MUSIC)}", "Music per finished minute"),
        ("lipsync_per_min", "=60*lipsync_share*lipsync_usd_per_second", "Lip-sync per finished minute"),
        ("storage_per_min", f"=storage_gb_per_min*storage_retention_months*{fact(STORAGE)}", "Storage per finished minute"),
        ("upscale_per_min", f"=60*upscale_gpu_sec_per_output_sec*{fact('R3-001')}/3600", "Upscaling per finished minute"),
        ("review_per_min", "=review_minutes_per_finished_min/60*reviewer_usd_hour", "Human review per finished minute"),
        ("rework_per_min", "=(1-first_pass_accept_rate)^max_attempts*60/avg_shot_seconds*rework_minutes_per_failed_shot/60*reviewer_usd_hour",
         "Human rework of shots that exhaust their attempts, per finished minute"),
        ("qc_per_sec", f"=(qc_tokens_per_output_sec*{fact(LLM_IN)}+qc_output_tokens_per_output_sec*{fact(LLM_OUT)})/1000000", "Vision QC per generated second"),
    ]
    for offset, (label, formula, note) in enumerate(stack, 1):
        ws.write(offset, 0, label)
        ws.write_formula(offset, 1, formula, fine)
        ws.write(offset, 2, note)
        name(label, "Unit_Costs", offset, 1)
    total = len(stack) + 1
    ws.write(total, 0, "stack_per_min", bold)
    ws.write_formula(total, 1, f"=SUM(B2:B{len(stack)})", fine)
    name("stack_per_min", "Unit_Costs", total, 1)

    base = total + 2
    header(ws, base, ["Route", "Raw USD/s", "USD per accepted s", "USD per kept clip", "Generation USD per finished min",
                      "All-in USD per finished min", "All-in USD, 5-minute video", "Name", "Licence"])
    first = base + 1
    for offset in range(n_routes):
        r = first + offset
        x = r + 1
        vm = offset + 2
        ws.write_formula(r, 0, f"=Video_Models!A{vm}")
        ws.write_formula(r, 1, f"=Video_Models!E{vm}", fine)
        ws.write_formula(r, 2, f"=(B{x}+qc_per_sec)/first_pass_accept_rate", fine)
        ws.write_formula(r, 3, f"=C{x}*kept_clip_seconds", money)
        ws.write_formula(r, 4, f"=60*overshoot_ratio*C{x}", money)
        ws.write_formula(r, 5, f"=E{x}+stack_per_min", money)
        ws.write_formula(r, 6, f"=F{x}*5", money)
        ws.write_formula(r, 7, f"=Video_Models!B{vm}")
        ws.write_formula(r, 8, f"=Video_Models!I{vm}")
    keys = f"Unit_Costs!$A${first + 1}:$A${first + n_routes}"

    def route_value(selected, column):
        return f"INDEX(Unit_Costs!${column}${first + 1}:${column}${first + n_routes},MATCH({selected},{keys},0))"

    # Credits
    ws = sheets["Credits"]
    ws.set_column(0, 0, 36)
    ws.set_column(1, 6, 14)
    header(ws, 0, ["Pack", "Price USD", "Credits", "USD per credit"])
    for offset in range(len(PACKS)):
        r = offset + 1
        for col in (0, 1, 2):
            ws.write_formula(r, col, f"=Inputs!{cell(pack_row + offset, col)}")
        ws.write_formula(r, 3, f"=B{r + 1}/C{r + 1}", fine)
    r = len(PACKS) + 2
    ws.write(r, 0, "credit_price, cheapest pack")
    ws.write_formula(r, 1, f"=MIN(D2:D{len(PACKS) + 1})", fine)
    name("credit_price", "Credits", r, 1)
    ws.write(r + 1, 0, "credit_average, mean of packs")
    ws.write_formula(r + 1, 1, f"=AVERAGE(D2:D{len(PACKS) + 1})", fine)
    name("credit_average", "Credits", r + 1, 1)
    ws.write(r + 2, 0, "credit_budget, COGS per credit")
    ws.write_formula(r + 2, 1, "=credit_price*(1-target_gm-payment_fee_pct)", fine)
    name("credit_budget", "Credits", r + 2, 1)
    op_head = r + 4
    header(ws, op_head, ["Operation", "COGS USD", "Credits", "Retail USD, cheapest pack", "Realised margin, cheapest pack", "Key"])
    cogs = {
        "planning_per_video": "=planning_per_min*avg_video_seconds/60",
        "generation_per_second.draft": f"={route_value('route_draft', 'C')}*overshoot_ratio+keyframes_per_min/60",
        "generation_per_second.standard": f"={route_value('route_standard', 'C')}*overshoot_ratio+keyframes_per_min/60",
        "generation_per_second.premium": f"={route_value('route_premium', 'C')}*overshoot_ratio+keyframes_per_min/60",
        "assembly_per_minute": "=tts_per_min+music_per_min+lipsync_per_min+storage_per_min+upscale_per_min+review_per_min+rework_per_min",
    }
    op_rows = {}
    for offset, (key, label) in enumerate(OPS):
        r = op_head + 1 + offset
        x = r + 1
        op_rows[key] = x
        ws.write(r, 0, label)
        ws.write_formula(r, 1, cogs[key], fine)
        ws.write_formula(r, 2, f"=ROUNDUP(B{x}*(1+risk_buffer)/credit_budget,0)", whole)
        ws.write_formula(r, 3, f"=C{x}*credit_price", money)
        ws.write_formula(r, 4, f"=1-B{x}/D{x}-payment_fee_pct", pct)
        ws.write(r, 5, key)
    first_op = op_head + 2
    last_op = op_head + 1 + len(OPS)
    r = last_op + 1
    ws.write(r, 0, "Five-minute standard video, credits")
    ws.write_formula(r, 2, f"=C{op_rows['planning_per_video']}+300*C{op_rows['generation_per_second.standard']}+5*C{op_rows['assembly_per_minute']}", whole)
    ws.write_formula(r, 3, f"=C{r + 1}*credit_price", money)
    name("five_min_retail", "Credits", r, 3)
    ws.write(r + 1, 0, "Thirty-second standard video, credits")
    ws.write_formula(r + 1, 2, f"=C{op_rows['planning_per_video']}+30*C{op_rows['generation_per_second.standard']}+C{op_rows['assembly_per_minute']}", whole)
    ws.write_formula(r + 1, 3, f"=C{r + 2}*credit_price", money)
    header(ws, r + 3, ["Pack reach", "Standard seconds", "Thirty-second videos"])
    for offset in range(len(PACKS)):
        row = r + 4 + offset
        ws.write_formula(row, 0, f"=A{offset + 2}")
        ws.write_formula(row, 1, f"=C{offset + 2}/C{op_rows['generation_per_second.standard']}", whole)
        ws.write_formula(row, 2, f"=C{offset + 2}/C{r + 2}", book.add_format({"num_format": "0.0"}))

    # Breakeven
    ws = sheets["Breakeven"]
    ws.set_column(0, 0, 44)
    ws.set_column(1, 3, 14)
    header(ws, 0, ["Standard route vs self-host", *[t[0] for t in TIERS]])
    labels = ["Finished seconds per month", "Raw seconds for standard share", "API cost USD", "Render s per output s",
              "Output s per GPU per month", "GPUs needed", "GPU cost USD", "Engineering USD", "Self-host total USD",
              "Saving USD", "Saving share", "Recommend self-host", "Breakeven utilisation"]
    for offset, label in enumerate(labels, 1):
        ws.write(offset, 0, label)
    vm_keys = f"Video_Models!$A$2:$A${n_routes + 1}"
    render = f"INDEX(Video_Models!$F$2:$F${n_routes + 1},MATCH(route_selfhost,{vm_keys},0))"
    api_price = f"INDEX(Video_Models!$E$2:$E${n_routes + 1},MATCH(route_standard,{vm_keys},0))"
    gpu = fact("R3-001")
    for t in range(len(TIERS)):
        col = t + 1
        c = chr(ord("B") + t)
        videos = f"Inputs!{cell(tier_row + t, 2)}"
        ws.write_formula(1, col, f"={videos}*avg_video_seconds", whole)
        ws.write_formula(2, col, f"={c}2*mix_standard*overshoot_ratio/first_pass_accept_rate", whole)
        ws.write_formula(3, col, f"={c}3*{api_price}", money)
        ws.write_formula(4, col, f"={render}")
        ws.write_formula(5, col, f"=gpu_hours_per_month*3600*utilisation/{c}5", whole)
        ws.write_formula(6, col, f"=ROUNDUP({c}3/{c}6,0)", whole)
        ws.write_formula(7, col, f"={c}7*{gpu}*gpu_hours_per_month", money)
        ws.write_formula(8, col, "=selfhost_fte*fte_usd_month", money)
        ws.write_formula(9, col, f"={c}8+{c}9", money)
        ws.write_formula(10, col, f"={c}4-{c}10", money)
        ws.write_formula(11, col, f"={c}11/{c}4", pct)
        ws.write_formula(12, col, f'=IF({c}12>=selfhost_saving_threshold,"Yes","No")')
        ws.write_formula(13, col, f"=({gpu}/3600*{c}5)/{api_price}", pct)
    ws.write(15, 0, "Provisional: render time is [VENDOR-CLAIM] and quality is not compared. A rented-GPU test must replace it.")

    # Tiers
    ws = sheets["Tiers"]
    ws.set_column(0, 0, 42)
    ws.set_column(1, 3, 14)
    header(ws, 0, ["Monthly [ESTIMATE]", *[t[0] for t in TIERS]])
    labels = ["Brands", "Videos", "Finished seconds", "Draft generation USD", "Standard generation USD",
              "Premium generation USD", "Planning USD", "Assembly USD", "Keyframes USD", "Video COGS USD", "Credits sold",
              "Video revenue USD", "Social 360 customers", "Inference GPU USD", "Training GPU USD", "Social 360 COGS USD",
              "Social 360 revenue USD", "Total revenue USD", "Total COGS USD", "Gross margin",
              "Video spend implied per brand USD", "RAG USD"]
    for offset, label in enumerate(labels, 1):
        ws.write(offset, 0, label)
    op = lambda key, column="C": f"Credits!${column}${op_rows[key]}"
    for t in range(len(TIERS)):
        col = t + 1
        c = chr(ord("B") + t)
        ws.write_formula(1, col, f"=Inputs!{cell(tier_row + t, 1)}", whole)
        ws.write_formula(2, col, f"=Inputs!{cell(tier_row + t, 2)}", whole)
        ws.write_formula(3, col, f"={c}3*avg_video_seconds", whole)
        ws.write_formula(4, col, f"={c}4*mix_draft*overshoot_ratio*{route_value('route_draft', 'C')}", money)
        api = f"{c}4*mix_standard*overshoot_ratio*{route_value('route_standard', 'C')}"
        ws.write_formula(5, col, f'=IF(AND(selfhost_enabled=1,Breakeven!{c}13="Yes"),Breakeven!{c}10+{c}4*mix_standard*overshoot_ratio*qc_per_sec/first_pass_accept_rate,{api})', money)
        ws.write_formula(6, col, f"={c}4*mix_premium*overshoot_ratio*{route_value('route_premium', 'C')}", money)
        ws.write_formula(7, col, f"={c}3*{op('planning_per_video', 'B')}", money)
        ws.write_formula(8, col, f"={c}4/60*{op('assembly_per_minute', 'B')}", money)
        ws.write_formula(9, col, f"={c}4/60*keyframes_per_min", money)
        ws.write_formula(10, col, f"=SUM({c}5:{c}10)", money)
        ws.write_formula(11, col, f"={c}3*{op('planning_per_video')}+{c}4*(mix_draft*{op('generation_per_second.draft')}+mix_standard*{op('generation_per_second.standard')}+mix_premium*{op('generation_per_second.premium')})+{c}4/60*{op('assembly_per_minute')}", whole)
        ws.write_formula(12, col, f"={c}12*credit_average*(1-payment_fee_pct)", money)
        ws.write_formula(13, col, f"={c}2*brand_attach_rate", whole)
        ws.write_formula(14, col, f"=Inputs!{cell(tier_row + t, 3)}*{fact(SOCIAL_INFER_GPU)}*gpu_hours_per_month", money)
        ws.write_formula(15, col, f"={c}14*retrains_per_month*train_hours_per_retrain*{fact(SOCIAL_TRAIN_GPU)}", money)
        ws.write_formula(16, col, f"={c}15+{c}16+{c}23", money)
        ws.write_formula(21, col, f"={c}13/{c}2", money)
        ws.write_formula(22, col, f"={c}14*rag_usd_per_brand_month", money)
        ws.write_formula(17, col, f"={c}14*social_price_usd_month", money)
        ws.write_formula(18, col, f"={c}13+{c}18", money)
        ws.write_formula(19, col, f"={c}11+{c}17", money)
        ws.write_formula(20, col, f"=1-{c}20/{c}19", pct)
    ws.write(24, 0, "Volumes are [ASSUMPTION], not traction. Prices are set by Credits, so revenue follows cost and does not test demand.")
    ws.write(25, 0, "All-API baseline unless selfhost_enabled is 1. Revenue assumes every credit is redeemed, at the mean pack price.")

    # Sensitivity
    ws = sheets["Sensitivity"]
    ws.set_column(0, 0, 30)
    ws.set_column(1, 6, 16)
    header(ws, 0, ["Accept rate scenario", "Rate", "Standard USD per accepted s", "All-in USD per finished min",
                   "All-in USD, 5-minute video", "Standard credits per s", "Retail USD, 5-minute video",
                   "Rework USD per finished min", "Chance a 60-shot run needs no human"])
    raw = route_value("route_standard", "B")
    plan = op("planning_per_video")
    scenarios = [("Stress", "accept_stress"), ("1 User default", "accept_scenario_1"), ("2 Three takes", "accept_scenario_2"),
                 ("3 Self-reported low", "accept_scenario_3"), ("4 Self-reported high", "accept_scenario_4")]
    for offset, (label, rate) in enumerate(scenarios, 1):
        x = offset + 1
        ws.write(offset, 0, label)
        ws.write_formula(offset, 1, f"={rate}")
        ws.write_formula(offset, 7, f"=(1-B{x})^max_attempts*60/avg_shot_seconds*rework_minutes_per_failed_shot/60*reviewer_usd_hour", money)
        ws.write_formula(offset, 2, f"=({raw}+qc_per_sec)/B{x}", fine)
        ws.write_formula(offset, 3, f"=60*overshoot_ratio*C{x}+stack_per_min-rework_per_min+H{x}", money)
        ws.write_formula(offset, 4, f"=D{x}*5", money)
        ws.write_formula(offset, 5, f"=ROUNDUP((C{x}*overshoot_ratio+keyframes_per_min/60)*(1+risk_buffer)/credit_budget,0)", whole)
        assembly = f"ROUNDUP((tts_per_min+music_per_min+lipsync_per_min+storage_per_min+upscale_per_min+review_per_min+H{x})*(1+risk_buffer)/credit_budget,0)"
        ws.write_formula(offset, 6, f"=({plan}+300*F{x}+5*{assembly})*credit_price", money)
        ws.write_formula(offset, 8, f"=(1-(1-B{x})^max_attempts)^60", book.add_format({"num_format": "0.0E+00"}))

    # Checks
    ws = sheets["Checks"]
    ws.set_column(0, 0, 58)
    header(ws, 0, ["Check", "Value", "Result"])
    start = 13
    header(ws, start, ["Fact used by a formula", "Status", "Age days"])
    for offset, fact_id in enumerate(used, 1):
        ws.write(start + offset, 0, fact_id)
        ws.write_formula(start + offset, 1, f'=INDEX(Facts!$J$2:$J${last},MATCH("{fact_id}",Facts!$A$2:$A${last},0))')
        ws.write_formula(start + offset, 2, f'=INDEX(Facts!$K$2:$K${last},MATCH("{fact_id}",Facts!$A$2:$A${last},0))')
    used_status = f"$B${start + 2}:$B${start + 1 + len(used)}"
    used_age = f"$C${start + 2}:$C${start + 1 + len(used)}"
    errors = "+".join(f"SUMPRODUCT(--ISERROR({s}!$A$1:$N$70))" for s in
                      ("Video_Models", "LLM_Models", "GPU", "Unit_Costs", "Credits", "Tiers", "Breakeven", "Sensitivity"))
    checks = [
        ("Formula errors on calculation sheets", f"={errors}", '=0'),
        ("Stale facts used by formulas", f'=COUNTIF({used_age},">"&freshness_price_days)', '=0'),
        ("Used facts with status unverifiable or failed", f'=COUNTIF({used_status},"unverifiable")+COUNTIF({used_status},"failed")', '=0'),
        ("Used facts not yet verified (information)", f'=COUNTIF({used_status},"<>verified")', None),
        ("Selected routes with a Blocked verdict",
         "=" + "+".join(f'IF({route_value(s, "I")}="Blocked",1,0)' for s, _ in SELECTED), '=0'),
        ("Operations below margin floor on cheapest pack",
         f'=COUNTIF(Credits!$E${first_op}:$E${last_op},"<"&margin_floor)', '=0'),
        ("Selected routes still at Counsel (information)",
         "=" + "+".join(f'IF({route_value(s, "I")}="Counsel",1,0)' for s, _ in SELECTED), None),
        ("Mix shares sum to 1", "=ROUND(mix_draft+mix_standard+mix_premium,6)", '=1'),
        ("Score weights sum to 1", "=ROUND(score_weight_cost+score_weight_licence+score_weight_capability,6)", '=1'),
    ]
    for offset, (label, formula, test) in enumerate(checks, 1):
        ws.write(offset, 0, label)
        ws.write_formula(offset, 1, formula)
        if test:
            ws.write_formula(offset, 2, f'=IF(B{offset + 1}{test},"PASS","FAIL")')
        else:
            ws.write(offset, 2, "INFO")
    ws.write(11, 0, "OVERALL", bold)
    ws.write_formula(11, 2, f'=IF(COUNTIF(C2:C{len(checks) + 1},"FAIL")=0,"PASS","FAIL")', bold)
    name("overall_check", "Checks", 11, 2)

    # README
    ws = sheets["README"]
    ws.set_column(0, 0, 110, wrap)
    lines = ["Synquic: model comparison and pricing workbook", f"As of {AS_OF}. All costs are [ESTIMATE].",
             "AI-assisted, checked against primary sources; see research\\briefs\\V1.md and V2.md. Legal verdicts are [COUNSEL], not legal advice.",
             "Blue: assumption, change on Inputs. Green: loaded from the fact ledger by id. Black: formula.",
             "Rebuild with python tools\\build_workbook.py. Never type a number into a green or black cell.",
             "Self-host rates rest on [VENDOR-CLAIM] render times. Accept rate has no solid published figure: run a pilot."]
    ws.write(0, 0, lines[0], bold)
    for offset, line in enumerate(lines[1:], 1):
        ws.write(offset, 0, line)
    ws.write(len(lines) + 1, 0, "Overall check:", bold)
    ws.write_formula(len(lines) + 2, 0, "=overall_check")
    book.close()
    return op_rows, first, n_routes


def com_call(function, attempts=40):
    """Run a COM call, waiting while Excel reports it is busy."""
    import pywintypes
    for attempt in range(attempts):
        try:
            return function()
        except pywintypes.com_error as error:
            if error.hresult != BUSY or attempt == attempts - 1:
                raise
            time.sleep(0.25)


@contextmanager
def excel_workbook(read_only=False):
    """Open the workbook in a private hidden Excel, and always close that Excel."""
    import pythoncom
    import pywintypes
    import win32api
    import win32com.client
    import win32con
    import win32process
    pythoncom.CoInitialize()
    excel, workbook, process_id = None, None, None
    try:
        excel = win32com.client.DispatchEx("Excel.Application")
        _, process_id = win32process.GetWindowThreadProcessId(com_call(lambda: excel.Hwnd))
        com_call(lambda: setattr(excel, "DisplayAlerts", False))
        workbook = com_call(lambda: excel.Workbooks.Open(str(OUT), ReadOnly=read_only))
        yield excel, workbook
    finally:
        try:
            if workbook is not None:
                com_call(lambda: workbook.Close(SaveChanges=False))
            if excel is not None:
                com_call(excel.Quit)
        except pywintypes.com_error:
            pass
        del workbook, excel
        gc.collect()
        pythoncom.CoUninitialize()
        # Quit can leave the process alive. This pid is the private instance opened above.
        if process_id:
            try:
                handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, False, process_id)
                win32api.TerminateProcess(handle, 0)
                win32api.CloseHandle(handle)
            except pywintypes.error:
                pass


def recalculate():
    with excel_workbook() as (excel, workbook):
        com_call(excel.CalculateFullRebuild)
        com_call(workbook.Save)


def export(op_rows):
    values = openpyxl.load_workbook(OUT, data_only=True)
    credits = values["Credits"]
    read = lambda key: int(credits[f"C{op_rows[key]}"].value)
    card = {
        "status": "workbook", "as_of": AS_OF, "label": "[ESTIMATE]",
        "operations": {
            "planning_per_video": read("planning_per_video"),
            "generation_per_second": {t: read(f"generation_per_second.{t}") for t in ("draft", "standard", "premium")},
            "assembly_per_minute": read("assembly_per_minute"),
        },
    }
    (ROOT / "poc" / "rate_card.json").write_text(json.dumps(card, indent=2), encoding="utf-8")

    sheet = values["Video_Models"]
    providers = [{"name": "mock", "price_per_second_usd": 0, "max_clip_seconds": 30, "max_width": 1920,
                  "max_height": 1080, "supports_references": True, "licence_verdict": "Allowed"}]
    for offset, route in enumerate(ROUTES, 2):
        providers.append({
            "name": route["key"], "display_name": route["name"], "kind": route["kind"],
            "price_per_second_usd": round(sheet[f"E{offset}"].value, 6), "max_clip_seconds": route["clip"],
            "max_width": route["w"], "max_height": route["h"], "supports_references": route["refs"],
            "licence_verdict": route["verdict"], "verdict_source": route["src"],
        })
    for key, label, source in (("minimax_h3_open_weights", "MiniMax H3 open weights", "R2-002"),
                               ("hunyuanvideo_15", "HunyuanVideo 1.5", "R2-059")):
        providers.append({"name": key, "display_name": label, "kind": "self", "price_per_second_usd": None,
                          "max_clip_seconds": 5, "max_width": 1280, "max_height": 720, "supports_references": True,
                          "licence_verdict": "Blocked", "verdict_source": source})
    catalog = {"status": "workbook", "as_of": AS_OF, "providers": providers}
    (ROOT / "poc" / "provider_catalog.json").write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    return values["Checks"]["C12"].value


def main():
    OUT.parent.mkdir(exist_ok=True)
    op_rows, _, _ = build()
    recalculate()
    overall = export(op_rows)
    print("Workbook checks:", overall)
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
