"""ISA figures.

slide_isa.png: slide version. Format, the 32 opcodes, and the inner loop as instruction chips.
isa.png:       explainer version. Adds field typing, addressing modes and the commented Phase-1 listing.
"""
import os
from diagram_kit import Canvas, NAVY, GREY, INK, INK2, ACCENT, FILL, KEY

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
ACC_TXT = "#9a3412"

GROUPS = [
    ("00", "Vector arithmetic", ["VMAC", "VSUB", "VADD", "VSCALE", "VABS", "VMOV", "VREDUCE", "VMUL"]),
    ("01", "Memory / AGU", ["VLD", "VST", "AGU_SET", "AGU_ADD", "WLD", "WSLIDE", "SST", "SLD"]),
    ("10", "Scalar / loop", ["SMUL", "SADD", "SSUB", "SDIV", "SMOV", "SIMM", "CSR_RD", "LOOP"]),
    ("11", "Control / result", ["PKMAX", "PKOUT", "SYNC", "PKCLR", "IRQ", "NOP", "HALT", "CSR_WR"]),
]


def draw_detail(path):
    c = Canvas(1800, 900)

    # ---------------- instruction format
    c.text(30, 30, "32-bit instruction, fixed format - single-cycle decode", fs=15, color=NAVY, bold=True, ha="left")
    fields = [("OPCODE", 5, "31:27", KEY), ("DST", 5, "26:22", FILL), ("SRC1", 5, "21:17", FILL),
              ("SRC2", 5, "16:12", FILL), ("IMM12", 12, "11:0", "white")]
    x0, unit, y = 30, 34, 58
    x = x0
    for name, bits, rng, fc in fields:
        w = bits * unit
        c.rect(x, y, w, 58, fc=fc, ec=NAVY, lw=1.4)
        c.text(x + w / 2, y + 22, name, fs=14, color=NAVY, bold=True)
        c.text(x + w / 2, y + 44, f"[{rng}]  {bits} b", fs=10.5, color=INK2)
        x += w
    c.text(x0, 136, "OPCODE[4:3] = group  ·  fields typed by opcode: V0-V7, W0-W7 (window), S0-S7 / ZERO, A0-A7  ·  "
           "CSR index in IMM12", fs=11, color=INK2, ha="left")

    # ---------------- opcode map
    c.text(30, 172, "All 32 opcodes", fs=15, color=NAVY, bold=True, ha="left")
    cw, ch, gx, gy = 128, 52, 230, 196
    for col in range(8):
        c.text(gx + col * cw + cw / 2, gy - 2, f"{col:03b}", fs=10, color=INK2, va="bottom")
    for r, (code, name, ops) in enumerate(GROUPS):
        yy = gy + 6 + r * (ch + 8)
        c.text(30, yy + ch / 2 - 9, code, fs=13, color=NAVY, bold=True, ha="left")
        c.text(30, yy + ch / 2 + 10, name, fs=11, color=INK2, ha="left")
        for col, op in enumerate(ops):
            c.rect(gx + col * cw + 2, yy, cw - 6, ch, fc=FILL, ec=NAVY, lw=1.0)
            c.text(gx + col * cw + cw / 2 - 1, yy + ch / 2, op, fs=12, color=NAVY, bold=True)

    # ---------------- addressing modes (right column)
    ax0 = 1270
    c.text(ax0, 30, "Addressing modes", fs=15, color=NAVY, bold=True, ha="left")
    modes = [
        ("Post-increment", "VLD V4, [A2]+16", "load 16 lanes, then A2 += 16"),
        ("Circular (ring)", "AGU_SET A0, A7, X_RING, circ", "A0 wraps mod 512 inside the\ninput ring: no history copies"),
        ("Sliding window", "WSLIDE [A0], len=64", "WIN shifts by 1 sample and pulls\nM[A0]: next row / column of X"),
    ]
    for i, (t, code, desc) in enumerate(modes):
        yy = 58 + i * 130
        c.box(ax0, yy, 500, 116, "", "", kind="white", lw=1.2)
        c.text(ax0 + 14, yy + 20, t, fs=12.5, color=NAVY, bold=True, ha="left")
        c.text(ax0 + 14, yy + 48, code, fs=11.5, color=INK, ha="left", family="DejaVu Sans Mono")
        c.text(ax0 + 14, yy + 84, desc, fs=10.5, color=INK2, ha="left")

    # ---------------- phase 1 inner loop
    c.text(30, 520, "Phase 1 inner loop  -  y[i] = row i of X · w   (all 3 PEs, 48 MACs per VMAC)", fs=15, color=NAVY,
           bold=True, ha="left")
    code = [
        ("LOOP    128, 7", "zero-overhead hardware loop: 128 rows, 7-instruction body"),
        ("VMAC.C  W0, V4", "VACC = x[i+1..i+16] × w_rev[0..15]   (clear + multiply)"),
        ("VMAC    W1, V5", "VACC += next 16 taps"),
        ("VMAC    W2, V6", ""),
        ("VMAC    W3, V7", "64 taps done - w stays in V4-V7 for the whole phase"),
        ("VREDUCE S1, >>23, rnd, sat16", "adder tree 16→1 → y[i] in Q1.15"),
        ("WSLIDE  [A0], len=64", "window → row i+1 (one new sample from the X ring)"),
        ("SST     S1, [A3]+1", "store y[i]"),
    ]
    c.box(30, 546, 1740, 30 * len(code) + 26, "", "", kind="white", lw=1.2)
    for i, (ins, cm) in enumerate(code):
        yy = 566 + i * 30
        c.text(52, yy, ins, fs=12, color=INK if i else NAVY, ha="left", family="DejaVu Sans Mono",
               bold=(i == 0))
        if cm:
            c.text(470, yy, "; " + cm, fs=11, color=INK2, ha="left", family="DejaVu Sans Mono")
    c.save(path)


def draw_slide(path):
    c = Canvas(1800, 840)

    # ---------------- format, with what each field means
    c.text(30, 30, "Every instruction: 32 bits, one fixed format", fs=16, color=NAVY, bold=True, ha="left")
    fields = [("OPCODE", 5, "which operation", KEY), ("DST", 5, "where the result goes", FILL),
              ("SRC1", 5, "first input", FILL), ("SRC2", 5, "second input", FILL),
              ("IMM12", 12, "a constant: offset, count, shift", "white")]
    unit, x = 1740 / 32, 30
    for name, bits, meaning, fc in fields:
        w = bits * unit
        c.rect(x, 58, w, 64, fc=fc, ec=NAVY, lw=1.5)
        c.text(x + w / 2, 80, name, fs=15, color=NAVY, bold=True)
        c.text(x + w / 2, 105, f"{bits} bits", fs=11, color=INK2)
        c.text(x + w / 2, 140, meaning, fs=11.5, color=INK2)
        x += w

    # ---------------- opcode map
    c.text(30, 196, "32 instructions in 4 groups", fs=16, color=NAVY, bold=True, ha="left")
    cw, ch, gx, gy = 190, 56, 250, 224
    for r, (code, name, ops) in enumerate(GROUPS):
        yy = gy + r * (ch + 10)
        c.text(30, yy + ch / 2, name, fs=13, color=NAVY, bold=True, ha="left")
        for col, op in enumerate(ops):
            c.rect(gx + col * cw + 2, yy, cw - 8, ch, fc=FILL, ec=NAVY, lw=1.0)
            c.text(gx + col * cw + cw / 2 - 2, yy + ch / 2, op, fs=13.5, color=NAVY, bold=True)

    # ---------------- inner loop as chips
    c.text(30, 520, "The inner loop: 7 instructions, repeated 128 times by LOOP with no branch cost", fs=16,
           color=NAVY, bold=True, ha="left")
    chips = ["VMAC", "VMAC", "VMAC", "VMAC", "VREDUCE", "WSLIDE", "SST"]
    x0, y0, w, h, gap = 150, 610, 170, 64, 36
    for i, op in enumerate(chips):
        x = x0 + i * (w + gap)
        c.box(x, y0, w, h, op, kind="ours", fs=15, radius=8)
        if i < len(chips) - 1:
            c.arrow([(x + w, y0 + h / 2), (x + w + gap, y0 + h / 2)], lw=1.6)
    xe = x0 + 6 * (w + gap) + w
    c.arrow([(xe - w / 2, y0), (xe - w / 2, 572), (x0 + w / 2, 572), (x0 + w / 2, y0)], lw=1.8, color=ACCENT)
    c.text((x0 + xe) / 2, 572, "  LOOP 128  ", fs=12.5, color=ACC_TXT, bold=True,
           bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none"))
    notes = [(0, 3, "4 × 16 lanes = 64 multiply-adds"), (4, 4, "sum 16 lanes → 1"),
             (5, 5, "slide window by 1"), (6, 6, "store result")]
    for a, b, t in notes:
        xa, xb = x0 + a * (w + gap), x0 + b * (w + gap) + w
        c.ax.plot([xa, xa, xb, xb], [y0 + h + 12, y0 + h + 20, y0 + h + 20, y0 + h + 12], color=GREY, lw=1.2)
        c.text((xa + xb) / 2, y0 + h + 42, t, fs=12, color=INK2)
    c.text(30, 800, "Whole block: 78 instructions.  Checked in an instruction-level simulator: bit-exact with the "
           "fixed-point model.", fs=12.5, color=INK2, ha="left")
    c.save(path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    draw_slide(os.path.join(OUT, "slide_isa.png"))
    draw_detail(os.path.join(OUT, "isa.png"))
    print("ok")
