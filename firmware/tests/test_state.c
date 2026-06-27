#include "lm_state.h"
#include "lm_test.h"

void test_state_boot_flow(void) {
    LM_CHECK(lm_state_next(LM_STATE_BOOT, LM_EV_BOOT_DONE) == LM_STATE_PROVISIONING);
    LM_CHECK(lm_state_next(LM_STATE_PROVISIONING, LM_EV_PROVISIONED) == LM_STATE_IDLE);
}

void test_state_motion(void) {
    LM_CHECK(lm_state_next(LM_STATE_IDLE, LM_EV_MOTION) == LM_STATE_TRACKING);
    LM_CHECK(lm_state_next(LM_STATE_TRACKING, LM_EV_STILL) == LM_STATE_IDLE);
}

void test_state_guard(void) {
    LM_CHECK(lm_state_next(LM_STATE_TRACKING, LM_EV_GEOFENCE_WARN) == LM_STATE_GUARD);
    LM_CHECK(lm_state_next(LM_STATE_GUARD, LM_EV_GEOFENCE_CLEAR) == LM_STATE_TRACKING);
}

void test_state_priority_overrides(void) {
    /* high-priority events apply from any state */
    LM_CHECK(lm_state_next(LM_STATE_IDLE, LM_EV_LOST_ON) == LM_STATE_LOST);
    LM_CHECK(lm_state_next(LM_STATE_TRACKING, LM_EV_BATTERY_LOW) == LM_STATE_LOW_BATTERY);
    LM_CHECK(lm_state_next(LM_STATE_GUARD, LM_EV_OTA_START) == LM_STATE_OTA);
    LM_CHECK(lm_state_next(LM_STATE_LOST, LM_EV_FAULT) == LM_STATE_FAULT_RECOVER);
    /* recovery paths */
    LM_CHECK(lm_state_next(LM_STATE_LOST, LM_EV_LOST_OFF) == LM_STATE_TRACKING);
    LM_CHECK(lm_state_next(LM_STATE_LOW_BATTERY, LM_EV_BATTERY_OK) == LM_STATE_IDLE);
    LM_CHECK(lm_state_next(LM_STATE_OTA, LM_EV_OTA_DONE) == LM_STATE_IDLE);
    LM_CHECK(lm_state_next(LM_STATE_FAULT_RECOVER, LM_EV_FAULT_RECOVERED) == LM_STATE_IDLE);
}

void test_state_unchanged_on_irrelevant_event(void) {
    LM_CHECK(lm_state_next(LM_STATE_IDLE, LM_EV_GEOFENCE_CLEAR) == LM_STATE_IDLE);
}

void test_state_names_and_modes(void) {
    LM_CHECK_STR(lm_state_name(LM_STATE_FAULT_RECOVER), "fault_recover");
    LM_CHECK_STR(lm_state_mode_name(LM_STATE_TRACKING), "tracking");
    LM_CHECK(lm_state_mode_name(LM_STATE_BOOT) == NULL); /* not a reporting mode */
}

void test_state_intervals(void) {
    lm_config_t cfg = lm_config_default();
    LM_CHECK(lm_reporting_interval_s(LM_STATE_LOST, &cfg) == cfg.lost_interval_s);
    LM_CHECK(lm_reporting_interval_s(LM_STATE_GUARD, &cfg) == cfg.guard_interval_s);
    LM_CHECK(lm_reporting_interval_s(LM_STATE_TRACKING, &cfg) == cfg.tracking_interval_s);
    LM_CHECK(lm_reporting_interval_s(LM_STATE_IDLE, &cfg) == cfg.heartbeat_interval_s);
    LM_CHECK(lm_reporting_interval_s(LM_STATE_OTA, &cfg) == 0); /* no periodic reporting */
    /* lost must report more frequently than tracking */
    LM_CHECK(cfg.lost_interval_s < cfg.tracking_interval_s);
}
