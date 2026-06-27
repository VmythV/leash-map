/* LeashMap firmware — bounded offline cache (ring buffer).
 * Holds location points while offline; drains in batches after reconnect.
 * Fixed-capacity, no heap — suitable for MCU use. */
#ifndef LM_CACHE_H
#define LM_CACHE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define LM_CACHE_CAP 64

typedef struct {
    uint32_t seq;
    uint64_t ts;
    double   lat;
    double   lng;
    double   accuracy_m;
    int      battery_pct;
    char     source[12];
    char     motion_state[12];
} lm_cache_point_t;

typedef struct {
    lm_cache_point_t buf[LM_CACHE_CAP];
    size_t head;   /* index of oldest */
    size_t count;  /* number stored */
} lm_cache_t;

void   lm_cache_init(lm_cache_t *c);
size_t lm_cache_count(const lm_cache_t *c);
bool   lm_cache_is_full(const lm_cache_t *c);

/* Enqueue a point. When full, drops the oldest to make room and returns true
 * (signals a STORAGE_FULL condition the caller may log). */
bool   lm_cache_push(lm_cache_t *c, const lm_cache_point_t *p);

/* Copy up to `max` oldest points into `out` and remove them. Returns the
 * number drained. */
size_t lm_cache_drain(lm_cache_t *c, lm_cache_point_t *out, size_t max);

#endif /* LM_CACHE_H */
