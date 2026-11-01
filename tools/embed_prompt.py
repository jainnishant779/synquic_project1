"""Copy poc\\prompts\\master_prompt.md into docs\\02-master-prompt.md so the two cannot drift."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "02-master-prompt.md"
PROMPT = ROOT / "poc" / "prompts" / "master_prompt.md"
BLOCK = re.compile(r"(<!-- BEGIN master_prompt -->\n).*?(<!-- END master_prompt -->)", re.DOTALL)


def main():
    text = DOC.read_text(encoding="utf-8")
    body = PROMPT.read_text(encoding="utf-8").strip().replace("```", "'''")
    embedded = f"```text\n{body}\n```\n"
    updated, count = BLOCK.subn(lambda m: m.group(1) + embedded + m.group(2), text)
    if count != 1:
        print("marker block not found in docs/02-master-prompt.md")
        return 1
    DOC.write_text(updated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
