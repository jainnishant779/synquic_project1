# Red-team review of the Synquic data room

**As of 2026-11-01.** Written for a YC partner. The reviewer did not write any of this material.

**Method.** I read the README, docs 01 to 09, the workbook (values and formulas), all code in `poc/` and `tools/`, and `research/facts.csv`. All 343 cited fact ids were read against the sentences citing them. Findings marked "reproduced" were run, on temp directories and a scratch copy of `poc/`. Findings marked "by reading" were not run.

**Limits.** No network was used, so citations were checked doc against ledger, not ledger against source pages. The Excel half of `verify_workbook.py` was not run. `check_facts.py` was not run, because it rewrites `facts.csv`. Of the research briefs, only R5 was consulted, and only in part. Diagram sources 02, 03, 05 and 06 were read; the rendered images were not.

**Overall.** The data room is unusually candid about mock versus real, and its tables match its workbook. Its weak points are a flat isolation claim with reproduced counterexamples, a monthly cost table that embeds an unvalidated decision, cost totals that omit things the docs criticise others for omitting, and a brief-coverage gap around privacy and the data pipeline.

| Severity | Count |
|---|---|
| Blocker | 2 |
| Major | 18 |
| Minor | 19 |

---

## Blockers

### B1. "Tenant isolation holds at application level" has two reproduced cross-tenant paths

- **Where.** `docs/09-claims-register.md:38`, `docs/04-social360-architecture.md:85-93`, `docs/08-roadmap.md:97`. Code: `poc/social360/registry.py:14-17, 34-36, 38-45, 66-67`; `poc/social360/service.py:47-54`; `poc/social360/store.py:116-119`.
- **Claimed.** Isolation holds at application level, `[REAL: test_isolation.py]`. `test_04` is named "adapter versions resolve only for owner".
- **Actually true (reproduced).**
  - **Path 1: version traversal.** `Registry` checks the `tenant_id` argument but never validates `version`. With tenant A's context, `metadata(ctx_a, A, "../../fictional_bikes/registry/v0001")` returned B's insights (B's product and sentiment vocabulary). `promote` with the same string moved A's prod pointer onto B's adapter. `POST /v1/infer` with A's token then returned 200, served B's adapter, and put `../../fictional_bikes/registry/v0001` in `X-Model-Version`.
  - **Path 2: tenant-id reuse.** `offboard()` never clears `Platform._models`, which is keyed `(tenant_id, version)`. After offboarding B and provisioning a new customer under the same id, the new customer's `v0001` was served from the cached object holding the previous owner's weights. The weights did not match the new adapter file.
- **Reachability.** Neither path is open to a tenant holding only a token today. No HTTP route takes `version`, and path 2 needs id reuse. Path 1 becomes exposed the moment an operator promote or rollback endpoint exists. `test_04` passes only because it attacks the `tenant_id` argument.
- **Why it matters.** Isolation is what doc 04 calls defensible. A partner's engineer can find path 1 in minutes, and the sentence is flat. The honest wording is "no path found through the current HTTP routes".
- **Severity.** Blocker for the claim as worded.

### B2. Doc 06's monthly cost table silently embeds the self-host decision and the payroll it says it excludes

- **Where.** `docs/06-gpu-deployment-cost-assessment.md:120-129`. Workbook `Tiers!C6:D6`, `tools/build_workbook.py:426`, and `Breakeven!C10`, which is GPU plus engineer.
- **Claimed.** "Payroll, CDN overage and SOC 2 costs are excluded." The listed assumptions are 60-second videos, 50% attach and the GPU counts. Doc 06:86 says self-hosting is "a direction, not a decision".
- **Actually true.** When `Breakeven` row 13 says "Yes", `Tiers` replaces Gen-4.5 standard generation with the Breakeven self-host total. So Launch and Scale video COGS assume all standard footage is made on Wan 2.2 5B on rented RTX 4090s, and that figure includes one $12,000 engineer. Neither is disclosed beside the table. Credits still charge Gen-4.5's 124 per second, so a 5B output is sold at the premium model's price.

| USD per month | Doc 06 video COGS | All-API video COGS | Self-host, payroll removed as stated |
|---|---|---|---|
| Launch | 51,626 | 67,883 | 39,626 |
| Scale | 403,066 | 678,832 | 391,066 |

  Workbook gross margin is 83.5% at Launch and 87.4% at Scale. All-API it is 78.6% and 79.1%. Recomputed independently in Python; the doc 06 row matched exactly.
- **Why it matters.** The table reads as an estimate of the recommended API launch plan. It understates video COGS by 24% at Launch and 41% at Scale against that plan, it contradicts its own footnote, and it rests on the provisional equivalence doc 06 warns about. `verify_workbook.py` does not touch `Tiers` at all (see M12).
- **Severity.** Blocker.

---

## Major

### M1. The leakage gate cannot detect real leakage, and one detector has no negative control

- **Where.** `docs/07-demo-plan.md:20`, `docs/05-automated-learning-workflow.md:43`, `docs/04-social360-architecture.md:88, 93`. Code: `poc/social360/gates.py:60-64`, `poc/social360/trainers/tiny.py:111-123`, `poc/tests/test_isolation.py:97-100, 116-120, 131-153`.
- **Claimed.** "Canary leak detection `[REAL]`." "Detectors can actually detect." "A pass elsewhere means something" (doc 07:72).
- **Actually true (reproduced).**
  - G3 is a literal byte search. `LeakyTrainer` passes it only because it writes the canary as a raw `uint8` tensor, which no real trainer would do. I trained A's adapter on 20 copies of B's canary record. G3 returned `passed: True, hits: 0`.
  - `check_bytes` is blind to ciphertext. With B's canary in A's `records.enc`, and with B's canary in B's store before offboarding, it passes. So the scans in `test_05` and `test_10` cannot fire on `.enc` files. `test_05` line 100 partly compensates in one direction only.
  - `check_text` has no negative control. With it disabled, `test_07` and `test_08` all passed.
  - The retrieval and bytes controls are genuine. Disabling those detectors fails `test_08`, and they are the same functions used by `test_02` and `test_05`. `gate_leakage` also has a working control in `test_08b`.
- **Why it matters.** The negative control proves the detector finds what the fixture was built to plant. Doc 04:93 does mark the LLM probe `[DESIGN]`, but doc 07 tells the presenter to say a pass "means something".
- **Severity.** Major.

### M2. The 5-minute headline assumes retries the pipeline does not perform

- **Where.** `README.md:32`, `docs/06-gpu-deployment-cost-assessment.md:9`. `poc/video/pipeline.py:16, 115-118`, `docs/03-video-production-architecture.md:68-69`.
- **Claimed.** A 5-minute video costs $147 at a 25% accept rate.
- **Actually true.** That figure needs an average of four attempts per kept shot. `MAX_ATTEMPTS` is 3. At 25%, each shot fails all three with probability 0.42, so about 25 of 60 shots go to reroute or a human, and the chance a 60-shot run completes unaided is about 5e-15. At 61% it is 2.6%. At 85% it is 82%. Reroute is not built, and the workbook has no line for reroute, human handling or the vendor spend on abandoned runs. `run()` charges no credits on `failed_qc`, so that spend is unrecovered.
- **Why it matters.** Cost per kept second is arithmetically right, but the product described cannot finish the job at the default rate. Accept rate also decides feasibility and labour, not only price, and the docs do not say so.
- **Severity.** Major.

### M3. "All-in" omits what doc 06 faults the earlier report for omitting

- **Where.** `docs/06-gpu-deployment-cost-assessment.md:13, 54`, `tools/build_workbook.py:284-292, 435-437`.
- **Claimed.** The earlier $6.08 "leaves out keyframes, voice, QC and upscaling". Doc 06's all-in "adds generation, QC and a supporting stack".
- **Actually true.**
  - There is no upscaling line, though the baseline route is modelled at 720p.
  - There is no cost for the human steps doc 03 requires: asset approval, keyframe approval, sampled review and failed-shot handling.
  - There is no cost for repair edits, OCR, identity embedding, CDN, or the orchestration in diagram 02.
  - QC is priced at `gpt-5-nano` input tokens (R3-100) with no output tokens, about $0.02 per 5-minute video. The evidence in doc 03:57 is for GPT-4o and Gemini 2.5, and no fact shows `gpt-5-nano` can judge video.
  - Social 360 COGS is GPU hours only. RAG is called "the core of the product" and has no cost: no embeddings, index, ingestion compute or storage.
- **Why it matters.** Applying the same test to doc 06 that it applied to the earlier report produces the same criticism, in kind. Labour is likely the largest omission.
- **Severity.** Major.

### M4. The baseline route's "clear commercial terms" rest on a learning page, and its limits are unsourced

- **Where.** `docs/01-video-models-and-pricing.md:8, 22, 27`, `docs/06-gpu-deployment-cost-assessment.md:59, 63`, `docs/09-claims-register.md:53-61`, `tools/build_workbook.py:74-75`.
- **Claimed.** Runway has "clear published prices and commercial terms (R1-051)". The route is "Allowed". Max clip is "see below".
- **Actually true.** R1-051's own note says "Learning page, not the contract. Terms of Use not read. Enterprise agreement ... not read." Doc 09's known gaps list Kling, MiniMax, xAI and Seedance terms, but not Runway. R1-038 says Gen-4.5 max clip, resolution and audio were "not stated on pages read", yet the workbook hard-codes 10 s and 1280x720. Nothing below the table in doc 01 gives a max clip, so "see below" dangles. The Luma "Allowed" has the same weakness: R1-112's note leaves it to counsel whether pay-as-you-go counts as a qualifying subscription.
- **Why it matters.** Recommendation 2 and the headline figure sit on the one vendor whose contract is unread and undisclosed as unread.
- **Severity.** Major.

### M5. The router does not implement the recommendation, and the demo never exercises it

- **Where.** `docs/03-video-production-architecture.md:81, 92`, `docs/07-demo-plan.md:50`, `poc/video/router.py:28, 50`, `poc/video/cli.py:43`, `poc/provider_catalog.json`.
- **Claimed.** The router filters "by capability, licence verdict and cost". Wan 2.2 is the clean default. Doc 07 tells the presenter to point this out on the route line.
- **Actually true (reproduced).** With all catalog routes available, the router chose `magihuman_h100` (Counsel) for 720p and 1080p at 5 s, `ltx25_4090` (Counsel) at the POC spec, and `h3_lite` (Counsel, terms unread) at 6 s and 8 s. In none of these cases did it choose Runway or Wan 2.2. Only `Blocked` is excluded, and the shipped catalog contains no Blocked entry, so the licence filter has nothing to reject. In the demo, every route but mock is rejected as "not available in this run", the first check, so no capability or licence logic runs. `rejected` shows this on screen.
- **Why it matters.** In production form it would route to the routes the docs say need a lawyer first. The presenter's line is not what the screen shows.
- **Severity.** Major.

### M6. Privacy design contradicts the API-first plan, and residency, retention and sub-processors are absent

- **Where.** `docs/03-video-production-architecture.md:90`, `docs/01-video-models-and-pricing.md:7`, `docs/04-social360-architecture.md:81-106`, `research/facts.csv` R3-001 to R3-009 conditions.
- **Claimed.** "Tenant assets and customer footage stay on RunPod Secure Cloud or equivalent."
- **Actually true.** The launch plan sends character references, product images and prompts to Runway, the image API, ElevenLabs and a hosted LLM. No doc analyses vendor retention, training on inputs, or DPAs for those vendors. A text search of docs 01 to 09 finds no mention of data residency, cross-border transfer, sub-processors or a retention period. Every RunPod price is "region not stated", and R3-027 says SOC 2 coverage "varies by workload, region and provider", which doc 06:42 drops. The video pipeline has no tenant concept: `Brief` and the cache key carry no tenant.
- **Why it matters.** The brief asked for privacy with tenant isolation. Isolation here is a Social 360 story, and the first question from an enterprise or EU buyer has no answer.
- **Severity.** Major.

### M7. The "automated daily brand data pipeline" has no connector, retention or eligibility enforcement

- **Where.** `docs/04-social360-architecture.md:66, 79`, `poc/social360/ingest.py:43`, `poc/social360/pipeline.py:24-25`, `poc/social360/run_daily.py`.
- **Claimed.** "Records are tagged with source and training eligibility at ingestion, so the training job can only see eligible data. This is the mechanism that enforces the table." Storage is "within each platform's storage limits".
- **Actually true.** Ingest stores `text`, `label` and `day` only. A search of `poc/` finds no source or eligibility tag, and `build_dataset` trains on every record. There are no connectors, no scheduler, no OAuth or consent design, and no deletion or TTL, despite the 30-day YouTube and ten-day LinkedIn duties in R7-016 and R7-008. "Daily" is a Python loop with a `day` argument. The only `approved` control is a boolean in the input record.
- **Why it matters.** Doc 04's central finding is that platform terms limit training. The one mechanism named to enforce that does not exist, and the POC would train on anything it ingests. It falls under the "`[DESIGN]` unless a test is named" header, but the design is two sentences.
- **Severity.** Major.

### M8. The base model table misattributes figures and treats GPT-OSS on a different basis

- **Where.** `docs/04-social360-architecture.md:26-29, 31, 33, 114`.
- **Claimed.** "QLoRA training" of 22 GB (R5-036), 24 GB (R5-053), 24 GB (R5-072), and "BF16 LoRA about 44 GB" for gpt-oss-20b. "Dense models train on a single GPU and vLLM lists LoRA for their architectures (R5-102)."
- **Actually true.**
  - The three cited facts are 4-bit inference memory (17-20, 16-19 and 17 GB). R5-053's verifier note says "No fine-tuning figures on this page". The real sources are R5-041, R5-058 and R5-076.
  - The GPT-OSS row switches metric. R5-023 gives Unsloth QLoRA for gpt-oss-20b at **14 GB**, below Gemma's 22 GB, in the same column where the doc shows 44 GB for a different method. The MoE objection may still hold (R5-041, R5-105), but the table flatters the winner, on the model the brief named.
  - R5-102 lists `GptOssForCausalLM` as LoRA-ticked too, so it does not separate dense from MoE. Its note says a tick does not cover a quantised checkpoint or these exact models.
  - R5-105 is a TensorRT-LLM limit, not vLLM.
  - Nothing explains Gemma over Qwen. Both are Apache, dense and similar in memory. Gemma's price advantage is an FP4 route that R5-042 says adapters cannot use, and R5-065 shows no independent score for Gemma at all. Doc 04:33 words this as Qwen having "the stronger independent record" while making Gemma primary.
  - Doc 04:114 says an L40S holds "the 22 to 24 GB QLoRA footprint", but R5-058 records about 47 GiB for the closest Qwen 27B config on Axolotl, a named tool, against a 48 GB card.
- **Why it matters.** Base model selection was an explicit brief item, and this table is the first thing a technical reader will check.
- **Severity.** Major.

### M9. Doc 07 says "end to end", and the script does not survive a rehearsal

- **Where.** `docs/07-demo-plan.md:7, 13-26, 36, 51, 71`, `poc/video/assemble.py:34-35`, `poc/social360/run_daily.py:67-70`.
- **Claimed.** "It proves the architecture runs end to end." The status table lists what is mock. Step 4 shows `total_attempts: 8`.
- **Actually true (reproduced).**
  - Stages with no POC presence and no line in that table: asset approval, keyframes, repair, reroute, voice, music, lip-sync, colour match, normalisation and loudness. Audio is a 220 Hz sine tone, and narration and captions are template strings. `has_audio_stream` and `silent_audio` pass on the tone.
  - "Production API" is an in-process `TestClient`. `/v1/infer` returns a classifier label plus BM25 matches. There is no generated answer.
  - Provider dialects are shown as `[REAL]`, but `pipeline.run` always compiles `generic` (`pipeline.py:86`). `Shot.mode` is never used.
  - `total_attempts` was 8 only on an empty run directory. A second run gave 0, so faults never fire and QC does not run. The shipped `poc/runs/video` gave 5, and its manifest is a 12-second, 3-attempt run. `poc/runs/` is gitignored.
  - Doc 07 step 6 says to show the version header, but the demo prints only the JSON body.
- **Why it matters.** Disclosure is otherwise good, which makes these gaps conspicuous. A rehearsed demo will show 0 attempts in front of the audience.
- **Severity.** Major.

### M10. The resume cache claim is false as written

- **Where.** `docs/03-video-production-architecture.md:25`, `poc/video/pipeline.py:42-44`, `poc/tests/test_video.py:161-164`.
- **Claimed.** Shots are "cached by a hash of its prompt, references and spec, and a failed job resumes without repeating them".
- **Actually true (reproduced).** The key excludes reference images. I replaced every reference image and the run reused the cache with 0 attempts. The test has no failed job in it: two clean runs, the second all cached. A mutation making the key the shot id alone survived every test. If `cache_dir` is shared, a tenant with the same prompt and different brand assets receives another's clip.
- **Why it matters.** It is a wrong-output bug on a `[REAL]` line, and a cross-tenant asset path if the cache is ever shared.
- **Severity.** Major.

### M11. Several tests prove less than their names and the docs say

- **Where.** `poc/tests/`, with claims in docs 03, 04, 05, 09.

| Test | Claim | What it does | Evidence |
|---|---|---|---|
| `test_10_offboarding_removes_everything` | Doc 04:91: delete "data, index, adapters and key" | Creates no adapter and no registry entry. Its scan cannot read ciphertext. There is no index in the code | Mutation leaving the registry survived |
| `test_06_adapter_changes_only_its_own_tenant` | Name | No training happens between `before` and `after`, so reloading one file twice must match | By reading |
| `test_versions_are_immutable_and_record_lineage` | Doc 05:62 "never overwritten" | Never tries to overwrite | Mutation overwriting older adapters survived |
| `test_five_minute_mock_run` | Doc 09:35 "assembles in order, watermarked throughout" | Order is checked on `storyboard.json`, not the video. Watermark at 3 timestamps | Reversing clips in `assemble` survived |
| Same test | Doc 03:55 final QC is `[REAL]` | `all(...)` over `checks` is vacuous if empty | `check_final` stubbed to empty survived |
| `test_qc_catches_each_injected_fault` | Doc 03:53, six checks | Four faults. No missing-stream or silence case. Silence is not checked per clip | Mutation on the stream check survived |
| `test_clean_clip_passes_and_semantic_checks_are_not_passes` | `qc.py:4` "never counted as a pass" | `QCResult.passed` is true with all four not evaluated, and the shot is accepted | By reading |
| `test_resume_reuses_passed_shots` | Doc 03:25 | See M10 | Mutation survived |
| `test_01b_bad_or_missing_token_is_refused` | Auth | Expiry untested | Mutation disabling expiry survived |
| G4 latency | Doc 05:44 `[REAL]` | No test can fail it | Always-pass mutation survived all 44 tests |
| `test_02` API assertion | Retrieval | No status-code assertion, so a 4xx passes | By reading |
| `test_tenant_training_never_changes_the_shared_base` | Doc 04:92 "hash checked" | Test only. No runtime hash check | By reading |
| `test_router_picks_cheapest_eligible_and_skips_blocked` | Doc 03:81 | True on a synthetic catalog. See M5 | Reproduced |

- **Why it matters.** The suite is real and useful, but "44 passed" overstates what is proven. A reader who runs mutations will find this quickly.
- **Severity.** Major.

### M12. "Independent", "verified" and "workbook arithmetic is correct" are all stronger than the evidence

- **Where.** `docs/01-video-models-and-pricing.md:3`, `docs/09-claims-register.md:7-15, 42`, `tools/verify_workbook.py:56-77`, `tools/build_workbook.py:479`.
- **Actually true.**
  - The "independent verifier" is another agent in the same AI process. Doc 09 says "AI-assisted", but a reader will take "independent" to mean a third party.
  - 89 of the 412 "verified" facts (22%) are `V-` facts created by the verifiers and marked verified by their finders. They include most supporting-model Blocked verdicts and two render times.
  - 168 of 343 cited facts (49%) are not verified: 131 single_source, 19 conflict, 17 unverifiable, 1 failed. Doc 09:12 calls unchecked facts "mostly descriptive", but 6 of the 8 rows of doc 02's design rationale rest only on single_source facts, and so does the membership-inference position.
  - The workbook's unverifiable-fact check passes while `verdict_source` values for 7 routes are R1-055 and R1-087 (unverifiable: H3 API, H3 Lite, both Kling routes) or single_source (R1-096, R1-069, R1-116: Wan 3.0, Seedance, Veo via fal). The check covers formula facts only. R1-055 is about direct Kling, while the route is via Replicate.
  - The "21 checks" do not touch `Tiers` or `Sensitivity`, which include the sheet with the B2 logic. They import inputs from the build script, and the mix is hard-coded at 0.6.
  - `build_workbook.py:74-88` hard-codes clip, resolution and `refs=True` for every route. The header says green cells come from the ledger, but these inputs do not.
- **Severity.** Major.

### M13. Demand is untested, and the volumes imply an ARPU nobody states

- **Where.** `docs/06-gpu-deployment-cost-assessment.md:88-116, 129`, workbook `Tiers`, `tools/build_workbook.py:433`.
- **Claimed.** Margin "says nothing about demand", which is a fair disclaimer in doc 06:129. The sheet and the credit table still present 74% per operation, and 75% to 87% gross margin.
- **Actually true.**
  - The tier volumes imply about **$3,053 per brand per month** in video credits, at all three tiers. That is about 6 times Social 360's $499, and 2.4 times Emplifi's $1,249 floor. This is not stated anywhere.
  - A pack buys little: Starter ($39) is 16 s of standard video, and Scale ($299) is 145 s. A 30-second ad is 3,848 credits, about $64 at the cheapest rate, so it does not fit a Starter pack. A 5-minute video needs more than two of the largest packs. Doc 06:116 calls 30 seconds "far easier to price" without saying so.
  - Retail is $2.06 per second against Runway's public $0.12.
  - There is no competitor video pricing anywhere, though credit pricing was a brief item and doc 06:116 argues from competitors.
  - Revenue assumes 100% credit redemption, no refunds, and the unweighted mean of pack prices, which is not the cheapest-pack basis doc 06 sets margin on.
- **Why it matters.** The disclaimer is honest, but the reader gets no way to see that the model needs enterprise-level spend per brand.
- **Severity.** Major.

### M14. $46 to $147 is not a range

- **Where.** `README.md:32`, `docs/06-gpu-deployment-cost-assessment.md:9-11, 26`, `docs/08-roadmap.md:13`.
- **Claimed.** Cost is "about $46 to $147 depending on it".
- **Actually true.** Neither end is a first-pass accept rate. V-042's note says it "measures selection for a final cut, not first-pass acceptance". R4-060's note says it estimates "share of a video, not first-pass rate per shot". R4-061 records hard shots at 8 or more generations, and its 3-per-shot figure conflicts with its own 25%. Doc 06:26 is candid about provenance, but the README still gives two endpoints with nothing beyond them. At 10% the same model gives about $360. Doc 09 criticises the earlier report's use of this source while the default here is the same figure, with disclosure.
- **Severity.** Major.

### M15. Character consistency has no working identity check, and its best evidence is a technique outside the plan

- **Where.** `docs/02-master-prompt.md:19`, `docs/03-video-production-architecture.md:40, 45, 54, 59`.
- **Claimed.** Keyframe-first is the "best supported" identity method. Identity QC is "designed around a licensed embedding model". The pilot "must measure" identity.
- **Actually true.** R4-036 and R4-037 describe **face swap on keyframes** (KeyID) plus interpolation, in the author's own method. The 0.260 to 0.643 gain is that swap, not image-to-video from an approved keyframe. No doc includes a face-swap step. Doc 03:40's "fails on blur and extreme poses" is a face-swap failure mode. No licensed embedding model is named. InsightFace is Blocked (V-015), the alternatives are unnamed, and ArcFace is the metric behind much of the evidence. So the pilot has no named tool for its main long-form risk. Product consistency has "little direct evidence" (doc 03:45), which is honest.
- **Why it matters.** Character consistency was a named brief item. The answer is a method whose evidence does not apply, and a gate with no component.
- **Severity.** Major.

### M16. Licence positions are inconsistent, and no cleared default stack exists

- **Where.** `docs/01-video-models-and-pricing.md:73-76, 84-87`, `docs/03-video-production-architecture.md:59, 85`, `docs/06-gpu-deployment-cost-assessment.md:54-65`, `tools/build_workbook.py:69`.
- **Actually true.**
  - **LatentSync** is Counsel in doc 01:76, while LivePortrait and Hallo2 are Blocked as shipped for the same InsightFace dependency. V-022 itself says "Blocked as shipped" for the detector.
  - **Doc 06's Licence column** covers the video route only. Every all-in figure includes FLUX keyframes (terms unread, doc 01:85), sync.so lip-sync (terms unread, R3-128, undisclosed in doc 01) and ElevenLabs music (Counsel, doc 01:87 says "a legal decision first"). R3-121 notes employee caps and a resale bar that could bind Synquic.
  - **Premium tier** is Kling via Replicate, Counsel, in every COGS figure and in the rate card.
  - **"At least two live routes per tier"** (doc 03:85) cannot be met on Allowed routes. Premium has none. Standard's only other Allowed API vendor is Luma, limited to 5 s with keyframes (V-036) in a keyframe-first design that uses 4 to 8 s shots. Doc 01:8 says "add a second vendor" and names none.
  - **Doc 01:86** cites R3-126 (sync.so) and R3-129 (fal LatentSync) as if one vendor. "The vendor" is undefined.
- **Severity.** Major.

### M17. The learning gates do not do what the prose implies

- **Where.** `docs/05-automated-learning-workflow.md:7, 16, 42`, `poc/social360/gates.py:44, 53`, `poc/social360/pipeline.py:41`.
- **Claimed.** G2 passes when the lower bound "is above the margin". Doc 05:16: an adapter goes live "only if it beats" a baseline. Doc 05:7: training starts "when enough new data has built up".
- **Actually true.** G2 is non-inferiority: `lower > -0.02`. The test asserts an identical candidate passes. In the shipped run, both day-4 promotions have **negative** lower bounds (-0.015, -0.01). Repeated promotion can ratchet quality down by up to the margin each time. The few-shot comparison is `[DESIGN]`. The trigger counts today's batch only (`report.accepted`), so a brand ingesting 19 records a day never trains. G1 then checks the cumulative count. Training runs before G1, so data rejected for PII has already been trained on, though that artefact is not promoted.
- **Severity.** Major.

### M18. Thin answers to brief items: local production, commercial integration and benchmarking

- **Where.** `docs/03-video-production-architecture.md:90`, `docs/04-social360-architecture.md:155-162`, `docs/05-automated-learning-workflow.md:68, 82`, `docs/08-roadmap.md`, `poc/video/adapters/local_http.py`.
- **Actually true.**
  - **Local production.** One paragraph plus a diagram box. No worker design, model serving stack, queue, GPU failure handling or capacity plan. `LocalAdapter` speaks to an invented API. One engineer runs 222 GPUs at Scale in doc 06:80. That is about $197 per hour, above the default, raisable $80 per hour account limit noted in R3-021, and availability of 222 Secure Cloud 4090s is unverified.
  - **Commercial integration.** A four-row table on `[ASSUMPTION]`, because platform details "were not supplied". No API, data flow or packaging.
  - **Benchmarking.** Doc 05:68 says "pre-registered protocol", but no sample size, primary metric or margin is set; line 83 says they will be. It is a plan, not a pre-registration.
  - **Production operations.** A search finds no SLO, failover or disaster recovery. Seed and Launch rest on 1 and 2 GPUs.
  - **Roadmap.** No budget, and no effort figures despite doc 08:3 labelling effort estimates.
- **Severity.** Major.

---

## Minor

| # | Where | Claimed | Actually true | Why it matters |
|---|---|---|---|---|
| 1 | `poc/social360/store.py:116-119`, `service.py:73-79` | Offboarding removes everything | A token stays valid after offboarding. `GET versions` returned 200, `POST infer` returned 500, and the next call recreated the tenant directory (reproduced). `rmtree(ignore_errors=True)` hides partial failure, then the key is destroyed | Deletion is not durable or verifiable |
| 2 | `registry.py:30-31`, docs 04:86, 04:99 | Per-tenant encrypted storage; weights presumed personal data | `adapter.pt` and `metadata.json` are plaintext. Insights hold tenant vocabulary (seen in shipped runs). Key destruction does not protect them | Crypto-shredding does not cover the riskiest artefact |
| 3 | `service.py:113-121`, `store.py:52-55` | Break-glass is controlled | `tenant_id` is unvalidated. `../../x` created a directory outside the root (reproduced, then removed). Unknown tenant gave a 500 after logging "break_glass". No approval, expiry or second person. It returns only a count, so the support route it stands for is unproven | Admin-only, but contradicts the care claimed |
| 4 | `service.py:99-105`, `tenancy.py:18-21` | Roles are separated | `versions` has no role check: an admin token for tenant A got 200. `TenantContext` is a plain dataclass that break-glass itself constructs, so it is a convention, not a capability | Design note |
| 5 | Doc 04:89, `service.py:119` | Logs hold hashes and counts only | Break-glass `reason` is stored verbatim, including an email I supplied. `test_07` runs before it. `tenant_hash` is unsalted and truncated, so dictionary-reversible | Log claim has a hole |
| 6 | `tenancy.py:44` | Bad tokens get 401 | Non-ASCII signature gave 500 via `compare_digest` (reproduced). Fails closed | Robustness |
| 7 | `store.py` , docs 04:87, 05:28, 04:86 | "Separate index per tenant", "Tenant index rebuilt", "Envelope encryption" | No index exists: BM25 runs per query over decrypted records. There is no KEK or DEK | Wording is stronger than code |
| 8 | `store.py:98-113`, `poc/runs/social360` | Shipped run is evidence | Keys are in memory only and the secret is random, so shipped `records.enc` cannot be decrypted or audited | Evidence is not inspectable |
| 9 | Doc 05:43, `pipeline.py:61-69` | G3 failure raises an incident | Only a `cycle` log line is written; nothing raises an incident | Unbuilt step in a `[REAL]` row |
| 10 | Doc 05:62, `pipeline.py:63` | Version records base model revision | Records the filename `base.pt` | Lineage is weaker than claimed |
| 11 | `api_http.py:77-82`, docs 07:87-92, 03:86 | API path "built"; set a key to go live | Unknown status becomes FAILED, so a real `pending` would abandon a billed job. The CLI hard-codes `MockAdapter`. `VIDEO_API_KEY` is read nowhere, and `--max-spend` is not a CLI flag, only words in an error string. `LocalAdapter` has no spend cap. `SpendCapExceeded` and HTTP errors escape with no manifest | "Next demo" understates the work |
| 12 | `qc.py:72`, `gates.py:74` | Black QC; p95 | `pic_th=0.90` is tuned to the mock band: at 180p a black clip was not flagged black (frozen caught it). `p95` is the 47th of 50 samples | Thresholds fit the mock |
| 13 | Doc 03:57 | "Technical QC is solved" | R4-049 says confirm thresholds and shorten defaults. Doc 03 itself says they must be tightened | Overstatement |
| 14 | `tools/check_claims.py:38, 43-45` | "Honesty rules" | Any line containing "report" is exempt. Any fact id on a line clears it. It never checks the id exists, or that a `[REAL: x]` test exists | Green result means little |
| 15 | Eight lines in docs 05 and 07 | README: `[REAL: test]` | Bare `[REAL]` on 05:29, 32, 44 and 07:15-17, 19, 20, despite the stated rule | Unlabelled evidence, G4 included |
| 16 | `docs/07-demo-plan.md:36` | 5-minute test "takes several minutes" | It ran in 29 s here, on a different machine from the reference laptop | Reason for excluding it from `run_demo.ps1` looks weak |
| 17 | `poc/requirements.txt`, `trainers/base.py:17` | Reproducible; values "finalised in docs/04" | Requirements are unpinned. Doc 04 has no rank, alpha or target modules. The spec's rank 16 sits oddly with "start low" | Reproducibility |
| 18 | Doc 06:56-65 | Route table | Shows 8 of 15 routes. The two cheapest, LTX ($7) and MagiHuman ($19), and H3 Lite ($51) are omitted, without saying so | Selective, though all three are Counsel |
| 19 | Doc 09:65, 129-131 | Audits "a reference guide" | The guide is not in `docs/`, so that section cannot be checked | Unverifiable audit |

---

## Citation sample

All 343 cited ids resolve to a ledger row. This table lists 56 headline checks, covering 78 fact ids. "OK" means the fact says what the sentence says.

| Fact | Status | Doc:line | Verdict |
|---|---|---|---|
| R5-036 | single_source | 04:26 | **Misattributed.** 4-bit inference memory, not QLoRA |
| R5-053 | verified | 04:27 | **Misattributed.** Note says no fine-tuning figures on this page |
| R5-072 | single_source | 04:28 | **Misattributed.** 17 GB inference |
| R5-023 | verified | 04:29 | **Selective.** Omits 14 GB QLoRA from the same fact |
| R5-102 | verified | 04:33 | **Does not discriminate.** Lists GPT-OSS as well |
| R1-051 | verified | 01:8 | **Stronger than fact.** Learning page; contract unread |
| R1-112 | verified | 06:60 | **Stronger than fact.** "Allowed" with an open counsel question |
| R4-036 | single_source | 02:19 | **Stronger than fact.** Face swap, author-run |
| R4-037 | single_source | 03:40 | **Misapplied.** Face-swap failure, stated of keyframe-first |
| R4-044 | single_source | 02:21 | **Partly opposite.** Vendor recommends reusing outputs; unmeasured |
| R4-045 | single_source | 03:42 | **Misapplied.** Model rollout, not user last-frame chaining |
| R4-034 | single_source | 02:22 | Selective. Quotes the worst method; EntityMem fell only to 0.669 |
| R4-054 | single_source | 03:57 | **Wrong unit.** "Agreement about 60%" is a Spearman rho |
| R7-027, V-529 | conflict, verified | 04:75 | **Contradicted.** "Competing models only" drops the Grounded Results and Maps training bars |
| R7-089 | conflict | 04:99 | **Stronger than fact.** V2: "unenforceable on its face", one attorney's view, secondary |
| R6-054, R6-055 | single_source | 04:99 | **Selective.** R6-055 also has AG News, AUC 0.961, 46.7% TPR; omitted, and its note warns short social posts may sit at that end |
| R6-022 | single_source | 04:47, 05:16 | **Misattributed.** Tests prompting only; does not show fine-tuning wins |
| R6-021 | single_source | 05:16 | Stronger than fact. Sentiment and detox, stated flatly as "style transfer" |
| R6-025 | single_source | 05:16 | Weak. Fine-tuned classifiers, not QLoRA on an LLM |
| R6-060 | verified | 05:68 | **Wrong citation.** A protection method, not benchmark absence |
| R3-129 | verified | 01:86 | **Does not support.** A fal price; says nothing of InsightFace |
| V-022 | verified | 01:76 | **Softened.** "Blocked as shipped" for the detector, shown as Counsel |
| V-042 | verified | 06:26 | OK on provenance; used as an accept rate it does not measure |
| R4-060 | conflict | 06:26 | Disclosed, but used as a first-pass rate; note says it is not one |
| R1-001 | verified | 01:7 | Slightly strong. Live shutdown inferred from a notice |
| R3-089 | verified | 06:47 | Selective. us-east-1 only; other regions are far below on-demand |
| R3-027 | single_source | 06:42 | Omits "coverage varies by workload, region and provider" |
| R1-111 | single_source | 01:37 | Slightly strong. `budget_exhausted` may be charged |
| R5-050 | conflict | 04:27 | Stated as 27B; 27B vs 28B unflagged. Harmless |
| R2-084 | failed | 01:55 | OK. Doc uses the verifier's corrected value |
| R1-037, R1-038 | verified | 01:27 | OK. $0.01 times 12 credits |
| R1-040 | verified | 01:22 | OK on price. "Image-to-video" is not in the fact |
| R1-048, R1-049 | single_source | 03:87 | OK, as far as the unlabelled page allows |
| R1-050 | single_source | 01:37 | OK |
| R1-096 | single_source | 01:91 | OK, unverified clause |
| R2-002, R2-003 | verified | 01:58 | OK |
| R2-025, R2-026 | verified | 01:10 | OK |
| R2-045 | verified | 01:9 | OK; R2-047 supports "components clean" |
| R2-059 | verified | 01:59 | OK |
| V-015, V-016, V-018 | verified | 03:59 | OK |
| V-901, R2-049 | verified | 06:67 | OK as vendor claims; frames are repo defaults |
| R3-001, R3-003, R3-005 | verified | 06:34-36 | OK |
| R4-047 | single_source | 02:24 | OK; Veo, Kling and Seedance untested |
| R4-052, R4-053 | single_source | 03:57 | OK |
| R4-059 | conflict | 06:26 | OK, flagged |
| R5-104 | unverifiable | 04:37 | OK, flagged as open |
| R6-017, R6-018 | single_source | 05:15 | OK, "one study" |
| R6-031, V-504 | single_source, verified | 04:133 | OK |
| R6-038, R6-039 | single_source | 04:137 | OK, caveated |
| R6-049, V-501, V-503 | verified | 04:130-132 | OK |
| R7-005, R7-008 | verified | 04:66 | OK; doc 04:73 notes the inference |
| R7-012, R7-019 | unverifiable | 04:76 | OK, flagged |
| R7-051 | conflict | 04:105 | OK, flagged |
| R7-054, R7-055 | single_source, verified | 03:94 | OK; re-verified by V-525 |
| R7-065, R7-067 | single_source | 04:39 | OK; re-verified by V-527 |
| R3-013, R3-014 | conflict | 06:49 | OK, flagged |

---

## Numbers recomputed

| Doc table | Result |
|---|---|
| Doc 06 accept rate (lines 19-22) | All cells match `Sensitivity` |
| GPU rental (34-40) | Match |
| Cost per usable video (58-65) | Match `Unit_Costs` |
| Breakeven (77-82) | Match; 22% utilisation correct |
| Credits (100-104) | Match, including 74% and 84% margins |
| Monthly cost (124-127) | Arithmetic matches, logic does not: see B2 |
| README, $46 to $147 | Match $45.51 and $147.17 |
| Doc 01 prices | Match `Video_Models` and the ledger |
| `rate_card.json`, `provider_catalog.json` | Match cached values |
| Facts sheet vs `facts.csv` | Match; 2 of 800 rows differ only in float repr |

**Formula logic checked, no error found:** row references in `Tiers` and `Breakeven`; seconds and minutes in assembly, keyframes and planning; `stack_per_min` excluding the per-second QC term; keyframes not double counted between `Credits` and `Tiers`; `overshoot_ratio` at 1.0 not stacking on accept rate; credit rounding; breakeven utilisation.

**Logic problems:** B2, M2, M3, M13. Also planning COGS is costed for a 60-second video but charged flat for any length, which is immaterial in dollars.

---

## Tests run

- `python -m pytest poc/tests -q -p no:cacheprovider -k "not five_minute"`: **44 passed, 1 deselected.**
- `five_minute` run separately: **1 passed in 29 s.**
- No `[REAL: test_name]` label cites a test that does not exist. Two cite a file or tool: `test_isolation.py`, and `tools/verify_workbook.py`, which is not a test.

**Mutation results on a scratch copy**

| Mutation | Result |
|---|---|
| `check_bytes` disabled | Killed |
| `check_retrieval` disabled | Killed |
| `gate_leakage` always passes | Killed |
| Router lets Blocked through | Killed |
| Offboard leaves registry and adapters | **Survived** |
| `check_text` disabled | **Survived** |
| G4 always passes | **Survived** |
| Register overwrites older adapters | **Survived** |
| Token expiry disabled | **Survived** |
| `check_final` returns nothing | **Survived** |
| Cache key is shot id only | **Survived** |
| Missing-stream check made to pass | **Survived** |
| Clips reversed in assembly | **Survived** |

---

## Checked and found sound

**Honesty**
- README opens with the right warning: no AI video, no LLM trained, costs estimated, legal verdicts need a lawyer.
- Doc 07's spoken script and Q&A are accurate on the main points. Tier volumes are labelled as not traction. Doc 08's say and do-not-say table is good.
- No SOC 2, GDPR or similar certification is implied. RunPod's SOC 2 is labelled vendor-stated. Doc 04:106 says "designed to support" until a report exists.
- Mock clips are watermarked, the manifest carries `real_generation: false`, and `semantic_qc: not_evaluated` is recorded.
- "No routine human access" is correctly limited in doc 04:97.
- Hosted comparison claims are withheld: no superiority over GPT or Claude is made.

**Research**
- Ledger counts reconcile: 711 + 87 + 2 = 800, status totals sum to 800, and 362 re-fetched.
- None of the 307 price and licence attributes I could match by name is left as single_source.
- Conflicts are mostly recorded and flagged, not averaged: R3 serverless, DPDP dates, SOC 2 timing.
- Licence reasoning for H3, Hunyuan, LTX, XTTS, InsightFace and FLUX.1 dev matches the facts.
- The Unverified lines in doc 01 and known gaps in doc 09 are real gaps, apart from M4.
- Doc 09's audit samples check out against the PDFs: $6.08, 74.1%, $0.085 blend, 4,000 hero seconds, "industry-standard" 25%, 79.6%, 2.5 million, "mathematically preventing", 16-dimension VBench-2.0, $500 to $1,000, Llama-2 Apache. The other doc 09 re-derivations were not recomputed.

**Code**
- Tenant comes from the signed token, and a forged or wrong-tenant token is refused.
- Wrong-key decryption is refused. Retrieval stays per tenant through the API, and the HTTP routes I attacked did not cross tenants.
- Admin and tenant routes are separated for metrics and inference.
- A leaking artefact is discarded and its metadata kept. Rollback and the atomic pointer work.
- Bounded retries work. Blocked routes are excluded when present. The API spend cap holds.
- The base model file is unchanged by adapter training. The rate card drives credits.

**Coverage with a real answer:** video research and pricing, master prompt, 5-minute workflow, QC design, credit formula, platform data rights, tenant-isolation design, vLLM security floor, automated learning shape, diagrams, costs, and roadmap structure.

---

## Reviewer note on side effects

No data room file was edited other than this report. The first pytest run may have created gitignored `__pycache__` folders under `poc/`. One probe created an empty folder at `%LOCALAPPDATA%\rt_escape_probe` to prove the traversal, and removed it. All other probes wrote to temp or scratch directories.
