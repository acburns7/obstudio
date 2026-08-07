"""Regression guards for the instrument OTLP application-log contract."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "otel-instrument" / "SKILL.md"
LOG_CONTRACT = (
    ROOT
    / "skills"
    / "otel-instrument"
    / "references"
    / "log-export-contract.md"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _squash(path: Path) -> str:
    return " ".join(_read(path).split())


def test_instrument_routes_every_selected_log_change_to_local_contract() -> None:
    skill = _squash(SKILL)

    assert (
        "Any validated selected application-log change, including correlation-only, "
        "OTLP export, or an OTLP bridge"
    ) in skill
    assert "add export components only for selected OTLP work" in skill
    assert "./references/log-export-contract.md" in skill
    assert LOG_CONTRACT.is_file()


def test_log_export_contract_preserves_scope_and_pipeline_risk_guards() -> None:
    contract = _squash(LOG_CONTRACT)

    for term in (
        "every validated selected application-log change",
        "`correlation-only`:",
        "`otlp`:",
        "`not requested`:",
        "Never add an OTLP log bridge for unselected work",
        "Stdout correlation is not OTLP log export",
        "privacy, cost, and duplicate-ingestion risks",
        "formatter field",
        "logging adapter",
        "MDC or context variable",
        "framework access-log formatter",
        "exception renderer",
        "final pipeline privacy and correlation checks",
    ):
        assert term in contract


def test_log_export_contract_requires_direct_record_proof() -> None:
    contract = _squash(LOG_CONTRACT)

    for property_name in (
        "| Body |",
        "| Category |",
        "| Severity |",
        "| Correlation |",
        "| Redaction |",
        "| Resource identity |",
        "| OTLP visibility |",
    ):
        assert property_name in contract

    for term in (
        "Direct proof must establish every applicable property",
        "stdout alone is not visibility proof",
        "does not create duplicate backend records",
        "Use `Not configured`",
        "Do not downgrade this to `Not proven`",
    ):
        assert term in contract
