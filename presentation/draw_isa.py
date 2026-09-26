"""ISA figure: instruction format, 32-opcode map (v1.1), addressing modes, Phase-1 inner loop."""
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
NEW = {"AGU_ADD", "WLD", "WSLIDE", "SST", "SLD", "LOOP", "PKCLR"}


def draw(path):
    c = Canvas(1800, 900)

    # ---------------- instruction format
    c.text(30, 30, "32-bit instruction, fixed format — single-cycle decode", fs=15, color=NAVY, bold=True, ha="left")
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
    c.text(x0, 136, "OPCODE[4:3] = group  ·  fields typed by opcode: V0–V7, W0–W7 (window), S0–S7 / ZERO, A0–A7  ·  "
           "CSR index in IMM12", fs=11, color=INK2, ha="left")

    # ---------------- opcode map
    c.text(30, 172, "All 32 opcodes (v1.1)", fs=15, color=NAVY, bold=True, ha="left")
    cw, ch, gx, gy = 128, 52, 230, 196
    for col in range(8):
        c.text(gx + col * cw + cw / 2, gy - 2, f"{col:03b}", fs=10, color=INK2, va="bottom")
    for r, (code, name, ops) in enumerate(GROUPS):
        yy = gy + 6 + r * (ch + 8)
        c.text(30, yy + ch / 2 - 9, code, fs=13, color=NAVY, bold=True, ha="left")
        c.text(30, yy + ch / 2 + 10, name, fs=11, color=INK2, ha="left")
        for col, op in enumerate(ops):
            new = op in NEW
            c.rect(gx + col * cw + 2, yy, cw - 6, ch, fc="#fdeee7" if new else FILL, ec=ACCENT if new else NAVY,
                   lw=1.4 if new else 1.0)
            c.text(gx + col * cw + cw / 2 - 1, yy + ch / 2, op, fs=12, color=ACC_TXT if new else NAVY, bold=True)
    c.rect(30, 452, 22, 16, fc="#fdeee7", ec=ACCENT, lw=1.4)
    c.text(60, 460, "new in v1.1 (memory addressing, loops) — replaces AGU_INC / AGU_SLIDE / AGU_COL / LOOP_SET / "
           "VLD_S / SACC_CLR / PHASE_END", fs=10.5, color=INK2, ha="left")

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
    c.text(30, 520, "Phase 1 inner loop  —  y[i] = row i of X · w   (all 3 PEs, 48 MACs per VMAC)", fs=15, color=NAVY,
           bold=True, ha="left")
    code = [
        ("LOOP    128, 7", "zero-overhead hardware loop: 128 rows, 7-instruction body"),
        ("VMAC.C  W0, V4", "VACC = x[i+1..i+16] × w_rev[0..15]   (clear + multiply)"),
        ("VMAC    W1, V5", "VACC += next 16 taps"),
        ("VMAC    W2, V6", ""),
        ("VMAC    W3, V7", "64 taps done — w stays in V4–V7 for the whole phase"),
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
    c.text(30, 850, "Whole block (5 phases) = 78 instructions (312 B of IMEM) · verified bit-exact against the "
           "fixed-point model in an instruction-level simulator", fs=11.5, color=INK2, ha="left")
    c.save(path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    draw(os.path.join(OUT, "isa.png"))
    print("ok")
