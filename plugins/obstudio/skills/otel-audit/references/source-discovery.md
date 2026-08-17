# Source Discovery And Topology

Use this reference for every `$otel-audit` source scan. It defines the evidence
and per-signal topology needed before the canonical audit can be written.

## Contents

- [Repository discovery](#repository-discovery)
- [Provider and exporter topology](#provider-and-exporter-topology)
- [Signal inventory](#signal-inventory)
- [Dependency coverage](#dependency-coverage)
- [Source-derived verification plan](#source-derived-verification-plan)
- [Anti-patterns](#anti-patterns)

## Repository discovery

Identify each deployable process independently.

| Ecosystem | Primary evidence |
|---|---|
| Go | `go.mod`, `cmd/`, `main.go` |
| Python | `pyproject.toml`, `requirements.txt`, `setup.py`, app/worker modules |
| Node.js | `package.json`, lockfile, scripts, app/server entry point |
| Java | `pom.xml`, `build.gradle`, wrapper, application/main class |
| Rust | `Cargo.toml`, binaries |
| .NET | `*.csproj`, `*.sln`, program/host startup |

For each process:

- Record its complete manifest, entry point, route/controller/router sources,
  dependencies, workers/jobs, and startup path.
- Enumerate every HTTP/RPC route with method and stable path or method name.
- Record wrappers, task runners, toolchain/version files, lockfiles, CI commands,
  devcontainers, test layout, and locally safe configured commands.
- Inspect `Dockerfile`, compose, Make, package scripts, launch configs, procfiles,
  service units, worker files, and deployment environment when present.
- For an AI path, include demo/load/eval/replay clients, synthetic/canary checks,
  model/config resolvers, tool/MCP dispatch, retrieval, and streaming clients.
- Cite complete repository-relative paths and confirmed symbols. Use optional
  `:line`, `:start-end`, or comma-separated line selectors only for exact files.

## Provider and exporter topology

Build a matrix keyed by **process x signal**. Inspect traces, metrics, and logs
separately.

Trace from the real process entry point and startup environment to recording
call sites. Find:

- explicit and lazy `TracerProvider`, `MeterProvider`, and `LoggerProvider`
  creation;
- global `set_*_provider` calls and no-op branches;
- exporter, processor/reader, resource, propagation, flush, and shutdown setup;
- helpers that initialize a provider on first instrument access;
- agent/preload/operator bootstrap and its ordering relative to app imports;
- framework instrumentation timing, especially middleware added from a late
  lifespan/startup hook;
- operator `OTEL_SERVICE_NAME` and `OTEL_RESOURCE_ATTRIBUTES` precedence versus
  application defaults and resource merges;
- per-signal OTLP endpoint and protocol. Require gRPC receivers for `grpc`, or
  `/v1/<signal>` HTTP endpoints for `http/protobuf`; a mismatched pair is a gap.

Classify each signal for each process as:

- `source-active`: reachable app source creates and registers a real provider;
- `externally bootstrapped`: the selected startup path supplies it outside app
  source;
- `source-defined but inactive`: setup exists but is not reachable for that
  process/startup configuration;
- `no provider`: neither app nor selected bootstrap supplies it.

These labels are source conclusions, never runtime emission proof. A metrics
provider does not prove tracing or logs, and a missing agent wrapper does not
make reachable app-owned providers no-op.

For Python, run:

```bash
python3 -I "<skill-root>/scripts/scan_python_otel_topology.py" "<service-root>"
```

Treat scanner output only as candidates; reconcile each hit with process
reachability and startup order.

## Signal inventory

List exact emitted or configured items one row at a time.

### Spans

- Enumerate every route/RPC span an installed framework instrumentation can
  produce; do not write "all server spans".
- Find custom creation such as Go `tracer.Start`, Python
  `start_as_current_span`/`start_span`, Node `startActiveSpan`/`startSpan`, and
  Java `@WithSpan`/`Span.current()`.
- Record stable span name, type (`auto` or `custom`), process, and exact source.
- Inspect propagation, status/error type, exception recording, parentage, and
  variable/high-cardinality names.

### Metrics

- Enumerate every exact metric from runtime/framework/client instrumentation;
  do not use `(+ related)` or group runtime/HTTP/RPC instruments.
- Find custom counters, histograms, gauges, observable gauges, and up/down
  counters. Record metric name, instrument type, process, attributes, and exact
  source.
- Flag user, tenant, request, session, task, trace, raw URL/path, payload, or
  other unbounded values in metric dimensions.

### Logs

- Find OTel SDK/bridge packages, OTLP handlers/exporters, trace-context
  injection, span events, MDC/context variables, access-log formatters,
  exception helpers, adapters, and final formatter/filter paths.
- Check whether request, user, tenant, session, raw URL, exception text,
  traceback, header, credential, or content values can reach the final record.
- Classify as `otlp`, `correlation-only`, or `not configured`. Trace IDs in
  stdout do not prove an OTLP log pipeline.

## Dependency coverage

Check only dependencies actually present. Prefer the official OpenTelemetry
instrumentation for the installed ecosystem/version.

| Ecosystem | Common dependency -> instrumentation checks |
|---|---|
| Go | `net/http` -> `otelhttp`; gorilla/mux -> `otelmux`; chi -> `otelchi`; gRPC -> `otelgrpc`; Redis -> `redisotel`; Kafka -> `otelsegmentio`; AWS SDK v2 -> `otelaws`; runtime/host metrics |
| Python | Flask, Django, FastAPI/Starlette, requests, httpx, urllib3/aiohttp, psycopg2/SQLAlchemy, MongoDB, Redis, Celery, gRPC, Kafka, botocore, stdlib logging -> matching `opentelemetry-instrumentation-*` package |
| Node.js | Express, Fastify, Koa, NestJS, HTTP, pg/mysql2/MongoDB, Redis, gRPC, KafkaJS, GraphQL, AWS SDK -> matching `@opentelemetry/instrumentation-*` package |
| Java | Check Java-agent support for servlet/Spring, WebFlux, JDBC/JPA, outbound HTTP, Kafka, RabbitMQ, gRPC, and the selected servlet container |

For every dependency, record whether matching instrumentation is installed,
initialized for the target process, and expected to emit spans, metrics, logs,
or a combination. Package presence alone is not active coverage.

## Source-derived verification plan

Define reusable environments once, including stable ID, surface, configured
runtime/toolchain, config evidence, project-native runner, module scope, and
shared prerequisites.

Create a stable scenario per telemetry-distinct route, operation, dependency,
worker/job, startup/shutdown, error/timeout, stream, tool, or retrieval path.
For each scenario record:

- source entry point and exact existing operation/span name;
- expected exact signals and attributes/dimensions;
- acceptance criteria for status, parentage, datapoints, correlation,
  redaction, resource/exporter behavior, or lifecycle;
- environment IDs and proof level: `focused call-site`, `full runtime`, or
  `either`.

Use `full runtime` when proof depends on agent/preload startup,
framework-resolved names, automatic metrics, runtime log export, or absence of
duplicate automatic spans. Split paths when telemetry differs; combine only
when the emitted contract is identical. Prefer fakes or an existing test seam
over live credentials. Record missing prerequisites in the environment, not in
every scenario.

## Anti-patterns

Flag source evidence for:

- multiple SDK/provider initializations in one process;
- hard-coded OTLP endpoints or resource identity that overwrites operator
  values;
- providers, tracers, or meters created in request/loop hot paths;
- missing propagation, shutdown/flush, error status, or exception recording;
- variable span names and high-cardinality metric attributes;
- late framework instrumentation after serving begins;
- endpoint/protocol mismatches;
- community wrappers where an appropriate official OTel package exists.
