#include "lm_led.h"
#include "lm_test.h"

void test_led_pattern_names(void) {
    LM_CHECK_STR(lm_led_pattern_name(LM_LED_MORSE), "morse");
    LM_CHECK(lm_led_pattern_from_name("blink") == LM_LED_BLINK);
    LM_CHECK(lm_led_pattern_from_name("nope") == LM_LED_OFF);
}

void test_led_off_solid(void) {
    lm_led_t led;
    lm_led_init(&led, LM_LED_OFF, NULL);
    LM_CHECK(lm_led_on(&led, 0) == false);
    LM_CHECK(lm_led_on(&led, 9999) == false);
    lm_led_init(&led, LM_LED_SOLID, NULL);
    LM_CHECK(lm_led_on(&led, 0) == true);
    LM_CHECK(lm_led_on(&led, 9999) == true);
}

void test_led_blink(void) {
    lm_led_t led;
    lm_led_init(&led, LM_LED_BLINK, NULL); /* 500 on / 500 off */
    LM_CHECK(lm_led_on(&led, 100) == true);
    LM_CHECK(lm_led_on(&led, 700) == false);
    LM_CHECK(lm_led_on(&led, 1100) == true); /* next cycle */
}

void test_led_morse_sos(void) {
    lm_led_t led;
    lm_led_init(&led, LM_LED_MORSE, "SOS"); /* unit 200ms */
    /* first dot of 'S' is on for unit 0..200 */
    LM_CHECK(lm_led_on(&led, 50) == true);
    /* intra-letter gap 200..400 is off */
    LM_CHECK(lm_led_on(&led, 250) == false);
}

void test_morse_table(void) {
    LM_CHECK_STR(lm_morse_for_char('S'), "...");
    LM_CHECK_STR(lm_morse_for_char('o'), "---"); /* case-insensitive */
    LM_CHECK_STR(lm_morse_for_char('5'), ".....");
    LM_CHECK_STR(lm_morse_for_char(' '), "");
}
