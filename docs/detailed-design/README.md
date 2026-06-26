# LeashMap MVP Detailed Design

> Version: v1.0  
> Date: 2026-06-26

This directory contains detailed design documents for the MVP implementation areas.

## Design Documents

| Document | Scope |
| --- | --- |
| [hardware.md](hardware.md) | Hardware development board validation, prototype architecture, power, antenna, enclosure, test plan |
| [firmware.md](firmware.md) | Firmware state machine, module boundaries, device protocol, upload strategy, OTA, logging |
| [cloud.md](cloud.md) | Cloud services, data model, APIs, location processing, geofence, alerts, realtime updates |
| [app.md](app.md) | User App navigation, screens, state model, API integration, realtime updates, MVP UX rules |
| [device-simulator.md](device-simulator.md) | Device simulator behavior, route generation, mocked device states, test scenarios |

## MVP System Loop

```text
Hardware / Device Simulator
  -> Firmware or simulator protocol
  -> Cloud ingestion and processing
  -> User App map, trail, geofence, and alert views
```

## Design Principles

- Keep MVP small enough to run end-to-end.
- Prefer simulator-first software development before real hardware is stable.
- Keep device protocol explicit and versioned.
- Show location accuracy and source clearly in the App.
- Avoid overpromising recovery or zero-error positioning.
- Keep B2B dashboard and organization management out of the MVP.

