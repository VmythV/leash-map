#include "lm_cache.h"

void lm_cache_init(lm_cache_t *c) {
    c->head = 0;
    c->count = 0;
}

size_t lm_cache_count(const lm_cache_t *c) {
    return c->count;
}

bool lm_cache_is_full(const lm_cache_t *c) {
    return c->count == LM_CACHE_CAP;
}

bool lm_cache_push(lm_cache_t *c, const lm_cache_point_t *p) {
    bool dropped = false;
    if (c->count == LM_CACHE_CAP) {
        /* drop oldest */
        c->head = (c->head + 1) % LM_CACHE_CAP;
        c->count--;
        dropped = true;
    }
    size_t tail = (c->head + c->count) % LM_CACHE_CAP;
    c->buf[tail] = *p;
    c->count++;
    return dropped;
}

size_t lm_cache_drain(lm_cache_t *c, lm_cache_point_t *out, size_t max) {
    size_t drained = 0;
    while (c->count > 0 && drained < max) {
        out[drained++] = c->buf[c->head];
        c->head = (c->head + 1) % LM_CACHE_CAP;
        c->count--;
    }
    return drained;
}
