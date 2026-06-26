# Cloud Detailed Design

> MVP area: Cloud  
> Version: v1.0  
> Date: 2026-06-26

## 1. Objective

Build the cloud backend that receives device data, stores location points, processes trails and geofences, creates alerts, and serves APIs for the user App.

## 2. Cloud Scope

MVP includes:

- Device authentication.
- Device location ingestion.
- Latest location query.
- Historical trail query.
- Pet and device binding.
- Circular geofence CRUD.
- Exit-zone, low-battery, and offline alerts.
- Realtime location and alert push.
- Basic diagnostics and logs.

MVP excludes:

- Full B2B organization model.
- Admin dashboard.
- Billing and subscription.
- Marketplace or store.
- Complex analytics and heatmaps.

## 3. Service Modules

```text
server/
  api/              App-facing APIs
  ingest/           Device upload endpoints
  devices/          Device registration, binding, status
  pets/             Pet profiles
  location/         Location validation, storage, trail query
  geofence/         Safe-zone rules and spatial checks
  alerts/           Alert generation, deduplication, acknowledgement
  realtime/         WebSocket or SSE push
  notifications/    Push provider abstraction
  migrations/       Database schema
```

## 4. Data Model

### Core Tables

```text
users
pets
devices
device_bindings
location_points
geofences
alerts
device_events
```

### `location_points`

| Field | Description |
| --- | --- |
| id | primary key |
| device_id | device identifier |
| pet_id | pet identifier after binding |
| timestamp | device-side event time |
| latitude | WGS84 latitude |
| longitude | WGS84 longitude |
| accuracy_m | accuracy radius |
| source | gnss, cell, wifi, ble, simulator |
| speed_mps | optional speed |
| heading | optional heading |
| battery_pct | battery percentage |
| motion_state | still, moving, unknown |
| raw_payload | optional original payload |

### `geofences`

| Field | Description |
| --- | --- |
| id | primary key |
| user_id | owner |
| pet_id | target pet |
| name | safe-zone name |
| center_lat | circle center latitude |
| center_lng | circle center longitude |
| radius_m | circle radius |
| enabled | active flag |

### `alerts`

| Field | Description |
| --- | --- |
| id | primary key |
| user_id | alert recipient |
| pet_id | target pet |
| device_id | source device |
| type | exit_zone, low_battery, offline |
| severity | info, warning, critical |
| status | open, acknowledged, resolved |
| location_point_id | related location |
| created_at | alert time |
| acknowledged_at | optional acknowledgement |

## 5. API Design

### Device Ingestion

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/v1/device/locations` | Upload one location point |
| POST | `/v1/device/locations/batch` | Upload offline cached points |
| POST | `/v1/device/heartbeat` | Upload heartbeat |
| POST | `/v1/device/events` | Upload device event |

### App APIs

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/v1/pets` | Create pet |
| GET | `/v1/pets` | List pets |
| POST | `/v1/devices/bind` | Bind device to pet |
| GET | `/v1/pets/{petId}/location/latest` | Get latest location |
| GET | `/v1/pets/{petId}/trail` | Query trail by time range |
| POST | `/v1/pets/{petId}/geofences` | Create safe zone |
| GET | `/v1/pets/{petId}/geofences` | List safe zones |
| GET | `/v1/alerts` | List alerts |
| POST | `/v1/alerts/{alertId}/ack` | Acknowledge alert |

## 6. Location Processing

Pipeline:

1. Authenticate device.
2. Validate payload schema.
3. Reject invalid coordinates.
4. Reject impossible timestamp drift.
5. Score point quality by source and accuracy.
6. Store location point.
7. Update latest location cache.
8. Evaluate geofences.
9. Generate alerts if needed.
10. Push realtime event to App.

## 7. Geofence Rules

MVP uses circular geofences only.

Exit-zone alert should not trigger from a single bad point. Use debounce:

- The point must be outside the safe zone.
- Accuracy must be acceptable, or alert is marked as weak confidence.
- Trigger after 2 consecutive outside points or after a configured outside duration.
- Deduplicate alerts while one exit-zone alert remains open.

## 8. Offline Detection

- Device heartbeat defines online state.
- Normal mode offline threshold: 15-30 minutes.
- Lost-pet mode offline threshold: 1-3 minutes.
- Low-battery mode may use a longer threshold.

## 9. Realtime Channel

Use WebSocket or SSE for MVP.

Events:

- `location.updated`
- `alert.created`
- `device.status_updated`
- `device.battery_updated`

## 10. Cloud Deliverables

- Database migrations.
- Device ingestion API.
- App API.
- Geofence processor.
- Alert processor.
- Realtime push service.
- API tests.
- Local demo seed script.

