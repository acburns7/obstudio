---
name: otel-instrument
description: >-
  Implement an approved OpenTelemetry audit selection in an application's
  existing runtime, add auto-instrumentation and selected custom signals,
  validate the code, and hand the exact scope to otel-verify. Use for requests
  to add OTel, tracing, metrics, incident-readiness signals, GenAI telemetry,
  or exact audit finding IDs.
---

# Instrument

Implement only validated, dependency-closed work from the canonical OTel audit.
Preserve the application's runtime shape and downstream telemetry contracts.

Before editing application code, read `../references/report-flow-contract.md`
and follow its Instrumentation Contract and Reader-First Report Order. Read
`./references/json-approval-handoff.md` whenever
`.observe/otel-audit.json` exists or the request supplies finding IDs. It owns
selection precedence, normalized digests, instrumentation JSON, and human HTML.
Read `./references/project-runtime-validation.md` before selecting a runtime or
running implementation checks.

## Reference Routing

Load only what the repository and selected work require:

| Condition | Read |
|---|---|
| Python, Node.js, Java, or Go target | The one matching file under `./references/languages/` |
| Choosing a custom signal type | `./references/signal-mapping-guide.md` |
| Requests for faster incident detection/localization, incident evidence, or owned workflow/dependency/freshness/backpressure/auth/capacity surfaces | `../references/incident-readiness.md` |
| LLM, agent, tool/function, MCP, retrieval, model gateway, evaluation, or other GenAI ownership | `../references/genai-readiness.md` |
| Implementing selected incident-readiness or GenAI work, including span ownership, evaluation, token pressure, MCP, or route-aware HTTP proof | `./references/readiness-implementation.md` after the applicable shared readiness reference |
| Any validated selected application-log change, including correlation-only, OTLP export, or an OTLP bridge | `./references/log-export-contract.md` before changing logging setup; add export components only for selected OTLP work |
| A claim depends on a real agent, preload, framework route resolver, automatic metric, startup exporter, duplicate suppression, or OTLP log bridge | `../references/full-runtime-acceptance.md` |

## Workflow

### 1. Preflight

#### Canonical Audit And Selection Gate

The JSON flow is mandatory:

- `.observe/otel-audit.json` is the canonical audit and `.observe/otel.html` is
  the audit and scope-planning surface. Never infer scope from audit Markdown.
- If the canonical audit is absent, stop before application-code, dependency,
  runtime-config, or test edits and ask the user to run `$otel-audit`. Never
  fabricate audit IDs or selection artifacts.
- Before edits, read and follow `./references/json-approval-handoff.md`.
- Selection precedence is: current-request exact `--ids`; trusted repository
  selection or embedded `review_selection`; explicitly supplied saved-audit
  candidate; automatically adopted matching saved state only when repository
  scope is absent; then, only for a bare or broad request, deterministic
  `select --all`.
- Unless current `--ids` already wrote a fresh selection, run the shared
  `adopt-selection` helper as an idempotent preflight step before reporting a
  missing selection. If the helper prints `PASS:` or `wrote`, immediately run
  `validate-flow` and continue the same `$otel-instrument` run; do not ask the
  user to move a download, save again, or rerun instrumentation.
- If broad `select --all` reports manual-decision options, stop and present the
  exact `--decision OTEL-###=option-id` choices. Never choose between mutually
  exclusive owners, providers, propagation paths, or signal shapes.
- `manual decision` and `external follow-up` IDs cannot enter the executable
  selection. `decision_answers` records choice state but never selects work.
  Only work inside the recorded option's `unlocks` may be requested; work
  outside the recorded option's `unlocks` is invalid. A valid answer-only
  handoff with empty `approved_ids` authorizes no edits.
- Run `validate-flow`. A missing, stale, unknown, dependency-incomplete, or
  empty executable selection is a hard stop. Do not edit until a validated
  selection has nonempty `approved_ids`.
- Implement exactly the selected IDs plus executable dependencies added by
  `select`: the dependency-closed `approved_ids` in canonical audit order.
  Never add unselected work.
- Bind instrumentation to the exact normalized selection with
  `selection_sha256`. It includes requested IDs, approved IDs,
  `decision_answers`, and approval metadata, so an answer change invalidates
  older instrumentation even when executable IDs are unchanged.

#### Evidence Preflight

Before the first edit, inspect source, dependencies, startup surfaces, config,
tests, dashboards/detectors, and the selected audit scenarios. Establish:

- language/framework and the actual target process and entrypoint;
- runtime shape and the project-selected runner, probe, and narrow validation
  command from `project-runtime-validation.md`;
- `service.name`, `service.version`, environment source, and safe
  low-cardinality region/platform/image/config/rollout resource context;
- incremental addition versus new scaffold, existing telemetry indicators,
  and log scope: `correlation-only`, `otlp`, or `not requested`;
- provider/exporter topology per signal, including explicit or lazy provider
  creation, global registration, exporter protocol/endpoint/path, no-op paths,
  shutdown, and reachability from the selected process;
- existing consumer contracts: metric/span/log/resource names and dimensions,
  exporter settings, query fixtures, dashboards, detectors, and entity mapping;
- each selected finding's stable verification scenarios, environment IDs, and
  required `proof_level`; never downgrade `full runtime` to a focused test.

For Python, run
`../otel-audit/scripts/scan_python_otel_topology.py <service-root>` when it is
available and reconcile candidates with source. For Java, follow the Java
reference's Trace Wiring Inventory and classify tracing as `auto-only`,
`custom-with-provider`, `custom-provider-external`, or `missing`.

Detect incident-readiness and GenAI ownership before planning. Load the
matching shared reference when triggered. For incident, postmortem, ticket, or
alert evidence, use Incident-Evidence Mode and map the failure mechanism to its
owning code or platform surface and to `MTTD-improving`, `localization-only`,
or uncovered proof. For GenAI, follow the GenAI Semconv Source Contract,
record live-or-snapshot provenance, and build its semconv closure matrix.

State one pre-edit progress note containing the target process, runtime shape,
service/environment identity, incremental/scaffold choice, selected runtime and
validation command, audit ID/SHA, selection path, exact dependency-closed IDs,
selected scenario IDs, provider ownership, log scope, consumer compatibility
risks, and applicable incident/GenAI surfaces. If multiple runnable surfaces
remain plausible, ask one focused question; do not invent an entrypoint.

### 2. Audit-Driven Gap Closure Plan

Treat the validated dependency-closed selected finding set as the implementation
queue. Build an internal closure matrix before editing:

`finding ID -> area -> priority -> required fix -> instrument mode -> planned action -> verification scenarios`

For every selected finding, record the concrete change or proof-only action,
exact telemetry items/call sites, consumer impact, tests, required proof level,
remaining signal or owner, and status. A row cannot be `Working` while a
required signal is absent, only a follow-up, or supported only by an unexecuted
test. Owner-map an unsafe or externally owned prerequisite; add no placeholder
instrument.

For incident-readiness rows, reconcile each partial or missing
`current_instrumentation.incident_readiness` row with the selected finding
having the same `area`; together they are one implementation contract. Broad
incident-readiness requests select every safe app-owned incident gap before
editing. Do not choose one representative gap unless the user narrows scope.

For GenAI, use the canonical audit's selected `genai_readiness` surfaces. Track
`surface -> required_signals -> implemented/proven -> tests -> remaining_signals -> status`.
Do not claim a surface covered or complete unless every required signal is
implemented and tested, proven with its source/signal name, or owner-mapped.

### 3. Implement The Selected Scope

Use the application's existing package manager, startup path, config style, and
lifecycle. Do not introduce containers merely for observability.

Core constraints:

- Use official OpenTelemetry packages; use a library-maintained integration
  only where no official package exists.
- Find and extend existing setup. Keep one provider per signal and one shared
  resource identity per process. Do not initialize an SDK twice.
- Resolve each exporter as protocol plus endpoint plus signal path. Trace
  delivery does not prove metric or log delivery.
- Merge operator-provided resource values; defaults only fill absent keys.
  Prefer `deployment.environment.name`, `cloud.region`, `cloud.platform`,
  `container.image.name`, and `container.image.tags`.
- Preserve safe consumer-visible aliases. Default telemetry changes to
  additive compatibility. Replacing unsafe high-cardinality fields is an
  intentional breaking migration: record the bounded replacement and query
  migration in `telemetry_changes[].consumer_compatibility` as `compatible`,
  `breaking`, or `requires_review`.
- Put initialization in a separate file, preserve actual entrypoints, reuse
  tracer/meter/instruments, and install framework instrumentation before the
  process starts serving. Libraries get opt-in setup, never SDK initialization
  on import.
- Use stable low-cardinality span names and metric dimensions. On custom-span
  failure, record the exception and set ERROR. Never emit secrets, raw URLs,
  user/tenant/session/request/trace IDs, raw payloads, prompts, completions, or
  tool arguments as metric dimensions.
- Use semantic-convention signals first. Add recommended optional signals only
  when an approved readiness or verification requirement needs them, the
  service can observe the value accurately, and privacy/cardinality rules
  permit it.
- Before adding an outcome counter/histogram inside HTTP, RPC, database, or
  messaging work, determine whether the existing RED metric already carries
  the outcome or has a supported per-call metric-attribute hook. Use a custom
  metric only when no call exists or the outcome cannot be represented there.
  Follow the language reference for exact behavior.
- Create spans only for diagnostic boundaries and metric instruments once at
  startup with explicit unit and description.

#### Language Routes

Read the one detected language reference and follow its exact dependency,
provider, framework, metric-reader, and startup patterns:

| Language | Required baseline |
|---|---|
| Python | Explicit API/SDK/OTLP and detected instrumentation dependencies; shared setup module; framework instrumentation before serving; one provider per signal |
| Node.js | Explicit HTTP/framework packages; `NodeSDK` with documented `metricReader`; correct `--require` or `--import` preload |
| Go | Dedicated initialization/shutdown; `otelhttp.NewHandler` outermost for HTTP metrics; route-aware inner middleware when needed |
| Java | Reuse the classified trace source; prefer the Java agent for basic Spring coverage; add API/DI only when custom work requires it and no binding exists |

For local/eval metric readers, use `OTEL_METRIC_EXPORT_INTERVAL=1000` and
`OTEL_METRIC_EXPORT_TIMEOUT=500` through the language's exact API. Default the
host/native OTLP HTTP endpoint to `http://localhost:4318` only when existing
platform config does not supply a collector.

#### Audit-Driven Incident Readiness

Follow `../references/incident-readiness.md` for source-evidenced workflow,
dependency, input complexity, freshness, queue depth/lag/oldest age,
worker/pool saturation, stream/long-lived connection active count and
send/write failure, synthetic/canary, auth/edge, capacity, health/readiness,
and release/config signals.

Do not call a bare age gauge detector-ready during healthy idle periods.
Require expected cadence, pending/backlogged work, or accepted input; otherwise
classify it `localization-only` and prefer backlog, queue delay, or missed
schedule. For web/worker repos, use distinct, operator-overridable
`service.name` defaults and initialize each process only from its actual
entrypoint or startup hook; API imports must not initialize worker telemetry.
Focused tests must execute enqueue success/failure and worker task
success/failure through an in-memory or equivalent telemetry seam. AST or grep
does not prove emission. For changed concurrent Go packages, run
`go test -race`; a normal `go test` pass is insufficient. Detector-critical
tests must drive a non-default incident state and assert the datapoint and
bounded dimensions.

#### GenAI Readiness Contract

Follow `../references/genai-readiness.md` for exact semconv, span-source,
inference lifecycle, parent-context, incident, privacy, and closure contracts.
Use one canonical GenAI span source per logical operation and suppress overlap
before bootstrap. Preserve source-backed stable workflow/agent/model/tool names.
App-owned model calls need a real inference lifecycle span under the owning
workflow/agent. Do not keep a current-span context manager open across async
stream yield/task boundaries or mutate immutable framework carriers in place.

Implement selected provider/model, workflow/agent, tool/function or MCP,
retrieval, streaming, token/context, prompt/response, safety/policy,
AI-derived-data, memory, evaluation, content governance, cost, and model/config
signals exactly as required by the audit. Metrics-only evaluation does not
satisfy selected-trace evidence. Raw content capture is off by default.

### Fast Path And Custom Instrumentation Prompt

When auto-instrumentation is configured and no canonical selection, incident or
GenAI readiness path, or requested custom signal supplies approval, ask:

> Auto-instrumentation is configured. Would you like me to add custom spans or metrics for your business logic?

Skip this prompt for a validated canonical selection, a specific custom signal,
or incident-readiness or GenAI/LLM work; that scoped selection/request is the
approval. If the OTel SDK already exists, add only the requested selected
signal and do not re-scaffold. Even this fast path covers every selected ID.
When no canonical audit exists, stop before custom instrumentation and ask the
user to run `$otel-audit` first.

### 4. Deterministic Validation And Verification

Follow `./references/project-runtime-validation.md` without asking permission
for local-safe project checks:

1. Probe and record the selected project runtime/version.
2. Run `git diff --check` and syntax/parser checks for changed config/scripts.
3. Compile, typecheck, or import every affected module with that runtime.
4. Run the smallest focused repo-native tests. For custom signals, execute each
   changed call site and assert emitted telemetry; prove removed signals absent.
5. Map actual test execution to every selected audit scenario. A no-match guard
   is not evidence.
6. Repair instrumentation-caused failures and rerun affected gates.

If the configured runtime or dependency is unavailable, record the exact
prerequisite as `Blocked`; never substitute an incompatible global runtime.
Skip commands only when the user explicitly forbids verification or assigns it
to an external eval, and then record `Not run` without claiming success.

After the implementation gate, invoke or apply `$otel-verify` with the same
bound selection unless the user explicitly opts out or a concrete prerequisite
blocks it. Record its result and `.observe/otel-verify.md`. Apply the conditional
full-runtime gate whenever runtime-only behavior is claimed; attempt a safe
local profile without asking, or name the exact missing runtime, listener,
dependency, credential, or fixture and keep affected rows `Partial`, `Blocked`,
or `Not proven`.

`Not run` or `no collector was run` alone is not an acceptable blocker. For
each full-runtime row, record either the executed command and direct result or
the concrete unavailable runtime, listener, dependency, credential, or fixture.
Do not finalize while a safe local profile exists and remains unattempted.

If verified metric evidence exists and the user requested detectors or Splunk
configuration, invoke or apply `$splunk-configure` and report its verification.

### 5. VS Code Debugging

If `.vscode/launch.json` exists, update at least one service configuration with:

- `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`
- `OTEL_METRIC_EXPORT_INTERVAL=1000`
- `OTEL_BSP_SCHEDULE_DELAY=100`

Report the configuration and whether values were added or present. If the file
exists but cannot be updated, stop and explain. Otherwise state:
`No .vscode/launch.json found; Step 6 skipped.`

### 6. Artifacts And Finalize

Always write `.observe/otel-instrumentation.md`. In canonical flow also write
`.observe/otel-instrumentation.json` and render
`.observe/otel-instrumentation.html`. Never modify the canonical audit or put
implementation state in `.observe/otel.html`.
Users open `.observe/otel-instrumentation.html` after instrumentation to review
the selected changes and proof. Do not use it to change selected scope.

#### Reader Order

Use this Markdown order:

```markdown
# OTel Instrumentation Report: <service>
**Result:** Pass | Partial | Fail | Blocked
## Executive Summary
## Flow
## Files Changed
## Signals Changed
## Audit Gap Closure
## GenAI Readiness Closure
## Validation Gates
## Verification Handoff / Results
## Detector Handoff / Results
## Remaining Gaps
## Next Steps
```

Omit `GenAI Readiness Closure` unless the source audit declares GenAI ownership
and selected findings map to those surfaces. `Signals Changed` is the
implementation-change inventory for exact added, modified, removed, or `None`
traces/spans, metrics, logs/events, runtime/config, and dependencies, with
product action, source/test evidence, and verification status.

#### Signals Changed

| Signal type | Added | Modified | Removed | Product result / next product action | Evidence | Verification status |
|---|---|---|---|---|---|---|

Do not claim a removal unless the previous report or Git diff proves it existed
and current source proves it was removed. Use `None` for empty cells.

Use one row per selected audit finding and keep unselected
findings out of this implementation report and canonical instrumentation JSON:

`Finding | What changed | Tested | Result | Evidence / reason`

Allowed results are `Working`, `Not working`, `Not proven`, `Not configured`,
and `Deferred`. Only an executed failed check is `Not working`. Project
`changes`, `tests`, and `evidence` from instrumentation JSON without independent
paraphrase; after verification, take only `Result` from the bound verify row.
Derive `**Result:**` from all applicable closure tables.

For incident work, add `### Incident Readiness Signal Roles` under
`## Signals Changed` with one row per exact signal:

| Surface | Exact signal | Role | Detector use / reason | Proof | Remaining owner / prerequisite |
|---|---|---|---|---|---|

Use exactly `MTTD-improving`, `localization-only`,
`provider/platform-owned`, or `uncovered`; this is not another gap ledger.

For selected GenAI surfaces, copy the audit's exact surface and complete
required-signals cell into `GenAI Readiness Closure`, then record
implemented/proven signals, tests, remaining signals, and result. `Working`
requires `Remaining signals` to be `None`; otherwise name the remaining signal
or owner. Never create this closure without canonical source audit ownership.

Instrumentation JSON must match the exact shape and rules in
`json-approval-handoff.md`: exact selected findings once in audit order; bound
audit and selection digests; nonempty finding `changes`; stable per-item
`telemetry_changes[].id`; exact source, attributes, product view, scenario IDs,
follow-ups, and consumer compatibility; and `resolved_commit: null` without
commit proof. Verification proof remains in the separately bound verify JSON.

Validate and render with the exact commands from the handoff:

```bash
python3 "<directory-containing-loaded-SKILL.md>/scripts/observe_report.py" validate-flow \
  .observe/otel-audit.json \
  --selection-json .observe/otel-selection.json \
  --instrumentation-json .observe/otel-instrumentation.json

python3 "<directory-containing-loaded-SKILL.md>/scripts/observe_report.py" render-instrumentation-html \
  .observe/otel-audit.json \
  -o .observe/otel-instrumentation.html \
  --selection-json .observe/otel-selection.json \
  --instrumentation-json .observe/otel-instrumentation.json
```

After `$otel-verify`, rerun both with
`--verify-json .observe/otel-verify.json`. Require its
`instrumentation_sha256` to match the normalized instrumentation overlay.
Repair binding, digest, ID-order, status, or evidence errors before finalizing.

Use the command's returned loopback links for both otel-instrumentation.html and
otel.html; do not open either report automatically and do not provide
local-file HTML links. Keep Markdown and JSON report links as absolute local
paths.

The final response separates files changed from verified outcomes and states:
selected runtime, compile/type/import result, focused tests that ran, verify
result/blocker, selected gap counts by result, service-name and OTLP config,
expected automatic spans/metrics, log scope, full-runtime result, compatibility
migrations, remaining incident/GenAI signals and owners, and detector handoff
when requested. Never say `complete`, `working`, or `verified` when mandatory
source validation failed, was blocked, or was not run.

## Credential Safety And Scope

- Before introducing env files, ensure `.env` is ignored. Put only safe
  placeholders in `.env.example`; never commit tokens or credentials.
- Search tracked config for real tokens without printing secret values. Do not
  place secrets in source, reports, terminal output, or generated HTML.
- Existing apps are incremental: add only selected missing work. New apps get
  a scaffold only when the audit selected it, matching the current runtime.
- Do not silently expand to another process, environment, service, detector,
  dashboard, or production apply.
