# LeashMap API & Protocol Contract

> Version: v1 (MVP)
> Date: 2026-06-27
> Status: source of truth for `simulator/`, `server/`, and `app/`

本目录是 Phase 1 的数据契约，三端（设备模拟器、云端、App）都以此为准。
任何字段或路径变更都应先改这里，再改代码。

## 文档

| 文档 | 范围 |
| --- | --- |
| [device-protocol.md](device-protocol.md) | 设备 → 云端上行协议、云端 → 设备下行命令 |
| [realtime-events.md](realtime-events.md) | 云端 → App 实时事件（SSE） |
| [openapi.yaml](openapi.yaml) | 设备接入 + App API 的正式 OpenAPI 3.1 规范 |
| [examples/](examples/) | 请求 / 响应示例 fixtures |

## MVP 传输决定（可回退）

| 链路 | MVP 方案 | 后续 |
| --- | --- | --- |
| 设备 → 云 | HTTP/JSON，`POST /v1/device/*` | 固件阶段加 MQTT over TLS，复用同一 payload schema |
| 云 → App（请求/响应） | HTTP/JSON REST | 不变 |
| 云 → App（实时推送） | SSE，`GET /v1/realtime/stream` | 需要双向时升级 WebSocket |
| 序列化 | JSON | 流量敏感时设备侧改 Protobuf/CBOR（仅编码变，字段不变） |

## 通用约定

### 版本

- URL 前缀统一 `/v1`。
- 设备上行 payload 额外带 `protocol_version`（当前 `1`），便于固件灰度。

### 环境与 Base URL

| 环境 | Base URL（占位） |
| --- | --- |
| local | `http://localhost:8080` |
| dev | `https://dev-api.leashmap.example` |
| staging | `https://staging-api.leashmap.example` |

### ID 格式

均为带前缀、URL 安全、对客户端不透明的字符串。

| 实体 | 前缀 | 示例 |
| --- | --- | --- |
| 用户 | `usr_` | `usr_8f3a1c9b2d4e` |
| 宠物 | `pet_` | `pet_2b7d4f10a6c1` |
| 设备 | `dev_` | `dev_mvp_001` |
| 围栏 | `geo_` | `geo_5c1e9a3b7f02` |
| 告警 | `alt_` | `alt_91b0c7d3e84a` |
| 命令 | `cmd_` | `cmd_44a2f8c1` |

正则：`^(usr|pet|dev|geo|alt|cmd)_[a-z0-9_]{3,40}$`。

### 鉴权

所有接口要求 `Authorization: Bearer <token>`。

- **设备 token**：出厂/激活时下发，标识单台设备，仅可访问 `/v1/device/*`。
- **App session token**：`POST /v1/auth/demo-session` 返回，标识用户，访问 App API。
- MVP 不实现刷新流；token 视为长期有效，过期返回 `unauthenticated`。

### 时间

- 设备上行：Unix epoch **秒**（整数），字段 `ts`。
- App API 响应 / 实时事件：RFC3339 UTC 字符串，如 `2026-06-27T08:00:00Z`。

### 坐标

- WGS84，`lat` ∈ [-90, 90]，`lng` ∈ [-180, 180]。
- App 地图渲染时按地图 SDK 自行做 GCJ-02 等转换；存储与协议一律 WGS84。

### 统一响应包络

成功（App API）直接返回资源对象或 `{ "data": ... , "page": ... }`。

错误统一为：

```json
{
  "error": {
    "code": "invalid_argument",
    "message": "lat must be within [-90, 90]",
    "details": { "field": "lat" },
    "request_id": "req_3f9a2c"
  }
}
```

| code | HTTP | 含义 |
| --- | --- | --- |
| `invalid_argument` | 400 | 参数/ schema 校验失败 |
| `unauthenticated` | 401 | 缺失或无效 token |
| `permission_denied` | 403 | 无权访问该资源 |
| `not_found` | 404 | 资源不存在 |
| `conflict` | 409 | 状态冲突（如设备已绑定） |
| `rate_limited` | 429 | 限流 |
| `internal` | 500 | 服务端错误 |

### 幂等

- 设备上行点带 `seq`（设备内单调递增）；云端按 `(device_id, seq)` 去重。
- 下行命令带 `command_id` 与 `expires_at`，设备按 `command_id` 幂等执行。

### 分页

列表接口用游标分页：`?limit=50&cursor=<opaque>`，响应含 `page.next_cursor`（无更多则为 `null`）。

## 设备绑定流程

```text
1. App  POST /v1/pets                      创建宠物 -> pet_id
2. App  POST /v1/devices/bind              {device_id, pet_id} 绑定
3. 设备  POST /v1/device/heartbeat          上线心跳（设备 token）
4. 设备  POST /v1/device/locations          上报定位点
5. 云端                                     按绑定关系把 device_id 的点归属到 pet_id
6. App  GET  /v1/pets/{petId}/location/latest   查询最新位置
7. App  GET  /v1/realtime/stream            订阅实时事件
```

绑定约束：一台设备同一时刻只能绑定一只宠物；重复绑定返回 `conflict`。
解绑后历史定位点保留，但不再产生新归属。
