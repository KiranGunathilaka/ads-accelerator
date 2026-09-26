"""
Tracking study: how fast does the centered Block-LMS follow the moving source?

Compares the current update  w += (mu/B) * X^T e            (step depends on signal level)
with block-NLMS              w += (mu/B) * X^T e / (L*Px + eps)   (Px = mean input power this block)
and reports accuracy plus the time lag that best aligns the estimate with the true TDOA.

NLMS is stable for 0 < mu < 2 (with the L*Px normalisation), so mu is not comparable between the two rows.

Usage:  python3 simulation_py/tracking_study.py
"""
import contextlib
import io
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view as swv

from realtime_simulation import generate_moving_source_signals

B, L = 128, 64
CT = L // 2


def run(mics, mu, nlms):
    nb = mics.shape[1] // B
    w = np.zeros((3, L))
    xh = np.zeros((3, L))
    dh = np.zeros(CT)
    est = np.zeros((nb, 3))
    for b in range(nb):
        s = b * B
        d_full = np.concatenate((dh, mics[0, s:s + B]))
        d_del = d_full[:B]
        for p in range(3):
            x_full = np.concatenate((xh[p], mics[p + 1, s:s + B]))
            X = swv(x_full[1:], L)[:B][:, ::-1]            # identical to x_full[i+L:i:-1]
            e = d_del - X @ w[p]
            g = X.T @ e
            step = mu / B
            if nlms:
                step /= L * np.mean(x_full[1:] ** 2) + 1e-6
            w[p] += step * g
            xh[p] = x_full[-L:]
            est[b, p] = CT - np.argmax(np.abs(w[p]))
        dh = d_full[-CT:]
    return est


def main():
    with contextlib.redirect_stdout(io.StringIO()):
        fs, mics, td = generate_moving_source_signals("source2.wav")
    nb = mics.shape[1] // B
    mid = np.minimum(np.arange(nb) * B + B // 2, mics.shape[1] - 1)
    true = (td[1:, mid] - td[0, mid]).T
    skip = int(0.5 * fs / B)
    print(f"{'update':8s} {'mu':>5s}  {'MAE':>5s}  {'within+-1':>9s}  {'lag':>7s}")
    for nlms, mu in [(False, 0.05), (False, 0.2), (False, 0.5), (True, 0.3), (True, 0.64), (True, 1.0)]:
        est = run(mics, mu, nlms)
        err = est[skip:] - true[skip:]
        lags = range(0, 1500, 25)
        lag = min(lags, key=lambda k: np.abs(est[k:] - true[:nb - k]).mean())
        within = np.mean(np.abs(est[skip:] - np.round(true[skip:])) <= 1) * 100
        print(f"{'NLMS' if nlms else 'mu/B':8s} {mu:5.2f}  {np.abs(err).mean():5.2f}  {within:8.1f}%  {lag * B / fs:5.2f} s",
              flush=True)


if __name__ == "__main__":
    main()
