# GPU, Deployment Cost and Credit Pricing

**As of 2026-11-01.** All figures are `[ESTIMATE]`, computed in [the workbook](../workbook/synquic_comparison_pricing.xlsx). Tier volumes, labour rates and pack prices are `[ASSUMPTION]`, not traction. Change inputs on the `Inputs` sheet only.

## Final launch plan

Full-AI video at 5 minutes was rejected on cost. The final plan is a hybrid: AI video on key shots under a hard spend cap, with animated stills everywhere else and as the fallback for failed shots. It launches at 30 seconds. See [Task1-Final-Plan-and-Research.docx](Task1-Final-Plan-and-Research.docx).

| Format | AI spend cap | Accepted AI video | Cost range | Retail at target margin | Source |
|---|---|---|---|---|---|
| 30-second, Veo Fast | $2.00 | 5 to 10 s | $1.45 to $2.27 | $8.42 | [WB:Launch_Plan] |
| 60-second, Veo Fast | $3.00 | 7.5 to 15 s | $2.21 to $3.45 | $12.77 | [WB:Launch_Plan] |
| 5-minute, Veo Fast | $3.50 | 8.8 to 25 s | $4.70 to $5.26 | $19.49 | [WB:Launch_Plan] |
| 5-minute, Veo Standard | $6.50 | 8.1 to 25 s | $7.64 to $8.26 | $30.60 | [WB:Launch_Plan] |

Ranges run from a 25% to an 85% accept rate. [ESTIMATE] These exclude human review, motion graphics engineering, licensed footage and legal cost. The cap holds cost, but a low accept rate cuts the AI share of the video. Rates are V-914 and V-003; stills use V-919. The pilot is budgeted at about $486. [WB:Launch_Plan]

The rest of this document is the full-AI analysis that led to that decision.

## Summary

The biggest unknown is not GPU price. It is how many generations a usable shot takes, and nobody has published a reliable figure. That one number decides cost, retail price, and whether a long video can finish without a person.

- A 5-minute video on Runway Gen-4.5 costs about $51 at an 85% accept rate, $258 at 25%, and $551 at 10%. [WB:Sensitivity]
- None of those rates is a measured first-pass rate per shot, so this is a sensitivity, not a range to plan on.
- At 25%, the 3-attempt pipeline almost never finishes a 60-shot video unaided, and human rework becomes the largest single cost after generation. [WB:Sensitivity]

**Unit economics cannot be committed until a pilot measures this.** The earlier report's $6.08 per 5-minute video is not supportable: see [doc 09](09-claims-register.md).

## Accept rate

The model assumes a shot is regenerated until accepted. The real pipeline stops after 3 automatic attempts, and a person handles what is left, so labour is modelled as well.

| Scenario | Rate | Generation USD per accepted second | Rework USD per finished minute | All-in USD, 5-minute video | Retail USD at target margin | Chance a 60-shot run needs no human | Source |
|---|---|---|---|---|---|---|---|
| Stress | 0.10 | 1.20 | 36.45 | 551 | 2,348 | about 0 | [WB:Sensitivity] |
| Default | 0.25 | 0.48 | 21.09 | 258 | 1,099 | about 0 | [WB:Sensitivity] |
| Three takes | 0.333 | 0.36 | 14.84 | 191 | 816 | about 0 | [WB:Sensitivity] |
| Self-reported low | 0.61 | 0.20 | 2.97 | 82 | 354 | 2.6% | [WB:Sensitivity] |
| Self-reported high | 0.85 | 0.14 | 0.17 | 51 | 220 | 82% | [WB:Sensitivity] |

Rework assumes 10 minutes per failed shot at $30 per hour `[ASSUMPTION]`. It overlaps slightly with generation cost, which is the conservative direction. Switch scenarios with `accept_selector` on `Inputs`.

**How weak these inputs are.** The 25% is the chosen default, and its source is a marketing FAQ reporting 41 of 164 clips in one episode. It measures selection for a final cut, not first-pass acceptance (V-042). The 85% estimates a share of a video, not a first-pass rate per shot (R4-060). Hard shots are reported at 8 or more generations (R4-061). Published overshoot ratios range from 3:1 to 300:1 on different definitions (R4-061, R4-066). Keyframe-first may improve the rate, but nothing measured supports a number.

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

**Choice: RunPod Secure Cloud.** Per-second billing, no egress fees, a public DPA and vendor-stated SOC 2 Type II (R3-022, R3-026, R3-027, R3-028). No report was read, and the vendor says coverage varies by workload, region and provider. Prices were region-unspecified, so data residency must be confirmed before any EU workload.

**Traps**

- Stopped volume disks cost double, $0.20 against $0.10 per GB per month (R3-023, R3-024).
- Do not budget on spot. RunPod retired it (R3-012). AWS H100 spot in us-east-1 sat above on-demand, though other regions were far below it, and it interrupts with two minutes' warning (R3-085, R3-089).
- CoreWeave prices are per 8-GPU instance, not per GPU (R3-056).
- RunPod's serverless page and docs disagree on rates (R3-013, R3-014, R3-017, R3-018), and cold starts and idle time are billed (R3-020, R3-021). Accounts have a default $80 per hour limit, which is raisable (R3-021).
- The earlier report's $2.15 A100 and $6.35 H200 rates are wrong for RunPod Pods (V-009, R3-009).

## Cost per usable video

All-in cost adds generation, QC and a supporting stack: planning, keyframes, voice, music, lip-sync, storage, upscaling, human review and rework. At the 25% default that stack is about $22.73 per finished minute, of which $21.09 is rework. [WB:Unit_Costs]

| Route, at the default accept rate | Licence | Raw USD/s | USD per kept 5 s clip | All-in USD, 5-minute video | Source |
|---|---|---|---|---|---|
| LTX-2.5 distilled, RTX 4090, 640x384 | Counsel | 0.003 | 0.07 | 118 | [WB:Unit_Costs] |
| daVinci-MagiHuman, H100, 1080p | Counsel | 0.013 | 0.26 | 129 | [WB:Unit_Costs] |
| Wan 2.2 TI2V-5B I2V, RTX 4090 | Allowed | 0.04 | 0.80 | 162 | [WB:Unit_Costs] |
| MiniMax H3 Lite API, 768p | Counsel | 0.04 | 0.80 | 162 | [WB:Unit_Costs] |
| Runway Gen-4 Turbo | Counsel | 0.05 | 1.00 | 174 | [WB:Unit_Costs] |
| Luma Ray3.2, 720p | Counsel | 0.06 | 1.20 | 186 | [WB:Unit_Costs] |
| MiniMax H3 API, 768p | Counsel | 0.08 | 1.60 | 210 | [WB:Unit_Costs] |
| Wan 3.0 API, 720p | Counsel | 0.10 | 2.00 | 234 | [WB:Unit_Costs] |
| Runway Gen-4.5 | Counsel | 0.12 | 2.40 | 258 | [WB:Unit_Costs] |
| Kling 4.0, 1080p | Counsel | 0.235 | 4.70 | 396 | [WB:Unit_Costs] |
| Wan 2.2 A14B, H100 | Allowed | 0.355 | 7.10 | 540 | [WB:Unit_Costs] |

Self-hosted rows assume 65% utilisation `[ASSUMPTION]` and rest on `[VENDOR-CLAIM]` render times (V-901, R2-049, R2-033, R2-085), with no quality comparison. The LTX and MagiHuman figures are for different resolutions and purposes, so they do not compare directly.

**Licence column.** It covers the video route only. Every all-in figure also includes a keyframe API, a lip-sync API and music whose terms are unread or Counsel ([doc 01](01-video-models-and-pricing.md)). No API route is clear today.

**What is still not included.** OCR, identity embedding, orchestration, CDN overage, support, and the vendor spend on runs abandoned part-way. `run()` charges no credits for a failed job, so that spend is unrecovered.

## Self-hosting breakeven

Standard-tier generation only, on Wan 2.2 TI2V-5B on an RTX 4090, against Gen-4.5. This is a **what-if**. It is off in the cost tables below, through `selfhost_enabled` on `Inputs`. [WB:Breakeven]

| | Seed | Launch | Scale | Source |
|---|---|---|---|---|
| Videos per month `[ASSUMPTION]` | 250 | 2,500 | 25,000 | [WB:Breakeven] |
| API cost, USD | 4,320 | 43,200 | 432,000 | [WB:Breakeven] |
| GPUs needed | 3 | 23 | 222 | [WB:Breakeven] |
| Self-host total with one engineer, USD | 13,949 | 26,943 | 156,233 | [WB:Breakeven] |
| Saving, USD | -9,629 | 16,257 | 275,767 | [WB:Breakeven] |
| Clears the saving threshold | No | Yes | Yes | [WB:Breakeven] |

Breakeven GPU utilisation is about 22%, before engineering cost. [WB:Breakeven]

**Treat this as a direction, not a decision.** It compares a 5B model with a premium API as though the footage were equivalent, which is not established. One engineer cannot plausibly run 222 GPUs, which would also cost about $197 per hour against a default $80 account limit (R3-021). Availability of that many Secure Cloud 4090s is unverified. One day on a rented GPU would replace the render figure.

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
| Assembly with human review, per minute | 22.59 | 5,793 | 96.23 | 74% | [WB:Credits] |

Packs are $39 for 2,000, $99 for 5,500 and $299 for 18,000 credits `[ASSUMPTION]`. These margins are mechanical: prices are computed from cost, so they say nothing about whether anyone would pay.

**Rules that protect margin**

- Automatic QC regenerations are inside the rate, so customers are never charged for them, and nothing is counted twice.
- Credits are set from the cheapest pack.
- Unused credits count as zero margin. Free credits are acquisition cost, not COGS.
- Provider failures must be refunded and reconciled against actual vendor bills, because vendors differ on billing failed jobs ([doc 01](01-video-models-and-pricing.md)).
- Reprice whenever a vendor rate changes. The workbook rebuild writes `poc/rate_card.json`, so the product and the model share one source. [REAL: test_rate_card_matches_the_workbook]

**The commercial problem.** At the default rate these prices do not work:

| Item at the default accept rate and target margin | Result | Source |
|---|---|---|
| 30-second standard video | 9,515 credits, about $158 | [WB:Credits] |
| 5-minute standard video | 66,167 credits, about $1,099 | [WB:Credits] |
| What the $39 pack buys | 16 s of generation, a fifth of a 30-second video | [WB:Credits] |
| What the $299 pack buys | 145 s of generation, under two 30-second videos | [WB:Credits] |
| Retail per generated second | $2.06, against Runway's public $0.12 raw rate (R1-037, R1-038) | [WB:Credits] |

A customer can buy from Runway directly for far less, so this pricing fails. Competitor video pricing was not researched beyond Runway's plans (V-047), and it should be. There are three levers, in order: raise the accept rate, cut human handling per shot, and shift the mix to cheaper routes. At an 85% rate, a 5-minute video retails near $220. [WB:Sensitivity]

## Monthly deployment cost

All-API baseline, which is the recommended launch plan. Video COGS plus Social 360 inference, training and RAG. [WB:Tiers]

| Monthly `[ESTIMATE]`, USD | Seed | Launch | Scale | Source |
|---|---|---|---|---|
| Brands `[ASSUMPTION]` | 10 | 100 | 1,000 | [WB:Tiers] |
| Videos `[ASSUMPTION]` | 250 | 2,500 | 25,000 | [WB:Tiers] |
| Video COGS | 12,315 | 123,148 | 1,231,482 | [WB:Tiers] |
| Social 360 COGS | 1,454 | 4,081 | 25,134 | [WB:Tiers] |
| Total COGS | 13,768 | 127,230 | 1,256,615 | [WB:Tiers] |
| Implied video spend per brand | 5,532 | 5,532 | 5,532 | [WB:Tiers] |

Assumes 60-second average videos, a 50% Social 360 attach rate, $25 per brand per month for RAG `[ASSUMPTION]`, and 1, 2 and 8 inference GPUs. Payroll, except reviewer time, and SOC 2 costs are excluded.

**Read the last row carefully.** The volumes imply about $5,532 per brand per month in video credits, roughly 11 times the assumed Social 360 price and above Emplifi's $1,249 starting price (R6-082). That is enterprise spending. The workbook also shows gross margin around 76% to 78%, but revenue is computed from cost, assumes every credit is redeemed, and uses the mean pack price. It is a design target and says nothing about demand. [WB:Tiers]

**Social 360 cost is mostly one always-on GPU.** That is fixed, so cost per brand falls quickly with scale. Training hours are `[ASSUMPTION]`, since no reliable published figure exists (R6-011, R6-012, R6-013).

## What would replace these estimates

| Unknown | Test | Rough cost |
|---|---|---|
| Accept rate and rework time, per route | 50 to 100 shot pilot on 2 or 3 models | [ESTIMATE] about $200 to $500 of API spend |
| Self-host render time and quality | One day on a rented RTX 4090 and an H100 | [ESTIMATE] under $100 |
| LoRA on the chosen base | One adapter smoke test in vLLM | [ESTIMATE] under $50 |
| Adapter training time | Timed run on an L40S | [ESTIMATE] under $50 |
| Willingness to pay | Competitor price survey and design-partner conversations | [ESTIMATE] time only |
