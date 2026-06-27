/* LeashMap firmware — uplink payload serialization (JSON).
 * Field names/shapes match docs/api/device-protocol.md (the contract source
 * of truth). MVP uses snprintf into a caller buffer; an embedded build can
 * swap in a no_std JSON writer without changing call sites. */
#ifndef LM_PROTOCOL_H
#define LM_PROTOCOL_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define LM_PROTOCOL_VERSION 1

typedef struct {
    const char *device_id;
    uint32_t    seq;
    uint64_t    ts;          /* unix epoch seconds */
    double      lat;
    double      lng;
    double      accuracy_m;
    const char *source;      /* "gnss" | "cell" | "wifi" | "ble" | "simulator" */
    bool        has_speed;   double speed_mps;
    bool        has_heading; int    heading;
    bool        has_battery; int    battery_pct;
    const char *motion_state; /* "still"|"moving"|"unknown" or NULL */
} lm_location_t;

typedef struct {
    const char *device_id;
    uint64_t    ts;
    int         battery_pct;
    const char *mode;          /* idle|tracking|guard|lost|low_battery */
    const char *network_type;  /* e.g. "cat1bis" or NULL */
    bool        has_rssi; int  rssi;
    const char *firmware_version; /* or NULL */
} lm_heartbeat_t;

/* Each writer returns the number of bytes written (excluding NUL), or a
 * negative value if the output was truncated. */
int lm_protocol_location(char *buf, size_t n, const lm_location_t *p);
int lm_protocol_heartbeat(char *buf, size_t n, const lm_heartbeat_t *p);
int lm_protocol_event(char *buf, size_t n, const char *device_id, uint64_t ts,
                      const char *event, const char *data_json /* or NULL */);

#endif /* LM_PROTOCOL_H */
