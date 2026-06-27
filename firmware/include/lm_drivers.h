/* LeashMap firmware — hardware driver abstraction (HAL vtable).
 *
 * Business logic depends only on this interface, so the same app loop runs
 * against real drivers on an MCU and against mocks on the host. Maps to the
 * key interfaces in docs/detailed-design/firmware.md §5.
 */
#ifndef LM_DRIVERS_H
#define LM_DRIVERS_H

#include <stdbool.h>
#include <stdint.h>

#include "lm_command.h"

typedef enum {
    LM_MOTION_UNKNOWN = 0,
    LM_MOTION_STILL,
    LM_MOTION_MOVING
} lm_motion_t;

typedef struct {
    double lat;
    double lng;
    double accuracy_m;
    bool   has_speed;   double speed_mps;
    bool   has_heading; int    heading;
} lm_fix_t;

/* Result of an uplink publish: the cloud may piggyback a downlink command on
 * the response (HTTP body / MQTT). The network layer parses it into a command;
 * see lm_protocol_parse_command. */
typedef struct {
    bool         has_command;
    lm_command_t command;
} lm_publish_result_t;

typedef struct {
    /* Read a GNSS fix. Returns true if a usable fix is available. */
    bool        (*gnss_read)(void *ctx, lm_fix_t *out);
    /* Ensure the modem is attached/connected. Returns true if online. */
    bool        (*modem_connect)(void *ctx);
    /* Publish one payload. Returns true on success; may set *result. */
    bool        (*modem_publish)(void *ctx, const char *payload, lm_publish_result_t *result);
    /* Current motion state from the IMU. */
    lm_motion_t (*imu_read_motion)(void *ctx);
    /* Battery percentage 0..100. */
    int         (*battery_read)(void *ctx);
    /* Wall clock, unix epoch seconds. */
    uint64_t    (*clock_now)(void *ctx);
    /* Diagnostic log hook (error code + message). */
    void        (*log_event)(void *ctx, const char *code, const char *msg);

    void *ctx; /* driver-private context, passed back to each callback */
} lm_drivers_t;

#endif /* LM_DRIVERS_H */
