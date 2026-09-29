"""
Slide/explainer figures for the simulation results.
Reads simulation_py/results/feasibility.npz (run simulation_py/feasibility_run.py first).

Usage:  python3 presentation/plot_results.py
"""
import os
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "simulation_py", "results", "feasibility.npz")
FIG = os.path.join(HERE, "figures")

INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0"
BLUE, ORANGE = "#2a78d6", "#eb6834"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 13, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "figure.facecolor": "white",
    "axes.facecolor": "white", "savefig.facecolor": "white",
})


def tracking(r):
    t, true, est = r["t"], r["true"], r["est_fx32_fast"]
    names = ["τ21  (Mic2 vs Mic1)", "τ31  (Mic3 vs Mic1)", "τ41  (Mic4 vs Mic1)"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.3), sharey=True)
    step = 4
    for p, ax in enumerate(axes):
        for a0, a1, txt in [(66, 90, "bass-only\naudio"), (120, t[-1], "fade\nout")]:
            ax.axvspan(a0, a1, color="#f1f0ec", zorder=0, lw=0)
            ax.text((a0 + a1) / 2, -16.8, txt, ha="center", va="bottom", fontsize=10.5, color=INK2)
        ax.plot(t[::step], est[::step, p], color=BLUE, lw=1.0, alpha=0.9, drawstyle="steps-post",
                label="accelerator estimate (fixed-point)")
        ax.plot(t, true[:, p], color=INK, lw=2.2, label="true TDOA")
        ax.set_title(names[p], loc="left", fontsize=14, color=INK, fontweight="bold")
        ax.set_xlabel("time (s)")
        ax.set_xlim(0, t[-1])
        ax.set_ylim(-18, 18)
    axes[0].set_ylabel("delay (samples @ 48 kHz)")
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h[::-1], lab[::-1], loc="upper right", ncol=2, frameon=False, fontsize=12.5,
               bbox_to_anchor=(0.995, 1.02))
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(os.path.join(FIG, "sim_tracking.png"), dpi=160)
    plt.close(fig)


def accuracy(r):
    true = r["true"]
    skip = int(0.5 * 48000 / 128)
    rows = [
        ("float, μ = 0.05 (current)", r["est_float"]),
        ("fixed-point, 16-bit weights", r["est_fx16"]),
        ("fixed-point, μ = 0.05", r["est_fx32"]),
        ("float, μ = 0.5", r["est_float_fast"]),
        ("fixed-point, μ = 0.5", r["est_fx32_fast"]),
    ]
    vals = [np.mean(np.abs(e[skip:] - np.round(true[skip:])) <= 1) * 100 for _, e in rows]
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    y = np.arange(len(rows))[::-1]
    colors = [MUTED, MUTED, BLUE, MUTED, BLUE]
    ax.barh(y, vals, color=colors, height=0.62)
    for yi, v in zip(y, vals):
        ax.text(v + 1.2, yi, f"{v:.1f}%", va="center", color=INK, fontsize=13)
    ax.set_yticks(y, [n for n, _ in rows])
    ax.set_xlim(0, 100)
    ax.set_xlabel("blocks with |error| ≤ 1 sample  (%)")
    ax.grid(axis="y", visible=False)
    ax.set_axisbelow(True)
    ax.set_title("Delay accuracy over 126.8 s (3 pairs)", loc="left", fontsize=14, color=INK, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "sim_accuracy.png"), dpi=160)
    plt.close(fig)
    return dict(zip([n for n, _ in rows], vals))


def weights(r):
    b = int(r["snap_blocks"][-1])
    wf, wq = r[f"w_float_{b}"], r[f"w_fx32_{b}"]
    L = wf.shape[1]
    ct = L // 2
    fig, ax = plt.subplots(figsize=(8, 4))
    j = np.arange(L)
    ax.axvline(ct, color=MUTED, lw=1.2, ls="--")
    ax.text(ct + 0.6, ax.get_ylim()[1] if False else 0, "", color=INK2)
    ax.plot(j, wf[0], color=INK, lw=2.2, label="float")
    ax.plot(j, wq[0], color=BLUE, lw=1.4, ls=(0, (4, 2)), label="fixed-point")
    k = int(np.argmax(np.abs(wf[0])))
    ax.annotate(f"peak at tap {k} → τ21 = {ct} − {k} = {ct - k}", xy=(k, wf[0][k]), xytext=(k + 6, wf[0][k] * 0.85),
                arrowprops=dict(arrowstyle="->", color=INK2), color=INK, fontsize=12.5)
    ax.text(ct + 0.6, ax.get_ylim()[0] * 0.9 + 0.001, "center tap (zero delay)", color=INK2, fontsize=11)
    ax.set_xlabel("filter tap j")
    ax.set_ylabel("w[j]")
    ax.set_title(f"Mic2 filter weights at t = {r['t'][b]:.1f} s", loc="left", fontsize=14, color=INK, fontweight="bold")
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "sim_weights.png"), dpi=160)
    plt.close(fig)


def slide(r):
    """One figure for the simulation-results slide: tracking (top), accuracy + weights (bottom)."""
    t, true, est = r["t"], r["true"], r["est_fx32_fast"]
    fig = plt.figure(figsize=(18, 8.6))
    gs = fig.add_gridspec(2, 6, height_ratios=[1, 1.02], hspace=0.42, wspace=0.9)
    names = ["τ21  (Mic2 vs Mic1)", "τ31  (Mic3 vs Mic1)", "τ41  (Mic4 vs Mic1)"]
    for p in range(3):
        ax = fig.add_subplot(gs[0, 2 * p:2 * p + 2])
        for a0, a1, txt in [(66, 90, "bass-only"), (120, t[-1], "fade")]:
            ax.axvspan(a0, a1, color="#f1f0ec", zorder=0, lw=0)
            ax.text((a0 + a1) / 2, -16.8, txt, ha="center", va="bottom", fontsize=10.5, color=INK2)
        ax.plot(t[::4], est[::4, p], color=BLUE, lw=1.0, drawstyle="steps-post", label="accelerator (fixed-point)")
        ax.plot(t, true[:, p], color=INK, lw=2.2, label="true TDOA")
        ax.set_title(names[p], loc="left", fontsize=14, color=INK, fontweight="bold")
        ax.set_xlim(0, t[-1]); ax.set_ylim(-18, 18); ax.set_xlabel("time (s)")
        if p == 0:
            ax.set_ylabel("delay (samples)")
            h, lab = ax.get_legend_handles_labels()
    fig.legend(h[::-1], lab[::-1], loc="upper right", ncol=2, frameon=False, fontsize=13, bbox_to_anchor=(0.99, 1.0))
    fig.text(0.01, 0.985, "Sound source moving around the 4 microphones · 127 s of music", fontsize=13,
             color=INK2, va="top")

    ax = fig.add_subplot(gs[1, 0:3])
    skip = int(0.5 * 48000 / 128)
    rows = [("floating-point,  μ = 0.5", r["est_float_fast"], MUTED),
            ("fixed-point,  μ = 0.5", r["est_fx32_fast"], BLUE),
            ("fixed-point,  μ = 0.05", r["est_fx32"], BLUE)]
    vals = [np.mean(np.abs(e[skip:] - np.round(true[skip:])) <= 1) * 100 for _, e, _ in rows]
    y = np.arange(len(rows))[::-1]
    ax.barh(y, vals, color=[c for *_, c in rows], height=0.55)
    ax.set_axisbelow(True)
    for yi, v in zip(y, vals):
        ax.text(v + 1.2, yi, f"{v:.1f}%", va="center", color=INK, fontsize=13)
    ax.set_yticks(y, [n for n, *_ in rows], fontsize=13); ax.set_xlim(0, 100); ax.grid(axis="y", visible=False)
    ax.set_xlabel("blocks within ±1 sample of the true delay (%)")
    ax.set_title("Fixed-point = floating-point;  larger μ tracks faster", loc="left", fontsize=14, color=INK,
                 fontweight="bold")

    ax = fig.add_subplot(gs[1, 3:6])
    b = int(r["snap_blocks"][-1]); wf, wq = r[f"w_float_{b}"], r[f"w_fx32_{b}"]
    L = wf.shape[1]; ct = L // 2; j = np.arange(L)
    ax.axvline(ct, color=MUTED, lw=1.2, ls="--")
    ax.plot(j, wf[0], color=INK, lw=2.2, label="float")
    ax.plot(j, wq[0], color=BLUE, lw=1.5, ls=(0, (4, 2)), label="fixed-point")
    k = int(np.argmax(np.abs(wf[0])))
    ax.annotate(f"peak at tap {k}  →  τ21 = {ct} − {k} = {ct - k}", xy=(k, wf[0][k]),
                xytext=(k + 7, wf[0][k] * 0.8), arrowprops=dict(arrowstyle="->", color=INK2), color=INK, fontsize=12.5)
    ax.text(ct + 0.8, -0.012, "zero delay", color=INK2, fontsize=11)
    ax.set_xlabel("filter tap j"); ax.set_ylabel("w[j]"); ax.legend(frameon=False, loc="center right")
    ax.set_title(f"Mic2 weights at t = {r['t'][b]:.0f} s: the peak is the delay", loc="left", fontsize=14, color=INK,
                 fontweight="bold")
    fig.subplots_adjust(left=0.135, right=0.99, top=0.9, bottom=0.08)
    fig.savefig(os.path.join(FIG, "slide_simulation.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(FIG, exist_ok=True)
    r = np.load(RES)
    tracking(r)
    print(accuracy(r))
    weights(r)
    slide(r)
    print("figures written to", FIG)
