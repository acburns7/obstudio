---
name: otel-verify
description: >-
  Verify existing OpenTelemetry instrumentation with deterministic application
  tests, temporary harnesses, and optional local OTLP evidence, then write
  reader and machine reports. Use for $otel-verify, proving spans, metrics, or
  logs, checking audit-selected telemetry, GenAI trace shape, path coverage, or
  local explorer visibility. Read-only for application code unless the user
  explicitly asks to add or repair tests; use $otel-instrument for telemetry
  implementation changes.
---

# OTel Verify

Prove what the application emits; do not infer runtime behavior from source
presence. The default is read-only for application code. Temporary harnesses
may live under `.observe/tmp/`; create or repair permanent tests only when the
user explicitly requests that work.

Resolve every path below from the directory containing this loaded `SKILL.md`,
never from the service repository. Before writing artifacts, read
`../references/report-flow-contract.md` and follow its Verification Report
Contract and Reader-First Report Order.

## Reference Routing

Read only the references required by the current run:

| Trigger | Required reference |
|---|---|
| Canonical `.observe/otel-audit.json` exists | `./references/json-approval-handoff.md` |
| Selecting a configured project runtime | `references/project-runtime-resolution.md` |
| Routes, workflows, jobs, startup, streaming, tools, retrieval, redaction, errors, or other distinct paths are in scope | `references/path-scenario-coverage.md` |
| A claim depends on agents, preload, framework routes, automatic metrics, duplicate automatic spans, startup wiring, or runtime OTLP logs | `../references/full-runtime-acceptance.md` |
| The user asks to add, repair, or persist application tests | `references/app-code-test-authoring.md` |
| Claiming local collector or Obstudio visibility | `references/explorer-witness.md` |

## Scope And Safety Gate

1. Require `.observe/otel-audit.json`. If it is absent, stop and ask for
   `$otel-audit`; never fabricate canonical scope from Markdown.
2. When a canonical audit exists, read and validate the bound
   `.observe/otel-selection.json` and `.observe/otel-instrumentation.json` per
   `./references/json-approval-handoff.md`; verify exactly the approved findings
   in audit order and their referenced scenarios. Also verify every bound
   instrumentation item. Unselected findings are outside this result and must
   not make it partial. Validate the exact `selection_sha256` and bind verification with
   `instrumentation_sha256`; matching IDs alone do not prove freshness.
3. If selection exists but instrumentation JSON does not, perform only an
   explicitly incomplete read-only check. Do not write canonical verification
   JSON or infer instrumentation from Markdown; route the missing handoff to
   `$otel-instrument`.
4. Reconcile saved paths, commands, runtime evidence, and expected signals with
   the current repository. Treat saved output as prior evidence, not current
   proof.
5. Never require production credentials or send verification telemetry to a
   production endpoint. Prefer deterministic fakes and loopback OTLP. Do not
   install dependencies globally or alter manifests/lockfiles unless the user
   explicitly requested that implementation work.

## Build The Proof Plan

Inventory before running commands:

- every exact span/call site, metric, log category or pipeline, resource,
  exporter, and runtime behavior in scope;
- every added, modified, removed, and existing telemetry item, including its
  source, application path, expected attributes/dimensions/body, consumer
  compatibility, and required proof;
- every telemetry-distinct scenario from the selected audit and current code,
  including success, failure, timeout, empty, retry/fallback, streaming,
  startup/shutdown, worker, tool, retrieval, and dependency paths;
- every changed module and the configured compile, typecheck, syntax, import,
  or build gate that must load it.

Use one closure row per exact operation or changed item. A shared helper or one
representative trace does not prove every route, workflow, operation, tool, or
signal. Preserve audit finding, scenario, environment, and instrumentation item
IDs. For GenAI scope, prove the workflow/agent/model/tool/retrieval hierarchy,
token and provider attributes, error paths, and absence of duplicate logical
spans.

## Verification Workflow

1. Read the project-runtime reference, then choose the repository-configured
   wrapper, toolchain, environment, and focused commands. Probe the selected
   runtime before testing. A failure under an unrelated global runtime is a
   rejected candidate, not an application failure.
2. Run static integrity checks for changed scripts/config and `git diff --check`
   when Git is available, then run the narrowest build/import viability gate
   for every changed module. Classify failures as
   `instrumentation-introduced`, `pre-existing`, `environment`, `unknown`, or
   `not applicable`. Continue independent rows, but do not run expensive
   harnesses through a broken prerequisite.
3. Map existing tests and fakes to inventory rows. Prefer proof in this order:
   existing application test; explicitly requested repo-native test; temporary
   app-code harness; the same scenario with loopback OTLP; generated SDK
   contract only when application code cannot run.
4. Run the smallest scenario set that proves every row. Trigger the full
   runtime gate whenever its reference says it is required; a direct handler
   call cannot prove agent/preload behavior, framework route names, automatic
   metrics, or duplicate-span suppression.
5. When local OTLP is available, export the same deterministic scenarios and
   query before stopping the source. Verify each signal's effective protocol,
   endpoint, resource identity, and stored evidence independently. Never treat
   successful traces as proof that metrics or logs are configured.
6. Validate consumer compatibility. `compatible` requires the safe legacy
   contract and additive semantic fields to emit together; `breaking` requires
   the declared removal/replacement proof; `requires_review` remains unproven
   until downstream impact is classified or accepted.

## Proof Rules

- Application code must execute for application proof. Generated SDK telemetry
  is contract-only.
- A span requires its name, required attributes, status/error behavior, and
  relevant parentage or links.
- A metric requires an observed/asserted datapoint, exact name, unit,
  instrument type, and complete bounded dimensions.
- A log requires its body/category, severity, required trace correlation, and
  redaction.
- A path requires its trigger, expected telemetry/topology, and required OTLP
  evidence when applicable.
- A runtime-only row requires the actual configured process and bootstrap.
- Source presence is never runtime proof.

Use these row statuses consistently:

- `Verified: unit`, `Verified: OTLP`, `Verified: unit+OTLP`,
  `Verified: app test`, or `Verified: app test+OTLP` only for direct evidence.
- `Source only` when implementation exists but emission was not proven.
- `Not emitted` when a scenario ran and expected telemetry was absent.
- `Not run`, `Blocked`, `Not configured`, or `Not applicable` as their names
  imply. An absent exporter is `Not configured`, not `Not proven`.

Overall result:

- `Pass`: every in-scope row is working with required proof.
- `Fail`: an executed expectation failed, or instrumentation-introduced source
  viability failed.
- `Partial`: meaningful proof passed, but one or more rows remain unproven or
  environmentally blocked.
- `Blocked`: no meaningful proof could run because a concrete prerequisite is
  unavailable.
- `Not run`: no verification was attempted.

## Artifacts And Validation

Write `.observe/otel-verify.md`. In canonical flow also write
`.observe/otel-verify.json`, bind it to the exact normalized instrumentation
overlay, validate the full flow, and refresh
`.observe/otel-instrumentation.html`. Never write verification state into
`.observe/otel.html`; that remains the audit and scope surface.

The reader report follows the exact Verification Report Contract in
`../references/report-flow-contract.md`. Its first screen must show the result,
what changed, every individual tested item and working state, anything not
working or not proven, and direct proof. Keep runtime inventories, commands,
trace IDs, and detailed diagnostics in technical detail. Never expose raw trace
or span IDs in generated HTML.

Use this exact per-item table header in both the reader report and final
response:

```markdown
| Item ID | OTel item | Type | Added or modified | Working status | How it was tested | Product result / visibility | Evidence |
```

Escape literal `|` characters in Markdown table cells, then run:

```bash
python3 -I "<directory-containing-loaded-SKILL.md>/scripts/validate_reader_report.py" \
  "<service-root>/.observe/otel-verify.md"
```

In canonical mode also pass:

```text
--instrumentation-json <service-root>/.observe/otel-instrumentation.json
--verify-json <service-root>/.observe/otel-verify.json
--audit-json <service-root>/.observe/otel-audit.json
--selection-json <service-root>/.observe/otel-selection.json
```

Repair every validator error and rerun. Follow `Validate And Render` in
`./references/json-approval-handoff.md`; repair canonical JSON or Markdown, never generated
HTML. Do not open reports automatically.

## Final Response

Mirror the reader-first report with these headings in this order:

```markdown
**Result:** Pass | Fail | Partial | Blocked | Not run
**Report:** [otel-verify.md](<absolute path>)
**Machine report:** [otel-verify.json](<absolute path>) when canonical
**Instrumentation report:** [otel-instrumentation.html](http://127.0.0.1:<port>/<token>/otel-instrumentation.html) when canonical
**Audit report:** [otel.html](http://127.0.0.1:<port>/<token>/otel.html) when canonical

## What Changed
## Tested And Working
**Individual result:** <working>/<total> working: <counts by signal type>.
| Item ID | OTel item | Type | Added or modified | Working status | How it was tested | Product result / visibility | Evidence |
|---|---|---|---|---|---|---|---|
## Not Working Or Not Proven
## Proof
```

Include every individual OTel row, even for mixed or failed runs. Write `None`
under `Not Working Or Not Proven` only when every row is proven. Keep technical
diagnostics out of chat. In canonical flow, state the audit ID and approved IDs
and confirm unselected findings were excluded. Name `$otel-instrument` as the
repair path for implementation failures; rerunning verification is not a fix.
Keep the Markdown and JSON report links as absolute local-file paths. Use the
loopback links returned by the renderer for HTML, and do not open either report
automatically.
