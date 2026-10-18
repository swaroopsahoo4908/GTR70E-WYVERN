// Minimal Arduino shim so controller.h / shared_state.h build on a desktop for SIL replay.
#pragma once
#include <cstdint>
#include <cstring>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <algorithm>
template <class T, class L, class H> static inline T constrain(T x, L lo, H hi) { return x < lo ? (T)lo : (x > hi ? (T)hi : x); }
static uint32_t __ms = 0;
static inline uint32_t millis() { return __ms; }
static inline void delay(uint32_t) {}
using std::isnan;
