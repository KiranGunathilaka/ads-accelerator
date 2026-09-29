"""PE datapath diagram in the style of the week-2 draw.io draft: register files, ALUs, muxes, MAC lanes, adder tree.

Top: the shared control unit (fetch with the hardware loop, decode, AGU, CSRs).
Bottom: one processing element (PE1 and PE2 are identical copies).
"""
import os
from matplotlib.patches import Circle
from diagram_kit import Canvas, NAVY, GREY, INK, INK2, ACCENT, FILL, KEY

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
ACC_TXT = "#9a3412"
PALE_ACC = "#fdeee7"


def dot(c, x, y, color=NAVY):
    c.ax.add_patch(Circle((x, y), 4, fc=color, ec=color, zorder=6))


def wire_label(c, x, y, s, fs=9.5, color=INK2, ha="center"):
    c.text(x, y, s, fs=fs, color=color, ha=ha, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))


def op_box(c, x, y, w, h, s):
    """Control input of a unit: which operation the decoded instruction selects (the draft's 'CTRL - Op')."""
    c.box(x, y, w, h, "", kind="white", lw=1.1, radius=3, dashed=True, z=4)
    c.text(x + w / 2, y + h / 2, s, fs=9.5, color=INK2, linespacing=1.25)


def lane(c, x, y, w, name):
    """One DSP48E1 lane: multiplier, adder, P register (the accumulator) with its feedback."""
    c.rect(x, y, w, 96, fc="white", ec=NAVY, lw=1.1, z=4)
    cx = x + w / 2
    c.text(cx, y + 13, name, fs=9.5, color=NAVY, bold=True)
    mx, ax_, py = cx - 30, cx + 2, y + 50
    c.ax.add_patch(Circle((mx, py), 12, fc=KEY, ec=NAVY, lw=1.2, zorder=5))
    c.ax.add_patch(Circle((ax_, py), 12, fc=KEY, ec=NAVY, lw=1.2, zorder=5))
    c.text(mx, py, "×", fs=12, color=NAVY, bold=True)
    c.text(ax_, py, "+", fs=12, color=NAVY, bold=True)
    c.rect(cx + 22, py - 10, 28, 20, fc=FILL, ec=NAVY, lw=1.1, z=5)
    c.text(cx + 36, py, "P", fs=10, color=NAVY, bold=True)
    c.arrow([(x + 4, py), (mx - 12, py)], lw=1.2)
    c.arrow([(mx + 12, py), (ax_ - 12, py)], lw=1.2)
    c.arrow([(ax_ + 12, py), (cx + 22, py)], lw=1.2)
    c.arrow([(cx + 36, py - 10), (cx + 36, py - 22), (ax_, py - 22), (ax_, py - 12)], lw=1.1)
    c.arrow([(cx + 36, py + 10), (cx + 36, y + 96)], lw=1.2, head=False)
    return cx + 36


def draw(path):
    c = Canvas(1800, 1016)

    # ========================================================= shared control unit
    c.box(12, 12, 1776, 256, "", kind="container", z=1)
    c.text(28, 32, "Control unit  —  one copy, drives all 3 PEs", fs=14, color=INK2, bold=True, ha="left")

    # --- fetch: PC, next-PC mux, +1, loop stack, IMEM, IR, decode
    c.box(110, 50, 190, 52, "Loop stack  ×2", "start · end · count", fs=11.5, sub_fs=9.5, radius=4)
    c.mux(56, 132, 26, 80, orient="right")
    c.box(110, 150, 70, 44, "PC", fs=13, radius=3)
    c.box(118, 214, 54, 28, "+1", fs=11, radius=3)
    c.box(214, 126, 160, 92, "IMEM", "512 × 32 bit\n(BRAM18)", fs=13, sub_fs=9.5, radius=4)
    c.box(404, 150, 60, 44, "IR", fs=13, radius=3)
    c.box(494, 108, 222, 124, "Decode + issue", "scoreboard: stall until\nthe operands are ready", kind="key",
          fs=12.5, sub_fs=9.8, radius=4)
    c.arrow([(82, 172), (110, 172)], lw=1.4)
    c.arrow([(180, 172), (214, 172)], lw=1.4)
    c.arrow([(145, 194), (145, 214)], lw=1.2)
    c.arrow([(118, 228), (40, 228), (40, 196), (56, 196)], lw=1.2)
    c.arrow([(110, 76), (40, 76), (40, 148), (56, 148)], lw=1.2)
    wire_label(c, 40, 112, "loop\nstart", fs=8.5)
    c.arrow([(374, 172), (404, 172)], lw=1.4)
    c.arrow([(464, 172), (494, 172)], lw=1.4)
    c.arrow([(330, 60), (330, 126)], lw=1.2, color=GREY)
    c.text(340, 80, "program written\nby the ARM", fs=9, color=INK2, ha="left", va="center")

    # --- AGU: address registers, adder, circular wrap
    c.text(770, 32, "Address generator (AGU)", fs=11.5, color=NAVY, bold=True, ha="left")
    c.regfile(770, 56, 140, "Address regs", ["A0", "A1", "…", "A7"], fs=11, row_fs=10)
    c.box(1023, 50, 110, 32, "IMM", fs=11, radius=3)
    c.trap(950, 100, 170, 56, "+", notch=True, fs=14)
    c.box(944, 176, 182, 32, "circular wrap, mod 512", fs=9.5, radius=3)
    c.arrow([(910, 90), (992, 90), (992, 100)], lw=1.3)
    c.arrow([(1078, 82), (1078, 100)], lw=1.3)
    c.arrow([(1035, 156), (1035, 176)], lw=1.3)
    c.arrow([(944, 192), (928, 192), (928, 150), (910, 150)], lw=1.3)
    wire_label(c, 1000, 238, "post-increment:  An ← An + IMM", fs=9)

    # --- CSRs + sequencer
    c.text(1250, 32, "Registers for the ARM", fs=11.5, color=NAVY, bold=True, ha="left")
    c.regfile(1250, 56, 270, "Control & status (CSRs)",
              ["CTRL · STATUS", "MU · B · L", "TAU21 · TAU31 · TAU41", "…  16 in total"], fs=11, row_fs=9.8)
    c.arrow([(1520, 96), (1770, 96)], "AXI4-Lite  ↔  ARM", both=True, label_off=(0, -13), fs=10)
    c.box(1560, 140, 200, 76, "Sequencer", "SYNC · HALT\nIRQ → ARM", fs=12, sub_fs=9.8, radius=4)

    # --- broadcast bus
    c.rect(40, 284, 1720, 30, fc=KEY, ec=NAVY, lw=1.2)
    c.text(900, 299, "broadcast every cycle to PE0, PE1 and PE2:   control word  +  address", fs=11.5,
           color=NAVY, bold=True)
    c.arrow([(605, 232), (605, 284)], "control word", label_pos=0.5, label_off=(0, 0), fs=9.5)
    c.arrow([(840, 184), (840, 284)], "address", label_pos=0.62, label_off=(0, 0), fs=9.5)

    # ========================================================= processing element
    c.box(12, 332, 1776, 670, "", kind="white", lw=1.8, z=1)
    c.text(1772, 350, "Processing element  —  PE0 shown;  PE1 and PE2 are identical copies", fs=13.5,
           color=NAVY, bold=True, ha="right")

    # --- local memory (16 banks) with write-select mux and single-word read mux
    c.mux(50, 380, 250, 32, orient="down", label="write select")
    for x, s in [(90, "input writer"), (175, "VST"), (260, "SST")]:
        c.arrow([(x, 366), (x, 380)], lw=1.2, color=GREY)
        c.text(x, 358, s, fs=9, color=INK2)
    c.box(40, 440, 440, 250, "Local data memory", "16 banks · each 512 × 32 bit (one BRAM18)", title_top=True,
          fs=13, sub_fs=9.8, radius=4)
    bw = (440 - 32) / 16
    for i in range(16):
        c.rect(56 + i * bw + 1, 500, bw - 4, 150, fc="white", ec=NAVY, lw=0.9, z=4)
        c.text(56 + i * bw + bw / 2 - 1, 575, str(i), fs=8.5, color=INK2)
    c.text(260, 670, "bank = address mod 16", fs=9, color=INK2)
    c.arrow([(175, 412), (175, 440)], lw=1.4)
    c.arrow([(350, 314), (350, 440)], lw=1.5)
    wire_label(c, 350, 420, "address", fs=9)
    c.mux(412, 406, 56, 24, orient="up", label="16:1", fs=8)
    c.arrow([(440, 440), (440, 430)], lw=1.2)

    # single-word path: WSLIDE (into the window) and SLD (into the scalar registers)
    c.arrow([(440, 406), (440, 376), (1685, 376), (1685, 400)], lw=1.4, color=ACCENT)
    c.arrow([(1010, 376), (1010, 456), (980, 456)], lw=1.4, color=ACCENT)
    dot(c, 1010, 376, ACCENT)
    wire_label(c, 720, 376, "1 word  (WSLIDE → window,  SLD → scalar regs)", fs=9.5, color=ACC_TXT)

    # row path: 16 words (VLD → vector regs, WLD → window)
    c.arrow([(480, 560), (540, 560), (540, 456), (580, 456)], lw=1.6)
    c.arrow([(540, 560), (540, 690), (580, 690)], lw=1.6)
    dot(c, 540, 560)
    wire_label(c, 510, 544, "16 words", fs=8.5)

    # --- window register
    c.box(580, 408, 400, 96, "Window register  ·  128 × 16 bit", kind="accent", title_top=True, fs=11.5,
          radius=4)
    cw = (400 - 24) / 8
    for i in range(8):
        c.rect(592 + i * cw + 1, 440, cw - 4, 50, fc="white", ec=ACCENT, lw=1.1, z=4)
        c.text(592 + i * cw + cw / 2 - 1, 465, f"W{i}", fs=10, color=ACC_TXT, bold=True)
    c.mux(720, 520, 120, 28, orient="down", label="8 : 1", fs=9)
    c.arrow([(780, 504), (780, 520)], lw=1.3, color=ACCENT)
    c.arrow([(780, 548), (780, 570), (1030, 570), (1030, 625), (1044, 625)], lw=1.4, color=ACCENT)
    wire_label(c, 905, 570, "16 samples", fs=9, color=ACC_TXT)

    # --- vector register file
    c.regfile(580, 610, 240, "Vector registers", ["V0", "V1", "…", "V7"], sub="8 × (16 lanes × 32 bit)",
              fs=12, row_fs=10)
    c.arrow([(820, 655), (1044, 655)], lw=1.4)
    wire_label(c, 930, 655, "Va", fs=9)
    c.box(910, 701, 80, 28, "» sh", fs=10.5, radius=3)
    c.arrow([(820, 715), (910, 715)], lw=1.4)
    c.arrow([(990, 715), (1100, 715)], lw=1.4)
    wire_label(c, 865, 715, "Vb", fs=9)
    wire_label(c, 1045, 715, "A port\n25 bit", fs=8.5)

    # B-port select: window chunk or vector register
    c.mux(1044, 610, 30, 60, orient="right")
    c.arrow([(1074, 640), (1100, 640)], lw=1.4)
    wire_label(c, 1087, 596, "B port\n18 bit", fs=8.5)

    # --- vector ALU (+ write-back) and peak detector
    c.trap(610, 800, 180, 60, "Vector ALU", notch=True, fs=11)
    c.arrow([(655, 756), (655, 800)], lw=1.3)
    c.arrow([(745, 756), (745, 800)], lw=1.3)
    c.arrow([(700, 860), (700, 880), (850, 880), (850, 740), (820, 740)], lw=1.3)
    op_box(c, 870, 806, 120, 46, "op: add · sub\nabs · mov")
    c.arrow([(655, 780), (595, 780), (595, 910)], lw=1.3)
    dot(c, 655, 780)
    c.box(580, 910, 240, 66, "Peak detector", "|v| compare tree + running max", fs=12, sub_fs=9.5, radius=4)
    c.arrow([(820, 943), (900, 943)], lw=1.3)
    c.text(908, 943, "τ → TAU CSR", fs=10, color=INK2, ha="left")

    # --- 16 MAC lanes
    c.box(1100, 596, 470, 170, "", kind="key", radius=4)
    c.text(1116, 612, "16 MAC lanes  —  one DSP48E1 per lane", fs=11.5, color=NAVY, bold=True, ha="left")
    outs = []
    for x, name in [(1116, "DSP48  #0"), (1242, "DSP48  #1"), (1444, "DSP48  #15")]:
        outs.append(lane(c, x, 656, 110, name))
    c.text(1398, 704, "…", fs=18, color=NAVY, bold=True)
    op_box(c, 1400, 552, 170, 32, "op: MUL · MAC · clear")
    c.arrow([(1485, 584), (1485, 596)], lw=1.1, color=GREY)
    c.text(1116, 634, "P = 48-bit accumulator (VACC), fed back every cycle", fs=9, color=INK2, ha="left")

    # --- adder tree + round/shift/saturate → scalar registers
    c.trap(1140, 806, 420, 56, "Adder tree  16 → 1", fs=12, inset=0.24)
    for x in outs:
        c.arrow([(x, 752), (x, 806)], lw=1.2)
    c.box(1250, 882, 200, 34, "round · » sh · saturate", fs=10.5, radius=3)
    c.arrow([(1350, 862), (1350, 882)], lw=1.3)
    c.arrow([(1450, 899), (1590, 899), (1590, 470), (1610, 470)], lw=1.4)

    # --- scalar register file + scalar ALU
    c.regfile(1610, 400, 150, "Scalar regs", ["S0", "S1", "…", "S7"], fs=11.5, row_fs=10)
    c.trap(1610, 566, 150, 58, "ALU", notch=True, fs=11.5)
    c.arrow([(1647, 528), (1647, 566)], lw=1.3)
    c.arrow([(1722, 528), (1722, 566)], lw=1.3)
    c.arrow([(1685, 624), (1685, 642), (1778, 642), (1778, 490), (1760, 490)], lw=1.3)
    op_box(c, 1610, 662, 150, 46, "op: add · sub\nmul · div")

    # --- how to read
    c.box(40, 760, 440, 150, "", kind="white", lw=1.0, radius=4)
    c.text(56, 778, "How to read this", fs=11.5, color=NAVY, bold=True, ha="left")
    c.text(56, 800, "Solid arrows are data wires.\nDashed 'op' boxes: the operation the broadcast\n"
           "instruction selects for that unit.\nGrey stubs (input writer, VST, SST) are wires\n"
           "drawn as labels to keep the picture readable.", fs=9.8, color=INK2, ha="left", va="top",
           linespacing=1.4)
    c.save(path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    draw(os.path.join(OUT, "pe_datapath.png"))
    print("ok")
