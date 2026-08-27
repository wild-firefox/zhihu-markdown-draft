#!/usr/bin/env python3
"""Focused regression tests for Zhihu compatibility warnings."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("prepare_zhihu_markdown.py")
SPEC = importlib.util.spec_from_file_location("prepare_zhihu_markdown", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class PrepareZhihuMarkdownTests(unittest.TestCase):
    def prepare(self, markdown: str) -> dict:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.md"
            output = root / "output.md"
            report = root / "report.json"
            source.write_text(markdown, encoding="utf-8")
            return MODULE.prepare(source, output, report, strip_first_h1=True)

    def categories(self, markdown: str) -> list[str]:
        report = self.prepare(markdown)
        return [item["category"] for item in report["compatibility_warnings"]]

    def test_currency_dollar_is_blocking(self) -> None:
        report = self.prepare("# Title\n\nPrice is $100.\n")
        self.assertIn(
            "currency-dollar",
            [item["category"] for item in report["blocking_compatibility_warnings"]],
        )

    def test_complete_formula_is_not_blocking(self) -> None:
        report = self.prepare("# Title\n\nFormula: $E=mc^2$.\n")
        self.assertEqual([], report["blocking_compatibility_warnings"])

    def test_fenced_code_masks_dollars_and_markdown(self) -> None:
        report = self.prepare("# Title\n\n```python\nprice = '$100'\n```\n")
        self.assertEqual([], report["compatibility_warnings"])

    def test_nested_list_is_not_indented_code(self) -> None:
        categories = self.categories("# Title\n\n- one\n    - two\n")
        self.assertNotIn("indented-code", categories)

    def test_actual_indented_code_is_blocking(self) -> None:
        report = self.prepare("# Title\n\n    price = $100\n")
        categories = [
            item["category"] for item in report["blocking_compatibility_warnings"]
        ]
        self.assertIn("indented-code", categories)

    def test_underscore_identifier_is_not_italic(self) -> None:
        categories = self.categories("# Title\n\nrisk_parity_position_sizing\n")
        self.assertNotIn("single-underscore-italic", categories)

    def test_deep_heading_and_task_list_are_reported(self) -> None:
        categories = self.categories("# Title\n\n### Deep\n\n- [x] done\n")
        self.assertIn("deep-heading", categories)
        self.assertIn("task-list", categories)


if __name__ == "__main__":
    unittest.main()
