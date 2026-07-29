from __future__ import annotations

import json
from pathlib import Path

from fms19_toolkit.compatibility import (
    RESEARCH_CATALOG_PATH,
    RESEARCH_SOURCES_PATH,
    build_normalized_catalog,
    build_normalized_sources,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "catalog/fm19.5/compatibility"


def _load(relative: str) -> dict:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def _write(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    research_catalog = _load(RESEARCH_CATALOG_PATH)
    research_sources = _load(RESEARCH_SOURCES_PATH)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _write(
        OUTPUT_DIR / "script-steps.json",
        build_normalized_catalog(research_catalog),
    )
    _write(
        OUTPUT_DIR / "sources.json",
        build_normalized_sources(research_catalog, research_sources),
    )
    print("Compatibility catalog generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
