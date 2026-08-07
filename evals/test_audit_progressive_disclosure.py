import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "otel-audit" / "SKILL.md"
REPORT_FLOW = ROOT / "skills" / "references" / "report-flow-contract.md"
SCHEMA_V2 = ROOT / "skills" / "otel-audit" / "references" / "schema-v2-contract.md"


def normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_audit_routes_to_the_schema_v2_authoring_contract() -> None:
    skill = normalized(SKILL)
    assert "references/schema-v2-contract.md" in skill
    assert "Before authoring .observe/otel-audit.json" in skill.replace("`", "")
    assert SCHEMA_V2.is_file()


def test_schema_v2_reference_keeps_machine_authoring_deterministic() -> None:
    source = SCHEMA_V2.read_text(encoding="utf-8")
    contract = " ".join(source.split())
    match = re.search(r"```json\n(.*?)\n```", source, re.DOTALL)
    assert match, "schema-v2 reference must include a parseable canonical example"
    example = json.loads(match.group(1))

    assert example["schema_version"] == 2
    assert example["kind"] == "otel-audit"
    assert set(example) >= {
        "meta",
        "signal_flow",
        "current_instrumentation",
        "findings",
        "verification",
    }
    finding = example["findings"][0]
    assert set(finding) >= {
        "id",
        "area",
        "priority",
        "required_fix",
        "instrument_mode",
        "verification_scenarios",
        "dependencies",
        "expected_telemetry",
    }
    assert example["verification"]["environments"]
    assert example["verification"]["scenarios"]

    for term in (
        "signal_flow.component_flow_map",
        "Every finding contains all of these fields",
        "Keep dependencies acyclic",
        "requested_ids",
        "approved_ids",
        "decision_answers",
        "Every scenario environment ID must exist",
        "Every finding verification_scenarios ID must exist",
    ):
        assert term.replace("`", "") in contract.replace("`", "")


def test_audit_renderer_owns_the_canonical_reader_projection() -> None:
    skill = normalized(SKILL)

    for term in (
        ".observe/otel-audit.json",
        ".observe/otel.html",
        "canonical machine-readable audit source",
        "self-contained human review report",
        "Write two audit artifacts",
        "finalize-audit",
        "--html .observe/otel.html",
        "turns exact existing repository-relative citations into local file links",
        "Review report: [otel.html](http://127.0.0.1:<port>/<token>/otel.html)",
    ):
        assert term.replace("`", "") in skill.replace("`", "")


def test_audit_human_report_is_one_priority_ordered_decision_view() -> None:
    skill = normalized(SKILL)
    flow = normalized(REPORT_FLOW)

    for text in (skill, flow):
        for term in (
            "exactly one findings list ordered by",
            "Priority defines ordering only",
            "Findings · N",
            "Each card has one title, one expected monitoring outcome",
            "only the plain selectable terminal command section",
            "Do not render a selection-count summary",
            "do not expose browser save or download controls",
            "$otel-instrument --ids OTEL-001,OTEL-002 --decision OTEL-003=option-id",
            "normally finalized report must never show the literal <service-root> placeholder",
        ):
            assert term.replace("`", "") in text.replace("`", "")


def test_audit_finding_cards_keep_technical_detail_collapsed() -> None:
    skill = normalized(SKILL)
    flow = normalized(REPORT_FLOW)

    for text in (skill, flow):
        for term in (
            "expanded narrative decision-sized",
            "Gap, Why it matters, a mode-aware required action, and Next step",
            "Instrumentation change for executable work",
            "Decision needed for a manual prerequisite",
            "External requirement for an external prerequisite",
            "one collapsed Technical details disclosure",
            "Do not render raw verification-scenario IDs",
            "Those fields remain in canonical JSON",
        ):
            assert term.replace("`", "") in text.replace("`", "")


def test_audit_selection_handoff_preserves_explicit_user_intent() -> None:
    skill = normalized(SKILL)
    flow = normalized(REPORT_FLOW)

    for text in (skill, flow):
        for term in (
            "neutral Select checkbox",
            "requested_ids",
            "approved_ids",
            "decision_answers",
            "Use explicit requested IDs",
            "dependency-closed executable selection",
            "review_selection",
            ".observe/otel-selection.json",
        ):
            assert term.replace("`", "") in text.replace("`", "")


def test_audit_does_not_promote_context_or_mutually_exclusive_branches_to_findings() -> None:
    skill = normalized(SKILL)
    flow = normalized(REPORT_FLOW)

    for text in (skill, flow):
        for term in (
            "Do not create manual or external findings just to record product/runtime choices",
            "billing, cost, safety policy, content-governance, or external business context",
            "create one option-locked executable finding per real branch",
            "Do not use one shared executable finding for multiple exclusive options",
            "two branch implementations appear as simultaneous independent audit gaps",
        ):
            assert term.replace("`", "") in text.replace("`", "")

    for term in (
        "Readiness rows are audit context first",
        "Promote a missing or partial readiness surface",
        "only when the repository owns a concrete OTel closure gap",
        "Do not promote service behavior choices, health endpoint semantics, readiness/liveness contracts",
        "put each branch ID in only that option's unlocks",
    ):
        assert term.replace("`", "") in skill.replace("`", "")
