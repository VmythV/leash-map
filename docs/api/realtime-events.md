# Realtime Events (SSE, v1)

> 云端 → App 单向实时推送。MVP 用 **Server-Sent Events (SSE)**。
> 通用约定见 [README.md](README.md)。

## 1. 连接

```
GET /v1/realtime/stream?pet_id=pet_2b7d4f10a6c1
Authorization: Bearer <app_session_token>
Accept: text/event-stream
```

- `pet_id` 可选；省略则推送当前用户所有宠物的事件。
- 服务端保持长连接，按 SSE 规范输出 `event:` + `data:`。
- 心跳：服务端每 ~15s 发一条注释行 `:keepalive` 防中间层断连。

## 2. SSE 帧格式

```
event: location.updated
id: 1782432000-1001
data: {"pet_id":"pet_2b7d4f10a6c1","device_id":"dev_mvp_001","ts":"2026-06-27T08:00:00Z","lat":31.2304,"lng":121.4737,"accuracy_m":12.0,"source":"gnss","battery_pct":78,"motion_state":"moving"}

```

- `id`：事件游标，断线重连时客户端用 `Last-Event-ID` 头续传。
- `data`：单行 JSON。

## 3. 事件类型

| event | 触发 | data 关键字段 |
| --- | --- | --- |
| `location.updated` | 新有效定位点入库 | `pet_id, device_id, ts, lat, lng, accuracy_m, source, battery_pct, motion_state` |
| `alert.created` | 生成新告警 | `alert_id, pet_id, device_id, type, severity, status, message, created_at, location_point_id` |
| `device.status_updated` | 在线/离线变化 | `device_id, pet_id, online, mode, last_seen_at` |
| `device.battery_updated` | 电量显著变化 | `device_id, pet_id, battery_pct, charging, ts` |

### alert.created 示例

```json
{
  "alert_id": "alt_91b0c7d3e84a",
  "pet_id": "pet_2b7d4f10a6c1",
  "device_id": "dev_mvp_001",
  "type": "exit_zone",
  "severity": "warning",
  "status": "open",
  "message": "Buddy 可能离开了安全区域「家」",
  "created_at": "2026-06-27T08:01:30Z",
  "location_point_id": 88123
}
```

`type` ∈ `exit_zone` / `low_battery` / `offline`；
`severity` ∈ `info` / `warning` / `critical`；
`status` ∈ `open` / `acknowledged` / `resolved`。

## 4. 围栏离区防误报（影响 alert.created 时机）

与 cloud 设计一致：

- 仅用 `accuracy_m` 小于阈值的点触发强提醒；精度差但趋势离区发弱提醒。
- 连续 2 个有效点在围栏外，或持续超过配置时长，才推 `exit_zone`。
- 一条 `exit_zone` 告警 open 期间对同一围栏去重，回到围栏内置为 `resolved`。

## 5. 客户端容错（App 侧约定）

- SSE 断开显示「重连中」，并降级为轮询 `GET /v1/pets/{petId}/location/latest`。
- 实时失败绝不阻塞地图展示「最后已知位置」。
- 重连带 `Last-Event-ID` 续传，避免漏事件。

## 6. 升级路径

需要双向（如 App 主动下发寻宠命令的低延迟确认）时，将 `/v1/realtime/stream`
升级为 WebSocket，事件名与 data schema 保持不变。
