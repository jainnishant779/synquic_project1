# Roadmap and YC Readiness

**As of 2026-11-01.** Written for YC partners and technical diligence reviewers. Dates are relative to the start of work, for a team of 2 or 3 engineers `[ASSUMPTION]`.

## Where things stand

**Built.** A tested skeleton of both pipelines, a sourced fact ledger, a costed workbook, and an architecture for each product.

**Not built.** Real video generation, a trained LLM, or anything run on real customer data. See [doc 07](07-demo-plan.md).

**The technical story.** Video models and LLMs are commoditising, and vendors disappear. So Synquic owns the layers that last: the shot pipeline, the provider-neutral plan, QC, per-brand knowledge, and the evaluation evidence.

**The honest risk.** Unit economics depend on an accept rate no one has measured reliably. The first month exists to measure it.

## First 30 days: measure

Goal: replace the biggest assumptions with data.

| Work | Output | Done when |
|---|---|---|
| Video pilot: 50 to 100 shots across 2 or 3 models, on real briefs | Accept rate per route, rejection reasons, hand-labelled defects | Workbook updated from pilot data |
| Confirm one API adapter against a live provider | First real clips in the pipeline | Real run replaces the mock in the demo |
| Rented GPU day: Wan 2.2 and one adapter smoke test | Real render times; LoRA on quantised bases settled | R5-104 closed |
| Counsel review | Runway, TikTok, Reddit, Alibaba, Gemini, Lightricks, InsightFace, music | Data table and licence verdicts final; at least one API route cleared |
| Choose an identity check | A commercially licensed face-matching option | The pilot can measure character drift |
| Sub-processor and residency review | Vendor retention, input-training and region table | Customer assets can lawfully enter the pipeline |
| Competitor price survey | What customers pay per finished video today | Pricing has a market reference |

## Days 31 to 90: first real product

Goal: paying design partners on short-form video and grounded insights.

| Video | Social 360 |
|---|---|
| Live planner on the master prompt | Per-brand RAG on first-party documents |
| Keyframe-first flow with human approval | Bake-off of Gemma 4 31B and Qwen3.8-27B on real tasks |
| Semantic QC, calibrated on pilot labels | Private benchmark on real held-out brand data |
| Licensed voice, keyframes, lip-sync | Adapter pilot against the few-shot baseline |
| Credit ledger with refund reconciliation | Gateway with `cache_salt`, immutable adapters, vLLM v0.31.0 or later |
| C2PA and watermarking on by default | KMS-backed per-tenant keys |

**Decisions at day 90**

- Keep or drop adapters, based on the pilot.
- Self-host or stay on APIs, based on measured render time and quality.
- Which video length to sell first, based on measured cost.

## Days 91 to 180: harden and scale

| Area | Work |
|---|---|
| Long form | 5-minute jobs, continuity records, reappearing-character handling |
| Reliability | Second and third provider per tier, automatic reroute, cost alerts |
| Trust | SOC 2 Type 1 path, DPA template, DPIA, AI Act transparency compliance review, penetration test |
| Commercial | Credit packs repriced from real cost; Social 360 integrated into the platform |
| Self-hosting | Only if day 90 justified it |

## Budget

Rough, excluding salaries. All `[ESTIMATE]`.

| Period | Item | USD |
|---|---|---|
| Days 1 to 30 | Pilot API spend, rented GPU tests | 500 to 1,000 |
| Days 1 to 30 | Counsel | 5,000 to 15,000 |
| Days 31 to 90 | Always-on inference GPU, three months at the A100 rate (R3-005) | 3,900 |
| Days 31 to 90 | Design-partner video COGS, capped | 3,000 to 10,000 |
| Days 91 to 180 | SOC 2 Type 1 path and penetration test (R7-084, R7-085, R7-086) | 15,000 to 40,000 |

## Team

| Role | Why |
|---|---|
| ML engineer | Video pipeline, QC calibration, evaluation |
| Backend engineer | Orchestration, tenancy, ledger, adapters |
| Part-time counsel | Platform terms, licences, AI Act, DPAs |
| Later: product designer | Approval flows are where quality is won |

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Accept rate stays low | Medium | High | Pilot first; keyframe-first; sell short form first |
| Vendor shuts down a model | High | Medium | Multi-vendor adapter, neutral plans; it has already happened (R1-001) |
| Vendor raises prices | Medium | Medium | Rebuild rate card from the ledger; keep a second route |
| Competing-use clauses bite | Medium | High | Counsel review; no training on vendor outputs (R1-096, V-040, R2-005) |
| Platform data cannot train adapters | High | Medium | First-party sources; RAG carries value without training (R7-005, R7-008) |
| Adapters show no benefit | Medium | Low | Drop them and save cost. RAG remains the core |
| Cross-tenant leak | Low | Critical | Security floor in doc 04; canary audits; dedicated replicas for sensitive tenants |
| Identity drift in long form | High | Medium | Keyframes, continuity record, human review (R4-034) |
| Synthetic-person regulation | Medium | Medium | Disclosure default, no fake testimonials (R7-060, R7-068, R7-070) |

## Diligence pack

| Question | Where |
|---|---|
| Which models, at what price, under what licence? | [Doc 01](01-video-models-and-pricing.md), [workbook](../workbook/synquic_comparison_pricing.xlsx) |
| How do you turn a brief into a film? | [Doc 02](02-master-prompt.md), [doc 03](03-video-production-architecture.md) |
| How is tenant data protected? | [Doc 04](04-social360-architecture.md), `poc/tests/test_isolation.py` |
| How does the model improve safely? | [Doc 05](05-automated-learning-workflow.md) |
| What does it cost? | [Doc 06](06-gpu-deployment-cost-assessment.md) |
| What can I see running? | [Doc 07](07-demo-plan.md) |
| How do I trust any of this? | [Doc 09](09-claims-register.md), `research/facts.csv` |

## Terms to use in the pitch

| Say | Do not say |
|---|---|
| Proprietary adapters, data pipeline and evaluation suite, built on an open-weight base | Our own foundation model |
| Daily ingestion and RAG refresh; adapter retraining is triggered, batched and gated | Self-learning model |
| Designed to support GDPR and SOC 2 | Compliant, certified |
| Isolation tested at application level, with negative controls | Mathematically isolated |
| Automated checks for technical defects, human review for quality | Fully automated QC |
