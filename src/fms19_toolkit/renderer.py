from __future__ import annotations

from html import escape
import json
from pathlib import Path

from .script_ir import ensure_renderable_v2, normalize_ir_to_v2
from .snippet import validate_snippet_text

STEP_IDS = {
    "comment": (89, "# (comment)"),
    "set_error_capture": (86, "Set Error Capture"),
    "set_variable": (141, "Set Variable"),
    "if": (68, "If"),
    "else": (69, "Else"),
    "end_if": (70, "End If"),
    "exit_script": (103, "Exit Script"),
}


def cdata(value: str) -> str:
    # Split the only byte sequence that cannot appear inside a CDATA section.
    return "<![CDATA[" + value.replace("]]>", "]]]]><![CDATA[>") + "]]>"


def _step_open(step_type: str, enabled: bool) -> str:
    step_id, name = STEP_IDS[step_type]
    return f'  <Step enable="{"True" if enabled else "False"}" id="{step_id}" name="{escape(name)}">'


def render_step(step: dict) -> list[str]:
    kind = step.get("type")
    if kind not in STEP_IDS:
        raise ValueError(f"unsupported step type: {kind!r}")
    enabled = bool(step.get("enabled", True))
    lines = [_step_open(kind, enabled)]

    if kind == "comment":
        lines.append(f"    <Text>{escape(str(step.get('text', '')))}</Text>")
    elif kind == "set_error_capture":
        lines.append(f'    <Set state="{"True" if step.get("state", True) else "False"}"/>')
    elif kind == "set_variable":
        name = str(step.get("name", ""))
        if not name.startswith("$"):
            raise ValueError("Set Variable name must start with $ or $$")
        calculation = str(step.get("calculation", ""))
        repetition = str(step.get("repetition", "1"))
        lines.extend([
            "    <Value>",
            f"      <Calculation>{cdata(calculation)}</Calculation>",
            "    </Value>",
            "    <Repetition>",
            f"      <Calculation>{cdata(repetition)}</Calculation>",
            "    </Repetition>",
            f"    <Name>{escape(name)}</Name>",
        ])
    elif kind == "if":
        lines.append('    <Restore state="False"/>')
        lines.append(f"    <Calculation>{cdata(str(step.get('calculation', '')))}</Calculation>")
    elif kind == "else":
        lines.append('    <Restore state="False"/>')
    elif kind == "end_if":
        # FileMaker emits an empty self-closing Step for End If.
        return [lines[0][:-1] + "/>"]
    elif kind == "exit_script":
        calculation = str(step.get("calculation", ""))
        if calculation:
            lines.append(f"    <Calculation>{cdata(calculation)}</Calculation>")

    lines.append("  </Step>")
    return lines


def render_ir(data: dict) -> str:
    normalized = normalize_ir_to_v2(data)
    ensure_renderable_v2(normalized)
    steps = normalized["steps"]

    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<fmxmlsnippet type="FMObjectList">']
    for step in steps:
        lines.extend(render_step(step))
    lines.append("</fmxmlsnippet>")
    xml = "\n".join(lines) + "\n"

    findings = validate_snippet_text(xml)
    errors = [f for f in findings if f.severity == "error"]
    if errors:
        raise ValueError("rendered XML failed validation: " + "; ".join(f.message for f in errors))
    return xml


def render_ir_file(input_path: str | Path, output_path: str | Path) -> None:
    data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    Path(output_path).write_text(render_ir(data), encoding="utf-8", newline="\n")
