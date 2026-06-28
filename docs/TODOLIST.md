# LeashMap MVP TODOLIST

> Version: v1.0  
> Date: 2026-06-26  
> Scope: Build the minimum MVP for hardware, firmware, cloud, and user App.

## 1. MVP Goal

Build the first runnable product loop:

```text
Device or simulator uploads pet location
  -> Cloud stores and processes location data
  -> App displays real-time location and historical trails
  -> Geofence triggers safety alerts
```

MVP is complete when a user can bind a device, view the pet's latest location, replay a trail, create a circular safe zone, and receive an alert when the device leaves the zone.

## 2. Phase 0: Project Foundation

- [x] Create initial repository structure:
  - [x] `app/`
  - [x] `server/`
  - [x] `simulator/`
  - [x] `firmware/`
  - [x] `scripts/`
  - [x] `tests/`
  - [x] `docs/`
- [x] Choose MVP technology stack for cloud service. (Python 3.12 + FastAPI + SQLAlchemy/SQLite; PostgreSQL later)
- [x] Choose MVP technology stack for user App. (Flutter + provider + http; Web first)
- [~] Choose MVP firmware toolchain. (C/clang for host-testable core; MCU toolchain TBD at dev-board stage)
- [x] Define environment naming: (docs/api/README.md)
  - [x] local
  - [x] dev
  - [x] staging
- [x] Define device ID format. (docs/api/README.md)
- [x] Define pet ID and user ID strategy. (docs/api/README.md)
- [x] Define API error format. (docs/api/README.md)
- [ ] Define logging convention.
- [ ] Define minimal release naming convention.

## 3. Phase 1: Protocol and Data Contract

> Done. Source of truth: [docs/api/](detailed-design/../api/) — README.md,
> device-protocol.md, realtime-events.md, openapi.yaml, examples/.

- [x] Define device upload protocol. (device-protocol.md)
- [x] Define location point payload. (device-protocol.md §3)
- [x] Define heartbeat payload. (device-protocol.md §5)
- [x] Define battery status payload. (folded into heartbeat/location/event, device-protocol.md §5–6)
- [x] Define device event payload. (device-protocol.md §6)
- [x] Define offline batch upload payload. (device-protocol.md §4)
- [x] Define cloud command payload. (device-protocol.md §8)
- [x] Define App API contract. (openapi.yaml)
- [x] Define WebSocket or SSE real-time event format. (realtime-events.md — SSE for MVP)
- [x] Define geofence alert event format. (realtime-events.md §3)
- [x] Define device binding flow. (README.md)
- [x] Create initial OpenAPI document or equivalent API spec. (openapi.yaml)
- [x] Create example request and response fixtures. (docs/api/examples/)

## 4. Phase 2: Hardware Preparation

- [ ] Purchase 4G Cat 1 bis development board.
- [ ] Purchase dual-band GNSS evaluation board.
- [ ] Purchase MCU development board.
- [ ] Purchase LIS2DW12 or equivalent low-power IMU module.
- [ ] Purchase LTE and GNSS antennas.
- [ ] Purchase antenna adapter cables.
- [ ] Prepare SIM cards from at least two carriers.
- [ ] Prepare 500-700mAh lithium batteries.
- [ ] Prepare charging modules.
- [ ] Prepare fuel gauge modules.
- [ ] Prepare USB-TTL adapters.
- [ ] Prepare ST-Link or J-Link debugger.
- [ ] Prepare multimeter.
- [ ] Prepare adjustable power supply.
- [ ] Prepare power profiler.
- [ ] Prepare collar samples.
- [ ] Prepare simple enclosure materials for field tests.
- [ ] Record supplier, model, firmware version, and purchase channel for each hardware item.

## 5. Phase 3: Device Simulator

> Done (Python 3.12 + uv + httpx). Verified end-to-end via scripts/demo.sh.

- [x] Create `simulator/` project.
- [x] Implement fixed-route location generation. (routes.build_points + fixtures)
- [x] Implement random walk route generation. (routes.random_walk)
- [x] Implement battery drain simulation. (runner)
- [x] Implement online, offline, reconnect states. (offline mode = cache + batch flush)
- [x] Implement low-accuracy GNSS point simulation. (drift mode)
- [x] Implement location drift simulation. (routes.apply_drift)
- [x] Implement geofence exit simulation. (exit_zone mode = routes.walk_away)
- [x] Implement high-frequency lost-pet mode simulation. (lost mode)
- [x] Implement offline cache and batch upload simulation. (offline mode)
- [x] Support CLI configuration for:
  - [x] device ID
  - [x] upload interval
  - [x] route file
  - [x] API endpoint
  - [x] auth token
- [x] Add simulator test fixtures. (fixtures/park-route.json)
- [x] Add simulator README.

## 6. Phase 4: Cloud Foundation

> Done over SQLite (SQLAlchemy 2.0). Tables auto-created via create_all; a
> migration tool (Alembic) and a PostgreSQL swap are the remaining DB items.
> End-to-end loop verified by `server/tests/test_smoke.py` and scripts/demo.sh.

- [x] Create `server/` project.
- [ ] Add database migration system. (Alembic; currently SQLAlchemy create_all)
- [x] Create users table. (SQLite; + sessions)
- [x] Create pets table.
- [x] Create devices table. (device_status)
- [x] Create device bindings table.
- [x] Create location points table.
- [x] Create geofences table.
- [x] Create alerts table.
- [x] Create device events table.
- [x] Implement device authentication.
- [x] Implement location ingestion endpoint. (+ batch)
- [x] Implement heartbeat endpoint.
- [x] Implement latest location query.
- [x] Implement historical trail query.
- [x] Implement pet creation API.
- [x] Implement device binding API.
- [~] Implement circular geofence CRUD. (create + list; update/disable pending)
- [x] Implement alert list API.
- [x] Implement basic API tests. (server/tests/test_smoke.py)
- [x] Implement seed script for local demo data. (scripts/demo.sh seeds via API)

## 7. Phase 5: Location and Geofence Processing

- [x] Validate latitude and longitude range. (Pydantic schema bounds)
- [x] Validate timestamp drift. (max_ts_drift_seconds -> rejected)
- [x] Reject impossible speed jumps. (max_speed_mps vs previous point -> rejected)
- [x] Store location source:
  - [x] GNSS
  - [x] Cell
  - [x] Wi-Fi
  - [x] BLE
  - [x] Simulator
- [x] Store accuracy radius.
- [x] Store battery percentage.
- [x] Store motion state.
- [x] Implement latest location cache. (latest_for_pet query)
- [x] Implement trail point query by time range.
- [x] Implement simple trail downsampling. (Douglas-Peucker when ?downsample=true)
- [x] Implement circular geofence containment check. (haversine)
- [x] Implement geofence exit debounce.
- [x] Implement geofence re-entry detection. (resolves on re-entry)
- [x] Implement low-battery alert.
- [x] Implement offline alert. (background scan of last_seen)
- [x] Implement alert deduplication. (one open alert per pet+type)

## 8. Phase 6: Realtime and Notification

- [x] Choose WebSocket or SSE for App realtime updates. (SSE)
- [x] Implement latest-location realtime push. (location.updated)
- [x] Implement alert realtime push. (alert.created)
- [x] Implement reconnect handling. (App falls back; SSE Last-Event-ID documented)
- [x] Implement basic notification service abstraction. (notifications.py)
- [x] Add placeholder push provider for local development. (ConsoleProvider)
- [x] Add alert delivery status. (notification_deliveries table)
- [x] Implement alert acknowledgement API. (/v1/alerts/{id}/ack)

## 9. Phase 7: User App MVP

> Done (Flutter Web). flutter analyze clean, build web + widget test pass.
> Self-demos via /demo/run. Connects to live API + SSE.

- [x] Create `app/` project.
- [x] Implement startup and environment configuration. (config.dart, --dart-define)
- [x] Implement login or temporary demo session.
- [x] Implement pet creation screen. (auto-create on bootstrap)
- [x] Implement device binding screen. (auto-bind on bootstrap + QR/manual bind screen)
- [x] Implement map home screen. (MiniMap)
- [x] Display pet latest location.
- [x] Display device online status.
- [x] Display battery percentage.
- [x] Display location accuracy.
- [x] Display location source.
- [x] Implement trail playback screen.
- [x] Implement safe-zone settings screen.
- [x] Implement alert list screen.
- [x] Implement lost-pet mode entry. (home toggle -> /v1/pets/{id}/lost-mode -> set_mode command)
- [x] Implement empty states for no device and no location.
- [x] Implement API client.
- [x] Implement realtime client. (SSE)
- [x] Connect App to simulator-backed cloud data.

## 10. Phase 8: Firmware Skeleton

> Pure-logic skeleton done in C (host-testable, make test → 66 checks).
> Hardware driver abstractions come with dev-board integration (Phase 9).

- [x] Create `firmware/` project.
- [x] Set up firmware build toolchain. (clang host build via Makefile; MCU toolchain TBD)
- [x] Define firmware module boundaries.
- [x] Implement device state machine:
  - [x] boot
  - [x] provisioning
  - [x] idle
  - [x] tracking
  - [x] guard
  - [x] lost
  - [x] low battery
  - [x] OTA
  - [x] fault recovery
- [~] Implement modem abstraction. (HAL vtable interface; MCU impl pending)
- [~] Implement GNSS abstraction. (HAL vtable interface; MCU impl pending)
- [~] Implement IMU abstraction. (HAL vtable interface; MCU impl pending)
- [~] Implement battery abstraction. (HAL vtable interface; MCU impl pending)
- [x] Implement local storage queue abstraction. (lm_cache ring buffer)
- [x] Implement data payload serialization. (lm_protocol + command parse/ack)
- [x] Implement upload retry strategy. (offline cache + flush-on-reconnect in lm_app)
- [~] Implement serial logging. (log_event hook in HAL; MCU sink pending)
- [~] Implement configuration storage. (lm_config struct; persistence pending)
- [x] Add unit-testable pure logic for state transitions.
- [x] Add device app orchestrator + downlink command apply/ack. (lm_app, mock-tested)

## 11. Phase 9: Development Board Integration

- [ ] Connect GNSS development board.
- [ ] Parse GNSS output.
- [ ] Extract latitude, longitude, speed, heading, timestamp, and accuracy.
- [ ] Connect Cat 1 bis development board.
- [ ] Establish cellular network connection.
- [ ] Upload heartbeat to cloud.
- [ ] Upload real GNSS location to cloud.
- [ ] Connect IMU module.
- [ ] Detect motion and stillness.
- [ ] Connect battery measurement module.
- [ ] Upload battery status.
- [ ] Validate reconnect after network loss.
- [ ] Validate offline cache and batch upload.
- [ ] Validate App display with real device-board data.

## 12. Phase 10: Power and Field Testing

- [ ] Measure idle current.
- [ ] Measure GNSS acquisition current.
- [ ] Measure cellular upload current.
- [ ] Measure normal tracking mode power.
- [ ] Measure lost-pet mode power.
- [ ] Measure low-battery mode behavior.
- [ ] Run open-sky GNSS test.
- [ ] Run urban street GNSS test.
- [ ] Run park walking route test.
- [ ] Run collar-worn orientation test.
- [ ] Run weak-signal upload test.
- [ ] Run short offline and reconnect test.
- [ ] Record location accuracy statistics.
- [ ] Record upload success rate.
- [ ] Record battery runtime estimate.

## 13. Phase 11: Engineering Prototype

- [ ] Draft MVP PCB block diagram.
- [ ] Confirm module pin mapping.
- [ ] Confirm antenna placement.
- [ ] Confirm charging structure.
- [ ] Confirm battery size.
- [ ] Confirm enclosure size target.
- [ ] Build first custom PCB prototype.
- [ ] Build simple enclosure prototype.
- [ ] Validate basic waterproof structure.
- [ ] Validate collar installation.
- [ ] Validate charging.
- [ ] Validate antenna performance after enclosure installation.
- [ ] Validate thermal behavior during charging and upload.

## 14. Phase 12: MVP Acceptance

- [ ] A device or simulator can upload continuous location data.
- [ ] Cloud can store and query location points.
- [ ] App can show latest pet location.
- [ ] App can replay a historical trail.
- [ ] User can create a circular safe zone.
- [ ] System can generate exit-zone alert.
- [ ] App can display low-battery and offline alerts.
- [ ] Lost-pet mode can increase reporting frequency.
- [ ] Offline cache can be uploaded after reconnect.
- [ ] Basic documentation exists for running the demo.

## 15. Phase 13: Post-MVP Decisions

- [ ] Decide whether to continue with current Cat 1 bis module.
- [ ] Decide whether independent GNSS module is required.
- [ ] Decide whether App stack is acceptable for long-term development.
- [ ] Decide whether cloud architecture should remain monolithic or split into services.
- [ ] Decide when to start LeashMap Vision.
- [ ] Decide when to start B2B organization model.
- [ ] Decide when to start industrial design.
- [ ] Decide certification plan.
- [ ] Decide MVP pilot user group.

