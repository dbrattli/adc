"""Exercise the extraction boundary and real compiler diagnostics."""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEAN = os.environ.get("LEAN") or shutil.which("lean")


class LeanifyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="adc-leanify-test-")
        self.addCleanup(self.directory.cleanup)
        self.source = Path(self.directory.name) / "Example.fsx"
        self.output = Path(self.directory.name) / "Example.lean"

    def leanify(self, text, check=False):
        self.source.write_text(text, encoding="utf-8")
        command = [
            sys.executable,
            str(HERE / "leanify.py"),
            str(self.source),
            str(self.output),
        ]
        if check:
            command.append("--check")
        return subprocess.run(
            command, capture_output=True, text=True, cwd=HERE, timeout=30, check=False
        )

    def test_preserves_lines_and_copies_lean_verbatim(self):
        source = "(**\n```lean\nnamespace Demo\n```\n*)\nlet x = 1\n"
        source += "(**\n```lean\ndef α : Nat := 1\nend Demo\n```\n*)\n"
        result = self.leanify(source)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        expected = ["-- " + line for line in source.splitlines()]
        for index in [2, 8, 9]:
            expected[index] = source.splitlines()[index]
        self.assertEqual(self.output.read_text().splitlines(), expected)

    def test_ignores_fake_blocks_inside_multiline_strings(self):
        source = 'let text = """\n(**\n```lean\nINVALID\n```\n*)\n"""\n'
        source += "(**\n```lean\ndef real : Nat := 1\n```\n*)\n"
        result = self.leanify(source)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("-- INVALID", self.output.read_text())
        self.assertIn("\ndef real : Nat := 1\n", self.output.read_text())

    def test_rejects_missing_blocks(self):
        result = self.leanify('let text = "```lean"\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No Lean blocks found", result.stderr)
        self.assertFalse(self.output.exists())

    def test_rejects_empty_block(self):
        result = self.leanify("(**\n```lean\n   \n```\n*)\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Empty Lean block", result.stderr)

    def test_rejects_unclosed_block(self):
        result = self.leanify("(**\n```lean\ndef value : Nat := 1\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unclosed Lean block", result.stderr)

    def test_rejects_fsharp_code_inside_unclosed_block(self):
        result = self.leanify("(**\n```lean\ndef value : Nat := 1\n*)\nlet x = 1\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("leaves its host comment", result.stderr)

    def test_rejects_nested_fence(self):
        result = self.leanify("(**\n```lean\n```lean\ndef value : Nat := 1\n```\n*)\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unexpected fence", result.stderr)

    def test_extracts_raw_and_backtick_inline_statements(self):
        source = "// lean: namespace Demo\n"
        source += "    /// lean: `def NonEmpty (xs : List α) : Prop := xs ≠ []`\n"
        source += "// lean: `end Demo`\n"
        result = self.leanify(source)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.output.read_text().splitlines(),
            [
                "namespace Demo",
                "def NonEmpty (xs : List α) : Prop := xs ≠ []",
                "end Demo",
            ],
        )

    def test_ignores_inline_markers_inside_strings(self):
        source = 'let text = """\n/// lean: `INVALID`\n"""\n'
        source += "// lean: `def value : Nat := 1`\n"
        result = self.leanify(source)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("-- /// lean: `INVALID`", self.output.read_text())

    def test_rejects_empty_inline_statements(self):
        for text in ["// lean: ", "/// lean: ``", "/// lean: `   `"]:
            with self.subTest(text=text):
                result = self.leanify(text + "\n")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Empty lean: comment", result.stderr)

    def test_rejects_unclosed_inline_code_span(self):
        result = self.leanify("/// lean: `def value : Nat := 1\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unclosed inline Lean code span", result.stderr)

    def test_rejects_internal_backticks_in_code_span(self):
        result = self.leanify("/// lean: ``def value : Nat := 1``\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Use a fenced Lean block", result.stderr)

    @unittest.skipUnless(LEAN, "Set LEAN or install Lean for compiler checks")
    def test_compiles_inline_contract_without_proof(self):
        result = self.leanify(
            "/// lean: `def NonEmpty (xs : List α) : Prop := xs ≠ []`\n", check=True
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(LEAN, "Set LEAN or install Lean for compiler checks")
    def test_restores_inline_comment_and_backtick_column_offset(self):
        prefix = "    /// lean: `"
        result = self.leanify(prefix + 'def α : Nat := "wrong"`\n', check=True)
        self.assertNotEqual(result.returncode, 0)
        raw = subprocess.run(
            [LEAN, str(self.output)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        location = re.search(
            re.escape(str(self.output)) + r":1:(\d+):", raw.stdout + raw.stderr
        )
        self.assertIsNotNone(location, raw.stdout + raw.stderr)
        expected_column = int(location.group(1)) + len(prefix)
        self.assertIn(
            f"{self.source}:1:{expected_column}:", result.stdout + result.stderr
        )

    def test_preserves_relative_layout_at_different_host_depths(self):
        source = "module Outer =\n    (**\n    ```lean\n"
        source += "    def first (n : Nat) : Nat :=\n      match n with\n"
        source += "      | 0 => 1\n      | n + 1 => n\n\n    ```\n    *)\n"
        source += "    module Inner =\n        (**\n        ```lean\n"
        source += "        example : first 0 = 1 := by\n          rfl\n"
        source += "        ```\n        *)\n"
        result = self.leanify(source)
        self.assertEqual(result.returncode, 0, result.stderr)
        generated = self.output.read_text()
        self.assertEqual(len(generated.splitlines()), len(source.splitlines()))
        self.assertIn(
            "def first (n : Nat) : Nat :=\n  match n with\n  | 0 => 1\n", generated
        )
        self.assertIn("example : first 0 = 1 := by\n  rfl\n", generated)

    def test_rejects_content_outside_fence_indentation(self):
        result = self.leanify("(**\n    ```lean\n  def value : Nat := 1\n    ```\n*)\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("content must include", result.stderr)

    def test_rejects_misaligned_closing_fence(self):
        result = self.leanify("(**\n    ```lean\n    def value : Nat := 1\n```\n*)\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Closing fence must match", result.stderr)

    def test_rejects_tabs_in_host_indentation(self):
        result = self.leanify("(**\n\t```lean\n\tdef value : Nat := 1\n\t```\n*)\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("indentation must use spaces", result.stderr)

    @unittest.skipUnless(LEAN, "Set LEAN or install Lean for compiler checks")
    def test_compiles_indented_block(self):
        result = self.leanify(
            "module Outer =\n    (**\n    ```lean\n"
            "    theorem valid : True := by\n      trivial\n"
            "    ```\n    *)\n    let x = 1\n",
            check=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(LEAN, "Set LEAN or install Lean for compiler checks")
    def test_restores_diagnostic_columns_for_indented_unicode_source(self):
        result = self.leanify(
            "module Outer =\n    (**\n    ```lean\n"
            '    def α : Nat := "wrong"\n    ```\n    *)\n',
            check=True,
        )
        self.assertNotEqual(result.returncode, 0)
        raw = subprocess.run(
            [LEAN, str(self.output)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        location = re.search(
            re.escape(str(self.output)) + r":4:(\d+):", raw.stdout + raw.stderr
        )
        self.assertIsNotNone(location, raw.stdout + raw.stderr)
        expected_column = int(location.group(1)) + 4
        self.assertIn(
            f"{self.source}:4:{expected_column}:", result.stdout + result.stderr
        )

    @unittest.skipUnless(LEAN, "Set LEAN or install Lean for compiler checks")
    def test_maps_lean_error_to_original_source(self):
        result = self.leanify(
            '(**\n```lean\ndef broken : Nat := "wrong"\n```\n*)\n', check=True
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"{self.source}:3:", result.stdout + result.stderr)
        self.assertNotIn(f"{self.output}:3:", result.stdout + result.stderr)

    @unittest.skipUnless(LEAN, "Set LEAN or install Lean for compiler checks")
    def test_fails_on_unfinished_proof_warning(self):
        result = self.leanify(
            "(**\n```lean\ntheorem unfinished : True := by sorry\n```\n*)\n", check=True
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sorry", result.stdout + result.stderr)

    def test_python_comments_ignore_strings_and_docstrings(self):
        self.source = self.source.with_suffix(".py")
        result = self.leanify(
            '"""\n# lean: `INVALID`\n"""\n'
            "# lean: `def value : Nat := 1`\n"
            'text = "# lean: INVALID"\n'
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("-- # lean: `INVALID`", self.output.read_text())
        self.assertIn("\ndef value : Nat := 1\n", self.output.read_text())

    def test_python_indented_comment(self):
        self.source = self.source.with_suffix(".py")
        result = self.leanify(
            "def f():\n    # lean: `def value : Nat := 1`\n    pass\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.output.read_text().splitlines()[1], "def value : Nat := 1"
        )

    def test_ignores_verbatim_strings_and_nested_comments(self):
        result = self.leanify(
            'let text = @"\n/// lean: INVALID\n"\n'
            "(* outer (* nested *) // text *)\n"
            "// lean: `def value : Nat := 1`\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("-- /// lean: INVALID", self.output.read_text())

    def test_rejects_interpolation_without_overwriting_output(self):
        self.output.write_text("previous")
        for prefix in ['$"', '$"""', '$@"', '@$"', '$$"""']:
            with self.subTest(prefix=prefix):
                result = self.leanify(
                    "let text = " + prefix + 'text"\n// lean: def x := 1\n'
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("interpolated strings", result.stderr)
                self.assertEqual(self.output.read_text(), "previous")

    def test_rejects_unclosed_string(self):
        result = self.leanify('let text = "unclosed\n// lean: def x := 1\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unclosed F# string", result.stderr)

    def test_rejects_unsupported_extension(self):
        self.source = self.source.with_suffix(".txt")
        result = self.leanify("// lean: def x := 1\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())

    def test_crlf_and_utf8_bom(self):
        result = self.leanify("\ufeff// lean: `def α : Nat := 1`\r\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output.read_text(), "def α : Nat := 1\n")

    def test_rust_inline_doc_comments(self):
        self.source = self.source.with_suffix(".rs")
        result = self.leanify(
            "//! lean: `namespace Demo`\n"
            "/// lean: `def NonEmpty (xs : List α) : Prop := xs ≠ []`\n"
            "// lean: `end Demo`\n"
            "fn main() {}\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output.read_text().splitlines()[0], "namespace Demo")
        self.assertIn("def NonEmpty", self.output.read_text())

    def test_rust_raw_string_delimiters(self):
        self.source = self.source.with_suffix(".rs")
        for prefix in ["r", "br", "cr"]:
            for hashes in ["", "#", "###"]:
                with self.subTest(prefix=prefix, hashes=hashes):
                    quoted = prefix + hashes + '"\n/// lean: INVALID\n"' + hashes
                    result = self.leanify(
                        "let text = " + quoted + ";\n// lean: `def value : Nat := 1`\n"
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("-- /// lean: INVALID", self.output.read_text())

    def test_rust_normal_and_byte_strings(self):
        self.source = self.source.with_suffix(".rs")
        for prefix in ["", "b", "c"]:
            with self.subTest(prefix=prefix):
                result = self.leanify(
                    "let text = " + prefix + '"\n/// lean: INVALID\n";\n'
                    "// lean: `def value : Nat := 1`\n"
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("-- /// lean: INVALID", self.output.read_text())

    def test_rust_characters_and_lifetimes(self):
        self.source = self.source.with_suffix(".rs")
        result = self.leanify(
            "fn borrow<'a>(x: &'a str) -> &'a str { x }\n"
            "let quote = '\"'; let slash = b'/';\n"
            "// lean: `def value : Nat := 1`\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("\ndef value : Nat := 1\n", self.output.read_text())

    def test_rust_nested_comments_and_indented_fence(self):
        self.source = self.source.with_suffix(".rs")
        result = self.leanify(
            "/** outer /* nested */\n"
            "    ```lean\n"
            "    def value : Nat :=\n"
            "      1\n"
            "    ```\n"
            "*/\nfn main() {}\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("def value : Nat :=\n  1\n", self.output.read_text())

    def test_rust_rejects_unclosed_raw_string(self):
        self.source = self.source.with_suffix(".rs")
        result = self.leanify('let text = r##"\n// lean: INVALID\n"#;\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unclosed Rust raw string", result.stderr)
        self.assertFalse(self.output.exists())

    @unittest.skipUnless(LEAN, "Set LEAN or install Lean for compiler checks")
    def test_rust_compiles_indented_model(self):
        self.source = self.source.with_suffix(".rs")
        result = self.leanify(
            "mod batch {\n"
            "    /// lean: `def Batch (α : Type) := { xs : List α // xs ≠ [] }`\n"
            "    struct Batch<T> { head: T, tail: Vec<T> }\n"
            "}\n",
            check=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
