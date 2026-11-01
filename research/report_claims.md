# Audit list: "AI Video and LLM Architecture" report

Source: `docs\AI Video and LLM Architecture.pdf`, supplied by the user on 2026-11-01. Treated as input to check, not as a source of record. Most of its pricing citations are blogs, aggregators or Reddit, so under `RESEARCH_RULES.md` they can raise a question but not settle one. The PDF still contains `[span_N]` artefacts from the tool that generated it.

Nothing below is a finding about vendors until checked. Section A is arithmetic on the report's own numbers. Sections B to D are for the verifier, and the suspicions there come from memory, so they must be confirmed from primary sources or dropped.

## A. Arithmetic on the report's own numbers (checked)

| Item | Report says | Recomputed | Effect |
|---|---|---|---|
| Hero shot COGS, Table 4 | $0.240 at "1.3x API take" | Luma 720p $0.30 x 1.3 = $0.39; Gen-4.5 $0.60 x 1.3 = $0.78; Kling Pro $0.60-0.85 x 1.3 = $0.78-1.11; Luma 1080p $1.20 x 1.3 = $1.56 | Understated by 1.6x to 6.5x |
| Standard HD COGS, Table 4 | $0.085, "70% local A100 / 30% Turbo API" | 0.7 x $0.107 + 0.3 x $0.25 = $0.150 before retakes | Understated by about 1.8x |
| Per-minute retail, Table 4 | $0.40, $3.00, $2.00, $9.00, $28.00 | 5 s clips mean 12 per minute: $0.48, $3.60, $2.40, $10.80, $33.60 | Column uses 10 per minute |
| 30 s ad COGS, section 2.6 | Below $0.45 | 6 x $0.085 = $0.51, on the report's own unit cost | Inconsistent |
| 5-minute COGS $6.08 | "Total compute & API" | The sum 20 x 0.035 + 35 x 0.085 + 10 x 0.24 = $6.08 is right, but with the two corrected units (35 x 0.15 and 10 x 0.39 to 1.56) it is $9.85 to $21.55, still on the report's own unit prices. The tier is specified at 1080p, which rules out the $0.39 route: Gen-4.5 at $0.78 gives $13.75 | Stated 74.1% margin falls to 58% at best and 8% at worst; 41% on Gen-4.5 |
| Omitted from $6.08 | | 130-150 keyframes per video (at Runway's 8 credits, about $10.40-12.00), TTS, planning LLM, QC compute, upscaling, storage | Further understatement |
| Plan discounts, Table 5 | Margin computed at $0.02 per credit | Agency annual is $249 / 18,000 = $0.0138 per credit | Deepest pack earns 31% less per credit |
| Hero seconds, Table 9 | 4,000 s for 250 videos | 10 hero shots x 5 s x 1.3 x 250 = 16,250 s | Volume understated 4x against Table 4 |
| A100 hours, Table 9 | 250 h for 250 videos | 35 shots x 180 s x 250 = 437 h before retakes | Under-provisioned |
| Phase totals and margins, Table 9 | $3,139; $18,005; $138,192; 74.9%, 76.9%, 77.7% | Sums and ratios are correct | MRR behind them has no stated basis |
| Credit mix, Table 4 | 1,175 credits, $23.50 | Correct | |

## B. Claims with no basis in the report (cannot be presented as results)

- Table 7 benchmark figures for Social 360: only the last column is headed "Target", the rest have no citation, and the model does not exist. Includes the GPT-4o and Claude 3.5 baselines.
- Table 8 demo outputs presented as observed: "viral accuracy 41% to 79%", "DINO: 0.94", "LSE-C: 7.8", "<350 ms TTFT", "135 seconds".
- "2.5 million cross-platform marketing analytics records": no provenance.
- MRR of $12,500, $78,000, $620,000; the 10, 100 and 1,000 brand counts.
- "beating baseline benchmarks by >25%", ">75% gross margin verified in production telemetry across 100+ active brand workspaces", within 16 weeks.
- SOC 2 Type II readiness inside 16 weeks; compare with R7's timeline.
- QC thresholds (DINO 0.92, CLIP 0.90, smoothness 0.95, LAION 6.0, ArcFace 0.82, LSE-C): check whether any is published or whether they are invented.

## C. Claims that break the honesty rules in the plan

- "domain-specific foundation model", "Proprietary AI Model".
- "mathematically preventing cross-tenant adapter invocation or KV-cache prefix leakage", "mathematically isolated", "ironclad", "strict cryptographic tenant isolation". An API gateway does not address a shared KV or prefix cache. Check against R6.
- "zero-human-in-the-loop" QC, "zero human engineers can view raw customer records".
- "continuous learning"; "broadcast-ready".
- "mathematically constrained to interpolate" between keyframes.
- "verified 2026 RunPod cloud GPU pricing": no verification shown.

## D. Facts for the verifier to check against primary sources

Licences, highest priority because they can block a production route:
- XTTS-v2 weights: production use; suspected non-commercial model licence.
- FLUX.1 keyframe model: which variant, and is it licensed for commercial SaaS.
- InsightFace, ArcFace pretrained models and IP-Adapter-FaceID: suspected non-commercial pretrained weights. Report makes them the identity gate.
- MuseTalk 1.5, LivePortrait, Hallo2, EchoMimicV2, LatentSync, SyncNet: weights and every dependency, not only the repo licence.
- LTX 2.3: report says Apache 2.0 with "unrestricted commercial deployment". Mochi 1, Wan 2.1, CogVideoX-5B: same check. Note any revenue threshold.
- HunyuanVideo 1.5: exact restriction; report says "restricted for competing SaaS".
- GPT-OSS: report says Apache 2.0, 20B and 120B. Confirm, including usage policy and naming.
- Qwen2.5-14B, Qwen3: Apache 2.0 per size; Qwen2.5-72B licence differs per report's use as teacher, so check.
- DeepSeek-V3, R1 distilled: "MIT / Apache 2.0". Llama-3 terms.

Prices and specs:
- Runway API: $0.01 per credit, Gen-4.5 12, Gen-4 Turbo 5, Aleph 2.0 28, Kling 3.0 and Seedance tiers; Grok Imagine; Wan3.
- Luma Ray 3.2 tiers and HDR or EXR multipliers; Ray 2 through Apiframe.
- Veo 3.1 "$0.40 per second". R1 could not read direct Veo pricing.
- RunPod RTX 4090 $0.89, A100 SXM $2.15, H200 SXM $6.35.
- Render times in Table 2, per GPU, resolution and steps. Cost per clip follows directly from these.

Technical:
- "25% keep rate" attributed to InVideo telemetry.
- "VBench-2.0" with 16 dimensions: does it exist under that name, and how does it differ from VBench.
- FastLibra paper figures: 730.8 ms, 1,032.4 ms, 1,905.1 ms; is the patch available for production vLLM.
- vLLM flags, default LoRA memory fraction, AIBrix adapter controller states.
- Whether Wan 2.1 and Qwen2.5 are superseded as of 2026-11-01. R1 reports Wan 3.0 exists.

Data rights, check against R7:
- Ingesting "competitor post transcripts", "live competitor content gaps" and "trending motifs" through platform APIs.
- Using brand telemetry from Meta, TikTok, YouTube, LinkedIn and X to train adapters.

## F. Second report: "AI Video Generation Engine & Social360 Model Research"

Source: `docs\AI Video Generation Engine & Social360 Model Research.pdf`, 5 pages, author metadata "ChatGPT Deep Research". Its citations are unresolvable markers such as `【21†L113-L119】`, and one line still contains a `$X` placeholder. The sources it names are mostly secondary.

To check:
- Licence: "both GPT-OSS and Llama-2 are Apache 2.0"; Open-Sora Apache 2.0; CogVideoX-1.5; "Wan 2.2/3.0 (Apache-2.0)" against R2's finding that core open weights stop at 2.2.
- LTX-2.5 at 22B, 32 GB VRAM at FP8, native audio, and its use as the POC's default open model. R2 has the licence as Counsel.
- Wan 2.2 and HunyuanVideo needing about 80 GB; A100 and H100 at $3-$8 per hour against R3's rates.
- Seedance 2.0 at about $9 per minute at 1080p; Veo 3.1 at $0.03-$0.40 per second; Sora 2 at $0.10-$0.70 listed as a live option, when R1 reports the API ended.
- "8×A100 (p4d.24xlarge) spot cluster, about $3/hr per GPU" can fine-tune a 20B model "in a few hours". R3 advises against budgeting on spot and R6 found thin timing evidence.
- Costs: about $10K for an initial model build; $500-$1000 per month per inference server; 50% margin. One always-on GPU at R3's rates is likely to exceed that server figure.

Already in conflict with decisions or findings:
- "Anthropic Claude" listed as an open-weight alternative. It is not open-weight.
- "learns from aggregate brand experience" contradicts the chosen tenancy, where tenant data never reaches the shared base.
- "the model is our own IP" breaks the wording rule. Use the required "built on [base] under [licence]" wording.
- "API usage ... to social platforms" as a training source, and daily or hourly fine-tuning, conflict with R7 and with gated retraining.
- "open-weights ... match closed SaaS quality at near-zero marginal cost" is contradicted by its own GPU cost and by R2's render times.

## E. Reference guide pasted by the user, 2026-11-01

The guide marks these "verified". In this ledger only V sets that status, so each one is re-checked at the vendor page. Where it agrees, the fact is confirmed; where it disagrees, record a conflict and resolve it by a fresh fetch.

- Sora: web closed 2026-04-26, API off 2026-09-24. R1 agrees on the API date.
- Runway web credits $0.024 monthly and $0.0192 annual, separate from API balance.
- Kling 4 on Runway: 12.56 and 18.8 credits per second as a 20% promo to 2026-11-30; list 15.7 and 23.5. Baseline uses list. R1 flagged the same promo.
- Runway-hosted catalogue: Kling 3.0 standard, pro and 4K; wan3 at 5, 10, 20; seedance2_5 at 20, 30, 68 with an 80 credit minimum.
- Luma: Ray 3.2 SDR $0.30 and $1.20 for 5 s, $0.90 and $3.60 for 10 s, V2V $1.44 and $2.16, Draft $0.012 per second; HDR 2x; HDR+EXR 3x. Apiframe Ray 2 at $1.12 to $2.03 per clip, with failed jobs refunded.
- Wan 2.1: 8.19 GB, 9.8 GB, about 240 s and about 123 s on a 4090, 18.8 GB T5 encoder. The workbook's example `render_sec_per_output_sec = 48.0` depends on the 240 s figure.
- Hunyuan: verdict Counsel; blogs mislabel it as Apache 2.0.
- Replicate wrappers for LivePortrait and MuseTalk: commercial use prohibited even where the core repo permits it.
- RunPod: RTX 4090 $0.89, A100 SXM $2.15, H200 SXM $6.35; L40S and H100 SXM contact sales.
- InVideo keep rate 25%; Activepieces' 3-take figures for 5,000 clips.
- vLLM default 0.2 LoRA memory ratio causing latency spikes.

Decisions already taken on the guide:
- `first_pass_accept_rate` defaults to 0.25 as a blue `[ASSUMPTION]`, with a sensitivity table. The table spans 0.25, 0.333, and R4's self-reported 0.61 to 0.85, because R4 found no solid figure and these numbers use different definitions.
- Canaries are not redacted before dataset construction. A redacted canary cannot leak, so the leak tests would pass vacuously. PII is redacted as normal.
- Scraped third-party social data is `Blocked` and a brand's own OAuth-authorised data is `[COUNSEL]`, pending R7.
