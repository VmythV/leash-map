# Hardware Detailed Design

> MVP area: Hardware  
> Version: v1.0  
> Date: 2026-06-26

## 1. Objective

Build a development-validated pet tracker hardware path that can provide location, cellular upload, battery status, motion state, and basic enclosure feasibility for field testing.

MVP hardware does not need to be production-ready. It must be good enough to validate location accuracy, power consumption, antenna behavior, and collar-worn use.

## 2. Hardware Scope

MVP includes:

- 4G Cat 1 bis connectivity.
- GNSS positioning, preferably dual-band and multi-constellation.
- Low-power IMU for motion detection.
- MCU or low-power controller.
- 500-700mAh battery path.
- Charging and battery protection.
- Battery percentage estimation.
- LTE and GNSS antenna validation.
- Simple collar attachment for field tests.

MVP excludes:

- RTK centimeter-level positioning.
- Full Mini cat version.
- Mass-production tooling.
- Full certification.
- Final waterproof industrial design.

## 3. Proposed Hardware Block

```text
Battery
  -> charger and protection
  -> fuel gauge
  -> power rails
      -> MCU
      -> Cat 1 bis modem
      -> GNSS module
      -> IMU
      -> LED / buzzer

MCU
  -> UART to Cat 1 bis modem
  -> UART or I2C to GNSS
  -> I2C or SPI to IMU
  -> I2C to fuel gauge
  -> GPIO to LED / buzzer
```

## 4. P0 Development Hardware

| Item | Purpose | Acceptance |
| --- | --- | --- |
| Cat 1 bis development board | Validate cellular attach and data upload | Can upload heartbeat and location payload to cloud |
| Dual-band GNSS evaluation board | Validate positioning quality | Can output usable location in open-sky and park routes |
| MCU development board | Run firmware state machine | Can read peripherals and trigger upload flow |
| Low-power IMU board | Detect motion and stillness | Can classify moving vs still for power strategy |
| Fuel gauge module | Estimate battery percentage | Can report stable battery percentage to firmware |
| LTE/GNSS antennas | Validate RF behavior | Can maintain network and GNSS fix in collar-like orientation |

## 5. Electrical Interfaces

| Interface | Direction | Notes |
| --- | --- | --- |
| MCU <-> Modem | UART | AT command control and data upload |
| MCU <-> GNSS | UART preferred | NMEA or vendor binary protocol |
| MCU <-> IMU | I2C preferred | Motion interrupt should wake MCU |
| MCU <-> Fuel gauge | I2C | Battery percentage and voltage |
| MCU -> LED | GPIO | Device status indication |
| MCU -> Buzzer | GPIO/PWM | Lost-pet local prompt |

## 6. Power Modes

| Mode | Hardware behavior |
| --- | --- |
| Idle | Modem and GNSS mostly off or in low-power state; IMU watches motion |
| Tracking | GNSS wakes periodically; modem uploads in batches |
| Guard | GNSS and upload frequency increases when near or outside geofence |
| Lost-pet | GNSS and modem high-frequency operation; buzzer/LED may be enabled |
| Low battery | GNSS/upload frequency reduced; last known location prioritized |

## 7. Mechanical Requirements

P0:

- Support temporary collar attachment.
- Allow antenna placement experiments.
- Allow battery replacement during tests.
- Allow wired debugging.

P1:

- Move toward compact enclosure.
- Validate magnetic charging or protected charging contacts.
- Validate basic water resistance.
- Reduce cable exposure.

## 8. Antenna Test Plan

- Test GNSS antenna in open-sky orientation.
- Test GNSS antenna with collar-worn side orientation.
- Test GNSS with pet-body-like obstruction.
- Test LTE antenna indoors, outdoors, and in weak-signal areas.
- Compare antenna placement before and after enclosure installation.
- Record time to first fix, accuracy radius, upload success rate, and signal strength.

## 9. Hardware Deliverables

- Hardware purchase list.
- Wiring diagram for P0 development board setup.
- Power measurement table.
- GNSS field test report.
- LTE upload stability report.
- P1 PCB block diagram.
- Prototype enclosure notes.

## 10. Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Antenna performance is poor in small enclosure | Bad positioning and upload failures | Run antenna tests before final enclosure decisions |
| Power consumption is too high | Poor user experience | Use motion-triggered power modes and batch upload |
| Cat 1 bis module GNSS is not accurate enough | Track quality suffers | Keep independent GNSS module option |
| Waterproofing conflicts with charging | Higher failure rate | Evaluate magnetic charging and sealed contacts early |

