#include "lm_app.h"

#include <stdio.h>
#include <string.h>

#include "lm_protocol.h"

void lm_app_init(lm_app_t *app, const char *device_id, lm_config_t cfg, lm_drivers_t drv) {
    app->state = LM_STATE_BOOT;
    app->cfg = cfg;
    app->drv = drv;
    app->device_id = device_id;
    app->seq = 0;
    lm_cache_init(&app->cache);
}

void lm_app_event(lm_app_t *app, lm_event_t ev) {
    app->state = lm_state_next(app->state, ev);
}

void lm_app_apply_command(lm_app_t *app, const lm_command_t *cmd) {
    switch (cmd->type) {
        case LM_CMD_SET_MODE:
            if (strcmp(cmd->params_mode, "lost") == 0) {
                lm_app_event(app, LM_EV_LOST_ON);
            } else if (app->state == LM_STATE_LOST) {
                lm_app_event(app, LM_EV_LOST_OFF);
            }
            break;
        case LM_CMD_SET_INTERVAL:
            if (cmd->interval_s > 0) {
                app->cfg.tracking_interval_s = cmd->interval_s;
            }
            break;
        case LM_CMD_LOCATE_NOW:
        case LM_CMD_OTA:
        case LM_CMD_NONE:
        default:
            break;
    }
}

static const char *motion_name(lm_motion_t m) {
    switch (m) {
        case LM_MOTION_MOVING: return "moving";
        case LM_MOTION_STILL:  return "still";
        default:               return "unknown";
    }
}

/* Serialize one point and publish it. On a piggybacked command, apply it and
 * publish a command_ack. Returns true if the point was delivered. */
static bool publish_point(lm_app_t *app, const lm_cache_point_t *pt) {
    char buf[512];
    lm_location_t loc = {0};
    loc.device_id = app->device_id;
    loc.seq = pt->seq;
    loc.ts = pt->ts;
    loc.lat = pt->lat;
    loc.lng = pt->lng;
    loc.accuracy_m = pt->accuracy_m;
    loc.source = pt->source[0] ? pt->source : "gnss";
    loc.has_battery = true;
    loc.battery_pct = pt->battery_pct;
    loc.motion_state = pt->motion_state[0] ? pt->motion_state : NULL;
    if (lm_protocol_location(buf, sizeof buf, &loc) < 0) {
        return false;
    }

    lm_publish_result_t res = {0};
    if (!app->drv.modem_publish(app->drv.ctx, buf, &res)) {
        return false;
    }

    if (res.has_command) {
        lm_app_apply_command(app, &res.command);
        char ack[256];
        lm_publish_result_t ignore = {0};
        if (lm_protocol_command_ack(ack, sizeof ack, app->device_id,
                                    app->drv.clock_now(app->drv.ctx),
                                    res.command.command_id, "applied") > 0) {
            app->drv.modem_publish(app->drv.ctx, ack, &ignore);
        }
    }
    return true;
}

void lm_app_tick(lm_app_t *app) {
    /* sense motion */
    lm_motion_t motion = app->drv.imu_read_motion(app->drv.ctx);
    if (motion == LM_MOTION_MOVING) {
        lm_app_event(app, LM_EV_MOTION);
    } else if (motion == LM_MOTION_STILL) {
        lm_app_event(app, LM_EV_STILL);
    }

    /* battery */
    int batt = app->drv.battery_read(app->drv.ctx);
    if (batt < app->cfg.low_battery_threshold) {
        lm_app_event(app, LM_EV_BATTERY_LOW);
    } else if (app->state == LM_STATE_LOW_BATTERY) {
        lm_app_event(app, LM_EV_BATTERY_OK);
    }

    /* non-reporting states (boot/provisioning/ota/fault_recover) do nothing */
    if (lm_reporting_interval_s(app->state, &app->cfg) == 0) {
        return;
    }

    lm_fix_t fix;
    if (!app->drv.gnss_read(app->drv.ctx, &fix)) {
        app->drv.log_event(app->drv.ctx, "GNSS_NO_FIX", "no fix this cycle");
        return;
    }

    lm_cache_point_t pt = {0};
    pt.seq = ++app->seq;
    pt.ts = app->drv.clock_now(app->drv.ctx);
    pt.lat = fix.lat;
    pt.lng = fix.lng;
    pt.accuracy_m = fix.accuracy_m;
    pt.battery_pct = batt;
    snprintf(pt.source, sizeof pt.source, "gnss");
    snprintf(pt.motion_state, sizeof pt.motion_state, "%s", motion_name(motion));

    if (!app->drv.modem_connect(app->drv.ctx)) {
        lm_cache_push(&app->cache, &pt);
        app->drv.log_event(app->drv.ctx, "UPLOAD_FAIL", "offline, cached");
        return;
    }

    if (!publish_point(app, &pt)) {
        lm_cache_push(&app->cache, &pt);
        return;
    }

    /* reconnected: flush any cached points */
    lm_cache_point_t drained[LM_CACHE_CAP];
    size_t n = lm_cache_drain(&app->cache, drained, LM_CACHE_CAP);
    for (size_t i = 0; i < n; i++) {
        if (!publish_point(app, &drained[i])) {
            lm_cache_push(&app->cache, &drained[i]);
        }
    }
}
