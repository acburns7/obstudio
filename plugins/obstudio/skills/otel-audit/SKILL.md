---
name: otel-audit
description: >-
  Audit a service repository for existing OpenTelemetry instrumentation,
  provider/exporter topology, and observability gaps. Use for $otel-audit,
  observability readiness or missing-signal reviews, incident detectability,
  and GenAI/LLM semantic-convention coverage. Read-only for application code:
  write only audit artifacts under .observe/. Use $otel-instrument for changes.
---

# Audit OpenTelemetry Coverage

## Contract

Perform a source-derived audit. It does not modify service code, dependencies,
configuration, or tests, and it does not run telemetry verification. The skill
writes `.observe/otel-audit.json` and `.observe/otel.html`; bulky captured
output may go under `.observe/evidence/`. Source definitions are not runtime
proof.

Resolve every path below from the directory containing this loaded `SKILL.md`
(the **skill root**):

- `references/source-discovery.md` is local to this skill.
- `references/schema-v2-contract.md` is local to this skill.
- `../references/*.md` is shared under the parent `skills/` directory.
- `scripts/*.py` is local to this skill.

Never look for skill scripts or references in the audited service or repository
root.

Before scanning, read [source discovery](references/source-discovery.md).
Before authoring `.observe/otel-audit.json`, read and follow the
[schema v2 authoring contract](references/schema-v2-contract.md). It owns the
exact fields, stable IDs, ordering, dependencies, selection invariants, and
human-report projection boundaries.
Before writing artifacts, read and follow the Audit Contract and Reader-First
Report Order in
[the shared report-flow contract](../references/report-flow-contract.md).

Load these references only when their condition applies:

- Read [incident readiness](../references/incident-readiness.md) when the repo
  owns user-visible workflows, dependencies, workers, queues/streams,
  freshness, auth/edge, capacity, release/config behavior, or when incident,
  alert, ticket, or postmortem evidence is supplied.
- Read [GenAI readiness](../references/genai-readiness.md) when the repo owns an
  LLM/provider, agent/workflow, tool/MCP, retrieval/RAG, memory/context,
  evaluation, prompt/response, token/cost, model/config, or other AI-path
  surface.

## Workflow

### 1. Bound the service and discover source

1. Confirm the service root. If no dependency manifest is present, ask for the
   correct subdirectory. If multiple independent services are present, ask for
   scope or audit each independently.
2. Follow `references/source-discovery.md` to identify every target process,
   language, framework, manifest, entry point, route, dependency, worker/job,
   runtime/startup surface, and existing test seam.
3. Cite complete repository-relative paths, with exact line selectors when
   useful. Confirm paths and symbols with `rg -n`; never cite guessed paths,
   globs, or shortened basenames.
4. Enumerate every route as its own method/path entry. Inventory Traffic and readiness clients
   that exercise an AI path, including demo, load, eval, or replay scripts such
   as `load_demo.py`.
5. Record configured runtime/toolchain requirements and project-native runners,
   not the shell's incidental default. Do not install dependencies.

### 2. Build the current-state topology

For each target process and each signal independently:

1. Trace provider creation, global registration, lazy initialization, no-op
   branches, exporters, resources, startup reachability, and shutdown/flush.
2. Classify traces, metrics, and logs separately as `source-active`,
   `externally bootstrapped`, `source-defined but inactive`, or `no provider`.
   None of these is emission proof.
3. Reconcile OTLP endpoint/protocol pairs, resource precedence, startup timing,
   and operator-provided identity. Do not infer all-signal coverage from one
   provider or one launch command.
4. For Python, run the bundled candidate scanner, then reconcile every hit with
   the selected process and startup path:

   ```bash
   python3 -I "<skill-root>/scripts/scan_python_otel_topology.py" "<service-root>"
   ```

5. List every exact span, metric, and log integration separately with its
   source. Do not group signals as "HTTP spans", "runtime metrics", or
   "related" items. Classify logs as `otlp`, `correlation-only`, or
   `not configured`.
6. Identify missing official auto-instrumentation for detected dependencies and
   anti-patterns in provider ownership, cardinality, span naming, propagation,
   exception recording, endpoint configuration, and lifecycle handling.

### 3. Route specialized readiness

When incident readiness applies, use the complete incident reference. Map
evidence as:

`incident class -> failure mechanism -> owner -> code surface -> signal -> MTTD impact -> remaining owner`

Mark a signal `MTTD-improving` only if it can drive detection before or at
first customer impact. Use `localization-only` when it mainly narrows an
already-detected fault. Owner-map platform signals; do not pretend detector
configuration can replace a missing service-owned metric.

When GenAI ownership applies, follow the complete GenAI reference, including:

- the `GenAI Semconv Source Contract`: reconcile relevant surfaces with current
  official docs when available and record live-or-snapshot provenance plus a
  semconv closure matrix;
- the `Single-Source GenAI Span Contract`: choose one canonical GenAI span source per logical operation
  across framework/vendor bridges, provider SDK hooks, callbacks, and
  auto-instrumentors, with one GenAI node per logical operation, correct parent shape,
  expected LLM and tool counts, and stable model/tool names;
- the `LLM Inference Lifecycle Contract`: workflow-level token accounting or a
  final usage event is not a model-call lifecycle span. Inspect
  `on_chat_model_start`, `on_chat_model_end`, `on_chat_model_error`, or the
  direct provider/stream call for `chat`, `generate_content`, or
  `text_completion`, `gen_ai.operation.name`, `gen_ai.request.model`, and
  `gen_ai.response.model`; keep missing work in `remaining_signals`;
- pre-bootstrap suppression: when app spans are canonical and startup uses
  `opentelemetry-instrument` or another auto-instrumentation bootstrap, require
  the launch environment to suppress overlap before the bootstrap. App module code that mutates environment variables
  is not sufficient proof because framework hooks may already be registered;
  inspect Makefile targets, service runner scripts, Docker or Helm env,
  VS Code launch configs, and generated env scripts;
- identity and context: preserve stable business workflow identity and stable agent identity
  from constants, workflow registrations, telemetry event names,
  framework agent names, agent factory names, registration names, callback owner names,
  docs, or prior trace names. Do not invent names from HTTP routes,
  session-derived labels, or generic service-derived names. For example,
  preserve `assistant_v3_turn` rather than inventing
  `assistant_v3_session_turn` or `POST /v2/assistant/sessions`; preserve a
  discovered DeepAgents identity as `deepagents`, not `assistant_v3_agent`;
- trace shape: preserve the owning workflow/agent context. `chat` and
  `execute_tool` spans must not become siblings of the workflow under a generic HTTP root span
  or generic server span. Put `gen_ai.usage.input_tokens`, `assistant.llm.calls`,
  and `assistant.tool.calls` on the workflow or most specific owning GenAI span.
  Require `workflow -> chat` and
  `workflow -> execute_tool` parent-context proof, and reject wrapper spans as
  canonical GenAI operations;
- privacy and closure: do not capture raw prompts, completions, tool arguments,
  retrieved content, credentials, users, or tenants by default. Audit
  token/context pressure, response parse failure, prompt/tool schema version,
  expected-vs-running model/config, memory/context, evaluation quality,
  `gen_ai.evaluation.result`, evaluation score distribution, content capture mode/redaction/access owner,
  content governance, framework bridge, cost ownership, and owner-mapped billing source
  without inventing observable data.

For tool/MCP surfaces, require a stable tool/method family,
authentication/authorization result, invalid-token or permission failure outcome,
duration/error/timeout signals, and send/write failure. Never use
JSON-RPC request, session, trace, user, or tenant IDs as metric dimensions.

Treat demo-only environment hints as incomplete. `OTEL_SERVICE_NAME` or
`OTEL_EXPORTER_OTLP_ENDPOINT` without SDK setup, exporter setup, resource attributes,
and framework instrumentation is incomplete resource/exporter configuration.

For GenAI incident-evidence mode, map:

`incident class -> failure mechanism -> repo/service owner -> code surface -> required signal`

Cover provider/model gateway, tool/function execution or MCP when present,
retrieval/RAG, streaming, token/context, prompt/response assembly, safety/policy,
AI-derived data and AI-derived data jobs, model/config rollout and model/config compatibility,
AI-owned cache/session, and AI-path synthetic/canary checks. Route detector reliability evidence
for missed, flapping, auto-resolved, or no-data alerts to
`$splunk-configure`.

### 4. Create deterministic closure scope

Load `references/schema-v2-contract.md` before building the canonical JSON.
Build reusable test-environment profiles, then one stable acceptance scenario
per telemetry-distinct success, error, timeout, startup, shutdown, worker,
dependency, streaming, tool, or retrieval path. Each scenario must cite an
existing entry point, reference environment IDs, name exact expected signals,
state acceptance criteria, and use proof level `focused call-site`,
`full runtime`, or `either`. This is a source-derived plan; do not execute it.

Write new audits as schema v2. Keep these invariants:

- `.observe/otel-audit.json` is the canonical machine-readable audit source;
  `.observe/otel.html` is the self-contained human review report.
- Give the audit, every finding, environment, and scenario stable IDs. Preserve
  canonical order and dependency direction from executable work to its
  prerequisite.
- Include `meta`, `summary`, `flow`, `evidence`, `routes`, `signal_flow`,
  `current_instrumentation`, `genai_readiness`, `findings`, `verification`,
  `anti_patterns`, and `recommendation` as required by the bundled validator.
- Set `meta.genai_ownership_detected`. Declare `**GenAI ownership detected:** Yes` or `No`;
  include one matching `GenAI ownership` evidence row. Populate
  `genai_readiness` only for `Yes`.
- **Deterministic gap section contract:** the canonical audit has exactly one actionable gap source: `findings`.
  Record GenAI detail in canonical `genai_readiness` rows, promote only service-owned OTel telemetry closure rows into `findings`,
  and keep the HTML decision view focused on those findings.
  Readiness rows are audit context first;
  preserve authored readiness rows in canonical JSON. Promote a missing or
  partial readiness surface only when the repository owns a concrete OTel
  closure gap. Human HTML must not render full Incident or GenAI readiness
  ledgers as peer action sections. Do not render authored readiness tables as
  visible peer sections in audit HTML.
- Use priorities `required`, `recommended`, or `deferred`; use instrument modes
  `default`, `fix all`, `manual decision`, or `external follow-up`. A finding
  must carry impact, `product_outcome`, exact fix or prerequisite, evidence,
  acceptance criteria, expected telemetry, follow-up actions, dependencies,
  and mapped scenario IDs when runnable.
- Use executable `default`/`fix all` findings for app-owned work. Do not create
  manual or external findings just to record product/runtime choices, billing,
  cost, safety policy, content-governance, or external business context. Use
  those modes only when they block concrete executable OTel work. Do not
  promote service behavior choices, health endpoint semantics,
  readiness/liveness contracts, or other product policy as OTel findings.
- A manual decision has two or three `decision_options`; each has a stable ID,
  `label`, concrete `outcome`, and pairwise disjoint `unlocks`. For real
  instrumentation branches, create one option-locked executable finding per
  real branch and put each branch ID in
  only that option's `unlocks`. Do not use one shared executable finding for
  multiple exclusive options or make two branch implementations appear as
  simultaneous independent audit gaps. External follow-up names the exact owner
  and telemetry prerequisite.
- `requested_ids` records explicit executable selections; `approved_ids` is the
  dependency-closed executable selection; `decision_answers` separately records
  manual `finding_id`/`option_id` pairs. Manual/external IDs never enter either
  executable ID list, and an answer unlocks but never selects work. The audit
  baseline remains immutable; selection is a bound overlay or compatible
  `review_selection`; a selection carrying `decision_answers` is schema v2.

The **GenAI readiness contract** makes `genai_readiness` the complete GenAI observability ledger.
For each telemetry-distinct owned surface, write one separate readiness row with
`surface`, `status`, `evidence`, `required_signals`, `owner`,
`acceptance_criteria`, and `impact`; use the surface name as the human-facing
identifier.
Keep workflow, provider/model, tool/function, token/context, stream/session, retrieval, evaluation/data
export, and other distinct surfaces independently actionable for
instrumentation closure. Only telemetry closure rows from that ledger become
instrumentation findings. Telemetry closure rows may become findings;
Governance/context rows stay in `## GenAI Readiness`:
Content capture policy, safety/refusal policy, and cost/billing ownership are
not default service instrumentation findings. Evaluation telemetry can be a finding.
Do not bundle that with safety or content-governance work. Cost telemetry can be a finding only when the repository owns an authoritative pricing source.

### 5. Write, validate, and render

Write two audit artifacts inside the service root:

- `.observe/otel-audit.json` -- canonical machine-readable audit source.
- `.observe/otel.html` -- self-contained human review report generated from the
  JSON.

Write the JSON first. Then run `finalize-audit` exactly from the service root:

```bash
python3 -I "<directory-containing-loaded-SKILL.md>/scripts/observe_report.py" finalize-audit \
  .observe/otel-audit.json \
  --html .observe/otel.html
```

Resolve the placeholder from the loaded skill, not the service. When the audit
is rendered from outside its service root, add `--repo-root <service-root>`.
The renderer turns exact existing repository-relative citations into local file
links. If finalization fails, repair canonical JSON or the renderer problem and
rerun `finalize-audit`; never patch generated HTML.

The reviewer uses `.observe/otel.html` to understand findings, answer decisions,
select executable work, and copy the generated command. It is not a proof
report. Use explicit requested IDs when generating the command; preserve
`.observe/otel-selection.json`, `review_selection`, `requested_ids`,
`approved_ids`, and `decision_answers` as the shared flow contract defines.
If the same request already supplies executable IDs, validate their bound
selection with the same helper:

```bash
python3 "<directory-containing-loaded-SKILL.md>/scripts/observe_report.py" select \
  .observe/otel-audit.json --ids OTEL-001 -o .observe/otel-selection.json
```

Use only the top-level sections in the reader order defined by the shared
report-flow contract; do not invent parallel finding or readiness ledgers.

The report must be exactly one findings list ordered by `required`,
`recommended`, then `deferred`; Priority defines ordering only. Put a compact
`Findings · N` heading over cards. Each card has one title, one expected
monitoring outcome, and a neutral `Select` checkbox only for executable work.
Keep the expanded narrative decision-sized: `Gap`, `Why it matters`, a
mode-aware required action, and `Next step`. Use `Instrumentation change` for
executable work, `Decision needed` for a manual prerequisite, and `External
requirement` for an external prerequisite. Put source evidence, expected
telemetry, acceptance criteria, and guardrails in one collapsed `Technical
details` disclosure. Do not render raw verification-scenario IDs. Those fields
remain in canonical JSON.

The HTML terminal command uses explicit requested IDs, for example:

```text
$otel-instrument --ids OTEL-001,OTEL-002 --decision OTEL-003=option-id <absolute-service-root>
```

Show only the plain selectable terminal command section after selection. Do not
render a selection-count summary, and do not expose browser save or download
controls.
A normally finalized report must never show the literal `<service-root>`
placeholder. Do not open the browser automatically.

`finalize-audit` returns a tokenized loopback Markdown link in
`links.review_report`. It starts or reuses a server bound only to `127.0.0.1`
on an available port; remote workspaces may require their normal localhost port
forwarding. After success, the final response must contain exactly this one line
and nothing else:

```text
Review report: [otel.html](http://127.0.0.1:<port>/<token>/otel.html)
```

Copy `links.review_report` verbatim after `Review report: `. Do not include
summary bullets, finding counts, recommendations, a machine-report link,
artifact narration, or any other text.

## Downstream Boundary

The audit stops after finalization. Do not present `$otel-verify` or generic
`run verification` as the audit prompt's next step. The reviewer selects
executable findings in the HTML and runs `$otel-instrument`; that workflow owns
implementation and its internal verification. Run standalone `$otel-verify`
only as a separate, explicit request after this audit completes.
