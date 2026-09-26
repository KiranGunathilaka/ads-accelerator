"""
Bit-accurate fixed-point model of one SIMD PE running centered Block-LMS.

This mirrors RealTimeCenteredNLMS.process_block() (the float golden model in
realtime_simulation.py) but uses the number formats and memory layout of the
hardware described in ISA_Design.md v1.1:

  x, d, y, e : Q1.15  (16-bit, what the audio codec delivers)
  w          : Q2.30  (32-bit, stored REVERSED in the scratchpad: w_rev[k] = w[L-1-k])
  multiplier : 25 x 18 (DSP48E1) -> w is truncated to Q2.23 before multiplying
  accumulator: 48-bit (DSP48E1 P register)

Storing w reversed makes every X access an ascending, unit-stride read:
  row i of X    (Phase 1) = x_full[i+1 .. i+L]
  column k of X (Phase 3) = x_full[k+1 .. k+B]   (gives g_rev[k] = g[L-1-k])
"""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

Q15_MAX, Q15_MIN = (1 << 15) - 1, -(1 << 15)
I32_MAX, I32_MIN = (1 << 31) - 1, -(1 << 31)


def to_q15(x):
    return np.clip(np.round(np.asarray(x, dtype=np.float64) * 32768.0), Q15_MIN, Q15_MAX).astype(np.int64)


def sat(v, lo, hi):
    return np.clip(v, lo, hi)


class FixedPointBlockLMS:
    def __init__(self, L, B, mu, weight_bits=32):
        assert B & (B - 1) == 0, "B must be a power of two (division by B is a shift)"
        assert L % 16 == 0 and B % 16 == 0, "L and B must be multiples of VLEN=16"
        self.L, self.B, self.ct = L, B, L // 2
        self.log2B = B.bit_length() - 1
        self.mu_q15 = int(round(mu * 32768))
        self.weight_bits = weight_bits           # 32 = design choice; 16 = naive Q15 weights (for comparison)
        self.w_rev = np.zeros(L, dtype=np.int64)  # Q2.30 (or Q1.15 if weight_bits == 16)
        self.x_hist = np.zeros(L, dtype=np.int64)
        self.d_hist = np.zeros(self.ct, dtype=np.int64)

    def process_block(self, x_block_q15, d_block_q15):
        L, B = self.L, self.B
        x_full = np.concatenate((self.x_hist, x_block_q15))
        d_full = np.concatenate((self.d_hist, d_block_q15))
        d_del = d_full[:B]

        if self.weight_bits == 32:
            w_mul = self.w_rev >> 7               # Q2.30 -> Q2.23 (25-bit A port)
            y_shift = 23
        else:
            w_mul = self.w_rev                    # Q1.15
            y_shift = 15

        # Phase 1: y[i] = sum_k x_full[i+1+k] * w_rev[k]
        rows = sliding_window_view(x_full[1:], L)[:B]
        acc1 = rows @ w_mul
        y = sat((acc1 + (1 << (y_shift - 1))) >> y_shift, Q15_MIN, Q15_MAX)

        # Phase 2: e = d_delayed - y
        e = sat(d_del - y, Q15_MIN, Q15_MAX)

        # Phase 3: g_rev[k] = sum_i x_full[k+1+i] * e[i]; VREDUCE shift by log2(B) gives mean gradient in Q2.30
        cols = sliding_window_view(x_full[1:], B)[:L]
        g_mean = (cols @ e) >> self.log2B

        # Phase 4: w_rev += mu * g_mean
        if self.weight_bits == 32:
            dw = ((g_mean >> 7) * self.mu_q15) >> 8     # Q2.23 x Q1.15 = 38 frac bits -> Q2.30
            self.w_rev = sat(self.w_rev + dw, I32_MIN, I32_MAX)
        else:
            dw = ((g_mean >> 15) * self.mu_q15) >> 15   # everything in Q1.15
            self.w_rev = sat(self.w_rev + dw, Q15_MIN, Q15_MAX)

        self.x_hist = x_full[-L:]
        self.d_hist = d_full[-self.ct:]

        # Phase 5: peak on reversed weights; tau = k* - (L-1-center_tap)
        k_star = int(np.argmax(np.abs(self.w_rev)))
        return k_star - (L - 1 - self.ct)

    def weights_float(self):
        scale = 2.0 ** 30 if self.weight_bits == 32 else 2.0 ** 15
        return self.w_rev[::-1] / scale
