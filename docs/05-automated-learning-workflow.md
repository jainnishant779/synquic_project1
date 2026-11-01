# Automated Learning Workflow

**As of 2026-11-01.** Written for engineers reviewing the design. "Daily ingestion and RAG refresh; adapter retraining is triggered, batched and gated." Nothing here is online learning.

## Summary

Each day, approved brand data is ingested and redacted, and that brand's retrieval index is refreshed. Separately, when enough new data has built up, a candidate adapter is trained and must pass four gates before it reaches production. Every version is immutable and can be rolled back.

A tiny CPU classifier exercises the pipeline. No LLM has been trained.

![Learning loop](../diagrams/04-learning-loop.png)

## Why it is shaped this way

- **Facts go in RAG, not weights.** RAG beats fine-tuning for facts. In one study on current events, adding fine-tuning made RAG worse, 0.875 falling to 0.830 (R6-017, R6-018, R6-019).
- **Adapters must earn their place.** Small-data QLoRA showed limited utility, and no study has tested brand voice directly (R6-020, R6-025). Fine-tuning does beat prompting on style transfer (R6-021, R6-022). So an adapter goes live only if it beats a few-shot prompt baseline on that brand's held-out data.
- **Scheduled, not online.** Evidence conflicts on forgetting, and no controlled comparison of online and scheduled retraining was found (R6-027, R6-028, R6-029). Scheduled is the conservative choice.
- **Retraining stays gated.** Daily fine-tuning would add cost and risk, and small daily additions rarely move a model. Retrieval already carries daily freshness.

## Pipeline

| Step | What happens | POC status |
|---|---|---|
| 1. Authorise | Tenant comes from the signed token, never from request data | [REAL: test_01_token_cannot_name_another_tenant] |
| 2. Approve | Only records marked approved enter | [REAL: test_ingest_refuses_unapproved_and_stores_no_pii] |
| 3. Redact | PII removed before storage | [REAL: test_redaction_removes_email_phone_and_handle], regex only. Production needs an NER-based redactor [DESIGN] |
| 4. Store | Encrypted per tenant with a per-tenant key | [REAL: test_03_stores_are_keyed_and_encrypted]. Demo cipher; production uses KMS and AES-GCM [DESIGN] |
| 5. Refresh RAG | Tenant index rebuilt | [REAL: test_02_retrieval_returns_only_own_records], BM25 |
| 6. Extract insights | Patterns per label stored with the version | Rule-based [REAL]. LLM extraction is [DESIGN] |
| 7. Build dataset | Hashed, recorded in version metadata, disjoint from golden set | [REAL: test_versions_are_immutable_and_record_lineage] |
| 8. Train | Low-rank adapter trained on frozen base | Tiny classifier [REAL: test_learning_improves_on_the_base_model]. QLoRA is [DESIGN] |
| 9. Gate | G1 to G4 below | [REAL] for the classifier |
| 10. Promote | Atomic per-tenant pointer move, with rollback | [REAL: test_day_sequence] |

**Data sources.** The workflow trains only on what R7 permits; see [doc 04](04-social360-architecture.md). API engagement data is for live reporting, kept per tenant, and is not used for training unless the platform agrees in writing. `[COUNSEL]`

## Gates

| Gate | Passes when | On failure | Evidence |
|---|---|---|---|
| G1 Data | Enough examples, none overlapping the golden set, no PII hits, dataset hash recorded | Reject | [REAL: test_data_gate_rejects_golden_overlap_and_pii] |
| G2 Quality | Paired bootstrap lower bound of candidate minus champion is above the margin | Reject, champion stays | [REAL: test_quality_gate_decisions] |
| G3 Leakage | No other tenant's canary in the artefact | Discard artefact, keep metadata, raise incident | [REAL: test_08b_leakage_gate_blocks_promotion] |
| G4 Latency | p95 within budget | Reject | [REAL] on CPU. The demo budget says nothing about LLM serving |

Production adds to G2 a comparison against the few-shot baseline, and to G3 generated canary probes, because LoRA reduces membership leakage but does not remove it (R6-054, R6-055, R6-058).

**Simulated run.** `python -m poc.social360.run_daily` produces the following for two fictional tenants. [SIMULATED] days, [REAL: test_day_sequence] outcomes.

| Day | Event | Outcome |
|---|---|---|
| 1 | 60 new examples | Promoted over the base |
| 2 | 5 new examples | Skipped, too few |
| 3 | Fixture trainer on rotated labels | Rejected, champion stays |
| 4 | 40 new examples | Promoted |
| 5 | Operator rollback | Previous version restored |

Accuracy in that run moves from about 0.7 to about 0.9 on a synthetic task built so that the same word means opposite things per brand. It shows the machinery works. It says nothing about real brand data.

## Versioning

Each version records its dataset hash, base model revision, previous version, gate results and insights. Versions are never overwritten. Each tenant has its own `prod` pointer and history.

vLLM, SGLang and Ray docs define no adapter version concept. llm-d's name-to-version mapping with traffic shifting is the one pattern found (R6-032), so the registry owns versions and maps them to served adapter names. Swaps need matching target layers (R6-033), and mixed ranks raised P95 TTFT by 84% (R6-043), so one rank is fixed across the fleet.

## Benchmark protocol

Doc-level results do not exist yet. This is the pre-registered protocol. No public brand-voice benchmark was found (R6-060 onward; see the R6 brief), so a private one must be built.

**Compare, per brand:**

1. Base model alone.
2. Base with few-shot examples.
3. Base with few-shot examples and RAG.
4. Base with RAG and adapter.
5. A commercial general-purpose LLM, under its terms.

**Tasks.** Sentiment and intent on the brand's comments, brand voice rewriting, comment replies, content calendar generation, and factual Q&A from brand documents.

**Rules, fixed before any run**

- Golden sets are held out, frozen, and hashed before training starts.
- Reviewers score blind, and inter-rater agreement is reported.
- Sample size and the primary metric are stated up front. Use the metric ensemble in R6-022 for voice.
- Results are reported with confidence intervals and failures, including null results.
- If adapters do not beat option 3, drop them, along with their serving, leakage and retraining costs.

**TweetEval** is usable for sentiment, though its licences vary by subset (R6-062). DeepEval and promptfoo are active; promptfoo is now part of OpenAI but stays MIT (R6-065, R6-067).

Until this runs on real held-out data, no comparative claim can be made. The Table 7 figures in the earlier report are not results.

## Monitoring and operations

Metrics carry counts and hashes, never content. [REAL: test_07_logs_and_metrics_hold_no_content] Watch retrieval hit rate, rejection rate per gate, adapter age, latency per adapter and feedback from reviewers.

Log FLOP per training run. It is cheap evidence that adapters stay under the GPAI modification threshold (R7-065, R7-067). `[COUNSEL]`
