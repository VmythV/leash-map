# server — LeashMap Cloud

云端后端：接收设备数据、存储位置点、处理轨迹与围栏、生成告警、对 App 提供 API。
详见 [../docs/detailed-design/cloud.md](../docs/detailed-design/cloud.md)。

## 模块划分

| 目录 | 职责 |
| --- | --- |
| `api/` | 面向 App 的 API |
| `ingest/` | 设备上报接入端点 |
| `devices/` | 设备注册、绑定、在线状态 |
| `pets/` | 宠物资料 |
| `location/` | 位置校验、存储、轨迹查询 |
| `geofence/` | 圆形安全区规则与空间判断 |
| `alerts/` | 告警生成、去重、确认 |
| `realtime/` | WebSocket / SSE 实时推送 |
| `notifications/` | 推送通道抽象 |
| `migrations/` | 数据库 schema 迁移 |

## MVP 范围

包含：设备鉴权、位置接入、最新位置查询、历史轨迹查询、宠物与设备绑定、
圆形围栏 CRUD、离区/低电/离线告警、实时推送、基础诊断日志。

不含：B2B 组织模型、后台大屏、计费订阅、商城、复杂分析与热力图。

## 数据表

`users` `pets` `devices` `device_bindings` `location_points`
`geofences` `alerts` `device_events`

## 主要接口

设备接入：`POST /v1/device/locations` `/locations/batch` `/heartbeat` `/events`
App：`/v1/pets` `/v1/devices/bind` `/v1/pets/{petId}/location/latest`
`/v1/pets/{petId}/trail` `/v1/pets/{petId}/geofences` `/v1/alerts` `/v1/alerts/{id}/ack`

## 待定（Phase 0）

- [ ] 技术栈（语言 / Web 框架 / ORM）
- [ ] 数据库（PostgreSQL + PostGIS / TimescaleDB）
- [ ] 实时通道（WebSocket vs SSE）
