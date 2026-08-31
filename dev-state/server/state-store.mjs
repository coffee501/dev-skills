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
    const change = this.putObject({
      ...input, object_type: "CHG", object_id: input.change_id, expected_version: 0,
      status: input.status || "Draft", payload: objectOrEmpty(input.payload, "payload"),
    });
    return { created: true, change };
  }

  lifecycleGet(input) {
    return this.getObject({ ...input, object_type: "LCV", object_id: "LCV" });
  }

  lifecyclePut(input) {
    return this.putObject({ ...input, object_type: "LCV", object_id: "LCV" });
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

  workPrepare(input) {
    const inputVersions = arrayOrEmpty(input.input_versions, "input_versions");
    const payload = {
      skill: requireId(input.skill, "skill"),
      input_versions: inputVersions,
      input_fingerprint: digest(canonicalJson(inputVersions)),
      owned_paths: arrayOrEmpty(input.owned_paths, "owned_paths"),
      owned_artifacts: arrayOrEmpty(input.owned_artifacts, "owned_artifacts"),
      expected_outputs: arrayOrEmpty(input.expected_outputs, "expected_outputs"),
      constraints: objectOrEmpty(input.constraints, "constraints"),
      attempt: 0,
      agent_id: null,
    };
    return this.putObject({
      ...input, object_type: "WIT", object_id: requireId(input.work_item_id, "work_item_id"),
      status: "Prepared", payload,
    });
  }

  workClaim(input) {
    const current = this.#requireObject(input, "WIT", input.work_item_id);
    if (!new Set(["Prepared", "Blocked"]).has(current.status)) {
      throw new DevStateError("INVALID_TRANSITION", `cannot claim work item in ${current.status}`);
    }
    const agentId = requireString(input.agent_id, "agent_id");
    return this.putObject({
      ...input, object_type: "WIT", object_id: input.work_item_id, status: "Running",
      payload: { ...current.payload, agent_id: agentId, attempt: (current.payload.attempt || 0) + 1, started_at: this.clock() },
    });
  }

  workComplete(input) {
    const current = this.#requireObject(input, "WIT", input.work_item_id);
    if (current.status !== "Running") throw new DevStateError("INVALID_TRANSITION", `cannot complete work item in ${current.status}`);
    const agentId = requireString(input.agent_id, "agent_id");
    if (current.payload.agent_id !== agentId) throw new DevStateError("AGENT_MISMATCH", "agent_id does not own this work item");
    const fingerprint = requireString(input.input_fingerprint, "input_fingerprint");
    if (current.payload.input_fingerprint !== fingerprint) {
      throw new DevStateError("STALE_INPUT", "work result input fingerprint does not match current work item");
    }
    const status = requireString(input.status, "status");
    if (!WORK_TERMINAL.has(status)) throw new DevStateError("INVALID_TRANSITION", `unsupported terminal status ${status}`);
    return this.putObject({
      ...input, object_type: "WIT", object_id: input.work_item_id, status,
      payload: {
        ...current.payload,
        outputs: arrayOrEmpty(input.outputs, "outputs"),
        evidence: arrayOrEmpty(input.evidence, "evidence"),
        result: objectOrEmpty(input.result, "result"),
        completed_at: this.clock(),
      },
    });
  }

  agentRunBind(input) {
    return this.putObject({
      ...input, object_type: "AGENT_RUN", object_id: requireId(input.run_id || `RUN-${randomUUID()}`, "run_id"),
      status: input.status || "Running",
      payload: {
        agent_id: requireString(input.agent_id, "agent_id"),
        work_item_id: requireId(input.work_item_id, "work_item_id"),
        input_fingerprint: requireString(input.input_fingerprint, "input_fingerprint"),
        details: objectOrEmpty(input.details, "details"),
      },
    });
  }

  handoffPrepare(input) {
    return this.putObject({
      ...input, object_type: "HOF", object_id: requireId(input.handoff_id, "handoff_id"), status: "Prepared",
      payload: {
        from: requireId(input.from, "from"),
        to: requireId(input.to, "to"),
        inputs: arrayOrEmpty(input.inputs, "inputs"),
        expected_outputs: arrayOrEmpty(input.expected_outputs, "expected_outputs"),
        unresolved: arrayOrEmpty(input.unresolved, "unresolved"),
        preserved_behavior: arrayOrEmpty(input.preserved_behavior, "preserved_behavior"),
      },
    });
  }

  handoffTransition(input, status) {
    const current = this.#requireObject(input, "HOF", input.handoff_id);
    if (current.status !== "Prepared") throw new DevStateError("INVALID_TRANSITION", `cannot ${status.toLowerCase()} handoff in ${current.status}`);
    const acceptance = {
      decided_by: requireString(input.decided_by, "decided_by"),
      decided_at: this.clock(),
      reason: requireString(input.reason, "reason"),
      evidence: arrayOrEmpty(input.evidence, "evidence"),
    };
    return this.putObject({
      ...input, object_type: "HOF", object_id: input.handoff_id, status,
      payload: { ...current.payload, acceptance },
    });
  }

  applyInvalidation(input) {
    const targets = arrayOrEmpty(input.targets, "targets");
    if (targets.length === 0) throw new DevStateError("INVALID_ARGUMENT", "targets must not be empty");
    return this.#transaction(() => {
      const invalidationId = requireId(input.invalidation_id, "invalidation_id");
      const changed = targets.map((target) => {
        const current = this.#requireObject(input, target.object_type, target.object_id);
        return this.#putObjectInTransaction({
          ...input,
          object_type: target.object_type,
          object_id: target.object_id,
          expected_version: requireVersion(target.expected_version, "target.expected_version"),
          status: requireString(target.new_status, "target.new_status"),
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
    return this.putObject({
      ...input, object_type: "CHG", object_id: input.change_id, status: "Archived",
      payload: { ...current.payload, archived_by: requireString(input.archived_by, "archived_by"), archived_at: this.clock(), archive_reason: requireString(input.reason, "reason") },
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
