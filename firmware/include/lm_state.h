/* LeashMap firmware — device state machine (pure logic, host-testable).
 * States and transitions follow docs/detailed-design/firmware.md §4. */
#ifndef LM_STATE_H
#define LM_STATE_H

#include <stdint.h>

#include "lm_config.h"

typedef enum {
    LM_STATE_BOOT = 0,
    LM_STATE_PROVISIONING,
    LM_STATE_IDLE,
    LM_STATE_TRACKING,
    LM_STATE_GUARD,
    LM_STATE_LOST,
    LM_STATE_LOW_BATTERY,
    LM_STATE_OTA,
    LM_STATE_FAULT_RECOVER
} lm_state_t;

typedef enum {
    LM_EV_BOOT_DONE = 0,
    LM_EV_PROVISIONED,
    LM_EV_MOTION,
    LM_EV_STILL,
    LM_EV_GEOFENCE_WARN,
    LM_EV_GEOFENCE_CLEAR,
    LM_EV_LOST_ON,
    LM_EV_LOST_OFF,
    LM_EV_BATTERY_LOW,
    LM_EV_BATTERY_OK,
    LM_EV_OTA_START,
    LM_EV_OTA_DONE,
    LM_EV_FAULT,
    LM_EV_FAULT_RECOVERED
} lm_event_t;

/* Full diagnostic name, e.g. "fault_recover". Never NULL. */
const char *lm_state_name(lm_state_t s);

/* Heartbeat `mode` value valid for the cloud contract
 * (idle/tracking/guard/lost/low_battery), or NULL for non-reporting states. */
const char *lm_state_mode_name(lm_state_t s);

/* Pure transition function. Returns the next state (unchanged if the event
 * does not apply). High-priority events (fault, OTA, low battery, lost) take
 * precedence over per-state transitions. */
lm_state_t lm_state_next(lm_state_t s, lm_event_t ev);

/* Periodic reporting interval for a state, in seconds. 0 means no periodic
 * reporting (boot/provisioning/ota/fault_recover). */
uint32_t lm_reporting_interval_s(lm_state_t s, const lm_config_t *cfg);

#endif /* LM_STATE_H */
