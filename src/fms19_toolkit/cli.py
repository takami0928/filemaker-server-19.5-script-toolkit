from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .renderer import render_ir_file
from .script_ir import migrate_ir_file, validate_ir_file
from .snippet import validate_snippet_file
from .windows_clipboard import DEFAULT_FORMAT, detect_formats, read_xml, write_xml


def _lint(path: str) -> int:
    findings = validate_snippet_file(path)
    if not findings:
        print(f"OK: {path}")
        return 0
    for finding in findings:
        print(f"{finding.severity.upper()} {finding.code}: {finding.message}")
    return 1 if any(f.severity == "error" for f in findings) else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FileMaker Server 19.5 script XML toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    lint_p = sub.add_parser("lint", help="validate an fmxmlsnippet")
    lint_p.add_argument("xml")

    render_p = sub.add_parser("render", help="render conservative JSON IR to fmxmlsnippet")
    render_p.add_argument("input")
    render_p.add_argument("output")

    validate_ir_p = sub.add_parser(
        "validate-ir",
        help="validate Script IR v1 or v2",
    )
    validate_ir_p.add_argument("input")

    migrate_ir_p = sub.add_parser(
        "migrate-ir",
        help="deterministically migrate Script IR v1 to v2",
    )
    migrate_ir_p.add_argument("input")
    migrate_ir_p.add_argument("output")

    write_p = sub.add_parser("clipboard-write", help="write XML to Windows FileMaker clipboard format")
    write_p.add_argument("xml")
    write_p.add_argument("--format", default=DEFAULT_FORMAT)

    read_p = sub.add_parser("clipboard-read", help="read Windows FileMaker clipboard XML")
    read_p.add_argument("output", nargs="?")
    read_p.add_argument("--format", default=DEFAULT_FORMAT)

    sub.add_parser("clipboard-detect", help="list Windows custom clipboard formats")

    args = parser.parse_args(argv)
    try:
        if args.command == "lint":
            return _lint(args.xml)
        if args.command == "render":
            render_ir_file(args.input, args.output)
            if _lint(args.output) != 0:
                return 1
            print(f"Rendered: {args.output}")
            return 0
        if args.command == "validate-ir":
            version = validate_ir_file(args.input)
            print(f"Valid Script IR v{version}: {args.input}")
            return 0
        if args.command == "migrate-ir":
            migrate_ir_file(args.input, args.output)
            print(f"Migrated Script IR v1 to v2: {args.output}")
            return 0
        if args.command == "clipboard-write":
            if _lint(args.xml) != 0:
                print("Clipboard not modified because validation failed.", file=sys.stderr)
                return 1
            xml = Path(args.xml).read_text(encoding="utf-8-sig")
            write_xml(xml, args.format)
            print(f"Clipboard ready as {args.format}: {args.xml}")
            return 0
        if args.command == "clipboard-read":
            xml = read_xml(args.format)
            if args.output:
                Path(args.output).write_text(xml + "\n", encoding="utf-8")
                print(f"Saved: {args.output}")
            else:
                print(xml)
            return 0
        if args.command == "clipboard-detect":
            for format_id, name in detect_formats():
                marker = "  <-- FileMaker candidate" if name.startswith("Mac-XM") else ""
                print(f"{format_id:6d}  {name}{marker}")
            return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
