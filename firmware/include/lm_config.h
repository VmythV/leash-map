/* LeashMap firmware — device configuration (intervals, thresholds).
 * Defaults follow the power strategy in docs/technical-plan.md §4.5. */
#ifndef LM_CONFIG_H
#define LM_CONFIG_H

#include <stdbool.h>
#include <stdint.h>

#include "lm_led.h"

typedef struct {
    uint32_t tracking_interval_s;     /* normal activity */
    uint32_t guard_interval_s;        /* near/at geofence boundary */
    uint32_t lost_interval_s;         /* lost-pet high frequency */
    uint32_t heartbeat_interval_s;    /* idle low-power heartbeat */
    uint32_t low_battery_interval_s;  /* reduced frequency when low */
    uint8_t  low_battery_threshold;   /* percent */
    /* No buzzer. LED only. */
    bool             led_enabled;
    lm_led_pattern_t led_pattern;
    char             led_morse[LM_LED_MSG_MAX]; /* default "SOS" */
} lm_config_t;

/* Sensible MVP defaults. */
lm_config_t lm_config_default(void);

#endif /* LM_CONFIG_H */
