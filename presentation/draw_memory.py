"""Memory & addressing figure: sliding window + reversed w, circular input ring, bank alignment, memory map."""
import os
import numpy as np
from matplotlib.patches import Wedge
from diagram_kit import Canvas, NAVY, GREY, INK, INK2, ACCENT, FILL, KEY

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
ACC_TXT = "#9a3412"
PALE_ACC = "#fdeee7"


def draw(path):
    c = Canvas(1800, 900)

    # ================= (A) one window serves rows and columns
    c.text(30, 30, "① One sliding window serves both X·w and Xᵀ·e", fs=15, color=NAVY, bold=True, ha="left")
    n, x0, y0, cw = 48, 30, 96, 22          # draw 48 representative samples of x_full
    for j in range(n):
        c.rect(x0 + j * cw, y0, cw - 2, 30, fc="white", ec=GREY, lw=0.8)
    c.text(x0 - 2, y0 - 14, "x_full  =  [ history (L) | new block (B) ]   (192 samples)", fs=11, color=INK2,
           ha="left")
    # row i window
    def span(a, b, y, fc, ec, label, lab_color):
        c.rect(x0 + a * cw - 1, y, (b - a) * cw, 12, fc=fc, ec=ec, lw=1.2)
        c.text(x0 + (a + b) / 2 * cw, y + 24, label, fs=10.5, color=lab_color)
    span(3, 3 + 16, y0 + 40, PALE_ACC, ACCENT, "row i  →  x_full[i+1 … i+L]", ACC_TXT)
    span(4, 4 + 16, y0 + 84, PALE_ACC, ACCENT, "row i+1  =  same window shifted by ONE sample", ACC_TXT)
    span(20, 20 + 26, y0 + 40, KEY, NAVY, "column k  →  x_full[k+1 … k+B]", NAVY)
    c.arrow([(x0 + 19 * cw + 4, y0 + 46), (x0 + 20 * cw + 12, y0 + 90)], color=ACCENT, lw=1.4)
    c.box(30, 232, 1060, 176, "", "", kind="white", lw=1.2)
    c.text(50, 258, "Store w reversed:   w_rev[k] = w[L−1−k]", fs=13, color=NAVY, bold=True, ha="left")
    c.text(50, 294, "y[i]      = Σₖ x_full[i+1+k] · w_rev[k]      → row i starts at x_full[i+1], ascending",
           fs=12, color=INK, ha="left", family="DejaVu Sans Mono")
    c.text(50, 326, "g_rev[k]  = Σᵢ x_full[k+1+i] · e[i]          → column k starts at x_full[k+1], ascending",
           fs=12, color=INK, ha="left", family="DejaVu Sans Mono")
    c.text(50, 364, "Both phases: fill WIN once, then WSLIDE (+1 sample) per row / column.   τ = k* − (L−1−L/2)",
           fs=11.5, color=INK2, ha="left")
    c.text(50, 390, "v1.0 read ascending from x_full[j]: the loop still converges but reports −τ (checked in "
           "simulation).", fs=11, color=ACC_TXT, ha="left")

    # ================= (B) circular input ring
    cx, cy, R, rw = 1450, 272, 162, 48
    c.text(1150, 30, "② Circular X / D rings — no copies", fs=15, color=NAVY, bold=True, ha="left")

    def arc(a0, a1, fc, ec):
        # word offset -> clockwise angle from 12 o'clock on screen; the canvas y axis points down,
        # so a screen angle phi corresponds to data angle phi - 90
        t0, t1 = a0 / 512 * 360 - 90, a1 / 512 * 360 - 90
        c.ax.add_patch(Wedge((cx, cy), R, t0, t1, width=rw, fc=fc, ec=ec, lw=1.4, zorder=3,
                             transform=c.ax.transData))
    # y axis is inverted in canvas coordinates, so mirror angles by drawing with negative sense
    arc(0, 191, KEY, NAVY)
    arc(191, 319, PALE_ACC, ACCENT)
    arc(319, 512, "#f3f4f6", GREY)
    for k in range(4):
        ang = np.deg2rad(90 - k * 90)
        c.ax.plot([cx + (R - rw) * np.cos(ang), cx + R * np.cos(ang)],
                  [cy - (R - rw) * np.sin(ang), cy - R * np.sin(ang)], color="white", lw=2, zorder=4)
    for off in (0, 128, 256, 384):
        phi = np.deg2rad(off / 512 * 360)
        c.text(cx + (R + 24) * np.sin(phi), cy - (R + 24) * np.cos(phi), str(off), fs=10, color=INK2)
    c.text(cx + 16, cy - R - 24, "← A7 (base of block n)", fs=10.5, color=NAVY, ha="left", bold=True)
    c.text(cx, cy - 16, "X ring", fs=13, color=NAVY, bold=True)
    c.text(cx, cy + 8, "512 words", fs=11, color=INK2)
    c.text(cx, cy + 30, "(same for D ring)", fs=10, color=INK2)
    c.box(1150, 470, 620, 0.1, "", "", kind="white", lw=0)
    leg = [(KEY, NAVY, "block n being processed: x_full[1 … 191]"),
           (PALE_ACC, ACCENT, "DMA fills block n+1 at the same time"),
           ("#f3f4f6", GREY, "free")]
    for i, (fc, ec, t) in enumerate(leg):
        c.rect(1180, 484 + i * 28, 22, 16, fc=fc, ec=ec, lw=1.2)
        c.text(1212, 492 + i * 28, t, fs=11, color=INK2, ha="left")
    c.text(1180, 578, "Base A7 advances by B = 128 per block (mod 512).\nInput writer stores sample t at "
           "(t + L−1) mod 512,\nso history is already in place and x_full[1] is 16-aligned.", fs=11, color=INK,
           ha="left", va="top", linespacing=1.4)

    # ================= (C) banks: aligned rows only
    c.text(30, 450, "③ 16 banks, one per lane — every vector access is one aligned row", fs=15, color=NAVY,
           bold=True, ha="left")
    bx, by = 30, 488
    for b in range(16):
        c.text(bx + 40 + b * 62 + 29, by, f"bank {b}", fs=9.5, color=INK2)
    rows = [("row r", ["…"] * 16, False),
            ("A7 →", [f"x{j}" for j in range(1, 17)], True),
            ("row r+2", [f"x{j}" for j in range(17, 33)], False)]
    for ri, (rl, cells, hi) in enumerate(rows):
        yy = by + 12 + ri * 36
        c.text(bx + 34, yy + 15, rl, fs=10, color=INK2, ha="right")
        for b, lab in enumerate(cells):
            c.rect(bx + 40 + b * 62, yy, 58, 30, fc=PALE_ACC if hi else "white", ec=ACCENT if hi else GREY,
                   lw=1.2 if hi else 0.8)
            c.text(bx + 40 + b * 62 + 29, yy + 15, lab if lab == "…" else lab.replace("x", "x[") + "]",
                   fs=9.5, color=ACC_TXT if hi else INK2)
    c.text(bx + 40, by + 132, "WLD W0 reads one row: x_full[1…16] — no rotator / crossbar needed.  "
           "Scalar stores (y[i], g[k]) use per-bank write enables.", fs=11, color=INK, ha="left")

    # ================= (D) memory map
    c.text(30, 680, "④ Local memory map per PE  (word addresses; 16 × 512 words = 32 KB physical)", fs=15,
           color=NAVY, bold=True, ha="left")
    regions = [("X ring", 0x000, 512, KEY, NAVY), ("D ring", 0x200, 512, KEY, NAVY),
               ("w_rev", 0x400, 64, PALE_ACC, ACCENT), ("y", 0x440, 128, FILL, NAVY), ("e", 0x4C0, 128, FILL, NAVY),
               ("g", 0x540, 64, FILL, NAVY)]
    mx, my, scale = 30, 712, 1.02
    x = mx
    for name, base, size, fc, ec in regions:
        w = size * scale
        c.rect(x, my, w, 56, fc=fc, ec=ec, lw=1.2)
        c.text(x + w / 2, my + 20, name, fs=12 if size > 100 else 10.5, color=ACC_TXT if ec == ACCENT else NAVY,
               bold=True)
        c.text(x + w / 2, my + 40, f"{size}", fs=9.5, color=INK2)
        c.text(x, my + 72, f"0x{base:03X}", fs=9, color=INK2, ha="left")
        x += w
    c.rect(x, my, 1770 - x, 56, fc="#f3f4f6", ec=GREY, lw=1.0)
    c.text((x + 1770) / 2, my + 28, "free: 6 784 words (room for larger B, L)", fs=10.5, color=INK2)
    c.text(x, my + 72, "0x580", fs=9, color=INK2, ha="left")
    c.text(30, 820, "w_rev persists across blocks (adaptive state).  v1.0's x_hist, d_hist and ping-pong copies are "
           "gone: the rings hold them in place.", fs=11.5, color=INK, ha="left")
    c.save(path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    draw(os.path.join(OUT, "memory.png"))
    print("ok")
