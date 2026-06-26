# Device Simulator Detailed Design

> MVP supporting component: Device Simulator  
> Version: v1.0  
> Date: 2026-06-26

## 1. Objective

Build a simulator that behaves like a pet tracker before real hardware is ready. It enables cloud and App development to proceed without waiting for hardware integration.

## 2. Simulator Scope

MVP includes:

- Location upload simulation.
- Fixed route playback.
- Random walk route.
- Battery drain simulation.
- Online/offline/reconnect simulation.
- Geofence exit simulation.
- Low-accuracy location simulation.
- Offline cache and batch upload simulation.
- Lost-pet high-frequency reporting simulation.

## 3. CLI Design

Example:

```bash
leashmap-sim \
  --device-id dev_mvp_001 \
  --endpoint http://localhost:8080 \
  --token dev-token \
  --route fixtures/park-route.json \
  --interval 5s \
  --battery 85
```

Options:

| Option | Purpose |
| --- | --- |
| `--device-id` | Simulated device ID |
| `--endpoint` | Cloud API base URL |
| `--token` | Device auth token |
| `--route` | Route fixture file |
| `--interval` | Upload interval |
| `--battery` | Initial battery percentage |
| `--mode` | normal, lost, offline, drift |

## 4. Route Fixture

```json
{
  "name": "park-route",
  "points": [
    {
      "lat": 31.2304,
      "lng": 121.4737,
      "accuracy_m": 10,
      "source": "simulator"
    }
  ]
}
```

## 5. Upload Payload

```json
{
  "type": "location",
  "protocol_version": 1,
  "device_id": "dev_mvp_001",
  "seq": 1001,
  "ts": 1782432000,
  "lat": 31.2304,
  "lng": 121.4737,
  "accuracy_m": 12,
  "source": "simulator",
  "speed_mps": 1.2,
  "heading": 86,
  "battery_pct": 78,
  "motion_state": "moving"
}
```

## 6. Simulation Modes

| Mode | Behavior |
| --- | --- |
| normal | Upload route points at configured interval |
| lost | Upload route points at high frequency |
| offline | Stop upload and cache generated points |
| reconnect | Batch upload cached points |
| drift | Inject low-accuracy or shifted points |
| low_battery | Reduce battery and trigger low-battery payloads |
| exit_zone | Move from inside to outside a configured safe zone |

## 7. Test Scenarios

- Real-time map update.
- Historical trail generation.
- Geofence exit alert.
- Low-battery alert.
- Offline alert.
- Offline cache batch upload.
- Lost-pet mode high-frequency updates.
- Bad GNSS point filtering.

## 8. Simulator Deliverables

- CLI simulator.
- Route fixture format.
- Example route files.
- Example shell commands.
- Automated simulator tests.
- Local demo instructions.

