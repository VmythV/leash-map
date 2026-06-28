/* Firmware <-> cloud live bridge (host build).
 *
 * Implements lm_drivers_t with a real HTTP socket driver and runs the actual
 * firmware app loop (lm_app) against a running server. Proves the C core
 * drives the real cloud end to end — not just contract alignment.
 *
 *   build:  make -C firmware bridge
 *   run:    scripts/firmware-bridge-demo.sh   (sets up the pet + safe zone)
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "http.h"
#include "lm_app.h"
#include "lm_protocol.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
#define M_PER_DEG 111320.0

typedef struct {
    const char *host;
    int port;
    const char *token;
    double lat0, lng0; /* start = safe-zone center */
    int idx, count;
    double battery;
} bridge_t;

static void offset(double lat, double lng, double north_m, double east_m,
                   double *olat, double *olng) {
    *olat = lat + north_m / M_PER_DEG;
    *olng = lng + east_m / (M_PER_DEG * cos(lat * M_PI / 180.0));
}

/* --- driver callbacks --- */
static bool b_gnss(void *ctx, lm_fix_t *out) {
    bridge_t *b = ctx;
    if (b->idx >= b->count) return false;
    double step = 18.0 * b->idx; /* spiral outward, leaves the zone partway */
    offset(b->lat0, b->lng0, step * cos(0.8), step * sin(0.8), &out->lat, &out->lng);
    out->accuracy_m = 9.0;
    out->has_speed = false;
    out->has_heading = false;
    b->idx++;
    return true;
}
static bool b_connect(void *ctx) { (void)ctx; return true; }
static bool b_publish(void *ctx, const char *payload, lm_publish_result_t *res) {
    bridge_t *b = ctx;
    char resp[4096];
    int status = lm_http_post(b->host, b->port, "/v1/device/locations", b->token,
                              payload, resp, sizeof resp);
    if (status != 200) {
        printf("  publish failed (status=%d)\n", status);
        return false;
    }
    lm_command_t cmd;
    if (lm_protocol_parse_command(resp, &cmd)) {
        res->has_command = true;
        res->command = cmd;
    }
    return true;
}
static lm_motion_t b_motion(void *ctx) { (void)ctx; return LM_MOTION_MOVING; }
static int b_battery(void *ctx) {
    bridge_t *b = ctx;
    int v = (int)(b->battery + 0.5);
    b->battery -= 0.7;
    if (b->battery < 0) b->battery = 0;
    return v;
}
static uint64_t b_clock(void *ctx) { (void)ctx; return (uint64_t)time(NULL); }
static void b_log(void *ctx, const char *code, const char *msg) {
    (void)ctx;
    printf("  [log] %s: %s\n", code, msg);
}

int main(int argc, char **argv) {
    bridge_t b = {
        .host = "127.0.0.1", .port = 8080, .token = "dev-token",
        .lat0 = 31.2304, .lng0 = 121.4737, .idx = 0, .count = 14, .battery = 80.0,
    };
    const char *device_id = (argc > 1) ? argv[1] : "dev_bridge_001";
    if (argc > 2) b.port = atoi(argv[2]);

    lm_drivers_t drv = {0};
    drv.gnss_read = b_gnss;
    drv.modem_connect = b_connect;
    drv.modem_publish = b_publish;
    drv.imu_read_motion = b_motion;
    drv.battery_read = b_battery;
    drv.clock_now = b_clock;
    drv.log_event = b_log;
    drv.ctx = &b;

    lm_app_t app;
    lm_app_init(&app, device_id, lm_config_default(), drv);
    lm_app_event(&app, LM_EV_BOOT_DONE);
    lm_app_event(&app, LM_EV_PROVISIONED);

    printf("bridge: device=%s -> %s:%d, %d points\n", device_id, b.host, b.port, b.count);
    for (int i = 0; i < b.count; i++) {
        lm_app_tick(&app);
        printf("[%2d] state=%s battery=%d%%\n", i + 1, lm_state_name(app.state), (int)(b.battery + 0.5));
        struct timespec ts = {0, 150 * 1000 * 1000}; /* 150ms */
        nanosleep(&ts, NULL);
    }
    printf("bridge: done\n");
    return 0;
}
