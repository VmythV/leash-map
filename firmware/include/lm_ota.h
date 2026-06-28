/* LeashMap firmware — OTA update state machine (pure logic).
 *
 * Models the download -> verify -> apply -> done/rollback flow from
 * docs/detailed-design/firmware.md. Verification failure discards the package
 * (stay on current firmware); apply failure triggers rollback. */
#ifndef LM_OTA_H
#define LM_OTA_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    LM_OTA_IDLE = 0,
    LM_OTA_DOWNLOADING,
    LM_OTA_VERIFYING,
    LM_OTA_APPLYING,
    LM_OTA_DONE,
    LM_OTA_ROLLBACK
} lm_ota_state_t;

typedef enum {
    LM_OTA_EV_START = 0,
    LM_OTA_EV_DOWNLOAD_DONE,
    LM_OTA_EV_VERIFY_OK,
    LM_OTA_EV_VERIFY_FAIL,
    LM_OTA_EV_APPLY_OK,
    LM_OTA_EV_APPLY_FAIL,
    LM_OTA_EV_ROLLBACK_DONE,
    LM_OTA_EV_ABORT
} lm_ota_event_t;

const char *lm_ota_state_name(lm_ota_state_t s);

/* Pure transition. Unknown events leave the state unchanged. */
lm_ota_state_t lm_ota_next(lm_ota_state_t s, lm_ota_event_t ev);

/* Download progress context. */
typedef struct {
    lm_ota_state_t state;
    uint32_t total_bytes;
    uint32_t received_bytes;
} lm_ota_t;

void lm_ota_reset(lm_ota_t *o);
void lm_ota_begin(lm_ota_t *o, uint32_t total_bytes);
void lm_ota_on_chunk(lm_ota_t *o, uint32_t n);
int  lm_ota_progress_pct(const lm_ota_t *o);
bool lm_ota_download_complete(const lm_ota_t *o);

#endif /* LM_OTA_H */
