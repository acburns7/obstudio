"""Deterministic guards for compact skill entry points and reference routing."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / "skills"

# Budgets include frontmatter and allow modest maintenance headroom while keeping
# detailed algorithms and examples in references. They are intentionally
# per-skill because the implementation workflow is broader than a redirect stub.
SKILL_WORD_BUDGETS = {
    "otel-audit": 2400,
    "otel-instrument": 3200,
    "otel-verify": 1600,
    "splunk-configure": 1400,
    "splunk-dashboard": 1700,
    "splunk-dashboard-publish": 1700,
    "splunk-dashboard-sync": 150,
    "splunk-detector-publish": 1500,
    "splunk-sync": 150,
}

# Every canonical skill must point directly to the detailed contracts it needs.
# Paths are written exactly as they must appear in that skill's SKILL.md.
CORE_REFERENCE_ROUTES = {
    "otel-audit": (
        "references/source-discovery.md",
        "references/schema-v2-contract.md",
        "../references/report-flow-contract.md",
        "../references/incident-readiness.md",
        "../references/genai-readiness.md",
    ),
    "otel-instrument": (
        "../references/report-flow-contract.md",
        "./references/json-approval-handoff.md",
        "./references/project-runtime-validation.md",
        "./references/languages/",
        "./references/signal-mapping-guide.md",
        "./references/log-export-contract.md",
        "../references/incident-readiness.md",
        "../references/genai-readiness.md",
        "./references/readiness-implementation.md",
        "../references/full-runtime-acceptance.md",
    ),
    "otel-verify": (
        "../references/report-flow-contract.md",
        "./references/json-approval-handoff.md",
        "references/project-runtime-resolution.md",
        "references/path-scenario-coverage.md",
        "../references/full-runtime-acceptance.md",
        "references/app-code-test-authoring.md",
        "references/explorer-witness.md",
    ),
    "splunk-configure": (
        "../references/report-flow-contract.md",
        "../references/incident-readiness.md",
        "../references/genai-readiness.md",
        "references/input-and-validation-contract.md",
        "references/detector-classification.md",
        "references/terraform-templates.md",
    ),
    "splunk-dashboard": (
        "references/dashboard-classification.md",
        "references/dashboard-templates.md",
        "../references/signalflow-patterns.md",
        "../references/terraform-normalization.md",
    ),
    "splunk-dashboard-publish": (
        "../references/terraform-normalization.md",
        "../references/splunk-api.md",
        "../references/coverage-decision-tree.md",
        "references/dashboard-coverage-model.md",
        "../splunk-dashboard/references/dashboard-templates.md",
        "../references/ledger-template.md",
    ),
    "splunk-detector-publish": (
        "../references/terraform-normalization.md",
        "../references/splunk-api.md",
        "../references/coverage-decision-tree.md",
        "references/coverage-model.md",
        "../references/ledger-template.md",
    ),
}

DEPRECATED_ROUTES = {
    "splunk-dashboard-sync": "../splunk-dashboard-publish/SKILL.md",
    "splunk-sync": "../splunk-detector-publish/SKILL.md",
}

NEW_SPLIT_CONTRACTS = {
    "otel-audit": (
        "references/source-discovery.md",
        "references/schema-v2-contract.md",
    ),
    "otel-instrument": (
        "./references/readiness-implementation.md",
        "./references/log-export-contract.md",
    ),
    "splunk-configure": ("references/input-and-validation-contract.md",),
}


def _skill_path(skill_name: str) -> Path:
    return SKILLS_ROOT / skill_name / "SKILL.md"


def _read_skill(skill_name: str) -> str:
    path = _skill_path(skill_name)
    assert path.is_file(), f"missing skill entry point: {path}"
    return path.read_text(encoding="utf-8")


def test_every_top_level_skill_has_a_word_budget():
    discovered = {
        path.parent.name
        for path in SKILLS_ROOT.glob("*/SKILL.md")
        if path.is_file()
    }
    assert discovered == set(SKILL_WORD_BUDGETS), (
        "update SKILL_WORD_BUDGETS whenever a top-level skill is added or removed"
    )


def test_top_level_skills_stay_within_their_word_budgets():
    overruns = []
    for skill_name, budget in SKILL_WORD_BUDGETS.items():
        word_count = len(_read_skill(skill_name).split())
        if word_count > budget:
            overruns.append(f"{skill_name}: {word_count} > {budget}")

    assert not overruns, (
        "top-level SKILL.md exceeded its progressive-disclosure budget; move "
        "detailed algorithms or examples into a routed reference:\n"
        + "\n".join(overruns)
    )


def test_core_skills_route_directly_to_required_references():
    failures = []
    for skill_name, routes in CORE_REFERENCE_ROUTES.items():
        skill_path = _skill_path(skill_name)
        text = _read_skill(skill_name)
        for route in routes:
            target = (skill_path.parent / route).resolve()
            if route not in text:
                failures.append(f"{skill_name}: missing route {route}")
            elif not target.exists():
                failures.append(f"{skill_name}: route does not resolve: {route}")

    assert not failures, "broken progressive-disclosure routes:\n" + "\n".join(failures)


def test_new_split_contracts_remain_explicit_entry_point_routes():
    for skill_name, routes in NEW_SPLIT_CONTRACTS.items():
        text = _read_skill(skill_name)
        for route in routes:
            assert route in text, (
                f"{skill_name} must route directly to its split contract {route}"
            )


def test_deprecated_stubs_route_to_compact_canonical_skills():
    for skill_name, route in DEPRECATED_ROUTES.items():
        skill_path = _skill_path(skill_name)
        text = _read_skill(skill_name)
        target = (skill_path.parent / route).resolve()
        assert route in text, f"{skill_name} must route to {route}"
        assert target.is_file(), f"{skill_name} canonical route is missing: {target}"
