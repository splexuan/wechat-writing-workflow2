#!/usr/bin/env python3
"""Validate the writing skill package and its behavior-case definitions."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "wechat-writing"
CASES_FILE = ROOT / "evals" / "cases.json"


def fail(message: str) -> None:
    raise AssertionError(message)


def validate_required_files() -> None:
    required = [
        SKILL_DIR / "SKILL.md",
        SKILL_DIR / "agents" / "openai.yaml",
        SKILL_DIR / "references" / "workspace.md",
        SKILL_DIR / "assets" / "author-profile.template.md",
        SKILL_DIR / "assets" / "style-lessons.template.md",
        SKILL_DIR / "assets" / "article-brief.template.md",
        ROOT / "docs" / "wechat-writing-skill-workflow.png",
        CASES_FILE,
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        fail(f"missing required files: {', '.join(missing)}")


def validate_frontmatter() -> None:
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        fail("SKILL.md has no valid frontmatter block")
    frontmatter = match.group(1)
    if not re.search(r"(?m)^name:\s*wechat-writing\s*$", frontmatter):
        fail("SKILL.md name must be wechat-writing")
    description = re.search(r"(?m)^description:\s*(.+)$", frontmatter)
    if not description or len(description.group(1).strip()) < 20:
        fail("SKILL.md description is missing or not discriminating")


def validate_markdown_links() -> int:
    markdown_files = list(SKILL_DIR.rglob("*.md")) + [ROOT / "README.md"]
    broken: list[str] = []
    checked = 0
    for source in markdown_files:
        text = source.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            checked += 1
            relative_target = target.split("#", 1)[0]
            resolved = (source.parent / relative_target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                broken.append(f"{source.relative_to(ROOT)} -> outside repository: {target}")
                continue
            if not resolved.exists():
                broken.append(f"{source.relative_to(ROOT)} -> {target}")
    if broken:
        fail("broken markdown links:\n" + "\n".join(broken))
    return checked


def validate_workspace_contract() -> None:
    package_text = "\n".join(
        path.read_text(encoding="utf-8") for path in SKILL_DIR.rglob("*.md")
    )
    legacy_paths = [
        "workspace/author-profile.example.md",
        "workspace/style-lessons.example.md",
    ]
    found = [path for path in legacy_paths if path in package_text]
    if found:
        fail(f"legacy external template references remain: {', '.join(found)}")
    required_phrases = [
        "assets/author-profile.template.md",
        "assets/style-lessons.template.md",
        "active-article.md",
        "current: draft.md",
        "不要根据 `SKILL.md` 所在位置推断用户工作区",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in package_text]
    if missing:
        fail(f"workspace contract is incomplete: {', '.join(missing)}")


def validate_routing_contract() -> None:
    skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    lines = skill_text.splitlines()

    def route_line(marker: str) -> str:
        matches = [line for line in lines if marker in line]
        if len(matches) != 1:
            fail(f"expected exactly one routing rule for: {marker}")
        return matches[0]

    contracts = [
        ("明确要求直接成稿，但尚未确认中心主题", ["references/ideation.md"]),
        ("用户已经明确确认最终中心主题", ["references/drafting.md", "references/natural-editing.md", "references/review.md"]),
        ("事实密集、时效性强或高风险文章", ["references/research.md", "references/argument.md", "references/drafting.md", "references/natural-editing.md", "references/review.md"]),
        ("要求事实检查", ["references/research.md", "references/review.md"]),
        ("继续上次文章", ["references/workspace.md"]),
        ("学习作者风格", ["references/style-learning.md", "references/workspace.md"]),
    ]
    for marker, references in contracts:
        line = route_line(marker)
        missing = [reference for reference in references if reference not in line]
        if missing:
            fail(f"routing rule '{marker}' is missing: {', '.join(missing)}")

    topic_gate_phrases = [
        "给出新主题、事件、现象、链接或研究问题，但尚未给出中心判断",
        "问题即使很具体",
        "等待用户选择",
        "选中方向只代表选择探索路线",
        "等待明确确认",
    ]
    missing_gate_phrases = [
        phrase for phrase in topic_gate_phrases if phrase not in skill_text
    ]
    if missing_gate_phrases:
        fail(f"topic gate is incomplete: {', '.join(missing_gate_phrases)}")

    ideation = (SKILL_DIR / "references" / "ideation.md").read_text(encoding="utf-8")
    ideation_phrases = [
        "问题再具体，也不等于已经有选题",
        "展示方向卡和推荐后停止",
        "质疑或重构原前提",
        "切换到不同参与者或分析层级",
        "讨论并确认中心主题",
        "中心主题确认前",
    ]
    missing_ideation_phrases = [
        phrase for phrase in ideation_phrases if phrase not in ideation
    ]
    if missing_ideation_phrases:
        fail(f"ideation gate is incomplete: {', '.join(missing_ideation_phrases)}")

    workflow_phrases = [
        "最小 brief",
        "自然化与精简",
        "重要机制和关键反方讲透",
        "默认只交付成稿",
    ]
    missing_workflow_phrases = [
        phrase for phrase in workflow_phrases if phrase not in skill_text
    ]
    if missing_workflow_phrases:
        fail(f"completion workflow is incomplete: {', '.join(missing_workflow_phrases)}")

    drafting = (SKILL_DIR / "references" / "drafting.md").read_text(encoding="utf-8")
    drafting_phrases = [
        "所有新生成的完整初稿和全文改稿",
        "先转入 [自然化编辑](natural-editing.md)",
        "按重要性分配解释量",
    ]
    missing_drafting_phrases = [
        phrase for phrase in drafting_phrases if phrase not in drafting
    ]
    if missing_drafting_phrases:
        fail(f"drafting completion gate is incomplete: {', '.join(missing_drafting_phrases)}")

    argument = (SKILL_DIR / "references" / "argument.md").read_text(encoding="utf-8")
    argument_phrases = [
        "同层比较",
        "一节一职",
        "去重合并",
        "旁枝止步",
        "结尾不加料",
    ]
    missing_argument_phrases = [
        phrase for phrase in argument_phrases if phrase not in argument
    ]
    if missing_argument_phrases:
        fail(f"outline gate is incomplete: {', '.join(missing_argument_phrases)}")

    natural_editing = (SKILL_DIR / "references" / "natural-editing.md").read_text(
        encoding="utf-8"
    )
    if "完整新稿和全文改稿必须执行一轮" not in natural_editing:
        fail("natural-editing pass must be mandatory for complete drafts")

    research = (SKILL_DIR / "references" / "research.md").read_text(encoding="utf-8")
    if "普通单轮请求可在当前任务上下文中维护" not in research:
        fail("single-turn research must support a non-persistent evidence ledger")
    if "研究必须发生在方向和最小 brief 确定之后" not in research:
        fail("research must follow the chosen direction and minimum brief")


def validate_cases() -> int:
    data = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail("evals/cases.json root must be an object")
    scenarios = data.get("scenarios")
    if data.get("version") != 1 or not isinstance(scenarios, list):
        fail("evals/cases.json must contain version 1 and a scenarios list")
    if len(scenarios) < 10:
        fail("at least 10 behavior scenarios are required")

    ids: set[str] = set()
    requests: set[str] = set()
    categories: set[str] = set()
    required_fields = {"id", "category", "request", "expected_refs", "must", "must_not"}
    for index, scenario in enumerate(scenarios, start=1):
        missing = required_fields - scenario.keys()
        if missing:
            fail(f"scenario {index} missing fields: {', '.join(sorted(missing))}")
        scenario_id = scenario["id"]
        request = scenario["request"]
        if scenario_id in ids or request in requests:
            fail(f"duplicate scenario id or request: {scenario_id}")
        ids.add(scenario_id)
        requests.add(request)
        categories.add(scenario["category"])
        for field in ("expected_refs", "must", "must_not"):
            value = scenario[field]
            if not isinstance(value, list) or not value or not all(
                isinstance(item, str) and item.strip() for item in value
            ):
                fail(f"scenario {scenario_id} has invalid {field}")
        for reference in scenario["expected_refs"]:
            if not (SKILL_DIR / reference).is_file():
                fail(f"scenario {scenario_id} references missing file: {reference}")

    expected_categories = {
        "theme-confirmation",
        "fact-check",
        "ideation",
        "hot-analysis",
        "tutorial",
        "local-edit",
        "deep-revision",
        "resume-single",
        "resume-ambiguous",
        "style-learning",
        "single-turn-research",
        "persisted-draft",
    }
    missing_categories = expected_categories - categories
    if missing_categories:
        fail(f"missing behavior categories: {', '.join(sorted(missing_categories))}")

    required_topic_gate_cases = {
        "specific-why-question-must-ideate": "references/ideation.md",
        "ordinary-write-request-still-ideates": "references/ideation.md",
        "explicit-thesis-direct-draft": "references/drafting.md",
        "broad-topic-direct-still-confirms-theme": "references/ideation.md",
        "selected-direction-needs-theme-discussion": "references/ideation.md",
        "theme-refinement-is-not-confirmation": "references/ideation.md",
        "explicit-theme-confirmation-unlocks-brief": "references/ideation.md",
    }
    scenarios_by_id = {scenario["id"]: scenario for scenario in scenarios}
    for scenario_id, required_reference in required_topic_gate_cases.items():
        scenario = scenarios_by_id.get(scenario_id)
        if scenario is None:
            fail(f"missing topic-gate behavior scenario: {scenario_id}")
        if required_reference not in scenario["expected_refs"]:
            fail(
                f"topic-gate scenario {scenario_id} must reference: "
                f"{required_reference}"
            )

    required_quality_cases = {
        "concise-complete-draft",
        "outline-structure-gate",
    }
    missing_quality_cases = required_quality_cases - scenarios_by_id.keys()
    if missing_quality_cases:
        fail(
            "missing writing-quality behavior scenarios: "
            + ", ".join(sorted(missing_quality_cases))
        )

    complete_draft_cases = {
        "explicit-thesis-direct-draft",
        "current-public-issue",
        "personal-tutorial",
        "deep-revision-and-naturalize",
        "single-turn-research-no-files",
        "persisted-multiturn-article",
        "concise-complete-draft",
        "outline-structure-gate",
    }
    for scenario_id in complete_draft_cases:
        scenario = scenarios_by_id.get(scenario_id)
        if scenario is None:
            fail(f"missing complete-draft behavior scenario: {scenario_id}")
        if "references/natural-editing.md" not in scenario["expected_refs"]:
            fail(f"complete-draft scenario must include natural editing: {scenario_id}")
    return len(scenarios)


def main() -> int:
    try:
        validate_required_files()
        validate_frontmatter()
        link_count = validate_markdown_links()
        validate_workspace_contract()
        validate_routing_contract()
        scenario_count = validate_cases()
    except (AssertionError, json.JSONDecodeError, KeyError, OSError, TypeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(
        "PASS: writing workflow validated "
        f"({scenario_count} behavior scenarios, {link_count} local markdown links)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
