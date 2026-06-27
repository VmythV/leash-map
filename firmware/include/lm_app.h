/* LeashMap firmware — application orchestrator (pure logic over the HAL).
 *
 * Ties the state machine, drivers, offline cache and protocol together into a
 * single host-testable tick: sense -> decide -> collect -> publish or cache ->
 * flush on reconnect -> apply downlink command + ack. */
#ifndef LM_APP_H
#define LM_APP_H

#include <stdint.h>

#include "lm_cache.h"
#include "lm_command.h"
#include "lm_drivers.h"
#include "lm_state.h"

typedef struct {
    lm_state_t   state;
    lm_config_t  cfg;
    lm_drivers_t drv;
    lm_cache_t   cache;
    const char  *device_id;
    uint32_t     seq;
} lm_app_t;

void lm_app_init(lm_app_t *app, const char *device_id, lm_config_t cfg, lm_drivers_t drv);

/* Feed an event to the state machine. */
void lm_app_event(lm_app_t *app, lm_event_t ev);

/* Run one orchestration cycle. */
void lm_app_tick(lm_app_t *app);

/* Apply a downlink command (also reachable via the publish result path). */
void lm_app_apply_command(lm_app_t *app, const lm_command_t *cmd);

#endif /* LM_APP_H */
