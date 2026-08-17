# Splunk Observability Cloud REST API — auth, paginated fetch, status handling

Shared reference for every skill that talks to the Splunk Observability Cloud
REST API directly: `splunk-detector-publish`, `splunk-dashboard-publish`, and any
future publish skill. An optional read-only Observer MCP call may supply the
default realm. The auth, pagination, and HTTP-status rules are identical
regardless of which object type (detector, dashboard, chart, group) is being
synced — this file is the single source of truth for them.

## Auth and realm resolution

Read the access token from the environment — never hard-code it, never log it:

| Variable | Purpose |
|---|---|
| `SPLUNK_ACCESS_TOKEN` | Org access token; sent as the `X-SF-Token` request header |
| `SPLUNK_REALM` | Optional fallback realm (e.g. `lab0`, `us0`, `us1`, `eu0`) |

If `SPLUNK_ACCESS_TOKEN` is missing, **stop** and tell the user to set it.
Then resolve the realm in this order:

1. Use a non-empty `SPLUNK_REALM` when it is set. This keeps the environment
   token and environment realm paired.
2. Otherwise, if the Observer MCP tools are available, call
   `observer_splunk_connection_realm` and use its non-empty `realm`. This is the
   region stored with the active Splunk Observability Cloud connection.
3. If neither source provides a realm, **stop** and ask the user to set
   `SPLUNK_REALM` or connect Splunk Observability Cloud in SOS.

The realm tool returns only the non-secret region. It is not a token source.
Direct REST calls always use `SPLUNK_ACCESS_TOKEN` from the environment.

Before any create, update, or delete, include the resolved realm in the
confirmation and state whether it came from the connected SOS destination or
`SPLUNK_REALM`.

Base API URL: `https://api.${realm}.signalfx.com`
App (browser) URL for deep links: `https://app.${realm}.signalfx.com`

Treat `SPLUNK_ACCESS_TOKEN` as a secret: never echo it, never write it into a
report/ledger, never place it in prompt context or a Terraform `*.tfvars` example
with a real value. In Terraform the matching variable is always
`sensitive = true`.

## Paginated fetch - diagnostic skip-on-500, fail-closed coverage

The Splunk list endpoints (`GET /v2/detector`, `GET /v2/dashboard`,
`GET /v2/dashboardgroup`, `GET /v2/chart`) share a known server-side bug: some
`offset` values return **HTTP 500**. Continue past a 500 only to collect
diagnostic evidence from later pages. A skipped page means objects may be
missing, so the inventory is incomplete even if later pages succeed. An
incomplete inventory must not assign COVERED or GAP and must not authorize any
write. Track every skipped offset explicitly:

```python
import urllib.request, urllib.error, json

token = "<SPLUNK_ACCESS_TOKEN>"   # from env; never logged
realm = "<resolved realm>"
base  = f"https://api.{realm}.signalfx.com/v2/<object>"   # detector|dashboard|dashboardgroup|chart

limit = 50          # keep small; large limits hit the 500 bug more often
offset = 0
results = []
seen_ids = set()
skipped_offsets = []    # any entry makes this inventory incomplete
consecutive_empty = 0   # counts empty-batch pages (real end-of-list signal)
consecutive_500 = 0     # counts 500 pages separately — does NOT contribute to
                        # the empty-page stop condition; only a long 500 run
                        # (likely auth masquerading as 500) triggers its own stop

while consecutive_empty < 5 and consecutive_500 < 10:
    url = f"{base}?limit={limit}&offset={offset}"
    req = urllib.request.Request(url, headers={"X-SF-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 500:
            # Advance only to collect diagnostic evidence from later pages.
            # This page is missing, so the result can never authorize a write.
            skipped_offsets.append(offset)
            # Do NOT increment consecutive_empty here — a 500 is not an empty
            # page; counting it as one would stop pagination prematurely when
            # valid pages follow a run of 500-returning offsets.
            offset += limit
            consecutive_500 += 1
            continue
        raise RuntimeError(f"Splunk API error {e.code}: {e}") from e
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:
        raise RuntimeError(f"Failed to fetch from Splunk: {e}") from e

    consecutive_500 = 0  # a successful response resets the 500 streak
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise RuntimeError("Splunk list response has no usable results array")
    batch = data["results"]
    if not batch:
        consecutive_empty += 1
        offset += limit
        continue

    consecutive_empty = 0
    for obj in batch:
        if obj["id"] not in seen_ids:
            seen_ids.add(obj["id"])
            results.append(obj)
    offset += limit

inventory_complete = consecutive_empty >= 5 and not skipped_offsets
if not inventory_complete:
    # Keep results only as diagnostics. The calling publish skill must classify
    # every local object UNCERTAIN and send no POST, PUT, or DELETE request.
    inventory_failure_reason = (
        f"incomplete pagination; skipped offsets={skipped_offsets}"
    )
```

Only HTTP 500 may be skipped for continued diagnostic collection. Every other
status is surfaced as a failed fetch. Do **not** wrap the loop in a bare
`except Exception` that swallows everything - that would hide auth and parse
failures and silently under-report live objects. Any skipped or failed page
makes the inventory incomplete; classify all local objects UNCERTAIN and send
no write request.

Only a complete pagination run with no skipped page may prove that the org has
zero objects of that type. Then, and only then, the empty live list may support
GAP classification.

## HTTP status handling on create (POST)

`urllib` raises `HTTPError` for any non-2xx response, so branch on the status
code rather than letting it raise blindly:

| Status | Meaning | Action |
|---|---|---|
| 200 / 201 | Created | Record the returned `id`, `name`, and app deep link in the ledger |
| 409 / duplicate-name | Diff/create race | Refetch the existing object and rerun the full object-specific structural classification below; never reuse by name alone |
| 400 "Unrecognized field" | Field-name casing mismatch | Check camelCase wire names (`programText`, `detectLabel`, `chartId`, `groupId`) vs HCL snake_case |
| 400 SignalFlow parse/syntax | `program_text` was sent un-normalized | Re-normalize per `terraform-normalization.md`: dedent `<<-EOF`, resolve every `${var.*}` |
| 403 | Token lacks write scope | **Stop** and tell the user; do not retry |
| 401 | Token invalid/expired | **Stop** and tell the user |
| other | Unexpected | Record the failure, continue with remaining items, report all failures in the summary |

Create items sequentially (not in parallel) so progress is visible and any
failure is attributable to a specific local spec.

### HTTP 409 race reclassification

A name match is not proof of structural coverage. On HTTP 409:

1. Refresh the complete relevant object inventory with the fail-closed
   pagination procedure, collect every current candidate by name, and fetch any
   detail needed by the object-specific coverage model.
2. Rerun the same full classification used before confirmation: detector
   metric + resolved service filter + Standard origin; chart metric + filter +
   type; dashboard group + name + complete panel/chart structure.
3. Reuse the existing ID only when that fresh classification is `COVERED`.
   Record the matched ID and every criterion in the ledger.
4. Classify a partial, ambiguous, or divergent candidate `UNCERTAIN`. Do not
   retry the conflicting POST and stop every write that depends on that object.
   Continue only mutations that are independent and still match the confirmed
   plan.
5. If a dashboard POST races after charts were created, immediately persist
   every chart created earlier in the run as an orphan candidate. After the
   dashboard refetch, record which candidates it references and keep each
   unreferenced chart under the orphan-recovery contract. Do not turn the
   confirmed POST into an implicit PUT, and do not silently attach or delete
   those charts. A changed attach or cleanup action requires a fresh inventory,
   a new plan, and explicit confirmation.

HTTP 409 handling never bypasses the complete-inventory gate. If the conflict
refetch or any required detail fetch fails, the refreshed inventory is
incomplete and no further write is allowed.

## Updating an existing dashboard (adding a chart to a COVERED dashboard)

When a dashboard is COVERED but contains one or more chart-level GAPs, use
`PUT /v2/dashboard/{id}` to add the new chart(s) rather than recreating the
whole dashboard (which would produce a duplicate):

```python
# 1. Fetch the existing dashboard to get its current charts[] array.
url = f"https://api.{realm}.signalfx.com/v2/dashboard/{dashboard_id}"
req = urllib.request.Request(url, headers={"X-SF-Token": token})
with urllib.request.urlopen(req, timeout=15) as resp:
    existing = json.load(resp)

# 2. Create the new GAP chart(s) first (chart-first ordering — see Step 6).
new_chart_id = ...  # returned by POST /v2/chart

# 3. PUT the dashboard with the merged charts[] list.
merged_charts = existing["charts"] + [
    {"chartId": new_chart_id, "column": c, "row": r, "width": w, "height": h}
]
put_body = {
    "name": existing["name"],
    "description": existing.get("description", ""),
    "groupId": existing["groupId"],
    "charts": merged_charts,
}
put_req = urllib.request.Request(
    f"https://api.{realm}.signalfx.com/v2/dashboard/{dashboard_id}",
    data=json.dumps(put_body).encode(),
    headers={"X-SF-Token": token, "Content-Type": "application/json"},
    method="PUT",
)
with urllib.request.urlopen(put_req, timeout=15) as resp:
    updated = json.load(resp)
```

Status handling on `PUT`: 200 means updated; 404 means the dashboard changed
since confirmation, so stop, refresh inventory, re-plan, and obtain new
confirmation before creating anything; 403/401 means stop; 400 uses the same
field-casing / normalization check as POST.

## Red flags

- `SPLUNK_ACCESS_TOKEN` unset — stop and tell the user.
- No realm from `SPLUNK_REALM` or the connected Observer — stop and tell the
  user.
- Any skipped or failed pagination page - inventory is incomplete; all local
  objects are UNCERTAIN and no write is allowed.
- **All** offsets returning HTTP 500 continuously - likely an auth failure
  masquerading as 500; verify the token is valid.
- A live object has `programText` missing or empty — treat as not-a-match (cannot
  verify the filter); classify UNCERTAIN, never COVERED.
- POST returns 403 — token lacks write scope; stop.
- POST returns 400 — distinguish a field-name casing error from a SignalFlow
  parse error (see the table); they have different fixes.
