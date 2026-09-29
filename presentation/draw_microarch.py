"""Microarchitecture diagrams.

slide_microarch.png: slide version. Hardware blocks only: Zynq PS, DMA, control unit, 3 PEs.
microarch.png:       explainer version. Every port, CSR and the inside of PE0 in detail.
"""
import os
from diagram_kit import Canvas, NAVY, GREY, INK2, ACCENT, FILL, KEY

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
ACC_TXT = "#9a3412"


def draw_detail(path):
    c = Canvas(1800, 930)

    # ---------------- Zynq PS
    c.box(12, 14, 262, 902, "Zynq PS", "", kind="container", title_top=True, fs=13, dashed=True)
    c.box(30, 64, 226, 212, "ARM Cortex-A9", "C program (driver)\n• load microprogram → IMEM\n• write μ, B, L → CSRs\n"
          "• flush cache, start DMA\n• on IRQ: read τ21 τ31 τ41\n• 3-D triangulation", kind="ext", title_top=True,
          sub_fs=10.5)
    c.box(30, 770, 226, 120, "DDR3", "4-channel audio\n(16-bit PCM, interleaved)", kind="ext", title_top=True)

    # ---------------- PL glue IP
    c.box(292, 14, 262, 902, "PL: standard IP", "", kind="container", title_top=True, fs=13, dashed=True)
    c.box(310, 110, 226, 80, "AXI Interconnect", "(SmartConnect)", kind="ext")
    c.box(310, 570, 226, 140, "AXI DMA  (MM2S)", "Xilinx AXI DMA\nor Forencich verilog-axi\n(free, vendor-neutral)",
          kind="ext", title_top=True)
    c.arrow([(256, 150), (310, 150)], "M_AXI_GP0", label_off=(0, -13))
    c.arrow([(423, 190), (423, 570)], "DMA control", label_pos=0.4, label_off=(0, 0), color=GREY)
    c.arrow([(340, 710), (340, 830), (256, 830)], "S_AXI_HP0", label_pos=0.75, label_off=(0, -13), color=GREY,
            both=True)

    # ---------------- SIMD cluster container
    c.box(572, 14, 1216, 902, "SIMD cluster  —  custom RTL, vendor-neutral Verilog", "", kind="container",
          title_top=True, fs=13.5)

    # AXI-Lite slave
    c.box(590, 64, 246, 146, "AXI4-Lite slave", "16 CSRs: CTRL, μ, B, L,\nτ21 / τ31 / τ41, status …\n"
          "+ IMEM write window", title_top=True)
    c.arrow([(536, 150), (590, 150)])

    # Control unit
    c.box(852, 64, 918, 146, "Control unit  —  one per cluster, shared by all PEs", "", kind="key", title_top=True)
    sub = [("IMEM", "512 × 32 bit\n(1 BRAM18)"), ("Fetch", "PC +\n2-level loop stack"),
           ("Decode / issue", "scoreboard\n(RAW stalls)"), ("AGU", "A0–A7, post-increment,\ncircular mod 512"),
           ("Sequencer", "SYNC · HALT · IRQ\nblock-ready wait")]
    for i, (t, s) in enumerate(sub):
        x = 866 + i * 180
        c.box(x, 100, 166, 96, t, s, kind="white", fs=12, sub_fs=9.8, radius=4)
        if i < 4:
            c.arrow([(x + 166, 148), (x + 180, 148)], lw=1.4)
    c.arrow([(836, 110), (866, 110)], lw=1.4)
    c.arrow([(1676, 64), (1676, 46), (143, 46), (143, 64)], "IRQ_F2P  (level; ARM clears it)", color=ACCENT,
            label_pos=0.5, label_off=(0, 0), label_color=ACC_TXT)

    # Input writer (vertical, next to the DMA)
    c.box(590, 250, 190, 620, "Input writer", "AXI4-Stream slave\n\nbeat =\n{mic4, mic3, mic2, mic1}\n× 16 bit\n\n"
          "mic2 → PE0 X ring\nmic3 → PE1 X ring\nmic4 → PE2 X ring\n\nmic1 → D ring of\nevery PE (broadcast)\n\n"
          "sample counter\n→ 'block ready'", title_top=True, sub_fs=10.2)
    c.arrow([(536, 640), (590, 640)], "AXI4-Stream\n64-bit", label_off=(0, -26), fs=9.8)
    c.arrow([(740, 250), (740, 228), (1586, 228), (1586, 196)], "block ready", label_pos=0.62, label_off=(0, 0),
            fs=9.8)

    # broadcast bus
    c.rect(800, 256, 970, 28, fc=KEY, ec=NAVY, lw=1.2)
    c.text(1285, 270, "broadcast each cycle: one control word + one address → PE0, PE1, PE2 (lockstep)", fs=11.5,
           color=NAVY, bold=True)
    c.arrow([(1300, 196), (1300, 256)], lw=1.6)

    # PE shadows + PE0
    c.box(836, 332, 950, 570, "", "", kind="white", lw=1.1, z=1)
    c.box(818, 314, 950, 570, "", "", kind="white", lw=1.1, z=1)
    c.box(800, 296, 950, 570, "", "", kind="white", lw=1.8, z=2)
    c.text(816, 316, "PE0  (Mic2 ↔ Mic1)  —  PE1 (Mic3) and PE2 (Mic4) are identical", fs=12.5, color=NAVY, bold=True, ha="left")
    for x in (900, 1470, 1660):
        c.arrow([(x, 284), (x, 296)], lw=1.4)

    # local data memory: 16 banks
    c.text(818, 350, "Local data memory — 16 banks, one per lane (BRAM18, 512 × 32)", fs=11, color=NAVY, bold=True,
           ha="left")
    for i in range(16):
        c.rect(818 + i * 34, 362, 30, 58, fc=FILL, ec=NAVY, lw=1.0)
        c.text(818 + i * 34 + 15, 391, f"b{i}", fs=8.5, color=INK2)
    c.text(1090, 432, "address a → bank a mod 16, row a / 16  ·  every vector access is one aligned row", fs=9.8,
           color=INK2)
    c.arrow([(780, 391), (818, 391)], color=GREY, lw=1.4)

    # VRF + scalar
    c.box(1388, 350, 176, 104, "VRF  V0–V7", "8 × 16 lanes × 32 bit\n↔ memory: VLD / VST", fs=12.5, sub_fs=9.8)
    c.box(1578, 350, 158, 104, "Scalar unit", "S0–S7, add /\nsub / mul / div", fs=12.5)
    c.arrow([(1362, 391), (1388, 391)], both=True, lw=1.5)

    # window register
    c.text(818, 468, "Sliding-window register WIN (128 × 16-bit)", fs=11, color=NAVY, bold=True,
           ha="left")
    for i in range(8):
        c.rect(818 + i * 68, 480, 64, 38, fc="#fdeee7", ec=ACCENT, lw=1.2)
        c.text(818 + i * 68 + 32, 499, f"W{i}", fs=10.5, color=ACC_TXT, bold=True)
    c.arrow([(1368, 499), (1360, 499)], color=ACCENT, lw=1.6)
    c.text(1372, 499, "1 new sample\nper row (WSLIDE)", fs=9.5, color=ACC_TXT, ha="left")
    c.arrow([(1330, 442), (1330, 480)], color=ACCENT, lw=1.6)
    c.text(1322, 458, "WLD: 16 samples", fs=9.5, color=ACC_TXT, ha="right")

    # MAC lanes
    c.text(818, 552, "16 MAC lanes · DSP48E1 (25×18, 48-bit acc = VACC)", fs=11, color=NAVY,
           bold=True, ha="left")
    for i in range(16):
        c.rect(818 + i * 44, 564, 40, 48, fc=KEY, ec=NAVY, lw=1.0)
        c.text(818 + i * 44 + 20, 588, "×+", fs=11, color=NAVY, bold=True)
    c.arrow([(1326, 518), (1326, 564)], color=ACCENT, lw=1.6)
    c.text(1318, 541, "x (window)", fs=9.8, color=ACC_TXT, ha="right")
    c.arrow([(1500, 454), (1500, 564)], lw=1.5)
    c.text(1492, 541, "w or e", fs=9.8, color=INK2, ha="right")

    # peak detector
    c.box(1578, 540, 158, 150, "Peak detect", "|w| comparator\ntree + running\nmax & index\n→ τ to CSR",
          fs=11.5, sub_fs=9.8, title_top=True)
    c.arrow([(1564, 430), (1570, 430), (1570, 600), (1578, 600)], lw=1.3)

    # adder tree + VALU
    c.box(818, 650, 370, 76, "Adder tree 16 → 1", "4 pipelined stages + round / shift / saturate", fs=12.5)
    c.arrow([(1003, 612), (1003, 650)])
    c.box(1208, 650, 356, 76, "Vector ALU", "add / sub / abs / scale (saturating)", fs=12.5)
    c.arrow([(1548, 454), (1548, 650)], both=True, lw=1.3)
    c.arrow([(1003, 726), (1003, 760), (1745, 760), (1745, 430), (1736, 430)], "", lw=1.5)
    c.text(1330, 760, "VREDUCE → y[i] or g[k] → scalar → SST to memory", fs=9.8, color=INK2,
           bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none"))

    # legend
    c.box(818, 812, 26, 20, "", "", kind="ours", radius=3)
    c.text(852, 822, "custom RTL", fs=10.5, ha="left")
    c.box(970, 812, 26, 20, "", "", kind="ext", radius=3)
    c.text(1004, 822, "Xilinx / free third-party IP", fs=10.5, ha="left")
    c.rect(1216, 812, 26, 20, fc="#fdeee7", ec=ACCENT, lw=1.2)
    c.text(1250, 822, "sliding-window path (memory addressing)", fs=10.5, ha="left")

    c.save(path)


def pe_column(c, px, py, name, pair):
    """One PE as a stack of hardware blocks. Data enters at the bottom (memory) and flows up."""
    W, x0, iw = 394, px + 14, 366
    c.box(px, py, W, 398, "", "", kind="white", lw=1.8, z=2)
    c.text(x0, py + 20, name, fs=15, color=NAVY, bold=True, ha="left")
    c.text(px + W - 14, py + 20, pair, fs=11, color=INK2, ha="right")

    # top row: ALUs and peak detector
    bw = (iw - 20) / 3
    for i, t in enumerate(["Vector ALU", "Scalar unit", "Peak detect"]):
        c.box(x0 + i * (bw + 10), py + 42, bw, 50, t, kind="ours", fs=11, radius=4)
    # adder tree (wide side = 16 inputs at the bottom)
    c.trap(x0 + 20, py + 110, iw - 40, 46, "Adder tree  16 → 1", up=True, fs=12, inset=0.3)
    # 16 MAC lanes
    c.box(x0, py + 174, iw, 76, "16 MAC lanes  (DSP48E1)", kind="key", title_top=True, fs=12, radius=4)
    cw = (iw - 24) / 16
    for i in range(16):
        c.rect(x0 + 12 + i * cw + 1, py + 208, cw - 3, 32, fc="white", ec=NAVY, lw=0.9, z=4)
        c.text(x0 + 12 + i * cw + cw / 2 - 0.5, py + 224, "×", fs=10.5, color=NAVY, bold=True)
    # window register + vector registers
    hw = (iw - 10) / 2
    c.box(x0, py + 268, hw, 48, "Window register", kind="accent", fs=11.5, radius=4)
    c.box(x0 + hw + 10, py + 268, hw, 48, "Vector registers", kind="ours", fs=11.5, radius=4)
    # local memory: 16 banks
    c.box(x0, py + 334, iw, 56, "Local memory  ·  16 banks", kind="ours", title_top=True, fs=11.5, radius=4)
    for i in range(16):
        c.rect(x0 + 12 + i * cw + 1, py + 360, cw - 3, 22, fc="white", ec=NAVY, lw=0.8, z=4)

    # data flows upwards
    for x in (x0 + hw / 2, x0 + hw + 10 + hw / 2):
        c.arrow([(x, py + 334), (x, py + 316)], lw=1.5)
        c.arrow([(x, py + 268), (x, py + 250)], lw=1.5)
    c.arrow([(x0 + iw / 2, py + 174), (x0 + iw / 2, py + 156)], lw=1.5)
    c.arrow([(x0 + iw / 2, py + 110), (x0 + iw / 2, py + 92)], lw=1.5)


def draw_slide(path):
    c = Canvas(1800, 840)

    # ---------------- Zynq PS (ARM side)
    c.box(12, 12, 250, 816, "Zynq PS  (ARM)", kind="container", title_top=True, fs=14, dashed=True)
    c.box(28, 96, 218, 132, "ARM Cortex-A9", "runs our C driver", kind="ext", fs=14.5, sub_fs=11.5)
    c.box(28, 716, 218, 96, "DDR memory", "audio from 4 mics", kind="ext", fs=14.5, sub_fs=11.5)

    # ---------------- Zynq PL (FPGA fabric)
    c.box(276, 12, 1512, 816, "Zynq PL  (FPGA fabric)", kind="container", title_top=True, fs=14, dashed=True)
    c.box(292, 716, 150, 96, "AXI DMA", "standard IP", kind="ext", fs=14.5, sub_fs=11.5)
    c.box(500, 48, 1276, 766, "", kind="white", lw=1.4, z=2)
    c.text(1138, 66, "SIMD accelerator  —  our Verilog", fs=14, color=NAVY, bold=True)

    c.box(520, 96, 220, 132, "Control registers", "μ, B, L in\nτ21, τ31, τ41 out", kind="ours", fs=13.5,
          sub_fs=11.5)
    c.box(760, 88, 996, 148, "Control unit  —  one copy, shared by all PEs", kind="key", title_top=True, fs=13.5)
    subs = ["Instruction\nmemory", "Fetch +\nloop counter", "Decode", "Address\ngenerator"]
    for i, t in enumerate(subs):
        x = 776 + i * 244
        c.box(x, 136, 228, 80, t, kind="white", fs=13, radius=4)
        if i < 3:
            c.arrow([(x + 228, 176), (x + 244, 176)], lw=1.5)
    c.arrow([(740, 162), (760, 162)], lw=1.5)

    # broadcast bar
    c.rect(520, 256, 1236, 38, fc=KEY, ec=NAVY, lw=1.3)
    c.text(1138, 275, "every cycle the same instruction + address go to all 3 PEs   →   3 × 16 lanes = 48 MACs per "
           "instruction", fs=12.5, color=NAVY, bold=True)
    c.arrow([(1258, 236), (1258, 256)], lw=1.8)

    # three identical PEs
    pes = [("PE0", "Mic 2 vs Mic 1"), ("PE1", "Mic 3 vs Mic 1"), ("PE2", "Mic 4 vs Mic 1")]
    for i, (n, pair) in enumerate(pes):
        px = 520 + i * 421
        pe_column(c, px, 314, n, pair)
        c.arrow([(px + 197, 294), (px + 197, 314)], lw=1.8)
        c.arrow([(px + 197, 736), (px + 197, 712)], lw=1.8, color=GREY)

    # input writer + links
    c.box(520, 736, 1236, 56, "Input writer  —  audio samples → PE memories", kind="ours", fs=13, radius=4)
    c.arrow([(246, 764), (292, 764)], color=GREY)
    c.arrow([(442, 764), (520, 764)], "AXI4-\nStream", label_off=(0, -28), color=GREY, fs=10.5)
    c.arrow([(246, 140), (520, 140)], "AXI4-Lite:  settings in, τ out", both=True, label_off=(0, -14), fs=11.5)
    c.arrow([(520, 196), (246, 196)], "interrupt:  τ ready", color=ACCENT, label_off=(0, -14), fs=11.5,
            label_color=ACC_TXT)

    # legend
    for i, (kind, t) in enumerate([("ours", "our Verilog"), ("ext", "ARM side /\nstandard IP"),
                                   ("accent", "sliding-window\n(memory addressing)")]):
        c.box(36, 420 + i * 62, 26, 20, "", kind=kind, radius=3)
        c.text(72, 430 + i * 62, t, fs=11, ha="left", va="top" if "\n" in t else "center")
    c.save(path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    draw_slide(os.path.join(OUT, "slide_microarch.png"))
    draw_detail(os.path.join(OUT, "microarch.png"))
    print("ok")
