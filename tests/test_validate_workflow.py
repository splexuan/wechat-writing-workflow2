from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import validate_workflow


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ValidateWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory(
            prefix="wechat-writing-validator-test-"
        )
        self.root = Path(self.temporary_directory.name)
        shutil.copytree(PROJECT_ROOT / "wechat-writing", self.root / "wechat-writing")
        (self.root / "evals").mkdir()
        shutil.copy2(PROJECT_ROOT / "evals" / "cases.json", self.root / "evals")
        shutil.copy2(PROJECT_ROOT / "README.md", self.root / "README.md")
        shutil.copy2(PROJECT_ROOT / "LICENSE", self.root / "LICENSE")

        self.original_paths = (
            validate_workflow.ROOT,
            validate_workflow.SKILL_DIR,
            validate_workflow.CASES_FILE,
        )
        validate_workflow.ROOT = self.root
        validate_workflow.SKILL_DIR = self.root / "wechat-writing"
        validate_workflow.CASES_FILE = self.root / "evals" / "cases.json"

    def tearDown(self) -> None:
        (
            validate_workflow.ROOT,
            validate_workflow.SKILL_DIR,
            validate_workflow.CASES_FILE,
        ) = self.original_paths
        self.temporary_directory.cleanup()

    def test_current_package_passes_all_checks(self) -> None:
        validate_workflow.validate_required_files()
        validate_workflow.validate_frontmatter()
        self.assertGreater(validate_workflow.validate_markdown_links(), 0)
        validate_workflow.validate_workspace_contract()
        validate_workflow.validate_routing_contract()
        self.assertGreaterEqual(validate_workflow.validate_cases(), 10)

    def test_missing_packaged_asset_is_rejected(self) -> None:
        asset = (
            validate_workflow.SKILL_DIR
            / "assets"
            / "author-profile.template.md"
        )
        asset.unlink()
        with self.assertRaisesRegex(AssertionError, "missing required files"):
            validate_workflow.validate_required_files()

    def test_broken_or_external_markdown_link_is_rejected(self) -> None:
        skill = validate_workflow.SKILL_DIR / "SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8") + "\n[bad](../../outside.md)\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(AssertionError, "broken markdown links"):
            validate_workflow.validate_markdown_links()

    def test_missing_evaluation_reference_is_rejected(self) -> None:
        data = json.loads(validate_workflow.CASES_FILE.read_text(encoding="utf-8"))
        data["scenarios"][0]["expected_refs"] = ["references/missing.md"]
        validate_workflow.CASES_FILE.write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )
        with self.assertRaisesRegex(AssertionError, "references missing file"):
            validate_workflow.validate_cases()

    def test_fact_check_route_cannot_drop_research(self) -> None:
        skill = validate_workflow.SKILL_DIR / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        text = text.replace("[研究与证据](references/research.md) → ", "")
        skill.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(AssertionError, "要求事实检查"):
            validate_workflow.validate_routing_contract()


if __name__ == "__main__":
    unittest.main()
