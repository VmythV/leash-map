# LeashMap Architecture

How the pieces fit and how data flows. Per-component detail lives in each
directory's README; the API contract is the source of truth in
[docs/api/](docs/api/).

## Components

| Component | Dir | Stack | Role |
| --- | --- | --- | --- |
| Contract | `docs/api/` | OpenAPI 3.1 + Markdown | Source of truth shared by all ends |
| Device simulator | `simulator/` | Python 3.12 (uv) + httpx | Drives the cloud over HTTP without hardware |
| Firmware core | `firmware/` | C11 (host-testable) | State machine, protocol, cache, driver HAL, app loop |
| Cloud | `server/` | Python 3.12 (uv) · FastAPI · SQLAlchemy/SQLite · SSE | Ingest, store, geofence/alerts, realtime, downlink commands |
| User App | `app/` | Flutter (Web) · flutter_map · provider | Map, trail, safe zone, alerts, lost-mode, QR bind |

## Data flow

```text
                         docs/api  (one contract)
                              │
  ┌──────────────┐  HTTP/JSON │   ┌───────────────────────── server (cloud) ─────────────────────────┐
  │ simulator    │────────────┼──▶│ /v1/device/*  ─▶ services ─▶ SQLite (SQLAlchemy)                  │
  │ (or firmware │  uplink     │   │   ingest ─▶ geofence/low-battery/offline alerts                   │
  │  on a board) │            │   │   broker (SSE)            notifications (console)                  │
  └──────▲───────┘            │   │        │                         │                                 │
         │  commands (downlink)│   │   pending command queue          │                                 │
         │  on uplink response │   └────────┼─────────────────────────┼─────────────────────────────────┘
         │                     │            │ SSE events              │ REST
         │                     │            ▼                         ▼
         │                     │   ┌──────────────────────── app (Flutter) ─────────────────────────┐
         └─────────────────────┼───│ map (live follow) · trail · safe zone · alerts · lost-mode · QR │
           set_mode etc.       │   └─────────────────────────────────────────────────────────────────┘
```

- **Uplink** (device → cloud): `POST /v1/device/{locations,locations/batch,heartbeat,events}`,
  device bearer token. Payloads in [device-protocol.md](docs/api/device-protocol.md).
- **Realtime** (cloud → app): SSE `GET /v1/realtime/stream` —
  `location.updated`, `alert.created`, `device.status_updated`, `device.battery_updated`.
- **Downlink** (cloud → device): commands piggyback on the uplink response
  `commands[]` until the device acks via a `command_ack` event.

## Two vertical loops (proven end-to-end)

1. **Exit-zone alert** — device leaves a circular safe zone → debounced
   `exit_zone` alert → SSE → App map marker turns red + alert appears.
2. **Lost-pet command** — App toggle → `POST /v1/pets/{id}/lost-mode` enqueues
   `set_mode lost` → delivered on next uplink → device applies + `command_ack`
   → no longer delivered. (Firmware side mock-tested in `firmware/tests/test_app.c`.)

## Run & test

```bash
make test            # every suite: server, simulator, firmware, app
make demo            # boot cloud + run simulator + print trail & alerts
make demo MODE=low_battery   # exit_zone|low_battery|offline|drift|lost|normal

# individual ends
make test-server     # FastAPI + SQLite pytest
make test-simulator  # simulator pytest
make test-firmware   # C host tests (make -C firmware test)
make test-app        # flutter analyze + test
```

The live web demo (`GET /demo` on the running server) and the Flutter app both
visualize the same loop. CI ([.github/workflows/ci.yml](.github/workflows/ci.yml))
runs all four suites on every push/PR.

## What's deliberately not built yet

- Real hardware: MCU driver implementations behind `firmware/include/lm_drivers.h`,
  power/field testing, custom PCB (Phase 2 / 9–11 in [docs/TODOLIST.md](docs/TODOLIST.md)).
- Production concerns: real accounts (vs demo session), PostgreSQL (URL-ready),
  real push channels (vs console), OTA package verification.

See [docs/TODOLIST.md](docs/TODOLIST.md) for the full phase checklist.
