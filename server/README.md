# server — LeashMap Cloud

云端后端：接收设备数据、存储位置点、处理轨迹与围栏、生成告警、对 App 提供 API。
契约见 [../docs/api/](../docs/api/)，云端设计见 [../docs/detailed-design/cloud.md](../docs/detailed-design/cloud.md)。

## 技术栈（Phase 0 已定）

- **Python 3.12 + uv** 管理依赖与虚拟环境。
- **FastAPI + Pydantic v2**，SSE 实时推送（`sse-starlette`）。
- **SQLite + SQLAlchemy 2.0** 持久化（`LEASHMAP_DATABASE_URL` 默认 `sqlite:///leashmap.db`）。
  几何计算在 Python 内完成（`leashmap/geo.py`），不依赖 PostGIS；后续换 PostgreSQL
  只需改 URL，ORM 层不变。

## 快速开始

```bash
cd server
uv sync                                   # 创建 .venv(py3.12) 并安装依赖
uv run uvicorn leashmap.main:app --reload --port 8080

curl localhost:8080/health
open http://localhost:8080/docs           # Swagger UI

uv run pytest -q                          # 测试（内存 SQLite，见 tests/conftest.py）
```

配置走环境变量（前缀 `LEASHMAP_`），见 [.env.example](.env.example)。

一键端到端演示（启动云端 + 模拟器联调）见 [`../scripts/demo.sh`](../scripts/demo.sh)。

## 代码布局

```text
leashmap/
  main.py        应用工厂、CORS、/health、异常处理装配
  config.py      环境配置（pydantic-settings）
  db.py          SQLAlchemy 引擎 + ORM 表（SQLite，PostgreSQL-ready）
  store.py       持久化 store：方法返回脱离会话的 DTO
  schemas.py     Pydantic 模型，对应 docs/api/openapi.yaml
  errors.py      统一错误包络
  deps.py        鉴权依赖（设备 token / App session）+ 单例注入
  ids.py         带前缀 ID 生成
  geo.py         haversine 距离（PostGIS 的临时替代）
  broker.py      SSE 进程内 pub/sub（Redis 占位）
  services.py    接入流水线、围栏防误报、告警评估
  web.py         App 路由公共助手（归属校验、记录→响应转换）
  routers/
    device.py    /v1/device/*      设备上行（鉴权：设备 token）
    auth.py      /v1/auth/*        demo 会话
    pets.py      /v1/pets, /v1/devices/bind
    location.py  /v1/pets/{id}/location/latest, /trail
    geofence.py  /v1/pets/{id}/geofences
    alerts.py    /v1/alerts, /v1/alerts/{id}/ack
    realtime.py  /v1/realtime/stream   SSE
tests/
  conftest.py    测试用内存 SQLite
  test_smoke.py  端到端闭环：绑定→接入→离区告警→轨迹→低电→ack
```

## 数据表（SQLite）

`users` `sessions` `pets` `device_bindings` `location_points`
`geofences` `alerts` `device_status` `device_events`

围栏的离区防误报运行态（`consecutive_outside` / `open_alert_id`）暂随
`geofences` 行存储，MVP 从简。

## 概念模块映射（对照 cloud.md）

| 设计模块 | 代码位置 |
| --- | --- |
| api | `routers/` (App 部分) |
| ingest | `routers/device.py` + `services.py` |
| devices / pets | `routers/pets.py` |
| location | `routers/location.py` + `services.py` |
| geofence | `routers/geofence.py` + `services._eval_geofences` |
| alerts | `services._create_alert` + `routers/alerts.py` |
| realtime | `broker.py` + `routers/realtime.py` |
| notifications | 暂用 SSE 推送；推送通道抽象后续补 |
| migrations | SQLAlchemy `create_all` 自动建表；正式迁移工具（Alembic）后续接 |

## MVP 现状与后续

已实现：设备鉴权、单点/批量接入、心跳、事件、最新位置、轨迹、圆形围栏 CRUD、
离区防误报告警、低电告警、SSE 实时推送、demo 会话、SQLite 持久化。

后续：
- [ ] 迁移工具（Alembic）替代 `create_all`
- [ ] 换 PostgreSQL（仅改 `LEASHMAP_DATABASE_URL`）
- [ ] 离线告警（后台定时扫描 `device_status.last_seen`）
- [ ] 下行命令实际入队（寻宠模式 set_mode）
- [ ] 持久化的设备 token / 证书
