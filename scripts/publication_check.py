from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "ARCHITECTURE.md",
    "SPECIFICATION.md",
    "LIMITATIONS.md",
    "ROADMAP.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    "LICENSE",
    "CITATION.cff",
    "REFERENCES.md",
    "docs/threat-model.md",
    "docs/settlement-model.md",
    "docs/liquidity-model.md",
    "docs/evidence-model.md",
    "docs/source-repositories.md",
    "docs/settlement-control-plane.md",
    "docs/settlement-compression.md",
    "docs/securitisation-settlement.md",
    "docs/t0-architecture.md",
]

README_SECTIONS = [
    "problem",
    "architecture",
    "why settlement compression matters",
    "what is implemented",
    "securitisation scenario",
    "failure scenarios",
    "quickstart",
    "control-plane summary output",
    "exception control model",
    "benchmark",
    "research motivation",
    "related implementations",
    "documentation",
    "limitations",
    "contributing",
    "security",
    "citation",
    "license",
]

SOURCE_URLS = [
    "https://github.com/vishnugovind10/tokenize-stack",
    "https://github.com/vishnugovind10/temporal-liquidity-risk",
    "https://github.com/vishnugovind10/institutional-settlement-state-machine",
    "https://github.com/vishnugovind10/canton-proofpack",
    "https://github.com/vishnugovind10/canton-sync-debt-observatory",
    "https://github.com/vishnugovind10/haircut",
    "https://github.com/vishnugovind10/arc-fintech-risk-layer",
    "https://github.com/vishnugovind10/liquid-proofpack",
    "https://github.com/vishnugovind10/liquid-witness",
    "https://github.com/vishnugovind10/correlation-governor",
]

SECRET_PATTERNS = [
    re.compile(r"gh[opsu]_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]


def fail(message: str) -> None:
    print(f"publication check failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    for file_name in REQUIRED_FILES:
        if not (ROOT / file_name).exists():
            fail(f"missing required file: {file_name}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for section in README_SECTIONS:
        if section not in readme:
            fail(f"README missing required section: {section}")
    for url in SOURCE_URLS:
        if url not in readme:
            fail(f"README missing source URL: {url}")

    critical_docs = ["README.md", "ARCHITECTURE.md", "SPECIFICATION.md", "LIMITATIONS.md", "SECURITY.md"]
    for doc in critical_docs:
        text = (ROOT / doc).read_text(encoding="utf-8")
        if "TODO" in text or "TBD" in text or "placeholder" in text.lower():
            fail(f"publication-critical placeholder text found in {doc}")

    for path in ROOT.rglob("*"):
        if ".git" in path.parts or path.is_dir() or path.suffix.lower() in {".png", ".gif"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                fail(f"secret-like token found in {path.relative_to(ROOT)}")

    run([sys.executable, "-m", "digital_collateral.demo"])
    run([sys.executable, "-m", "digital_collateral.demo", "--scenario", "temporal-liquidity-failure"])
    run([sys.executable, "-m", "digital_collateral.demo", "--scenario", "securitisation-settlement"])
    run([sys.executable, "-m", "digital_collateral.demo", "--control-plane-summary"])
    run([sys.executable, "-m", "digital_collateral.experiments.compression"])
    run([sys.executable, "-m", "pytest"])
    print("publication check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
