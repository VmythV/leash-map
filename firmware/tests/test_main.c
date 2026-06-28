#include <stdio.h>

#include "lm_test.h"

int lm_total = 0;
int lm_fail = 0;

/* state */
void test_state_boot_flow(void);
void test_state_motion(void);
void test_state_guard(void);
void test_state_priority_overrides(void);
void test_state_unchanged_on_irrelevant_event(void);
void test_state_names_and_modes(void);
void test_state_intervals(void);
/* protocol */
void test_protocol_location_full(void);
void test_protocol_location_omits_optional(void);
void test_protocol_heartbeat(void);
void test_protocol_event(void);
void test_protocol_truncation(void);
/* cache */
void test_cache_push_drain(void);
void test_cache_overflow_drops_oldest(void);
void test_cache_partial_drain(void);
/* command parsing */
void test_parse_set_mode(void);
void test_parse_set_interval(void);
void test_parse_missing_returns_false(void);
/* app orchestrator */
void test_app_tracking_publishes(void);
void test_app_no_fix_skips(void);
void test_app_offline_caches_then_flushes(void);
void test_app_applies_command_and_acks(void);
/* ota */
void test_ota_happy_path(void);
void test_ota_verify_fail_discards(void);
void test_ota_apply_fail_rolls_back(void);
void test_ota_abort_from_any(void);
void test_ota_progress(void);

int main(void) {
    LM_RUN(test_state_boot_flow);
    LM_RUN(test_state_motion);
    LM_RUN(test_state_guard);
    LM_RUN(test_state_priority_overrides);
    LM_RUN(test_state_unchanged_on_irrelevant_event);
    LM_RUN(test_state_names_and_modes);
    LM_RUN(test_state_intervals);

    LM_RUN(test_protocol_location_full);
    LM_RUN(test_protocol_location_omits_optional);
    LM_RUN(test_protocol_heartbeat);
    LM_RUN(test_protocol_event);
    LM_RUN(test_protocol_truncation);

    LM_RUN(test_cache_push_drain);
    LM_RUN(test_cache_overflow_drops_oldest);
    LM_RUN(test_cache_partial_drain);

    LM_RUN(test_parse_set_mode);
    LM_RUN(test_parse_set_interval);
    LM_RUN(test_parse_missing_returns_false);

    LM_RUN(test_app_tracking_publishes);
    LM_RUN(test_app_no_fix_skips);
    LM_RUN(test_app_offline_caches_then_flushes);
    LM_RUN(test_app_applies_command_and_acks);

    LM_RUN(test_ota_happy_path);
    LM_RUN(test_ota_verify_fail_discards);
    LM_RUN(test_ota_apply_fail_rolls_back);
    LM_RUN(test_ota_abort_from_any);
    LM_RUN(test_ota_progress);

    printf("\n%d checks, %d failed\n", lm_total, lm_fail);
    return lm_fail == 0 ? 0 : 1;
}
