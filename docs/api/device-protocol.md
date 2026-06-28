# Device Upload Protocol (v1)

> 设备 → 云端上行 + 云端 → 设备下行命令。
> 通用约定（ID、鉴权、时间、错误）见 [README.md](README.md)。

MVP 绑定到 HTTP/JSON；payload 设计为传输无关，固件阶段可整体搬到 MQTT topic
而字段不变。

## 1. 公共字段

每个上行消息都是一个 JSON 对象，含信封字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `type` | string | 是 | `location` / `location_batch` / `heartbeat` / `event` |
| `protocol_version` | int | 是 | 当前 `1` |
| `device_id` | string | 是 | 设备 ID |
| `ts` | int | 是 | 设备侧事件时间，Unix epoch 秒 |

鉴权用设备 token：`Authorization: Bearer <device_token>`。

## 2. 上行端点

| Method | Path | type | 用途 |
| --- | --- | --- | --- |
| POST | `/v1/device/locations` | `location` | 单点上报 |
| POST | `/v1/device/locations/batch` | `location_batch` | 离线缓存批量补传 |
| POST | `/v1/device/heartbeat` | `heartbeat` | 心跳 / 在线 / 电量 / 模式 |
| POST | `/v1/device/events` | `event` | 设备事件（开关机、充电、低电、故障、命令 ack） |

## 3. 定位点 location

```json
{
  "type": "location",
  "protocol_version": 1,
  "device_id": "dev_mvp_001",
  "seq": 1001,
  "ts": 1782432000,
  "lat": 31.2304,
  "lng": 121.4737,
  "accuracy_m": 12.0,
  "source": "gnss",
  "speed_mps": 1.2,
  "heading": 86,
  "battery_pct": 78,
  "motion_state": "moving"
}
```

| 字段 | 类型 | 必填 | 取值 / 说明 |
| --- | --- | --- | --- |
| `seq` | int | 是 | 设备内单调递增，去重用 |
| `lat` `lng` | number | 是 | WGS84 |
| `accuracy_m` | number | 是 | 精度半径（米），用于围栏置信判断 |
| `source` | string | 是 | `gnss` / `cell` / `wifi` / `ble` / `simulator` |
| `speed_mps` | number | 否 | 速度（米/秒） |
| `heading` | number | 否 | 航向角 0–359 |
| `battery_pct` | int | 否 | 0–100 |
| `motion_state` | string | 否 | `still` / `moving` / `unknown` |

## 4. 批量补传 location_batch

离线缓存恢复网络后补传。信封带 `device_id`，点数组省略重复的 `device_id`。

```json
{
  "type": "location_batch",
  "protocol_version": 1,
  "device_id": "dev_mvp_001",
  "ts": 1782432600,
  "points": [
    { "seq": 1002, "ts": 1782432060, "lat": 31.2306, "lng": 121.4740, "accuracy_m": 14.0, "source": "gnss", "battery_pct": 77, "motion_state": "moving" },
    { "seq": 1003, "ts": 1782432120, "lat": 31.2310, "lng": 121.4742, "accuracy_m": 18.0, "source": "gnss", "battery_pct": 77, "motion_state": "moving" }
  ]
}
```

- 单批建议 ≤ 200 点。
- 云端按 `(device_id, seq)` 去重，乱序到达按 `ts` 排序后处理。

## 5. 心跳 heartbeat

```json
{
  "type": "heartbeat",
  "protocol_version": 1,
  "device_id": "dev_mvp_001",
  "ts": 1782432000,
  "battery_pct": 78,
  "mode": "tracking",
  "network": { "type": "cat1bis", "rssi": -84 },
  "firmware_version": "0.1.0"
}
```

| 字段 | 类型 | 必填 | 取值 / 说明 |
| --- | --- | --- | --- |
| `battery_pct` | int | 是 | 0–100 |
| `mode` | string | 是 | `idle` / `tracking` / `guard` / `lost` / `low_battery` |
| `network.type` | string | 否 | `cat1bis` / `wifi` / `simulator` |
| `network.rssi` | int | 否 | 信号强度 dBm |
| `firmware_version` | string | 否 | 固件版本 |

心跳定义在线状态。离线阈值（来自 cloud 设计）：日常 15–30 分钟、寻宠 1–3 分钟、
低电模式放宽。

## 6. 设备事件 event

```json
{
  "type": "event",
  "protocol_version": 1,
  "device_id": "dev_mvp_001",
  "ts": 1782432000,
  "event": "low_battery",
  "data": { "battery_pct": 14 }
}
```

| `event` | `data` 示例 | 说明 |
| --- | --- | --- |
| `power_on` | `{}` | 开机 |
| `power_off` | `{ "reason": "user" }` | 关机 |
| `charging_start` | `{ "battery_pct": 30 }` | 开始充电 |
| `charging_end` | `{ "battery_pct": 95 }` | 结束充电 |
| `low_battery` | `{ "battery_pct": 14 }` | 低电阈值（触发低电告警） |
| `mode_changed` | `{ "from": "idle", "to": "tracking" }` | 模式切换 |
| `fault` | `{ "code": "gnss_timeout" }` | 故障 |
| `command_ack` | `{ "command_id": "cmd_44a2f8c1", "status": "applied" }` | 命令执行回执 |

## 7. 上行响应包络

所有上行端点成功返回：

```json
{
  "ok": true,
  "accepted": 1,
  "duplicated": 0,
  "rejected": 0,
  "server_ts": "2026-06-27T08:00:01Z",
  "commands": [
    {
      "command_id": "cmd_44a2f8c1",
      "type": "set_mode",
      "params": { "mode": "lost" },
      "expires_at": 1782433000
    }
  ]
}
```

| 字段 | 说明 |
| --- | --- |
| `accepted` | 实际入库点数（批量时为去重后数量） |
| `duplicated` | 因 seq 重复被忽略的点数 |
| `rejected` | 因质量过滤被丢弃的点数（时间戳漂移 / 速度跳变） |
| `commands` | 待执行的下行命令（搭车在响应里下发，见下节） |

## 8. 下行命令 command

MVP 用 **搭车下发**：命令放进上行（多为 heartbeat）的响应 `commands` 里。
设备执行后通过 `POST /v1/device/events` 上报 `command_ack`。

```json
{
  "command_id": "cmd_44a2f8c1",
  "type": "set_mode",
  "params": { "mode": "lost" },
  "expires_at": 1782433000
}
```

| `type` | `params` | 用途 |
| --- | --- | --- |
| `set_mode` | `{ "mode": "lost" }` | 切换工作模式（寻宠模式由此触发） |
| `set_interval` | `{ "seconds": 30 }` | 调整上报间隔 |
| `locate_now` | `{}` | 立即定位一次 |
| `ota` | `{ "version": "0.2.0", "url": "..." }` | OTA 升级（MVP 仅占位） |

规则：

- 设备按 `command_id` 幂等执行，已执行过的重复下发直接回 `command_ack`。
- 超过 `expires_at` 的命令丢弃，不执行。
- 命令未 ack 时云端可在后续响应里重复下发，直到 ack 或过期。

## 9. 校验与落点处理（云端）

接入后处理流水线（与 cloud 设计一致）：

1. 校验设备 token 与 payload schema。
2. 拒绝非法坐标 / 时间倒退过大 / 速度跳变不可能的点。
3. 按 `source` + `accuracy_m` 做质量评分。
4. 写入 `location_points`，更新最新位置缓存。
5. 评估圆形围栏（多点防误报，见 realtime/告警）。
6. 生成告警并经 SSE 推送 App。

错误响应沿用统一错误包络（见 README）。例如 schema 不合法返回
`400 invalid_argument`；token 无效返回 `401 unauthenticated`。
