# Video Models and Pricing

**As of 2026-11-01.** Prices come from vendor pages, re-fetched by a separate AI verifier agent. No human has reviewed them. The full comparison is in [the workbook](../workbook/synquic_comparison_pricing.xlsx). Licence verdicts are `[COUNSEL]`: research for a lawyer to review, not legal advice. Verdicts assume a commercial SaaS with global customers.

## Recommendation

1. **Launch on paid APIs through a multi-vendor adapter.** Vendors disappear: the Sora API ended 2026-09-24 and Gemini API Veo previews ended 2026-10-22 (R1-001, R1-020).
2. **Use Runway for the cost baseline, pending counsel.** Gen-4 Turbo and Gen-4.5 have clear published prices (R1-037, R1-038, R1-040). Its terms allow commercial use of outputs, but say inputs and outputs may train its models, bar using the service for "similar or competitive products", and require "Powered by Runway" in applications (V-903, V-904, V-905, V-906). Counsel must clear this, and brand assets should not be sent until an enterprise agreement covers input training. Tier 1 limits are also tight (R1-048).
3. **Make Wan 2.2 the open-weight default.** It is the clean Apache 2.0 option (R2-045).
4. **Talk to Lightricks now.** LTX-2.5 has the best spec, but its licence bars directly competing products and caps revenue at USD 10M, so it may become Blocked without a commercial licence (R2-025, R2-026).
5. **Do not rely on open-weight MiniMax H3 or HunyuanVideo 1.5** for a US or EU product (R2-002, R2-059). The H3 paid API is a separate agreement, and its terms are unread (R1-087).

No quality ranking is given. Quality cannot be verified from primary sources, so the pilot in [doc 03](03-video-production-architecture.md) must supply it.

## Paid APIs

Prices are raw list rates. A real cost per usable second is much higher: see [doc 06](06-gpu-deployment-cost-assessment.md). The workbook uses 10 s and 720p for both Runway routes as `[ASSUMPTION]`, because the API pages read did not state them.

| Model | Route | USD per second | Conditions | Max clip | Facts |
|---|---|---|---|---|---|
| MiniMax H3 Lite | Direct | 0.04 | 768p | 15 s | R1-077, R1-080 |
| Runway Gen-4 Turbo | Direct | 0.05 | Image-to-video | Not stated on pages read | R1-037, R1-040 |
| Luma Ray3.2 | Direct | 0.06 | $0.30 per 5 s clip, 720p SDR | 5 s with keyframes, 10 s without | R1-105, V-036 |
| MiniMax H3 | Direct | 0.08 | 768p | 15 s | R1-074, R1-080 |
| Wan 3.0 | Alibaba, Singapore | 0.10 | 720p list, API only | 30 s | R1-088, R1-091 |
| Gemini Omni Flash 1.1 | Google | about 0.10 | 720p, token-metered | 10 s | R1-003, R1-005 |
| Runway Gen-4.5 | Direct | 0.12 | Standard output | Not stated on pages read | R1-037, R1-038 |
| Kling 4.0 | Replicate | 0.157 / 0.235 | 720p / 1080p | 30 s | R1-056, R1-057, R1-059 |
| Veo 3.1 | Agent Platform | 0.20 / 0.40 | Audio off / on, 720p or 1080p. Unit printed as "/ 1 count" | 8 s | V-001, V-003, R1-024 |
| Seedance 2.5 | BytePlus | about 0.23 | 720p sample, no input video | 30 s | R1-065, R1-071 |

**Traps for the cost model**

- **Promos.** Kling 4.0 on Runway is 20% off until 2026-11-30, so the baseline uses list price (R1-042, R1-043). Wan 3.0 carries a limited-time label (R1-088).
- **Audio.** It doubles Veo's price at 720p and 1080p (V-001, V-003).
- **Video input is billed.** Kling 4.0 on Replicate bills a 5 s edit as 10 s, and H3 Max input costs more than output (R1-058, R1-078).
- **Failed jobs.** Runway keeps credits on `SAFETY.INPUT` failures. MiniMax, Alibaba, BytePlus, Luma and Replicate do not bill failures, and fal covers server errors only (R1-050, R1-084, R1-095, R1-068, R1-111, R1-115, R1-117).
- **Upscaled output.** Omni 1080p and 4K are upscaled (R1-006).
- **Luma.** The 10 s option is barred with keyframes, which matters for a keyframe-first pipeline (V-036). Luma grants commercial rights only under an active paid subscription, and whether pay-as-you-go counts is for counsel (R1-112).
- **Availability.** Direct Veo GA models show retirement "November 17, 2026 or later" (R1-021). BytePlus's April 2026 availability list omits the US (R1-069).

**Unverified.** Kling direct prices and terms, MiniMax terms, xAI terms, Seedance terms and Pika prices could not be read (R1-053, R1-054, R1-055, R1-070, R1-087, R1-103, R1-122). Runway's enterprise terms were not read.

**No API route is clear today.** Every API route in the workbook is at Counsel. Failed-job statements come from vendor docs and have exceptions, such as `budget_exhausted` on Replicate (R1-117).

## Open-weight video models

Render figures are mostly vendor claims on differing hardware. They cannot be ranked against each other.

| Model | Verdict | Why | Render, as published | Facts |
|---|---|---|---|---|
| Wan 2.2 | Allowed | Apache 2.0, components clean, no audio | TI2V-5B I2V 524.8 s on one RTX 4090; A14B 1,041.5 s on one H100, 720p | R2-045, V-901, R2-049 |
| Wan 2.1 | Allowed | Apache 2.0, superseded | About 4 minutes for 5 s at 480p | V-043 |
| NVIDIA Cosmos3 | Allowed | OpenMDW-1.1, components not assessed | Conditions incomplete | R2-076, R2-078 |
| Prism | Allowed | MIT, preview, 80 GB GPU | None published | R2-088, R2-089 |
| LTX-2.5, LTX-2.3 | Counsel | Competition clause and USD 10M cap. Not Apache | 43.7 s at 640x384 on RTX 4090, tester unnamed | R2-025, R2-031, V-025, R2-033 |
| daVinci-MagiHuman | Counsel | Weights Allowed; Gemma-terms encoder; audio model free only under USD 1M revenue | 38.4 s for 5 s at 1080p on one H100 | R2-083, R2-084, V-032, R2-085 |
| Kandinsky 6.0 | Counsel | MIT, but attributed to Sber in press, and VAE provenance is open | 133.2 s, Full HD, one H100 | R2-069, R2-072 |
| CogVideoX | Counsel | CogVideoX License, not Apache | Superseded | R2-090, V-030 |
| MiniMax H3 | Blocked | Excludes US, EU, UK, Korea, including outputs; requires UI branding; bars training on outputs | 132.5 s for 5 s on one B200 | R2-002, R2-003, R2-005, R2-009 |
| HunyuanVideo 1.5 | Blocked | Excludes EU, UK, Korea. Counsel only if geofenced | 28.33 s on 8 H800s | R2-059, R2-064 |

Wan core open weights stop at 2.2. Wan 3.0 is API only: none of the 27 Wan-AI repos holds it (V-046). Comfy claims to resell an H3 commercial licence, which MiniMax has not confirmed (V-033). It is worth asking, since it could change that verdict.

## Supporting models

The earlier report's stack depends on several of these. Most fail as shipped.

| Component | Verdict | Finding | Facts |
|---|---|---|---|
| XTTS-v2 voice | Blocked | Non-commercial licence that binds output | V-011 |
| FLUX.1 dev keyframes | Blocked without a paid licence | Use FLUX.1 schnell (Apache) or an API | V-012, V-013, V-014 |
| InsightFace pretrained models | Blocked | Non-commercial research only | V-015 |
| IP-Adapter-FaceID | Blocked | Research only, depends on InsightFace | V-016 |
| LivePortrait | Blocked as shipped | MIT, but requires InsightFace `buffalo_l` | V-018 |
| Replicate LivePortrait wrapper | Blocked | Self-hosting has the same bar, for the same reason | V-019 |
| Hallo2 | Blocked as shipped | MIT code; S-Lab CodeFormer and InsightFace | V-020 |
| LatentSync | Blocked as shipped | Detector imports InsightFace. Apache code, OpenRAIL++ weights are Counsel | V-022 |
| EchoMimicV2 | Counsel | Weights carry no licence, "academic research" | V-021 |
| MuseTalk 1.5 | Allowed for weights | Components unread | V-017 |
| Real-ESRGAN | Allowed | BSD-3. Avoid `face_enhance`, which pulls non-commercial parts | V-024 |
| SyncNet | Code Allowed | Weights Counsel | V-023 |

**Tooling around the models**

| Tool | Verdict | Finding | Facts |
|---|---|---|---|
| WanGP | Blocked for paid hosting without an agreement | WanGP Community License, not Apache. Free locally and outputs can be sold, but paid API or SaaS access needs a separate agreement. Running a Blocked model through it does not clear that model | V-907, V-908 |
| BluShooz text-to-video-generator | Do not reuse as a stack | MIT, but built on XTTS-v2, which is Blocked | V-913, V-011 |
| DiffSynth-Studio | Unconfirmed | Layer-level disk offload is real. The licence was not confirmed, so read it before use | Not in ledger |
| LoRAX | Do not use | Archived | R6-046 |

**What this means.** No lip-sync or identity chain in the earlier report is commercially clear as shipped. The default stack is:

- **Voice:** a paid TTS API (R3-112).
- **Keyframes:** a paid image API (R3-110). FLUX API output terms are still unread. FLUX.1 schnell is the Apache fallback (V-013).
- **Lip-sync:** sync.so as a paid API (R3-126), whose terms are unread (R3-128). fal's LatentSync endpoint (R3-129) needs a vendor answer on whether the InsightFace models are licensed (V-022).
- **Music:** a legal decision first, since both reviewed options are Counsel (R3-121, R3-123). ElevenLabs also limits plans by headcount and bars resale (R3-121).

## Vendor terms to put to counsel

- Alibaba bars using Output to train competing products, and bars resale (R1-096).
- The Gemini API bars developing competing models (V-040).
- H3 bars using outputs to train other models (R2-005).
- Runway bars using outputs or services for similar or competitive products, and may train on inputs (V-903, V-904).

Do not use any generated video to train models without clearing this.
