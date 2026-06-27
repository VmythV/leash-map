/* Minimal host test harness (no external deps). */
#ifndef LM_TEST_H
#define LM_TEST_H

#include <stdio.h>
#include <string.h>

extern int lm_total;
extern int lm_fail;

#define LM_CHECK(cond)                                                      \
    do {                                                                    \
        lm_total++;                                                         \
        if (!(cond)) {                                                      \
            lm_fail++;                                                       \
            printf("  FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);        \
        }                                                                   \
    } while (0)

#define LM_CHECK_STR(a, b)                                                  \
    do {                                                                    \
        lm_total++;                                                         \
        if (strcmp((a), (b)) != 0) {                                        \
            lm_fail++;                                                       \
            printf("  FAIL %s:%d: \"%s\" != \"%s\"\n", __FILE__, __LINE__,  \
                   (a), (b));                                               \
        }                                                                   \
    } while (0)

#define LM_RUN(fn)                                                          \
    do {                                                                    \
        printf("[run] %s\n", #fn);                                          \
        fn();                                                               \
    } while (0)

#endif /* LM_TEST_H */
