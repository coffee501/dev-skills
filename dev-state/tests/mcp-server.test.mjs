import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { createInterface } from "node:readline";
import test from "node:test";

function startServer() {
  const stateHome = mkdtempSync(join(tmpdir(), "dev-state-mcp-"));
  const child = spawn(process.execPath, ["--disable-warning=ExperimentalWarning", resolve("dev-state/server/dev-state-server.mjs")], {
    cwd: resolve("."), env: { ...process.env, DEV_SKILLS_STATE_HOME: stateHome }, stdio: ["pipe", "pipe", "pipe"],
  });
  const lines = createInterface({ input: child.stdout, crlfDelay: Infinity });
  const queue = [];
  const waiters = [];
  lines.on("line", (line) => {
    const value = JSON.parse(line);
    const waiter = waiters.shift();
    if (waiter) waiter.resolve(value); else queue.push(value);
  });
  function receive() {
    if (queue.length) return Promise.resolve(queue.shift());
    return new Promise((resolvePromise, reject) => {
      const timer = setTimeout(() => reject(new Error("MCP response timeout")), 5000);
      waiters.push({ resolve: (value) => { clearTimeout(timer); resolvePromise(value); } });
    });
  }
  async function request(id, method, params = {}) {
    child.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", id, method, params })}\n`);
    return receive();
  }
  async function close() {
    child.stdin.end();
    await new Promise((resolvePromise) => child.once("exit", resolvePromise));
    rmSync(stateHome, { recursive: true, force: true });
  }
  return { child, request, close };
}

test("MCP server initializes and exposes external-state tools", async () => {
  const server = startServer();
  try {
    const initialized = await server.request(1, "initialize", { protocolVersion: "2025-06-18" });
    assert.equal(initialized.result.serverInfo.name, "dev-state");
    const listed = await server.request(2, "tools/list");
    const names = new Set(listed.result.tools.map((tool) => tool.name));
    for (const name of [
      "workspace_resolve", "change_get", "change_put", "work_prepare", "handoff_prepare", "handoff_get", "handoff_list", "handoff_acknowledge",
      "work_get", "work_list", "agent_run_bind", "agent_run_list",
      "handoff_accept", "handoff_reject", "handoff_supersede", "promotion_prepare", "audit_list",
    ]) assert.ok(names.has(name));
    const resolved = await server.request(3, "tools/call", {
      name: "workspace_resolve", arguments: { project_path: resolve("."), display_name: "dev-skills" },
    });
    assert.ok(resolved.result.structuredContent.workspace_id.startsWith("WS-"));
  } finally { await server.close(); }
});

test("MCP handoff lifecycle records acknowledgement and acceptance", async () => {
  const server = startServer();
  try {
    const resolved = await server.request(1, "tools/call", {
      name: "workspace_resolve", arguments: { project_path: resolve("."), display_name: "dev-skills" },
    });
    const common = {
      workspace_id: resolved.result.structuredContent.workspace_id, change_id: "CHG-MCP", actor: "dev-orch", source: "test",
    };
    const prepared = await server.request(2, "tools/call", {
      name: "handoff_prepare", arguments: {
        ...common, handoff_id: "HOF-MCP", from: "dev-lld", to: "dev-impl", reason: "design ready",
        inputs: ["DET-001@v1"], preserved_behavior: [], decisions: [], unresolved: [], invalidated: [],
        expected_outputs: ["IMP"], entry_conditions: ["DET Baselined"], expected_version: 0,
      },
    });
    assert.equal(prepared.result.structuredContent.status, "Prepared");
    const acknowledged = await server.request(3, "tools/call", {
      name: "handoff_acknowledge", arguments: {
        ...common, handoff_id: "HOF-MCP", acknowledged_by: "implementation-owner", evidence: [], expected_version: 1,
      },
    });
    assert.equal(acknowledged.result.structuredContent.status, "Acknowledged");
    const accepted = await server.request(4, "tools/call", {
      name: "handoff_accept", arguments: {
        ...common, handoff_id: "HOF-MCP", accepted_by: "implementation-owner", reason: "inputs verified",
        evidence: ["review-001"], expected_version: 2,
      },
    });
    assert.equal(accepted.result.structuredContent.payload.acceptance.accepted_by, "implementation-owner");
  } finally { await server.close(); }
});

test("MCP lifecycle views retain LCV identities across atomic replacement", async () => {
  const server = startServer();
  try {
    const resolved = await server.request(1, "tools/call", {
      name: "workspace_resolve", arguments: { project_path: resolve("."), display_name: "dev-skills" },
    });
    const common = {
      workspace_id: resolved.result.structuredContent.workspace_id, change_id: "CHG-LCV", actor: "dev-lc", source: "test",
    };
    const first = await server.request(2, "tools/call", {
      name: "lifecycle_put", arguments: {
        ...common, lifecycle_id: "LCV-MCP-001", expected_version: 0, status: "Current", payload: { route_version: 1 },
      },
    });
    assert.equal(first.result.structuredContent.object_id, "LCV-MCP-001");
    const second = await server.request(3, "tools/call", {
      name: "lifecycle_put", arguments: {
        ...common, lifecycle_id: "LCV-MCP-002", expected_version: 0, status: "Current", payload: { route_version: 2 },
        supersedes_lifecycle_id: "LCV-MCP-001", supersedes_expected_version: 1,
      },
    });
    assert.equal(second.result.structuredContent.object_id, "LCV-MCP-002");
    const current = await server.request(4, "tools/call", { name: "lifecycle_get", arguments: common });
    assert.equal(current.result.structuredContent.object_id, "LCV-MCP-002");
  } finally { await server.close(); }
});

test("MCP tool failures return structured errors", async () => {
  const server = startServer();
  try {
    const response = await server.request(1, "tools/call", { name: "unknown", arguments: {} });
    assert.equal(response.error.code, -32601);
    assert.equal(response.error.data.code, "METHOD_NOT_FOUND");
  } finally { await server.close(); }
});
