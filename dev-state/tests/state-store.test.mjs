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
    const prepared = fx.store.workPrepare({
      ...fx.common, work_item_id: "WIT-001", skill: "dev-lld", input_versions: ["REQ-001@v2"],
      expected_version: 0, owned_paths: [], owned_artifacts: ["DET-001"], expected_outputs: ["DET"],
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
    fx.store.workPrepare({
      ...fx.common, work_item_id: "WIT-RECOVER", skill: "dev-cr", input_versions: ["IMP-001@v1"],
      expected_version: 0, owned_paths: [], owned_artifacts: ["REV-001"], expected_outputs: ["REV"],
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
