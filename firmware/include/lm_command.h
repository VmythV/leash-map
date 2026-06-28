/* LeashMap firmware — downlink command model.
 * Mirrors the command object in docs/api/device-protocol.md §8. */
#ifndef LM_COMMAND_H
#define LM_COMMAND_H

#include <stdint.h>

typedef enum {
    LM_CMD_NONE = 0,
    LM_CMD_SET_MODE,
    LM_CMD_SET_INTERVAL,
    LM_CMD_SET_CONFIG,
    LM_CMD_LOCATE_NOW,
    LM_CMD_OTA
} lm_command_type_t;

typedef struct {
    char              command_id[40];
    lm_command_type_t type;
    char              params_mode[16]; /* set_mode: idle/tracking/guard/lost/low_battery */
    uint32_t          interval_s;      /* set_interval / set_config report_interval_s */
    char              led_pattern[12]; /* set_config: off/solid/blink/morse */
    char              led_morse[16];   /* set_config: morse message */
    uint64_t          expires_at;      /* unix epoch seconds */
} lm_command_t;

#endif /* LM_COMMAND_H */
