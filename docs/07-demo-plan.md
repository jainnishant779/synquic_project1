# Working Demonstration Plan

**As of 2026-11-01.** Written for the team running the demo, and for a diligence reader checking what is real.

## What this demo proves

It proves the architecture runs end to end, with real control logic, on a laptop with no keys. It does not show AI-generated video or a trained LLM.

Say this out loud: "These clips are watermarked test patterns, and a tiny CPU classifier stands in for the LLM. What you're seeing is the pipeline, the gates and the isolation."

![POC coverage](../diagrams/06-poc-coverage.png)

| Part | Status |
|---|---|
| Storyboard schema, prompt compiler, provider dialects | [REAL] |
| ffprobe and ffmpeg QC, bounded regeneration, resume cache | [REAL] |
| ffmpeg assembly with captions | [REAL] |
| Credits charged from the workbook's rate card | [REAL: test_rate_card_matches_the_workbook] |
| PII redaction, per-tenant encryption, token-scoped API | [REAL], regex redaction and demo cipher |
| Gates, registry, rollback, canary leak detection | [REAL] |
| Isolation tests with negative controls | [REAL: test_isolation.py], one machine, application level |
| Video clips | [MOCK] watermarked ffmpeg test patterns |
| Planner | [MOCK] deterministic template |
| API and local adapters | [MOCK] tested against fake servers, never a live provider |
| Days, tenants | [SIMULATED] |
| Real generation, semantic QC, QLoRA, multi-adapter serving, KMS, cloud isolation, benchmarks | [DESIGN] |

## Run it

From the repo root, on Windows, with Python 3.14, ffmpeg and the packages in `poc/requirements.txt`:

```powershell
powershell -ExecutionPolicy Bypass -File poc\run_demo.ps1
```

This runs both flows and needs no keys and no spend. The 5-minute test takes several minutes on the reference laptop, so it is excluded from the live run.

## Video flow: about 2 minutes

**User input > Storyboard > Clips > Final video**

```powershell
python -m poc.video.cli --seconds 30 --fault sc01_sh02:1:black --fault sc02_sh01:1:frozen
```

| Step | Show | Point to make |
|---|---|---|
| 1 | `poc/video/sample_brief.json` | A brief with a character, a product and a style bible |
| 2 | `poc/runs/video/storyboard.json` | Canonical text appears in every shot prompt |
| 3 | Route line in the output | Router filters by capability, licence and cost |
| 4 | `total_attempts: 8` | 6 shots plus 2 regenerations: QC caught the injected black and frozen clips |
| 5 | `final.mp4` | Watermark on every frame, real assembly, caption track |
| 6 | `manifest.json` | Prompt hashes, attempts, QC results, `real_generation: false`, `semantic_qc: not_evaluated`, credits |

## Social 360 flow: about 2 minutes

**Secure ingestion > Automated learning > Evaluation > Updated model > Production API**

```powershell
python -m poc.social360.run_daily
python -m pytest poc/tests/test_isolation.py -v
```

| Step | Show | Point to make |
|---|---|---|
| 1 | Banner | Synthetic data, fictional tenants, simulated days |
| 2 | Day 1 | Ingests, redacts PII, refuses unapproved records, trains, promotes |
| 3 | Day 2 | Too little data, so no training |
| 4 | Day 3 | Bad candidate rejected, champion stays |
| 5 | Day 4 and 5 | Promotion, then rollback |
| 6 | API response | Version header, and retrieval limited to that tenant |
| 7 | `test_08_negative_control` | The detectors fire on a deliberate leak, so a pass elsewhere means something |

## Questions to expect

| Question | Honest answer |
|---|---|
| Is this AI video? | No. The clips are test patterns. The API path is built but has never called a live provider |
| Have you trained a model? | A tiny classifier, on CPU, to exercise the pipeline. No LLM has been trained |
| What's the cost of a 5-minute video? | It depends mainly on accept rate, which nobody has reliably published. See [doc 06](06-gpu-deployment-cost-assessment.md) for the range. A pilot is the next step |
| Is tenant data safe? | The tests show application-level isolation on one machine. Cloud and GPU isolation are designed, not built |
| Do you learn across customers? | No. Tenant data never reaches the shared base. That is a deliberate trade-off |
| Do you beat GPT or Claude? | Unknown. The benchmark protocol exists, and results need real held-out data |

## Next demo: with real footage

One short real clip set needs an API key and a spend cap. The API adapter's payload mapping must first be confirmed against the provider's docs, because it has never been run live.

```powershell
# After configuring a provider in poc/video/adapters/api_http.py
$env:VIDEO_API_KEY = '...'
```

A live GPU demo of LoRA hot-swapping, as proposed in the earlier report, needs a rented cluster, a trained adapter and a smoke test of vLLM LoRA on the chosen base (R5-104). None of those exist yet, so it is a later milestone.
