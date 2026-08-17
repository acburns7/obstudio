# OTLP Application Log Export Contract

Load this reference for every validated selected application-log change,
including correlation-only work, explorer-visible application logs, or an OTLP
log bridge. It does not authorize logging work by itself. For
`correlation-only` or `not requested` scope, do not add log-export dependencies,
handlers, bridges, exporters, or configuration; still apply the relevant final
pipeline privacy and correlation checks to selected correlation-only changes.

## Authorization And Topology

Classify the selected log scope before editing:

- `correlation-only`: application stdout/stderr records may carry safe trace
  context, but the application owns no OTLP log export path.
- `otlp`: an application logging provider or official bridge/exporter sends
  log records over OTLP.
- `not requested`: make no logging change.

Never add an OTLP log bridge for unselected work. Stdout correlation is not
OTLP log export, even when an MDC, adapter, or formatter injects `trace_id` and
`span_id`. Do not claim explorer-visible logs from stdout evidence.

Before adding or changing export, trace the complete existing path: logging
API, handler/appender, provider or bridge, exporter, endpoint/protocol, process
startup, flush/shutdown, platform agent, collector, and backend. Determine
whether a platform collector already tails stdout. A second application-owned
OTLP path can create duplicate ingestion, added cost, and inconsistent records.
Log export also expands privacy exposure. Record these privacy, cost, and
duplicate-ingestion risks in the implementation plan and preserve one
intentional canonical delivery path.

Use the official OTel bridge/exporter for the detected logging stack. Extend
the process's existing provider and resource topology; do not create a second
provider, initialize logging on library import, hardcode an endpoint, or infer
log delivery from a trace exporter. Configure only the selected process and
preserve operator-supplied signal-specific endpoint and protocol settings.

## Final Pipeline Privacy Review

Review the final emitted record, not only the application's `logger.*` call.
Inspect every formatter field, logging adapter, MDC or context variable,
framework access-log formatter, and exception renderer that can add data after
the call site.

Unless an explicit approved policy permits the field, keep these values out of
the exported application-log surface:

- credentials, authorization headers, cookies, tokens, and raw payloads;
- raw request, user, tenant, session, trace, or span identifiers in the body;
- raw dynamic URLs or query strings;
- exception text or tracebacks that can contain request or tenant data.

Trace and span IDs may appear only in their dedicated correlation fields when
the selected contract requires them. Keep the human report free of their raw
values. Use deterministic sentinel inputs for privacy checks and assert their
absence after the formatter, adapter, access logger, and exception renderer
have all run. Removing a value at one call site is insufficient if a later
pipeline stage restores it.

## Direct Runtime Proof

An OTLP bridge is startup-installed runtime behavior. Follow
[full-runtime acceptance](../../references/full-runtime-acceptance.md); static
source review, dependency presence, successful compilation, or stdout capture
does not prove export. Trigger a selected audit scenario through the real
logging pipeline and inspect the record accepted by the OTLP receiver and, when
the selected outcome requires it, the target explorer.

Direct proof must establish every applicable property:

| Property | Required evidence |
|---|---|
| Body | The received `body` matches the safe expected event, without relying on console text. |
| Category | The received logger/category or instrumentation-scope value identifies the intended source. |
| Severity | The received severity number/text matches the emitted level. |
| Correlation | Dedicated `trace_id` and `span_id` fields match the generated trace while an active span exists; do not print their raw values in reports. |
| Redaction | Sensitive sentinel values are absent from the final received body, attributes, exception fields, and resource. |
| Resource identity | The record carries the expected `service.name` plus selected environment/version identity from the process resource. |
| OTLP visibility | Receiver or backend evidence identifies the emitted record through the OTLP log path; stdout alone is not visibility proof. |

Also emit one deterministic sentinel record and prove the canonical OTLP path
does not create duplicate backend records. If stdout remains platform-collected
alongside direct OTLP export, prove the routing or filtering that prevents
double ingestion.

Map direct evidence to the selected finding's exact verification scenarios and
stable instrumentation item. Do not expose credentials, sentinel secret
values, raw correlation IDs, or unredacted records in source, terminal output,
JSON, Markdown, or generated HTML.

## Result Classification

- Use `Not configured` when selected OTLP export has no reachable configured
  bridge/exporter path. Do not downgrade this to `Not proven`.
- Use `Not proven` when configuration exists but the required direct runtime
  record or target visibility was not observed.
- Use `Not working` only when an executed check fails.
- Use `Working` for selected OTLP logs only after all applicable direct-proof
  properties and the duplicate-ingestion check pass.
- A selected `correlation-only` change may be `Working` without OTLP export
  after its correlation/privacy criteria pass; state that export was not added.
