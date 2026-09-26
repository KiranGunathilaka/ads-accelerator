"""
Runs the moving-source scenario from realtime_simulation.py through
  1. the float golden model   (RealTimeCenteredNLMS)
  2. the fixed-point hardware model with 32-bit weights (design choice)
  3. the fixed-point model with naive 16-bit Q15 weights (to justify 2.)
  4. float and fixed-point (32-bit weights) with a larger step mu = 0.5 (faster tracking)
and saves per-block delay estimates plus true delays to results/feasibility.npz.

Usage:  python3 simulation_py/feasibility_run.py
"""
import os
import time
import numpy as np

from realtime_simulation import RealTimeCenteredNLMS, generate_moving_source_signals
from fixed_point_model import FixedPointBlockLMS, to_q15

B, L, MU, MU_FAST = 128, 64, 0.05, 0.5
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")


def main():
    os.makedirs(OUT, exist_ok=True)
    fs, mics, true_delays = generate_moving_source_signals("source2.wav")
    N = mics.shape[1]
    nblk = N // B
    mics_q = to_q15(mics)

    models = {
        "float": [RealTimeCenteredNLMS(L, MU) for _ in range(3)],
        "fx32": [FixedPointBlockLMS(L, B, MU, weight_bits=32) for _ in range(3)],
        "fx16": [FixedPointBlockLMS(L, B, MU, weight_bits=16) for _ in range(3)],
        "float_fast": [RealTimeCenteredNLMS(L, MU_FAST) for _ in range(3)],
        "fx32_fast": [FixedPointBlockLMS(L, B, MU_FAST, weight_bits=32) for _ in range(3)],
    }
    est = {k: np.zeros((nblk, 3), dtype=np.int32) for k in models}
    true = np.zeros((nblk, 3))
    snap_blocks = sorted({nblk // 8, nblk // 2})
    snaps = {}

    t0 = time.time()
    for b in range(nblk):
        s, e = b * B, (b + 1) * B
        mid = min(s + B // 2, N - 1)
        true[b] = true_delays[1:, mid] - true_delays[0, mid]
        for p in range(3):
            est["float"][b, p] = models["float"][p].process_block(mics[p + 1, s:e], mics[0, s:e])
            est["fx32"][b, p] = models["fx32"][p].process_block(mics_q[p + 1, s:e], mics_q[0, s:e])
            est["fx16"][b, p] = models["fx16"][p].process_block(mics_q[p + 1, s:e], mics_q[0, s:e])
            est["float_fast"][b, p] = models["float_fast"][p].process_block(mics[p + 1, s:e], mics[0, s:e])
            est["fx32_fast"][b, p] = models["fx32_fast"][p].process_block(mics_q[p + 1, s:e], mics_q[0, s:e])
        if b in snap_blocks:
            snaps[f"w_float_{b}"] = np.stack([m.w for m in models["float"]])
            snaps[f"w_fx32_{b}"] = np.stack([m.weights_float() for m in models["fx32"]])
        if b % 5000 == 0:
            print(f"block {b}/{nblk}  ({time.time() - t0:.0f}s)", flush=True)

    t_blk = (np.arange(nblk) + 1) * B / fs
    np.savez(os.path.join(OUT, "feasibility.npz"), fs=fs, B=B, L=L, mu=MU, t=t_blk, true=true,
             est_float=est["float"], est_fx32=est["fx32"], est_fx16=est["fx16"],
             est_float_fast=est["float_fast"], est_fx32_fast=est["fx32_fast"], mu_fast=MU_FAST,
             snap_blocks=np.array(snap_blocks), **snaps)
    print(f"done: {nblk} blocks x 3 filters x {len(models)} models in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
