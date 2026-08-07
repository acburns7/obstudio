---
name: splunk-detector-publish
description: >-
  Compare local signalfx_detector Terraform with a complete live Splunk
  Observability detector inventory, then create only explicitly confirmed
  gaps. Use for $splunk-detector-publish, syncing detectors, finding missing
  detectors or monitors, or pushing detector gaps to Splunk. Produces a
  fail-closed COVERED/GAP/UNCERTAIN diff and .observe/detector-sync.md ledger.
metadata:
  author: otel-studio
  version: 0.3.3
  category: observability
---

# Publish Splunk Detectors

Compare `.observe/terraform/detectors.tf` with live Splunk Observability Cloud
detectors. Publish only verified, explicitly confirmed gaps. Never modify or
delete an existing detector.

## Required references

Resolve these paths from this skill directory and read them before the relevant
step:

- `../references/terraform-normalization.md` before parsing SignalFlow.
- `../references/splunk-api.md` before authentication or any REST request.
- `../references/coverage-decision-tree.md` and
  `references/coverage-model.md` before classifying detectors.
- `../references/ledger-template.md` before writing the ledger.

The references own detailed algorithms, wire formats, examples, and error
handling. This file owns the safety gates and execution order.

## Safety contract

- Require a complete live inventory before assigning `COVERED` or `GAP`.
- If any required fetch fails or the inventory may be incomplete, classify
  every local detector `UNCERTAIN` and make no write request. Confirmation
  cannot override this gate.
- Never send `POST /v2/detector` before an explicit user confirmation based on
  the current successful inventory.
- Create only confirmed `GAP` rows. Never create `COVERED`, `UNCERTAIN`, or
  AutoDetect-advisory rows.
- Keep `SPLUNK_ACCESS_TOKEN` secret: read it only from the environment, send it
  only as `X-SF-Token`, and never print, persist, or place it in a prompt.
- Perform creates sequentially. Record a concrete, non-empty Reason for every
  verdict and result.

## Workflow

### 1. Gate on the local specification

Work from the target repository root. Require
`.observe/terraform/detectors.tf`; if absent, stop and tell the user to run
`$splunk-configure`. Read `.observe/detectors.md` when present for intent and
classification rationale. A prior `.observe/detector-sync.md` is resume
evidence only; never use it instead of fresh live state.

Parse every `signalfx_detector` resource. Capture its HCL label, resolved name,
`program_text`, first `data(...)` metric, resolved service filter, and every
rule's severity, `detect_label`, and notifications. Reject malformed HCL.

Resolve variables from `terraform.tfvars`, then `*.auto.tfvars`, then
`terraform.tfvars.example`, then defaults in `variables.tf`. Prompt rather than
guess when a required value remains unresolved.

### 2. Normalize local SignalFlow

Follow `../references/terraform-normalization.md` once during parsing and use
the normalized value for both comparison and creation:

- Dedent `<<-EOF` heredocs and strip blank edges.
- Resolve every `${var.*}`, including service, threshold, stddev, percentile,
  and window values. Do not continue to creation with any unresolved token.
- Map HCL `program_text` to REST `programText` and `detect_label` to
  `detectLabel`.

An indented line or unresolved interpolation causes an HTTP 400 SignalFlow
parse error. A 400 "Unrecognized field" instead indicates snake_case leaked
into the REST body.

### 3. Resolve credentials and fetch live state

If the user or sandbox forbids network access, do not read credentials or make
a request. Parse and normalize locally, then follow the incomplete-inventory
path below.

For a permitted live run, follow `../references/splunk-api.md`. Require
`SPLUNK_ACCESS_TOKEN`. Resolve the realm from a non-empty `SPLUNK_REALM`,
otherwise from the read-only `observer_splunk_connection_realm` result. Stop if
either token or realm is unavailable. Keep the realm paired with the token and
report only the realm and its source.

Fetch the full org inventory with paginated `GET /v2/detector`, deduplicated by
ID. An HTTP 500 page may be skipped only to collect later diagnostic results;
any skipped offset makes the inventory incomplete. Surface every other error.
Fetch `GET /v2/detector/{id}` when list data omits or truncates `programText`.

Treat the inventory as complete only when the reference fetch procedure ends
successfully with no skipped page and every candidate needed for comparison has
usable data. A successful complete fetch returning zero detectors is a real
empty inventory. An auth, network, parse, skipped-page, HTTP, detail-fetch, or
completeness failure is not an empty inventory.

### 4. Classify every local detector

Apply `references/coverage-model.md` and record every criterion that fired:

- `COVERED`: one live Standard detector (`detectorOrigin != "AutoDetect"`)
  contains the same metric and the same resolved service filter. Treat
  `service.name` and `sf_service` as equivalent keys. Record its name, ID,
  metric, filter, and origin match.
- `GAP`: after a complete inventory, no live Standard detector fully or
  partially matches the metric and service scope. Record exactly what was
  searched and found absent.
- `UNCERTAIN`: a candidate partially matches but its service filter is absent,
  wildcarded, uses another key, or is otherwise ambiguous.
- `AutoDetect advisory`: report relevant org-wide AutoDetect latency/error
  detectors separately. They never count as service-specific coverage and
  never change the primary verdict.

If the live inventory is failed or incomplete, override the candidate results:
all local detectors are `UNCERTAIN`, each Reason states that absence or coverage
cannot be verified, and no POST is allowed. Always include an AutoDetect
Advisory section; state that it could not be evaluated when inventory is
unavailable.

### 5. Show the diff and gate writes

Render this structure before any write request:

```markdown
## Detector Publish Diff - <service>

Realm: `<realm>` (source: `<SPLUNK_REALM|Observer>`)
Inventory: `<complete|incomplete: reason>`

### COVERED (N)
| Local Spec | Metric | Live Detector | Reason |

### GAP (N)
| Local Spec | Metric | Severity | Reason |

### UNCERTAIN (N)
| Local Spec | Metric | Candidate | Reason |

### AutoDetect Advisory (N)
| Local Spec | Metric | AutoDetect Detector | Reason |
```

Every row must have a non-empty Reason naming the detector, metric, resolved
service filter, and exact live-inventory basis.

With an incomplete inventory, show all rows under `UNCERTAIN`, state that no
write is allowed, write the ledger, and stop without a confirmation prompt or
POST payload.

With a complete inventory:

- If no `GAP` or `UNCERTAIN` remains, state that all specs are covered, write
  the ledger, and do not ask for confirmation.
- Otherwise summarize how many verified GAPs would be created and how many
  UNCERTAIN rows need review. Ask `Confirm creation of these GAP rows? (yes/no)`.
  A preview request may show redacted payloads, but is not confirmation.
- Stop on no, ambiguity, or silence. A prior confirmation does not authorize a
  later run with a newly fetched inventory.

### 6. Create only confirmed GAPs

For each confirmed GAP, build a `POST /v2/detector` body containing:

- resolved `name`;
- normalized `programText`;
- `rules[]` with `severity`, `detectLabel`, `notifications`, and
  `disabled: false`;
- a description citing the local HCL label.

Use the confirmed realm and the status rules in
`../references/splunk-api.md`:

- HTTP 200 or 201: record the returned ID, name, and detector deep link.
- HTTP 409 or duplicate name: refresh the complete detector inventory and
  candidate details, then rerun the full metric + resolved service filter +
  Standard-origin classification. Reuse its ID only for a fresh `COVERED`
  verdict. Mark a partial, ambiguous, or divergent candidate `UNCERTAIN`; never
  reuse by name alone or retry the same POST.
- HTTP 401 or 403: stop; report invalid credentials or missing write scope.
- HTTP 400: distinguish field casing from unnormalized SignalFlow; record the
  failure and do not retry an unchanged payload.
- Any other error: record it, continue with remaining confirmed GAPs, and list
  every failure in the final response.

Update the ledger after each create result so a partial run remains auditable.

### 7. Persist the resume ledger

Write or overwrite `.observe/detector-sync.md` for every classified run,
including all-covered, incomplete-inventory, and partial-create runs. Follow
`../references/ledger-template.md` and include:

- date, local spec path, resolved service filter, realm, and inventory status;
- summary counts for `COVERED`, `CREATED`, `FAILED`, `UNCERTAIN`, and
  `AutoDetect Advisory`;
- one row per local spec with metric, status, detector ID/link when known, and a
  concrete non-empty Reason;
- create errors without credentials, tokens, or raw authorization headers.

On rerun, refetch live state and reclassify every spec. The ledger supports
resume and audit but never proves current coverage. Fresh diffing plus HTTP 409
handling provides idempotency.

## Final response

Report exactly the outcome supported by this run:

```markdown
## Detector Publish <Complete|Stopped|Partial> - <service>

| Status | Count |
|--------|-------|
| Already covered | N |
| Created | N |
| Failed | N |
| Uncertain | N |
| AutoDetect advisory | N |

Ledger: `.observe/detector-sync.md`
```

State the realm, inventory status, and whether any write occurred. List failed
GAPs with sanitized errors. For `UNCERTAIN`, name the required review or say to
rerun after a complete live fetch; never imply that an incomplete run found
real gaps.
