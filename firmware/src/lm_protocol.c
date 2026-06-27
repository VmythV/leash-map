#include "lm_protocol.h"

#include <stdio.h>
#include <string.h>

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

int lm_protocol_command_ack(char *buf, size_t n, const char *device_id, uint64_t ts,
                            const char *command_id, const char *status) {
    char data[96];
    int w = snprintf(data, sizeof data,
                     "{\"command_id\":\"%s\",\"status\":\"%s\"}", command_id, status);
    if (w < 0 || (size_t)w >= sizeof data) return -1;
    return lm_protocol_event(buf, n, device_id, ts, "command_ack", data);
}

/* --- minimal command parser (string scanning, no JSON lib) --- */

static bool find_str(const char *json, const char *key, char *out, size_t n) {
    char pat[40];
    snprintf(pat, sizeof pat, "\"%s\":\"", key);
    const char *p = strstr(json, pat);
    if (!p) return false;
    p += strlen(pat);
    size_t i = 0;
    while (*p && *p != '"' && i + 1 < n) out[i++] = *p++;
    out[i] = '\0';
    return true;
}

static bool find_uint(const char *json, const char *key, unsigned long long *out) {
    char pat[40];
    snprintf(pat, sizeof pat, "\"%s\":", key);
    const char *p = strstr(json, pat);
    if (!p) return false;
    p += strlen(pat);
    return sscanf(p, "%llu", out) == 1;
}

bool lm_protocol_parse_command(const char *json, lm_command_t *cmd) {
    memset(cmd, 0, sizeof *cmd);
    if (!find_str(json, "command_id", cmd->command_id, sizeof cmd->command_id)) return false;

    char type[20];
    if (!find_str(json, "type", type, sizeof type)) return false;
    if (strcmp(type, "set_mode") == 0) {
        cmd->type = LM_CMD_SET_MODE;
        find_str(json, "mode", cmd->params_mode, sizeof cmd->params_mode);
    } else if (strcmp(type, "set_interval") == 0) {
        cmd->type = LM_CMD_SET_INTERVAL;
        unsigned long long s = 0;
        if (find_uint(json, "seconds", &s)) cmd->interval_s = (uint32_t)s;
    } else if (strcmp(type, "locate_now") == 0) {
        cmd->type = LM_CMD_LOCATE_NOW;
    } else if (strcmp(type, "ota") == 0) {
        cmd->type = LM_CMD_OTA;
    } else {
        cmd->type = LM_CMD_NONE;
    }

    unsigned long long e = 0;
    if (find_uint(json, "expires_at", &e)) cmd->expires_at = e;
    return true;
}
