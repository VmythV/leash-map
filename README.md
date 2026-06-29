# LeashMap

[中文说明](README.zh-CN.md)

![Status](https://img.shields.io/badge/status-MVP%20planning-blue)
![Scope](https://img.shields.io/badge/scope-pet%20tracking%20system-green)
![Docs](https://img.shields.io/badge/docs-product%20%26%20technical%20planning-lightgrey)
[![CI](https://github.com/VmythV/leash-map/actions/workflows/ci.yml/badge.svg)](https://github.com/VmythV/leash-map/actions/workflows/ci.yml)

LeashMap, also named **领迹** in Chinese, is a pet safety and movement-trail visualization system.

> Brand tagline: See every step they take.

## Quickstart

```bash
make test            # run every suite: server, simulator, firmware, app
make demo            # boot the cloud, run the simulator, print trail & alerts
```

The software MVP loop runs without hardware. See [ARCHITECTURE.md](ARCHITECTURE.md)
for how the five components fit together and how data flows.

## Overview

LeashMap is designed for pet families and pet-related organizations. The product is not positioned as a simple Bluetooth anti-loss tag. It is intended to become a full pet location and trail data system.

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
- MVP build TODOLIST
- MVP detailed design documents

There is no production application code yet. The recommended next step is to build the first runnable demo with a device simulator, cloud APIs, and an App prototype.

## MVP Scope

The minimum MVP includes four development areas:

| Area | Responsibility |
| --- | --- |
| Hardware | Tracker structure, circuit, GNSS, 4G, antenna, battery, waterproofing, charging |
| Firmware | Location collection, low-power strategy, data upload, offline cache, device status, basic OTA |
| Cloud | Device access, location storage, trail processing, geofence, alerts, user/pet/device APIs |
| User App | Device binding, real-time location, trail playback, geofence, notifications, lost-pet mode |

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

## First Runnable Demo

The first demo does not require production hardware. It should prove the core system loop:

1. A device simulator uploads a moving pet route.
2. The cloud stores location points.
3. The App displays the pet's real-time location on a map.
4. The App can replay historical trails.
5. A user can create a circular safe zone.
6. The App receives an alert when the simulated device leaves the safe zone.

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

## Documentation

| Document | Description |
| --- | --- |
| [README.zh-CN.md](README.zh-CN.md) | Chinese README |
| [docs/brand.md](docs/brand.md) | Brand name, positioning, values, target users, product naming system |
| [docs/technical-plan.md](docs/technical-plan.md) | Full technical plan, hardware direction, cloud architecture, App, dashboard, data model, acceptance criteria |
| [docs/mvp-development-scope.md](docs/mvp-development-scope.md) | MVP development areas, boundaries, deferred areas, acceptance criteria |
| [docs/mvp-preparation-and-code-scope.md](docs/mvp-preparation-and-code-scope.md) | Hardware checklist, code scope, parallel development plan, first tasks |
| [docs/hardware-procurement.md](docs/hardware-procurement.md) | Consolidated, orderable hardware procurement list (P0 dev boards, tools, P1 prototype; LED-only, no buzzer) |
| [docs/hardware-components.md](docs/hardware-components.md) | Per-component spec: recommended models, role, rationale, firmware mapping, and future expansion points |
| [docs/TODOLIST.md](docs/TODOLIST.md) | End-to-end MVP build checklist |
| [docs/detailed-design/README.md](docs/detailed-design/README.md) | Detailed design index for MVP areas |
| [docs/detailed-design/hardware.md](docs/detailed-design/hardware.md) | Hardware detailed design |
| [docs/detailed-design/firmware.md](docs/detailed-design/firmware.md) | Firmware detailed design |
| [docs/detailed-design/cloud.md](docs/detailed-design/cloud.md) | Cloud detailed design |
| [docs/detailed-design/app.md](docs/detailed-design/app.md) | User App detailed design |
| [docs/detailed-design/device-simulator.md](docs/detailed-design/device-simulator.md) | Device simulator detailed design |
| [docs/api/README.md](docs/api/README.md) | API & protocol contract (conventions, device protocol, realtime, OpenAPI) shared by simulator, server, and app |

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

## Product Principles

- Do not build a simple pet AirTag clone.
- Build a pet safety and trail data system.
- Do not claim 100% recovery, never-lost, or zero-error location.
- Validate location, trail, geofence, and alert loops first.
- Use development boards and engineering prototypes before mass-production miniaturization.
- Let software development move ahead with a device simulator.
