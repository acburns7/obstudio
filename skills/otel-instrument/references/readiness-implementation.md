# Readiness Implementation

Load this reference only when a validated selection includes incident-readiness
or GenAI implementation. Read the applicable shared readiness reference first;
it owns surface discovery and semantic conventions. This reference owns the
source-backed patch, proof, and exact closure rules.

## Contents

- Canonical GenAI span ownership
- Incident and GenAI surface closure
- Evaluation, token pressure, and MCP
- Source-owned route-aware HTTP proof
- Exact remaining-signal gate

## Canonical GenAI Span Ownership

- Inventory framework/vendor bridges, provider SDK hooks, callbacks,
  middleware, auto-instrumentors, and app spans before adding GenAI spans.
- Choose one canonical GenAI span source per logical operation. A representative
  trace must contain one GenAI node for each workflow, agent, model call, tool
  call, retrieval, memory operation, or evaluation result.
- When a framework/vendor bridge is canonical, keep it and add only missing
  context, safe aggregates, metrics, or owner mappings. Do not create duplicate
  app-owned `chat` or `execute_tool` spans for the same operation.
- When app-owned spans are canonical, emit the complete selected span set and
  disable, opt out of, or suppress overlapping framework/vendor GenAI
  instrumentation with the discovered runtime mechanism. Do not hard-code this
  decision to one framework. Keep HTTP/database/runtime auto-instrumentation
  when it does not duplicate GenAI nodes.
- For a preload, agent, `opentelemetry-instrument`, `NODE_OPTIONS --require`, or
  equivalent bootstrap, configure suppression in the real launch environment
  before bootstrap. Updating environment variables in app code afterward is
  defense in depth, not proof that hooks were suppressed.
- Prove one canonical node per operation, no wrapper-only tools, stable
  model/tool names, expected LLM/tool counts, and correct workflow/agent parent
  shape. Apply the full-runtime acceptance gate when bootstrap behavior matters.

## Incident And GenAI Surface Closure

- For incident evidence, map `incident class -> failure mechanism -> owner ->
  code surface -> signal -> MTTD impact -> remaining owner`. Classify each
  signal as `MTTD-improving`, `localization-only`, or uncovered.
- For GenAI incident-evidence mode, map each AI pathway failure mechanism to its
  provider/model gateway, workflow/agent, tool/function execution or MCP
  dispatcher, retrieval, streaming, token/context, prompt/response,
  safety/policy, AI-derived data, model/config rollout, or AI-owned cache/session
  surface before editing.
- Parse each selected `genai_readiness` row by human-readable `surface`, complete
  `required_signals`, owner/source files, and acceptance criteria. Use the
  surface name as the human-facing identifier.
- Maintain `surface -> required_signals -> implemented_signals -> tests ->
  remaining_signals -> status`. Implement and test app-owned work, prove
  existing coverage with source path and signal name, and owner-map an unsafe or
  external prerequisite with its exact missing source.
- Do not call GenAI instrumentation complete while any selected app-owned
  provider/model, workflow/agent, tool/MCP, retrieval, streaming,
  token/context, prompt/response, safety/policy, AI-derived data,
  memory/context, evaluation, content-governance, framework-bridge, cost, or
  model/config signal remains only a follow-up.

## Evaluation, Token Pressure, And MCP

- For a selected evaluation-quality surface, instrument the owning evaluator or
  scoring path. Emit `gen_ai.evaluation.result` on the relevant workflow or
  evaluation span with `gen_ai.evaluation.name`,
  `gen_ai.evaluation.score.value` for numeric scores,
  `gen_ai.evaluation.score.label` for labels or verdicts, and safe parent
  linkage. Add detector-ready score, count, latency, error, no-data, and
  freshness metrics when source values exist. Metrics-only coverage does not
  satisfy selected-trace evaluation visibility; keep the surface partial and
  name the missing span-level event or metrics.
- For token/context pressure, reconcile token usage, context-budget percent,
  truncation, token-limit errors, prompt/tool schema size, and per-workflow LLM
  and tool-call fanout separately. Token usage or a context gauge alone does not
  close a broader selected pressure gap.
- Use a low-cardinality detector-ready proxy for prompt/tool schema pressure
  when the app can measure one safely, such as schema JSON length bucket,
  schema field count, prompt length bucket, or tool count. Prompt/schema version
  span attributes are trace context; they do not close schema-size pressure.
- For MCP, JSON-RPC, and tool dispatch, never record JSON-RPC request IDs, raw
  request/session/trace IDs, identities, payloads, prompts, completions, or tool
  arguments as metric dimensions. Use stable methods only from an allowlist or
  known route/tool registration; otherwise use bounded families such as
  `known_tool`, `unknown_method`, `invalid_request`, or `unsupported_method`.
- GenAI spans alone do not satisfy detector-ready tool coverage. When app code
  observes execution, add or prove a tool-specific duration histogram and tool
  error/timeout counter with stable bounded dimensions.
- For app-owned streaming or protocol send loops, add a send/write failure
  signal as a counter, span event, or bounded outcome attribute. Otherwise
  owner-map the missing source explicitly. A focused repo-native test must
  execute the failure path and assert emitted telemetry; do not finalize with a
  compile or source-string check as emission proof.

## Source-Owned Route-Aware HTTP Proof

- When the selected app-owned HTTP surface has parameterized routes,
  route-aware server spans are required. Use the detected framework's real
  route resolver and a low-cardinality route pattern; follow the language
  reference for wrapper placement and preserve automatic request metrics.
- Prove every selected route through the actual source-owned router. Each
  request must emit exactly one canonical `SERVER` span, and combined framework
  and generic wrappers must not emit duplicate server spans.
- Use focused route tests for app-owned naming and the full-runtime gate for
  framework-resolved routes, preload/agent behavior, automatic metrics, or
  duplicate suppression. Owner-map platform-owned route behavior that the repo
  cannot change.

## Exact Remaining-Signal Gate

- A closure row cannot be `Working` while a required signal is absent, only a
  follow-up, or supported by an unexecuted test. Name every residual signal in
  `remaining_signals`; use `None` only when direct proof closes the whole row.
- Keep unselected findings out of implementation claims. When no canonical
  source audit exists, do not create `## GenAI Readiness Closure` or collapse
  absent GenAI readiness into a generic implementation claim.
- Final summaries and PR descriptions must preserve exact residual token,
  schema, fanout, evaluation-event, MCP/tool, send-failure, route, and external
  owner gaps. Say `Remaining signals: none` only when no applicable closure row
  is partial, blocked, deferred, not configured, or not proven.
