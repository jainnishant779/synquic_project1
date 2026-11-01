# GPU, Deployment Cost and Credit Pricing

**As of 2026-11-01.** All figures are `[ESTIMATE]`, computed in [the workbook](../workbook/synquic_comparison_pricing.xlsx). Tier volumes are `[ASSUMPTION]`, not traction. Change inputs on the `Inputs` sheet only.

## Summary

The biggest unknown is not GPU price. It is how many generations a usable shot takes, and nobody has published a reliable figure.

- At the default 25% accept rate, a 5-minute video on Runway Gen-4.5 costs about $147. [WB:Sensitivity]
- At the best self-reported rate, 85%, it costs about $46. [WB:Sensitivity]
- That is a threefold swing from one input, so **unit economics cannot be committed until a pilot measures it**.

The earlier report's $6.08 per 5-minute video is not supportable. Its own unit costs add up to more, and it leaves out keyframes, voice, QC and upscaling. See [doc 09](09-claims-register.md).

## Accept rate

| Scenario | Rate | USD per accepted second, Gen-4.5 | All-in USD, 5-minute video | Retail USD at target margin |
|---|---|---|---|---|
| Default | 0.25 | 0.48 | 147 | 628 |
| Three takes | 0.333 | 0.36 | 111 | 474 |
| Self-reported low | 0.61 | 0.20 | 62 | 270 |
| Self-reported high | 0.85 | 0.14 | 46 | 195 |

[WB:Sensitivity] Switch scenarios with `accept_selector` on `Inputs`.

The 25% is an assumption by choice. Its source is a marketing FAQ reporting 41 of 164 clips in one episode, not telemetry (V-042). The 61% to 85% figures are self-reported with undefined acceptance (R4-059, R4-060). Published overshoot ratios range from 3:1 to 300:1 on different definitions (R4-061, R4-066). Keyframe-first may improve the rate, but nothing measured supports a number.

## GPU rental

On-demand rates. [WB:GPU]

| Offer | USD per hour | USD per month, always on | Facts |
|---|---|---|---|
| RunPod RTX 4090, 24 GB | 0.89 | 650 | R3-001 |
| RunPod L40S, 48 GB | 1.09 | 796 | R3-003 |
| RunPod A100, 80 GB | 1.79 | 1,307 | R3-005, V-009 |
| RunPod H100 SXM, 80 GB | 3.99 | 2,913 | R3-007 |
| RunPod H200, 141 GB | 5.29 | 3,862 | R3-009 |
| Lambda H100 SXM, single | 4.29 | 3,132 | R3-035 |
| AWS p5.4xlarge, one H100 | 6.88 | 5,022 | R3-084 |

**Choice: RunPod Secure Cloud.** Per-second billing, no egress fees, a public DPA and vendor-stated SOC 2 Type II; no report was read (R3-022, R3-026, R3-027, R3-028).

**Traps**

- Stopped volume disks cost double, $0.20 against $0.10 per GB per month (R3-023, R3-024).
- Do not budget on spot. RunPod retired it, and AWS H100 spot in us-east-1 sat above on-demand (R3-012, R3-085, R3-089).
- CoreWeave prices are per 8-GPU instance, not per GPU (R3-056).
- RunPod's serverless page and docs disagree on rates (R3-013, R3-014, R3-017, R3-018), and cold starts and idle time are billed (R3-020, R3-021).
- The earlier report's $2.15 A100 and $6.35 H200 rates are wrong for RunPod Pods (V-009, R3-009).

## Cost per usable video

All-in cost adds generation, QC and a supporting stack: planning, keyframes, voice, music, lip-sync and storage. That stack is about $0.63 per finished minute. [WB:Unit_Costs]

| Route | Licence | Raw USD/s | USD per kept 5 s clip | All-in USD, 5-minute video |
|---|---|---|---|---|
| Wan 2.2 TI2V-5B I2V, RTX 4090 | Allowed | 0.04 | 0.80 | 51 |
| Runway Gen-4 Turbo | Allowed | 0.05 | 1.00 | 63 |
| Luma Ray3.2, 720p | Allowed | 0.06 | 1.20 | 75 |
| MiniMax H3 API, 768p | Counsel | 0.08 | 1.60 | 99 |
| Wan 3.0 API, 720p | Counsel | 0.10 | 2.00 | 123 |
| Runway Gen-4.5 | Allowed | 0.12 | 2.40 | 147 |
| Kling 4.0, 1080p | Counsel | 0.235 | 4.70 | 285 |
| Wan 2.2 A14B, H100 | Allowed | 0.355 | 7.10 | 429 |

[WB:Unit_Costs] At the default 25% accept rate. Self-hosted rows assume 65% utilisation `[ASSUMPTION]` and rest on `[VENDOR-CLAIM]` render times (V-901, R2-049), with no quality comparison.

Two surprises. The larger open model on an H100 is the most expensive route listed, not a saving. And the stack cost is small: generation dominates.

## Self-hosting breakeven

Standard-tier generation only, on Wan 2.2 TI2V-5B on an RTX 4090, against Gen-4.5. [WB:Breakeven]

| | Seed | Launch | Scale |
|---|---|---|---|
| Videos per month `[ASSUMPTION]` | 250 | 2,500 | 25,000 |
| API cost, USD | 4,320 | 43,200 | 432,000 |
| GPUs needed | 3 | 23 | 222 |
| Self-host total with one engineer, USD | 13,949 | 26,943 | 156,233 |
| Saving, USD | -9,629 | 16,257 | 275,767 |
| Recommendation | Stay on API | Self-host | Self-host |

[WB:Breakeven] Breakeven GPU utilisation is about 22%, before engineering cost.

**This is provisional.** It compares a 5B model to a premium API as though the footage were equivalent, and that is not established. One hour of a rented GPU would replace the render figure. Treat it as a direction, not a decision.

## Credit-based pricing

Credits are priced from real cost, so margin survives the deepest pack. [WB:Credits]

```
accepted_sec  = (raw_sec + qc_cost_per_sec) / first_pass_accept_rate
credit_budget = cheapest_pack_price_per_credit x (1 - target_gm - payment_fee_pct)
credits(op)   = ROUNDUP(cogs(op) x (1 + risk_buffer) / credit_budget)
```

| Operation | COGS USD | Credits | Retail USD, cheapest pack | Margin, cheapest pack | Source |
|---|---|---|---|---|---|
| Planning, per video | 0.004 | 2 | 0.03 | 84% | [WB:Credits] |
| Generation, draft, per second | 0.20 | 52 | 0.86 | 74% | [WB:Credits] |
| Generation, standard, per second | 0.48 | 124 | 2.06 | 74% | [WB:Credits] |
| Generation, premium, per second | 0.94 | 242 | 4.02 | 74% | [WB:Credits] |
| Assembly, per minute | 0.49 | 126 | 2.09 | 74% | [WB:Credits] |

[WB:Credits] Packs are $39 for 2,000, $99 for 5,500 and $299 for 18,000 credits `[ASSUMPTION]`.

**Rules that protect margin**

- Automatic QC regenerations are inside the rate, so customers are never charged for them, and nothing is counted twice.
- Credits are set from the cheapest pack.
- Unused credits count as zero margin. Free credits are acquisition cost, not COGS.
- Provider failures must be refunded and reconciled against actual vendor bills, because vendors differ on billing failed jobs ([doc 01](01-video-models-and-pricing.md)).
- Reprice whenever a vendor rate changes. The workbook rebuild writes `poc/rate_card.json`, so the product and the model share one source. [REAL: test_rate_card_matches_the_workbook]

**The commercial problem.** At the default rate and 70% target, a 5-minute standard video retails at about $628. [WB:Sensitivity] That is unlikely to sell against competitors bundling generation in cheap subscriptions. There are three levers, in order: raise the accept rate through keyframe-first and QC, shift the mix to cheaper routes, and sell short-form video first. A 30-second ad at the same rates is far easier to price.

## Monthly deployment cost

Video COGS, plus Social 360 inference and training. [WB:Tiers]

| Monthly `[ESTIMATE]`, USD | Seed | Launch | Scale |
|---|---|---|---|
| Brands `[ASSUMPTION]` | 10 | 100 | 1,000 |
| Video COGS | 6,788 | 51,626 | 403,066 |
| Social 360 COGS | 1,329 | 2,831 | 12,634 |
| Total COGS | 8,117 | 54,458 | 415,700 |

[WB:Tiers] Assumes 60-second average videos, a 50% Social 360 attach rate, and 1, 2 and 8 inference GPUs. Payroll, CDN overage and SOC 2 costs are excluded. The workbook also computes revenue, but since prices are set from cost, the resulting margin is a design target and says nothing about demand.

**Social 360 cost is mostly one always-on GPU.** That is fixed, so per-brand cost falls quickly with scale. Training hours are `[ASSUMPTION]`, since no reliable published figure exists (R6-011, R6-012, R6-013).

## What would replace these estimates

| Unknown | Test | Rough cost |
|---|---|---|
| Accept rate, per route | 50 to 100 shot pilot on 2 or 3 models | [ESTIMATE] about $200 to $500 of API spend |
| Self-host render time and quality | One day on a rented RTX 4090 and an H100 | [ESTIMATE] under $100 |
| LoRA on the chosen base | One adapter smoke test in vLLM | [ESTIMATE] under $50 |
| Adapter training time | Timed run on an L40S | [ESTIMATE] under $50 |
