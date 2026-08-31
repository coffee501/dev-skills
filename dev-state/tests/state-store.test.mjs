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
    assert.match(change.change.state_uri, /^devstate:\/\/workspace\/WS-/);

    const lcv = fx.store.lifecyclePut({ ...fx.common, expected_version: 0, status: "Active", payload: { route: ["dev-req"] } });
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
    fx.store.lifecyclePut({ ...fx.common, expected_version: 0, status: "Active", payload: {} });
    assert.throws(
      () => fx.store.lifecyclePut({ ...fx.common, expected_version: 0, status: "Active", payload: { stale: true } }),
      (error) => error instanceof DevStateError && error.code === "VERSION_CONFLICT" && error.details.current.version === 1,
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

test("invalidation updates targets atomically", () => {
  const fx = fixture();
  try {
    fx.store.lifecyclePut({ ...fx.common, expected_version: 0, status: "Active", payload: { route: [] } });
    fx.store.artifactPut({
      ...fx.common, artifact_id: "DET-001", artifact_type: "DET", expected_version: 0, status: "Accepted", payload: {},
    });
    const result = fx.store.applyInvalidation({
      ...fx.common, invalidation_id: "INV-001", expected_version: 0, reason: "REQ changed",
      targets: [
        { object_type: "LCV", object_id: "LCV", expected_version: 1, new_status: "NeedsReview", reason: "route changed" },
        { object_type: "ARTIFACT", object_id: "DET-001", expected_version: 1, new_status: "Expired", reason: "input changed" },
      ],
    });
    assert.equal(result.targets[0].status, "NeedsReview");
    assert.equal(result.targets[1].status, "Expired");
    assert.equal(result.invalidation.status, "Applied");
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
