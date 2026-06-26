# 领迹 LeashMap

[English](README.md)

![Status](https://img.shields.io/badge/status-MVP%20planning-blue)
![Scope](https://img.shields.io/badge/scope-pet%20tracking%20system-green)
![Docs](https://img.shields.io/badge/docs-product%20%26%20technical%20planning-lightgrey)

**领迹 / LeashMap** 是一款面向宠物家庭与宠物机构的智能定位品牌，核心定位是：

> 宠物安全与轨迹可视化系统

产品通过项圈内置或外挂式定位设备采集宠物实时位置与运动轨迹，并在 App 与云端中完成位置追踪、轨迹回放、安全提醒与数据可视化。

品牌口号：

> 看见它的每一步

## 项目概览

领迹不是“宠物版 AirTag”，而是围绕实时定位、历史轨迹、电子围栏、安全提醒和云端可视化构建的宠物位置数据系统。

核心能力：

- 宠物实时定位
- 历史轨迹回放
- 电子围栏与安全提醒
- 电量、在线状态、定位精度展示
- 运动与活动数据
- 云端位置与轨迹存储

## 当前阶段

本仓库当前处于产品定义与 MVP 方案阶段。

已完成规划文档：

- 品牌设定
- 产品技术方案
- 最小 MVP 端侧开发划分
- MVP 硬件准备清单
- 硬件未就绪前可先写的代码范围
- MVP 构建 TODOLIST
- MVP 各端详细设计文档

当前还没有正式应用代码。下一步建议先用设备模拟器、云端 API 和 App 原型跑通第一版可运行演示。

## MVP 范围

最小 MVP 先做四块：

| 端侧 | 核心职责 |
| --- | --- |
| 硬件端 | 定位器结构、电路、GNSS、4G、天线、电池、防水、充电 |
| 固件端 | 定位采集、低功耗策略、数据上报、离线缓存、设备状态、OTA 基础能力 |
| 云端 | 设备接入、位置存储、轨迹处理、电子围栏、告警、用户/宠物/设备 API |
| 用户 App | 设备绑定、实时位置、轨迹回放、电子围栏、告警通知、寻宠模式 |

暂缓内容：

- 完整管理端 / 领迹 Vision
- B 端多组织权限
- Fleet / Shelter / Park 等 B 端产品线
- 商城、会员、社区、宠物健康分析
- RTK 厘米级定位
- 极致小型化 Mini 量产硬件

## 技术路线

推荐硬件方向：

```text
4G Cat 1 bis + 双频多星座 GNSS + 低功耗 IMU + MCU + 云端 OTA
```

推荐软件链路：

```text
定位器
  -> 固件低功耗采集并上报位置数据
  -> 云端接收、存储、处理轨迹与告警
  -> 用户 App 查看宠物位置、历史轨迹和安全提醒
```

## 第一版可运行演示

第一版演示不需要真实量产硬件，只需要证明核心系统闭环：

1. 设备模拟器持续上报一条宠物移动路线。
2. 云端保存定位点。
3. App 地图实时显示宠物位置。
4. App 可以回放历史轨迹。
5. 用户可以创建一个圆形安全区域。
6. 模拟设备离开安全区域后，App 收到离区提醒。

## 硬件准备

P0 阶段建议先准备开发验证硬件：

- 4G Cat 1 bis 开发板
- 双频 GNSS 评估板
- MCU 开发板
- LIS2DW12 或同级低功耗 IMU 模块
- LTE/GNSS 天线和转接线
- 至少两个运营商的测试 SIM 卡
- 500-700mAh 锂电池
- 充电模块和电量计模块
- USB-TTL 串口、ST-Link/J-Link、万用表、可调电源、功耗分析工具
- 项圈样品和简易外壳材料，用于外场佩戴测试

P1 阶段再进入自研 PCB、3D 打印外壳、防水结构、磁吸充电和工程样机。

## 可先写代码的部分

真实硬件未到位前，可以先开发：

- 设备模拟器
- 云端 API
- 数据库迁移
- 定位点上报接口
- 最新位置查询接口
- 历史轨迹查询接口
- 圆形电子围栏算法
- 离区、低电、离线告警
- App 地图首页
- App 轨迹回放
- App 安全区域设置
- 固件状态机框架
- 固件数据上报协议封装

建议初始目录规划：

```text
app/          用户 App
server/       云端服务
simulator/    设备模拟器
firmware/     固件代码
scripts/      运维和测试脚本
tests/        自动化测试
docs/         产品、技术和决策文档
```

## 文档导航

| 文档 | 内容 |
| --- | --- |
| [README.md](README.md) | 英文 README |
| [docs/brand.md](docs/brand.md) | 品牌名称、定位、价值观、目标用户、产品命名体系 |
| [docs/technical-plan.md](docs/technical-plan.md) | 完整技术方案、硬件路线、云端架构、App、后台、数据模型、验收标准 |
| [docs/mvp-development-scope.md](docs/mvp-development-scope.md) | MVP 四端划分、各端边界、暂缓端侧、验收标准 |
| [docs/mvp-preparation-and-code-scope.md](docs/mvp-preparation-and-code-scope.md) | 硬件准备清单、可先写代码、并行开发方式、首轮任务 |
| [docs/TODOLIST.md](docs/TODOLIST.md) | 构建 MVP 的端到端任务清单 |
| [docs/detailed-design/README.md](docs/detailed-design/README.md) | MVP 详细设计索引 |
| [docs/detailed-design/hardware.md](docs/detailed-design/hardware.md) | 硬件端详细设计 |
| [docs/detailed-design/firmware.md](docs/detailed-design/firmware.md) | 固件端详细设计 |
| [docs/detailed-design/cloud.md](docs/detailed-design/cloud.md) | 云端详细设计 |
| [docs/detailed-design/app.md](docs/detailed-design/app.md) | 用户 App 详细设计 |
| [docs/detailed-design/device-simulator.md](docs/detailed-design/device-simulator.md) | 设备模拟器详细设计 |

## 推荐执行顺序

1. 准备开发验证硬件。
2. 定义设备上报协议和 App API。
3. 实现设备模拟器。
4. 实现云端定位点接入与存储。
5. 实现 App 地图首页。
6. 实现轨迹回放。
7. 实现圆形电子围栏和告警。
8. 接入真实开发板数据。
9. 做小规模外场测试。
10. 根据测试结果修正硬件、功耗策略、定位过滤和告警逻辑。

## 产品原则

- 不做简单的“宠物版 AirTag”。
- 做宠物安全与轨迹数据系统。
- 不承诺 100% 找回、永不丢失、零误差定位。
- 首先验证定位、轨迹、围栏、告警闭环。
- 在量产小型化前，先使用开发板和工程样机验证。
- 软件可以通过设备模拟器先行开发。
