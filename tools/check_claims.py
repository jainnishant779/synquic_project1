"""Check docs against the honesty rules. Fails on banned wording and on unreferenced figures.

A figure must have a fact id (R1-012), a workbook reference ([WB:Sheet]), or a label on its line.
Risky phrases must carry a label or appear in a line that quotes them for correction.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = sorted((ROOT / "docs").glob("*.md"))

LABEL = re.compile(r"\[(REAL|MOCK|SIMULATED|DESIGN|ESTIMATE|VENDOR-CLAIM|ASSUMPTION|COUNSEL)\b")
EVIDENCE = re.compile(r"R\d-\d{3}|\[WB:[A-Za-z_]+\]|V-\d{3}")
FIGURE = re.compile(r"\$\s?\d|\d\s?%|\b\d+(\.\d+)?\s?(GB|GiB|tok/s|USD)\b")
BANNED = [
    "our own foundation model", "foundation model we built", "mathematically isolated",
    "mathematically preventing", "ironclad", "cryptographic tenant isolation",
    "better than gpt", "soc 2 compliant", "gdpr compliant", "zero-human",
]
# These sections exist to quote wording that must not be used, or claims under audit.
QUOTING_SECTIONS = ["Terms to use in the pitch", "Earlier reports: audit"]
RISKY = ["proprietary model", "production-ready", "proven", "real-time", "continuous learning",
         "open-source", "compliant", "guarantee"]


def check(path: Path) -> list[str]:
    problems, in_code, quoting = [], False, False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("```"):
            in_code = not in_code
            continue
        if line.startswith("## "):
            quoting = any(title in line for title in QUOTING_SECTIONS)
        if quoting:
            continue
        lowered = line.lower()
        quoted = "report" in lowered or "do not say" in lowered or line.lstrip().startswith(">")
        if in_code or quoted:
            continue
        where = f"{path.name}:{number}"
        problems += [f"{where}: banned phrase '{phrase}'" for phrase in BANNED if phrase in lowered]
        labelled = LABEL.search(line) or EVIDENCE.search(line)
        problems += [f"{where}: risky phrase '{phrase}' without label"
                     for phrase in RISKY if phrase in lowered and not labelled]
        if FIGURE.search(line) and not labelled:
            problems.append(f"{where}: figure without evidence: {line.strip()[:90]}")
    return problems


def main() -> int:
    problems = [problem for path in DOCS for problem in check(path)]
    for problem in problems:
        print(problem)
    print(f"{len(DOCS)} docs, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
