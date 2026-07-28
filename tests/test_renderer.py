import unittest

from fms19_toolkit.renderer import render_ir
from fms19_toolkit.snippet import validate_snippet_text
from fms19_toolkit.windows_clipboard import build_windows_payload, parse_windows_payload


class RendererTests(unittest.TestCase):
    def test_render_and_payload_roundtrip(self):
        data = {
            "target": "FileMaker Server 19.5",
            "kind": "script_steps",
            "steps": [
                {"type": "set_error_capture", "state": True},
                {"type": "set_variable", "name": "$x", "calculation": "1", "repetition": "1"},
                {"type": "exit_script", "calculation": "$x"},
            ],
        }
        xml = render_ir(data)
        self.assertFalse(validate_snippet_text(xml))
        payload = build_windows_payload(xml)
        decoded = parse_windows_payload(payload)
        self.assertIn('name="Set Variable"', decoded)

    def test_render_balanced_if(self):
        data = {
            "target": "FileMaker Server 19.5",
            "kind": "script_steps",
            "steps": [
                {"type": "if", "calculation": "1"},
                {"type": "else"},
                {"type": "end_if"},
            ],
        }
        self.assertFalse(validate_snippet_text(render_ir(data)))

    def test_cdata_terminator_is_split(self):
        data = {
            "target": "FileMaker Server 19.5",
            "kind": "script_steps",
            "steps": [{"type": "set_variable", "name": "$x", "calculation": '"]]>"'}],
        }
        xml = render_ir(data)
        self.assertIn("]]><![CDATA[", xml)
        self.assertFalse(validate_snippet_text(xml))

    def test_end_if_is_self_closing(self):
        data = {
            "target": "FileMaker Server 19.5",
            "kind": "script_steps",
            "steps": [{"type": "if", "calculation": "1"}, {"type": "end_if"}],
        }
        xml = render_ir(data)
        self.assertIn('name="End If"/>', xml)

    def test_unknown_step_fails_closed(self):
        data = {"target": "FileMaker Server 19.5", "kind": "script_steps", "steps": [{"type": "delete_everything"}]}
        with self.assertRaises(ValueError):
            render_ir(data)


if __name__ == "__main__":
    unittest.main()
