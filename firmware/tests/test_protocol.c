#include <string.h>

#include "lm_protocol.h"
#include "lm_test.h"

static int contains(const char *hay, const char *needle) {
    return strstr(hay, needle) != NULL;
}

void test_protocol_location_full(void) {
    lm_location_t p = {
        .device_id = "dev_mvp_001", .seq = 1001, .ts = 1782432000ULL,
        .lat = 31.2304, .lng = 121.4737, .accuracy_m = 12.0, .source = "gnss",
        .has_speed = true, .speed_mps = 1.2,
        .has_heading = true, .heading = 86,
        .has_battery = true, .battery_pct = 78,
        .motion_state = "moving",
    };
    char buf[512];
    int w = lm_protocol_location(buf, sizeof buf, &p);
    LM_CHECK(w > 0);
    LM_CHECK(contains(buf, "\"type\":\"location\""));
    LM_CHECK(contains(buf, "\"protocol_version\":1"));
    LM_CHECK(contains(buf, "\"device_id\":\"dev_mvp_001\""));
    LM_CHECK(contains(buf, "\"seq\":1001"));
    LM_CHECK(contains(buf, "\"ts\":1782432000"));
    LM_CHECK(contains(buf, "\"lat\":31.230400"));
    LM_CHECK(contains(buf, "\"source\":\"gnss\""));
    LM_CHECK(contains(buf, "\"battery_pct\":78"));
    LM_CHECK(contains(buf, "\"motion_state\":\"moving\""));
}

void test_protocol_location_omits_optional(void) {
    lm_location_t p = {
        .device_id = "dev_mvp_001", .seq = 1, .ts = 1, .lat = 0, .lng = 0,
        .accuracy_m = 5.0, .source = "simulator",
        .has_speed = false, .has_heading = false, .has_battery = false,
        .motion_state = NULL,
    };
    char buf[256];
    LM_CHECK(lm_protocol_location(buf, sizeof buf, &p) > 0);
    LM_CHECK(!contains(buf, "speed_mps"));
    LM_CHECK(!contains(buf, "heading"));
    LM_CHECK(!contains(buf, "motion_state"));
}

void test_protocol_heartbeat(void) {
    lm_heartbeat_t h = {
        .device_id = "dev_mvp_001", .ts = 1782432060ULL, .battery_pct = 78,
        .mode = "tracking", .network_type = "cat1bis", .has_rssi = true,
        .rssi = -84, .firmware_version = "0.1.0",
    };
    char buf[256];
    LM_CHECK(lm_protocol_heartbeat(buf, sizeof buf, &h) > 0);
    LM_CHECK(contains(buf, "\"type\":\"heartbeat\""));
    LM_CHECK(contains(buf, "\"mode\":\"tracking\""));
    LM_CHECK(contains(buf, "\"network\":{\"type\":\"cat1bis\",\"rssi\":-84}"));
    LM_CHECK(contains(buf, "\"firmware_version\":\"0.1.0\""));
}

void test_protocol_event(void) {
    char buf[256];
    LM_CHECK(lm_protocol_event(buf, sizeof buf, "dev_mvp_001", 1782432000ULL,
                               "low_battery", "{\"battery_pct\":14}") > 0);
    LM_CHECK(contains(buf, "\"event\":\"low_battery\""));
    LM_CHECK(contains(buf, "\"data\":{\"battery_pct\":14}"));
}

void test_protocol_truncation(void) {
    lm_location_t p = {
        .device_id = "dev_mvp_001", .seq = 1, .ts = 1, .lat = 1, .lng = 1,
        .accuracy_m = 1, .source = "gnss",
    };
    char small[16];
    LM_CHECK(lm_protocol_location(small, sizeof small, &p) < 0); /* truncated */
}
