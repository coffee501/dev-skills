import assert from "node:assert/strict";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { DatabaseSync } from "node:sqlite";
import { DevStateError, StateStore, resolveStateHome } from "../server/state-store.mjs";

function fixture() {
  const root = mkdtempSync(join(tmpdir(), "dev-state-test-"));
  const project = join(root, "project");
  const stateHome = join(root, "external-state");
  const store = new StateStore({ stateHome, clock: () => "2026-08-20T00:00:00.000Z" });
  const workspace = store.resolveWorkspace({ project_path: project, display_name: "project" });
  const common = { workspace_id: workspace.workspace_id, change_id: "CHG-001", actor: "dev-orch", source: "test" };
  return {
    root, project, stateHome, store, workspace, common,
    close() { store.close(); rmSync(root, { recursive: true, force: true }); },
  };
}

let routeCounter = 0;

function prepareRoute(fx, skill, nodeId = `${skill}-node`) {
  routeCounter += 1;
  const lifecycleId = `LCV-WIT-${routeCounter}`;
  const lcv = fx.store.lifecyclePut({
    ...fx.common, lifecycle_id: lifecycleId, expected_version: 0, status: "Current",
    payload: { route: [{ node_id: nodeId, skill, dependencies: [] }] },
  });
  return { lifecycle_route_ref: `${lifecycleId}@v${lcv.version}`, route_version: lcv.version, node_id: nodeId };
}
test("state home never defaults to the project", () => {
  assert.equal(resolveStateHome({ DEV_SKILLS_STATE_HOME: "D:/state" }, "win32", "C:/Users/test"), "D:\\state");
  assert.equal(resolveStateHome({ CLAUDE_PLUGIN_DATA: "D:/plugin-data" }, "win32", "C:/Users/test"), "D:\\plugin-data\\dev-state");
  assert.equal(resolveStateHome({ LOCALAPPDATA: "D:/local" }, "win32", "C:/Users/test"), "D:\\local\\dev-skills\\state");
  assert.equal(resolveStateHome({ XDG_STATE_HOME: "/var/user-state" }, "linux", "/home/test"), "/var/user-state/dev-skills");
});

test("state store rejects a configured state directory inside the project", () => {
  const root = mkdtempSync(join(tmpdir(), "dev-state-boundary-"));
  const project = join(root, "project");
  const stateHome = join(project, ".state");
  try {
    assert.throws(
      () => new StateStore({ stateHome, projectRoot: project }),
      (error) => error instanceof DevStateError && error.code === "STATE_INSIDE_PROJECT",
    );
    assert.equal(existsSync(stateHome), false);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("workspace, CHG, LCV and audit state stay external", () => {
  const fx = fixture();
  try {
    assert.ok(fx.workspace.workspace_id.startsWith("WS-"));
    assert.ok(fx.store.databasePath.startsWith(fx.stateHome));
    assert.equal(existsSync(fx.project), false);

    const change = fx.store.changeGetOrCreate({ ...fx.common, payload: { objective: "deliver" } });
    assert.equal(change.created, true);
    assert.equal(change.change.version, 1);
    assert.equal(fx.store.changeGet(fx.common).object_id, "CHG-001");
    assert.match(change.change.state_uri, /^devstate:\/\/workspace\/WS-/);

    const lcv = fx.store.lifecyclePut({
      ...fx.common, lifecycle_id: "LCV-001", expected_version: 0, status: "Current", payload: { route: ["dev-req"] },
    });
    assert.equal(lcv.version, 1);
    assert.deepEqual(fx.store.lifecycleGet(fx.common).payload.route, ["dev-req"]);
    assert.equal(fx.store.auditList(fx.common).length, 2);
    assert.equal(existsSync(fx.project), false);
  } finally { fx.close(); }
});

test("8.1 lifecycle write rejects invalid route topology before persistence", () => {
  const fx = fixture();
  try {
    const base = {
      ...fx.common, lifecycle_id: "LCV-STRICT", expected_version: 0, status: "Current",
    };
    assert.throws(
      () => fx.store.lifecyclePut({
        ...base, payload: { protocol_version: "DEV-SUITE-8.1", route: [
          { node_id: "a", stage: "G1", skill: "dev-req", applicability: "Applicable",
            dependencies: ["missing"], entry_conditions: [], expected_outputs: ["REQ"], stop_conditions: [] },
        ] },
      }),
      (error) => error instanceof DevStateError && error.code === "INVALID_ROUTE",
    );
    assert.equal(fx.store.lifecycleGet(fx.common), null);
    const node = (id, stage, skill, dependencies, extra = {}) => ({
      node_id: id, stage, skill, applicability: "Applicable", dependencies,
      entry_conditions: [], expected_outputs: [], stop_conditions: [], ...extra,
    });
    assert.throws(
      () => fx.store.lifecyclePut({
        ...base, payload: { route: [node("requirements", "G1", "dev-req", [])] },
      }),
      (error) => error instanceof DevStateError && error.code === "INVALID_ROUTE",
    );
    assert.throws(
      () => fx.store.lifecyclePut({
        ...base, payload: { protocol_version: "DEV-SUITE-8.1",
          route: [node("build", "G4", "dev-impl", [])] },
      }),
      (error) => error instanceof DevStateError && error.code === "INVALID_ROUTE",
    );
    assert.throws(
      () => fx.store.lifecyclePut({
        ...base, payload: { protocol_version: "DEV-SUITE-8.1",
          route: [node("probe", "G3", "dev-impl", [], {
            route_kind: "design-probe", design_refs: ["DVAL-001@v1"],
            expected_outputs: ["probe-evidence"],
          })] },
      }),
      (error) => error instanceof DevStateError && error.code === "INVALID_ROUTE",
    );
    const valid = fx.store.lifecyclePut({
      ...base, payload: { protocol_version: "DEV-SUITE-8.1", route: [
        node("probe", "G3", "dev-impl", [], {
          route_kind: "design-probe", design_refs: ["DVAL-001@v1"],
          expected_outputs: ["probe-evidence"],
        }),
        node("validate", "G3", "dev-val", ["probe"], {
          route_kind: "design-validation", design_refs: ["DVAL-001@v1"],
          expected_outputs: ["EVD", "RUN"],
        }),
      ] },
    });
    assert.equal(valid.version, 1);
  } finally { fx.close(); }
});

test("8.1 CHG write rejects LCV-owned route fields", () => {
  const fx = fixture();
  try {
    assert.throws(
      () => fx.store.changeGetOrCreate({
        ...fx.common, payload: { protocol_version: "DEV-SUITE-8.1", route: [] },
      }),
      (error) => error instanceof DevStateError && error.code === "INVALID_ARGUMENT",
    );
    assert.equal(fx.store.changeGet(fx.common), null);
  } finally { fx.close(); }
});

test("remote fingerprint alone does not merge independent clones", () => {
  const root = mkdtempSync(join(tmpdir(), "dev-state-workspace-"));
  const store = new StateStore({ stateHome: join(root, "state") });
  try {
    const first = store.resolveWorkspace({ project_path: join(root, "clone-a"), remote_fingerprint: "remote:abc" });
    const second = store.resolveWorkspace({ project_path: join(root, "clone-b"), remote_fingerprint: "remote:abc" });
    assert.notEqual(first.workspace_id, second.workspace_id);
    const rebound = store.resolveWorkspace({
      project_path: join(root, "clone-a-moved"), remote_fingerprint: "remote:abc", workspace_id: first.workspace_id,
    });
    assert.equal(rebound.workspace_id, first.workspace_id);
  } finally { store.close(); rmSync(root, { recursive: true, force: true }); }
});

test("newer database schemas are never downgraded", () => {
  const root = mkdtempSync(join(tmpdir(), "dev-state-schema-"));
  const database = new DatabaseSync(join(root, "dev-state.db"));
  database.exec("PRAGMA user_version = 2");
  database.close();
  try {
    assert.throws(
      () => new StateStore({ stateHome: root }),
      (error) => error instanceof DevStateError && error.code === "UNSUPPORTED_SCHEMA",
    );
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("optimistic versions reject stale updates", () => {
  const fx = fixture();
  try {
    fx.store.lifecyclePut({ ...fx.common, lifecycle_id: "LCV-001", expected_version: 0, status: "Current", payload: {} });
    assert.throws(
      () => fx.store.lifecyclePut({
        ...fx.common, lifecycle_id: "LCV-001", expected_version: 0, status: "Superseded", payload: { stale: true },
      }),
      (error) => error instanceof DevStateError && error.code === "VERSION_CONFLICT" && error.details.current.version === 1,
    );
  } finally { fx.close(); }
});

test("superseding an existing LCV cannot rewrite its snapshot payload", () => {
  const fx = fixture();
  try {
    fx.store.lifecyclePut({
      ...fx.common, lifecycle_id: "LCV-001", expected_version: 0, status: "Current", payload: { route_version: 1 },
    });
    const superseded = fx.store.lifecyclePut({
      ...fx.common, lifecycle_id: "LCV-001", expected_version: 1, status: "Superseded", payload: { route_version: 999 },
    });
    assert.equal(superseded.status, "Superseded");
    assert.deepEqual(superseded.payload, { route_version: 1 });
  } finally { fx.close(); }
});

test("CHG and LCV reject statuses outside their lifecycle contracts", () => {
  const fx = fixture();
  try {
    assert.throws(
      () => fx.store.changeGetOrCreate({ ...fx.common, status: "Archived", payload: {} }),
      (error) => error instanceof DevStateError && error.code === "INVALID_ARGUMENT",
    );
    assert.throws(
      () => fx.store.lifecyclePut({
        ...fx.common, lifecycle_id: "LCV-001", expected_version: 0, status: "Active", payload: {},
      }),
      (error) => error instanceof DevStateError && error.code === "INVALID_ARGUMENT",
    );
  } finally { fx.close(); }
});

test("LCV replacement preserves immutable identities and one Current view", () => {
  const fx = fixture();
  try {
    const first = fx.store.lifecyclePut({
      ...fx.common, lifecycle_id: "LCV-001", expected_version: 0, status: "Current", payload: { route_version: 1 },
    });
    const second = fx.store.lifecyclePut({
      ...fx.common, lifecycle_id: "LCV-002", expected_version: 0, status: "Current", payload: { route_version: 2 },
      supersedes_lifecycle_id: "LCV-001", supersedes_expected_version: first.version,
    });
    assert.equal(second.object_id, "LCV-002");
    assert.equal(fx.store.lifecycleGet(fx.common).object_id, "LCV-002");
    const old = fx.store.getObject({ ...fx.common, object_type: "LCV", object_id: "LCV-001" });
    assert.equal(old.status, "Superseded");
    assert.equal(old.payload.superseded_by, "LCV-002@v1");
    assert.deepEqual(second.payload.supersedes, [first.state_uri]);
  } finally { fx.close(); }
});

test("CHG transitions follow the lifecycle and reject reopening a terminal change", () => {
  const fx = fixture();
  try {
    const draft = fx.store.changeGetOrCreate({ ...fx.common, payload: { objective: "deliver" } }).change;
    const active = fx.store.changePut({ ...fx.common, expected_version: draft.version, status: "Active", payload: draft.payload });
    const completed = fx.store.changePut({
      ...fx.common, expected_version: active.version, status: "Completed",
      payload: { ...active.payload, completion: { confirmed_by: "project-owner" } },
    });
    assert.equal(completed.status, "Completed");
    assert.throws(
      () => fx.store.changePut({ ...fx.common, expected_version: completed.version, status: "Active", payload: completed.payload }),
      (error) => error instanceof DevStateError && error.code === "INVALID_TRANSITION",
    );
  } finally { fx.close(); }
});

test("WIT claim and completion enforce agent and input identity", () => {
  const fx = fixture();
  try {
    const route = prepareRoute(fx, "dev-lld", "G3-lld");
    const prepared = fx.store.workPrepare({
      ...fx.common, work_item_id: "WIT-001", skill: "dev-lld", input_versions: ["REQ-001@v2"],
      ...route, expected_version: 0, owned_paths: [], owned_artifacts: ["DET-001"], expected_outputs: ["DET"],
    });
    assert.equal(prepared.status, "Prepared");
    const running = fx.store.workClaim({ ...fx.common, work_item_id: "WIT-001", agent_id: "agent-1", expected_version: 1 });
    assert.equal(running.payload.attempt, 1);
    assert.throws(
      () => fx.store.workComplete({
        ...fx.common, work_item_id: "WIT-001", agent_id: "agent-2", input_fingerprint: running.payload.input_fingerprint,
        status: "Completed", expected_version: 2,
      }),
      (error) => error instanceof DevStateError && error.code === "AGENT_MISMATCH",
    );
    const completed = fx.store.workComplete({
      ...fx.common, work_item_id: "WIT-001", agent_id: "agent-1", input_fingerprint: running.payload.input_fingerprint,
      status: "Completed", outputs: ["DET-001@v1"], evidence: [], expected_version: 2,
    });
    assert.equal(completed.status, "Completed");
    assert.deepEqual(completed.payload.outputs, ["DET-001@v1"]);
  } finally { fx.close(); }
});

test("durable recovery can read WIT and validated Agent run bindings", () => {
  const fx = fixture();
  try {
    const route = prepareRoute(fx, "dev-cr", "G4-cr");
    fx.store.workPrepare({
      ...fx.common, work_item_id: "WIT-RECOVER", skill: "dev-cr", input_versions: ["IMP-001@v1"],
      ...route, expected_version: 0, owned_paths: [], owned_artifacts: ["REV-001"], expected_outputs: ["REV"],
    });
    const running = fx.store.workClaim({
      ...fx.common, work_item_id: "WIT-RECOVER", agent_id: "review-agent", expected_version: 1,
    });
    assert.throws(
      () => fx.store.agentRunBind({
        ...fx.common, run_id: "RUN-BAD", work_item_id: "WIT-RECOVER", agent_id: "other-agent",
        input_fingerprint: running.payload.input_fingerprint, expected_version: 0,
      }),
      (error) => error instanceof DevStateError && error.code === "AGENT_MISMATCH",
    );
    const bound = fx.store.agentRunBind({
      ...fx.common, run_id: "RUN-RECOVER", work_item_id: "WIT-RECOVER", agent_id: "review-agent",
      input_fingerprint: running.payload.input_fingerprint, expected_version: 0, details: { host: "local" },
    });
    assert.equal(bound.payload.work_item_id, "WIT-RECOVER");
    assert.equal(fx.store.workGet({ ...fx.common, work_item_id: "WIT-RECOVER" }).status, "Running");
    assert.deepEqual(fx.store.workList({ ...fx.common, status: "Running" }).map((item) => item.object_id), ["WIT-RECOVER"]);
    assert.deepEqual(
      fx.store.agentRunList({ ...fx.common, work_item_id: "WIT-RECOVER" }).map((item) => item.object_id),
      ["RUN-RECOVER"],
    );
  } finally { fx.close(); }
});

test("WIT prepare is create-only and never reopens terminal work", () => {
  const fx = fixture();
  try {
    const route = prepareRoute(fx, "dev-lld", "G3-lld");
    fx.store.workPrepare({
      ...fx.common, work_item_id: "WIT-CREATE-ONLY", skill: "dev-lld", input_versions: ["REQ-001@v2"],
      ...route, expected_version: 0, owned_paths: [], owned_artifacts: ["DET-001"], expected_outputs: ["DET"],
    });
    const running = fx.store.workClaim({
      ...fx.common, work_item_id: "WIT-CREATE-ONLY", agent_id: "agent-1", expected_version: 1,
    });
    const completed = fx.store.workComplete({
      ...fx.common, work_item_id: "WIT-CREATE-ONLY", agent_id: "agent-1",
      input_fingerprint: running.payload.input_fingerprint, status: "Completed",
      outputs: ["DET-001@v1"], evidence: ["test"], result: { ok: true }, expected_version: 2,
    });
    assert.throws(
      () => fx.store.workPrepare({
        ...fx.common, work_item_id: "WIT-CREATE-ONLY", skill: "dev-lld", input_versions: ["REQ-001@v3"],
        ...route, expected_version: completed.version, owned_paths: [], owned_artifacts: ["DET-002"], expected_outputs: ["DET"],
      }),
      (error) => error instanceof DevStateError && error.code === "INVALID_TRANSITION",
    );
    const current = fx.store.workGet({ ...fx.common, work_item_id: "WIT-CREATE-ONLY" });
    assert.equal(current.status, "Completed");
    assert.equal(current.payload.attempt, 1);
    assert.deepEqual(current.payload.outputs, ["DET-001@v1"]);
  } finally { fx.close(); }
});

test("WIT prepare requires a Current lifecycle route", () => {
  const fx = fixture();
  try {
    assert.throws(
      () => fx.store.workPrepare({
        ...fx.common, work_item_id: "WIT-NO-LCV", skill: "dev-lld", input_versions: ["REQ-001@v2"],
        expected_version: 0, owned_paths: [], owned_artifacts: [], expected_outputs: [],
      }),
      (error) => error instanceof DevStateError && error.code === "INVALID_ARGUMENT",
    );
  } finally { fx.close(); }
});
test("WIT route binding is required for Current LCV and rejects stale route identity", () => {
  const fx = fixture();
  try {
    const lcv = fx.store.lifecyclePut({
      ...fx.common, lifecycle_id: "LCV-ROUTE", expected_version: 0, status: "Current",
      payload: { route: [{ node_id: "G3-lld", skill: "dev-lld", dependencies: [] }] },
    });
    assert.throws(
      () => fx.store.workPrepare({
        ...fx.common, work_item_id: "WIT-NO-ROUTE", skill: "dev-lld", input_versions: ["REQ-001@v2"],
        expected_version: 0, owned_paths: [], owned_artifacts: [], expected_outputs: [],
      }),
      (error) => error instanceof DevStateError && error.code === "INVALID_ARGUMENT",
    );
    assert.throws(
      () => fx.store.workPrepare({
        ...fx.common, work_item_id: "WIT-STALE-ROUTE", skill: "dev-lld", input_versions: ["REQ-001@v2"],
        lifecycle_route_ref: "LCV-ROUTE@v1", route_version: lcv.version + 1, node_id: "G3-lld",
        expected_version: 0, owned_paths: [], owned_artifacts: [], expected_outputs: [],
      }),
      (error) => error instanceof DevStateError && error.code === "STALE_ROUTE",
    );
    const prepared = fx.store.workPrepare({
      ...fx.common, work_item_id: "WIT-ROUTE", skill: "dev-lld", input_versions: ["REQ-001@v2"],
      lifecycle_route_ref: "LCV-ROUTE@v1", route_version: lcv.version, node_id: "G3-lld",
      expected_version: 0, owned_paths: [], owned_artifacts: [], expected_outputs: [],
    });
    assert.equal(prepared.payload.lifecycle_route_ref, "LCV-ROUTE@v1");
    assert.equal(prepared.payload.route_version, 1);
    assert.equal(prepared.payload.node_id, "G3-lld");
  } finally { fx.close(); }
});

test("WIT claim and successful completion reject superseded route bindings", () => {
  const fx = fixture();
  try {
    const first = fx.store.lifecyclePut({
      ...fx.common, lifecycle_id: "LCV-OLD", expected_version: 0, status: "Current",
      payload: { route: [{ node_id: "G4-impl", skill: "dev-impl", dependencies: [] }] },
    });
    fx.store.workPrepare({
      ...fx.common, work_item_id: "WIT-STALE-CLAIM", skill: "dev-impl", input_versions: ["DET-001@v1"],
      lifecycle_route_ref: "LCV-OLD@v1", route_version: first.version, node_id: "G4-impl",
      expected_version: 0, owned_paths: [], owned_artifacts: [], expected_outputs: [],
    });
    fx.store.lifecyclePut({
      ...fx.common, lifecycle_id: "LCV-NEW", expected_version: 0, status: "Current",
      payload: { route: [{ node_id: "G4-impl-v2", skill: "dev-impl", dependencies: [] }] },
      supersedes_lifecycle_id: "LCV-OLD", supersedes_expected_version: first.version,
    });
    assert.throws(
      () => fx.store.workClaim({
        ...fx.common, work_item_id: "WIT-STALE-CLAIM", agent_id: "impl-agent", expected_version: 1,
      }),
      (error) => error instanceof DevStateError && error.code === "STALE_ROUTE",
    );
  } finally { fx.close(); }
});

test("WIT Completed rejects stale route while Cancelled can close cleanup state", () => {
  const fx = fixture();
  try {
    const first = fx.store.lifecyclePut({
      ...fx.common, lifecycle_id: "LCV-COMPLETE-OLD", expected_version: 0, status: "Current",
      payload: { route: [{ node_id: "G4-impl", skill: "dev-impl", dependencies: [] }] },
    });
    fx.store.workPrepare({
      ...fx.common, work_item_id: "WIT-STALE-COMPLETE", skill: "dev-impl", input_versions: ["DET-001@v1"],
      lifecycle_route_ref: "LCV-COMPLETE-OLD@v1", route_version: first.version, node_id: "G4-impl",
      expected_version: 0, owned_paths: [], owned_artifacts: [], expected_outputs: [],
    });
    const running = fx.store.workClaim({
      ...fx.common, work_item_id: "WIT-STALE-COMPLETE", agent_id: "impl-agent", expected_version: 1,
    });
    fx.store.lifecyclePut({
      ...fx.common, lifecycle_id: "LCV-COMPLETE-NEW", expected_version: 0, status: "Current",
      payload: { route: [{ node_id: "G4-impl-v2", skill: "dev-impl", dependencies: [] }] },
      supersedes_lifecycle_id: "LCV-COMPLETE-OLD", supersedes_expected_version: first.version,
    });
    assert.throws(
      () => fx.store.workComplete({
        ...fx.common, work_item_id: "WIT-STALE-COMPLETE", agent_id: "impl-agent",
        input_fingerprint: running.payload.input_fingerprint, status: "Completed", expected_version: 2,
      }),
      (error) => error instanceof DevStateError && error.code === "STALE_ROUTE",
    );
    const cancelled = fx.store.workComplete({
      ...fx.common, work_item_id: "WIT-STALE-COMPLETE", agent_id: "impl-agent",
      input_fingerprint: running.payload.input_fingerprint, status: "Cancelled", expected_version: 2,
      evidence: ["route superseded"], result: { reason: "stale route cleanup" },
    });
    assert.equal(cancelled.status, "Cancelled");
  } finally { fx.close(); }
});
test("legacy WIT without route binding cannot be claimed or completed", () => {
  const fx = fixture();
  try {
    prepareRoute(fx, "dev-impl", "G4-impl");
    fx.store.putObject({
      ...fx.common, object_type: "WIT", object_id: "WIT-LEGACY-PREPARED",
      status: "Prepared", expected_version: 0, payload: { skill: "dev-impl", attempt: 0 },
    });
    assert.throws(
      () => fx.store.workClaim({
        ...fx.common, work_item_id: "WIT-LEGACY-PREPARED", agent_id: "impl-agent", expected_version: 1,
      }),
      (error) => error instanceof DevStateError && error.code === "STALE_ROUTE",
    );
    fx.store.putObject({
      ...fx.common, object_type: "WIT", object_id: "WIT-LEGACY-RUNNING",
      status: "Running", expected_version: 0,
      payload: { skill: "dev-impl", agent_id: "impl-agent", input_fingerprint: "legacy-input" },
    });
    assert.throws(
      () => fx.store.workComplete({
        ...fx.common, work_item_id: "WIT-LEGACY-RUNNING", agent_id: "impl-agent",
        input_fingerprint: "legacy-input", status: "Completed", expected_version: 1,
      }),
      (error) => error instanceof DevStateError && error.code === "STALE_ROUTE",
    );
    const cancelled = fx.store.workComplete({
      ...fx.common, work_item_id: "WIT-LEGACY-RUNNING", agent_id: "impl-agent",
      input_fingerprint: "legacy-input", status: "Cancelled", expected_version: 1,
      evidence: ["legacy WIT requires replanning"],
    });
    assert.equal(cancelled.status, "Cancelled");
  } finally { fx.close(); }
});
test("WIT completion atomically closes matching running Agent runs", () => {
  const fx = fixture();
  try {
    const route = prepareRoute(fx, "dev-impl", "G4-impl");
    fx.store.workPrepare({
      ...fx.common, work_item_id: "WIT-RUN-CLOSE", skill: "dev-impl", input_versions: ["DET-001@v1"],
      ...route, expected_version: 0, owned_paths: [], owned_artifacts: ["IMP-001"], expected_outputs: ["IMP"],
    });
    const running = fx.store.workClaim({
      ...fx.common, work_item_id: "WIT-RUN-CLOSE", agent_id: "impl-agent", expected_version: 1,
    });
    fx.store.agentRunBind({
      ...fx.common, run_id: "RUN-CLOSE", work_item_id: "WIT-RUN-CLOSE", agent_id: "impl-agent",
      input_fingerprint: running.payload.input_fingerprint, expected_version: 0, details: { host: "local" },
    });
    fx.store.workComplete({
      ...fx.common, work_item_id: "WIT-RUN-CLOSE", agent_id: "impl-agent",
      input_fingerprint: running.payload.input_fingerprint, status: "Completed",
      outputs: ["IMP-001@v1"], evidence: ["test"], expected_version: 2,
    });
    const runs = fx.store.agentRunList({ ...fx.common, work_item_id: "WIT-RUN-CLOSE" });
    assert.equal(runs.length, 1);
    assert.equal(runs[0].status, "Completed");
    assert.equal(runs[0].payload.work_status, "Completed");
    assert.equal(fx.store.agentRunList({ ...fx.common, status: "Running" }).length, 0);
    assert.throws(
      () => fx.store.agentRunBind({
        ...fx.common, run_id: "RUN-LATE", work_item_id: "WIT-RUN-CLOSE", agent_id: "impl-agent",
        input_fingerprint: running.payload.input_fingerprint, expected_version: 0,
      }),
      (error) => error instanceof DevStateError && error.code === "INVALID_TRANSITION",
    );
  } finally { fx.close(); }
});
test("invalidation updates targets atomically", () => {
  const fx = fixture();
  try {
    fx.store.lifecyclePut({ ...fx.common, lifecycle_id: "LCV-001", expected_version: 0, status: "Current", payload: { route: [] } });
    fx.store.artifactPut({
      ...fx.common, artifact_id: "DET-001", artifact_type: "DET", expected_version: 0, status: "Accepted", payload: {},
    });
    const result = fx.store.applyInvalidation({
      ...fx.common, invalidation_id: "INV-001", expected_version: 0, reason: "REQ changed",
      targets: [
        { object_type: "LCV", object_id: "LCV-001", expected_version: 1, new_status: "Superseded", reason: "route changed" },
        { object_type: "ARTIFACT", object_id: "DET-001", expected_version: 1, new_status: "Expired", reason: "input changed" },
      ],
    });
    assert.equal(result.targets[0].status, "Superseded");
    assert.equal(result.targets[1].status, "Expired");
    assert.equal(result.invalidation.status, "Applied");
  } finally { fx.close(); }
});

test("invalidation cannot bypass lifecycle status contracts", () => {
  const fx = fixture();
  try {
    fx.store.lifecyclePut({ ...fx.common, lifecycle_id: "LCV-001", expected_version: 0, status: "Current", payload: {} });
    assert.throws(
      () => fx.store.applyInvalidation({
        ...fx.common, invalidation_id: "INV-INVALID", expected_version: 0, reason: "bad route",
        targets: [{ object_type: "LCV", object_id: "LCV-001", expected_version: 1, new_status: "NeedsReview", reason: "invalid" }],
      }),
      (error) => error instanceof DevStateError && error.code === "INVALID_ARGUMENT",
    );
    assert.equal(fx.store.lifecycleGet(fx.common).version, 1);
    assert.equal(fx.store.lifecycleGet(fx.common).status, "Current");
  } finally { fx.close(); }
});

function prepareHandoff(fx, handoffId = "HOF-001") {
  return fx.store.handoffPrepare({
    ...fx.common, handoff_id: handoffId, from: "dev-lld", to: "dev-impl", reason: "design ready",
    inputs: ["DET-001@v1"], preserved_behavior: ["existing API remains compatible"], decisions: ["DDEC-001@v1"],
    unresolved: [], invalidated: [], expected_outputs: ["IMP"], entry_conditions: ["DET Baselined"], expected_version: 0,
  });
}

test("HOF acknowledgement and acceptance preserve distinct decision evidence", () => {
  const fx = fixture();
  try {
    const prepared = prepareHandoff(fx);
    assert.equal(prepared.status, "Prepared");
    assert.equal(prepared.payload.reason, "design ready");
    assert.deepEqual(prepared.payload.entry_conditions, ["DET Baselined"]);
    assert.equal(fx.store.handoffGet({ ...fx.common, handoff_id: "HOF-001" }).status, "Prepared");
    assert.deepEqual(fx.store.handoffList({ ...fx.common, status: "Prepared" }).map((item) => item.object_id), ["HOF-001"]);

    const acknowledged = fx.store.handoffAcknowledge({
      ...fx.common, handoff_id: "HOF-001", acknowledged_by: "implementation-owner", evidence: ["ack-001"], expected_version: 1,
    });
    assert.equal(acknowledged.status, "Acknowledged");
    assert.equal(acknowledged.payload.acknowledgement.acknowledged_by, "implementation-owner");

    const accepted = fx.store.handoffTransition({
      ...fx.common, handoff_id: "HOF-001", accepted_by: "implementation-owner", reason: "inputs verified",
      evidence: ["review-001"], expected_version: 2,
    }, "Accepted");
    assert.equal(accepted.status, "Accepted");
    assert.equal(accepted.payload.acceptance.accepted_by, "implementation-owner");
    assert.equal(accepted.payload.acceptance.accepted_at, "2026-08-20T00:00:00.000Z");
    assert.equal(accepted.payload.rejection, undefined);
  } finally { fx.close(); }
});

test("HOF rejection and supersession use their own traceable records", () => {
  const fx = fixture();
  try {
    prepareHandoff(fx, "HOF-REJECT");
    const rejected = fx.store.handoffTransition({
      ...fx.common, handoff_id: "HOF-REJECT", rejected_by: "implementation-owner", reason: "input version stale",
      evidence: ["diff-001"], expected_version: 1,
    }, "Rejected");
    assert.equal(rejected.payload.rejection.rejected_by, "implementation-owner");
    assert.equal(rejected.payload.acceptance, undefined);

    const superseded = fx.store.handoffSupersede({
      ...fx.common, handoff_id: "HOF-REJECT", superseded_by: "lifecycle-owner", reason: "replacement HOF-002",
      evidence: ["HOF-002@v1"], expected_version: 2,
    });
    assert.equal(superseded.status, "Superseded");
    assert.equal(superseded.payload.supersession.superseded_by, "lifecycle-owner");
  } finally { fx.close(); }
});

test("CHG archival preserves terminal lifecycle status and rejects active changes", () => {
  const fx = fixture();
  try {
    fx.store.changeGetOrCreate({ ...fx.common, status: "Active", payload: {} });
    assert.throws(
      () => fx.store.archiveChange({ ...fx.common, archived_by: "lifecycle-owner", reason: "premature", expected_version: 1 }),
      (error) => error instanceof DevStateError && error.code === "INVALID_TRANSITION",
    );

    const terminalCommon = { ...fx.common, change_id: "CHG-TERMINAL" };
    const terminalDraft = fx.store.changeGetOrCreate({ ...terminalCommon, payload: {} }).change;
    const terminalActive = fx.store.changePut({ ...terminalCommon, status: "Active", payload: {}, expected_version: terminalDraft.version });
    fx.store.changePut({
      ...terminalCommon, status: "Completed", payload: { completion: { confirmed_by: "owner" } }, expected_version: terminalActive.version,
    });
    const archived = fx.store.archiveChange({
      ...terminalCommon, archived_by: "lifecycle-owner", reason: "retention policy", expected_version: 3,
    });
    assert.equal(archived.status, "Completed");
    assert.equal(archived.payload.archival.archived_by, "lifecycle-owner");
    assert.equal(archived.payload.archival.reason, "retention policy");
  } finally { fx.close(); }
});

test("promotion records intent and confirmation without writing the target", () => {
  const fx = fixture();
  try {
    const target = join(fx.project, "docs", "design.md");
    const prepared = fx.store.promotionPrepare({
      ...fx.common, promotion_id: "PROM-001", source_ref: "DET-001@v3", target_path: target,
      expected_hash: "sha256:abc", expected_version: 0,
    });
    assert.equal(prepared.payload.writes_project, false);
    assert.equal(existsSync(target), false);
    const confirmed = fx.store.promotionConfirm({
      ...fx.common, promotion_id: "PROM-001", actual_path: target, actual_hash: "sha256:abc",
      confirmed_by: "design-owner", expected_version: 1,
    });
    assert.equal(confirmed.status, "Confirmed");
    assert.equal(existsSync(target), false);
  } finally { fx.close(); }
});

test("promotion confirmation rejects a different target", () => {
  const fx = fixture();
  try {
    const target = join(fx.project, "docs", "design.md");
    fx.store.promotionPrepare({
      ...fx.common, promotion_id: "PROM-002", source_ref: "DET-001@v3", target_path: target,
      expected_hash: "sha256:abc", expected_version: 0,
    });
    assert.throws(
      () => fx.store.promotionConfirm({
        ...fx.common, promotion_id: "PROM-002", actual_path: join(fx.project, "other.md"), actual_hash: "sha256:abc",
        confirmed_by: "design-owner", expected_version: 1,
      }),
      (error) => error instanceof DevStateError && error.code === "PROMOTION_MISMATCH",
    );
  } finally { fx.close(); }
});

test("WIT survives unrelated LCV revisions but rejects dependency changes", () => {
  const fx = fixture();
  try {
    const route = [
      { node_id: "design", skill: "dev-lld", dependencies: [], expected_outputs: ["DET"] },
      { node_id: "build", skill: "dev-impl", dependencies: ["design"], expected_outputs: ["IMP"] },
      { node_id: "review", skill: "dev-cr", dependencies: [] },
    ];
    const first = fx.store.lifecyclePut({
      ...fx.common, lifecycle_id: "LCV-FINGERPRINT-1", expected_version: 0, status: "Current",
      payload: { summary: "first", route },
    });
    const prepared = fx.store.workPrepare({
      ...fx.common, work_item_id: "WIT-FINGERPRINT", skill: "dev-impl", input_versions: ["DET-1@v1"],
      lifecycle_route_ref: "LCV-FINGERPRINT-1@v1", route_version: first.version, node_id: "build",
      expected_version: 0,
    });
    assert.match(prepared.payload.route_fingerprint, /^[a-f0-9]{64}$/);
    const second = fx.store.lifecyclePut({
      ...fx.common, lifecycle_id: "LCV-FINGERPRINT-2", expected_version: 0, status: "Current",
      payload: { summary: "clarified", route: [...route.slice(0, 2), { ...route[2], expected_outputs: ["REV"] }] },
      supersedes_lifecycle_id: first.object_id, supersedes_expected_version: first.version,
    });
    const running = fx.store.workClaim({
      ...fx.common, work_item_id: "WIT-FINGERPRINT", agent_id: "impl-agent", expected_version: 1,
    });
    assert.equal(running.status, "Running");
    fx.store.lifecyclePut({
      ...fx.common, lifecycle_id: "LCV-FINGERPRINT-3", expected_version: 0, status: "Current",
      payload: { route: [{ ...route[0], expected_outputs: ["DET", "DVAL"] }, route[1], route[2]] },
      supersedes_lifecycle_id: second.object_id, supersedes_expected_version: second.version,
    });
    assert.throws(() => fx.store.workComplete({
      ...fx.common, work_item_id: "WIT-FINGERPRINT", agent_id: "impl-agent",
      input_fingerprint: running.payload.input_fingerprint, status: "Completed", expected_version: 2,
    }), (error) => error instanceof DevStateError && error.code === "STALE_ROUTE");
    assert.equal(fx.store.workGet({ ...fx.common, work_item_id: "WIT-FINGERPRINT" }).status, "Running");
  } finally { fx.close(); }
});

test("WIT completes after a metadata-only lifecycle revision", () => {
  const fx = fixture();
  try {
    const route = [{ node_id: "build", skill: "dev-impl", dependencies: [] }];
    const first = fx.store.lifecyclePut({
      ...fx.common, lifecycle_id: "LCV-META-1", expected_version: 0, status: "Current", payload: { route, summary: "first" },
    });
    fx.store.workPrepare({
      ...fx.common, work_item_id: "WIT-META", skill: "dev-impl", input_versions: ["DET-1@v1"],
      lifecycle_route_ref: "LCV-META-1@v1", route_version: first.version, node_id: "build", expected_version: 0,
    });
    const running = fx.store.workClaim({
      ...fx.common, work_item_id: "WIT-META", agent_id: "impl-agent", expected_version: 1,
    });
    fx.store.lifecyclePut({
      ...fx.common, lifecycle_id: "LCV-META-2", expected_version: 0, status: "Current",
      payload: { route, summary: "clarified" },
      supersedes_lifecycle_id: first.object_id, supersedes_expected_version: first.version,
    });
    const completed = fx.store.workComplete({
      ...fx.common, work_item_id: "WIT-META", agent_id: "impl-agent",
      input_fingerprint: running.payload.input_fingerprint, status: "Completed", expected_version: 2,
      outputs: ["IMP-1"], evidence: ["test"],
    });
    assert.equal(completed.status, "Completed");
  } finally { fx.close(); }
});

test("artifactGet reads exact historical versions beyond auditList window", () => {
  const fx = fixture();
  try {
    let current;
    for (let version = 0; version < 502; version += 1) {
      current = fx.store.artifactPut({
        ...fx.common, artifact_id: "DET-HISTORY", artifact_type: "DET",
        expected_version: version, status: "Draft", payload: { revision: version + 1 },
      });
    }
    assert.equal(current.version, 502);
    assert.equal(fx.store.artifactGet({ ...fx.common, artifact_id: "DET-HISTORY" }).version, 502);
    const first = fx.store.artifactGet({ ...fx.common, artifact_id: "DET-HISTORY", version: 1 });
    assert.equal(first.payload.revision, 1);
    assert.equal(first.state_uri.endsWith("@v1"), true);
    assert.equal(fx.store.artifactGet({ ...fx.common, artifact_id: "DET-HISTORY", version: 503 }), null);
    assert.equal(fx.store.artifactGet({ ...fx.common, artifact_id: "missing", version: 1 }), null);
    assert.throws(() => fx.store.artifactGet({ ...fx.common, artifact_id: "DET-HISTORY", version: 0 }),
      (error) => error instanceof DevStateError && error.code === "INVALID_ARGUMENT");
  } finally { fx.close(); }
});

test("legacy route-bound WIT retains strict version checking", () => {
  const fx = fixture();
  try {
    const first = fx.store.lifecyclePut({
      ...fx.common, lifecycle_id: "LCV-LEGACY-BOUND-1", expected_version: 0, status: "Current",
      payload: { route: [{ node_id: "build", skill: "dev-impl", dependencies: [] }], summary: "old" },
    });
    fx.store.putObject({
      ...fx.common, object_type: "WIT", object_id: "WIT-LEGACY-BOUND",
      expected_version: 0, status: "Prepared",
      payload: {
        skill: "dev-impl", lifecycle_route_ref: "LCV-LEGACY-BOUND-1@v1",
        route_version: first.version, node_id: "build", attempt: 0,
      },
    });
    fx.store.lifecyclePut({
      ...fx.common, lifecycle_id: "LCV-LEGACY-BOUND-2", expected_version: 0, status: "Current",
      payload: { route: [{ node_id: "build", skill: "dev-impl", dependencies: [] }], summary: "new" },
      supersedes_lifecycle_id: first.object_id, supersedes_expected_version: first.version,
    });
    assert.throws(() => fx.store.workClaim({
      ...fx.common, work_item_id: "WIT-LEGACY-BOUND", agent_id: "impl-agent", expected_version: 1,
    }), (error) => error instanceof DevStateError && error.code === "STALE_ROUTE");
  } finally { fx.close(); }
});
