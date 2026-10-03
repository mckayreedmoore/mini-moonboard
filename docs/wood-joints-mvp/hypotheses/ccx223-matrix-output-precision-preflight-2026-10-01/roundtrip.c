#include <errno.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int same_bits(double a, double b) {
    uint64_t ua;
    uint64_t ub;
    memcpy(&ua, &a, sizeof ua);
    memcpy(&ub, &b, sizeof ub);
    return ua == ub;
}

static int roundtrip(double value, const char *format, double *parsed,
                     char *token, size_t token_size) {
    int n = snprintf(token, token_size, format, value);
    char *end = NULL;
    if (n < 0 || (size_t)n >= token_size) return 0;
    errno = 0;
    *parsed = strtod(token, &end);
    return errno == 0 && end != token && *end == '\0';
}

int main(void) {
    double base = 100.0;
    double adjacent = nextafter(base, INFINITY);
    const double values[] = {
        0.0, -0.0, 0.1, -0.1,
        base, adjacent, -base, -adjacent,
        1.0e-300, -1.0e-300,
        1.234567890123456e-8, -9.876543210987654e-5,
        1.234567890123456e+6, -9.876543210987654e+11,
        0x1.fffffffffffffp-1, -0x1.123456789abcdp+20,
    };
    const size_t count = sizeof values / sizeof values[0];
    unsigned exact17 = 0;
    unsigned changed14 = 0;
    char token14[96];
    char token17[96];

    for (size_t i = 0; i < count; ++i) {
        double parsed14;
        double parsed17;
        if (!roundtrip(values[i], "%20.13e", &parsed14,
                       token14, sizeof token14)
            || !roundtrip(values[i], "%20.16e", &parsed17,
                          token17, sizeof token17)) {
            fprintf(stderr, "conversion failed at vector %zu\n", i);
            return 1;
        }
        if (same_bits(values[i], parsed17)) {
            ++exact17;
        } else {
            fprintf(stderr, "17-significant-digit mismatch at %zu: %s\n",
                    i, token17);
            return 1;
        }
        if (!same_bits(values[i], parsed14)) ++changed14;
    }

    double old_base;
    double old_adjacent;
    double new_base;
    double new_adjacent;
    if (!roundtrip(base, "%20.13e", &old_base, token14, sizeof token14)
        || !roundtrip(adjacent, "%20.13e", &old_adjacent,
                      token14, sizeof token14)
        || !roundtrip(base, "%20.16e", &new_base,
                      token17, sizeof token17)
        || !roundtrip(adjacent, "%20.16e", &new_adjacent,
                      token17, sizeof token17)) {
        fprintf(stderr, "cancellation-pair conversion failed\n");
        return 1;
    }
    if (old_base != old_adjacent || !same_bits(base, new_base)
        || !same_bits(adjacent, new_adjacent)
        || new_adjacent - new_base != adjacent - base || changed14 == 0) {
        fprintf(stderr, "precision/cancellation known-answer failed\n");
        return 1;
    }

    printf("PASS values=%zu exact_17_digit_roundtrips=%u changed_14_digit=%u\n",
           count, exact17, changed14);
    printf("adjacent_to_100_original_delta=%.17g old_14_digit_delta=%.17g "
           "new_17_digit_delta=%.17g\n",
           adjacent - base, old_adjacent - old_base,
           new_adjacent - new_base);
    return 0;
}
