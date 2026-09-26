"""Feasibility figure: cycles per block (from isa_sim.py), real-time budget, Zybo resources, verification."""
import os
import sys
from diagram_kit import Canvas, NAVY, GREY, INK, INK2, ACCENT, FILL, KEY

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figures")
ACC_TXT = "#9a3412"
BLUE = "#2a78d6"


def phase_cycles():
    sys.path.insert(0, os.path.join(HERE, "..", "simulation_py"))
    import numpy as np
    from isa_sim import Cluster, microprogram
    prog, _ = microprogram(128, 64)
    cl = Cluster(128, 64, 0.05)
    cl.stream_in(np.zeros((128, 4), dtype=np.int64))
    total = cl.run(prog, [i["phase"] for i in prog])
    return total, cl.phase_cycles


def draw(path):
    total, ph = phase_cycles()
    fclk = 100e6
    t_us = total / fclk * 1e6
    period_us = 128 / 48000 * 1e6

    c = Canvas(1800, 900)
    # ---------------- cycles per block
    c.text(30, 30, f"Cycles per block — measured by running the microprogram in the ISA simulator", fs=15,
           color=NAVY, bold=True, ha="left")
    x0, y0, W = 30, 70, 1740
    segs = [("P0", ph.get(0, 0) + 2), ("P1  filter  y = Xw", ph[1]), ("P2", ph[2]), ("P3  gradient  g = Xᵀe", ph[3]),
            ("P4", ph[4]), ("P5", ph[5])]
    x = x0
    for i, (lab, cyc) in enumerate(segs):
        w = cyc / total * W
        big = cyc > 200
        c.rect(x, y0, w, 56, fc=KEY if big else FILL, ec=NAVY, lw=1.0)
        if big:
            c.text(x + w / 2, y0 + 20, lab, fs=12.5, color=NAVY, bold=True)
            c.text(x + w / 2, y0 + 40, f"{cyc:,} cycles", fs=11, color=INK2)
        x += w
    c.text(x0 + W, y0 + 80, "P0 setup · P2 error · P4 weight update · P5 peak search: "
           f"{segs[0][1] + ph[2] + ph[4] + ph[5]} cycles together", fs=11, color=INK2, ha="right")
    c.text(x0, y0 + 80, f"Total {total:,} cycles  →  {t_us:.1f} µs at 100 MHz   (v1.0 estimate: ~7 400 cycles)",
           fs=12.5, color=INK, ha="left", bold=True)

    # ---------------- real-time budget
    c.text(30, 220, "Real-time budget per block  (B = 128 samples at 48 kHz)", fs=15, color=NAVY, bold=True,
           ha="left")
    bw = 1400
    c.rect(30, 256, bw, 44, fc="white", ec=GREY, lw=1.2)
    c.text(40, 278, f"block period  {period_us:,.0f} µs", fs=12.5, color=INK2, ha="left")
    c.rect(30, 314, bw * t_us / period_us, 44, fc=BLUE, ec=BLUE, lw=0)
    c.text(30 + bw * t_us / period_us + 12, 336, f"accelerator busy {t_us:.0f} µs  =  {t_us / period_us * 100:.1f} %"
           f" of the period  →  ~{period_us / t_us:.0f}× headroom", fs=12.5, color=INK, ha="left", bold=True)
    c.text(30, 384, "Headroom is what makes longer filters (L = 256), more microphone pairs or higher sample rates "
           "possible without new hardware.", fs=11.5, color=INK2, ha="left")

    # ---------------- resources
    c.text(30, 440, "Fits the Zybo (Zynq-7000) — counts follow from the architecture; LUT / timing come from "
           "synthesis (next step)", fs=15, color=NAVY, bold=True, ha="left")
    rows = [("", "cluster needs", "Zybo Z7-10  (XC7Z010)", "Zybo Z7-20  (XC7Z020)"),
            ("DSP48E1", "51  (3 PEs × 16 lanes + 3 scalar)", "80   → 64 %", "220  → 23 %"),
            ("BRAM18", "49  (3 × 16 banks + 1 IMEM)", "120  → 41 %", "280  → 18 %"),
            ("Clock", "100 MHz  (FCLK_CLK0)", "", ""),
            ("Peak compute", "48 MAC / cycle = 4.8 GMAC/s", "", "")]
    colx = [30, 230, 760, 1170]
    for r, row in enumerate(rows):
        yy = 478 + r * 44
        if r == 0:
            c.rect(30, yy - 4, 1540, 38, fc=FILL, ec="none", lw=0)
        for ci, cell in enumerate(row):
            c.text(colx[ci] + 10, yy + 15, cell, fs=12.5 if r else 12, color=NAVY if (r == 0 or ci == 0) else INK,
                   bold=(r == 0 or ci == 0), ha="left")
        c.ax.plot([30, 1570], [yy + 36, yy + 36], color="#e5e7eb", lw=1, zorder=2)

    # ---------------- verification
    c.text(30, 720, "Verification so far", fs=15, color=NAVY, bold=True, ha="left")
    ver = [("600 / 600", "blocks bit-exact: ISA simulator\n(78-instruction program) vs\nfixed-point model"),
           ("99.6 %", "blocks where fixed-point τ\nequals the float golden model"),
           ("85.6 %", "blocks within ±1 sample of the\ntrue delay (μ = 0.5, 126.8 s of\nmoving-source audio)")]
    for i, (big, small) in enumerate(ver):
        xx = 30 + i * 520
        c.box(xx, 752, 500, 128, "", "", kind="white", lw=1.2)
        c.text(xx + 20, 816, big, fs=23, color=NAVY, bold=True, ha="left")
        c.text(xx + 236, 816, small, fs=11.5, color=INK2, ha="left", va="center", linespacing=1.35)
    c.save(path)
    return total, ph, t_us


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print(draw(os.path.join(OUT, "feasibility.png")))
