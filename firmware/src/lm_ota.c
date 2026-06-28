#include "lm_ota.h"

const char *lm_ota_state_name(lm_ota_state_t s) {
    switch (s) {
        case LM_OTA_IDLE:        return "idle";
        case LM_OTA_DOWNLOADING: return "downloading";
        case LM_OTA_VERIFYING:   return "verifying";
        case LM_OTA_APPLYING:    return "applying";
        case LM_OTA_DONE:        return "done";
        case LM_OTA_ROLLBACK:    return "rollback";
    }
    return "unknown";
}

lm_ota_state_t lm_ota_next(lm_ota_state_t s, lm_ota_event_t ev) {
    if (ev == LM_OTA_EV_ABORT) {
        /* Abort from any in-progress state returns to idle. */
        return (s == LM_OTA_DONE) ? s : LM_OTA_IDLE;
    }
    switch (s) {
        case LM_OTA_IDLE:
            if (ev == LM_OTA_EV_START) return LM_OTA_DOWNLOADING;
            break;
        case LM_OTA_DOWNLOADING:
            if (ev == LM_OTA_EV_DOWNLOAD_DONE) return LM_OTA_VERIFYING;
            break;
        case LM_OTA_VERIFYING:
            if (ev == LM_OTA_EV_VERIFY_OK) return LM_OTA_APPLYING;
            if (ev == LM_OTA_EV_VERIFY_FAIL) return LM_OTA_IDLE; /* discard, keep current */
            break;
        case LM_OTA_APPLYING:
            if (ev == LM_OTA_EV_APPLY_OK) return LM_OTA_DONE;
            if (ev == LM_OTA_EV_APPLY_FAIL) return LM_OTA_ROLLBACK;
            break;
        case LM_OTA_ROLLBACK:
            if (ev == LM_OTA_EV_ROLLBACK_DONE) return LM_OTA_IDLE;
            break;
        case LM_OTA_DONE:
            break;
    }
    return s;
}

void lm_ota_reset(lm_ota_t *o) {
    o->state = LM_OTA_IDLE;
    o->total_bytes = 0;
    o->received_bytes = 0;
}

void lm_ota_begin(lm_ota_t *o, uint32_t total_bytes) {
    o->state = LM_OTA_DOWNLOADING;
    o->total_bytes = total_bytes;
    o->received_bytes = 0;
}

void lm_ota_on_chunk(lm_ota_t *o, uint32_t n) {
    o->received_bytes += n;
    if (o->total_bytes && o->received_bytes > o->total_bytes) {
        o->received_bytes = o->total_bytes;
    }
}

int lm_ota_progress_pct(const lm_ota_t *o) {
    if (o->total_bytes == 0) return 0;
    return (int)((uint64_t)o->received_bytes * 100 / o->total_bytes);
}

bool lm_ota_download_complete(const lm_ota_t *o) {
    return o->total_bytes > 0 && o->received_bytes >= o->total_bytes;
}
