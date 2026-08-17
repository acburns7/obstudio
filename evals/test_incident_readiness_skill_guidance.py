"""Deterministic checks for incident-readiness skill guidance."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
INCIDENT_REF = SKILLS_DIR / "references" / "incident-readiness.md"
REPORT_FLOW = SKILLS_DIR / "references" / "report-flow-contract.md"
FULL_RUNTIME = SKILLS_DIR / "references" / "full-runtime-acceptance.md"
OTEL_AUDIT = SKILLS_DIR / "otel-audit" / "SKILL.md"
OTEL_INSTRUMENT = SKILLS_DIR / "otel-instrument" / "SKILL.md"
INSTRUMENT_READINESS = (
    SKILLS_DIR / "otel-instrument" / "references" / "readiness-implementation.md"
)
SPLUNK_CONFIGURE = SKILLS_DIR / "splunk-configure" / "SKILL.md"
SPLUNK_CONFIGURE_REFS = SKILLS_DIR / "splunk-configure" / "references"


def _read_raw(path: Path) -> str:
    assert path.exists(), f"Expected file not found: {path}"
    return path.read_text()


def _read(path: Path) -> str:
    """Read the effective progressively disclosed contract for core skills."""
    text = _read_raw(path)
    references = {
        OTEL_AUDIT: [
            INCIDENT_REF,
            REPORT_FLOW,
            SKILLS_DIR / "otel-audit" / "references" / "source-discovery.md",
            SKILLS_DIR / "otel-audit" / "references" / "schema-v2-contract.md",
        ],
        OTEL_INSTRUMENT: [
            INCIDENT_REF,
            REPORT_FLOW,
            FULL_RUNTIME,
            SKILLS_DIR / "otel-instrument" / "references" / "json-approval-handoff.md",
            SKILLS_DIR / "otel-instrument" / "references" / "project-runtime-validation.md",
            INSTRUMENT_READINESS,
            *sorted((SKILLS_DIR / "otel-instrument" / "references" / "languages").glob("*.md")),
        ],
        SPLUNK_CONFIGURE: [
            INCIDENT_REF,
            SKILLS_DIR / "references" / "report-flow-contract.md",
            SPLUNK_CONFIGURE_REFS / "detector-classification.md",
            SPLUNK_CONFIGURE_REFS / "input-and-validation-contract.md",
            SPLUNK_CONFIGURE_REFS / "terraform-templates.md",
        ],
    }.get(path, [])
    return "\n".join([text, *(_read_raw(reference) for reference in references)])


def _squash(text: str) -> str:
    return " ".join(text.split())


def test_incident_reference_covers_generic_incident_patterns():
    text = _read(INCIDENT_REF)
    required_terms = [
        "API/workflow",
        "Customer impact",
        "Dependency",
        "Freshness",
        "Backpressure",
        "Auth/edge",
        "Capacity",
        "Release context",
        "detector group-by keys",
    ]
    missing = [term for term in required_terms if term not in text]
    assert not missing


def test_incident_reference_covers_generic_mttd_signal_checklist():
    text = _read(INCIDENT_REF)
    required_terms = [
        "service.version",
        "deployment.environment.name",
        "cloud.region",
        "cloud.platform",
        "container.image.name",
        "container.image.tags",
        "artifact version",
        "config version",
        "canary/rollout batch",
        "restart/crash-loop",
        "desired-vs-healthy",
        "startup/readiness/healthcheck",
        "CPU/memory/disk",
        "concurrency",
        "quota",
        "throttling",
        "endpoint health",
        "target health",
        "traffic target health",
        "Synthetic/canary workflow checks",
        "input size/complexity bucket",
        "metadata count when relevant",
        "offline/derived data",
        "schema/migration version when present",
        "fallback target readiness",
        "compatibility failure class",
    ]
    missing = [term for term in required_terms if term not in text]
    assert not missing


def test_incident_reference_prefers_current_resource_semconv_names():
    text = _squash(_read(INCIDENT_REF))
    assert "deployment.environment.name" in text
    assert "`deployment.environment`" in text
    assert "legacy or custom" in text
    assert "do not newly emit them" in text
    for standard_name in [
        "cloud.region",
        "cloud.platform",
        "container.image.name",
        "container.image.tags",
    ]:
        assert standard_name in text


def test_java_agent_example_uses_current_environment_attribute():
    java = _read(SKILLS_DIR / "otel-instrument" / "references" / "languages" / "java.md")
    assert "deployment.environment.name=production" in java
    assert "deployment.environment=production" not in java


def test_python_auto_instrumentation_example_uses_current_environment_attribute():
    python = _read(SKILLS_DIR / "otel-instrument" / "references" / "languages" / "python.md")
    assert "deployment.environment.name=production" in python
    assert "deployment.environment=production" not in python


def test_audit_and_instrument_load_incident_reference():
    audit = _read_raw(OTEL_AUDIT)
    instrument = _read_raw(OTEL_INSTRUMENT)
    assert "../references/incident-readiness.md" in audit
    assert "../references/incident-readiness.md" in instrument
    assert "incident detectability" in audit
    assert "Requests for faster incident detection/localization" in instrument
    assert "./references/readiness-implementation.md" in instrument


def test_instrument_allows_recommended_semconv_readiness_signals():
    instrument = _squash(_read(SKILLS_DIR / "otel-instrument" / "SKILL.md"))
    required_terms = [
        "recommended optional signals",
        "approved readiness or verification requirement",
        "service can observe the value accurately",
        "privacy/cardinality rules permit it",
    ]
    missing = [term for term in required_terms if term not in instrument]
    assert not missing


def test_instrument_requires_signal_level_mttd_role_inventory():
    instrument = _read(SKILLS_DIR / "otel-instrument" / "SKILL.md")
    report_contract = _read(SKILLS_DIR / "references" / "report-flow-contract.md")
    required_terms = [
        "### Incident Readiness Signal Roles",
        "| Surface | Exact signal | Role | Detector use / reason | Proof | Remaining owner / prerequisite |",
        "`MTTD-improving`",
        "`localization-only`",
        "`provider/platform-owned`",
        "`uncovered`",
        "one row per exact",
        "not another gap ledger",
    ]
    for text in (instrument, report_contract):
        squashed = _squash(text)
        missing = [term for term in required_terms if term not in squashed]
        assert not missing


def test_instrument_requires_multi_process_and_concurrency_proof():
    instrument = _read_raw(OTEL_INSTRUMENT)
    incident = _squash(_read_raw(INCIDENT_REF))
    required_terms = [
        "distinct, operator-overridable `service.name` default",
        "real entrypoint or startup hook",
        "must not initialize",
        "explicitly record failure outcome",
        "enqueue success/failure and worker task success/failure",
        "AST/source-string checks do not prove telemetry",
        "`go test -race`",
        "normal `go test` pass",
        "toolchain/platform blocker",
        "drive the underlying app state to a non-default value",
        "Instrument registration, metric-name presence, and zero-value gauge collection",
        "saturated or deterministic backpressure path",
        "nonzero depth and oldest-age values",
        "keep the verification result `Partial`",
    ]
    missing = [term for term in required_terms if term not in incident]
    assert not missing
    assert "../references/incident-readiness.md" in instrument
    assert "../references/full-runtime-acceptance.md" in instrument


def test_incident_freshness_age_requires_demand_or_cadence_evidence():
    instrument = _squash(_read(SKILLS_DIR / "otel-instrument" / "SKILL.md")).casefold()
    incident = _squash(_read(INCIDENT_REF)).casefold()
    required_terms = [
        "healthy idle",
        "expected cadence",
        "pending/backlogged work",
        "accepted input",
        "localization-only",
        "backlog, queue delay, or missed schedule",
    ]
    for text in (instrument, incident):
        missing = [term for term in required_terms if term not in text]
        assert not missing


def test_instrument_converts_incident_readiness_audit_to_patchable_work():
    text = _squash(_read_raw(OTEL_INSTRUMENT))
    required_terms = [
        "Audit-Driven Incident Readiness",
        "each partial or missing `current_instrumentation.incident_readiness` row",
        "selected finding having the same `area`",
        "one implementation contract",
        "Broad incident-readiness requests select every safe app-owned incident gap before editing",
        "Do not edit until a validated selection has nonempty `approved_ids`",
        "Do not choose one representative gap",
        "A row cannot be `Working` while a required signal is absent",
        "Owner-map an unsafe or externally owned prerequisite",
        "add no placeholder instrument",
        "MTTD-improving",
    ]
    missing = [term for term in required_terms if term not in text]
    assert not missing


def test_instrument_requires_gap_closure_matrix_for_incident_readiness():
    text = _squash(_read_raw(OTEL_INSTRUMENT))
    required_terms = [
        "Audit-Driven Gap Closure",
        "validated dependency-closed selected finding set as the implementation queue",
        "Build an internal closure matrix before editing",
        "finding ID -> area -> priority -> required fix -> instrument mode -> planned action",
        "Use one row per selected audit finding",
        "keep unselected findings out of this implementation report and canonical instrumentation JSON",
        "`Working`",
        "`Not working`",
        "`Not proven`",
        "`Not configured`",
        "Deferred",
        "manual decision",
        "Owner-map an unsafe or externally owned prerequisite",
        "required fix",
        "remaining signal or owner",
    ]
    missing = [term for term in required_terms if term not in text]
    assert not missing


def test_instrument_requires_incident_evidence_gap_closure():
    skill = _squash(_read_raw(OTEL_INSTRUMENT))
    reference = _squash(_read_raw(INCIDENT_REF))
    required_skill_terms = [
        "Incident-Evidence Mode",
        "failure mechanism",
        "owner -> code surface",
        "MTTD-improving",
        "queue depth, consumer lag, oldest message age",
        "Streams and long-lived connections",
        "auth/edge",
        "last-success timestamp",
        "release/config",
    ]
    assert "../references/incident-readiness.md" in skill
    assert "Incident-Evidence Mode" in reference
    assert not [term for term in required_skill_terms if term not in reference]

    required_reference_terms = [
        "Incident-Evidence Mode",
        "MTTD-improving",
        "localization-only",
        "Required Surface Patterns",
        "Auth, edge, and secrets",
        "missing or stale output",
        "dependency target loss",
        "Jobs and offline/derived data outputs",
        "expected-vs-running version",
    ]
    missing_reference = [term for term in required_reference_terms if term not in reference]
    assert not missing_reference


def test_instrument_requires_generic_runtime_surface_closure():
    skill = _squash(_read_raw(OTEL_INSTRUMENT))
    reference = _squash(_read_raw(INCIDENT_REF))
    required_skill_terms = [
        "Follow `../references/incident-readiness.md`",
        "queue depth/lag/oldest age",
        "worker/pool saturation",
        "stream/long-lived connection",
        "active count",
        "send/write failure",
        "A row cannot be `Working` while a required signal is absent",
    ]
    required_reference_terms = [
        "Executors and queues",
        "queue remaining/capacity",
        "active or inflight work",
        "rejected/shed work",
        "Streams and long-lived connections",
        "open/connect",
        "stop/detach/keepalive",
        "connections/channels/streams",
    ]
    assert not [term for term in required_skill_terms if term not in skill]
    assert not [term for term in required_reference_terms if term not in reference]


def test_instrument_skips_custom_prompt_for_incident_readiness_requests():
    text = _squash(_read_raw(OTEL_INSTRUMENT))
    required_terms = [
        "Skip this prompt",
        "incident-readiness or GenAI/LLM",
        "Audit-Driven Incident Readiness",
        "safe app-owned incident gap",
        "scoped",
        "signals",
    ]
    missing = [term for term in required_terms if term not in text]
    assert not missing


def test_incident_readiness_guidance_is_present_across_all_skills():
    paths = [
        SKILLS_DIR / "otel-audit" / "SKILL.md",
        SKILLS_DIR / "otel-instrument" / "SKILL.md",
        SPLUNK_CONFIGURE,
    ]
    required_terms = [
        "customer",
        "dependency",
        "freshness",
        "backpressure",
        "auth/edge",
        "capacity",
        "release/config",
    ]
    for path in paths:
        text = _read(path)
        missing = [term for term in required_terms if term not in text]
        assert not missing, f"{path} missing incident-readiness terms: {missing}"


def test_splunk_configure_consumes_current_main_gaps_section():
    skill = _squash(_read(SPLUNK_CONFIGURE))
    required_terms = [
        "**Findings** from `findings`",
        "instrumentation prerequisite candidate",
        "Preserve its priority",
        "Instrumentation Prerequisites",
        "Do not generate a detector for a missing or unverified signal",
    ]
    missing = [term for term in required_terms if term not in skill]
    assert not missing


def test_audit_maps_incident_readiness_to_current_gap_contract():
    audit = _squash(_read_raw(OTEL_AUDIT))
    report_contract = _squash(_read_raw(REPORT_FLOW))
    required_audit_terms = [
        "Deterministic gap section contract",
        "canonical audit has exactly one actionable gap source: `findings`",
        "Give the audit, every finding, environment, and scenario stable IDs",
        "exact fix or prerequisite",
        "mapped scenario IDs",
    ]
    missing = [term for term in required_audit_terms if term not in audit]
    assert not missing
    assert "## Gap Ledger" not in audit
    required_contract_terms = [
        "one `### Incident Readiness` subsection",
        "Every telemetry-scoped `partial` or `missing` row",
        "product contracts, cost ownership, safety policy, content-governance policy",
        "remain readiness context",
        "`Area` cell is identical",
        "not a second top-level gap ledger",
        "telemetry-scoped Incident Readiness rows",
    ]
    assert not [term for term in required_contract_terms if term not in report_contract]


def test_instrument_reconciles_current_audit_gap_contract():
    instrument = _squash(_read_raw(OTEL_INSTRUMENT))
    required_terms = [
        "Audit-Driven Gap Closure",
        "validated dependency-closed selected finding set as the implementation queue",
        "Build an internal closure matrix before editing",
        "area -> priority -> required fix -> instrument mode -> planned action",
        "Use one row per selected audit finding",
        "keep unselected findings out of this implementation report and canonical instrumentation JSON",
        "Not working",
        "Not proven",
        "Not configured",
        "Deferred",
    ]
    missing = [term for term in required_terms if term not in instrument]
    assert not missing


def test_splunk_configure_demotes_partial_gap_coverage():
    skill = _squash(_read(SPLUNK_CONFIGURE))
    required_terms = [
        "partial closure",
        "generate detectors only for implemented or proven signals",
        "Do not imply complete coverage",
        "`remaining` or equivalent remaining signal fields",
        "Instrumentation Prerequisites",
    ]
    missing = [term for term in required_terms if term not in skill]
    assert not missing


def test_splunk_configure_no_metrics_still_reports_prerequisites():
    skill = _read(SPLUNK_CONFIGURE)
    required_terms = [
        "audit report contains no metrics",
        "do not generate detector or",
        "continue processing gaps and readiness sections",
        "incident-readiness",
        ".observe/detectors.md",
        "alert coverage matrix",
    ]
    missing = [term for term in required_terms if term not in skill]
    assert not missing


def test_splunk_configure_distinguishes_dashboard_prerequisite_and_empty_paths():
    skill = _squash(_read_raw(SPLUNK_CONFIGURE))
    required_terms = [
        "no detector-ready metric exists but accepted evidence supports a requested dashboard",
        "generate the dashboard resources plus both configure reports",
        "`--dashboards-report .observe/dashboards.md`",
        "gaps or readiness prerequisites exist",
        "prerequisites-only `Blocked` result",
        "prerequisites-only validator can still pass its provenance and report-structure checks",
        "neither accepted resources nor gaps exist",
        "without creating artifacts",
    ]
    missing = [term for term in required_terms if term not in skill]
    assert not missing


def test_splunk_configure_does_not_turn_desired_only_dashboards_into_hcl():
    skill = _squash(_read_raw(SPLUNK_CONFIGURE))
    assert (
        "`.observe/terraform/dashboards.tf` only when accepted evidence supports "
        "dashboard resources"
    ) in skill
    assert "when accepted evidence supports at least one Terraform resource" in skill
    assert "report-only desired-state specification" in skill
    assert "desired-only specification never authorizes dashboard HCL" in skill


def test_splunk_configure_routes_specialized_readiness_contracts():
    skill = _read_raw(SPLUNK_CONFIGURE)
    assert "../references/incident-readiness.md" in skill
    assert "../references/genai-readiness.md" in skill
    assert "meta.genai_ownership_detected" in skill


def test_splunk_configure_consumes_incident_readiness_section():
    skill = _squash(_read(SPLUNK_CONFIGURE))
    required_terms = [
        "**Incident readiness** from `current_instrumentation.incident_readiness`",
        "preserve `area`, `status`, `evidence`, `required_signals`, and `impact`",
        "Every `partial`, `missing`, or `owner-mapped` row must map to an unresolved finding",
        "identical area and to a verification scenario",
        "matching finding's `external_owner` or `decision_owner`",
        "readiness rows do not carry an owner field",
        "For every incident-readiness area",
        "unless equivalent metrics are source-backed and proven",
        "Do not generate a detector for a missing or unverified signal",
        "findings",
    ]
    missing = [term for term in required_terms if term not in skill]
    assert not missing


def test_splunk_configure_owns_detector_reliability_handoff():
    skill = _read(SPLUNK_CONFIGURE)
    classification = _read(SPLUNK_CONFIGURE_REFS / "detector-classification.md")
    templates = _read(SPLUNK_CONFIGURE_REFS / "terraform-templates.md")
    required_terms = [
        "detector reliability evidence",
        "missed, flapping, auto-resolved, or no-data alerts",
        "alert-coverage-audit",
        "Do not ask app instrumentation",
        "Do not generate service metric Terraform",
    ]
    combined = "\n".join((skill, classification, templates))
    missing = [term for term in required_terms if term not in combined]
    assert not missing


def test_splunk_configure_covers_dependency_release_and_capacity_mttd_signals():
    skill = _read(SPLUNK_CONFIGURE)
    classification = _read(SPLUNK_CONFIGURE_REFS / "detector-classification.md")
    required_terms = [
        "endpoint health",
        "target health",
        "rate-limit",
        "unhealthy target",
        "disk",
        "filesystem",
        "desired-vs-healthy",
        "startup/readiness/healthcheck",
        "deployment.environment.name",
        "cloud.region",
        "cloud.platform",
        "container.image.name",
        "container.image.tags",
        "artifact version",
    ]
    for text in (skill, classification):
        missing = [term for term in required_terms if term not in text]
        assert not missing


def test_splunk_configure_dashboard_signalflow_guardrails():
    skill = _read(SPLUNK_CONFIGURE)
    templates = _read(SPLUNK_CONFIGURE_REFS / "terraform-templates.md")
    required_skill_terms = [
        "Keep the Splunk Observability Cloud API `realm` variable separate",
        "Do not use `var.realm` as a SignalFlow filter",
        "`sfx_realm`",
        "dashboard variables",
        "Before writing chart `program_text`",
        "pre-aggregated percentile metrics",
        "do not average",
        "value sanity check",
        "apply_if_exist = true",
        "stale `configId` parameter",
        "mixed-unit signals",
        "separate panels",
        "provider-derived",
        "stale/unowned evidence",
        "source-backed coverage",
        "cumulative counters",
        "`rollup='rate'`",
    ]
    required_template_terms = [
        "Do not equate the provider/API `realm` variable with telemetry",
        "`sfx_realm`",
        "dashboard variables",
        "apply_if_exist = true",
        "apply_if_exist = false",
        "pre-aggregated",
        "do not average",
        "known-traffic window",
        "unverified in `.observe/dashboards.md`",
        "stale `configId` parameter",
        "mixed-unit signals",
        "separate panels",
        "provider-derived",
        "stale/unowned evidence",
        "source-backed emitter",
        "cumulative timers",
        "`rollup='rate'`",
    ]
    assert not [term for term in required_skill_terms if term not in skill]
    assert not [term for term in required_template_terms if term not in templates]
    assert 'property       = "deployment.environment.name"' in templates
    assert "newly instrumented services should emit `deployment.environment.name`" in templates
    for term in ["e.g. us1, eu0, lab0", "e.g. us1, eu0", "us1", "eu0", "lab0"]:
        assert term not in skill
        assert term not in templates


def test_splunk_configure_preserves_runtime_cpu_coverage():
    skill = _read(SPLUNK_CONFIGURE)
    classification = _read(SPLUNK_CONFIGURE_REFS / "detector-classification.md")
    templates = _read(SPLUNK_CONFIGURE_REFS / "terraform-templates.md")
    required_terms = [
        "source-backed CPU utilization",
        "CPU saturation detector",
        "Do not use thread count",
        "cumulative CPU time",
        "diagnostic rate",
        "`rollup='rate'`",
        "normalized CPU utilization",
    ]
    for text in (skill, classification, templates):
        missing = [term for term in required_terms if term not in text]
        assert not missing


def test_splunk_configure_prevents_generic_keywords_from_shadowing_fault_domains():
    classification = _read(SPLUNK_CONFIGURE_REFS / "detector-classification.md")
    templates = _read(SPLUNK_CONFIGURE_REFS / "terraform-templates.md")
    required_classification_terms = [
        "`availability` or `unavailable` alone is not sufficient",
        "dependency-specific",
        "`operation` alone is not sufficient",
        "rather than a client or dependency",
        "freshness/newest-event-age/event-age/ingest-lag/processing-lag/data-age/staleness",
        "There is no universal count threshold for queue depth or consumer lag",
        "Use `85` only for a normalized percentage",
        "metric matches the Capacity Saturation rule",
        "capacity/utilization/cpu/memory/heap/",
        "a gauge/up-down counter",
        "cumulative-CPU-time exclusion",
    ]
    assert not [
        term for term in required_classification_terms if term not in classification
    ]
    assert "85% only for normalized saturation" in templates


def test_dashboard_group_template_includes_provider_required_description():
    templates = _read(SPLUNK_CONFIGURE_REFS / "terraform-templates.md")
    dashboard_shape = templates.split("## Dashboard Terraform Shape", 1)[1]
    assert 'resource "signalfx_dashboard_group" "service"' in dashboard_shape
    assert 'description = "Service health dashboards for ${var.service_name}"' in dashboard_shape


def test_audit_keeps_current_main_report_contract():
    audit = _squash(_read_raw(OTEL_AUDIT))
    report_contract = _squash(_read_raw(REPORT_FLOW))
    current_audit_terms = [
        "`signal_flow`",
        "`current_instrumentation`",
        "`findings`",
        "`verification`",
        "`product_outcome`",
        "expected telemetry",
        "mapped scenario IDs",
        "priorities `required`, `recommended`, or `deferred`",
        "instrument modes `default`, `fix all`, `manual decision`, or `external follow-up`",
        "every finding, environment, and scenario stable IDs",
        "Human HTML must not render full",
    ]
    assert not [term for term in current_audit_terms if term not in audit]
    current_report_terms = [
        "machine-readable priority",
        "### Component Flow Map",
        "| Area | Status | Evidence | Required Signals / Gap | Detection / Localization Impact |",
        "### Test Environments",
        "### Acceptance Scenarios",
        "exact action, expected telemetry, proof level, and acceptance criteria",
        "| Priority | Area | Gap | Why it matters | Required fix | Instrument mode | Verification scenarios |",
    ]
    assert not [term for term in current_report_terms if term not in report_contract]
    assert "| Priority | Area | Gap | User Impact | Fix | Instrument Mode |" not in audit
    assert "## Gap Ledger" not in audit


def test_incident_readiness_guidance_stays_generic_and_non_genai():
    shared_skill_paths = [
        SKILLS_DIR / "otel-audit" / "SKILL.md",
        SKILLS_DIR / "otel-instrument" / "SKILL.md",
        SPLUNK_CONFIGURE,
        SPLUNK_CONFIGURE_REFS / "detector-classification.md",
        SPLUNK_CONFIGURE_REFS / "terraform-templates.md",
    ]
    genai_terms = [
        "GenAI",
        "LLM",
        "gen_ai",
        "RAG",
    ]
    assert not [term for term in genai_terms if term in _read_raw(INCIDENT_REF)]

    blocked_project_terms = [
        "IR-",
        "guildcore",
        "Guildcore",
        "guild.ai",
        "sb-rest",
        "signalboost",
        "signalboost-rest",
        "sbrest",
        "metadata-server",
        "matt-server",
        "Matt",
        "meatballs",
        "Meatballs",
        "US1",
        "EU0",
        "us1",
        "eu0",
        "lab0",
        "checkout",
        "missing report output",
        "active-node",
        "active node",
        "Decision or delivery workflow",
        "decision or delivery workflow",
        "workflow delivery/evaluation",
    ]
    for path in [INCIDENT_REF, *shared_skill_paths]:
        text = _read_raw(path)
        bad = [term for term in blocked_project_terms if term in text]
        assert not bad, f"{path} contains project-specific terms: {bad}"
