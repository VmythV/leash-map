#include <string.h>

#include "lm_app.h"
#include "lm_protocol.h"
#include "lm_test.h"

/* ---- mock driver ---- */
typedef struct {
    char published[32][512];
    int  published_count;
    bool connect_ok;
    bool gnss_has_fix;
    int  battery;
    lm_motion_t motion;
    bool inject_command;       /* deliver `command` on the next publish, once */
    lm_command_t command;
    uint64_t now;
} mock_t;

static bool m_gnss(void *ctx, lm_fix_t *out) {
    mock_t *m = ctx;
    if (!m->gnss_has_fix) return false;
    out->lat = 31.2304;
    out->lng = 121.4737;
    out->accuracy_m = 9.0;
    out->has_speed = false;
    out->has_heading = false;
    return true;
}
static bool m_connect(void *ctx) { return ((mock_t *)ctx)->connect_ok; }
static bool m_publish(void *ctx, const char *payload, lm_publish_result_t *res) {
    mock_t *m = ctx;
    if (m->published_count < 32) {
        snprintf(m->published[m->published_count++], 512, "%s", payload);
    }
    if (m->inject_command) {
        res->has_command = true;
        res->command = m->command;
        m->inject_command = false; /* deliver once */
    }
    return true;
}
static lm_motion_t m_motion(void *ctx) { return ((mock_t *)ctx)->motion; }
static int m_battery(void *ctx) { return ((mock_t *)ctx)->battery; }
static uint64_t m_now(void *ctx) { return ((mock_t *)ctx)->now++; }
static void m_log(void *ctx, const char *c, const char *msg) { (void)ctx; (void)c; (void)msg; }

static lm_drivers_t make_drivers(mock_t *m) {
    lm_drivers_t d = {0};
    d.gnss_read = m_gnss;
    d.modem_connect = m_connect;
    d.modem_publish = m_publish;
    d.imu_read_motion = m_motion;
    d.battery_read = m_battery;
    d.clock_now = m_now;
    d.log_event = m_log;
    d.ctx = m;
    return d;
}

static int count_substr(mock_t *m, const char *needle) {
    int c = 0;
    for (int i = 0; i < m->published_count; i++) {
        if (strstr(m->published[i], needle)) c++;
    }
    return c;
}

static lm_app_t make_app(mock_t *m) {
    lm_app_t app;
    lm_app_init(&app, "dev_mvp_001", lm_config_default(), make_drivers(m));
    lm_app_event(&app, LM_EV_BOOT_DONE);
    lm_app_event(&app, LM_EV_PROVISIONED); /* -> IDLE */
    return app;
}

void test_app_tracking_publishes(void) {
    mock_t m = {0};
    m.connect_ok = true;
    m.gnss_has_fix = true;
    m.battery = 80;
    m.motion = LM_MOTION_MOVING; /* idle -> tracking */
    m.now = 1782432000;
    lm_app_t app = make_app(&m);

    lm_app_tick(&app);
    LM_CHECK(app.state == LM_STATE_TRACKING);
    LM_CHECK(count_substr(&m, "\"type\":\"location\"") == 1);
    LM_CHECK(count_substr(&m, "\"device_id\":\"dev_mvp_001\"") == 1);
}

void test_app_no_fix_skips(void) {
    mock_t m = {0};
    m.connect_ok = true;
    m.gnss_has_fix = false;
    m.battery = 80;
    m.motion = LM_MOTION_MOVING;
    lm_app_t app = make_app(&m);

    lm_app_tick(&app);
    LM_CHECK(m.published_count == 0);
}

void test_app_offline_caches_then_flushes(void) {
    mock_t m = {0};
    m.gnss_has_fix = true;
    m.battery = 80;
    m.motion = LM_MOTION_MOVING;
    m.now = 1782432000;
    lm_app_t app = make_app(&m);

    /* offline: point is cached, nothing published */
    m.connect_ok = false;
    lm_app_tick(&app);
    LM_CHECK(m.published_count == 0);
    LM_CHECK(lm_cache_count(&app.cache) == 1);

    /* reconnect: current point + flushed cached point both published */
    m.connect_ok = true;
    lm_app_tick(&app);
    LM_CHECK(lm_cache_count(&app.cache) == 0);
    LM_CHECK(count_substr(&m, "\"type\":\"location\"") == 2);
}

void test_app_applies_command_and_acks(void) {
    mock_t m = {0};
    m.connect_ok = true;
    m.gnss_has_fix = true;
    m.battery = 80;
    m.motion = LM_MOTION_MOVING;
    m.now = 1782432000;
    m.inject_command = true;
    snprintf(m.command.command_id, sizeof m.command.command_id, "cmd_44a2f8c1");
    m.command.type = LM_CMD_SET_MODE;
    snprintf(m.command.params_mode, sizeof m.command.params_mode, "lost");

    lm_app_t app = make_app(&m);
    lm_app_tick(&app);

    LM_CHECK(app.state == LM_STATE_LOST);
    LM_CHECK(count_substr(&m, "\"event\":\"command_ack\"") == 1);
    LM_CHECK(count_substr(&m, "\"command_id\":\"cmd_44a2f8c1\"") == 1);
    LM_CHECK(count_substr(&m, "\"status\":\"applied\"") == 1);
}
