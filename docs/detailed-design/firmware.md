# Firmware Detailed Design

> MVP area: Firmware  
> Version: v1.0  
> Date: 2026-06-26

## 1. Objective

Build firmware that can collect location and device state, manage power modes, upload data reliably, cache offline data, and expose enough diagnostics for field testing.

## 2. Firmware Responsibilities

- Control GNSS, modem, IMU, battery, LED, and buzzer.
- Maintain device state machine.
- Collect location points.
- Collect battery and network status.
- Apply low-power strategy.
- Upload telemetry to cloud.
- Cache data when offline.
- Process cloud configuration and commands.
- Support basic OTA-ready architecture.
- Provide serial and remote diagnostics.

## 3. Module Boundaries

```text
firmware/
  app_state/       device state machine
  drivers/         modem, GNSS, IMU, battery, LED, buzzer
  protocol/        payload serialization and parsing
  storage/         offline queue and configuration
  network/         connect, publish, retry
  power/           power-mode policy
  ota/             firmware update hooks
  diagnostics/     logs and error codes
```

## 4. Device State Machine

```text
BOOT
  -> PROVISIONING
  -> IDLE
  -> TRACKING
  -> GUARD
  -> LOST
  -> LOW_BATTERY
  -> OTA
  -> FAULT_RECOVER
```

| State | Behavior |
| --- | --- |
| BOOT | Load config, check firmware, initialize peripherals |
| PROVISIONING | Wait for binding or activation |
| IDLE | Low-power state, IMU watches motion |
| TRACKING | Periodically collect location and upload |
| GUARD | Higher attention around geofence-related behavior |
| LOST | High-frequency location and optional buzzer/LED |
| LOW_BATTERY | Reduce frequency and preserve last known location |
| OTA | Download, verify, and switch firmware |
| FAULT_RECOVER | Restart failed module and report diagnostic event |

## 5. Key Interfaces

```text
gnss_read()
modem_connect()
modem_publish()
imu_read_motion()
battery_read()
storage_enqueue()
storage_flush()
config_get()
config_set()
log_event()
```

These functions should isolate hardware-specific drivers from business logic.

## 6. Telemetry Payloads

### Location Payload

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
  "source": "gnss",
  "speed_mps": 1.2,
  "heading": 86,
  "battery_pct": 78,
  "motion_state": "moving"
}
```

### Heartbeat Payload

```json
{
  "type": "heartbeat",
  "protocol_version": 1,
  "device_id": "dev_mvp_001",
  "seq": 1002,
  "ts": 1782432060,
  "battery_pct": 78,
  "state": "tracking",
  "rssi": -84,
  "firmware_version": "0.1.0"
}
```

## 7. Upload Strategy

- MQTT over TLS is preferred when available.
- HTTPS can be used as MVP fallback.
- Every payload carries sequence number and timestamp.
- Failed payloads enter offline queue.
- Offline queue flushes after reconnect.
- Lost-pet mode bypasses long batching and uploads more frequently.

## 8. Configuration

Firmware should support cloud-delivered or locally stored configuration:

- normal tracking interval
- lost-pet interval
- heartbeat interval
- low-battery threshold
- geofence guard mode enabled
- buzzer enabled
- LED enabled
- upload endpoint

## 9. Error Codes

| Code | Meaning |
| --- | --- |
| GNSS_NO_FIX | GNSS failed to get fix |
| MODEM_ATTACH_FAIL | Cellular network attach failed |
| UPLOAD_FAIL | Payload upload failed |
| STORAGE_FULL | Offline queue is full |
| BATTERY_LOW | Battery below threshold |
| OTA_VERIFY_FAIL | Firmware package verification failed |

## 10. Firmware Tests

- State transition tests.
- Payload serialization tests.
- Offline queue tests.
- Retry policy tests.
- Low-battery mode tests.
- Motion-triggered wake tests.
- Lost-pet mode interval tests.
- Development board integration tests.

## 11. Firmware Deliverables

- Buildable firmware skeleton.
- Protocol payload definitions.
- State machine implementation.
- Development board integration notes.
- Serial log format.
- Firmware test checklist.

