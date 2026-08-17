---
name: splunk-dashboard-publish
description: >-
  Compare local Splunk dashboard Terraform with a complete live Splunk
  Observability Cloud inventory, then create or update only explicitly confirmed
  gaps. Use for $splunk-dashboard-publish, "sync dashboards",
  "check which dashboards are missing", "create missing dashboards", or
  "push dashboard gaps to Splunk". Produces a fail-closed
  COVERED/GAP/UNCERTAIN diff and a resumable .observe/dashboard-sync.md ledger.
metadata:
  author: otel-studio
  version: 0.1.3
  category: observability
---

# Publish Splunk Dashboards

Compare `.observe/terraform/dashboards.tf` with live dashboard groups,
dashboards, and charts. Publish only verified, explicitly confirmed gaps in
group -> chart -> dashboard order.

## Required references

Resolve these paths from this skill directory and read them before the relevant
step:

- `../references/terraform-normalization.md` before parsing SignalFlow.
- `../references/splunk-api.md` before authentication or any REST request.
- `../references/coverage-decision-tree.md` and
  `references/dashboard-coverage-model.md` before classification.
- `../splunk-dashboard/references/dashboard-templates.md` before mapping HCL
  chart resources to REST chart types and payloads.
- `../references/ledger-template.md` before writing the resume ledger.

The references own detailed algorithms, payload examples, and match criteria.
This file owns the safety gates and execution order.

## Safety contract

- Require a complete live inventory before assigning `COVERED` or `GAP`.
- If any required fetch fails or any inventory may be incomplete, mark every
  local group, dashboard, and chart **UNCERTAIN** and send no `POST`, `PUT`, or
  `DELETE`. Confirmation cannot override this gate.
- Show a current, realm-bound plan before any writes. Require explicit user
  confirmation of that exact plan; stale or ambiguous confirmation is invalid.
- Mutate only confirmed `GAP` rows and confirmed orphan cleanup. Never mutate an
  `UNCERTAIN` row.
- Keep `SPLUNK_ACCESS_TOKEN` secret: read it only from the environment, send it
  only as `X-SF-Token`, and never log, print, persist, or place it in a prompt.
- Record a concrete, non-empty Reason on every row. A generic note such as
  "matched live dashboard" is insufficient.

## Workflow

### 1. Load and normalize local state

Work from the target repository root. Require
`.observe/terraform/dashboards.tf`; if absent, stop and tell the user to run
`$splunk-dashboard`. Read `.observe/dashboards.md` when present for intent. Read
`.observe/dashboard-sync.md` only as resume evidence; never treat it as current
live state.

Parse the complete three-level graph:

1. Each `signalfx_dashboard_group`: name and description.
2. Each `signalfx_dashboard`: name, description, `dashboard_group`, and each
   chart's `chart_id`, column, row, width, and height.
3. Each `signalfx_*_chart`: HCL label, name, chart type, `program_text`, and
   type-specific fields such as text markdown.

Reject malformed HCL. Resolve variables from `terraform.tfvars`, then
`*.auto.tfvars`, then `terraform.tfvars.example`, then `variables.tf` defaults;
prompt rather than guess.

Follow `../references/terraform-normalization.md`: dedent every `<<-EOF`
heredoc, strip blank edges, and resolve every `${var.*}`. Carry the normalized
SignalFlow through comparison and creation. Map HCL `program_text`, `chart_id`,
and `dashboard_group` to REST `programText`, `chartId`, and `groupId`.

Preflight payloads locally. Use the chart mapping in the dashboard templates:
`signalfx_time_chart` maps to `TimeSeriesChart`; other resource types use their
documented REST types. Include `packageSpecifications: "signalfx"`. Only
`TimeSeriesChart` accepts `defaultPlotType`; a text chart uses
`options.markdown` and omits `programText`. Reject unresolved interpolation,
invalid placement, and `.last()` without a window before planning a write.

### 2. Resolve auth and fetch a complete live inventory

If the user or sandbox forbids network access, do not read credentials or make
a request. Finish local parsing, then take the incomplete-inventory path below.

For a permitted live run, follow `../references/splunk-api.md`. Require
`SPLUNK_ACCESS_TOKEN`. Resolve realm from a non-empty `SPLUNK_REALM`, otherwise
from the read-only `observer_splunk_connection_realm` result. Stop if token or
realm is unavailable. Report only the realm and whether it came from the
environment or Observer.

Fetch and deduplicate the full inventories from `GET /v2/dashboardgroup`,
`GET /v2/dashboard`, and `GET /v2/chart`; fetch `GET /v2/chart/{id}` whenever
detail is required to compare `programText` and `options.type`. Use the shared
paginated procedure. An HTTP 500 page may be skipped only to collect later
diagnostic results; any skipped offset makes the inventory incomplete. Surface
every other error.

Call the inventory complete only when pagination terminates with no skipped page
and every group, dashboard, chart, and prior-ledger orphan needed for
classification has usable data. A successful complete fetch returning zero
objects is a real empty inventory. Auth, network, parse, skipped-page, HTTP,
detail-fetch, or completeness failure is not an empty inventory.

### 3. Classify at all three levels

Apply `references/dashboard-coverage-model.md` and record every criterion that
fired:

- Group: `COVERED` on an exact live group-name match; otherwise `GAP` only after
  a complete inventory.
- Dashboard: compare within the matched group by name and panel set. A complete
  match is `COVERED`; no same-named dashboard is `GAP`; conflicting live panels
  make it `UNCERTAIN`. A strict live subset leaves the dashboard `COVERED` and
  its absent local panels as chart-level `GAP`s.
- Chart: require one live chart matching metric, resolved service filter, and
  chart type. Treat `service.name` and `sf_service` as equivalent filter keys.
  A full match is `COVERED`, confirmed absence is `GAP`, and a partial or
  ambiguous match is `UNCERTAIN`.

A concrete covered reason looks like: `metric X + filter service.name=Y + type
time_series all matched live chart C-456`. GAP reasons state what a complete
inventory proved absent. UNCERTAIN reasons name the divergent or unavailable
criterion.

If inventory is failed or incomplete, override all candidate results: mark
every local group, dashboard, and chart **UNCERTAIN**, explain that complete
live inventory is unavailable and absence cannot be verified, and prohibit all
writes, including orphan cleanup.

### 4. Build an idempotent plan and gate writes

Render a diff before any write with realm, realm source, inventory status, and a
plan ID derived from the normalized local spec, live IDs/state, and proposed
actions:

```markdown
## Dashboard Publish Diff - <service>
| Level | Local object | Live target | Status | Planned action | Reason |
```

Include every group, dashboard, and chart. Every row has a non-empty Reason.
List orphan reuse or deletion as separate planned actions with IDs and evidence.

- Incomplete inventory: show all rows as `UNCERTAIN`, write the ledger, and stop
  without create counts, write payloads, or a confirmation prompt.
- Complete inventory with no GAP, UNCERTAIN, or orphan action: report
  all-covered, write the ledger, and stop.
- Otherwise, summarize verified GAPs, UNCERTAIN rows, and orphan actions. Ask
  `Confirm plan <id> for realm <realm>? (yes/no)`. Stop on no, ambiguity, or
  silence. A preview or earlier run's answer is not confirmation.

Refetch and re-plan if the realm, local spec, target IDs, or intended actions
change. This plan binding, fresh inventory on every run, and HTTP 409 recovery
make retries idempotent.

### 5. Apply the confirmed plan chart-first

Apply sequentially only after a complete inventory and exact-plan confirmation:

1. Reuse a `COVERED` group ID or create each GAP group with
   `POST /v2/dashboardgroup` using name and description.
2. Reuse a verified matching orphan chart ID or create each GAP chart with
   `POST /v2/chart`. Use name, normalized `programText` or text markdown,
   type-correct `options`, and `packageSpecifications`. Persist each returned
   chart ID immediately in `.observe/dashboard-sync.md` before continuing.
3. For a GAP dashboard, send `POST /v2/dashboard` with name, description,
   `groupId`, and placements referencing the collected `chartId` values.
4. For a COVERED dashboard with chart-level GAPs, refetch the dashboard, preserve
   its existing `charts[]`, append only confirmed new placements, and send the
   merged object with `PUT /v2/dashboard/{id}`. Never recreate that dashboard.

Do not create or update a dashboard unless every chart ID required by that
planned mutation is available. Persist the ledger after every mutation.

Use shared status handling:

- HTTP 200/201: record the resulting ID and deep link.
- HTTP 409/duplicate: refresh the complete relevant inventory and required
  details, then rerun the full group, dashboard, or chart structural
  classification. Reuse the ID only for a fresh `COVERED` verdict. Mark partial,
  ambiguous, or divergent content `UNCERTAIN` and stop dependent writes; never
  reuse by name alone.
- HTTP 401/403: stop all further writes and report invalid auth or missing scope.
- HTTP 400: distinguish REST field casing from SignalFlow normalization; record
  the failure and never retry an unchanged payload.
- PUT 404 or another state-changing race: stop, refresh inventory, re-plan, and
  obtain new confirmation before changing the action.
- Other failures: record sanitized errors, skip dependent mutations, and report
  a partial run.

### 6. Recover orphan charts safely

Treat prior-ledger orphan IDs as hints. With complete live state, verify that an
ID exists, is attributable to this ledger, and is not referenced by a live
dashboard. Reuse it only when name plus normalized SignalFlow fingerprint (or
metric + filter + type) matches a planned GAP chart.

If dashboard POST/PUT fails after chart creation, immediately record those chart
IDs as orphan candidates under orphan recovery. On dashboard POST 409, persist
every chart created earlier in the run before conflict recovery. After the
dashboard refetch, annotate whether it references each candidate and retain
unreferenced charts under the orphan-recovery contract. Never silently abandon
them or turn the confirmed POST into an implicit PUT.

Delete an unmatched chart with `DELETE /v2/chart/{id}` only when complete live
inventory proves it is an unreferenced, ledger-owned orphan and the exact delete
was in the explicitly confirmed current plan. Otherwise classify the cleanup
`UNCERTAIN` and leave it untouched. Never delete before inventory completion or
confirmation; a failed refresh stops all further writes.

### 7. Persist and resume

Write or overwrite `.observe/dashboard-sync.md` for every classified run,
including all-covered, incomplete, declined, and partial runs. Follow
`../references/ledger-template.md` and include date, spec, resolved service,
realm/source, inventory status, plan ID, summary counts, and separate group,
dashboard, chart, and orphan tables. Store IDs, deep links, results, sanitized
errors, and concrete Reasons; never store credentials or authorization headers.

On rerun, refetch and reclassify everything. The ledger preserves progress and
orphan provenance but never proves current coverage or authorizes another write.

## Final response

Report the realm/source, inventory status, plan ID, confirmation result, and
whether writes occurred. Give counts for already covered, created, updated,
failed, uncertain, reused orphans, and deleted orphans; link the ledger path.
List sanitized failures and orphan IDs requiring recovery. For `UNCERTAIN`, name
the required review or instruct the user to rerun after a complete live fetch.
Never claim a failed or incomplete run found real gaps.
