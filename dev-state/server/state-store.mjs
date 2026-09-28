import { createHash, randomUUID } from "node:crypto";
import { chmodSync, existsSync, mkdirSync, realpathSync } from "node:fs";
import { homedir } from "node:os";
import { basename, isAbsolute, join, posix, relative, resolve, sep, win32 } from "node:path";
import process from "node:process";
import { DatabaseSync } from "node:sqlite";

const SCHEMA_VERSION = 1;
const ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
const WORKSPACE_PATTERN = /^WS-[A-F0-9]{12}$/;
const WORK_TERMINAL = new Set(["Completed", "Blocked", "Failed", "Cancelled"]);
const CHANGE_STATUSES = new Set(["Draft", "Active", "Completed", "Cancelled", "Superseded"]);
const CHANGE_ARCHIVABLE = new Set(["Completed", "Cancelled", "Superseded"]);
const CHANGE_TRANSITIONS = new Map([
  ["Draft", new Set(["Draft", "Active", "Cancelled", "Superseded"])],
  ["Active", new Set(["Active", "Completed", "Cancelled", "Superseded"])],
  ["Completed", new Set(["Completed", "Superseded"])],
  ["Cancelled", new Set(["Cancelled", "Superseded"])],
  ["Superseded", new Set(["Superseded"])],
]);
const LIFECYCLE_STATUSES = new Set(["Current", "Superseded"]);
const HANDOFF_STATUSES = new Set(["Prepared", "Acknowledged", "Accepted", "Rejected", "Superseded"]);

export class DevStateError extends Error {
  constructor(code, message, details = undefined) {
    super(message);
    this.name = "DevStateError";
    this.code = code;
    this.details = details;
  }
}

function requireString(value, label) {
  if (typeof value !== "string" || value.trim() === "") {
    throw new DevStateError("INVALID_ARGUMENT", `${label} must be a non-empty string`);
  }
  return value.trim();
}

function requireId(value, label) {
  const normalized = requireString(value, label);
  if (!ID_PATTERN.test(normalized)) {
    throw new DevStateError("INVALID_ARGUMENT", `${label} contains unsupported characters`);
  }
  return normalized;
}

function requireVersion(value, label = "expected_version") {
  if (!Number.isInteger(value) || value < 0) {
    throw new DevStateError("INVALID_ARGUMENT", `${label} must be a non-negative integer`);
  }
  return value;
}

function requireStatus(value, allowed, label = "status") {
  const normalized = requireString(value, label);
  if (!allowed.has(normalized)) {
    throw new DevStateError("INVALID_ARGUMENT", `${label} must be one of: ${[...allowed].join(", ")}`);
  }
  return normalized;
}

function arrayOrEmpty(value, label) {
  if (value === undefined) return [];
  if (!Array.isArray(value)) {
    throw new DevStateError("INVALID_ARGUMENT", `${label} must be an array`);
  }
  return value;
}

function objectOrEmpty(value, label) {
  if (value === undefined) return {};
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new DevStateError("INVALID_ARGUMENT", `${label} must be an object`);
  }
  return value;
}

function validateChangePayload(payload) {
  if (payload.protocol_version !== "DEV-SUITE-8.1") return;
  for (const field of ["route", "gates", "lifecycle_route_ref"]) {
    if (Object.hasOwn(payload, field)) {
      throw new DevStateError("INVALID_ARGUMENT", "8.1 CHG must not copy LCV-owned " + field);
    }
  }
}

function validateLifecycleRoute(payload) {
  if (payload.protocol_version === undefined && Array.isArray(payload.route)
      && payload.route.some((node) => node && typeof node === "object"
        && (Object.hasOwn(node, "stage") || Object.hasOwn(node, "route_kind")))) {
    throw new DevStateError("INVALID_ROUTE", "formal LCV route requires protocol_version");
  }
  if (!["DEV-SUITE-8.0", "DEV-SUITE-8.1"].includes(payload.protocol_version)
      || !Object.hasOwn(payload, "route")) return;
  const route = payload.route;
  const fail = (message) => { throw new DevStateError("INVALID_ROUTE", message); };
  if (!Array.isArray(route)) fail("8.x LCV route must be an array");
  const nodes = new Map();
  const required = [
    "node_id", "stage", "skill", "applicability", "dependencies",
    "entry_conditions", "expected_outputs", "stop_conditions",
  ];
  const dvalRef = /^DVAL-[A-Za-z0-9._:-]+@v[1-9][0-9]*$/;
  for (const node of route) {
    if (!node || typeof node !== "object" || Array.isArray(node)) fail("route node must be an object");
    for (const field of required) {
      if (!Object.hasOwn(node, field)) fail("route node missing " + field);
    }
    if (typeof node.node_id !== "string" || !ID_PATTERN.test(node.node_id) || nodes.has(node.node_id)) {
      fail("route node_id must be unique and valid");
    }
    if (typeof node.skill !== "string" || !node.skill) fail("route skill must be a non-empty string");
    if (!["Applicable", "NotApplicable"].includes(node.applicability)) fail("route applicability is invalid");
    for (const field of ["agent", "parallel_groups", "attempt", "runtime_status", "work_item_id"]) {
      if (Object.hasOwn(node, field)) fail("route must not contain runtime field " + field);
    }
    for (const field of ["dependencies", "entry_conditions", "expected_outputs", "stop_conditions"]) {
      if (!Array.isArray(node[field])) fail("route " + field + " must be an array");
    }
    if (node.dependencies.some((ref) => typeof ref !== "string" || !ID_PATTERN.test(ref))) {
      fail("route dependencies must be valid node IDs");
    }
    const reason = node.applicability_reason;
    const hasReason = typeof reason === "string" ? reason.trim().length > 0
      : Array.isArray(reason) ? reason.length > 0
      : reason && typeof reason === "object" ? Object.keys(reason).length > 0 : false;
    if (node.applicability === "NotApplicable" && !hasReason) {
      fail("NotApplicable route requires applicability_reason");
    }
    if (node.skill === "dev-cr" && node.applicability === "NotApplicable") {
      const decision = node.applicability_decision;
      if (!decision || typeof decision.owner !== "string" || !decision.owner.trim()
          || ["basis", "residual_risks", "invalidates_when"].some((field) =>
            !Array.isArray(decision[field]) || decision[field].length === 0
            || decision[field].some((item) => typeof item !== "string" || !item.trim()))) {
        fail("NotApplicable dev-cr requires a complete applicability_decision");
      }
    }
    if (node.route_kind !== undefined) {
      if (payload.protocol_version !== "DEV-SUITE-8.1") fail("route_kind requires 8.1");
      if (!["design-probe", "design-validation"].includes(node.route_kind)) fail("unsupported route_kind");
      const isProbe = node.route_kind === "design-probe";
      const expected = isProbe ? ["probe-evidence"] : ["RUN", "EVD"];
      if (node.stage !== "G3" || node.skill !== (isProbe ? "dev-impl" : "dev-val")) {
        fail("design route node must use the G3 specialist");
      }
      if (node.expected_outputs.length !== expected.length
          || node.expected_outputs.some((item) => !expected.includes(item))
          || new Set(node.expected_outputs).size !== expected.length) {
        fail("design route node has invalid expected_outputs");
      }
      if (!Array.isArray(node.design_refs)
          || !node.design_refs.some((ref) => typeof ref === "string" && dvalRef.test(ref))) {
        fail("design route node requires a versioned DVAL");
      }
    }
    nodes.set(node.node_id, node);
  }
  for (const node of route) {
    if (node.dependencies.some((ref) => !nodes.has(ref))) fail("route has an unknown dependency");
  }
  const visiting = new Set();
  const visited = new Set();
  const visit = (id) => {
    if (visiting.has(id)) fail("route dependencies must be acyclic");
    if (visited.has(id)) return;
    visiting.add(id);
    for (const dependency of nodes.get(id).dependencies) visit(dependency);
    visiting.delete(id);
    visited.add(id);
  };
  for (const id of nodes.keys()) visit(id);
  const ancestors = (id) => {
    const result = new Set();
    const pending = [...nodes.get(id).dependencies];
    while (pending.length) {
      const dependency = pending.pop();
      if (result.has(dependency)) continue;
      result.add(dependency);
      pending.push(...nodes.get(dependency).dependencies);
    }
    return result;
  };
  const reviews = route.filter((node) => node.skill === "dev-cr");
  for (const node of reviews) {
    if (node.stage !== "G4") fail("dev-cr must use G4");
  }
  for (const node of route) {
    if (node.applicability !== "Applicable") continue;
    if (node.route_kind === "design-probe") {
      const matches = route.some((candidate) =>
        candidate.route_kind === "design-validation" && candidate.applicability === "Applicable"
        && ancestors(candidate.node_id).has(node.node_id)
        && node.design_refs.some((ref) => candidate.design_refs.includes(ref)));
      if (!matches) fail("design-probe must lead to matching G3 design-validation");
    }
    if (node.skill === "dev-impl" && node.route_kind !== "design-probe") {
      if (node.stage !== "G4") fail("product dev-impl must use G4");
      if (!reviews.some((review) => ancestors(review.node_id).has(node.node_id))) {
        fail("product dev-impl must lead to dev-cr");
      }
    }
    if (node.skill === "dev-val" && node.stage === "G5") {
      const dependencies = ancestors(node.node_id);
      if (reviews.some((review) => review.applicability === "Applicable" && !dependencies.has(review.node_id))) {
        fail("G5 dev-val must depend on all applicable dev-cr");
      }
    }
  }
}

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function digest(value) {
  return createHash("sha256").update(value).digest("hex");
}

function nowIso() {
  return new Date().toISOString();
}

function canonicalPath(input) {
  const absolute = resolve(requireString(input, "path"));
  const real = existsSync(absolute) ? realpathSync.native(absolute) : absolute;
  return process.platform === "win32" ? real.toLowerCase() : real;
}

function pathIsWithin(parent, candidate) {
  const offset = relative(canonicalPath(parent), canonicalPath(candidate));
  return offset === "" || (offset !== ".." && !offset.startsWith(`..${sep}`) && !isAbsolute(offset));
}

export function resolveStateHome(env = process.env, platform = process.platform, userHome = homedir()) {
  const pathApi = platform === "win32" ? win32 : posix;
  if (env.DEV_SKILLS_STATE_HOME?.trim()) return pathApi.resolve(env.DEV_SKILLS_STATE_HOME.trim());
  if (env.CLAUDE_PLUGIN_DATA?.trim()) return pathApi.resolve(env.CLAUDE_PLUGIN_DATA.trim(), "dev-state");
  if (platform === "win32") {
    return win32.resolve(env.LOCALAPPDATA?.trim() || win32.join(userHome, "AppData", "Local"), "dev-skills", "state");
  }
  if (platform === "darwin") return posix.resolve(userHome, "Library", "Application Support", "dev-skills", "state");
  return posix.resolve(env.XDG_STATE_HOME?.trim() || posix.join(userHome, ".local", "state"), "dev-skills");
}

function ensurePrivateDirectory(directory) {
  mkdirSync(directory, { recursive: true, mode: 0o700 });
  if (process.platform !== "win32") {
    try { chmodSync(directory, 0o700); } catch { /* best effort */ }
  }
}

export class StateStore {
  constructor({ stateHome = resolveStateHome(), projectRoot = process.env.CLAUDE_PROJECT_DIR, clock = nowIso } = {}) {
    this.stateHome = resolve(stateHome);
    this.clock = clock;
    if (projectRoot && pathIsWithin(projectRoot, this.stateHome)) {
      throw new DevStateError("STATE_INSIDE_PROJECT", "external state home must not be inside the project");
    }
    ensurePrivateDirectory(this.stateHome);
    this.databasePath = join(this.stateHome, "dev-state.db");
    this.db = new DatabaseSync(this.databasePath);
    try {
      this.db.exec("PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL; PRAGMA busy_timeout = 5000;");
      this.#migrate();
    } catch (error) {
      this.db.close();
      throw error;
    }
    if (process.platform !== "win32") {
      try { chmodSync(this.databasePath, 0o600); } catch { /* best effort */ }
    }
  }

  close() {
    this.db.close();
  }

  info() {
    return { schema_version: SCHEMA_VERSION, state_home: this.stateHome, database_path: this.databasePath };
  }

  #migrate() {
    const currentVersion = this.db.prepare("PRAGMA user_version").get().user_version;
    if (currentVersion > SCHEMA_VERSION) {
      throw new DevStateError("UNSUPPORTED_SCHEMA", `database schema ${currentVersion} is newer than supported ${SCHEMA_VERSION}`);
    }
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS workspaces (
        workspace_id TEXT PRIMARY KEY,
        display_name TEXT NOT NULL,
        git_common_dir TEXT,
        remote_fingerprint TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS workspace_bindings (
        binding_path TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
        created_at TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS objects (
        workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
        change_id TEXT NOT NULL,
        object_type TEXT NOT NULL,
        object_id TEXT NOT NULL,
        version INTEGER NOT NULL,
        status TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        actor TEXT NOT NULL,
        source TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (workspace_id, change_id, object_type, object_id)
      );
      CREATE INDEX IF NOT EXISTS idx_objects_change ON objects(workspace_id, change_id, object_type, status);
      CREATE TABLE IF NOT EXISTS audit_events (
        sequence INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id TEXT NOT NULL,
        change_id TEXT NOT NULL,
        object_type TEXT NOT NULL,
        object_id TEXT NOT NULL,
        operation TEXT NOT NULL,
        from_version INTEGER NOT NULL,
        to_version INTEGER NOT NULL,
        actor TEXT NOT NULL,
        source TEXT NOT NULL,
        snapshot_json TEXT NOT NULL,
        created_at TEXT NOT NULL
      );
      CREATE INDEX IF NOT EXISTS idx_audit_artifact_version
        ON audit_events(workspace_id, change_id, object_type, object_id, to_version);
      PRAGMA user_version = ${SCHEMA_VERSION};
    `);
  }

  #transaction(action) {
    this.db.exec("BEGIN IMMEDIATE");
    try {
      const result = action();
      this.db.exec("COMMIT");
      return result;
    } catch (error) {
      try { this.db.exec("ROLLBACK"); } catch { /* original error wins */ }
      throw error;
    }
  }

  resolveWorkspace(input) {
    const projectPath = canonicalPath(input.project_path);
    const gitCommonDir = input.git_common_dir ? canonicalPath(input.git_common_dir) : null;
    const bindingPath = gitCommonDir || projectPath;
    const displayName = input.display_name?.trim() || basename(projectPath);
    const remoteFingerprint = input.remote_fingerprint?.trim() || null;
    const requestedId = input.workspace_id?.trim() || null;
    if (requestedId && !WORKSPACE_PATTERN.test(requestedId)) {
      throw new DevStateError("INVALID_ARGUMENT", "workspace_id must match WS-[A-F0-9]{12}");
    }
    if (pathIsWithin(projectPath, this.stateHome)) {
      throw new DevStateError("STATE_INSIDE_PROJECT", "external state home must not be inside the project");
    }

    return this.#transaction(() => {
      const byBinding = this.db.prepare(`
        SELECT w.* FROM workspace_bindings b JOIN workspaces w ON w.workspace_id = b.workspace_id
        WHERE b.binding_path = ?
      `).get(bindingPath);
      if (byBinding) return this.#workspaceEnvelope(byBinding, projectPath, bindingPath);

      let workspace = null;
      if (requestedId) {
        workspace = this.db.prepare("SELECT * FROM workspaces WHERE workspace_id = ?").get(requestedId);
        if (!workspace) throw new DevStateError("NOT_FOUND", `workspace ${requestedId} does not exist`);
      }

      const timestamp = this.clock();
      if (!workspace) {
        const workspaceId = `WS-${digest(bindingPath).slice(0, 12).toUpperCase()}`;
        this.db.prepare(`
          INSERT INTO workspaces(workspace_id, display_name, git_common_dir, remote_fingerprint, created_at, updated_at)
          VALUES (?, ?, ?, ?, ?, ?)
        `).run(workspaceId, displayName, gitCommonDir, remoteFingerprint, timestamp, timestamp);
        workspace = this.db.prepare("SELECT * FROM workspaces WHERE workspace_id = ?").get(workspaceId);
      } else {
        this.db.prepare(`
          UPDATE workspaces SET display_name = ?, git_common_dir = COALESCE(?, git_common_dir),
            remote_fingerprint = COALESCE(?, remote_fingerprint), updated_at = ? WHERE workspace_id = ?
        `).run(displayName, gitCommonDir, remoteFingerprint, timestamp, workspace.workspace_id);
        workspace = this.db.prepare("SELECT * FROM workspaces WHERE workspace_id = ?").get(workspace.workspace_id);
      }

      this.#bindPath(workspace.workspace_id, bindingPath, timestamp);
      this.#bindPath(workspace.workspace_id, projectPath, timestamp);
      return this.#workspaceEnvelope(workspace, projectPath, bindingPath);
    });
  }

  #bindPath(workspaceId, bindingPath, timestamp) {
    const existing = this.db.prepare("SELECT workspace_id FROM workspace_bindings WHERE binding_path = ?").get(bindingPath);
    if (existing && existing.workspace_id !== workspaceId) {
      throw new DevStateError("CONFLICT", `binding already belongs to ${existing.workspace_id}`);
    }
    this.db.prepare("INSERT OR IGNORE INTO workspace_bindings(binding_path, workspace_id, created_at) VALUES (?, ?, ?)")
      .run(bindingPath, workspaceId, timestamp);
  }

  #workspaceEnvelope(row, projectPath, bindingPath) {
    return {
      workspace_id: row.workspace_id,
      display_name: row.display_name,
      git_common_dir: row.git_common_dir,
      remote_fingerprint: row.remote_fingerprint,
      project_path: projectPath,
      binding_path: bindingPath,
      state_uri: `devstate://workspace/${row.workspace_id}`,
      state_home: this.stateHome,
    };
  }

  getObject({ workspace_id, change_id, object_type, object_id }) {
    const workspaceId = requireString(workspace_id, "workspace_id");
    if (!WORKSPACE_PATTERN.test(workspaceId)) throw new DevStateError("INVALID_ARGUMENT", "workspace_id is invalid");
    const changeId = requireId(change_id, "change_id");
    const objectType = requireId(object_type, "object_type").toUpperCase();
    const objectId = requireId(object_id, "object_id");
    const row = this.db.prepare(`
      SELECT * FROM objects WHERE workspace_id = ? AND change_id = ? AND object_type = ? AND object_id = ?
    `).get(workspaceId, changeId, objectType, objectId);
    return row ? this.#objectEnvelope(row) : null;
  }

  listObjects({ workspace_id, change_id, object_type, status, limit = 100 }) {
    const workspaceId = requireString(workspace_id, "workspace_id");
    if (!WORKSPACE_PATTERN.test(workspaceId)) throw new DevStateError("INVALID_ARGUMENT", "workspace_id is invalid");
    const changeId = requireId(change_id, "change_id");
    if (!Number.isInteger(limit) || limit < 1 || limit > 200) {
      throw new DevStateError("INVALID_ARGUMENT", "limit must be between 1 and 200");
    }
    const clauses = ["workspace_id = ?", "change_id = ?"];
    const values = [workspaceId, changeId];
    if (object_type) { clauses.push("object_type = ?"); values.push(requireId(object_type, "object_type").toUpperCase()); }
    if (status) { clauses.push("status = ?"); values.push(requireString(status, "status")); }
    values.push(limit);
    return this.db.prepare(`SELECT * FROM objects WHERE ${clauses.join(" AND ")} ORDER BY updated_at DESC LIMIT ?`)
      .all(...values).map((row) => this.#objectEnvelope(row));
  }

  putObject(input) {
    return this.#transaction(() => this.#putObjectInTransaction(input));
  }

  #putObjectInTransaction(input) {
    const workspaceId = requireString(input.workspace_id, "workspace_id");
    if (!WORKSPACE_PATTERN.test(workspaceId)) throw new DevStateError("INVALID_ARGUMENT", "workspace_id is invalid");
    const changeId = requireId(input.change_id, "change_id");
    const objectType = requireId(input.object_type, "object_type").toUpperCase();
    const objectId = requireId(input.object_id, "object_id");
    const expectedVersion = requireVersion(input.expected_version);
    const status = requireString(input.status, "status");
    const actor = requireString(input.actor, "actor");
    const source = requireString(input.source, "source");
    const payload = objectOrEmpty(input.payload, "payload");
    const workspace = this.db.prepare("SELECT workspace_id FROM workspaces WHERE workspace_id = ?").get(workspaceId);
    if (!workspace) throw new DevStateError("NOT_FOUND", `workspace ${workspaceId} does not exist`);

    const current = this.db.prepare(`
      SELECT * FROM objects WHERE workspace_id = ? AND change_id = ? AND object_type = ? AND object_id = ?
    `).get(workspaceId, changeId, objectType, objectId);
    const currentVersion = current?.version || 0;
    if (currentVersion !== expectedVersion) {
      throw new DevStateError("VERSION_CONFLICT", `expected version ${expectedVersion}, found ${currentVersion}`, {
        current: current ? this.#objectEnvelope(current) : null,
      });
    }

    const timestamp = this.clock();
    const nextVersion = currentVersion + 1;
    const payloadJson = canonicalJson(payload);
    if (current) {
      this.db.prepare(`
        UPDATE objects SET version = ?, status = ?, payload_json = ?, actor = ?, source = ?, updated_at = ?
        WHERE workspace_id = ? AND change_id = ? AND object_type = ? AND object_id = ?
      `).run(nextVersion, status, payloadJson, actor, source, timestamp, workspaceId, changeId, objectType, objectId);
    } else {
      this.db.prepare(`
        INSERT INTO objects(workspace_id, change_id, object_type, object_id, version, status, payload_json,
          actor, source, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).run(workspaceId, changeId, objectType, objectId, nextVersion, status, payloadJson, actor, source, timestamp, timestamp);
    }
    const updated = this.db.prepare(`
      SELECT * FROM objects WHERE workspace_id = ? AND change_id = ? AND object_type = ? AND object_id = ?
    `).get(workspaceId, changeId, objectType, objectId);
    const envelope = this.#objectEnvelope(updated);
    this.db.prepare(`
      INSERT INTO audit_events(workspace_id, change_id, object_type, object_id, operation, from_version,
        to_version, actor, source, snapshot_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(workspaceId, changeId, objectType, objectId, current ? "update" : "create", currentVersion,
      nextVersion, actor, source, canonicalJson(envelope), timestamp);
    return envelope;
  }

  #objectEnvelope(row) {
    return {
      workspace_id: row.workspace_id,
      change_id: row.change_id,
      object_type: row.object_type,
      object_id: row.object_id,
      version: row.version,
      status: row.status,
      payload: JSON.parse(row.payload_json),
      actor: row.actor,
      source: row.source,
      created_at: row.created_at,
      updated_at: row.updated_at,
      state_uri: `devstate://workspace/${row.workspace_id}/change/${row.change_id}/${row.object_type}/${row.object_id}@v${row.version}`,
    };
  }

  changeGetOrCreate(input) {
    const existing = this.getObject({ ...input, object_type: "CHG", object_id: input.change_id });
    if (existing) return { created: false, change: existing };
    const status = requireStatus(input.status || "Draft", CHANGE_STATUSES);
    const payload = objectOrEmpty(input.payload, "payload");
    validateChangePayload(payload);
    const change = this.putObject({
      ...input, object_type: "CHG", object_id: input.change_id, expected_version: 0,
      status, payload,
    });
    return { created: true, change };
  }

  changeGet(input) {
    return this.getObject({ ...input, object_type: "CHG", object_id: input.change_id });
  }

  changePut(input) {
    const current = this.#requireObject(input, "CHG", input.change_id);
    const status = requireStatus(input.status, CHANGE_STATUSES);
    if (!CHANGE_TRANSITIONS.get(current.status)?.has(status)) {
      throw new DevStateError("INVALID_TRANSITION", `cannot move change from ${current.status} to ${status}`);
    }
    const payload = objectOrEmpty(input.payload, "payload");
    validateChangePayload(payload);
    return this.putObject({
      ...input, object_type: "CHG", object_id: input.change_id, status, payload,
    });
  }

  lifecycleGet(input) {
    const current = this.listObjects({ ...input, object_type: "LCV", status: "Current", limit: 2 });
    if (current.length > 1) {
      throw new DevStateError("CONFLICT", "multiple Current lifecycle views exist");
    }
    return current[0] || null;
  }

  lifecyclePut(input) {
    const lifecycleId = requireId(input.lifecycle_id, "lifecycle_id");
    if (!lifecycleId.startsWith("LCV-")) {
      throw new DevStateError("INVALID_ARGUMENT", "lifecycle_id must start with LCV-");
    }
    const status = requireStatus(input.status, LIFECYCLE_STATUSES);
    const existing = this.getObject({ ...input, object_type: "LCV", object_id: lifecycleId });
    if (existing) {
      if (existing.status !== "Current" || status !== "Superseded") {
        throw new DevStateError("INVALID_TRANSITION", "an existing lifecycle view is immutable except for Current to Superseded");
      }
      return this.putObject({
        ...input, object_type: "LCV", object_id: lifecycleId, status, payload: existing.payload,
      });
    }
    if (status !== "Current") {
      throw new DevStateError("INVALID_TRANSITION", "a new lifecycle view must start as Current");
    }

    return this.#transaction(() => {
      const current = this.listObjects({ ...input, object_type: "LCV", status: "Current", limit: 2 });
      if (current.length > 1) {
        throw new DevStateError("CONFLICT", "multiple Current lifecycle views exist");
      }
      const payload = objectOrEmpty(input.payload, "payload");
      validateLifecycleRoute(payload);
      if (current.length === 0) {
        if (input.supersedes_lifecycle_id !== undefined || input.supersedes_expected_version !== undefined) {
          throw new DevStateError("INVALID_ARGUMENT", "supersedes fields require a current lifecycle view");
        }
        return this.#putObjectInTransaction({
          ...input, object_type: "LCV", object_id: lifecycleId, status, payload,
        });
      }

      const previous = current[0];
      const supersedesId = requireId(input.supersedes_lifecycle_id, "supersedes_lifecycle_id");
      const supersedesVersion = requireVersion(input.supersedes_expected_version, "supersedes_expected_version");
      if (supersedesId !== previous.object_id || supersedesVersion !== previous.version) {
        throw new DevStateError("VERSION_CONFLICT", "supersedes lifecycle identity or version is stale", { current: previous });
      }
      this.#putObjectInTransaction({
        ...input, object_type: "LCV", object_id: previous.object_id,
        expected_version: previous.version, status: "Superseded",
        payload: { ...previous.payload, superseded_by: `${lifecycleId}@v1` },
      });
      return this.#putObjectInTransaction({
        ...input, object_type: "LCV", object_id: lifecycleId, expected_version: 0, status: "Current",
        payload: { ...payload, supersedes: [previous.state_uri] },
      });
    });
  }

  artifactPut(input) {
    const artifactType = requireId(input.artifact_type, "artifact_type").toUpperCase();
    return this.putObject({
      ...input, object_type: "ARTIFACT", object_id: requireId(input.artifact_id, "artifact_id"),
      payload: { ...objectOrEmpty(input.payload, "payload"), artifact_type: artifactType },
    });
  }

  artifactList(input) {
    const rows = this.listObjects({ ...input, object_type: "ARTIFACT" });
    const artifactType = input.artifact_type?.toUpperCase();
    return artifactType ? rows.filter((item) => item.payload.artifact_type === artifactType) : rows;
  }

  artifactGet(input) {
    const workspaceId = requireString(input.workspace_id, "workspace_id");
    const changeId = requireId(input.change_id, "change_id");
    const artifactId = requireId(input.artifact_id, "artifact_id");
    if (input.version === undefined) {
      return this.getObject({ workspace_id: workspaceId, change_id: changeId, object_type: "ARTIFACT", object_id: artifactId });
    }
    const version = requireVersion(input.version, "version");
    if (version === 0) throw new DevStateError("INVALID_ARGUMENT", "version must be positive");
    const row = this.db.prepare(`
      SELECT snapshot_json FROM audit_events
      WHERE workspace_id = ? AND change_id = ? AND object_type = 'ARTIFACT' AND object_id = ? AND to_version = ?
      ORDER BY sequence DESC LIMIT 1
    `).get(workspaceId, changeId, artifactId, version);
    return row ? JSON.parse(row.snapshot_json) : null;
  }

  workPrepare(input) {
    return this.#transaction(() => {
      const inputVersions = arrayOrEmpty(input.input_versions, "input_versions");
      const lifecycleBinding = this.#lifecycleRouteBinding(input);
      const payload = {
        skill: requireId(input.skill, "skill"),
        ...lifecycleBinding,
        input_versions: inputVersions,
        input_fingerprint: digest(canonicalJson(inputVersions)),
        owned_paths: arrayOrEmpty(input.owned_paths, "owned_paths"),
        owned_artifacts: arrayOrEmpty(input.owned_artifacts, "owned_artifacts"),
        expected_outputs: arrayOrEmpty(input.expected_outputs, "expected_outputs"),
        constraints: objectOrEmpty(input.constraints, "constraints"),
        attempt: 0,
        agent_id: null,
      };
      const workItemId = requireId(input.work_item_id, "work_item_id");
      const current = this.getObject({ ...input, object_type: "WIT", object_id: workItemId });
      if (current) {
        throw new DevStateError("INVALID_TRANSITION", "work item " + workItemId + " already exists in " + current.status);
      }
      return this.#putObjectInTransaction({
        ...input, object_type: "WIT", object_id: workItemId,
        status: "Prepared", payload,
      });
    });
  }

  workGet(input) {
    return this.getObject({ ...input, object_type: "WIT", object_id: input.work_item_id });
  }

  workList(input) {
    return this.listObjects({ ...input, object_type: "WIT" });
  }

  workClaim(input) {
    return this.#transaction(() => {
      const current = this.#requireObject(input, "WIT", input.work_item_id);
      if (!new Set(["Prepared", "Blocked"]).has(current.status)) {
        throw new DevStateError("INVALID_TRANSITION", `cannot claim work item in ${current.status}`);
      }
      this.#assertCurrentRouteBinding(input, current);
      const agentId = requireString(input.agent_id, "agent_id");
      return this.#putObjectInTransaction({
        ...input, object_type: "WIT", object_id: input.work_item_id, status: "Running",
        payload: { ...current.payload, agent_id: agentId, attempt: (current.payload.attempt || 0) + 1, started_at: this.clock() },
      });
    });
  }

  workComplete(input) {
    return this.#transaction(() => {
      const current = this.#requireObject(input, "WIT", input.work_item_id);
      if (current.status !== "Running") throw new DevStateError("INVALID_TRANSITION", "cannot complete work item in " + current.status);
      const agentId = requireString(input.agent_id, "agent_id");
      if (current.payload.agent_id !== agentId) throw new DevStateError("AGENT_MISMATCH", "agent_id does not own this work item");
      const fingerprint = requireString(input.input_fingerprint, "input_fingerprint");
      if (current.payload.input_fingerprint !== fingerprint) {
        throw new DevStateError("STALE_INPUT", "work result input fingerprint does not match current work item");
      }
      const status = requireString(input.status, "status");
      if (!WORK_TERMINAL.has(status)) throw new DevStateError("INVALID_TRANSITION", "unsupported terminal status " + status);
      if (status === "Completed") this.#assertCurrentRouteBinding(input, current);
      const completedAt = this.clock();
      const completed = this.#putObjectInTransaction({
        ...input, object_type: "WIT", object_id: input.work_item_id, status,
        payload: {
          ...current.payload,
          outputs: arrayOrEmpty(input.outputs, "outputs"),
          evidence: arrayOrEmpty(input.evidence, "evidence"),
          result: objectOrEmpty(input.result, "result"),
          completed_at: completedAt,
        },
      });
      const runs = this.#agentRunsForWork(input, input.work_item_id, agentId, "Running");
      for (const run of runs) {
        if (run.payload.input_fingerprint === fingerprint) {
          this.#putObjectInTransaction({
            ...input,
            object_type: "AGENT_RUN",
            object_id: run.object_id,
            expected_version: run.version,
            status,
            payload: { ...run.payload, completed_at: completedAt, work_status: status },
          });
        }
      }
      return completed;
    });
  }

  agentRunBind(input) {
    const workItem = this.#requireObject(input, "WIT", input.work_item_id);
    if (workItem.status !== "Running") {
      throw new DevStateError("INVALID_TRANSITION", `cannot bind agent run to work item in ${workItem.status}`);
    }
    const agentId = requireString(input.agent_id, "agent_id");
    if (workItem.payload.agent_id !== agentId) {
      throw new DevStateError("AGENT_MISMATCH", "agent_id does not own this work item");
    }
    const inputFingerprint = requireString(input.input_fingerprint, "input_fingerprint");
    if (workItem.payload.input_fingerprint !== inputFingerprint) {
      throw new DevStateError("STALE_INPUT", "agent run input fingerprint does not match current work item");
    }
    return this.putObject({
      ...input, object_type: "AGENT_RUN", object_id: requireId(input.run_id || `RUN-${randomUUID()}`, "run_id"),
      status: requireStatus(input.status || "Running", new Set(["Running"]), "status"),
      payload: {
        agent_id: agentId,
        work_item_id: requireId(input.work_item_id, "work_item_id"),
        input_fingerprint: inputFingerprint,
        details: objectOrEmpty(input.details, "details"),
      },
    });
  }

  agentRunList(input) {
    const rows = this.listObjects({ ...input, object_type: "AGENT_RUN" });
    const workItemId = input.work_item_id === undefined ? null : requireId(input.work_item_id, "work_item_id");
    const agentId = input.agent_id === undefined ? null : requireString(input.agent_id, "agent_id");
    return rows.filter((item) => (
      (workItemId === null || item.payload.work_item_id === workItemId)
      && (agentId === null || item.payload.agent_id === agentId)
    ));
  }

  #lifecycleRouteBinding(input) {
    const hasAnyRouteField = input.lifecycle_route_ref !== undefined
      || input.route_version !== undefined
      || input.node_id !== undefined;
    const current = this.lifecycleGet(input);
    if (!current && !hasAnyRouteField) {
      throw new DevStateError("INVALID_ARGUMENT", "Current lifecycle view and route binding are required to prepare work item");
    }
    const lifecycleRouteRef = requireString(input.lifecycle_route_ref, "lifecycle_route_ref");
    const routeVersion = requireVersion(input.route_version, "route_version");
    const nodeId = requireId(input.node_id, "node_id");
    if (!current) {
      throw new DevStateError("STALE_ROUTE", "lifecycle route binding was provided but no Current lifecycle view exists");
    }
    this.#assertRouteMatchesCurrent(input, current, { lifecycle_route_ref: lifecycleRouteRef, route_version: routeVersion, node_id: nodeId });
    return {
      lifecycle_route_ref: lifecycleRouteRef, route_version: routeVersion, node_id: nodeId,
      route_fingerprint: this.#routeFingerprint(current, nodeId),
    };
  }

  #assertCurrentRouteBinding(input, workItem) {
    const binding = {
      lifecycle_route_ref: workItem.payload.lifecycle_route_ref,
      route_version: workItem.payload.route_version,
      node_id: workItem.payload.node_id,
    };
    if (binding.lifecycle_route_ref === undefined && binding.route_version === undefined && binding.node_id === undefined) {
      throw new DevStateError("STALE_ROUTE", "work item has no lifecycle route binding; replan it under the Current lifecycle view");
    }
    const current = this.lifecycleGet(input);
    if (!current) {
      throw new DevStateError("STALE_ROUTE", "work item route binding exists but no Current lifecycle view exists");
    }
    if (workItem.payload.route_fingerprint === undefined) {
      // Existing work items retain their strict version binding until replanned.
      this.#assertRouteMatchesCurrent({ ...input, skill: workItem.payload.skill }, current, binding);
      return;
    }
    const fingerprint = requireString(workItem.payload.route_fingerprint, "route_fingerprint");
    if (fingerprint !== this.#routeFingerprint(current, binding.node_id, workItem.payload.skill)) {
      throw new DevStateError("STALE_ROUTE", "work item route node or its dependencies changed; replan it under the Current lifecycle view");
    }
  }

  #routeFingerprint(current, nodeId, skill) {
    const route = Array.isArray(current.payload.route) ? current.payload.route : [];
    const nodes = new Map();
    for (const node of route) {
      if (!node || typeof node.node_id !== "string") continue;
      if (nodes.has(node.node_id)) throw new DevStateError("STALE_ROUTE", "duplicate route node " + node.node_id);
      nodes.set(node.node_id, node);
    }
    const visited = new Set();
    const visiting = new Set();
    const closure = [];
    const visit = (id) => {
      if (visiting.has(id)) throw new DevStateError("STALE_ROUTE", "cyclic route dependency " + id);
      if (visited.has(id)) return;
      const node = nodes.get(id);
      if (!node) throw new DevStateError("STALE_ROUTE", "route dependency " + id + " is missing");
      visiting.add(id);
      const dependencies = Array.isArray(node.dependencies) ? node.dependencies : [];
      for (const dependency of dependencies) visit(dependency);
      visiting.delete(id);
      visited.add(id);
      closure.push({ ...node, dependencies: [...dependencies].sort() });
    };
    visit(requireId(nodeId, "node_id"));
    const node = nodes.get(nodeId);
    if (skill !== undefined && node.skill !== undefined && node.skill !== skill) {
      throw new DevStateError("STALE_ROUTE", "route node " + nodeId + " changed skill");
    }
    return digest(canonicalJson(closure.sort((a, b) => a.node_id.localeCompare(b.node_id))));
  }

  #assertRouteMatchesCurrent(input, current, binding) {
    const lifecycleRouteRef = requireString(binding.lifecycle_route_ref, "lifecycle_route_ref");
    const routeVersion = requireVersion(binding.route_version, "route_version");
    const nodeId = requireId(binding.node_id, "node_id");
    if (routeVersion !== current.version) {
      throw new DevStateError("STALE_ROUTE", "route_version does not match the Current lifecycle view", { current });
    }
    const shortRef = current.object_id + "@v" + current.version;
    if (lifecycleRouteRef !== current.state_uri && lifecycleRouteRef !== shortRef) {
      throw new DevStateError("STALE_ROUTE", "lifecycle_route_ref does not match the Current lifecycle view", { current });
    }
    const route = Array.isArray(current.payload.route) ? current.payload.route : [];
    if (route.length === 0) {
      throw new DevStateError("STALE_ROUTE", "Current lifecycle view has no route nodes", { current });
    }
    const node = route.find((item) => item?.node_id === nodeId);
    if (!node) {
      throw new DevStateError("STALE_ROUTE", "node_id " + nodeId + " does not exist in the Current lifecycle route", { current });
    }
    if (node.skill !== undefined && node.skill !== input.skill) {
      throw new DevStateError("STALE_ROUTE", "node_id " + nodeId + " is bound to " + node.skill + ", not " + input.skill, { current });
    }
  }

  #agentRunsForWork(input, workItemId, agentId, status) {
    const workspaceId = requireString(input.workspace_id, "workspace_id");
    const changeId = requireId(input.change_id, "change_id");
    const rows = this.db.prepare(`
      SELECT * FROM objects WHERE workspace_id = ? AND change_id = ? AND object_type = 'AGENT_RUN' AND status = ?
    `).all(workspaceId, changeId, requireString(status, "status"));
    const normalizedWorkItemId = requireId(workItemId, "work_item_id");
    const normalizedAgentId = requireString(agentId, "agent_id");
    return rows.map((row) => this.#objectEnvelope(row)).filter((item) => (
      item.payload.work_item_id === normalizedWorkItemId && item.payload.agent_id === normalizedAgentId
    ));
  }

  handoffPrepare(input) {
    const from = requireId(input.from, "from");
    const to = requireId(input.to, "to");
    if (from === to) throw new DevStateError("INVALID_ARGUMENT", "handoff from and to must differ");
    return this.putObject({
      ...input, object_type: "HOF", object_id: requireId(input.handoff_id, "handoff_id"), status: "Prepared",
      payload: {
        from,
        to,
        reason: requireString(input.reason, "reason"),
        inputs: arrayOrEmpty(input.inputs, "inputs"),
        preserved_behavior: arrayOrEmpty(input.preserved_behavior, "preserved_behavior"),
        decisions: arrayOrEmpty(input.decisions, "decisions"),
        unresolved: arrayOrEmpty(input.unresolved, "unresolved"),
        invalidated: arrayOrEmpty(input.invalidated, "invalidated"),
        expected_outputs: arrayOrEmpty(input.expected_outputs, "expected_outputs"),
        entry_conditions: arrayOrEmpty(input.entry_conditions, "entry_conditions"),
      },
    });
  }

  handoffGet(input) {
    return this.getObject({ ...input, object_type: "HOF", object_id: input.handoff_id });
  }

  handoffList(input) {
    return this.listObjects({ ...input, object_type: "HOF" });
  }

  handoffAcknowledge(input) {
    const current = this.#requireObject(input, "HOF", input.handoff_id);
    if (current.status !== "Prepared") {
      throw new DevStateError("INVALID_TRANSITION", `cannot acknowledge handoff in ${current.status}`);
    }
    return this.putObject({
      ...input, object_type: "HOF", object_id: input.handoff_id, status: "Acknowledged",
      payload: {
        ...current.payload,
        acknowledgement: {
          acknowledged_by: requireString(input.acknowledged_by, "acknowledged_by"),
          acknowledged_at: this.clock(),
          evidence: arrayOrEmpty(input.evidence, "evidence"),
        },
      },
    });
  }

  handoffTransition(input, status) {
    requireStatus(status, new Set(["Accepted", "Rejected"]));
    const current = this.#requireObject(input, "HOF", input.handoff_id);
    if (!new Set(["Prepared", "Acknowledged"]).has(current.status)) {
      throw new DevStateError("INVALID_TRANSITION", `cannot ${status.toLowerCase()} handoff in ${current.status}`);
    }
    const decisionEvidence = {
      reason: requireString(input.reason, "reason"),
      evidence: arrayOrEmpty(input.evidence, "evidence"),
    };
    const decision = status === "Accepted"
      ? {
        accepted_by: requireString(input.accepted_by, "accepted_by"),
        accepted_at: this.clock(),
        ...decisionEvidence,
      }
      : {
        rejected_by: requireString(input.rejected_by, "rejected_by"),
        rejected_at: this.clock(),
        ...decisionEvidence,
      };
    return this.putObject({
      ...input, object_type: "HOF", object_id: input.handoff_id, status,
      payload: { ...current.payload, [status === "Accepted" ? "acceptance" : "rejection"]: decision },
    });
  }

  handoffSupersede(input) {
    const current = this.#requireObject(input, "HOF", input.handoff_id);
    if (current.status === "Superseded") {
      throw new DevStateError("INVALID_TRANSITION", "handoff is already superseded");
    }
    return this.putObject({
      ...input, object_type: "HOF", object_id: input.handoff_id, status: "Superseded",
      payload: {
        ...current.payload,
        supersession: {
          superseded_by: requireString(input.superseded_by, "superseded_by"),
          superseded_at: this.clock(),
          reason: requireString(input.reason, "reason"),
          evidence: arrayOrEmpty(input.evidence, "evidence"),
        },
      },
    });
  }

  applyInvalidation(input) {
    const targets = arrayOrEmpty(input.targets, "targets");
    if (targets.length === 0) throw new DevStateError("INVALID_ARGUMENT", "targets must not be empty");
    return this.#transaction(() => {
      const invalidationId = requireId(input.invalidation_id, "invalidation_id");
      const changed = targets.map((target) => {
        const current = this.#requireObject(input, target.object_type, target.object_id);
        const objectType = requireId(target.object_type, "target.object_type").toUpperCase();
        const requestedStatus = requireString(target.new_status, "target.new_status");
        const allowed = objectType === "CHG" ? CHANGE_STATUSES
          : objectType === "LCV" ? LIFECYCLE_STATUSES
            : objectType === "HOF" ? HANDOFF_STATUSES : null;
        const newStatus = allowed ? requireStatus(requestedStatus, allowed, "target.new_status") : requestedStatus;
        return this.#putObjectInTransaction({
          ...input,
          object_type: objectType,
          object_id: target.object_id,
          expected_version: requireVersion(target.expected_version, "target.expected_version"),
          status: newStatus,
          payload: {
            ...current.payload,
            invalidated_by: invalidationId,
            invalidation_reason: requireString(target.reason, "target.reason"),
          },
        });
      });
      const record = this.#putObjectInTransaction({
        ...input, object_type: "INVALIDATION", object_id: invalidationId,
        status: "Applied", payload: { reason: requireString(input.reason, "reason"), targets: changed.map((item) => item.state_uri) },
      });
      return { invalidation: record, targets: changed };
    });
  }

  promotionPrepare(input) {
    return this.putObject({
      ...input, object_type: "PROMOTION", object_id: requireId(input.promotion_id, "promotion_id"), status: "Prepared",
      payload: {
        source_ref: requireString(input.source_ref, "source_ref"),
        target_path: requireString(input.target_path, "target_path"),
        expected_hash: input.expected_hash?.trim() || null,
        authorization_required: true,
        writes_project: false,
      },
    });
  }

  promotionConfirm(input) {
    const current = this.#requireObject(input, "PROMOTION", input.promotion_id);
    if (current.status !== "Prepared") throw new DevStateError("INVALID_TRANSITION", `cannot confirm promotion in ${current.status}`);
    const actualPath = requireString(input.actual_path, "actual_path");
    if (canonicalPath(actualPath) !== canonicalPath(current.payload.target_path)) {
      throw new DevStateError("PROMOTION_MISMATCH", "actual_path does not match the prepared target_path");
    }
    const actualHash = requireString(input.actual_hash, "actual_hash");
    if (current.payload.expected_hash && current.payload.expected_hash !== actualHash) {
      throw new DevStateError("PROMOTION_MISMATCH", "actual_hash does not match the prepared expected_hash");
    }
    return this.putObject({
      ...input, object_type: "PROMOTION", object_id: input.promotion_id, status: "Confirmed",
      payload: {
        ...current.payload,
        actual_path: actualPath,
        actual_hash: actualHash,
        confirmed_by: requireString(input.confirmed_by, "confirmed_by"),
        confirmed_at: this.clock(),
        evidence: arrayOrEmpty(input.evidence, "evidence"),
        writes_project: false,
      },
    });
  }

  archiveChange(input) {
    const current = this.#requireObject(input, "CHG", input.change_id);
    if (!CHANGE_ARCHIVABLE.has(current.status)) {
      throw new DevStateError("INVALID_TRANSITION", `cannot archive change in ${current.status}`);
    }
    return this.putObject({
      ...input, object_type: "CHG", object_id: input.change_id, status: current.status,
      payload: {
        ...current.payload,
        archival: {
          archived_by: requireString(input.archived_by, "archived_by"),
          archived_at: this.clock(),
          reason: requireString(input.reason, "reason"),
        },
      },
    });
  }

  auditList(input) {
    const workspaceId = requireString(input.workspace_id, "workspace_id");
    const changeId = requireId(input.change_id, "change_id");
    const limit = input.limit ?? 100;
    if (!Number.isInteger(limit) || limit < 1 || limit > 500) throw new DevStateError("INVALID_ARGUMENT", "limit must be between 1 and 500");
    return this.db.prepare(`
      SELECT * FROM audit_events WHERE workspace_id = ? AND change_id = ? ORDER BY sequence DESC LIMIT ?
    `).all(workspaceId, changeId, limit).map((row) => ({ ...row, snapshot: JSON.parse(row.snapshot_json), snapshot_json: undefined }));
  }

  #requireObject(input, objectType, objectId) {
    const current = this.getObject({ ...input, object_type: objectType, object_id: objectId });
    if (!current) throw new DevStateError("NOT_FOUND", `${objectType}/${objectId} does not exist`);
    return current;
  }
}
