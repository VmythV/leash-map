#include "lm_state.h"

#include <stddef.h>
#include <string.h>

lm_config_t lm_config_default(void) {
    lm_config_t c;
    c.tracking_interval_s = 120;     /* 2 min */
    c.guard_interval_s = 15;
    c.lost_interval_s = 7;
    c.heartbeat_interval_s = 1800;   /* 30 min idle heartbeat */
    c.low_battery_interval_s = 1800;
    c.low_battery_threshold = 15;
    c.led_enabled = true;
    c.led_pattern = LM_LED_BLINK;
    strncpy(c.led_morse, "SOS", sizeof c.led_morse);
    c.led_morse[sizeof c.led_morse - 1] = '\0';
    return c;
}

const char *lm_state_name(lm_state_t s) {
    switch (s) {
        case LM_STATE_BOOT:          return "boot";
        case LM_STATE_PROVISIONING:  return "provisioning";
        case LM_STATE_IDLE:          return "idle";
        case LM_STATE_TRACKING:      return "tracking";
        case LM_STATE_GUARD:         return "guard";
        case LM_STATE_LOST:          return "lost";
        case LM_STATE_LOW_BATTERY:   return "low_battery";
        case LM_STATE_OTA:           return "ota";
        case LM_STATE_FAULT_RECOVER: return "fault_recover";
    }
    return "unknown";
}

const char *lm_state_mode_name(lm_state_t s) {
    switch (s) {
        case LM_STATE_IDLE:        return "idle";
        case LM_STATE_TRACKING:    return "tracking";
        case LM_STATE_GUARD:       return "guard";
        case LM_STATE_LOST:        return "lost";
        case LM_STATE_LOW_BATTERY: return "low_battery";
        default:                   return NULL; /* not a reporting mode */
    }
}

lm_state_t lm_state_next(lm_state_t s, lm_event_t ev) {
    /* High-priority overrides regardless of current state. */
    switch (ev) {
        case LM_EV_FAULT:        return LM_STATE_FAULT_RECOVER;
        case LM_EV_OTA_START:    return LM_STATE_OTA;
        case LM_EV_BATTERY_LOW:  return LM_STATE_LOW_BATTERY;
        case LM_EV_LOST_ON:      return LM_STATE_LOST;
        default: break;
    }

    /* Per-state transitions. */
    switch (s) {
        case LM_STATE_BOOT:
            if (ev == LM_EV_BOOT_DONE) return LM_STATE_PROVISIONING;
            break;
        case LM_STATE_PROVISIONING:
            if (ev == LM_EV_PROVISIONED) return LM_STATE_IDLE;
            break;
        case LM_STATE_IDLE:
            if (ev == LM_EV_MOTION) return LM_STATE_TRACKING;
            break;
        case LM_STATE_TRACKING:
            if (ev == LM_EV_STILL) return LM_STATE_IDLE;
            if (ev == LM_EV_GEOFENCE_WARN) return LM_STATE_GUARD;
            break;
        case LM_STATE_GUARD:
            if (ev == LM_EV_GEOFENCE_CLEAR) return LM_STATE_TRACKING;
            if (ev == LM_EV_STILL) return LM_STATE_IDLE;
            break;
        case LM_STATE_LOST:
            if (ev == LM_EV_LOST_OFF) return LM_STATE_TRACKING;
            break;
        case LM_STATE_LOW_BATTERY:
            if (ev == LM_EV_BATTERY_OK) return LM_STATE_IDLE;
            break;
        case LM_STATE_OTA:
            if (ev == LM_EV_OTA_DONE) return LM_STATE_IDLE;
            break;
        case LM_STATE_FAULT_RECOVER:
            if (ev == LM_EV_FAULT_RECOVERED) return LM_STATE_IDLE;
            break;
    }
    return s; /* unchanged */
}

uint32_t lm_reporting_interval_s(lm_state_t s, const lm_config_t *cfg) {
    switch (s) {
        case LM_STATE_IDLE:        return cfg->heartbeat_interval_s;
        case LM_STATE_TRACKING:    return cfg->tracking_interval_s;
        case LM_STATE_GUARD:       return cfg->guard_interval_s;
        case LM_STATE_LOST:        return cfg->lost_interval_s;
        case LM_STATE_LOW_BATTERY: return cfg->low_battery_interval_s;
        default:                   return 0; /* no periodic reporting */
    }
}
