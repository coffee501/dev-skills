#!/usr/bin/env node
import { createInterface } from "node:readline";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import { DevStateError, StateStore } from "./state-store.mjs";

const COMMON_WRITE = {
  workspace_id: { type: "string" }, change_id: { type: "string" }, expected_version: { type: "integer", minimum: 0 },
  actor: { type: "string" }, source: { type: "string" },
};

function schema(properties, required = []) {
  return { type: "object", additionalProperties: false, properties, required };
}

const tools = [
  { name: "state_info", description: "读取外部状态位置和架构版本；不得写入项目。", inputSchema: schema({}) },
  { name: "workspace_resolve", description: "解析或绑定项目到外部工作区。", inputSchema: schema({
    project_path: { type: "string" }, git_common_dir: { type: "string" }, remote_fingerprint: { type: "string" },
    display_name: { type: "string" }, workspace_id: { type: "string" },
  }, ["project_path"]) },
  { name: "change_get_or_create", description: "在外部状态中读取或创建 CHG。", inputSchema: schema({
    ...COMMON_WRITE, status: { type: "string" }, payload: { type: "object" },
  }, ["workspace_id", "change_id", "actor", "source"]) },
  { name: "lifecycle_get", description: "读取变更当前的外部 LCV。", inputSchema: schema({
    workspace_id: { type: "string" }, change_id: { type: "string" },
  }, ["workspace_id", "change_id"]) },
  { name: "lifecycle_put", description: "使用乐观版本控制创建或更新外部 LCV。", inputSchema: schema({
    ...COMMON_WRITE, status: { type: "string" }, payload: { type: "object" },
  }, ["workspace_id", "change_id", "expected_version", "status", "payload", "actor", "source"]) },
  { name: "artifact_put", description: "在项目外登记中间产物。", inputSchema: schema({
    ...COMMON_WRITE, artifact_id: { type: "string" }, artifact_type: { type: "string" }, status: { type: "string" }, payload: { type: "object" },
  }, ["workspace_id", "change_id", "artifact_id", "artifact_type", "expected_version", "status", "actor", "source"]) },
  { name: "artifact_list", description: "列出外部中间产物。", inputSchema: schema({
    workspace_id: { type: "string" }, change_id: { type: "string" }, artifact_type: { type: "string" }, status: { type: "string" }, limit: { type: "integer" },
  }, ["workspace_id", "change_id"]) },
  { name: "work_prepare", description: "创建带输入指纹的版本化 WIT。", inputSchema: schema({
    ...COMMON_WRITE, work_item_id: { type: "string" }, skill: { type: "string" }, input_versions: { type: "array" },
    owned_paths: { type: "array" }, owned_artifacts: { type: "array" }, expected_outputs: { type: "array" }, constraints: { type: "object" },
  }, ["workspace_id", "change_id", "work_item_id", "skill", "input_versions", "expected_version", "actor", "source"]) },
  { name: "work_claim", description: "按当前版本为 Agent 认领 WIT。", inputSchema: schema({
    ...COMMON_WRITE, work_item_id: { type: "string" }, agent_id: { type: "string" },
  }, ["workspace_id", "change_id", "work_item_id", "agent_id", "expected_version", "actor", "source"]) },
  { name: "work_complete", description: "完成或阻塞 WIT；拒绝过期指纹或错误 Agent。", inputSchema: schema({
    ...COMMON_WRITE, work_item_id: { type: "string" }, agent_id: { type: "string" }, input_fingerprint: { type: "string" },
    status: { enum: ["Completed", "Blocked", "Failed", "Cancelled"] }, outputs: { type: "array" }, evidence: { type: "array" }, result: { type: "object" },
  }, ["workspace_id", "change_id", "work_item_id", "agent_id", "input_fingerprint", "status", "expected_version", "actor", "source"]) },
  { name: "agent_run_bind", description: "将 Agent 运行绑定到 WIT 和输入指纹。", inputSchema: schema({
    ...COMMON_WRITE, run_id: { type: "string" }, agent_id: { type: "string" }, work_item_id: { type: "string" },
    input_fingerprint: { type: "string" }, status: { type: "string" }, details: { type: "object" },
  }, ["workspace_id", "change_id", "agent_id", "work_item_id", "input_fingerprint", "expected_version", "actor", "source"]) },
  { name: "handoff_prepare", description: "在外部状态中创建 Prepared HOF。", inputSchema: schema({
    ...COMMON_WRITE, handoff_id: { type: "string" }, from: { type: "string" }, to: { type: "string" }, inputs: { type: "array" },
    expected_outputs: { type: "array" }, unresolved: { type: "array" }, preserved_behavior: { type: "array" },
  }, ["workspace_id", "change_id", "handoff_id", "from", "to", "expected_version", "actor", "source"]) },
  { name: "handoff_accept", description: "使用决策证据接受 Prepared HOF。", inputSchema: schema({
    ...COMMON_WRITE, handoff_id: { type: "string" }, decided_by: { type: "string" }, reason: { type: "string" }, evidence: { type: "array" },
  }, ["workspace_id", "change_id", "handoff_id", "decided_by", "reason", "expected_version", "actor", "source"]) },
  { name: "handoff_reject", description: "拒绝 Prepared HOF 并保留原因。", inputSchema: schema({
    ...COMMON_WRITE, handoff_id: { type: "string" }, decided_by: { type: "string" }, reason: { type: "string" }, evidence: { type: "array" },
  }, ["workspace_id", "change_id", "handoff_id", "decided_by", "reason", "expected_version", "actor", "source"]) },
  { name: "invalidation_apply", description: "原子标记受影响对象并记录失效信息。", inputSchema: schema({
    ...COMMON_WRITE, invalidation_id: { type: "string" }, reason: { type: "string" }, targets: { type: "array" },
  }, ["workspace_id", "change_id", "invalidation_id", "reason", "targets", "expected_version", "actor", "source"]) },
  { name: "promotion_prepare", description: "记录最终产物晋升意图；不得写入目标文件。", inputSchema: schema({
    ...COMMON_WRITE, promotion_id: { type: "string" }, source_ref: { type: "string" }, target_path: { type: "string" }, expected_hash: { type: "string" },
  }, ["workspace_id", "change_id", "promotion_id", "source_ref", "target_path", "expected_version", "actor", "source"]) },
  { name: "promotion_confirm", description: "记录已授权的最终产物写入；本工具不写入目标文件。", inputSchema: schema({
    ...COMMON_WRITE, promotion_id: { type: "string" }, actual_path: { type: "string" }, actual_hash: { type: "string" },
    confirmed_by: { type: "string" }, evidence: { type: "array" },
  }, ["workspace_id", "change_id", "promotion_id", "actual_path", "actual_hash", "confirmed_by", "expected_version", "actor", "source"]) },
  { name: "change_archive", description: "归档 CHG，不删除状态或审计历史。", inputSchema: schema({
    ...COMMON_WRITE, archived_by: { type: "string" }, reason: { type: "string" },
  }, ["workspace_id", "change_id", "archived_by", "reason", "expected_version", "actor", "source"]) },
  { name: "audit_list", description: "列出变更的不可变审计事件。", inputSchema: schema({
    workspace_id: { type: "string" }, change_id: { type: "string" }, limit: { type: "integer" },
  }, ["workspace_id", "change_id"]) },
];

const handlers = {
  state_info: (store) => store.info(),
  workspace_resolve: (store, args) => store.resolveWorkspace(args),
  change_get_or_create: (store, args) => store.changeGetOrCreate(args),
  lifecycle_get: (store, args) => store.lifecycleGet(args),
  lifecycle_put: (store, args) => store.lifecyclePut(args),
  artifact_put: (store, args) => store.artifactPut(args),
  artifact_list: (store, args) => store.artifactList(args),
  work_prepare: (store, args) => store.workPrepare(args),
  work_claim: (store, args) => store.workClaim(args),
  work_complete: (store, args) => store.workComplete(args),
  agent_run_bind: (store, args) => store.agentRunBind(args),
  handoff_prepare: (store, args) => store.handoffPrepare(args),
  handoff_accept: (store, args) => store.handoffTransition(args, "Accepted"),
  handoff_reject: (store, args) => store.handoffTransition(args, "Rejected"),
  invalidation_apply: (store, args) => store.applyInvalidation(args),
  promotion_prepare: (store, args) => store.promotionPrepare(args),
  promotion_confirm: (store, args) => store.promotionConfirm(args),
  change_archive: (store, args) => store.archiveChange(args),
  audit_list: (store, args) => store.auditList(args),
};

export class DevStateMcpServer {
  constructor(store = new StateStore()) {
    this.store = store;
  }

  close() { this.store.close(); }

  async handle(message) {
    if (message.method === "initialize") {
      return {
        protocolVersion: message.params?.protocolVersion || "2025-06-18",
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: "dev-state", version: "1.0.0" },
      };
    }
    if (message.method === "ping") return {};
    if (message.method === "tools/list") return { tools };
    if (message.method === "tools/call") {
      const name = message.params?.name;
      const handler = handlers[name];
      if (!handler) throw new DevStateError("METHOD_NOT_FOUND", `unknown tool ${name}`);
      const result = await handler(this.store, message.params?.arguments || {});
      return { content: [{ type: "text", text: JSON.stringify(result) }], structuredContent: result };
    }
    if (message.method?.startsWith("notifications/")) return undefined;
    throw new DevStateError("METHOD_NOT_FOUND", `unsupported method ${message.method}`);
  }
}

async function main() {
  const server = new DevStateMcpServer();
  const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
  for await (const line of input) {
    if (!line.trim()) continue;
    let message;
    try {
      message = JSON.parse(line);
      const result = await server.handle(message);
      if (message.id !== undefined && result !== undefined) {
        process.stdout.write(`${JSON.stringify({ jsonrpc: "2.0", id: message.id, result })}\n`);
      }
    } catch (error) {
      if (message?.id !== undefined) {
        const known = error instanceof DevStateError;
        process.stdout.write(`${JSON.stringify({
          jsonrpc: "2.0",
          id: message.id,
          error: {
            code: known && error.code === "METHOD_NOT_FOUND" ? -32601 : -32000,
            message: error.message,
            data: known ? { code: error.code, details: error.details } : { code: "INTERNAL_ERROR" },
          },
        })}\n`);
      }
    }
  }
  server.close();
}

if (process.argv[1] && fileURLToPath(import.meta.url) === resolve(process.argv[1])) {
  main().catch((error) => {
    process.stderr.write(`dev-state fatal: ${error.message}\n`);
    process.exitCode = 1;
  });
}
