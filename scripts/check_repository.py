from __future__ import annotations

from pathlib import Path
import sys

from fms19_toolkit.repository_policy import check_repository


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = check_repository(root)
    if not errors:
        print("Repository policy checks passed.")
        return 0
    for error in errors:
        print(f"ERROR: {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
