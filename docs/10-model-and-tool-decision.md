# 10. Model and tool decision (as of 2026-11-01)

Built from research R8 to R12 and verification V4 to V6 (`research/facts.csv`, 1368 facts, 631 verified). Costs marked [ESTIMATE] are my arithmetic on listed prices. Licence and origin points are for counsel [COUNSEL]. Open founder decisions are listed at the end and are not decided here.

## 1. Main finding

The earlier main video model, Veo 3.1, was chosen for Google's no-training terms. On Artificial Analysis (AA) it now ranks 962 text-to-video and 953 image-to-video, far below the top group (R8-019, verified by V4). It costs 0.20 to 0.40 USD/s on fal. Google's newer Gemini Omni Flash 1.1 has the same terms family, costs about 0.10 USD/s, and ranks higher on text-to-video (1128), but only 1046 on image-to-video. Product shots are image-to-video, so quality moves to other models.

## 2. Video: cost per usable second

Accept rate is still unmeasured. Columns show price per generated second divided by an assumed accept rate of 25% and 60% [ESTIMATE]. AA Elo is verified by V4 against the live boards; the resolution behind each Elo is not stated by AA (only MiniMax H3 is labelled 768p).

| Model | AA T2V / I2V | List USD/s | Per usable s at 25% / 60% | Origin | Status |
|---|---|---|---|---|---|
| Grok Imagine 1.5 Lite | 991 / 999 | 0.020 | 0.080 / 0.033 | US | Cheap filler. Price conflicts (AA 0.14/s, fal 0.01/s). xAI terms unread |
| HeyGen Video 1 | 1156 / 1120 | 0.03 at 768p (promo ended 2026-10-31) | 0.12 / 0.05 | US | Good value, but API terms not found. Do not recommend until read |
| MiniMax H3 768p | 1161 / 1128 | 0.08 | 0.32 / 0.13 | China | Best value for product image-to-video. API terms unreadable; weights licence bars US and EU |
| Wan 3.0 720p | 1175 / 1111 | 0.10 | 0.40 / 0.17 | China | Best for long text-to-video, up to 30 s. Alibaba competing-product and resale clauses need counsel |
| Gemini Omni Flash 1.1 | 1128 / 1046 | about 0.10 | 0.40 / 0.17 | US | Clean terms, weak on image-to-video |
| FLUX 3 Video standard | 1144 / 1071 | 0.17 (draft 0.06, FHD 0.29) | 0.68 / 0.28 | Germany | Non-Chinese. BFL has no output indemnity and its general terms allow training unless opted out |
| Kling 4.0 | not on AA | 0.157 at 720p | 0.63 / 0.26 | China | Direct price page unreadable; no independent score |
| Seedance 2.5 | 1157 / 1153 | 0.231 | 0.92 / 0.39 | China | Best image-to-video score, highest cost of the top group |
| Veo 3.1 / Lite | 962 / 953 | 0.20 to 0.40 | 0.80 to 1.60 / 0.33 to 0.67 | US | Worst value; keep only if terms outweigh quality |

Avoid P-Video-2-Pro: it inherits the MiniMax H3 licence by contract and carries no IP indemnity (R8-064, V4). "Blocked" is not supported; it is Counsel.

## 3. Everything else in the pipeline

| Stage | Pick | Price | Alternative | Note |
|---|---|---|---|---|
| Stills | Nano Banana 2.1 | 0.0336 per 1K image, up to 14 reference images | Muse Image 0.01 (preview, terms unread) | Paid Google API does not train on prompts. Overlay real logos in post; no model renders them reliably |
| Apparel try-on | FASHN Try-On Max | about 0.075 | Nano Banana 2.1 with references | No independent print or text test exists. Pilot on your own garments first. FASHN's legal entity is UK (V5) |
| Upscale to 1080p | Topaz Proteus | 0.02 per s | ByteDance upscaler 0.0072/s (China) | Avoid generative upscalers on product shots |
| Voice, English | ElevenLabs v4 Turbo | 0.04 per 1K chars, AA rank 1 | Gemini 3.8 Flash-Lite TTS, about 0.009/min | A 30 s script is about 450 characters, so about 0.018 [ESTIMATE] |
| Voice, Hindi and Hinglish | Test Sarvam Bulbul V4 Flash | INR 1.00 per 1K chars | ElevenLabs | No independent Hinglish ranking exists. Sarvam bars standalone resale of audio |
| Music | Pixabay (free) or Lyria 3.5 | 0.08 per song | Epidemic Sound Partner API (price unpublished) | Lyria documents no output licence. ElevenLabs Music has employee caps and a model-resale ban |
| Captions | Script plus forced alignment | compute only | Sarvam STT INR 0.49/min | No speech recognition needed when we have the script |
| Assembly | FFmpeg | compute only | Shotstack 0.20/min as pilot fallback | Animated captions: one-day spike of HyperFrames (Apache-2.0) against Remotion |
| QC | PySceneDetect, PaddleOCR, SigLIP 2, one vision LLM | open or per-call | VideoScore2 as a weak secondary signal | Drop DOVER, FAST-VQA and Q-Align (S-Lab, non-commercial) |
| Identity check | Trial AuraFace and AWS Rekognition (1.00 per 1,000) | | InsightFace commercial quote | AuraFace has no LICENSE file and an unnamed training set: Counsel |
| Reusable repos | None as a base | | Borrow patterns from ViMax (MIT) and MoneyPrinterTurbo (MIT) | Avoid waoowaoo (Elastic License bars hosted service), ShortGPT (stale) |

## 4. Two paths for the video hero

| | Path A: China allowed | Path B: no Chinese-origin vendors |
|---|---|---|
| Product image-to-video | MiniMax H3 768p, then upscale | FLUX 3 Video standard, or HeyGen once its terms are read |
| Long text-to-video | Wan 3.0 | Gemini Omni Flash 1.1 |
| Filler | Grok Imagine 1.5 Lite | Grok Imagine 1.5 Lite |
| Hero cost per usable second at 60% | about 0.13 | about 0.28 |
| Main risk | MiniMax and Alibaba terms | Higher cost; weaker image-to-video scores |

Path B costs roughly twice as much per usable second for the hero shot [ESTIMATE]. The accept-rate test decides whether that matters.

## 5. Social 360

- **Base model:** the plan stays Gemma 4 31B (Apache 2.0, Google) with Qwen3.8-27B as fallback, and gpt-oss-20b and gpt-oss-120b added to the bake-off because sir wants GPT-OSS. Gemma and gpt-oss are both non-Chinese; Qwen is the Chinese-origin option.
- **Sir's "GPT-OSS is worse than GPT-4" test:** the fine-tuning notes say gpt-oss must always use the harmony chat format, which is the first thing to check. I found no source linking this to answer quality, so the bake-off must test it, not assume it.
- **Training stack:** Axolotl (Apache) or Unsloth core. Keep Unsloth's `studio/*` and `unsloth_cli/*` (AGPL) out. One ephemeral RunPod or SkyPilot GPU per run (L40S about 1.09 USD/hr for 31B), Prefect or cron to schedule, lm-evaluation-harness plus promptfoo or Inspect AI as the gate, self-hosted MLflow as the registry.
- **Serve:** vLLM multi-LoRA. GPT-OSS MoE LoRA was first implemented in vLLM 0.11.1rc3 and improved from 0.15.0 (V6 corrected the earlier "from 0.15.0"). Smoke-load every adapter on staging.
- **Can the platform's existing providers host a fine-tune?**
  - Groq: not as documented. LoRA is enterprise-only and only Llama 3.1 8B is listed.
  - Cerebras: only Dedicated Inference by enterprise contract. Custom gpt-oss is an inference, not a stated fact. Get it in writing.
  - Fireworks: documented, GPT-OSS 120B and 20B are listed upload architectures; H100 8.00 USD/hr.
  - Together: gpt-oss upload not confirmed; H100 5.49 USD/GPU-hr.
  - So a custom adapter means a dedicated GPU somewhere, not a per-token API.
- **Pooled learning from all brands, retrained every 1 to 2 hours:** this conflicts with the per-brand design. Hourly adapter retraining is not needed for freshness; hourly retrieval refresh gives that. Pooled training needs per-brand consent and data that is eligible for training; platform_api data is never eligible.
- **"Nobody sees raw data":** Presidio may miss sensitive data, so redaction is not a guarantee. Confidential GPUs (Azure H100 6.98 USD/hr) stop the host operator reading memory but not a guest admin. A locked image with no SSH, attestation and customer-managed keys is also needed. No canary-insertion tool exists; build one.

## 6. Proposed paid mini test, for approval

Same 8 product prompts, 5 s each, 40 s per model: H3, Wan 3.0, Omni Flash 1.1, FLUX 3 Video standard, HeyGen, Grok Lite, Kling 4.0, Seedance 2.5. About 36 USD in video plus about 0.30 for 8 stills [ESTIMATE]. This fits inside the 40 to 64 USD range already discussed. Score each clip as usable or not by two raters, then rank by price per usable second. No customer data. API terms still apply.

## 7. Known gaps

- arena.ai scores were not verified (no URL in the verifier queue). AA does not state the resolution behind each Elo.
- HeyGen API terms, MiniMax API terms, Kling and LTX direct prices could not be read.
- 41 facts remain in conflict; 42 unverifiable. Many repo star counts are verified but commit dates are not, because the GitHub API returned 403.
- All vendor_origin facts rest on Wikipedia.
- No accept-rate data exists for any model. Every per-usable-second figure above depends on the test in section 6.

## 8. Open founder decisions (not decided here)

1. Are Chinese-origin vendors acceptable? Recommendation: build the adapter layer vendor-neutral and let the test price both paths.
2. Pooled or per-brand learning? Recommendation: per-brand adapters plus pooled, consented, anonymised data only for the shared base.
3. Realistic AI video or animated images? Recommendation: hybrid with the spend cap.
4. 30-second launch format. Recommendation: yes; gate 5-minute until the test passes.

## 9. First measured results (Kaggle T4, notebook 1, 2026-11-02) [REAL: run, one seed, 4 prompts, not yet rated by a person]

| Model | Result | Time per image | Peak GPU memory |
|---|---|---|---|
| FLUX.2 klein 4B (Apache) | 4 of 4 made. T-shirt text NORTHWIND exact; serum label GLOW 30ML exact, with one extra garbled line | about 29 s | 8.4 GB |
| Sana 1.6B | 4 of 4 made. T-shirt read "NIRTH WIRID"; serum label lost "ML" | about 22 s | 5.3 GB |
| Z-Image-Turbo | 4 of 4 blank (3 KB files): float16 failed. Now set to bfloat16, retest pending | about 50 s | 12.8 GB |
| Wan 2.2 5B image-to-video | Out of memory at 832x480 (15.4 GB peak on a 14.6 GB GPU). Notebook now falls back to 640x352 then 512x288 | | |
| Kandinsky 6 Lite, Wan 2.1 | Worker exit code 1, reason lost. Notebook now records the load error | | |

Text rendering is judged by eye on one image per prompt, so it is a sample of 4, not a measurement. The raw files are in `results/synquic_results/`.
