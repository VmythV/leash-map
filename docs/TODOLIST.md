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
- [x] Choose MVP technology stack for cloud service. (Python + FastAPI + Pydantic v2; in-memory store, PostgreSQL/PostGIS later)
- [ ] Choose MVP technology stack for user App.
- [ ] Choose MVP firmware toolchain.
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

- [ ] Validate latitude and longitude range.
- [ ] Validate timestamp drift.
- [ ] Reject impossible speed jumps.
- [ ] Store location source:
  - [ ] GNSS
  - [ ] Cell
  - [ ] Wi-Fi
  - [ ] BLE
  - [ ] Simulator
- [ ] Store accuracy radius.
- [ ] Store battery percentage.
- [ ] Store motion state.
- [ ] Implement latest location cache.
- [ ] Implement trail point query by time range.
- [ ] Implement simple trail downsampling.
- [ ] Implement circular geofence containment check.
- [ ] Implement geofence exit debounce.
- [ ] Implement geofence re-entry detection.
- [ ] Implement low-battery alert.
- [ ] Implement offline alert.
- [ ] Implement alert deduplication.

## 8. Phase 6: Realtime and Notification

- [ ] Choose WebSocket or SSE for App realtime updates.
- [ ] Implement latest-location realtime push.
- [ ] Implement alert realtime push.
- [ ] Implement reconnect handling.
- [ ] Implement basic notification service abstraction.
- [ ] Add placeholder push provider for local development.
- [ ] Add alert delivery status.
- [ ] Add alert acknowledgement API.

## 9. Phase 7: User App MVP

- [ ] Create `app/` project.
- [ ] Implement startup and environment configuration.
- [ ] Implement login or temporary demo session.
- [ ] Implement pet creation screen.
- [ ] Implement device binding screen.
- [ ] Implement map home screen.
- [ ] Display pet latest location.
- [ ] Display device online status.
- [ ] Display battery percentage.
- [ ] Display location accuracy.
- [ ] Display location source.
- [ ] Implement trail playback screen.
- [ ] Implement safe-zone settings screen.
- [ ] Implement alert list screen.
- [ ] Implement lost-pet mode entry.
- [ ] Implement empty states for no device and no location.
- [ ] Implement API client.
- [ ] Implement realtime client.
- [ ] Connect App to simulator-backed cloud data.

## 10. Phase 8: Firmware Skeleton

- [ ] Create `firmware/` project.
- [ ] Set up firmware build toolchain.
- [ ] Define firmware module boundaries.
- [ ] Implement device state machine:
  - [ ] boot
  - [ ] provisioning
  - [ ] idle
  - [ ] tracking
  - [ ] guard
  - [ ] lost
  - [ ] low battery
  - [ ] OTA
  - [ ] fault recovery
- [ ] Implement modem abstraction.
- [ ] Implement GNSS abstraction.
- [ ] Implement IMU abstraction.
- [ ] Implement battery abstraction.
- [ ] Implement local storage queue abstraction.
- [ ] Implement data payload serialization.
- [ ] Implement upload retry strategy.
- [ ] Implement serial logging.
- [ ] Implement configuration storage.
- [ ] Add unit-testable pure logic for state transitions.

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

