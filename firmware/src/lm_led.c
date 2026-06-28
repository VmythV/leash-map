#include "lm_led.h"

#include <stdio.h>
#include <string.h>

static const char *const MORSE_AZ[26] = {
    ".-", "-...", "-.-.", "-..", ".", "..-.", "--.", "....", "..", ".---",
    "-.-", ".-..", "--", "-.", "---", ".--.", "--.-", ".-.", "...", "-",
    "..-", "...-", ".--", "-..-", "-.--", "--..",
};
static const char *const MORSE_09[10] = {
    "-----", ".----", "..---", "...--", "....-",
    ".....", "-....", "--...", "---..", "----.",
};

const char *lm_morse_for_char(char c) {
    if (c >= 'a' && c <= 'z') c = (char)(c - 'a' + 'A');
    if (c >= 'A' && c <= 'Z') return MORSE_AZ[c - 'A'];
    if (c >= '0' && c <= '9') return MORSE_09[c - '0'];
    return "";
}

const char *lm_led_pattern_name(lm_led_pattern_t p) {
    switch (p) {
        case LM_LED_OFF:   return "off";
        case LM_LED_SOLID: return "solid";
        case LM_LED_BLINK: return "blink";
        case LM_LED_MORSE: return "morse";
    }
    return "off";
}

lm_led_pattern_t lm_led_pattern_from_name(const char *name) {
    if (!name) return LM_LED_OFF;
    if (strcmp(name, "solid") == 0) return LM_LED_SOLID;
    if (strcmp(name, "blink") == 0) return LM_LED_BLINK;
    if (strcmp(name, "morse") == 0) return LM_LED_MORSE;
    return LM_LED_OFF;
}

void lm_led_init(lm_led_t *led, lm_led_pattern_t pattern, const char *morse) {
    led->pattern = pattern;
    snprintf(led->morse, sizeof led->morse, "%s", (morse && *morse) ? morse : "SOS");
    led->unit_ms = 200;
    led->blink_on_ms = 500;
    led->blink_off_ms = 500;
}

/* Total Morse time (units) and the on/off state at a given unit offset.
 * Timing: dot=1, dash=3 on; intra-letter gap=1, inter-letter gap=3,
 * word gap=7 off; a trailing pause separates repeats. */
static bool morse_state_at(const lm_led_t *led, uint32_t unit_pos, uint32_t total_units) {
    uint32_t t = total_units ? (unit_pos % total_units) : 0;
    uint32_t acc = 0;
    const char *msg = led->morse;
    for (size_t i = 0; msg[i]; i++) {
        if (msg[i] == ' ') {
            acc += 7;
            if (t < acc) return false;
            continue;
        }
        const char *code = lm_morse_for_char(msg[i]);
        for (size_t j = 0; code[j]; j++) {
            uint32_t on = (code[j] == '.') ? 1u : 3u;
            acc += on;
            if (t < acc) return true;            /* LED on for the symbol */
            if (code[j + 1]) {
                acc += 1;                        /* intra-letter gap */
                if (t < acc) return false;
            }
        }
        acc += 3;                                /* inter-letter gap */
        if (t < acc) return false;
    }
    return false;                                /* trailing pause */
}

static uint32_t morse_total_units(const lm_led_t *led) {
    uint32_t acc = 0;
    const char *msg = led->morse;
    for (size_t i = 0; msg[i]; i++) {
        if (msg[i] == ' ') { acc += 7; continue; }
        const char *code = lm_morse_for_char(msg[i]);
        for (size_t j = 0; code[j]; j++) {
            acc += (code[j] == '.') ? 1u : 3u;
            if (code[j + 1]) acc += 1;
        }
        acc += 3;
    }
    return acc + 4; /* trailing pause before repeat */
}

bool lm_led_on(const lm_led_t *led, uint32_t elapsed_ms) {
    switch (led->pattern) {
        case LM_LED_OFF:
            return false;
        case LM_LED_SOLID:
            return true;
        case LM_LED_BLINK: {
            uint32_t period = (uint32_t)led->blink_on_ms + led->blink_off_ms;
            if (period == 0) return false;
            return (elapsed_ms % period) < led->blink_on_ms;
        }
        case LM_LED_MORSE: {
            uint32_t unit = led->unit_ms ? led->unit_ms : 200;
            uint32_t total = morse_total_units(led);
            if (total == 0) return false;
            uint32_t unit_pos = elapsed_ms / unit;
            return morse_state_at(led, unit_pos, total);
        }
    }
    return false;
}
