/* LeashMap firmware — LED indicator patterns (pure logic, host-testable).
 *
 * No buzzer. The LED supports: off, solid, blink loop, and Morse code of a
 * configurable message (default "SOS", server-adjustable). lm_led_on() is a
 * pure function of elapsed time, so the device main loop just samples it. */
#ifndef LM_LED_H
#define LM_LED_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    LM_LED_OFF = 0,
    LM_LED_SOLID,
    LM_LED_BLINK,
    LM_LED_MORSE
} lm_led_pattern_t;

#define LM_LED_MSG_MAX 16

typedef struct {
    lm_led_pattern_t pattern;
    char             morse[LM_LED_MSG_MAX]; /* message for MORSE, e.g. "SOS" */
    uint16_t         unit_ms;               /* Morse time unit (dot length) */
    uint16_t         blink_on_ms;
    uint16_t         blink_off_ms;
} lm_led_t;

void lm_led_init(lm_led_t *led, lm_led_pattern_t pattern, const char *morse);

/* Whether the LED is lit at `elapsed_ms` into the (repeating) pattern. */
bool lm_led_on(const lm_led_t *led, uint32_t elapsed_ms);

const char       *lm_led_pattern_name(lm_led_pattern_t p);
lm_led_pattern_t  lm_led_pattern_from_name(const char *name);

/* Morse symbols (".-") for A-Z / 0-9; "" for space/unknown. Exposed for tests. */
const char *lm_morse_for_char(char c);

#endif /* LM_LED_H */
