"""Check docs against the honesty rules. Fails on banned wording and on unreferenced figures.

A figure must have a fact id (R1-012), a workbook reference ([WB:Sheet]), or a label on its line.
Risky phrases must carry a label or appear in a line that quotes them for correction.
Fact ids must exist in the ledger, and every [REAL: x] must name a real test or file. Bare [REAL] fails.
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = sorted((ROOT / "docs").glob("*.md"))
FACT_ID = re.compile(r"\b(?:R\d|V)-\d{3}\b")
REAL = re.compile(r"\[REAL(?:: ([^\]]+))?\]")

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


def known_facts() -> set[str]:
    with (ROOT / "research" / "facts.csv").open(encoding="utf-8") as handle:
        return {row["fact_id"] for row in csv.DictReader(handle)}


def known_tests() -> set[str]:
    names = set()
    for path in (ROOT / "poc" / "tests").glob("test_*.py"):
        names.add(path.name)
        names.update(re.findall(r"^def (test_\w+)", path.read_text(encoding="utf-8"), re.MULTILINE))
    return names


def check_references(path: Path, facts: set[str], tests: set[str]) -> list[str]:
    problems = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        where = f"{path.name}:{number}"
        problems += [f"{where}: unknown fact {fact}" for fact in FACT_ID.findall(line) if fact not in facts]
        if line.startswith("| `[REAL: test]`") or "`[REAL" in line:
            continue
        for target in REAL.findall(line):
            if not target:
                problems.append(f"{where}: bare [REAL]")
            elif target not in tests and not (ROOT / target).exists():
                problems.append(f"{where}: [REAL] names nothing that exists: {target}")
    return problems


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
        quoted = "earlier report" in lowered or "do not say" in lowered or line.lstrip().startswith(">")
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
    facts, tests = known_facts(), known_tests()
    problems = [problem for path in DOCS for problem in check(path) + check_references(path, facts, tests)]
    for problem in problems:
        print(problem)
    print(f"{len(DOCS)} docs, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
