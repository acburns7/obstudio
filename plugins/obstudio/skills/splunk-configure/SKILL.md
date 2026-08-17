---
name: splunk-configure
description: >-
  Generate Splunk Observability Cloud detector and dashboard Terraform from
  canonical observability reports, using only proven or explicitly accepted
  metrics. Use for $splunk-configure, detector or dashboard generation, alert
  coverage audits, app-down versus degraded-impact classification,
  blast-radius views, MTTD improvements, incident localization, or GenAI/LLM
  detector coverage. Reports missing signals as prerequisites instead of
  inventing alerts.
metadata:
  author: otel-studio
  version: 0.3.0
  category: observability
---

# Splunk Configure

Generate reviewable Splunk Observability Terraform and evidence reports from
canonical `.observe/` artifacts. This skill writes local files only; it never
publishes or applies resources.

Resolve references and scripts from the directory containing this loaded
`SKILL.md`. Before writing outputs, read
`../references/report-flow-contract.md` and follow its Splunk Configure
Contract and Splunk Configure Verification. Also read
`references/input-and-validation-contract.md`; it owns the canonical input
join, partial/empty coverage, detector reliability, and dashboard value rules.

Load specialized readiness semantics only when the canonical audit requires
them:

- Read `../references/incident-readiness.md` when incident-readiness rows or an
  incident/impact/blast-radius mode is in scope.
- Read `../references/genai-readiness.md` only when
  `meta.genai_ownership_detected` is true or `genai_readiness` has rows.

## Modes

Use `generate` unless the user asks for a narrower outcome:

| Mode | Outcome |
|---|---|
| `generate` | Detector Terraform, supported dashboards, reports, and verification |
| `alert-coverage-audit` | Desired/current coverage matrix plus reliability gaps; no claim about live resources without an approved inventory |
| `impact-classify` | App-down versus degraded workflow, auth, ingest, dependency, or regional impact |
| `blast-radius` | Environment, region, workflow, and dependency rollups for localization |

Missed, flapping, auto-resolved, or no-data alerts are detector-reliability
evidence. Do not ask application instrumentation to emit alert lifecycle
metrics unless the application owns those events.

## Input And Proof Gate

1. Require `<service-root>/.observe/otel-audit.json`. If it is missing, stop
   and ask the user to run `$otel-audit`.
2. Read canonical audit metadata, `current_instrumentation.metrics`, findings,
   `current_instrumentation.incident_readiness`, and `genai_readiness`.
   Findings and expected telemetry describe desired work; they are not emitted
   metric proof.
3. When present, read the bound instrumentation and verification JSON overlays
   as the authoritative downstream state. Markdown reports provide reader
   detail only. Preserve exact finding, scenario, readiness-surface, and
   telemetry-item identities.
4. A detector candidate must have an exact source-backed metric and either a
   working emitted-datapoint row with expected unit and dimensions or the
   user's explicit acceptance of that exact metric as source-only. Aggregate
   counts and similarly named signals are insufficient.
5. Missing, partial, remaining, owner-mapped, not-working, or unproven signals
   become prerequisites. Never create a detector or panel from desired-only
   telemetry, and never label a partial readiness area covered.
6. If no detector-ready metric exists but accepted evidence supports a requested
   dashboard, generate the dashboard resources plus both configure reports. If
   no resource is supported but gaps or readiness prerequisites exist, write
   both reports as a prerequisites-only `Blocked` result and do not create empty
   Terraform. If neither accepted resources nor gaps exist, stop and explain
   that detector-ready data is absent without creating artifacts.

## Classify Accepted Metrics

Read `references/detector-classification.md` completely, then apply it in this
order:

1. Route-level de-duplication: one route/operation group may share a duration
   histogram for latency, error outcome, and throughput count. Do not create
   duplicate detectors for counters already represented by that group.
2. GenAI categories when audit evidence proves GenAI ownership: latency, token
   pressure, provider, tool, model/config, workflow fanout, retrieval,
   memory/context, evaluation quality, content governance, and cost. Generic
   words such as `model`, `workflow`, `tool`, `token`, `session`, `memory`,
   `evaluation`, or `cost` do not establish GenAI ownership.
3. Incident-readiness categories: impact classification, customer impact,
   auth/edge, freshness, backpressure, dependency, capacity saturation, and
   release context.
4. Generic latency, error, throughput, and saturation categories.

Assign each accepted metric to exactly one classification row while allowing
different detector intents to read the same route-group metric with distinct
filters/aggregations. Record every skipped metric and reason. For each absent
signal, route to `$otel-instrument`; for implemented but unproven emission,
route to `$otel-verify`; for platform/provider-owned signals, name that owner.

## Generate Artifacts

When accepted resources or recorded gaps/prerequisites require configure
artifacts, read `references/terraform-templates.md`, then write both
`.observe/detectors.md` and `.observe/splunk-configure-verify.md`. The clean
no-resource branch in the input gate stops before artifact generation.

Create `.observe/terraform/variables.tf`, `terraform.tfvars.example`, and
`.gitignore` when accepted evidence supports at least one Terraform resource.
Create `.observe/terraform/detectors.tf` only when at least one accepted metric
supports a detector, and create `.observe/terraform/dashboards.tf` only when
accepted evidence supports dashboard resources. Write
`.observe/dashboards.md` alongside supported dashboard HCL, or as a report-only
desired-state specification when the user explicitly requests one. A
desired-only specification never authorizes dashboard HCL.

Preserve `.observe/terraform/.terraform.lock.hcl` after successful init.
`.gitignore` must exclude `.terraform/`, local state, and `terraform.tfvars`.
Never write credentials, token examples, raw prompts/content, or sensitive IDs
to generated files.

Generation rules:

- Use `splunk-terraform/signalfx` and provider variables; never hard-code realm
  or token values. `api_token` must be `sensitive = true`.
- Emit one `signalfx_detector` per accepted classification intent, with inline
  SignalFlow, exact metric, bounded `service.name` filtering, declared
  threshold variables, matching published/detect labels, severity, and
  `var.notification_channel`.
- Follow the templates for static versus baseline conditions, trigger/clear
  duration, severity, dashboard resource shape, and variables. Do not invent
  thresholds when the template requires review.
- Release/config dimensions are filters and correlation context, not
  standalone alerts.
- Dashboard charts may use only accepted metrics and proven dimensions. Check
  that each chart returns meaningful values with the expected unit and
  dimensions; valid SignalFlow with no useful datapoints is not a proven panel.
- Keep US/non-US realm and environment scope explicit when supplied. This
  skill does not infer live coverage without an approved live inventory.

## Report Contract

`.observe/detectors.md` is the configure decision report. It includes:

- result and source artifact provenance;
- generated detector counts and exact classifications;
- skipped metrics with reasons;
- instrumentation and GenAI prerequisites;
- alert coverage matrix for app-down/degraded impact, workflows, freshness,
  auth/edge, dependencies, capacity, region/blast radius, release/config, and
  detector reliability;
- Terraform inventory and next actions.

`.observe/dashboards.md` is a subordinate panel/filter/unit/evidence inventory,
not a second result. `.observe/splunk-configure-verify.md` is the authoritative
proof report and follows the shared report-flow contract.

## Validate

For generated Terraform, run the narrowest available checks:

1. `terraform fmt -check -recursive .observe/terraform`
2. `terraform -chdir=.observe/terraform init -backend=false -input=false`
3. `terraform -chdir=.observe/terraform validate -json`
4. When an approved detector-capable Splunk token is already available,
   `terraform -chdir=.observe/terraform plan -refresh=false -input=false`
   without saving or applying the plan.

Never use a fake token or print credentials. A 401 proves only the auth
boundary, not SignalFlow. If a user Terraform CLI config forces an unavailable
private mirror, inspect it without exposing credentials; use
`TF_CLI_CONFIG_FILE=/dev/null` only when public-registry access is allowed and
record that local-only bypass. Otherwise mark native validation `Blocked`.

Independently verify that:

- every `data(...)` metric is an accepted input and every detector filters by
  `service.name`;
- metric names, units, and complete dimensions match proof;
- all threshold variables and detect labels resolve;
- provider auth/realm are variable-backed;
- filters/group-bys contain no high-cardinality user, session, request, trace,
  prompt/content, token, or secret data;
- detectors and dashboards map to accepted evidence; every exclusion and
  prerequisite has a reason and next owner/action.

Then run:

```bash
python3 "<directory-containing-loaded-SKILL.md>/scripts/validate_configure_output.py" \
  --terraform-dir .observe/terraform \
  --detectors-report .observe/detectors.md \
  --configure-verify-report .observe/splunk-configure-verify.md \
  --audit-json .observe/otel-audit.json \
  --selection-json .observe/otel-selection.json \
  --instrumentation-json .observe/otel-instrumentation.json \
  --verify-json .observe/otel-verify.json
```

Canonical JSON authorizes metrics; Markdown remains reader-facing. A partially
supplied overlay flow is invalid. Follow `Validator Modes And Canonical Proof`
in the input contract for audit-only `--allow-source-only-metric`,
`--prerequisites-only`, and dashboard-only `--dashboard-only` with
`--dashboards-report .observe/dashboards.md`. Never override bound downstream
proof. Repair every failure; report and proof results must agree.

Result rules:

- `Pass` requires clean local validation, authenticated SignalFlow compilation
  for every detector, and meaningful dashboard value proof when dashboards are
  generated.
- `Partial` means useful local validation passed but remote compilation,
  dashboard values, or accepted proof remains unproven.
- `Fail` means generated configuration or an executed validation is invalid.
- `Blocked` means no detector or dashboard configuration could be generated or
  proven. A prerequisites-only validator can still pass its provenance and
  report-structure checks while the configure result remains `Blocked`.

Applying or publishing resources is never part of configure verification.

## Final Response

Report the configure result, detector counts by category, generated files,
skipped/unproven inputs, and direct validation evidence. Link local files with
absolute paths. The next publish workflow is `$splunk-detector-publish`; use
`$splunk-dashboard-publish` for dashboards. Mention reviewed Terraform apply
only when the user chooses Terraform-managed resources. Never direct new work
to the deprecated `$splunk-sync` alias.
