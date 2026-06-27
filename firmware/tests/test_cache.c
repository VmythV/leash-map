#include "lm_cache.h"
#include "lm_test.h"

static lm_cache_point_t mk(uint32_t seq) {
    lm_cache_point_t p = {0};
    p.seq = seq;
    p.ts = 1782432000ULL + seq;
    p.lat = 31.0 + seq * 0.0001;
    p.lng = 121.0;
    p.accuracy_m = 10.0;
    p.battery_pct = 80;
    return p;
}

void test_cache_push_drain(void) {
    lm_cache_t c;
    lm_cache_init(&c);
    LM_CHECK(lm_cache_count(&c) == 0);
    for (uint32_t i = 1; i <= 5; i++) {
        LM_CHECK(lm_cache_push(&c, &(lm_cache_point_t){.seq = i}) == false);
    }
    LM_CHECK(lm_cache_count(&c) == 5);

    lm_cache_point_t out[10];
    size_t n = lm_cache_drain(&c, out, 10);
    LM_CHECK(n == 5);
    LM_CHECK(out[0].seq == 1);   /* FIFO order */
    LM_CHECK(out[4].seq == 5);
    LM_CHECK(lm_cache_count(&c) == 0);
}

void test_cache_overflow_drops_oldest(void) {
    lm_cache_t c;
    lm_cache_init(&c);
    bool dropped_any = false;
    for (uint32_t i = 1; i <= LM_CACHE_CAP + 3; i++) {
        lm_cache_point_t p = mk(i);
        dropped_any |= lm_cache_push(&c, &p);
    }
    LM_CHECK(dropped_any == true);
    LM_CHECK(lm_cache_is_full(&c));
    LM_CHECK(lm_cache_count(&c) == LM_CACHE_CAP);

    lm_cache_point_t out[LM_CACHE_CAP];
    size_t n = lm_cache_drain(&c, out, LM_CACHE_CAP);
    LM_CHECK(n == LM_CACHE_CAP);
    /* oldest 3 were dropped, so the first remaining is seq 4 */
    LM_CHECK(out[0].seq == 4);
}

void test_cache_partial_drain(void) {
    lm_cache_t c;
    lm_cache_init(&c);
    for (uint32_t i = 1; i <= 10; i++) {
        lm_cache_point_t p = mk(i);
        lm_cache_push(&c, &p);
    }
    lm_cache_point_t out[4];
    size_t n = lm_cache_drain(&c, out, 4);
    LM_CHECK(n == 4);
    LM_CHECK(out[0].seq == 1);
    LM_CHECK(lm_cache_count(&c) == 6); /* 10 - 4 */
}
