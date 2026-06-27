# Repository Layout

> 仓库初始目录结构说明。布局依据 `README.md` 的 *Recommended initial repository layout*
> 与 `docs/detailed-design/` 中的详细设计。

| Directory | Responsibility | Detailed design |
| --- | --- | --- |
| `app/` | 用户 App（宠物主人端，地图 / 轨迹 / 围栏 / 告警） | [docs/detailed-design/app.md](docs/detailed-design/app.md) |
| `server/` | 云端服务（设备接入、存储、处理、告警、API） | [docs/detailed-design/cloud.md](docs/detailed-design/cloud.md) |
| `simulator/` | 设备模拟器（无硬件时驱动端到端联调） | [docs/detailed-design/device-simulator.md](docs/detailed-design/device-simulator.md) |
| `firmware/` | 设备固件（状态机、采集、上报、OTA） | [docs/detailed-design/firmware.md](docs/detailed-design/firmware.md) |
| `scripts/` | 运维与测试脚本（本地起服务、seed、联调） | — |
| `tests/` | 跨模块 / 端到端自动化测试 | — |
| `docs/` | 产品、技术与决策文档 | [docs/](docs/) |

## 软件优先（Simulator-first）

MVP 推荐先跑通软件闭环，不等硬件：

```text
simulator/  ->  server/  ->  app/
设备模拟器上传位置  ->  云端存储+围栏+告警  ->  App 地图/轨迹/告警展示
```

`firmware/` 与真实硬件在软件闭环验证后再接入。

## 未决项（Phase 0）

各目录目前仅为骨架，具体技术栈尚未锁定，属 `docs/TODOLIST.md` 的 Phase 0 决策项：

- [ ] 云端服务技术栈
- [ ] 用户 App 技术栈
- [ ] 固件工具链

锁定后请在对应目录的 `README.md` 中补充具体语言、框架与构建方式。
