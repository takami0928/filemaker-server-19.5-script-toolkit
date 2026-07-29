from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .compatibility import (
    CONTEXTS,
    RENDERER_STATUSES,
    SUPPORT_VALUES,
    CompatibilityCatalogError,
    compatibility_steps,
    filter_steps,
    find_exact_step,
    normalize_context,
    suggest_steps,
)
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


def _context_argument(value: str) -> str:
    try:
        return normalize_context(value)
    except CompatibilityCatalogError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _json_output(value: object) -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")
    print(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


def _important_messages(step: dict) -> list[str]:
    messages: list[str] = []
    summary = step.get("summary")
    if isinstance(summary, str) and summary.strip():
        messages.append(summary.strip())
    for field in ("contextRequirements", "contextEffects"):
        values = step.get(field)
        if isinstance(values, list):
            messages.extend(
                value.strip()
                for value in values
                if isinstance(value, str) and value.strip()
            )
    dialog = step.get("dialogBehavior")
    if isinstance(dialog, str) and dialog.strip():
        messages.append(dialog.strip())
    options = step.get("options")
    if isinstance(options, list):
        for option in options:
            if not isinstance(option, dict):
                continue
            name = option.get("option")
            effect = option.get("effect")
            execution_notes = option.get("executionNotes")
            parts = [
                value.strip()
                for value in (effect, execution_notes)
                if isinstance(value, str) and value.strip()
            ]
            if isinstance(name, str) and name.strip() and parts:
                messages.append(f"{name.strip()}: {' '.join(parts)}")
    risks = step.get("risks")
    if isinstance(risks, list):
        messages.extend(
            risk.strip()
            for risk in risks
            if isinstance(risk, str) and risk.strip()
        )
    transitions = step.get("versionTransitions")
    if isinstance(transitions, list):
        for transition in transitions:
            if not isinstance(transition, dict):
                continue
            version = transition.get("fromVersion")
            change = transition.get("change")
            if (
                isinstance(version, str)
                and version.strip()
                and isinstance(change, str)
                and change.strip()
            ):
                messages.append(
                    f"From {version.strip()}: {change.strip()}"
                )
    return list(dict.fromkeys(messages))


def _print_compatibility(step: dict, context: str | None) -> None:
    available = "available" if step["availableIn19_5"] else "unavailable"
    server_version = step.get("serverSupportIntroducedIn")
    if server_version is None:
        server_version = "unknown"

    print(step["name"])
    print()
    print(f"FileMaker Pro 19.5: {available}")
    print(f"Introduced in: {step['introducedIn']}")
    print(f"Server support introduced in: {server_version}")
    print(
        "Research: "
        f"{step['researchStatus']} (confidence: {step['confidence']})"
    )

    if context is not None:
        print()
        print("Selected context:")
        print(f"  {context}: {step['execution'][context]}")

    print()
    print("Execution:")
    for execution_context in CONTEXTS:
        print(f"  {execution_context}: {step['execution'][execution_context]}")

    print()
    print("Important:")
    important = _important_messages(step)
    if important:
        for message in important:
            print(f"  - {message}")
    else:
        print("  - No additional conditions recorded.")

    print()
    print("Renderer:")
    print(f"  status: {step['rendererStatus']}")
    fixture = step["fileMakerPro19_5Fixture"].replace("_", " ")
    print(f"  FileMaker Pro 19.5 fixture: {fixture}")

    print()
    print("Sources:")
    for source_id in step["sourceIds"]:
        print(f"  - {source_id}")


def _print_step_list(steps: list[dict], context: str | None) -> None:
    if context is None:
        headers = (
            "NAME",
            "CATEGORY",
            "PSOS",
            "SERVER_SCHEDULE",
            "RENDERER",
        )
        print("\t".join(headers))
        for step in steps:
            print(
                "\t".join(
                    (
                        step["name"],
                        step["category"],
                        step["execution"]["psos"],
                        step["execution"]["server_schedule"],
                        step["rendererStatus"],
                    )
                )
            )
        return

    print("\t".join(("NAME", "CATEGORY", context.upper(), "RENDERER")))
    for step in steps:
        print(
            "\t".join(
                (
                    step["name"],
                    step["category"],
                    step["execution"][context],
                    step["rendererStatus"],
                )
            )
        )


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

    compat_p = sub.add_parser(
        "compat",
        help="show FileMaker 19.5 compatibility for a script step",
    )
    compat_p.add_argument("step_name")
    compat_p.add_argument(
        "--context",
        type=_context_argument,
        metavar="CONTEXT",
        help="canonical execution context: " + ", ".join(CONTEXTS),
    )
    compat_p.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="emit deterministic JSON",
    )

    list_steps_p = sub.add_parser(
        "list-steps",
        help="list normalized FileMaker 19.5 script-step compatibility",
    )
    list_steps_p.add_argument(
        "--context",
        type=_context_argument,
        metavar="CONTEXT",
        help="canonical execution context: " + ", ".join(CONTEXTS),
    )
    list_steps_p.add_argument(
        "--support",
        choices=SUPPORT_VALUES,
        help="filter support in the selected context",
    )
    list_steps_p.add_argument(
        "--category",
        help="filter by exact catalog category",
    )
    list_steps_p.add_argument(
        "--renderer-status",
        choices=RENDERER_STATUSES,
        help="filter derived renderer status",
    )
    list_steps_p.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="emit deterministic JSON",
    )

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
        if args.command == "compat":
            steps = compatibility_steps()
            step = find_exact_step(args.step_name, steps)
            if step is None:
                suggestions = suggest_steps(args.step_name, steps)
                print(
                    f"ERROR: no exact script-step match for {args.step_name!r}.",
                    file=sys.stderr,
                )
                if suggestions:
                    print("Candidates:", file=sys.stderr)
                    for suggestion in suggestions:
                        print(f"  - {suggestion}", file=sys.stderr)
                return 2
            if args.json_output:
                _json_output(step)
            else:
                _print_compatibility(step, args.context)
            return 0
        if args.command == "list-steps":
            if args.support is not None and args.context is None:
                print("ERROR: --support requires --context.", file=sys.stderr)
                return 2
            steps = filter_steps(
                compatibility_steps(),
                context=args.context,
                support=args.support,
                category=args.category,
                renderer_status=args.renderer_status,
            )
            if args.json_output:
                _json_output(steps)
            else:
                _print_step_list(steps, args.context)
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
