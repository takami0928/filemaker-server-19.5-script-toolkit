import unittest

from fms19_toolkit.snippet import validate_snippet_text


class SnippetTests(unittest.TestCase):
    def test_minimal_valid(self):
        xml = '<fmxmlsnippet type="FMObjectList"><Step enable="True" id="89" name="# (comment)"><Text>x</Text></Step></fmxmlsnippet>'
        self.assertEqual(validate_snippet_text(xml), [])

    def test_rejects_later_feature(self):
        xml = '<fmxmlsnippet type="FMObjectList"><Step enable="True" id="0" name="Open Transaction"/></fmxmlsnippet>'
        findings = validate_snippet_text(xml)
        self.assertTrue(any(f.code == "FM19_5_FORBIDDEN" for f in findings))

    def test_unbalanced_if(self):
        xml = '<fmxmlsnippet type="FMObjectList"><Step enable="True" id="68" name="If"><Calculation>1</Calculation></Step></fmxmlsnippet>'
        findings = validate_snippet_text(xml)
        self.assertTrue(any(f.code == "BLOCK_UNCLOSED" for f in findings))


if __name__ == "__main__":
    unittest.main()
