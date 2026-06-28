#include <string.h>

#include "lm_protocol.h"
#include "lm_test.h"

void test_parse_set_mode(void) {
    const char *json =
        "{\"command_id\":\"cmd_44a2f8c1\",\"type\":\"set_mode\","
        "\"params\":{\"mode\":\"lost\"},\"expires_at\":1782433000}";
    lm_command_t cmd;
    LM_CHECK(lm_protocol_parse_command(json, &cmd) == true);
    LM_CHECK_STR(cmd.command_id, "cmd_44a2f8c1");
    LM_CHECK(cmd.type == LM_CMD_SET_MODE);
    LM_CHECK_STR(cmd.params_mode, "lost");
    LM_CHECK(cmd.expires_at == 1782433000ULL);
}

void test_parse_set_interval(void) {
    const char *json =
        "{\"command_id\":\"cmd_x\",\"type\":\"set_interval\","
        "\"params\":{\"seconds\":30},\"expires_at\":1782433000}";
    lm_command_t cmd;
    LM_CHECK(lm_protocol_parse_command(json, &cmd) == true);
    LM_CHECK(cmd.type == LM_CMD_SET_INTERVAL);
    LM_CHECK(cmd.interval_s == 30);
}

void test_parse_set_config(void) {
    const char *json =
        "{\"command_id\":\"cmd_c\",\"type\":\"set_config\",\"params\":"
        "{\"led_pattern\":\"morse\",\"led_morse\":\"SOS\",\"report_interval_s\":120}}";
    lm_command_t cmd;
    LM_CHECK(lm_protocol_parse_command(json, &cmd) == true);
    LM_CHECK(cmd.type == LM_CMD_SET_CONFIG);
    LM_CHECK_STR(cmd.led_pattern, "morse");
    LM_CHECK_STR(cmd.led_morse, "SOS");
    LM_CHECK(cmd.interval_s == 120);
}

void test_parse_missing_returns_false(void) {
    lm_command_t cmd;
    LM_CHECK(lm_protocol_parse_command("{\"type\":\"set_mode\"}", &cmd) == false);
}
