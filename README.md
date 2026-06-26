# LeashMap / 领迹

![Status](https://img.shields.io/badge/status-MVP%20planning-blue)
![Scope](https://img.shields.io/badge/scope-pet%20tracking%20system-green)
![Docs](https://img.shields.io/badge/docs-product%20%26%20technical%20planning-lightgrey)

LeashMap, also named **领迹** in Chinese, is a pet safety and movement-trail visualization system.

**中文说明：** 领迹是一款宠物安全与轨迹可视化系统，通过项圈内置或外挂式定位设备采集宠物实时位置与运动轨迹，并在 App 与云端中完成位置追踪、轨迹回放、安全提醒与数据可视化。

> Brand tagline: See every step they take.  
> 品牌口号：看见它的每一步。

## Overview

LeashMap is designed for pet families and pet-related organizations. The product is not positioned as a simple Bluetooth anti-loss tag. It is intended to become a full pet location and trail data system.

**中文说明：** 领迹不是“宠物版 AirTag”，而是围绕实时定位、历史轨迹、电子围栏、安全提醒和云端可视化构建的宠物位置数据系统。

Core capabilities:

- Real-time pet location
- Historical trail playback
- Geofence and safety alerts
- Battery, online status, and location accuracy display
- Motion and activity data
- Cloud-based location and trail storage

## Project Status

This repository is currently in the product definition and MVP planning stage.

Completed planning documents:

- Brand definition
- Product technical plan
- MVP-side development scope
- MVP hardware preparation checklist
- Code development scope before hardware is ready

There is no production application code yet. The recommended next step is to build the first runnable demo with a device simulator, cloud APIs, and an App prototype.

**中文说明：** 当前仓库还没有正式应用代码，建议先用设备模拟器、云端 API 和 App 原型跑通最小闭环。

## MVP Scope

The minimum MVP includes four development areas:

| Area | Responsibility | 中文说明 |
| --- | --- | --- |
| Hardware | Tracker structure, circuit, GNSS, 4G, antenna, battery, waterproofing, charging | 硬件端：定位器结构、电路、定位、通信、天线、电池、防水和充电 |
| Firmware | Location collection, low-power strategy, data upload, offline cache, device status, basic OTA | 固件端：定位采集、低功耗策略、数据上报、离线缓存、设备状态和基础 OTA |
| Cloud | Device access, location storage, trail processing, geofence, alerts, user/pet/device APIs | 云端：设备接入、位置存储、轨迹处理、电子围栏、告警和 API |
| User App | Device binding, real-time location, trail playback, geofence, notifications, lost-pet mode | 用户 App：设备绑定、实时位置、轨迹回放、安全区域、提醒和寻宠模式 |

Deferred for later stages:

- Full admin dashboard / LeashMap Vision
- B2B multi-organization permissions
- Fleet / Shelter / Park product lines
- Store, subscription, community, and pet health analysis
- RTK centimeter-level positioning
- Ultra-miniaturized mass-production Mini hardware

## Technical Direction

Recommended hardware direction:

```text
4G Cat 1 bis + dual-band multi-constellation GNSS + low-power IMU + MCU + cloud OTA
```

Recommended software flow:

```text
Tracker
  -> Firmware collects and uploads low-power location data
  -> Cloud receives, stores, processes trails and alerts
  -> User App displays location, trail history, and safety alerts
```

**中文说明：** 硬件优先选择中成本、低功耗、定位较精准的方案；软件优先打通“设备上报 -> 云端处理 -> App 展示和提醒”的闭环。

## First Runnable Demo

The first demo does not require production hardware. It should prove the core system loop:

1. A device simulator uploads a moving pet route.
2. The cloud stores location points.
3. The App displays the pet's real-time location on a map.
4. The App can replay historical trails.
5. A user can create a circular safe zone.
6. The App receives an alert when the simulated device leaves the safe zone.

**中文说明：** 第一版演示可以先不接真实硬件，用设备模拟器验证云端和 App 的完整链路。

## Hardware Preparation

Recommended P0 hardware for development validation:

- 4G Cat 1 bis development board
- Dual-band GNSS evaluation board
- MCU development board
- LIS2DW12 or equivalent low-power IMU module
- LTE/GNSS antennas and adapter cables
- Test SIM cards from at least two carriers
- 500-700mAh lithium batteries
- Charging module and fuel gauge module
- USB-TTL adapter, ST-Link/J-Link, multimeter, adjustable power supply, power profiler
- Collar samples and simple enclosure materials for field testing

P1 should move to custom PCB, 3D-printed enclosure, waterproof structure, magnetic charging, and engineering prototypes.

**中文说明：** P0 先买开发板和测试工具，不建议一开始就直接投入量产结构。

## Software Work That Can Start Now

These parts can be implemented before real hardware is ready:

- Device simulator
- Cloud APIs
- Database migrations
- Location upload endpoint
- Latest location query
- Historical trail query
- Circular geofence algorithm
- Exit-zone, low-battery, and offline alerts
- App map home screen
- App trail playback
- App safe-zone settings
- Firmware state-machine skeleton
- Firmware data-upload protocol wrapper

Recommended initial repository layout:

```text
app/          User App
server/       Cloud services
simulator/    Device simulator
firmware/     Firmware code
scripts/      Operation and testing scripts
tests/        Automated tests
docs/         Product, technical, and decision documents
```

**中文说明：** 在硬件未完全到位前，可以先写设备模拟器、云端接口、App 原型和固件状态机框架。

## Documentation

| Document | Description | 中文说明 |
| --- | --- | --- |
| [docs/brand.md](docs/brand.md) | Brand name, positioning, values, target users, product naming system | 品牌名称、定位、价值观、目标用户、产品命名体系 |
| [docs/technical-plan.md](docs/technical-plan.md) | Full technical plan, hardware direction, cloud architecture, App, dashboard, data model, acceptance criteria | 完整技术方案、硬件路线、云端架构、App、后台、数据模型、验收标准 |
| [docs/mvp-development-scope.md](docs/mvp-development-scope.md) | MVP development areas, boundaries, deferred areas, acceptance criteria | MVP 四端划分、各端边界、暂缓端侧、验收标准 |
| [docs/mvp-preparation-and-code-scope.md](docs/mvp-preparation-and-code-scope.md) | Hardware checklist, code scope, parallel development plan, first tasks | 硬件准备清单、可先写代码、并行开发方式、首轮任务 |

## Recommended Execution Plan

1. Prepare development validation hardware.
2. Define the device upload protocol and App APIs.
3. Implement the device simulator.
4. Implement cloud location ingestion and storage.
5. Implement the App map home screen.
6. Implement trail playback.
7. Implement circular geofence and alerts.
8. Connect real development-board data.
9. Run small-scale field tests.
10. Refine hardware, power strategy, location filtering, and alert logic based on test results.

**中文说明：** 推荐先用模拟器跑通软件闭环，再接真实开发板，最后进入工程样机和外场测试。

## Product Principles

- Do not build a simple pet AirTag clone.
- Build a pet safety and trail data system.
- Do not claim 100% recovery, never-lost, or zero-error location.
- Validate location, trail, geofence, and alert loops first.
- Use development boards and engineering prototypes before mass-production miniaturization.
- Let software development move ahead with a device simulator.

**中文说明：** 首版重点是验证定位、轨迹、围栏、告警闭环；不做夸张承诺，也不急于量产小型化。

