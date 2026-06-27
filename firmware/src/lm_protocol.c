#include "lm_protocol.h"

#include <stdio.h>

/* Helper: advance an snprintf-style cursor; track truncation. */
#define LM_APPEND(...)                                              \
    do {                                                           \
        int _w = snprintf(buf + off, (off < n) ? (n - off) : 0,    \
                          __VA_ARGS__);                            \
        if (_w < 0) return -1;                                     \
        off += (size_t)_w;                                         \
    } while (0)

static int lm_finish(size_t off, size_t n) {
    if (off >= n) return -1; /* truncated */
    return (int)off;
}

int lm_protocol_location(char *buf, size_t n, const lm_location_t *p) {
    size_t off = 0;
    LM_APPEND("{\"type\":\"location\",\"protocol_version\":%d", LM_PROTOCOL_VERSION);
    LM_APPEND(",\"device_id\":\"%s\"", p->device_id);
    LM_APPEND(",\"seq\":%u", p->seq);
    LM_APPEND(",\"ts\":%llu", (unsigned long long)p->ts);
    LM_APPEND(",\"lat\":%.6f,\"lng\":%.6f", p->lat, p->lng);
    LM_APPEND(",\"accuracy_m\":%.1f", p->accuracy_m);
    LM_APPEND(",\"source\":\"%s\"", p->source);
    if (p->has_speed)   LM_APPEND(",\"speed_mps\":%.1f", p->speed_mps);
    if (p->has_heading) LM_APPEND(",\"heading\":%d", p->heading);
    if (p->has_battery) LM_APPEND(",\"battery_pct\":%d", p->battery_pct);
    if (p->motion_state) LM_APPEND(",\"motion_state\":\"%s\"", p->motion_state);
    LM_APPEND("}");
    return lm_finish(off, n);
}

int lm_protocol_heartbeat(char *buf, size_t n, const lm_heartbeat_t *p) {
    size_t off = 0;
    LM_APPEND("{\"type\":\"heartbeat\",\"protocol_version\":%d", LM_PROTOCOL_VERSION);
    LM_APPEND(",\"device_id\":\"%s\"", p->device_id);
    LM_APPEND(",\"ts\":%llu", (unsigned long long)p->ts);
    LM_APPEND(",\"battery_pct\":%d", p->battery_pct);
    LM_APPEND(",\"mode\":\"%s\"", p->mode);
    if (p->network_type) {
        LM_APPEND(",\"network\":{\"type\":\"%s\"", p->network_type);
        if (p->has_rssi) LM_APPEND(",\"rssi\":%d", p->rssi);
        LM_APPEND("}");
    }
    if (p->firmware_version) LM_APPEND(",\"firmware_version\":\"%s\"", p->firmware_version);
    LM_APPEND("}");
    return lm_finish(off, n);
}

int lm_protocol_event(char *buf, size_t n, const char *device_id, uint64_t ts,
                      const char *event, const char *data_json) {
    size_t off = 0;
    LM_APPEND("{\"type\":\"event\",\"protocol_version\":%d", LM_PROTOCOL_VERSION);
    LM_APPEND(",\"device_id\":\"%s\"", device_id);
    LM_APPEND(",\"ts\":%llu", (unsigned long long)ts);
    LM_APPEND(",\"event\":\"%s\"", event);
    if (data_json) LM_APPEND(",\"data\":%s", data_json);
    LM_APPEND("}");
    return lm_finish(off, n);
}
