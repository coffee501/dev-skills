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
    for (const name of ["workspace_resolve", "work_prepare", "promotion_prepare", "audit_list"]) assert.ok(names.has(name));
    const resolved = await server.request(3, "tools/call", {
      name: "workspace_resolve", arguments: { project_path: resolve("."), display_name: "dev-skills" },
    });
    assert.ok(resolved.result.structuredContent.workspace_id.startsWith("WS-"));
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
