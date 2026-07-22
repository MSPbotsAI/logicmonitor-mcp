# logicmonitor-mcp

**LogicMonitor** MCP server — exposes the LogicMonitor REST API (v3, `/santaba/rest`) as MCP tools.

## Overview

This server implements the [Model Context Protocol](https://modelcontextprotocol.io/) (Streamable HTTP/SSE transport) and wraps the LogicMonitor endpoints used by MSPbots' own LogicMonitor integration. It follows the MSPbots **Vendor MCP Service SOP**: stateless, no stored credentials, per-request header authentication.

The underlying API authenticates via **LMv1** — a per-request HMAC-SHA256 signature computed from an Access Id / Access Key pair (the same scheme MSPbots itself uses for this integration: Company + Access Id + Access Key, no OAuth). This server computes the LMv1 signature itself for every outgoing request from the credentials supplied in that request's headers; it never persists them.

## Quick Start

### Docker (recommended)

```bash
docker compose up --build
```

The server starts on `http://localhost:8080`.

### Local (uv)

```bash
uv sync
python -m logicmonitor_mcp
```

## Health Check

```bash
curl http://localhost:8080/health
# {"status": "ok", "service": "logicmonitor-mcp", "transport": "http"}
```

No credentials are required for the health endpoint.

## 授权参数说明 (Authentication)

Every request to `/mcp` must include the following HTTP headers:

| Header | 类型 | 是否必填 | 默认值 | 枚举值 | 字段描述 | Example |
|---|---|---|---|---|---|---|
| `X-LogicMonitor-Company` | string | 必填 | 无 | 无(自由文本) | LogicMonitor 门户子域名,即 `https://{company}.logicmonitor.com` 中的 `{company}` 部分,同时也是签名算法中 base URL 的一部分。 | `X-LogicMonitor-Company: acme` |
| `X-LogicMonitor-Access-Id` | string | 必填 | 无 | 无(自由文本) | LMv1 API Token 的 Access Id,与 MSPbots 集成配置里的 "Access Id" 字段一致。 | `X-LogicMonitor-Access-Id: abcd1234efgh5678` |
| `X-LogicMonitor-Access-Key` | string | 必填 | 无 | 无(自由文本,敏感信息) | LMv1 API Token 的 Access Key(密钥),用于对每次请求做 HMAC-SHA256 签名,本服务只在本次请求生命周期内使用,不做持久化存储。 | `X-LogicMonitor-Access-Key: <access_key>` |

Missing any of the three headers returns `401 Unauthorized`.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MCP_HTTP_PORT` | `8080` | Listening port |
| `MCP_HTTP_HOST` | `0.0.0.0` | Listening host |

logicmonitor-mcp has no required environment variables — all identity (company/access id/access key) is per-request via headers.

## MCP Endpoint

```
POST http://localhost:8080/mcp
```

Connect your MCP client with:
- Transport: `http` (Streamable HTTP / SSE)
- Headers: `X-LogicMonitor-Company`, `X-LogicMonitor-Access-Id`, `X-LogicMonitor-Access-Key` (all required)

## Tool List

**15 tools** — matching the 15 LogicMonitor API endpoints already registered under this integration in MSPbots (`sys_integration` subject_code `LOGICMONITOR`), so tool coverage is consistent with MSPbots' existing scope.

### Devices (3)

| Tool | 功能 | 参数 |
|---|---|---|
| `logicmonitor_get_devices` | 列出监控设备 | `size=100`, `offset=0`, `sort?`, `filter?`, `fields?` |
| `logicmonitor_get_device_groups` | 列出设备分组 | `size=100`, `offset=0`, `sort?`, `filter?`, `fields?` |
| `logicmonitor_get_device_properties` | 查设备的自定义/系统属性 | `device_id`, `size=100`, `offset=0`, `filter?` |

### Device DataSources (4)

| Tool | 功能 | 参数 |
|---|---|---|
| `logicmonitor_get_device_datasources` | 列出设备已应用的 DataSource | `device_id`, `size=100`, `offset=0`, `filter?`, `fields?` |
| `logicmonitor_get_device_datasource_instances` | 列出某 DataSource 在设备上的实例 | `device_id`, `source_id`, `size=100`, `offset=0`, `filter?` |
| `logicmonitor_get_device_datasource_data` | 获取 DataSource 采集的数据点 | `device_id`, `source_id`, `start?`, `end?` |
| `logicmonitor_get_device_datasource_instance_alertsettings` | 查 DataSource 实例的告警阈值/设置覆盖 | `device_id`, `source_id`, `instance_id` |

### Alerts (3)

| Tool | 功能 | 参数 |
|---|---|---|
| `logicmonitor_get_alerts` | 列出活跃/历史告警 | `size=50`, `offset=0`, `sort?`, `filter?`, `fields?` |
| `logicmonitor_get_alert_detail` | 查单条告警详情 | `alert_id` |
| `logicmonitor_get_alert_rules` | 列出告警升级规则 | `size=100`, `offset=0`, `filter?` |

### Admin (2)

| Tool | 功能 | 参数 |
|---|---|---|
| `logicmonitor_get_users` | 列出门户用户(admin)账号 | `size=100`, `offset=0`, `filter?`, `fields?` |
| `logicmonitor_get_roles` | 列出角色(权限集) | `size=100`, `offset=0`, `filter?` |

### Reports (2)

| Tool | 功能 | 参数 |
|---|---|---|
| `logicmonitor_get_reports` | 列出报表 | `size=100`, `offset=0`, `filter?`, `fields?` |
| `logicmonitor_get_report_groups` | 列出报表分组 | `size=100`, `offset=0`, `filter?` |

### SDT (1)

| Tool | 功能 | 参数 |
|---|---|---|
| `logicmonitor_get_sdts` | 列出计划停机(Scheduled Down Time)条目 | `size=100`, `offset=0`, `filter?` |

## 测试示例 (Test Example)

List devices:

```json
{
  "method": "tools/call",
  "params": { "name": "logicmonitor_get_devices", "arguments": { "size": 10 } }
}
```

Equivalent `curl` against the running server (streamable HTTP MCP endpoint):

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "X-LogicMonitor-Company: <company>" \
  -H "X-LogicMonitor-Access-Id: <access_id>" \
  -H "X-LogicMonitor-Access-Key: <access_key>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": { "name": "logicmonitor_get_devices", "arguments": { "size": 10 } }
  }'
```

A parameterized call:

```json
{
  "method": "tools/call",
  "params": {
    "name": "logicmonitor_get_device_datasources",
    "arguments": { "device_id": "7186" }
  }
}
```

## API Reference

- Official docs: [LogicMonitor REST API v3](https://www.logicmonitor.com/support/rest-api-developers-guide/overview/using-logicmonitors-rest-api)
- Auth scheme: [LMv1 API Tokens](https://www.logicmonitor.com/support/rest-api-developers-guide/overview/using-logicmonitors-rest-api#Authentication-Tokens)
- Base URL pattern: `https://{company}.logicmonitor.com/santaba/rest`

## Known Gaps / Not Yet Verified

- Not yet tested against a live LogicMonitor portal — only protocol-level verification (health check, 401 on missing headers, `tools/list` returning all 15 tools) has been done so far.
- Tool coverage intentionally matches MSPbots' existing 15 registered LogicMonitor API entries rather than the full LogicMonitor REST API surface (which additionally covers write operations, dashboards, websites, collectors, and LogicModules) — expand on request if broader coverage is needed.
