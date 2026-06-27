# server — LeashMap Cloud

云端后端：接收设备数据、存储位置点、处理轨迹与围栏、生成告警、对 App 提供 API。
契约见 [../docs/api/](../docs/api/)，云端设计见 [../docs/detailed-design/cloud.md](../docs/detailed-design/cloud.md)。

## 技术栈（Phase 0 已定）

Python + FastAPI + Pydantic v2，SSE 实时推送（`sse-starlette`）。
**MVP 用进程内内存存储**（`leashmap/store.py`），便于无依赖跑通闭环；
PostgreSQL + PostGIS 作为后续替换（路由/服务层只依赖 store 接口，替换不改调用点）。

## 快速开始

```bash
cd server
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"

# 运行
uvicorn leashmap.main:app --reload --port 8080
# 健康检查
curl localhost:8080/health
# 交互式文档
open http://localhost:8080/docs        # Swagger UI（FastAPI 自动生成）

# 测试
pytest -q
```

配置走环境变量（前缀 `LEASHMAP_`），见 [.env.example](.env.example)。

## 代码布局

```text
leashmap/
  main.py        应用工厂、CORS、/health、异常处理装配
  config.py      环境配置（pydantic-settings）
  schemas.py     Pydantic 模型，对应 docs/api/openapi.yaml
  errors.py      统一错误包络
  deps.py        鉴权依赖（设备 token / App session）+ 单例注入
  ids.py         带前缀 ID 生成
  geo.py         haversine 距离（PostGIS 的临时替代）
  store.py       内存存储（PostgreSQL 占位）
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
  test_smoke.py  端到端闭环：绑定→接入→离区告警→轨迹→低电→ack
```

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
| migrations | 待 PostgreSQL 接入后新增 |

## MVP 现状与后续

已实现（内存）：设备鉴权、单点/批量接入、心跳、事件、最新位置、轨迹、
圆形围栏 CRUD、离区防误报告警、低电告警、SSE 实时推送、demo 会话。

后续：
- [ ] 接 PostgreSQL + PostGIS，新增 `migrations/`
- [ ] 离线告警（需后台定时任务扫描 last_seen）
- [ ] 下行命令实际入队（寻宠模式 set_mode）
- [ ] 持久化的设备 token / 证书
