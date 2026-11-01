# Synquic: AI Video Engine and Social 360

Technical and commercial assessment, architecture and proof of concept, as of 2026-11-01. Prepared for YC pitching and technical due diligence.

**Read this first.** The POCs run real pipeline logic with no keys and no spend. They do not produce AI video, and no LLM has been trained. Costs are estimates, and legal verdicts need a lawyer.

## Start here

| If you want | Read |
|---|---|
| The plan and risks | [Roadmap and YC readiness](docs/08-roadmap.md) |
| The numbers | [Cost and credit pricing](docs/06-gpu-deployment-cost-assessment.md) |
| What is real | [Demo plan](docs/07-demo-plan.md), [claims register](docs/09-claims-register.md) |

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

1. **Accept rate decides the economics.** A 5-minute video on Runway Gen-4.5 costs about $46 to $147 depending on it, and no reliable figure exists. Run a pilot first.
2. **Platform terms limit training.** Plan on no platform API data in the shared base, and train brand adapters on first-party material. `[COUNSEL]`
3. **Much of the common open-source stack is not commercially clear.** InsightFace, XTTS-v2 and FLUX.1 dev are Blocked, which breaks most lip-sync and identity chains. `[COUNSEL]`
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

## Labels

`[REAL: test]` runs today. `[MOCK]` is a stand-in. `[SIMULATED]` is synthetic. `[DESIGN]` is specified, not built. `[ESTIMATE]` is modelled. `[VENDOR-CLAIM]` is published, not reproduced. `[ASSUMPTION]` is chosen by us. `[COUNSEL]` needs a lawyer.

## Layout

```
docs/       deliverables, plus the two earlier reports as supplied
workbook/   comparison and pricing workbook
diagrams/   rendered diagrams and sources
research/   fact ledger, briefs, verification, audit list
poc/        video and Social 360 proofs of concept
tools/      build and check scripts
```
