from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT_TAG = "fmxmlsnippet"
ROOT_TYPE = "FMObjectList"

OPENERS = {"If": "End If", "Loop": "End Loop"}
CLOSERS = {value: key for key, value in OPENERS.items()}
MIDDLE = {"Else", "Else If"}

# Explicitly blocked because they are later-version features or outside this 19.5 toolkit.
FORBIDDEN_STEP_NAMES = {
    "Open Transaction",
    "Commit Transaction",
    "Revert Transaction",
    "Perform Script on Server with Callback",
}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str


def strip_xml_declaration(text: str) -> str:
    return re.sub(r"^\ufeff?\s*<\?xml[^?]*\?>\s*", "", text, count=1)


def parse_snippet(text: str) -> ET.Element:
    return ET.fromstring(text)


def validate_snippet_text(text: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        root = parse_snippet(text)
    except ET.ParseError as exc:
        return [Finding("error", "XML_PARSE", str(exc))]

    if root.tag != ROOT_TAG:
        findings.append(Finding("error", "ROOT_TAG", f"root must be <{ROOT_TAG}>"))
    if root.attrib.get("type") != ROOT_TYPE:
        findings.append(Finding("error", "ROOT_TYPE", f'type must be "{ROOT_TYPE}"'))

    children = list(root)
    if not children:
        findings.append(Finding("error", "EMPTY", "snippet contains no objects"))
        return findings
    if any(child.tag != "Step" for child in children):
        findings.append(Finding("error", "OBJECT_TYPE", "this toolkit accepts script steps only"))

    stack: list[str] = []
    for index, step in enumerate(children, start=1):
        if step.tag != "Step":
            continue
        name = step.attrib.get("name", "")
        step_id = step.attrib.get("id")
        if not name:
            findings.append(Finding("error", "STEP_NAME", f"step {index} has no name"))
        if step_id is None:
            findings.append(Finding("error", "STEP_ID", f"step {index} ({name}) has no id"))
        if step.attrib.get("enable") not in {"True", "False"}:
            findings.append(Finding("error", "STEP_ENABLE", f"step {index} ({name}) has invalid enable"))
        if name in FORBIDDEN_STEP_NAMES:
            findings.append(Finding("error", "FM19_5_FORBIDDEN", f"{name} is not allowed for the 19.5 target"))

        if name in OPENERS:
            stack.append(name)
        elif name in MIDDLE:
            if not stack or stack[-1] != "If":
                findings.append(Finding("error", "BLOCK_MIDDLE", f"{name} at step {index} is outside If"))
        elif name in CLOSERS:
            expected_open = CLOSERS[name]
            if not stack:
                findings.append(Finding("error", "BLOCK_CLOSE", f"{name} at step {index} has no opener"))
            elif stack[-1] != expected_open:
                findings.append(Finding("error", "BLOCK_NEST", f"{name} closes {stack[-1]} at step {index}"))
            else:
                stack.pop()

    for opener in reversed(stack):
        findings.append(Finding("error", "BLOCK_UNCLOSED", f"{opener} is not closed by {OPENERS[opener]}"))

    return findings


def validate_snippet_file(path: str | Path) -> list[Finding]:
    return validate_snippet_text(Path(path).read_text(encoding="utf-8-sig"))
