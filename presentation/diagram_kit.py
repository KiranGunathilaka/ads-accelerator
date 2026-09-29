"""Tiny matplotlib helpers for light-mode block diagrams (coordinates in pixels, origin top-left)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Polygon

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

    def poly(self, pts, fc=FILL, ec=NAVY, lw=1.6, z=3):
        self.ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=ec, lw=lw, joinstyle="round", zorder=z))

    def trap(self, x, y, w, h, title="", sub="", fc=KEY, ec=NAVY, fs=12, sub_fs=10, inset=0.2, up=False, notch=False):
        """Trapezoid: wide side = inputs, narrow side = output. Default: inputs on top, output at the bottom.
        up=True flips it (inputs at the bottom). notch=True draws the ALU V-notch between the two inputs."""
        d = w * inset
        if up:
            pts = [(x + d, y), (x + w - d, y), (x + w, y + h), (x, y + h)]
        elif notch:
            n = w * 0.09
            pts = [(x, y), (x + w / 2 - n, y), (x + w / 2, y + h * 0.24), (x + w / 2 + n, y), (x + w, y),
                   (x + w - d, y + h), (x + d, y + h)]
        else:
            pts = [(x, y), (x + w, y), (x + w - d, y + h), (x + d, y + h)]
        self.poly(pts, fc=fc, ec=ec)
        cy = y + h * (0.6 if notch else 0.5)
        if sub:
            self.text(x + w / 2, cy - 1, title, fs=fs, color=NAVY, bold=True, va="bottom")
            self.text(x + w / 2, cy + 2, sub, fs=sub_fs, color=INK2, va="top")
        else:
            self.text(x + w / 2, cy, title, fs=fs, color=NAVY, bold=True)

    def mux(self, x, y, w, h, orient="down", label="", fs=9.5):
        """Multiplexer: wide side takes the inputs. orient = side the output leaves from."""
        d = 0.28
        if orient == "down":
            pts = [(x, y), (x + w, y), (x + w * (1 - d), y + h), (x + w * d, y + h)]
        elif orient == "up":
            pts = [(x + w * d, y), (x + w * (1 - d), y), (x + w, y + h), (x, y + h)]
        elif orient == "right":
            pts = [(x, y), (x + w, y + h * d), (x + w, y + h * (1 - d)), (x, y + h)]
        else:
            pts = [(x, y + h * d), (x + w, y), (x + w, y + h), (x, y + h * (1 - d))]
        self.poly(pts, fc="white", ec=NAVY, lw=1.4, z=4)
        if label:
            self.text(x + w / 2, y + h / 2, label, fs=fs, color=NAVY, bold=True, z=7)

    def regfile(self, x, y, w, title, rows, row_h=22, fs=12, row_fs=10, sub=""):
        """Register-file block: a titled box holding one strip per register (like S0 / S1 / … / S7)."""
        top = 30 if not sub else 48
        h = top + row_h * len(rows) + 10
        self.box(x, y, w, h, title, sub, kind="ours", title_top=True, fs=fs, sub_fs=9.5)
        for i, r in enumerate(rows):
            self.rect(x + 12, y + top + i * row_h, w - 24, row_h, fc="white", ec=NAVY, lw=0.9, z=4)
            self.text(x + w / 2, y + top + i * row_h + row_h / 2, r, fs=row_fs, color=INK)
        return h

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
