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
open http://localhost:8080/demo           # 实时地图 demo（local 环境）：①初始化 ②让宠物走动

uv run pytest -q                          # 测试（内存 SQLite，见 tests/conftest.py）
```

### 数据库迁移（Alembic）

应用启动用 `create_all` 直接建表，开发即开即用。需要演进 schema 时用 Alembic：

```bash
uv run alembic upgrade head                       # 应用迁移
uv run alembic revision --autogenerate -m "msg"   # 改动模型后生成迁移
```

### 实时地图 demo

`GET /demo`（仅 `local`）是一个零外部依赖的自包含网页：Canvas 画安全区 + 轨迹，
经 SSE 实时更新。点「让宠物走动」由云端进程内模拟一段走出安全区的路径，
触发 `location.updated` 与 `exit_zone` 告警。SSE 用 `?access_token=` 查询参数鉴权
（EventSource 无法设置请求头）。

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
    realtime.py  /v1/realtime/stream   SSE（header 或 ?access_token=）
    demo.py      /demo, /demo/seed, /demo/run（仅 local）
  static/
    demo.html    自包含实时地图页
alembic/         数据库迁移（env.py 接 Base.metadata + settings URL）
tests/
  conftest.py    测试用内存 SQLite
  test_smoke.py  端到端闭环：绑定→接入→离区告警→轨迹→低电→ack
  test_offline.py 离线告警扫描
  test_demo.py   demo seed + SSE token-query 鉴权
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
离区防误报告警、低电告警、**离线告警（后台扫描）**、SSE 实时推送、
**实时地图 demo**、demo 会话、SQLite 持久化、**Alembic 迁移**。

后续：
- [ ] 启动改用 `alembic upgrade head`（当前仍 `create_all`）
- [ ] 换 PostgreSQL（仅改 `LEASHMAP_DATABASE_URL`）
- [ ] 下行命令实际入队（寻宠模式 set_mode）
- [ ] 持久化的设备 token / 证书
