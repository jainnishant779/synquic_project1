# Claims Register

**As of 2026-11-01.** Written for diligence reviewers. It lists what this work claims and on what evidence, and what it found wrong in the two earlier reports.

## How the research was done

AI-assisted, checked against primary sources on 2026-11-01. No human or lawyer has reviewed it. Seven AI research agents collected 711 facts, each with source URL, verbatim quote and date. Two separate AI verifier agents re-fetched 362 of them: every pricing and licence fact, plus a one-in-five sample of the rest. "Verified" means another agent in the same process confirmed the page says it, not that a third party audited it. The verifiers added 87 new facts and marked them verified themselves, and 13 more came from direct checks of render times, Runway's terms and a repository catalog, for a ledger of 811.

| Status | Facts |
|---|---|
| Verified | 423, of which 100 were created and marked by the checkers |
| Single source, unchecked | 294, outside the sampled set. Many support design rationale, not just description |
| Conflict | 50, recorded rather than averaged |
| Unverifiable | 37, mostly login walls and unread terms |
| Failed and corrected | 7 |

## Labels

| Label | Meaning |
|---|---|
| `[REAL: test]` | Runs today and is covered by the named test |
| `[MOCK]` | A stand-in for the real thing |
| `[SIMULATED]` | Synthetic data or simulated time |
| `[DESIGN]` | Specified, not built |
| `[ESTIMATE]` | Modelled, not observed |
| `[VENDOR-CLAIM]` | Published by the vendor, unreproduced |
| `[ASSUMPTION]` | Chosen by us. Change it on the `Inputs` sheet |
| `[COUNSEL]` | Needs a lawyer. Not legal advice |

## Register

| Claim | Label | Evidence |
|---|---|---|
| The video pipeline runs end to end with injected faults recovered | [REAL: test_regeneration_recovers_from_fault] | `poc/tests/test_video.py` |
| A 5-minute mock video assembles, with final QC, watermark sampled at 3 points | [REAL: test_five_minute_mock_run] | `poc/tests/test_video.py` |
| Clips are AI generated | No. [MOCK] | Watermark on every frame; `real_generation: false` |
| The API adapter works against a live provider | Unknown. [MOCK] fake server only | `api_http.py` docstring |
| No cross-tenant path found through the current HTTP routes | [REAL: test_isolation.py] | Review found and fixed two code-level paths. See below. Not a penetration test |
| Tenant isolation holds in cloud or on a shared GPU | [DESIGN] | Not tested |
| A model was trained | Tiny CPU classifier only. No LLM has been trained | `poc/social360/trainers/tiny.py` |
| Bad candidates are rejected and rollback works | [REAL: test_day_sequence] | Simulated days |
| Workbook key outputs match a separate Python recalculation | [REAL: tools/verify_workbook.py] | 31 checks, including Tiers and Sensitivity. It shares inputs with the build, so it tests formulas, not assumptions |
| Credits charged match the workbook | [REAL: test_rate_card_matches_the_workbook] | Rate card exported from cached values |
| Cost of a 5-minute video | [ESTIMATE] | See doc 06. Range depends on accept rate |
| Accept rate | [ASSUMPTION] | No solid figure exists (R4-059, R4-060, V-042) |
| Self-host saving | [ESTIMATE], [VENDOR-CLAIM] render times | Doc 06, no quality comparison |
| Base model choice | Provisional | Licence and adapter fit, no task benchmark (R5-107) |
| Adapters improve brand voice | Unknown | No study tested it (R6 brief). Pilot required |
| Data rights table | [COUNSEL] | R7, V2. TikTok and Reddit unread |
| Licence verdicts | [COUNSEL] | R2, V1 |
| Superiority over GPT or Claude | Not claimed | Protocol in doc 05, no results |

## Known gaps

- **TikTok and Reddit terms** could not be read (R7-012, R7-013, R7-019, R7-020).
- **Kling direct, MiniMax, xAI and Seedance terms and some prices** could not be read (R1-053, R1-054, R1-055, R1-070, R1-087, R1-103).
- **OpenAI policy pages, DPDP Rules, California AB 2013 and the current Anthropic Usage Policy** remain unread (V2 brief).
- **Coverage.** Facts outside the pricing and licence queue were sampled at one in five. 294 remain unchecked. A few priority legal and vLLM facts missed the queue and were verified separately (V-504, V-505, V-506, V-525, V-526, V-527).
- **Render times.** They were missed by the verifier queue, then checked directly against source. Vendor-reported, not reproduced.
- **Citations.** 168 of 343 cited facts were not verified at review time. Doc 02's design rationale rests largely on single-source facts.
- **Privacy.** Vendor retention, input training, residency and sub-processors are not researched beyond Runway's terms.
- **Pricing.** No competitor video price survey exists. The tier volumes imply about $5,500 per brand per month, which is unvalidated. [WB:Tiers]
- **Route limits.** The workbook's clip, resolution and reference limits per route are typed in `tools/build_workbook.py`, not loaded from the ledger, and some are `[ASSUMPTION]`.
- **Reference guide.** It was pasted into the session and is not filed in this repo, so that audit cannot be re-checked from these files.
- **Fetch method.** Some blocked pages stayed blocked. Where a page simply would not render, a plain request was used. One licence blocked on Hugging Face was read from the vendor's own repository.
- **Volatility.** Prices are a one-day snapshot. Trackers report October 2026 GPU rises, unverified.

## Red team

A separate AI reviewer attacked this data room as a diligence reviewer: [research/briefs/red_team.md](../research/briefs/red_team.md). It found 2 blockers, 18 major and 19 minor issues, and confirmed every doc table matched the workbook. Its mutation test killed only 4 of 13 mutations, so the tests were strengthened. Mutations were not re-run after the fixes.

| Finding | Outcome |
|---|---|
| Version string reached another tenant's adapter | Fixed. [REAL: test_04b_version_strings_cannot_traverse] |
| Reused tenant id served the old owner's cached adapter | Fixed. [REAL: test_10b_offboarded_ids_are_never_reused] |
| Monthly costs hid a self-host decision and a salary | Fixed. All-API baseline, with self-hosting behind a switch |
| Leakage gate misses learned leakage | Disclosed. [REAL: test_08c_byte_scan_limit_is_real] |
| Cost range ignored retry limits and labour | Fixed. Rework, review, upscaling and RAG added, with a feasibility column |
| "Clear commercial terms" for Runway | Fixed. Terms read: verdict moved to Counsel (V-903, V-904) |
| Router would pick Counsel routes, and the demo never exercised it | Fixed. Counsel needs opt-in; demo dry-runs the real catalog |
| Privacy gaps in the video pipeline | Partly. Section added to doc 03; the research itself is still open |
| Data pipeline had no eligibility enforcement | Partly. Tagging and filter built; connectors and TTLs remain `[DESIGN]` |
| QLoRA table misattributed, flattered Gemma over GPT-OSS | Fixed in doc 04 |
| Identity evidence was for a method outside the plan | Fixed in docs 02 and 03. No licensed identity check is chosen yet |
| Demo script failed on rerun | Fixed with `--fresh` |
| Cache ignored reference images | Fixed. [REAL: test_changed_references_are_not_served_from_cache] |
| Thin local production, reliability and integration answers | Partly. Design tables added, all `[DESIGN]` |
| Adapters and metadata plaintext; break-glass lacks a second approver | Disclosed in doc 04 |

## Earlier reports: audit

Two AI-generated reports were supplied during this work, plus a reference guide pasted into the session: `docs/AI Video and LLM Architecture.pdf` and `docs/AI Video Generation Engine & Social360 Model Research.pdf`. They were treated as input to check. Much of the first report's architecture stands, and its tenant design matches the one chosen here. Its numbers should not be reused.

Most pricing citations in the first report are blogs and aggregators. The second report's citations cannot be resolved.

### Economics

| Report claim | Finding |
|---|---|
| 5-minute video COGS $6.08, margin 74.1% | Hero shot uses $0.24, below every listed route at its own retry rate. Standard shot uses $0.085, but its own 70/30 blend gives $0.15. Corrected on its own prices: $9.85 to $21.55, margin 58% to 8%. Keyframes, voice, QC and upscaling are also omitted |
| Margins above 74% at every stage | Rests on the above, and on $0.02 per credit while its deepest plan earns $0.0138 |
| 4,000 hero seconds for 250 videos | Its own mix implies 16,250 |
| 250 A100 hours for 250 videos | Its own figures imply 437, before retakes |
| Per-minute retail column | Uses 10 clips per minute; 5 s clips make 12 |
| 25% keep rate as "industry-standard" and "production telemetry" | A marketing FAQ: 41 of 164 clips in one episode (V-042) |
| RunPod A100 $2.15, H200 $6.35 | $1.79 and $5.29 (V-009, R3-009) |
| Wan 14B about 180 to 300 s on A100 | Unverifiable. Vendor's Wan 2.2 A14B table shows 2,735.7 s on one A100 at 720p (V-902) |
| $500 to $1,000 per month per server (second report) | Fits RTX 4090 and L40S only (R3-001, R3-003, R3-005) |

### Fabricated-looking results

| Report claim | Finding |
|---|---|
| Table 7 benchmarks, such as 79.6% quartile accuracy | The model does not exist. No citation for any column, and only one is marked "Target" |
| Table 8 demo outputs, such as "41% to 79%", "DINO 0.94", "<350 ms" | Scripted, not observed |
| "2.5 million" training records | No provenance |
| MRR, 100+ workspaces, >75% verified margin in 16 weeks | No basis |
| SOC 2 Type II inside 16 weeks | About 6 to 15 months, vendor-sourced (V-532) |

None of these should reach a YC application or a diligence room.

### Licences

| Report claim | Finding |
|---|---|
| XTTS-v2 for production voice | Blocked: non-commercial (V-011) |
| InsightFace identity gate, IP-Adapter-FaceID | Blocked (V-015, V-016) |
| LivePortrait, Hallo2 as "MIT" | Blocked as shipped, through dependencies (V-018, V-020) |
| LTX 2.3 "Apache 2.0, unrestricted" | Not Apache; competition clause, USD 10M cap (V-025, R2-031) |
| CogVideoX "Apache 2.0" | CogVideoX License (V-030) |
| Hunyuan "restricted for competing SaaS" | No such clause. Territory limits apply (R2-059) |
| DeepSeek-V3 "MIT / Apache" | DeepSeek License with use restrictions (V-520) |
| Llama-2 "Apache 2.0" (second report) | Llama 2 Community License (V-516) |
| Claude as open-weight alternative (second report) | Hosted service |
| Wan 3.0 Apache | No open weights exist (V-046) |

### Technical

| Report claim | Finding |
|---|---|
| VBench-2.0 has 16 dimensions, with thresholds 0.92, 0.90, 0.95, 6.0 | 18 dimensions; thresholds not published in either (V-513, V-514, V-515) |
| FastLibra eliminates TTFT spikes, to be patched in | Baseline averages on NPUs, no official code (V-508, V-510) |
| vLLM default 0.2 LoRA ratio | Not what the paper says, and no such option in current docs (V-507, V-509). The reference guide repeated this |
| API gateway "mathematically preventing" KV cache leakage | An API key does not set the salt, and salting is optional (V-501, V-506) |
| Render crisp brand text in the model | Generated text remains poor (R4-047). Composite at assembly |
| Qwen2.5-14B and Wan 2.1 as the current stack | Superseded (R5, R2) |

### Data rights

| Report claim | Finding |
|---|---|
| Train adapters on telemetry from five platforms | X and LinkedIn No; Meta and YouTube Conditional; TikTok unread (R7-005, R7-008, R7-001, R7-016). `[COUNSEL]` |
| Competitor transcripts and trend data from platform APIs | Barred on X, LinkedIn, YouTube, Pinterest; Meta unclear (R7-006, R7-009, R7-014, R7-021). `[COUNSEL]` |
| "Learns from aggregate brand experience" (second report) | Contradicts tenant isolation |

### Repository catalog (third input)

A pasted catalog of repositories and methods, also AI-generated, claimed to be grounded in primary documentation. Key claims were checked at source.

| Claim | Finding |
|---|---|
| WanGP is Apache 2.0 | Wrong. WanGP Community License; paid SaaS needs an agreement (V-907) |
| WanGP VAE 28 s to 11 s | Confirmed as a vendor claim (V-908) |
| WanGP RIFLEx, 8 s on 12 GB | Not on its README |
| LatentSync, LivePortrait, Hallo2 as open-source options | Blocked as shipped through InsightFace (V-018, V-020, V-022) |
| XTTS-v2 reference stack | Blocked (V-011) |
| BluShooz combines MuseTalk, LivePortrait, LTX | README names CogVideoX, XTTS-v2, Wav2Lip, Real-ESRGAN (V-913) |
| AIBrix Apache 2.0, v0.8.0 | Confirmed (V-909) |
| AIBrix cuts latency 19.2% and 79% | Not on its README, so not used |
| LoRAX as an alternative | Archived (R6-046) |
| VBench evaluates 16 dimensions, including VBench-2.0 | 16 is VBench; VBench-2.0 has 18 (V-513, V-514) |
| VBench 4:1 weighting | Confirmed (V-912). Not added to `manifest.json`, because an unused score there would imply a check that does not run |
| Wan 4n+1 frames | Confirmed for Wan only (V-910). Placed in the local adapter, not the shared `Shot` schema |
| English default negative prompt | Upstream default is Chinese (V-911). The English text was not found at source, so it was not adopted. A `wan_local` dialect sends the style bible's exclusions as a negative prompt, and the upstream default is not embedded |
| `[REAL: test_video_qc]` label | That test does not exist |

### Reference guide

Most of the guide's Runway, Luma and Kling figures were confirmed. Its A100 and H200 rates, and the 0.2 ratio above, were wrong. L40S and H100 are not contact-sales for Pods (R3-003, R3-007). Hunyuan should be Blocked for a global SaaS, not Counsel. Its code patterns for Excel cleanup and the negative control were adopted. Its suggestion to redact canaries before dataset construction was not, because a redacted canary cannot leak, which would leave the leak tests vacuous.
