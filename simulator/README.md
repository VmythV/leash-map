# simulator — Device Simulator

在真实硬件就绪前，模拟宠物定位器行为，按 `docs/api` 协议向云端上报，
驱动云端与 App 的端到端联调。详细设计见
[../docs/detailed-design/device-simulator.md](../docs/detailed-design/device-simulator.md)。

## 技术栈

Python 3.12 + uv，HTTP 客户端用 httpx。

## 快速开始

```bash
cd simulator
uv sync

# 先启动云端（另一个终端）：cd ../server && uv run uvicorn leashmap.main:app --port 8080
uv run leashmap-sim --mode normal --route fixtures/park-route.json --interval 1s
# 或不装 console script 直接跑模块：
uv run python -m leashmap_sim --mode exit_zone --count 8 --interval 0.5

uv run pytest -q
```

一键联调（自动起云端 + 跑模拟器 + 打印轨迹与告警）：

```bash
../scripts/demo.sh exit_zone     # 也可 low_battery | offline | drift | lost | normal
```

## CLI 选项

| 选项 | 默认 | 说明 |
| --- | --- | --- |
| `--device-id` | `dev_mvp_001` | 设备 ID |
| `--endpoint` | `http://localhost:8080` | 云端 Base URL |
| `--token` | `dev-token` | 设备 bearer token |
| `--route` | 无（随机游走） | 路线 fixture JSON |
| `--interval` | `1s` | 上报间隔，支持 `5s` / `500ms` / 裸数字(秒) |
| `--battery` | `85` | 初始电量百分比 |
| `--mode` | `normal` | 见下表 |
| `--count` | `20` | 上报点数 |
| `--batch-size` | `5` | offline 模式批量大小 |

## 模式

| mode | 行为 |
| --- | --- |
| `normal` | 按间隔沿路线上报 |
| `lost` | 高频上报（间隔上限 1s），心跳模式 `lost` |
| `offline` | 缓存点，按 `--batch-size` 走批量补传端点（演示离线缓存+补传） |
| `drift` | 注入低精度、偏移点（坏 GNSS 点） |
| `low_battery` | 低初始电量 + 加速消耗，触发低电告警 |
| `exit_zone` | 从路线起点向外直线行走，离开安全区触发离区告警 |

## 代码布局

```text
leashmap_sim/
  cli.py       argparse 入口（console script: leashmap-sim）
  client.py    httpx 设备客户端（location / batch / heartbeat）
  routes.py    路线加载与生成（纯函数：random_walk / walk_away / drift）
  runner.py    模式编排：电量、心跳、批量、上报循环
fixtures/
  park-route.json   示例路线
tests/
  test_routes.py    路线生成与 CLI 解析单测
```

上报 payload 与端点遵循 [../docs/api/device-protocol.md](../docs/api/device-protocol.md)。
