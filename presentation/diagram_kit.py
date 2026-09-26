"""Tiny matplotlib helpers for light-mode block diagrams (coordinates in pixels, origin top-left)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

NAVY = "#1b2f6b"       # our RTL: stroke + titles
FILL = "#eef1f8"       # our RTL: fill
KEY = "#dfe6f6"        # emphasised block fill
GREY = "#6b7280"       # external IP / secondary lines
LIGHT = "#f5f5f3"      # container fill
INK = "#111111"
INK2 = "#4b5563"
ACCENT = "#eb6834"     # used sparingly: "new / key idea"


class Canvas:
    def __init__(self, w, h, dpi=150):
        self.w, self.h = w, h
        self.fig = plt.figure(figsize=(w / 100, h / 100), dpi=dpi)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, w)
        self.ax.set_ylim(h, 0)
        self.ax.axis("off")

    def box(self, x, y, w, h, title="", sub="", kind="ours", fs=13, sub_fs=10.5, align="center",
            title_color=None, lw=1.6, radius=6, dashed=False, title_top=False, z=2):
        fc, ec = {"ours": (FILL, NAVY), "key": (KEY, NAVY), "ext": ("white", GREY),
                  "container": (LIGHT, GREY), "white": ("white", NAVY), "accent": ("#fdeee7", ACCENT)}[kind]
        p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}", fc=fc, ec=ec, lw=lw,
                           ls=(0, (5, 3)) if dashed else "-", zorder=z)
        self.ax.add_patch(p)
        tc = title_color or (INK2 if kind in ("ext", "container") else NAVY)
        if kind == "accent":
            tc = title_color or "#9a3412"
        ha = {"center": "center", "left": "left"}[align]
        tx = x + w / 2 if align == "center" else x + 10
        if title_top:
            self.ax.text(tx, y + 8, title, ha=ha, va="top", fontsize=fs, color=tc, fontweight="bold", zorder=z + 1)
            if sub:
                self.ax.text(tx, y + 8 + fs * 1.55, sub, ha=ha, va="top", fontsize=sub_fs, color=INK2, zorder=z + 1,
                             linespacing=1.35)
        else:
            if sub:
                self.ax.text(tx, y + h / 2 - 2, title, ha=ha, va="bottom", fontsize=fs, color=tc, fontweight="bold",
                             zorder=z + 1)
                self.ax.text(tx, y + h / 2 + 3, sub, ha=ha, va="top", fontsize=sub_fs, color=INK2, zorder=z + 1,
                             linespacing=1.35)
            else:
                self.ax.text(tx, y + h / 2, title, ha=ha, va="center", fontsize=fs, color=tc, fontweight="bold",
                             zorder=z + 1)
        return (x, y, w, h)

    def rect(self, x, y, w, h, fc="white", ec=NAVY, lw=1.0, z=3):
        self.ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw, zorder=z))

    def text(self, x, y, s, fs=11, color=INK2, ha="center", va="center", bold=False, z=6, family=None, **kw):
        self.ax.text(x, y, s, fontsize=fs, color=color, ha=ha, va=va, fontweight="bold" if bold else "normal",
                     zorder=z, family=family, **kw)

    def arrow(self, pts, label="", color=NAVY, lw=1.8, both=False, label_pos=0.5, label_off=(0, -9), fs=10,
              label_color=None, z=4, head=True):
        """pts: list of (x, y) points (orthogonal polyline)."""
        for i in range(len(pts) - 1):
            last = i == len(pts) - 2
            first = i == 0
            style = "-"
            if head and last and both and first:
                style = "<|-|>"
            elif head and last:
                style = "-|>"
            elif head and both and first:
                style = "<|-"
            a = FancyArrowPatch(pts[i], pts[i + 1], arrowstyle=style, mutation_scale=13, color=color, lw=lw,
                                shrinkA=0, shrinkB=0, zorder=z)
            self.ax.add_patch(a)
        if label:
            seg = max(0, min(len(pts) - 2, int(label_pos * (len(pts) - 1))))
            (x0, y0), (x1, y1) = pts[seg], pts[seg + 1]
            frac = label_pos * (len(pts) - 1) - seg
            lx, ly = x0 + (x1 - x0) * frac + label_off[0], y0 + (y1 - y0) * frac + label_off[1]
            self.ax.text(lx, ly, label, fontsize=fs, color=label_color or INK2, ha="center", va="center", zorder=z + 2,
                         bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))

    def save(self, path):
        self.fig.savefig(path, dpi=self.fig.dpi, facecolor="white")
        plt.close(self.fig)
