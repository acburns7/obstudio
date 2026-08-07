# Audit Schema v2 Authoring Contract

Load this reference before authoring `.observe/otel-audit.json`. It defines the
deterministic schema-v2 source contract. The audit remains a source-derived
baseline; selection, implementation, and verification results belong in bound
overlays and do not rewrite the baseline.

## Contents

- [Canonical document shape](#canonical-document-shape)
- [Stable identity and order](#stable-identity-and-order)
- [Source inventory and flow consistency](#source-inventory-and-flow-consistency)
- [Finding contract](#finding-contract)
- [Dependencies, decisions, and selections](#dependencies-decisions-and-selections)
- [Verification plan](#verification-plan)
- [Readiness consistency](#readiness-consistency)
- [Human report projection](#human-report-projection)

## Canonical Document Shape

Write JSON first. Use this shape, retaining empty arrays when a required
section has no rows:

```json
{
  "schema_version": 2,
  "kind": "otel-audit",
  "meta": {
    "audit_id": "example-service-20260717",
    "service_name": "example-service",
    "commit": "abc1234",
    "language": "go",
    "framework": "chi",
    "date": "2026-07-17",
    "status": "Partial",
    "genai_ownership_detected": false
  },
  "summary": ["Highest-impact source-backed finding first."],
  "flow": "audit -> select -> instrument -> verify -> configure/dashboard -> publish",
  "evidence": [
    {"check": "Manifest", "finding": "Go module", "source": "go.mod"},
    {"check": "Entry point", "finding": "HTTP service", "source": "main.go"},
    {"check": "Route source", "finding": "GET /health", "source": "main.go:42"},
    {"check": "Runtime/startup", "finding": "Go test runner", "source": "go.mod"},
    {"check": "GenAI ownership", "finding": "No", "source": "source scan"}
  ],
  "routes": [{"method": "GET", "path": "/health"}],
  "signal_flow": {
    "component_flow_map": "main.go [SOURCE-COVERED] -> handler [GAP: HTTP latency]"
  },
  "current_instrumentation": {
    "spans": [{"name": "GET /health", "source": "otelhttp", "type": "auto"}],
    "metrics": [],
    "logs": [],
    "incident_readiness": []
  },
  "genai_readiness": [],
  "findings": [
    {
      "id": "OTEL-001",
      "title": "HTTP latency lacks route-level proof",
      "severity": "high",
      "priority": "required",
      "effort": "small",
      "status": "proposed",
      "area": "HTTP latency",
      "gap": "Source shows no route latency metric or span timing.",
      "impact": "Operators cannot isolate slow routes.",
      "product_outcome": "Operators can filter route traces and latency views.",
      "required_fix": "Add HTTP server instrumentation and stable route attributes.",
      "instrument_mode": "default",
      "verification_scenarios": ["http.health.success"],
      "dependencies": [],
      "evidence": ["main.go:42"],
      "acceptance_criteria": ["One server span has http.route=/health."],
      "constraints": ["Keep route values low cardinality."],
      "expected_telemetry": [
        {
          "type": "span",
          "name": "GET /health",
          "attributes": ["http.route"],
          "product_view": "Trace waterfall and route filtering"
        }
      ],
      "follow_up_actions": ["Select this finding for $otel-instrument."]
    }
  ],
  "verification": {
    "environments": [
      {
        "id": "go.local",
        "surface": "example service",
        "config_evidence": "go.mod",
        "runner": "go test ./...",
        "scope": "module",
        "prerequisites": "none"
      }
    ],
    "scenarios": [
      {
        "id": "http.health.success",
        "trigger": "GET /health",
        "entrypoint": "main.go:42",
        "expected_signals": "GET /health span with http.route",
        "proof_level": "full runtime",
        "acceptance_criteria": "The route-named server span is emitted.",
        "environments": ["go.local"]
      }
    ]
  },
  "anti_patterns": [],
  "recommendation": ["Run $otel-instrument with selected executable finding IDs."]
}
```

The required top-level fields are `schema_version`, `kind`, `meta`, `summary`,
`flow`, `evidence`, `routes`, `signal_flow`, `current_instrumentation`,
`genai_readiness`, `findings`, `verification`, `anti_patterns`, and
`recommendation`. Add `scan_blockers` only when `meta.status` is `Blocked`; a
blocked audit needs at least one structured blocker, and other statuses must
not carry blockers.

Use `Pass`, `Partial`, or `Blocked` for `meta.status`. `Pass` has no findings;
`Partial` has at least one finding. Set `meta.genai_ownership_detected` to a
boolean and include exactly one matching `GenAI ownership` evidence row with a
`Yes` or `No` finding. Populate `genai_readiness` only when that boolean is
true. Always include evidence rows for `Manifest`, `Entry point`, `Route
source`, and `Runtime/startup`.

## Stable Identity and Order

- Give the audit, findings, environments, scenarios, decisions, and decision
  options stable IDs. IDs start with a letter and use only letters, digits,
  dots, underscores, or hyphens.
- Assign finding IDs such as `OTEL-001`, `OTEL-002`, in canonical priority
  order: `required`, then `recommended`, then `deferred`. Preserve authored
  order within a priority. Priority orders work; it does not authorize scope.
- Keep one stable, unique human-readable `area` per finding. Group evidence for
  one remediation theme, but split work with different owners, instrument
  modes, or acceptance criteria.
- Use `status: proposed` for newly discovered gaps. The canonical audit records
  the current source baseline; later lifecycle changes belong in overlays.
- Keep dependencies acyclic and directed from executable work to the finding
  that is its prerequisite. Every referenced finding ID must exist.

## Source Inventory and Flow Consistency

`current_instrumentation` owns source inventory, not proposed work or runtime
proof. Record each exact signal separately:

- `spans`: one row per span with `name`, `source`, and `type`.
- `metrics`: one row per metric with `name`, `source`, and `type`.
- `logs`: one row per integration with `integration`, `source`, and `detail`.
- `incident_readiness`: one row per telemetry-scoped area with `area`,
  `status`, `evidence`, `required_signals`, and `impact`.

Do not replace exact rows with grouped descriptions such as "HTTP spans" or
"runtime metrics." Extra source-backed fields may supplement a row but never
replace its required fields.

In `signal_flow.component_flow_map`, use only `[SOURCE-COVERED]` and
`[GAP: <area>]`. Every gap marker uses the exact `findings[*].area`, and every
finding area appears in at least one marker. Repeat an area only when one
finding spans multiple components; do not duplicate the finding.

## Finding Contract

Every finding contains all of these fields:

- `id`, `title`, `severity`, `priority`, `effort`, `status`, and unique `area`.
- Source-backed `gap`, human `impact`, and concise future-state
  `product_outcome` without claiming runtime proof.
- Exact `required_fix`, `instrument_mode`, `verification_scenarios`, and
  `dependencies`.
- Non-empty `evidence`, `acceptance_criteria`, `expected_telemetry`, and
  `follow_up_actions`; `constraints` may be empty.

Use only these enum values:

- `severity`: `critical`, `high`, `medium`, `low`, or `info`.
- `priority`: `required`, `recommended`, or `deferred`.
- `effort`: `small`, `medium`, `large`, or `decision`.
- `instrument_mode`: `default`, `fix all`, `manual decision`, or
  `external follow-up`.
- New finding `status`: `proposed`.

Each `expected_telemetry` item has `type`, `name`, `attributes`, and
`product_view`. Use only `span`, `metric`, `log`, `resource`, or
`configuration` for `type`. Name the exact signal or configuration, bounded
attributes, and the view an operator should gain.

Make `required_fix` specific to every required OTel signal, attribute,
resource, exporter, or configuration owner. Do not use vague instructions such
as "improve telemetry." Map runnable work to one or more existing scenario
IDs. Give every finding at least one concrete review or instrumentation next
step; do not direct the audit user to generic `$otel-verify` work.

When a fix changes an emitted metric, span, resource, log, exporter, dashboard,
or detector contract, state whether it is additive or breaking. Preserve safe
aliases by default. If an unsafe high-cardinality field must be removed, name a
bounded replacement and require migration of consumers that use the old field.

## Dependencies, Decisions, and Selections

`default` and `fix all` are executable. `manual decision` and `external
follow-up` are prerequisites only and cannot enter executable scope. In schema
v2, every non-executable finding must be in the transitive dependency closure
of at least one executable finding. Put app-owned implementation in a separate
executable finding that depends on the prerequisite.

A `manual decision` finding has:

- A concrete `decision_owner` and a telemetry-specific `decision_question`.
- Two or three `decision_options`, each with a unique stable `id`, concise
  `label`, concrete `outcome`, and `unlocks` list.
- Pairwise-disjoint unlock sets containing only executable findings that
  directly depend on the decision. An option may unlock no work.

For mutually exclusive implementation branches, author one executable finding
per branch and place each branch only in its matching option's `unlocks`. Do
not expose mutually exclusive branches as simultaneous independent gaps.

An `external follow-up` finding has a concrete `external_owner` and exact
`external_requirement` that says what OTel telemetry or proof the owner must
emit, export, configure, provide, supply, expose, prove, or verify. Its
`required_fix` must contain exactly that external requirement, without hidden
service implementation.

Do not create non-executable findings merely for product behavior, billing,
cost, safety policy, content governance, or external business context. Keep
that material in readiness context unless it blocks concrete executable OTel
work.

When `review_selection` or `.observe/otel-selection.json` is present:

- Bind it to `meta.audit_id` and the SHA-256 digest of normalized canonical
  audit JSON.
- `requested_ids` is the explicit reviewer-selected executable list.
- `approved_ids` is the dependency-closed executable scope in canonical audit
  order; the name does not imply human approval.
- `decision_answers` is a separate canonical-audit-order list of
  `{finding_id, option_id}` entries. A selection carrying it uses schema v2.
- Never put a manual or external finding ID in either executable ID list.
- An answer unlocks only the matching executable branch and never selects it.
  Reject unauthored answers, unanswered decision dependencies, or branch work
  outside the chosen option's unlocks.
- Preserve a valid answer that unlocks no work with empty executable lists.
  Do not invent IDs. If an answer changes, remove now-invalid requested and
  dependency-closed work.

## Verification Plan

`verification.environments` defines reusable source-backed profiles. Each row
has a stable `id`, `surface`, `config_evidence`, `runner`, `scope`, and
`prerequisites`.

`verification.scenarios` defines source-derived acceptance plans. Each row has
a stable `id`, `trigger`, existing `entrypoint`, exact `expected_signals`,
`proof_level`, `acceptance_criteria`, and one or more `environments`. Use only
`focused call-site`, `full runtime`, or `either` for `proof_level`.

Every scenario environment ID must exist. Every finding
`verification_scenarios` ID must exist. Create a scenario for every
telemetry-distinct success, failure, timeout, startup, shutdown, worker,
dependency, stream, tool, or retrieval path. Combine paths only when expected
telemetry is identical. This plan never claims that runtime emission passed.

## Readiness Consistency

Treat readiness arrays as canonical machine context, not a second finding
ledger.

- Every telemetry-scoped `partial`, `missing`, or `owner-mapped`
  `current_instrumentation.incident_readiness` row has an unresolved finding
  with an identical `area` and at least one verification scenario. A `covered`
  row cannot have an unresolved same-area finding.
- Each `genai_readiness` row has `surface`, `status`, `evidence`,
  `required_signals`, `owner`, `acceptance_criteria`, and `impact`. A `partial`
  or `missing` row has an unresolved finding whose `area` exactly matches its
  `surface`, plus mapped scenarios. A `covered` or `owner-mapped` row cannot
  have an unresolved same-area finding.
- A row is telemetry-scoped only when `required_signals` names service-owned
  OTel telemetry or configuration. Product contracts, cost ownership, safety
  policy, governance rules, and external business prerequisites stay context.

## Human Report Projection

The canonical JSON is the only authored source. Generate `.observe/otel.html`
with `finalize-audit`; repair JSON when validation fails and never patch the
generated HTML.

Follow the shared report-flow contract for layout. The HTML presents exactly
one findings list ordered `required`, `recommended`, then `deferred`, preserving
canonical order within each priority. It may summarize the baseline, but it
does not render `signal_flow.component_flow_map`, raw verification scenario
IDs, full current-instrumentation inventories, or Incident/GenAI readiness
ledgers as peer action sections. Those fields remain canonical machine context
for downstream selection, instrumentation, and verification.
