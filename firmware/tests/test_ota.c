#include "lm_ota.h"
#include "lm_test.h"

void test_ota_happy_path(void) {
    lm_ota_state_t s = LM_OTA_IDLE;
    s = lm_ota_next(s, LM_OTA_EV_START);         LM_CHECK(s == LM_OTA_DOWNLOADING);
    s = lm_ota_next(s, LM_OTA_EV_DOWNLOAD_DONE);  LM_CHECK(s == LM_OTA_VERIFYING);
    s = lm_ota_next(s, LM_OTA_EV_VERIFY_OK);      LM_CHECK(s == LM_OTA_APPLYING);
    s = lm_ota_next(s, LM_OTA_EV_APPLY_OK);       LM_CHECK(s == LM_OTA_DONE);
}

void test_ota_verify_fail_discards(void) {
    lm_ota_state_t s = lm_ota_next(LM_OTA_VERIFYING, LM_OTA_EV_VERIFY_FAIL);
    LM_CHECK(s == LM_OTA_IDLE); /* stay on current firmware */
}

void test_ota_apply_fail_rolls_back(void) {
    lm_ota_state_t s = lm_ota_next(LM_OTA_APPLYING, LM_OTA_EV_APPLY_FAIL);
    LM_CHECK(s == LM_OTA_ROLLBACK);
    s = lm_ota_next(s, LM_OTA_EV_ROLLBACK_DONE);
    LM_CHECK(s == LM_OTA_IDLE);
}

void test_ota_abort_from_any(void) {
    LM_CHECK(lm_ota_next(LM_OTA_DOWNLOADING, LM_OTA_EV_ABORT) == LM_OTA_IDLE);
    LM_CHECK(lm_ota_next(LM_OTA_APPLYING, LM_OTA_EV_ABORT) == LM_OTA_IDLE);
    LM_CHECK(lm_ota_next(LM_OTA_DONE, LM_OTA_EV_ABORT) == LM_OTA_DONE); /* done is terminal */
}

void test_ota_progress(void) {
    lm_ota_t o;
    lm_ota_reset(&o);
    LM_CHECK(lm_ota_progress_pct(&o) == 0);
    lm_ota_begin(&o, 1000);
    lm_ota_on_chunk(&o, 250);
    LM_CHECK(lm_ota_progress_pct(&o) == 25);
    LM_CHECK(!lm_ota_download_complete(&o));
    lm_ota_on_chunk(&o, 800); /* clamps at total */
    LM_CHECK(lm_ota_progress_pct(&o) == 100);
    LM_CHECK(lm_ota_download_complete(&o));
}
