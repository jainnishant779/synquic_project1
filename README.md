# Synquic: AI Video Engine and Social 360

Technical and commercial assessment, architecture and proof of concept, as of 2026-11-01. Prepared for YC pitching and technical due diligence.

**Read this first.** The POCs run real pipeline logic with no keys and no spend. They do not produce AI video, and no LLM has been trained. Costs are estimates, and legal verdicts need a lawyer.

The repository holds two things:

1. **Research** for an AI video ad engine (Task 1) and Social 360 (Task 2): fact ledger, briefs, reports, diagrams, cost workbook, Kaggle benchmark notebooks and proofs of concept.
2. **Ad Studio**, a FastAPI web app that turns a prompt into an ad. Code and tests are in [web_ec2/](web_ec2). It is live at http://13.205.82.99/editor. Setup, configuration and how to run it locally are in [web_ec2/README.md](web_ec2/README.md); the system design is [Doc 11](docs/11-ad-studio-system.md).

**Picking this up?** Read [HANDOFF.md](HANDOFF.md): current state, next steps in order, decisions taken and open risks. Before spending on fal.ai, follow [Doc 13](docs/13-fal-spend-plan.md).

## Repository map

| Folder | Contents |
|---|---|
| [research/](research) | Fact ledger (`facts.csv`), research briefs, raw search output, verification queues and results |
| [docs/](docs) | Numbered markdown deliverables (01 to 12), Word and PDF reports |
| [diagrams/](diagrams) | Rendered diagrams (PNG, SVG); Mermaid sources in `diagrams/src/` |
| [workbook/](workbook) | Comparison and pricing workbook |
| [notebooks/](notebooks) | Kaggle benchmark notebooks |
| [results/](results) | Kaggle benchmark outputs (CSV summaries and stills) |
| [poc/](poc) | Video and Social 360 proofs of concept, with tests in `poc/tests/` |
| [tools/](tools) | Build, check and notebook-generation scripts |
| [web_ec2/](web_ec2) | Ad Studio app: `main.py`, ad engine and director, templates, `ad_template_library/`, `fal_schemas/`, tests in `web_ec2/tests/` |
| [archive/](archive) | One-off patch, test and debug scripts (`archive/scripts/`), test media (`archive/media/`), a snapshot of earlier server files (`archive/ec2_remote_snapshot/`). Kept for history; not part of the app |

API keys are never stored in the repository. Copy `web_ec2/.env.example` to `web_ec2/.env` and fill it in locally.

## Start here

| If you want | Read |
|---|---|
| The plan and risks | [Roadmap and YC readiness](docs/08-roadmap.md) |
| The numbers | [Cost and credit pricing](docs/06-gpu-deployment-cost-assessment.md) |
| What is real | [Demo plan](docs/07-demo-plan.md), [claims register](docs/09-claims-register.md) |
| Kaggle notebooks | notebooks/synquic_kaggle_1_open_models.ipynb (free open models, GPU), notebooks/synquic_kaggle_2_api_models.ipynb (paid APIs, no GPU, keys in Kaggle Secrets), notebooks/synquic_video_benchmark.ipynb (older, builds the 30 s reel). Build with tools/build_kaggle_open.py and tools/build_kaggle_api.py, test with tools/test_kaggle_notebooks.py (dry run only, no model or endpoint was called) |
| Model and tool decision | [Doc 10](docs/10-model-and-tool-decision.md). Word reports for sir: docs/Handoff-Task1-AI-Video-Engine-v4.docx, docs/Handoff-Task2-Social360-v3.docx, docs/Synquic-Final-Report-for-Sir.docx. Flow charts: diagrams 10 to 13 |
| The Ad Studio app | [web_ec2/README.md](web_ec2/README.md), [Doc 11](docs/11-ad-studio-system.md), roadmap in docs/Synquic-Ad-Studio-Roadmap.docx, flow chart diagrams/14-ad-studio-flow.png |

## Task 1 final plan

[docs/Task1-Final-Plan-and-Research-v2.docx](docs/Task1-Final-Plan-and-Research-v2.docx) is the current Task 1 document. Launch a hybrid 30-second video product on Veo 3.1 Fast, with a capped AI spend and animated-image fallback, after a paid mini test of about $40 to $64 and, if results are good, a full benchmark of about $486. The full-AI 5-minute route was rejected on cost. `docs/Task1-AI-Video-Engine-Research-Summary.docx` predates this decision. `[ESTIMATE]`

## Model benchmark notebook

[notebooks/synquic_video_benchmark.ipynb](notebooks/synquic_video_benchmark.ipynb) runs every prompt on every model on Kaggle, then does technical QC, cost comparison and a 30-second hybrid reel. Its flow is tested by `tools/test_kaggle_notebook.py` in dry-run mode. On a real T4 GPU it generated 3 LTX-Video clips at about 170 s each, and Wan 2.1 ran out of system RAM. Paid APIs have not been run live. Rebuild it with `tools/build_kaggle_notebook.py`.

## Sample data for Social 360

[poc/sample_data/social360_sample.jsonl](poc/sample_data/social360_sample.jsonl) shows the format the backend should export: six record types, system fields on every record, and no personal data. Both brands are fictional, and platform API records are marked as not training-eligible. Regenerate it with `python -m poc.social360.sample_dataset`. It is a schema example, not training data. `[SIMULATED]`

## Deliverables

| Deliverable | Location | Status |
|---|---|---|
| Model comparison and pricing sheet | [Doc 01](docs/01-video-models-and-pricing.md), [workbook](workbook/synquic_comparison_pricing.xlsx) | Done |
| Master prompt | [Doc 02](docs/02-master-prompt.md), [poc/prompts](poc/prompts) | Done, not run on a live model |
| Video production architecture | [Doc 03](docs/03-video-production-architecture.md) | Done |
| Social 360 architecture | [Doc 04](docs/04-social360-architecture.md) | Done |
| Automated learning workflow | [Doc 05](docs/05-automated-learning-workflow.md) | Done |
| GPU and deployment cost assessment | [Doc 06](docs/06-gpu-deployment-cost-assessment.md) | Done, provisional until a pilot runs |
| Working demonstration plan | [Doc 07](docs/07-demo-plan.md), [poc](poc) | Done |
| Technical documentation and roadmap | [Doc 08](docs/08-roadmap.md), [doc 09](docs/09-claims-register.md) | Done |

Architecture diagrams are in [diagrams](diagrams).

## Main findings

1. **Accept rate decides the economics.** A 5-minute video on Runway Gen-4.5 costs about $51 at an 85% accept rate, $258 at 25% and $551 at 10%, and below about 60% it cannot finish without people. None of those rates is a measured first-pass rate. Run a pilot first. `[ESTIMATE]`
2. **Platform terms limit training.** Plan on no platform API data in the shared base, and train brand adapters on first-party material. `[COUNSEL]`
3. **Much of the usual stack is not commercially clear.** InsightFace, XTTS-v2 and FLUX.1 dev are Blocked, which breaks most lip-sync and identity chains. No paid video API is clear either: Runway's terms allow training on inputs and bar competitive products. `[COUNSEL]`
4. **Adapters are unproven for brand voice.** RAG is the core. Each adapter must beat a few-shot baseline.
5. **Shared serving is a security decision.** vLLM v0.31.0 or later, server-side `cache_salt`, immutable adapters.

## Run it

```powershell
pip install -r poc/requirements.txt
powershell -ExecutionPolicy Bypass -File poc\run_demo.ps1   # both demos, no keys
python -m pytest poc/tests -q                               # includes a slow 5-minute render
```

Requires Python 3.14 and ffmpeg. Rebuild the research outputs with Excel installed:

```powershell
python tools/check_facts.py        # validate and merge the ledger
python tools/build_workbook.py     # build, recalculate in Excel, export rate card
python tools/verify_workbook.py    # independent recalculation
python tools/check_claims.py       # honesty rules on the docs
powershell -ExecutionPolicy Bypass -File tools\render_diagrams.ps1
```

To run the Ad Studio app, follow [web_ec2/README.md](web_ec2/README.md). Its tests run with `python -m pytest web_ec2/tests -q`.

## Labels

`[REAL: test]` runs today. `[MOCK]` is a stand-in. `[SIMULATED]` is synthetic. `[DESIGN]` is specified, not built. `[ESTIMATE]` is modelled. `[VENDOR-CLAIM]` is published, not reproduced. `[ASSUMPTION]` is chosen by us. `[COUNSEL]` needs a lawyer.

