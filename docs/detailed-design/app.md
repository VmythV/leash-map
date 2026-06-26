# User App Detailed Design

> MVP area: User App  
> Version: v1.0  
> Date: 2026-06-26

## 1. Objective

Build the MVP mobile App that lets a pet owner bind a device, view real-time location, replay historical trails, configure a safe zone, and receive safety alerts.

## 2. App Scope

MVP includes:

- Demo login or lightweight account flow.
- Pet creation.
- Device binding.
- Map home screen.
- Latest location display.
- Battery, online state, location source, and accuracy display.
- Historical trail playback.
- Circular safe-zone setup.
- Alert list.
- Lost-pet mode entry.

MVP excludes:

- Community.
- Store and membership.
- Pet health reports.
- B2B organization management.
- Complex family permissions.

## 3. Navigation

```text
Launch
  -> Login / Demo Session
  -> Pet List
  -> Map Home
      -> Trail Playback
      -> Safe Zone Settings
      -> Alert List
      -> Device Detail
      -> Lost-pet Mode
```

## 4. Screens

### 4.1 Login / Demo Session

Purpose:

- Allow fast MVP testing.
- Avoid heavy account system in early demo.

MVP requirement:

- Support a local demo account or simple backend session.

### 4.2 Pet List

Displays:

- Pet name.
- Bound device status.
- Latest known location time.

Actions:

- Add pet.
- Enter map home.

### 4.3 Device Binding

Inputs:

- Device ID or QR code placeholder.
- Pet selection.

Output:

- Device is bound to pet.
- App can query latest location for that pet.

### 4.4 Map Home

Primary MVP screen.

Displays:

- Pet latest location marker.
- Location accuracy radius.
- Device online or offline state.
- Battery percentage.
- Location source.
- Last updated time.

Actions:

- Open trail playback.
- Open safe-zone settings.
- Open alert list.
- Enter lost-pet mode.

### 4.5 Trail Playback

Inputs:

- Pet ID.
- Date or time range.

Displays:

- Map route.
- Start and end points.
- Location point count.
- Distance estimate if available.
- Time range.

### 4.6 Safe Zone Settings

MVP only supports circular safe zone.

Inputs:

- Center point.
- Radius.
- Name.
- Enabled flag.

Actions:

- Create safe zone.
- Edit safe zone.
- Disable safe zone.

### 4.7 Alert List

Displays:

- Exit-zone alerts.
- Low-battery alerts.
- Offline alerts.
- Alert time.
- Pet and device.
- Status.

Actions:

- Acknowledge alert.
- Jump to related location.

### 4.8 Lost-pet Mode

MVP behavior:

- Sends command or cloud state to request higher reporting frequency.
- Shows higher power consumption warning.
- Displays last updated time prominently.

## 5. App State Model

```text
CurrentUser
Pets
SelectedPet
DeviceStatus
LatestLocation
TrailQuery
Geofences
Alerts
RealtimeConnection
```

## 6. API Dependencies

| App feature | API |
| --- | --- |
| Pet creation | `POST /v1/pets` |
| Pet list | `GET /v1/pets` |
| Device binding | `POST /v1/devices/bind` |
| Latest location | `GET /v1/pets/{petId}/location/latest` |
| Trail playback | `GET /v1/pets/{petId}/trail` |
| Safe zone | `POST /v1/pets/{petId}/geofences` |
| Alert list | `GET /v1/alerts` |
| Alert acknowledgement | `POST /v1/alerts/{alertId}/ack` |

## 7. Realtime Events

App should subscribe to:

- `location.updated`
- `alert.created`
- `device.status_updated`
- `device.battery_updated`

Realtime failure handling:

- Show reconnecting state.
- Fall back to polling latest location.
- Do not block map from showing last known location.

## 8. UX Rules

- Map home is the primary screen.
- Always show last updated time.
- Always show location source and accuracy when available.
- Do not hide uncertainty.
- Empty states must be clear:
  - no pet
  - no device
  - no location yet
  - device offline
- Lost-pet mode must warn about increased battery usage.

## 9. App Deliverables

- App shell.
- Pet creation flow.
- Device binding flow.
- Map home screen.
- Trail playback screen.
- Safe-zone screen.
- Alert list screen.
- API client.
- Realtime client.
- Simulator-backed demo flow.

