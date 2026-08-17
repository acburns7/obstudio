# Configure Input And Validation Contract

Use this reference with `splunk-configure` to join canonical audit state,
instrumentation proof, detector prerequisites, and dashboard validation. The
classification and Terraform template references remain authoritative for
category-specific rules and HCL shapes.

## Canonical Input Join

Read the following canonical audit surfaces independently:

- **Findings** from `findings`: each unresolved row is an instrumentation
  prerequisite candidate. Preserve its priority, required fix, owner or
  instrument mode, dependencies, and verification scenarios. Expected
  telemetry is desired state, not emitted-data proof.
- **Incident readiness** from
  `current_instrumentation.incident_readiness`: preserve `area`, `status`,
  `evidence`, `required_signals`, and `impact`. Every `partial`, `missing`, or
  `owner-mapped` row must map to an unresolved finding with the identical area
  and to a verification scenario. Obtain ownership from that matching
  finding's `external_owner` or `decision_owner`; readiness rows do not carry
  an owner field.
- **GenAI readiness** from `genai_readiness`: consume every independently actionable surface row.
  Keep provider/model, workflow/agent, tool/function,
  token/context, stream/session, retrieval, memory/context,
  evaluation/data export, content governance, privacy/cardinality,
  model/config, and cost ownership separate. Do not merge distinct readiness surfaces.
  Missing or partial GenAI areas become instrumentation prerequisites.
- **Instrumentation and verification overlays**: use exact selected findings,
  telemetry-change rows, remaining signals, item results, and evidence from
  the bound JSON artifacts. Markdown is reader detail, not canonical state.

Generate a detector only for an exact source-backed metric whose emitted
datapoint, type, unit, and dimensions are proven, unless the user explicitly
accepts that exact metric as source-only. Do not generate a detector for a
missing or unverified signal.

## Partial And Empty Coverage

For partial closure, generate detectors only for implemented or proven
signals. Do not imply complete coverage while `remaining` or equivalent
remaining signal fields are nonempty. Put each unresolved signal in
`Instrumentation Prerequisites` or `GenAI Instrumentation Prerequisites` with
the exact source/owner and next action.

If the audit report contains no metrics, continue processing gaps and readiness sections.
When those sections exist, do not generate detector or
dashboard resources from desired telemetry; write `.observe/detectors.md`, the
alert coverage matrix, and `.observe/splunk-configure-verify.md` as a
prerequisites-only result. Generate a desired-state dashboard specification
only when requested. If no metrics or readiness gaps exist, stop and explain
that detector-ready data is absent.

For every incident-readiness area that is partial or missing, create a
prerequisite unless equivalent metrics are source-backed and proven. Direct
missing application telemetry to `$otel-instrument`, implemented but unproven
telemetry to `$otel-verify`, and external telemetry to its platform/provider
owner.

## Validator Modes And Canonical Proof

Use exactly one validation shape:

- **Detectors:** require base Terraform plus `detectors.tf`. Authorize a metric
  only from a working direct item assertion with `otlp_accepted` or
  `explorer_visible` delivery in the fully bound canonical audit, selection,
  instrumentation, and verification JSON flow.
- **Audit-backed source-only exception:** when no downstream overlays exist,
  require canonical audit source inventory plus one explicit
  `--allow-source-only-metric` for each exact detector metric. Supplying only
  some overlays is invalid; Markdown never supplies metric proof.
- **Dashboard-only:** pass `--dashboard-only` and
  `--dashboards-report .observe/dashboards.md`; require base Terraform, that
  dashboard report, and a nonempty `dashboards.tf`, with no `detectors.tf`.
  The validator proves canonical provenance, report presence, and structure,
  while the dashboard value checks in this reference remain mandatory.
- **Prerequisites-only:** pass `--prerequisites-only`, require canonical audit
  and both `Blocked` reports, and generate no Terraform artifacts. Omit all
  overlays when none exist; if any exists, supply the complete trio so digest
  and binding validation still run.

Treat Markdown reports as reader projections. Editing a Markdown working row
must never authorize Terraform or repair a stale JSON digest.

## Detector Reliability

Missed, flapping, auto-resolved, or no-data alerts are detector reliability
evidence for `alert-coverage-audit`. Do not ask app instrumentation to emit
alert lifecycle metrics and do not generate service metric Terraform unless
the application actually owns the missing event. Check detector persistence,
clear hysteresis, missing-data behavior, data quality, group-by dimensions,
notification routing, and recovery behavior.

## Dashboard SignalFlow Guardrails

- Keep the Splunk Observability Cloud API `realm` variable separate from
  telemetry dimensions. Do not use `var.realm` as a SignalFlow filter. Use a
  proven telemetry dimension such as `sfx_realm` only when it is present in
  source and emitted evidence.
- Resolve dashboard variables independently of provider variables. Before writing chart `program_text`,
  prove each filter and dimension against the
  accepted metric evidence.
- Treat pre-aggregated percentile metrics as percentiles; do not average them.
  For cumulative counters and cumulative timers, use the documented
  `rollup='rate'` or delta/rate transformation rather than graphing the raw
  cumulative value.
- When a dimension may not exist on every MTS, use `apply_if_exist = true`
  only when the intended fallback is safe. Use `apply_if_exist = false` when
  absence must exclude the series. Never carry a stale `configId` parameter
  into generated SignalFlow.
- Keep mixed-unit signals in separate panels. Verify unit, aggregation,
  dimensions, and useful nonempty values over a known-traffic window. Record
  an unavailable value sanity check as unverified in
  `.observe/dashboards.md`; syntactic validation is not data proof.
- Provider-derived or platform-derived signals need an exact owner and
  evidence. Do not present stale/unowned evidence as source-backed coverage.

For capacity coverage, prefer source-backed CPU utilization or a normalized
CPU utilization signal for a CPU saturation detector. Do not use thread count
or cumulative CPU time as utilization. A cumulative CPU-time diagnostic rate
may use `rollup='rate'`, but label it as diagnostic rate rather than normalized
saturation.

## Reader Categories

When present, report the distinct display categories without collapsing them:

- GenAI Latency
- GenAI Token Pressure
- GenAI Provider
- GenAI Tool
- GenAI Model Config
- GenAI Workflow Fanout
- GenAI Retrieval
- GenAI Memory Context
- GenAI Evaluation Quality
- GenAI Content Governance
- GenAI Cost

The detector report and chat summary derive counts from the same classified
inventory. A category with zero generated resources may still appear in the
prerequisite or coverage matrix, but must not be described as covered.
