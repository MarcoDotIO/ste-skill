"""Behavior tests for the limited, advisory prose checker."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/asd-ste100/scripts/check_ste.py"
SPEC = importlib.util.spec_from_file_location("check_ste", SCRIPT)
ste = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ste
SPEC.loader.exec_module(ste)


class ProseChecks(unittest.TestCase):
    def check(self, text, mode="procedure"):
        return ste.check_text(text, "sample.md", mode)

    def test_sentence_limits_and_mode(self):
        twenty = " ".join(["word"] * 20) + "."
        self.assertEqual(self.check(twenty), [])
        findings = self.check("word " + twenty)
        self.assertEqual([item.code for item in findings], ["sentence-length"])
        self.assertIn("21 words", findings[0].message)
        self.assertEqual(self.check("word " + twenty, "description"), [])
        self.assertEqual(len(self.check(" ".join(["word"] * 26), "description")), 1)

    def test_wrapped_sentence_is_one_sentence_with_source_lines(self):
        text = "# Title\n\n" + "word " * 12 + "\n" + "word " * 9 + ".\nDo not stop.\nYou shouldn't continue."
        findings = self.check(text)
        self.assertEqual([(f.code, f.line) for f in findings], [("sentence-length", 3), ("contraction", 6)])

    def test_numbered_steps_remain_separate_without_final_periods(self):
        text = "1. " + "word " * 14 + "\n2. " + "word " * 14
        self.assertEqual(self.check(text), [])
        wrapped = "1) " + "word " * 14 + "\n   " + "word " * 7
        self.assertEqual([f.code for f in self.check(wrapped)], ["sentence-length"])

    def test_skip_frontmatter_fences_comments_and_headings(self):
        text = """---
description: Don't use this.
---
# Don't flag a heading.
Don't flag this title
====================
```python
Don't parse this code.
```
~~~text
Don't parse this code either.
~~~
<!-- Don't read
this text. -->
Check the input. <!-- Don't read this. -->
You don't continue.
"""
        findings = self.check(text)
        self.assertEqual([(f.code, f.line) for f in findings], [("contraction", 16)])

    def test_comments_on_both_sides_preserve_prose(self):
        findings = self.check("<!-- hidden -->Don't continue. <!-- hidden -->")
        self.assertEqual([f.code for f in findings], ["contraction"])

    def test_wrapped_setext_heading_is_skipped_as_a_whole(self):
        text = "Don't read " + "word " * 21 + "\nsecond title line\n=================\n\nCheck the input."
        self.assertEqual(self.check(text), [])

    def test_comment_markers_in_code_do_not_hide_following_prose(self):
        text = "```html\n<!--\n```\nDon't continue.\n\nUse `<!--` here. Don't continue."
        findings = self.check(text)
        self.assertEqual([(f.code, f.line) for f in findings], [("contraction", 4), ("contraction", 6)])

    def test_inline_code_is_one_token_and_kept_in_excerpt(self):
        text = "word " * 20 + "`Don't change the version 2.3.4 or is tested` ."
        findings = self.check(text)
        self.assertEqual([f.code for f in findings], ["sentence-length"])
        self.assertIn("21 words", findings[0].message)
        self.assertIn("`Don't change", findings[0].excerpt)

    def test_link_labels_count_and_destinations_do_not(self):
        text = "word " * 19 + "[two words](https://example.com/a_(page))."
        findings = self.check(text)
        self.assertEqual(len(findings), 1)
        self.assertIn("21 words", findings[0].message)
        self.assertNotIn("https", findings[0].excerpt)
        self.assertEqual(self.check("Read [these instructions][ref].\n\n[ref]: https://example.com/don't"), [])

    def test_tables_check_cells_separately_and_report_row_line(self):
        text = "| Action | Result |\n| --- | --- |\n| " + "word " * 15 + " | " + "word " * 15 + " |\n| Don't continue. | Stop. |"
        findings = self.check(text)
        self.assertEqual([(f.code, f.line) for f in findings], [("contraction", 4)])
        self.assertEqual(self.check("| `Don't | continue` | Stop. |"), [])

    def test_inline_code_pipe_does_not_break_wrapped_sentence(self):
        text = "word " * 11 + "`cat input | head`\n" + "word " * 10 + "."
        findings = self.check(text)
        self.assertEqual([(f.code, f.line) for f in findings], [("sentence-length", 1)])
        self.assertIn("22 words", findings[0].message)
        self.assertIn("`cat input | head`", findings[0].excerpt)

    def test_escaped_pipe_does_not_break_wrapped_sentence(self):
        text = "word " * 11 + "\\|\n" + "word " * 10 + "."
        findings = self.check(text)
        self.assertEqual([(f.code, f.line) for f in findings], [("sentence-length", 1)])
        self.assertIn("21 words", findings[0].message)

    def test_decimals_versions_and_abbreviations_do_not_end_sentences(self):
        text = "Set version 1.2.3 to 2.5 units and " + "word " * 14 + "."
        findings = self.check(text)
        self.assertEqual([f.code for f in findings], ["sentence-length"])
        self.assertIn("21 words", findings[0].message)
        self.assertEqual(self.check("For example, use a value, e.g. 2.5. Stop."), [])

    def test_url_at_sentence_end_does_not_join_two_sentences(self):
        text = "word " * 14 + "https://example.com. " + "word " * 14 + "."
        self.assertEqual(self.check(text), [])

    def test_contractions_but_not_ordinary_possessives(self):
        self.assertEqual(self.check("The operator's tool is ready. Check the customer's instructions."), [])
        findings = self.check("Don't proceed. We’re ready. It's open. Let's stop.")
        self.assertEqual([f.code for f in findings], ["contraction"] * 4)

    def test_passive_is_an_explicit_guess(self):
        findings = self.check("The cover is removed. The value was not correctly set.")
        self.assertEqual([f.code for f in findings], ["possible-passive"] * 2)
        self.assertTrue(all("Possible" in f.message and "adjective" in f.message for f in findings))
        self.assertEqual(self.check("Remove the cover. Set the value. The indicator is red."), [])

    def test_second_sentence_on_wrapped_line_has_correct_source_line(self):
        findings = self.check("Check the input.\nThe cover is removed.")
        self.assertEqual(findings[0].line, 2)

    def test_unsupported_mode_is_not_silently_accepted(self):
        with self.assertRaises(ValueError):
            self.check("Check the input.", "other")


class CommandLineChecks(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], text=True, capture_output=True, check=False)

    def test_clean_result_keeps_noncompliance_notice_and_file_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "clean.md"
            source = b"Open the cover.\n"
            path.write_bytes(source)
            result = self.run_cli("--json", path)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertIn("NOT a full ASD-STE100", report["notice"])
            self.assertIn("No findings does not establish conformance", report["notice"])
            self.assertEqual(report["findings"], [])
            self.assertEqual(path.read_bytes(), source)

    def test_candidate_exit_and_multiple_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.md"
            second = Path(directory) / "second.md"
            first.write_text("Open the cover.", encoding="utf-8")
            second.write_text("Don't continue.", encoding="utf-8")
            result = self.run_cli("--json", first, second)
            self.assertEqual(result.returncode, 1)
            report = json.loads(result.stdout)
            self.assertEqual(report["findings"][0]["path"], str(second))
            self.assertEqual(set(report["findings"][0]), {"path", "line", "code", "message", "excerpt"})

    def test_input_error_takes_priority_and_preserves_other_findings(self):
        with tempfile.TemporaryDirectory() as directory:
            good = Path(directory) / "candidate.md"
            good.write_text("Don't continue.", encoding="utf-8")
            result = self.run_cli("--json", good, Path(directory) / "missing.md")
            self.assertEqual(result.returncode, 2)
            report = json.loads(result.stdout)
            self.assertEqual(len(report["errors"]), 1)
            self.assertEqual(len(report["findings"]), 1)

    def test_directory_and_non_utf8_are_input_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / "bad.txt"
            bad.write_bytes(b"\xff\xfe")
            result = self.run_cli("--json", directory, bad)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(len(json.loads(result.stdout)["errors"]), 2)

    def test_help_documents_limits(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("not the standard's formal counting rules", result.stdout)
        self.assertIn("Passive-voice guesses", result.stdout)


if __name__ == "__main__":
    unittest.main()
