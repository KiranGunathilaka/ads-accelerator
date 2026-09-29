"""
ISA content for the explainer pages: where every instruction came from and why it is there.

Used by build_explainers.py:
  - isa_body()        -> body of isa.html (format, opcodes, addressing, fixed-point shifts, microprogram, timeline)
  - origins_body()    -> body of isa-origins.html (lineage, 32-slot map, one card per instruction, parameters)
  - index_section()   -> "Where the ISA came from" block for the briefing page
  - extend_qa(QA)     -> adds provenance / justification questions to the Q&A list
  - ORIGINS_CSS       -> extra styles (slot map, instruction cards, timelines)

Usage counts (static / executed per block) come from running the microprogram in simulation_py/isa_sim.py
(B = 128, L = 64). v1.0 facts come from ISA_Design.md as first committed (git 56b9d67).
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

ORIGINS_CSS = """
:root{--k-kept:#1b2f6b;--k-kept-bg:#eef1f8;--k-ren:#2459b8;--k-ren-bg:#e7effc;--k-rew:#8a5a00;--k-rew-bg:#fbf1db;
  --k-new:#c9501f;--k-new-bg:#fcece4}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--k-kept:#9db4f0;--k-kept-bg:#1a2238;
  --k-ren:#86b1ff;--k-ren-bg:#15223a;--k-rew:#f0c060;--k-rew-bg:#2b2413;--k-new:#ff8c5a;--k-new-bg:#2e1f19}}
:root[data-theme="dark"]{--k-kept:#9db4f0;--k-kept-bg:#1a2238;--k-ren:#86b1ff;--k-ren-bg:#15223a;--k-rew:#f0c060;
  --k-rew-bg:#2b2413;--k-new:#ff8c5a;--k-new-bg:#2e1f19}
.grid32{display:grid;grid-template-columns:118px repeat(8,minmax(0,1fr));gap:6px;min-width:840px}
.grid32 .gh{display:flex;flex-direction:column;justify-content:center;font-size:12.5px;color:var(--ink2);line-height:1.3}
.grid32 .gh b{font-family:"JetBrains Mono",ui-monospace,monospace;color:var(--navy);font-size:13px}
a.slot{display:block;border:1.5px solid var(--line);border-radius:6px;padding:6px 3px;text-align:center;
  background:var(--surface);color:var(--ink);text-decoration:none;line-height:1.25}
a.slot:hover{outline:2px solid var(--link);outline-offset:1px}
a.slot b{display:block;font-family:"JetBrains Mono",ui-monospace,monospace;font-size:12.5px}
a.slot i{display:block;font-style:normal;font-size:10.5px;color:var(--ink2)}
a.slot span{display:block;font-size:10.5px;color:var(--ink2);font-variant-numeric:tabular-nums}
a.slot.unused{border-style:dashed}
a.slot.unused span{color:var(--muted)}
.st-kept{border-color:var(--k-kept)!important;background:var(--k-kept-bg)!important}
.st-ren{border-color:var(--k-ren)!important;background:var(--k-ren-bg)!important}
.st-rew{border-color:var(--k-rew)!important;background:var(--k-rew-bg)!important}
.st-new{border-color:var(--k-new)!important;background:var(--k-new-bg)!important}
a.slot.st-kept b{color:var(--k-kept)} a.slot.st-ren b{color:var(--k-ren)}
a.slot.st-rew b{color:var(--k-rew)} a.slot.st-new b{color:var(--k-new)}
.legend{display:flex;flex-wrap:wrap;gap:8px 18px;font-size:13.5px;color:var(--ink2);margin:12px 0 4px}
.legend span{display:inline-flex;align-items:center;gap:6px}
.legend i{display:inline-block;width:16px;height:12px;border:1.5px solid;border-radius:3px}
.card{border:1px solid var(--line);border-radius:10px;background:var(--surface);margin:16px 0;scroll-margin-top:16px}
.card>header{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 10px;padding:12px 16px;border-bottom:1px solid var(--line)}
.card h3{margin:0;font-family:"JetBrains Mono",ui-monospace,monospace;font-size:17px;font-weight:600;color:var(--navy)}
.card .code{font-family:"JetBrains Mono",ui-monospace,monospace;font-size:13px;color:var(--muted)}
.card .plain{padding:10px 16px 0;margin:0}
.card .op{padding:4px 16px 0;margin:0;font-family:"JetBrains Mono",ui-monospace,monospace;font-size:13px;
  color:var(--ink2);max-width:none}
td .formal{display:block;font-family:"JetBrains Mono",ui-monospace,monospace;font-size:12px;color:var(--muted);
  margin-top:2px}
.card dl{display:grid;grid-template-columns:140px minmax(0,1fr);gap:8px 18px;padding:12px 16px 14px;margin:0}
.card dt{font-weight:600;color:var(--ink2);font-size:13.5px}
.card dd{margin:0;max-width:70ch}
.tag{display:inline-block;font-size:12px;border-radius:999px;padding:1px 9px;border:1px solid;color:var(--ink)}
.use{display:inline-block;font-size:12px;border-radius:999px;padding:1px 9px;border:1px solid var(--line);color:var(--ink2)}
.use.core{color:var(--good);border-color:var(--good)}
.use.weak{border-style:dashed;color:var(--muted)}
.lineage{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:16px 0}
.lineage>div{border:1px solid var(--line);border-radius:8px;background:var(--surface);padding:12px 14px}
.lineage h3{margin:0 0 6px;font-size:16px}
.lineage p{font-size:14.5px;margin:.3em 0}
.lineage ul{font-size:14.5px;margin:.3em 0;padding-left:18px}
table.tl td.stall{color:var(--muted);font-style:italic}
table.tl td:first-child{width:70px}
@media (max-width:760px){.lineage{grid-template-columns:minmax(0,1fr)}.card dl{grid-template-columns:minmax(0,1fr);gap:2px}
  .card dt{margin-top:8px}}
"""

GROUPS = [("00", "Vector arithmetic"), ("01", "Memory / AGU"), ("10", "Scalar / loop"), ("11", "Control / result")]

STATUS = {  # key -> (css class, short label, long label)
    "kept": ("st-kept", "v1.0", "Kept from v1.0"),
    "ren": ("st-ren", "renamed", "Renamed from v1.0"),
    "rew": ("st-rew", "reworked", "Reworked from v1.0"),
    "new": ("st-new", "new", "New in v1.1"),
}
USE = {
    "core": "runs every block",
    "nlms": "for block-NLMS (not run yet)",
    "util": "utility / debug (not run)",
    "weak": "weak case (not run)",
}


def _n(v):
    return f"{v:,}".replace(",", " ")


def g(key, text):
    """Link a term to its definition on the Basics & glossary page (same markup as build_explainers.g)."""
    return f'<a class="term" href="basics.html#g-{key}">{text}</a>'


PLAIN = {
    "VMAC": "multiply 16 pairs of numbers and add each product to that lane's running sum",
    "VSUB": "subtract two vectors, lane by lane", "VADD": "add two vectors, lane by lane",
    "VSCALE": "multiply every lane by one scalar (used for μ)", "VABS": "absolute value of every lane",
    "VMOV": "copy a vector, or fill all 16 lanes with one scalar",
    "VREDUCE": "add the 16 running sums together into one number",
    "VMUL": "multiply two vectors, lane by lane",
    "VLD": "load 16 words from memory into a vector register", "VST": "store a vector register to memory",
    "AGU_SET": "point an address register at a place in memory", "AGU_ADD": "move an address register along",
    "WLD": "load 16 samples into one chunk of the window register",
    "WSLIDE": "shift the window by one sample and read the one new sample",
    "SST": "store one scalar to memory", "SLD": "load one word into a scalar register",
    "SMUL": "multiply two scalars", "SADD": "add two scalars (plus a constant)",
    "SSUB": "subtract two scalars (plus a constant)",
    "SDIV": "divide two scalars (slow: 34 cycles, once per block)", "SMOV": "copy a scalar",
    "SIMM": "put a constant into a scalar register", "CSR_RD": "read a setting the ARM wrote (e.g. μ)",
    "LOOP": "repeat the next few instructions a given number of times",
    "PKMAX": "compare 16 weights with the largest seen so far; remember the biggest and its position",
    "PKOUT": "turn the peak position into τ and write it where the ARM can read it",
    "SYNC": "wait until a full new block of samples has arrived", "PKCLR": "reset the peak search",
    "IRQ": "tell the ARM the results are ready", "NOP": "do nothing for one cycle",
    "HALT": "stop; restart automatically when the next block arrives",
    "CSR_WR": "write a value where the ARM can read it",
}


# One entry per opcode, in opcode order. s / d = count in the 78-instruction program / executions per block.
INSTR = [
    # ------------------------------------------------------------------ 00 vector arithmetic
    dict(m="VMAC", code="00000", st="kept", was="VMAC", s=12, d=1024, use="core",
         op="VACC[i] = (.C ? 0 : VACC[i]) + SRC1[i] × (SRC2[i] &gt;&gt; sh)",
         why="Phases 1 and 3 are two matrix–vector products: 16 384 of the 16 576 operations per filter per block. "
             "One VMAC does 16 multiply-adds per PE, 48 across the cluster. It is 1 024 of the 1 709 instructions "
             "executed per block (60 %).",
         form="Three changes from v1.0, which did <code>V_DST += SRC1 × SRC2</code>. (1) The accumulator is VACC, "
              "the 48-bit P register inside each DSP48E1, not a 32-bit vector register. A product is up to 41 bits "
              "and a row adds 64 of them (47 bits), so a 32-bit register would overflow. Accumulating inside P also "
              "avoids a register-file write every cycle. (2) The <code>.C</code> flag (IMM[0]) starts a new sum by "
              "selecting DSP OPMODE Z = 0. It replaces v1.0's per-row <code>SACC_CLR V2</code>, a scalar "
              "instruction that v1.0 applied to a vector register. (3) <code>sh</code> (IMM[4:1]) shifts SRC2 right "
              "before the multiply so a 32-bit Q2.30 weight fits the 25-bit A port (sh = 7). SRC1 can also name a "
              "window chunk W0–W7 (operand codes 8–15), so the sliding window feeds the multipliers without being "
              "copied into vector registers first.",
         prec="The multiply-accumulate is the defining DSP instruction: MMX <code>PMADDWD</code> (lecture 29a, MMX "
              "slides), NEON <code>VMLA</code>/<code>VMLAL</code>, RISC-V V <code>vmacc</code>. TI C55x (40-bit "
              "AC0–AC3) and ADI Blackfin (40-bit A0/A1) also have wide dedicated accumulators.",
         hw="16 DSP48E1 per PE. Window sample → B port (18 bit); weight or error → A port (25 bit); P (48 bit) = VACC. "
            "Consecutive VMACs accumulate through the DSP's internal P feedback, so they issue every cycle.",
         without="Each chunk would need VMUL + VADD: twice the instructions in the two hot loops, with sums held in "
                 "32-bit registers that overflow."),
    dict(m="VSUB", code="00001", st="ren", was="VSUB_V", s=1, d=8, use="core",
         op="Vd[i] = sat(Va[i] − Vb[i])   (IMM[0]: clamp to 16 bits, else 32)",
         why="Phase 2 computes the error e = d_delayed − y, 16 samples at a time: 8 per block.",
         form="Renamed from VSUB_V. All four element-wise vector ops lost the <code>_V</code> suffix, because every "
              "vector op works element by element unless its name says otherwise (VREDUCE, VSCALE). Saturation is "
              "new. When the filter is far off, d − y can exceed the Q1.15 range. Clamping keeps e at the right "
              "sign; wrapping would flip it and push the weights the wrong way. The fixed-point model clamps the "
              "same way, which is part of why the ISA run matches it bit for bit.",
         prec="MMX <code>PSUBSW</code>, NEON <code>VQSUB</code>, RISC-V V <code>vssub</code> (all saturating).",
         hw="Vector ALU: 16 × 32-bit subtract with clamp.",
         without="VADD plus a negate instruction. Nothing cheaper forms e."),
    dict(m="VADD", code="00010", st="ren", was="VADD_V", s=1, d=4, use="core",
         op="Vd[i] = sat(Va[i] + Vb[i])",
         why="Phase 4 applies the update w_rev += Δw: 4 per block (64 weights / 16 lanes).",
         form="Renamed from VADD_V. It uses 32-bit saturation, so a weight that grows past ±2 in Q2.30 stops at the "
              "limit instead of wrapping to the opposite sign.",
         prec="MMX <code>PADDSW</code>, NEON <code>VQADD</code>, RISC-V V <code>vsadd</code>.",
         hw="Same vector ALU as VSUB.",
         without="The weight update could not be applied."),
    dict(m="VSCALE", code="00011", st="kept", was="VSCALE", s=1, d=4, use="core",
         op="Vd[i] = sat(((Va[i] &gt;&gt; pre) × Ss) &gt;&gt; post)",
         why="Phase 4 computes Δw = μ · g, with the scalar μ sent to all 16 lanes: 4 per block.",
         form="Kept from v1.0 (<code>V_DST = SRC1 × S_src</code>). v1.1 adds two shifts because the operands are "
              "fixed-point. pre = 7 turns the Q2.30 gradient into 25 bits for the A port. The product with Q1.15 μ "
              "has 38 fractional bits, and post = 8 brings it back to Q2.30. Separate instructions would need three "
              "steps (shift, multiply, shift). VSCALE reads the scalar register directly, so no broadcast (splat) is "
              "needed first.",
         prec="NEON multiply by scalar (<code>VMUL</code> by element) and <code>VQDMULH</code> (Q15 fractional "
              "multiply); RISC-V V <code>vmul.vx</code>.",
         hw="Reuses the 16 DSP48E1 lanes (μ on the B port); the product goes back to the vector register file.",
         without="VMOV splat, VMUL and shifts: 3–4 instructions per chunk instead of 1."),
    dict(m="VABS", code="00100", st="kept", was="VABS", s=0, d=0, use="weak",
         op="Vd[i] = |Va[i]|",
         why="The v1.1 program never runs it. In v1.0 it fed the peak search (<code>VABS V7, V6</code>, then "
             "<code>PKMAX V7</code>). In v1.1, PKMAX takes the absolute value inside its comparator tree, which "
             "saves 4 instructions and a register per block.",
         form="Unchanged from v1.0.",
         prec="NEON <code>VABS</code>/<code>VQABS</code>, SSSE3 <code>PABSW</code>.",
         hw="16 negate-and-select circuits in the vector ALU (small).",
         without="Nothing changes in the current program. The case for it is weak: a possible use is a mean |e| "
                 "convergence monitor. It is the first candidate if a slot is needed for something new."),
    dict(m="VMOV", code="00101", st="ren", was="VMOV_V", s=0, d=0, use="util",
         op="Vd = Va,   or   Vd[i] = Ss for every lane (splat) if IMM[0]",
         why="Not used per block. It is the only instruction that puts a scalar into every lane, for example an "
             "all-zero vector (splat of the ZERO code) to clear w_rev in a reset program. It is also the register "
             "copy that a software-pipelined loop would need.",
         form="Renamed from VMOV_V. The splat mode replaces v1.0's <code>VLD_S</code> (load one word and "
              "broadcast), which v1.1 does as SLD + VMOV. That freed a memory-group slot for the new window and "
              "scalar memory instructions.",
         prec="NEON <code>VMOV</code>/<code>VDUP</code>, RISC-V V <code>vmv.v.v</code>/<code>vmv.v.x</code>.",
         hw="A multiplexer in front of the vector register write port.",
         without="No way to build a constant vector. The per-block program would not change."),
    dict(m="VREDUCE", code="00110", st="kept", was="VREDUCE", s=2, d=192, use="core",
         op="Sd = sat((Σ_i VACC[i] + round) &gt;&gt; sh)",
         why="Each output y[i] (128 per block) and each gradient g[k] (64 per block) ends as 16 lane partial sums "
             "that must become one number: 192 per block.",
         form="Kept from v1.0 (<code>S_DST = Σ V_SRC[i]</code>). v1.1 sums VACC directly instead of a V register, so "
              "the 48-bit partial sums never pass through 32-bit registers. It also rescales in the same "
              "instruction: IMM[4:0] = shift, IMM[5] = round, IMM[6] = clamp to 16 bits. Phase 1 uses sh = 23 "
              "(38 fractional bits → 15, rounded, clamped: y in Q1.15). Phase 3 uses sh = 7 = log2 B, which turns "
              "the sum into the mean. That shift is the ÷B in μ/B, so the division costs nothing. The result is "
              "ready 5 cycles after issue (4 tree stages + round/clamp).",
         prec="RISC-V V <code>vredsum.vs</code>, AArch64 NEON <code>ADDV</code>. x86 SSE needs several "
              "<code>PHADD</code>/shuffle steps for the same thing.",
         hw="15 adders in 4 pipelined stages, about 52 bits wide (16 inputs of 48 bits), then a shifter, rounder "
            "and saturator.",
         without="15 scalar additions per output, more instructions per row than the whole 7-instruction loop."),
    dict(m="VMUL", code="00111", st="ren", was="VMUL_V", s=0, d=0, use="weak",
         op="Vd[i] = sat((Va[i] × Vb[i]) &gt;&gt; sh)",
         why="Not used. Block-LMS never needs an element-wise product kept in a register: every product either "
             "feeds a sum (VMAC) or multiplies by a scalar (VSCALE). The NLMS power Σx² is also a VMAC.",
         form="Renamed from VMUL_V; the shift was added for fixed point.",
         prec="NEON <code>VMUL</code>, RISC-V V <code>vmul.vv</code>, SSE <code>PMULLW</code>.",
         hw="Almost nothing extra: the path from the DSPs back into the vector registers already exists for "
            "VSCALE. VMUL feeds a vector instead of the broadcast scalar.",
         without="Nothing changes for this algorithm. It stays as a general-purpose operation that costs only "
                 "decode."),
    # ------------------------------------------------------------------ 01 memory / AGU
    dict(m="VLD", code="01000", st="kept", was="VLD", s=17, d=40, use="core",
         op="Vd = M[An … An+15];  An += sext(imm)      (An must be 16-aligned)",
         why="Loads w_rev (Phases 1, 4, 5), e (Phase 3), d and y (Phase 2) and g (Phase 4) into registers: 40 per "
             "block.",
         form="Kept from v1.0 with two fixes. (1) It names an address register An. v1.0's VLD had no pointer "
              "field, yet its listings used seven pointers (x_ptr, w_ptr, d_ptr, …). Three AGU_SETs in a row "
              "would have overwritten each other. (2) Post-increment by IMM12 replaces v1.0's separate "
              "<code>AGU_INC</code> after every access; v1.0's Phase 2 loop spent 3 of its 8 instructions on "
              "AGU_INC. Vector accesses must be 16-aligned, so a load is one row across the 16 banks in one cycle "
              "and needs no rotator.",
         prec="Auto-increment addressing <code>LD R4 = MEM[R1++]</code> (lecture 29a, scalar code example); NEON "
              "<code>VLD1 {…}, [Rn]!</code>; RISC-V V <code>vle32.v</code> (unit stride). The 16 word-interleaved "
              "banks are the lecture's vector memory system (CRAY-1: 16 banks).",
         hw="16 BRAM18 read ports into the vector register file; result ready after 2 cycles.",
         without="No way to get data into the vector registers."),
    dict(m="VST", code="01001", st="kept", was="VST", s=2, d=12, use="core",
         op="M[An … An+15] = Vs;  An += sext(imm)",
         why="Stores e (Phase 2, 8 times) and the updated w_rev (Phase 4, 4 times): 12 per block.",
         form="Same fixes as VLD: a named pointer, post-increment, aligned only.",
         prec="As for VLD.",
         hw="16 BRAM18 write ports; the PE has priority over the input writer on these ports.",
         without="Results could not go back to memory."),
    dict(m="AGU_SET", code="01010", st="kept", was="AGU_SET", s=13, d=13, use="core",
         op="An = (Am or ZERO) + imm;  circular flag = SRC2[0]",
         why="Points an address register at a region at the start of each phase: 13 per block.",
         form="Kept by name. v1.0's AGU_SET loaded its one implicit pointer with IMM12. v1.1 names the destination "
              "An and adds a base register Am and a circular flag. The base register is what makes the rings work: "
              "<code>AGU_SET A0, A7, X_RING, circ=1</code> points A0 at x_full[1] of the current block (A7 holds "
              "the block base) with no scalar arithmetic. The flag makes later post-increments wrap inside the "
              "512-word ring.",
         prec="The CRAY-1 has 8 address registers (lecture 29a, CRAY-1 slide). The TI C54x has AR0–AR7, with BK "
              "setting the circular-buffer size. ADI SHARC/Blackfin address generators have index, base and "
              "length registers.",
         hw="Shared AGU: 8 × 13-bit registers, 8 circular flags, one adder.",
         without="Pointers could only be constants. The block position in the ring would have to be computed in "
                 "scalar registers and then moved into the AGU."),
    dict(m="AGU_ADD", code="01011", st="rew", was="AGU_INC", s=1, d=1, use="core",
         op="An += sext(imm)   (wraps inside the ring if An is circular)",
         why="Moves the block base A7 on by B at the end of every block: 1 per block.",
         form="v1.0's AGU_INC added a fixed 16 to its single pointer after every access. v1.1 moves that per-access "
              "case into post-increment and keeps one general add for everything else. AGU_SET cannot do this job "
              "because it does not wrap: A7 would leave the X ring and point into the D ring after four blocks.",
         prec="The address-generator 'modify' step (I += M, with circular wrap) on ADI SHARC/Blackfin; TI C54x "
              "<code>MAR</code>.",
         hw="The same adder as post-increment.",
         without="A7 could not advance modulo 512."),
    dict(m="WLD", code="01100", st="new", was="", s=12, d=12, use="core",
         op="window chunk Wc = low 16 bits of M[An … An+15];  An += imm",
         why="Fills the sliding-window register at the start of Phase 1 (4 chunks) and Phase 3 (8 chunks): 12 per "
             "block.",
         form="New in v1.1, together with WSLIDE. v1.0 loaded each row of X with four VLDs starting at x_ptr + i: "
              "an arbitrary word offset. Sixteen single-port banks can deliver an aligned row in one cycle, but not "
              "an unaligned one, unless every PE gets a rotator or crossbar. WLD loads only aligned chunks, once "
              "per phase. It keeps the low 16 bits because samples are Q1.15, which halves the window's "
              "flip-flops.",
         prec="Loading a delay line (see WSLIDE).",
         hw="The same bank read as VLD, written into window chunk c instead of a vector register.",
         without="The window could not be filled."),
    dict(m="WSLIDE", code="01101", st="rew", was="AGU_SLIDE", s=2, d=192, use="core",
         op="WIN[0 … n−2] = WIN[1 … n−1];  WIN[n−1] = M[An];  An += 1      (n = len)",
         why="Row i+1 of X is row i moved by one sample plus one new sample, and so is column k+1. WSLIDE makes that "
             "step with a single one-word read: 128 times in Phase 1, 64 times in Phase 3.",
         form="Replaces v1.0's AGU_SLIDE, which only moved a pointer by one sample, so every row still needed four "
              "unaligned 16-wide loads. Moving the data instead of the pointer keeps every memory access either "
              "aligned or a single word. <code>len</code> (IMM) sets the window length: 64 for rows (L), 128 for "
              "columns (B). v1.0's AGU_COL is gone because, with w stored reversed, columns slide the same way as "
              "rows.",
         prec="RISC-V V <code>vslide1down.vx</code> does exactly this (every element moves down one place and a "
              "scalar enters at the top); here the new value comes straight from memory. DSPs keep FIR delay lines "
              "the same way, e.g. TI C54x <code>MACD</code>, a MAC that also shifts the delay line. NEON "
              "<code>VEXT</code> extracts a window from two registers.",
         hw="128 × 16-bit shift register (2 048 flip-flops), one single-bank read, and an 8:1 chunk multiplexer in "
            "front of the DSP B ports.",
         without="4 (Phase 1) or 8 (Phase 3) unaligned loads per row or column. That needs a 16 × 16 word rotator "
                 "per PE, the most LUT-hungry structure a PE could have."),
    dict(m="SST", code="01110", st="new", was="", s=2, d=192, use="core",
         op="M[An] = Ss;  An += imm",
         why="Writes each y[i] and g[k] as soon as VREDUCE produces it: 192 per block.",
         form="New in v1.1. v1.0's listings used <code>VST_S</code> for this, but VST_S was not in the opcode "
              "table. SST uses one bank's write enable, so it writes one word without touching the other 15 "
              "banks.",
         prec="The scalar store of any load/store ISA. The CRAY-1 pairs its vector registers with scalar registers "
              "the same way.",
         hw="Bank select from address bits [3:0] plus that bank's write enable.",
         without="Results would have to be packed into a vector register first (a lane-insert instruction) and "
                 "stored 16 at a time."),
    dict(m="SLD", code="01111", st="new", was="", s=0, d=0, use="util",
         op="Sd = M[An];  An += imm",
         why="Not used per block. It is the load partner of SST, and SLD + VMOV splat replaces v1.0's VLD_S (load "
             "one word and broadcast it). Uses: reading a constant kept in memory, or reading the weights around the "
             "peak if sub-sample interpolation ever moves onto the accelerator.",
         form="Same addressing as SST.",
         prec="The scalar load of any ISA.",
         hw="Almost nothing extra: WSLIDE already needs a one-word read path (16:1 bank multiplexer); SLD sends "
            "the word to a scalar register instead of the window.",
         without="The per-block program would not change."),
    # ------------------------------------------------------------------ 10 scalar / loop
    dict(m="SMUL", code="10000", st="kept", was="SMUL", s=0, d=0, use="weak",
         op="Sd = Sa × Sb",
         why="Not used. v1.0 listed it for computing μ/B, which v1.1 does with the VREDUCE shift. The NLMS path "
             "doesn't need it either: with L = 64 and a 128-sample power window, L·Pₓ = Σx² / 2, which is a shift.",
         form="Unchanged.",
         prec="RISC-V M <code>mul</code>.",
         hw="One DSP48E1 per PE: 3 of the 51 DSPs in the resource estimate.",
         without="Removing it saves 3 DSP48E1 (51 → 48). This is the only unused instruction with a real hardware "
                 "cost, so decide on it before writing RTL."),
    dict(m="SADD", code="10001", st="kept", was="SADD", s=0, d=0, use="nlms",
         op="Sd = Sa + Sb + sext(imm)",
         why="Not used by the μ/B program. Block-NLMS needs it once per block to add ε to the power "
             "(L·Pₓ + ε) before dividing. It is also the general scalar add.",
         form="v1.1 adds the immediate, so a constant can be added without a separate SIMM. With the ZERO operand "
              "it also covers SMOV (<code>Sd = Sa + ZERO</code>) and SIMM (<code>Sd = ZERO + ZERO + imm</code>).",
         prec="RISC-V <code>add</code> / <code>addi</code>.",
         hw="One 32-bit adder per PE.",
         without="NLMS could not add ε."),
    dict(m="SSUB", code="10010", st="kept", was="SSUB", s=0, d=0, use="weak",
         op="Sd = Sa − Sb + sext(imm)",
         why="Not used. v1.0 used it for τ = center_tap − peak_idx. PKOUT now does that in one step (v1.0 actually "
             "subtracted twice).",
         form="Unchanged apart from the immediate.",
         prec="RISC-V <code>sub</code>.",
         hw="Shares SADD's adder (one inverted input).",
         without="Nothing changes. It is kept for completeness and costs only decode."),
    dict(m="SDIV", code="10011", st="kept", was="SDIV", s=0, d=0, use="nlms",
         op="Sd = (Sa &lt;&lt; imm) / Sb      (iterative, 34 cycles)",
         why="Not used by the μ/B program. It is the NLMS step size μ_eff = μ / (L·Pₓ + ε), computed once per block. "
             "In the tracking study block-NLMS was the best update (88.0 % within ±1 sample at μ = 0.64, against "
             "85.6 % for μ/B at μ = 0.5), and its step does not depend on how loud the input is.",
         form="v1.0 used SDIV to compute μ/B. That is now the VREDUCE shift, so SDIV's only job is NLMS. The "
              "pre-shift (IMM) keeps precision in the fixed-point quotient. It is iterative because one 34-cycle "
              "division per block is about 0.01 % of the 266 700-cycle block period, and a fast divider would cost "
              "DSPs or many LUTs.",
         prec="RISC-V M <code>div</code>, which is multi-cycle in most small cores.",
         hw="Shift-and-subtract divider in LUTs, one per PE.",
         without="NLMS would have to move to the ARM: it could compute μ_eff from the audio it sends and write it "
                 "to the MU CSR every block. That is a valid fallback."),
    dict(m="SMOV", code="10100", st="kept", was="SMOV", s=0, d=0, use="weak",
         op="Sd = Sa",
         why="Not used. It does the same as <code>SADD Sd, Sa, ZERO</code>.",
         form="Unchanged. Redundant, but it makes assembly easier to read.",
         prec="RISC-V <code>mv</code> is only a pseudo-instruction for <code>addi rd, rs, 0</code>, the same "
              "situation.",
         hw="Decode only.",
         without="Nothing. It could become an assembler alias and free its slot."),
    dict(m="SIMM", code="10101", st="kept", was="SIMM", s=0, d=0, use="weak",
         op="Sd = sext(imm)",
         why="Not used. It does the same as <code>SADD Sd, ZERO, ZERO, imm</code>. v1.0 needed it to clear the "
             "scalar accumulator and the peak registers; VMAC.C and PKCLR do those jobs now.",
         form="Unchanged.",
         prec="RISC-V <code>li</code> (a pseudo-instruction built from <code>addi</code>/<code>lui</code>).",
         hw="Decode only.",
         without="Nothing. It could become an assembler alias."),
    dict(m="CSR_RD", code="10110", st="rew", was="VLD_CSR", s=1, d=1, use="core",
         op="Sd = CSR[imm]",
         why="Reads μ into S0 at the start of every block. Because μ is read every block, the ARM can change it while "
             "the cluster runs, without reloading the program. The CSRs are the only way ARM settings reach the "
             "datapath; the ARM cannot write the PE memories.",
         form="v1.0's VLD_CSR sat in the vector-memory group although it reads no memory, so v1.1 moved it to the "
              "scalar group, where its result goes. The CSR index now sits in IMM12[3:0]. v1.0 put it in a register "
              "field behind a 2-bit type tag, and the CSR tag overlapped index bit 3, so only 8 of the 16 CSRs "
              "could be reached.",
         prec="RISC-V Zicsr <code>csrr</code> (<code>csrrs rd, csr, x0</code>).",
         hw="16:1 multiplexer from the CSR bank to the scalar write port.",
         without="μ would have to be a constant inside the program."),
    dict(m="LOOP", code="10111", st="rew", was="LOOP_SET", s=5, d=5, use="core",
         op="repeat the next len instructions count times   (len = DST field, 1–31; count = IMM12, up to 4 095)",
         why="All control flow in Block-LMS is counted loops. Five LOOPs turn the 78 stored instructions into the "
             "1 709 executed per block. Fully unrolled, the program would be about 1 700 instructions, more than "
             "three times the 512-word instruction memory.",
         form="v1.0 had <code>LOOP_SET</code> to load a counter, and every listing ended its loops with "
              "<code>LOOP_DEC → label</code>. LOOP_DEC was not defined, and all 32 slots were already taken. v1.1 "
              "uses one instruction that records start, end and count. The fetch unit compares the PC with the "
              "loop end and jumps back in the same cycle, so iterations cost nothing. A decrement-and-branch "
              "would add at least one instruction to each of the 208 loop iterations per block, plus any branch "
              "bubble. The loop stack is 2 deep. The current program needs only 1 level, because the inner chunk "
              "loops are unrolled; the second level is for B or L above 128, where they can't be.",
         prec="Zero-overhead loops are standard in DSPs: ADI Blackfin <code>LSETUP</code> with two loop units "
              "(LC0/LC1), Qualcomm Hexagon <code>loop0</code>/<code>loop1</code>, ADI SHARC "
              "<code>DO … UNTIL</code>, TI C54x <code>RPTB</code>. The lecture's scalar example uses "
              "<code>DECBNZ</code> (decrement and branch) and lists 'fewer branches' as a vector-processor "
              "advantage.",
         hw="Loop stack of 2 × {start, end, count} and one comparator on the PC.",
         without="Either an instruction memory 4× larger, or a branch instruction plus its penalty."),
    # ------------------------------------------------------------------ 11 control / result
    dict(m="PKMAX", code="11000", st="kept", was="PKMAX", s=1, d=4, use="core",
         op="compare |Va[i]| over 16 lanes in a tree, then against the running max; keep the winner's index",
         why="τ comes from argmax |w_rev| over 64 weights: 4 per block.",
         form="Kept from v1.0 with two changes. It takes the absolute value itself (v1.0 needed VABS first). It also "
              "keeps its own index counter (+16 per call), so software does not track positions. Ties: inside "
              "the tree the lower lane wins, and the running compare is a strict >, so the earliest index wins, "
              "exactly like <code>numpy.argmax</code>. That is why τ matches the golden model bit for bit.",
         prec="SSE4.1 <code>PHMINPOSUW</code> returns the minimum of 8 words and its position; ADI Blackfin "
              "<code>SEARCH</code> finds a maximum or minimum and where it is; RISC-V V <code>vredmax</code> "
              "returns only the value.",
         hw="16-input comparator tree (4 stages) plus a running max/index register per PE; 5-cycle latency.",
         without="64 single-word loads per PE, each with a compare and a conditional update. This ISA has no "
                 "branches, so that would also need a conditional-select instruction."),
    dict(m="PKOUT", code="11001", st="ren", was="PKIDX_OUT", s=1, d=1, use="core",
         op="CSR[TAU_pe] = peak_idx − imm",
         why="Writes the finished τ into this PE's result register (TAU21, TAU31 or TAU41): once per block.",
         form="Renamed from PKIDX_OUT. It now subtracts an immediate: with reversed weights, τ = k* − (L−1−L/2), so "
              "imm = 31. v1.0 computed center_tap − index twice (SSUB, then PKIDX_OUT). PKOUT is also the only "
              "instruction in which each PE writes its own CSR. CSR_WR writes one shared CSR, so it could not "
              "return three different τ values.",
         prec="Specific to this application; there is no general-purpose equivalent.",
         hw="A subtractor and a per-PE CSR write.",
         without="The three τ values could not reach the ARM."),
    dict(m="SYNC", code="11010", st="kept", was="SYNC", s=1, d=1, use="core",
         op="SYNC 0: memory fence  ·  SYNC 1: stall until the input writer has a full new block",
         why="SYNC 1 at PC 0 makes each pass wait for its block of audio: 1 per block.",
         form="v1.0 defined SYNC only as a pipeline fence. v1.1 adds mode 1 (wait until SAMPLES_IN ≥ "
              "(blocks_done + 1)·B), which lets the cluster run by itself: HALT (with AUTO) → PC 0 → SYNC 1 waits "
              "for the next block. This program doesn't need mode 0: single issue plus the scoreboard already keeps "
              "memory accesses in order.",
         prec="Mode 0: RISC-V <code>FENCE</code>, ARM <code>DMB</code>. Mode 1 is like ARM <code>WFE</code> (wait "
              "for event), where the event is 'block ready'.",
         hw="A comparator between SAMPLES_IN and the block counter that holds issue.",
         without="The ARM would have to write START for every block (375 times a second), and the cluster would "
                 "depend on the ARM's interrupt latency."),
    dict(m="PKCLR", code="11011", st="new", was="", s=1, d=1, use="core",
         op="peak max = −1,  index = 0,  counter = 0",
         why="Resets the peak detector before each block's search.",
         form="New, in the slot of v1.0's PHASE_END. v1.0 reset 'peak_val' and 'peak_idx' with "
              "<code>SIMM S2, 0</code> and <code>SIMM S3, 0</code>. But PKMAX keeps its running max inside the peak "
              "detector, not in S2/S3, so those two instructions reset nothing that PKMAX uses. The max starts at "
              "−1 so the first compare always wins, even when every weight is 0.",
         prec="Specific to this application (the peak detector is ours).",
         hw="Synchronous reset of three registers.",
         without="The previous block's peak would carry over into the next search."),
    dict(m="IRQ", code="11100", st="ren", was="IRQ_FIRE", s=1, d=1, use="core",
         op="STATUS.DONE = 1;  raise IRQ_F2P if CTRL.IRQ_EN",
         why="Tells the ARM that TAU21/31/41 are ready: once per block.",
         form="Renamed from IRQ_FIRE. The way it is cleared changed. v1.0 cleared it with CTRL.RESET, but in v1.1 a "
              "reset also clears the ring position (A7) and the sample counter. The ARM now clears the interrupt by "
              "writing 1 to STATUS.DONE, which touches nothing else.",
         prec="Write-1-to-clear status bits are the usual pattern in AXI peripherals, including the Xilinx AXI DMA "
              "status register.",
         hw="One flag and a level interrupt output to the Zynq's IRQ_F2P.",
         without="The ARM would have to poll STATUS."),
    dict(m="NOP", code="11101", st="kept", was="NOP", s=0, d=0, use="weak",
         op="no operation",
         why="Not used. The scoreboard inserts stall cycles automatically, so the program never needs NOPs to wait "
             "for a result.",
         form="Unchanged. It costs nothing, and it gives a harmless word for overwriting an instruction when "
              "patching the instruction memory by hand.",
         prec="Every ISA has one. In statically scheduled designs (no hardware interlocks) NOPs fill latency "
              "slots; that is the design we did not choose.",
         hw="Decode only.",
         without="Nothing."),
    dict(m="HALT", code="11110", st="kept", was="HALT", s=1, d=1, use="core",
         op="PC ← 0; wait for CTRL.START, or restart at once if CTRL.AUTO",
         why="Ends each block's pass: 1 per block.",
         form="Kept from v1.0 ('await next DMA/START'). v1.1 adds the AUTO restart. With SYNC 1 at PC 0, the "
              "cluster then processes block after block without any action from the ARM.",
         prec="x86 <code>HLT</code>; RISC-V <code>WFI</code> plays a similar role.",
         hw="Sequencer state.",
         without="The program would have no defined end."),
    dict(m="CSR_WR", code="11111", st="kept", was="CSR_WR", s=0, d=0, use="util",
         op="CSR[imm] = Ss",
         why="Not used per block. It lets the program report a value to the ARM. That covers the debug purpose of "
             "v1.0's PHASE_END (write the phase number). Later it could report signal power, so the ARM knows when "
             "to hold the estimate (ISA_Design.md §14).",
         form="Kept from v1.0. The CSR index moved into IMM12, the same fix as CSR_RD. It writes one shared CSR (the "
              "simulator takes PE0's value).",
         prec="RISC-V Zicsr <code>csrw</code>.",
         hw="A write port from the scalar registers into the CSR bank.",
         without="The per-block program would not change; only debug visibility would be lost."),
]

DROPPED = [
    ("AGU_COL", "01101", "Set a pointer to column j of X for Phase 3.",
     "With w stored reversed, column k is an ascending window that slides exactly like a row, so WSLIDE handles both. "
     "(v1.0 also started column j at x_full[j], but it should have started at x_full[L−j].)"),
    ("VLD_S", "01110", "Load one word and broadcast it to all 16 lanes.",
     "Split into SLD + VMOV splat. Nothing in the block needs it anyway, because VSCALE reads its scalar directly."),
    ("SACC_CLR", "10110", "Clear an accumulator (v1.0 applied it to S1 and to vector register V2).",
     "Clearing the vector accumulator is now free: VMAC.C starts a new sum in the first multiply. A scalar is "
     "cleared with SIMM Sd, 0."),
    ("PHASE_END", "11011", "Tell the control unit that a phase ended and advance a phase counter.",
     "The phases are just positions in one straight-line program; the control unit never needs to know which one "
     "it is in. For debugging, the program can write a phase number with CSR_WR."),
]

PARAMS = [
    ("Instruction width", "32 bits, one fixed format",
     "One instruction per cycle from one BRAM18 (512 × 36). Every field sits at a fixed bit position, so decoding "
     "is wiring and takes one cycle.",
     "16-bit instructions can't hold three register fields and a 12-bit immediate. VLIW would widen the instruction "
     "memory and need a scheduler, and would gain nothing: one VMAC per cycle already keeps all 48 DSPs busy."),
    ("Opcode", "5 bits → 32 codes",
     "20 instructions run every block, so 4 bits (16 codes) is too few. 5 bits is the minimum and leaves 12 codes "
     "for NLMS, utility and spare.",
     "More bits would take space from the register fields and the immediate."),
    ("Group bits", "OPCODE[4:3]",
     "A 2-bit pre-decode steers each instruction to the vector unit, memory/AGU, scalar unit or sequencer before the "
     "full decode. This comes from v1.0, which based it on the pre-decode / supplement-decode split it cites from "
     "Mahmood & Al-Jbaar.",
     "—"),
    ("Register fields", "3 × 5 bits, typed by opcode",
     "Codes 0–7 name registers; 8 = ZERO for scalar and address fields; 8–15 = window chunks W0–W7 for vector "
     "sources. 4 bits would be enough today. 5 keeps v1.0's layout and leaves room for 16 vector registers.",
     "v1.0's global 2-bit type tag, which left only 8 of 16 CSRs reachable."),
    ("Immediate", "12 bits",
     "The largest values are the base address 0x540 (1 344), the loop count 128 and PKOUT's 31. Signed "
     "post-increments are ±16. 12 bits covers 0–4 095 unsigned and ±2 047 signed.",
     "A wider immediate would squeeze the register fields."),
    ("Lanes per PE", "16",
     "L = 64 and B = 128 are multiples of 16. 3 × 16 lanes + 3 scalar multipliers = 51 DSP48E1, which fits the "
     "Z7-10's 80. 16 lanes match 16 banks and a 4-level adder tree.",
     "32 lanes: 99 DSPs, more than the Z7-10 has. 8 lanes would still meet real time, with roughly twice the MAC "
     "instructions; that is a valid smaller option."),
    ("PEs", "3, in lockstep",
     "One per microphone pair, all running the same code. This is the SIMD organisation of Mahmood & Al-Jbaar and the "
     "lecture's array processor.",
     "One PE reused three times saves 32 DSPs and takes about 3× the cycles (~3 % busy). A valid area option."),
    ("Vector registers", "8 × 16 × 32 bit",
     "Phase 3 keeps all 128 error samples resident (128 / 16 = 8 registers); Phase 1 keeps all 64 weights (4). "
     "The CRAY-1 also has 8.",
     "4 registers: half of e would be reloaded for every column. 16 registers: twice the flip-flops, never used."),
    ("Scalar and address registers", "8 + 8",
     "The program uses S0–S1 and A0–A3, A7. Eight of each fit a 3-bit field plus the ZERO code. The CRAY-1 has 8 "
     "scalar and 8 address registers too.",
     "—"),
    ("Memory word", "32 bits",
     "w and g need 32 bits (Q2.30). Samples are stored sign-extended, so every region is addressed the same way.",
     "Separate 16-bit sample memory: saves BRAM bits but needs two word sizes in the address generator."),
    ("Weights", "Q2.30",
     "With 16-bit weights the tiny updates get lost: fixed-point τ agrees with float on only 89.1 % of blocks "
     "(99.6 % with 32 bits), and accuracy drops from 47.0 % to 43.4 %.",
     "Q1.15 weights."),
    ("Accumulator", "48 bits (DSP48E1 P)",
     "A Phase 1 sum needs up to 47 bits and a Phase 3 sum up to 39.",
     "v1.0 suggested 40 bits, which is too small once weights are 32 bits."),
    ("Local memory", "16 banks × 512 × 32 bit (16 BRAM18) per PE",
     "One bank per lane delivers one aligned row per cycle. Single-word writes (SST) and reads (WSLIDE) use one "
     "bank. 1 408 of the 8 192 words are used.",
     "One wide RAM gives the row too, but single-word writes then need byte enables across a 512-bit word."),
    ("Rings", "512 words each (X and D)",
     "Live data is 191 words (x_full[1…191]) plus room for the next 128-sample block: 319 words, more than 256. "
     "512 is the smallest power of two that fits, and a power of two makes the modulo free (keep the low 9 bits).",
     "256-word rings would overwrite live data. v1.0's ping-pong buffers and history copies did not fit."),
    ("Ring write offsets", "XOFF = L−1, DOFF = L/2",
     "XOFF puts x_full[1] (the first sample any product uses) at the block base, so every vector load is aligned. "
     "DOFF delays the reference by the center tap while writing, which gives d_delayed for free.",
     "Copying x_history and d_history every block, as v1.0 planned."),
    ("Window register", "128 × 16 bit",
     "Its length is max(B, L). 16 bits because samples are Q1.15.",
     "32-bit entries: twice the flip-flops for nothing."),
    ("Instruction memory", "512 × 32 (one BRAM18)",
     "The program is 78 instructions (15 %). One BRAM18 is the smallest unit.",
     "—"),
    ("Loop stack", "2 levels",
     "The program uses 1. When B or L exceeds 128, w or e no longer fits in 8 registers, so each VMAC needs its own "
     "VLD. The body then outgrows the 31-instruction limit, and the inner loop needs the second level.",
     "1 level would block larger parameters."),
    ("Control flow", "no branches",
     "Loop counts and addresses never depend on the data. The cycle count was the same on all 600 simulated blocks.",
     "A branch unit and predictor, with nothing to predict."),
    ("Hazards", "scoreboard (hardware interlocks)",
     "The program stays correct if synthesis changes a latency. It costs about 20 small ready-time counters.",
     "Scheduling NOPs in the program gives the same cycle count today, but the program would have to change "
     "whenever a latency changes."),
    ("Clock", "100 MHz",
     "A standard FCLK_CLK0 setting. At 27 µs per block the cluster is busy 1 % of the time, so there is no reason "
     "to push it.",
     "The real Fmax comes from synthesis."),
    ("Number format", "fixed point",
     "DSP48E1 slices are integer multipliers. The fixed-point run matches float on 99.6 % of blocks.",
     "float32 (v1.0) would need floating-point IP cores in every lane."),
]


# ---------------------------------------------------------------------------------------------------- helpers
def _slot(ins):
    cls, short, _ = STATUS[ins["st"]]
    unused = " unused" if ins["d"] == 0 else ""
    origin = "v1.0" if ins["st"] == "kept" else ("new in v1.1" if ins["st"] == "new" else f"was {ins['was']}")
    runs = f"{_n(ins['d'])}× / block" if ins["d"] else "not run"
    return (f'<a class="slot {cls}{unused}" href="isa-origins.html#op-{ins["m"]}">'
            f'<b>{ins["m"]}</b><i>{origin}</i><span>{runs}</span></a>')


def slot_map():
    cells = ""
    for gi, (code, name) in enumerate(GROUPS):
        cells += f'<div class="gh"><b>{code}xxx</b>{name}</div>'
        cells += "".join(_slot(i) for i in INSTR[gi * 8:(gi + 1) * 8])
    legend = ('<div class="legend">'
              '<span><i class="st-kept"></i>kept from v1.0 (18)</span>'
              '<span><i class="st-ren"></i>renamed (6)</span>'
              '<span><i class="st-rew"></i>reworked: same job, new mechanism (4)</span>'
              '<span><i class="st-new"></i>new in v1.1 (4)</span>'
              '<span><i style="border-style:dashed;border-color:var(--muted)"></i>dashed = never run by the '
              'current program (12)</span></div>')
    return f'<div class="scroll"><div class="grid32">{cells}</div></div>{legend}'


def _card(ins):
    cls, _, label = STATUS[ins["st"]]
    was = f" ({ins['was']})" if ins["st"] in ("ren", "rew") else ""
    if ins["d"]:
        use = (f'<span class="use core">runs every block · {ins["s"]} in program · {_n(ins["d"])}× per block'
               f'</span>')
    else:
        use = f'<span class="use{" weak" if ins["use"] == "weak" else ""}">{USE[ins["use"]]}</span>'
    return (f'<article class="card" id="op-{ins["m"]}"><header><h3>{ins["m"]}</h3>'
            f'<span class="code">{ins["code"]}</span><span class="tag {cls}">{label}{was}</span>{use}</header>'
            f'<p class="plain">In plain words: {PLAIN[ins["m"]]}.</p><p class="op">{ins["op"]}</p><dl>'
            f'<dt>Why it exists</dt><dd>{ins["why"]}</dd>'
            f'<dt>Why this form</dt><dd>{ins["form"]}</dd>'
            f'<dt>Seen before in</dt><dd>{ins["prec"]}</dd>'
            f'<dt>Hardware</dt><dd>{ins["hw"]}</dd>'
            f'<dt>Without it</dt><dd>{ins["without"]}</dd></dl></article>')


def _counts():
    from collections import Counter
    st = Counter(i["st"] for i in INSTR)
    use = Counter(i["use"] for i in INSTR)
    assert len(INSTR) == 32 and (st["kept"], st["ren"], st["rew"], st["new"]) == (18, 6, 4, 4), st
    assert (use["core"], use["nlms"], use["util"], use["weak"]) == (20, 2, 3, 7), use
    assert sum(i["s"] for i in INSTR) == 78 and sum(i["d"] for i in INSTR) == 1709
    return st, use


# ---------------------------------------------------------------------------------------------------- origins page
def origins_body():
    _counts()
    cards = ""
    for gi, (code, name) in enumerate(GROUPS):
        cards += f'<h3 id="grp-{code}" style="margin-top:36px">Group {code} · {name}</h3>'
        cards += "".join(_card(i) for i in INSTR[gi * 8:(gi + 1) * 8])
    dropped = "".join(f"<tr><td class='mono'><b>{m}</b></td><td class='mono'>{c}</td><td>{what}</td><td>{why}</td></tr>"
                      for m, c, what, why in DROPPED)
    unused_rows = "".join(
        f"<tr><td class='mono'><a href='#op-{i['m']}'>{i['m']}</a></td><td>{USE[i['use']]}</td>"
        f"<td>{i['without']}</td></tr>" for i in INSTR if i["d"] == 0)
    params = "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td>{d}</td></tr>" for a, b, c, d in PARAMS)
    body = f"""
<section id="answer">
<h2>The short answer</h2>
<div class="key">
<p><strong>The 32 instructions are not all new, and they were not copied from one source.</strong></p>
<p>Rakindu's v1.0 draft defined the 32-bit format, the four groups and all 32 opcode slots for Block-LMS. It took
the overall architecture from Mahmood &amp; Al-Jbaar (2011): one control unit broadcasting to lanes that each have
their own registers and memory, a lane-enable mask, and category bits for a fast pre-decode. v1.1 kept 28 of v1.0's
32 slots (18 unchanged in name and role, 6 renamed, 4 reworked), dropped 4, and added 4 new ones: WLD, SST, SLD and
PKCLR.</p>
<p>Each instruction on its own has a precedent in a well-known machine: the CRAY-1 and MMX from the course
lecture, ARM NEON, RISC-V V, and DSPs such as the TI C54x and ADI Blackfin. What is specific to this design is
<em>which</em> instructions were chosen, and the four ideas built for this algorithm: the sliding-window register,
the reversed weights, the circular input rings and the peak detector.</p>
<p>20 of the 32 run in every block. The other 12 are listed <a href="#unused">below</a> with an honest verdict.</p>
</div>
<div class="stats">
  <div class="stat"><b>28 / 32</b><span>opcode slots that come from v1.0 (18 kept, 6 renamed, 4 reworked)</span></div>
  <div class="stat"><b>4</b><span>new in v1.1: WLD, SST, SLD, PKCLR</span></div>
  <div class="stat"><b>20</b><span>opcodes the verified program runs every block</span></div>
  <div class="stat"><b>1 709</b><span>instructions executed per block, 1 024 of them VMAC</span></div>
</div>
</section>

<section id="lineage">
<h2>Lineage: paper → v1.0 → v1.1</h2>
<div class="lineage">
<div><h3>Mahmood &amp; Al-Jbaar, 2011</h3>
<p>“Design and implementation of SIMD Vector Processor on FPGA”, IEEE ISIICT 2011. According to its abstract: 4
parallel lanes (processing elements) working at the same time, each with its own arithmetic units, vector register
file and local memory, plus a scalar processor for the instructions the lanes can't run.</p>
<p><b>Gave us:</b> the organisation. One instruction stream, identical lanes, per-lane memory.</p></div>
<div><h3>v1.0 · Rakindu</h3>
<p>Mapped Block-LMS onto that organisation: 5 phases, 16-lane vectors, 3 PEs (one per mic pair).</p>
<ul><li>32-bit format, 5-bit opcode, 5-bit register fields, 12-bit immediate</li>
<li>4 groups of 8 via the top two opcode bits (the paper's pre-decode)</li>
<li>all 32 slots and mnemonics</li>
<li>CSRs including MASK_WORK and MASK_NET (the paper's Mask_Work_Reg / Mask_Net_Reg)</li></ul></div>
<div><h3>v1.1 · Kiran</h3>
<p>Checked v1.0 against the golden model and made it executable (16 fixes; see the
<a href="isa.html#changes">changelog</a>):</p>
<ul><li>address registers, post-increment, circular rings</li>
<li>sliding-window register (WLD, WSLIDE)</li>
<li>a real zero-overhead LOOP</li>
<li>fixed-point semantics (shifts, rounding, saturation)</li>
<li>verified: 78-instruction program bit-exact with the fixed-point model</li></ul></div>
</div>
<h3>What exactly came from the paper</h3>
<div class="tbl"><table>
<tr><th>Element</th><th>In v1.0</th><th>In v1.1</th></tr>
<tr><td>Lanes with their own register file and local memory, one instruction stream</td><td>3 PEs × 16 lanes</td><td>kept</td></tr>
<tr><td>Scalar processing next to the lanes</td><td>scalar ALU + S0–S7</td><td>kept (per PE), plus a shared control unit and AGU</td></tr>
<tr><td>Mask_Work_Reg (enable lanes)</td><td>CSR_MASK_WORK</td><td>kept as CSR 0x8 (not exercised by the simulator)</td></tr>
<tr><td>Mask_Net_Reg (lane-to-lane network)</td><td>CSR_MASK_NET, future VNET_RCV</td><td>dropped: the input writer broadcasts Mic 1 to every PE, so no network is needed</td></tr>
<tr><td>Pre-decode / supplement-decode</td><td>2-bit category in OPCODE[4:3]</td><td>kept</td></tr>
</table></div>
<p class="say"><b>Caveat.</b> We could check only the paper's abstract; the full text is behind the IEEE paywall
(doi:10.1109/ISIICT.2011.6149607). The Mask_Work_Reg, Mask_Net_Reg and pre-decode details are as v1.0 reports them.
Only Rakindu, or the full paper, can say whether any v1.0 mnemonics came straight from the paper's own instruction
table. Settle that before the presentation, because it changes the answer to “did you design this ISA?”.
v1.0 also cites an <code>arch.txt</code> that is not in the repository.</p>
</section>

<section id="map">
<h2>The 32 slots at a glance</h2>
<p>Each box is one opcode, in encoding order (rows are OPCODE[4:3], columns OPCODE[2:0]). The colour says where it
came from; the last line says how often the verified program runs it per block. Click a box to jump to its
justification.</p>
{slot_map()}
<p>The ISA slide colours 7 boxes orange (AGU_ADD, WLD, WSLIDE, SST, SLD, LOOP, PKCLR): the instructions whose
<em>mechanism</em> is new for memory addressing and looping. Counted strictly by origin, 4 of those are brand new and
3 are reworked v1.0 slots (AGU_INC → AGU_ADD, AGU_SLIDE → WSLIDE, LOOP_SET → LOOP). CSR_RD is the fourth reworked
slot (v1.0's VLD_CSR, moved to the scalar group). Both counts are correct; say which one you mean.</p>
<h3>The four v1.0 instructions that were dropped</h3>
<div class="tbl"><table>
<tr><th>v1.0</th><th>Code</th><th>What it did</th><th>Why it went</th></tr>
{dropped}
</table></div>
</section>

<section id="cards">
<h2>Every instruction, justified</h2>
<p>Each card answers the same five questions. <b>Why it exists</b>: which step of the algorithm needs it and how often
it runs. <b>Why this form</b>: what changed from v1.0 and why the fields are what they are. <b>Seen before in</b>:
known machines with the same idea (named so you can say it is an established technique, not because we copied
them). <b>Hardware</b>: what it costs. <b>Without it</b>: what would happen if we removed it.</p>
{cards}
</section>

<section id="unused">
<h2>The 12 instructions the program never runs</h2>
<p>The verified per-block program uses 20 opcodes. The other 12 come from v1.0, or are the obvious partner of
an instruction that is used. Here is the honest status of each:</p>
<div class="tbl"><table>
<tr><th>Instruction</th><th>Status</th><th>If removed</th></tr>
{unused_rows}
</table></div>
<div class="key">
<p><strong>How to say it.</strong> “20 instructions carry the algorithm. SDIV and SADD are there for block-NLMS, which
simulated best. VMOV, SLD and CSR_WR are utility and debug. The remaining seven came from v1.0 and cost only decode,
except SMUL, which costs 3 DSP slices and is on our list to decide before RTL. Twenty needed instructions already
require a 5-bit opcode, so the spare codes are free.”</p>
</div>
<h3>What NLMS would add (sketch, not yet simulated)</h3>
<pre><code>; once per block, after Phase 1 while V0–V3 are free   (Open item 2 in ISA_Design.md)
AGU_SET A0, A7, X_RING, circ=1
VLD     V0, [A0]+16          ; first aligned chunk of x_full[1..128]
VMAC.C  V0, V0               ; VACC  = x²
LOOP    7, 2
  VLD     V0, [A0]+16        ; the other 7 chunks
  VMAC    V0, V0             ; VACC += x²
VREDUCE S2, sh=…             ; L·Pₓ = 64 · Σx² / 128 = Σx² / 2: a shift, folded into sh
                             ; (sh must also bring Σx², up to 39 bits, into a 32-bit register)
SADD    S2, S2, ZERO, imm=ε  ; + ε, so silence can't divide by zero
SDIV    S3, S0, S2, pre=…    ; S3 = μ / (L·Pₓ + ε)
; Phase 4 then uses S3 instead of S0 in VSCALE</code></pre>
<p>That is about 20 extra instructions and one 34-cycle division per block, small next to the 2 695-cycle block. Two
details for the scaling study: the tracking study averaged the power over the 191 samples x_full[1…191], while this
sketch uses the 128 aligned samples x_full[1…128]; and the shift and <code>pre</code> values still have to be chosen
so the quotient keeps its precision. The same step size can also freeze the filter in silence without a branch: if
the power is below a threshold, the ARM (or the program) makes μ zero.</p>
</section>

<section id="params">
<h2>Every design parameter, and why</h2>
<div class="tbl"><table>
<tr><th>Choice</th><th>Value</th><th>Why</th><th>Alternative we rejected</th></tr>
{params}
</table></div>
</section>

<section id="refs">
<h2>Sources</h2>
<ul>
<li>B. Mahmood, M. A. Al-Jbaar, “Design and implementation of SIMD Vector Processor on FPGA,” 4th Int. Symp. on
Innovation in Information &amp; Communication Technology (ISIICT), 2011. doi:10.1109/ISIICT.2011.6149607. Abstract
only.</li>
<li>ISA_Design.md v1.0 (Rakindu), git commit 56b9d67, and v1.1 with its changelog.</li>
<li>O. Mutlu, <i>Computer Architecture, Lecture 29a: SIMD Architectures</i>, ETH Zürich, Fall 2025
(<code>onur-comparch-fall2025-lecture29a-simd-afterlecture.pdf</code> in the repo): vector registers,
VLEN/VSTR/VMASK, auto-increment addressing, 16 word-interleaved banks, CRAY-1 organisation (8 vector, 8 scalar, 8
address registers), MMX (fixed width, stride 1, PMADDWD).</li>
<li>Instruction precedents: RISC-V “V” vector extension 1.0; Arm Advanced SIMD (NEON); Intel SSE4.1
(PHMINPOSUW); TI TMS320C54x (AR0–AR7, BK, RPTB, MACD); ADI Blackfin (LSETUP, SEARCH) and SHARC (DO UNTIL); Qualcomm
Hexagon (loop0/loop1).</li>
<li>AMD/Xilinx UG479, <i>7 Series DSP48E1 Slice</i> (25 × 18 multiplier, 48-bit P, OPMODE) and UG473, <i>7 Series
Memory Resources</i> (BRAM18, 512 × 36 simple dual-port).</li>
<li>Usage counts: <code>simulation_py/isa_sim.py</code>, B = 128, L = 64.</li>
</ul>
</section>
"""
    toc = [("answer", "Short answer"), ("lineage", "Lineage"), ("map", "32 slots at a glance"),
           ("cards", "Every instruction"), ("unused", "The 12 unused"), ("params", "Design parameters"),
           ("refs", "Sources")]
    return toc, body


# ---------------------------------------------------------------------------------------------------- ISA page
CHANGES = [
    ("No way to loop", "LOOP_DEC used everywhere but not in the table; all 32 opcodes taken",
     "LOOP: zero-overhead hardware loop, 2-level stack"),
    ("VST_S undefined", "used to store y[i] and g[j]", "SST / SLD"),
    ("AGU pointer can't be selected", "7 pointers used, but no instruction field names one",
     "A0–A7, named by every load/store, post-increment"),
    ("X indexing reports −τ", "rows are reversed; column j starts at L−j, not j. Simulated: +7 instead of −7",
     "store w reversed → row i and column k both start at x_full[·+1], ascending"),
    ("Unaligned 16-wide loads", "sliding window needs any start offset; one BRAM port can't deliver it",
     "16 aligned banks + window register (WLD / WSLIDE)"),
    ("Memory map broken", "d_delayed not contiguous; ping-pong buffers don't fit; x_hist redundant",
     "circular X / D rings, no copies"),
    ("CSR encoding clash", "tag bits [4:3] overlap the 4-bit CSR index → only 8 reachable",
     "operand fields typed by opcode; CSR index in IMM12"),
    ("SACC_CLR on a vector", "scalar-only instruction applied to V2", "VMAC.C clears via DSP OPMODE"),
    ("float32 on DSP48", "DSP48 slices are integer multipliers", "Q1.15 / Q2.30 fixed point, verified"),
    ("Wrong timing inputs", "assumed 16 kHz and ~7 400 cycles", "48 kHz; measured 2 695 cycles"),
    ("Motivation overstated", "“ARM has no headroom”: false at 18 M MAC/s", "latency, PS offload, scaling headroom"),
    ("DSP48E2 with Cortex-A9", "E2 is UltraScale; Zynq-7000 has DSP48E1", "DSP48E1"),
    ("Double subtraction for τ", "SSUB then PKIDX_OUT both computed CT − idx", "PKOUT once, reversed index"),
    ("d_block to 3 PEs", "needed a future VNET_RCV", "input writer broadcasts Mic 1"),
    ("IRQ cleared by RESET", "RESET would also reset the ring position", "STATUS.DONE write-1-to-clear"),
    ("μ = 0.05 lags", "47 % within ±1; 3.7 s lag", "μ = 0.5 (85.6 %) or NLMS (88 %)"),
]


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def isa_body(figure):
    """figure: build_explainers.figure(name, alt, caption, wide=False), used to embed figures/isa.png."""
    _counts()
    fig = figure("isa.png", "Instruction format, the 32 opcodes in four groups, field typing, addressing modes and "
                 "the commented Phase-1 loop",
                 "The ISA on one page: format, the 32 opcodes (orange = new mechanism in v1.1), how register "
                 "fields are typed, the three addressing modes and the Phase-1 inner loop.", wide=True)
    rows = ""
    for gi, (code, name) in enumerate(GROUPS):
        for k, ins in enumerate(INSTR[gi * 8:(gi + 1) * 8]):
            grp = f'<td rowspan="8"><b>{code}</b><br><span class="say">{name}</span></td>' if k == 0 else ""
            cls, _, label = STATUS[ins["st"]]
            origin = label + (f" ({ins['was']})" if ins["st"] in ("ren", "rew") else "")
            runs = _n(ins["d"]) if ins["d"] else '<span class="say">—</span>'
            rows += (f"<tr>{grp}<td class='mono'>{ins['code']}</td>"
                     f"<td class='mono'><a href='isa-origins.html#op-{ins['m']}'><b>{ins['m']}</b></a></td>"
                     f"<td>{PLAIN[ins['m']]}<span class='formal'>{ins['op']}</span></td>"
                     f"<td><span class='tag {cls}'>{origin}</span></td><td class='num'>{runs}</td></tr>")
    chg = "".join(f"<tr><td class='num'>{i + 1}</td><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>"
                  for i, (a, b, c) in enumerate(CHANGES))
    listing = open(os.path.join(HERE, "..", "ISA_Design.md")).read()
    start = listing.index("; ---- Phase 0: wait + setup ----")
    asm = _esc(listing[start:listing.index("```", start)])
    body = f"""
<section id="what">
<h2>What an instruction set is, for this accelerator</h2>
<p>An {g("isa", "instruction set (ISA)")} is the list of commands the accelerator understands and how each one is
written as a 32-bit number. Our program is written in these commands. It runs on the accelerator's own
{g("pe", "control unit")}, not on the ARM. The ARM writes the program (78 words) into the
{g("imem", "instruction memory")} once at start-up; after that it runs once per block of audio by itself.</p>
<ul>
<li><b>One instruction, three PEs.</b> The control unit reads one instruction and sends it to all three PEs at the
same time (that is {g("simd", "SIMD")}). Each PE works on its own microphone pair. Inside a PE there are 16
{g("lane", "lanes")}, so one {g("mac", "multiply-accumulate")} instruction does 16 × 3 = 48 multiply-adds.</li>
<li><b>Four kinds of {g("register", "registers")}.</b> V0–V7 hold 16 numbers each (one per lane). W0–W7 are the 8
chunks of the {g("window", "window register")} (16 samples each). S0–S7 hold one number each. A0–A7 hold memory
addresses, and are shared by all PEs because all PEs use the same addresses.</li>
<li><b>From text to bits.</b> The {g("assembler", "assembler")} in <code>isa_sim.py</code> turns a line such as
<code>VMAC.C W0, V4, sh=7</code> into the number <code>0x0010400F</code>. That number is what the hardware
decodes.</li>
</ul>
{fig}
</section>

<section id="format">
<h2>Instruction format</h2>
<div class="scroll"><div class="bits">
<div><b>OPCODE</b><span>[31:27] · 5 bits</span></div><div><b>DST</b><span>[26:22] · 5</span></div>
<div><b>SRC1</b><span>[21:17] · 5</span></div><div><b>SRC2</b><span>[16:12] · 5</span></div>
<div><b>IMM12</b><span>[11:0] · 12 bits</span></div></div></div>
<p>This layout is v1.0's, unchanged. Every instruction is 32 bits with the same five fields at the same positions,
so the decoder is mostly wiring, and one instruction comes out of the 32-bit-wide instruction memory every cycle.
<code>OPCODE[4:3]</code> picks one of four groups of eight, which tells the control unit which unit the instruction
belongs to before the rest is decoded.</p>
<div class="tbl"><table>
<tr><th>Field</th><th>Bits</th><th>Why this width</th></tr>
<tr><td>OPCODE</td><td class="num">5</td><td>20 instructions run every block, more than 4 bits (16) can encode. 5 bits
is the minimum, and gives 32 codes.</td></tr>
<tr><td>DST, SRC1, SRC2</td><td class="num">5 each</td><td>Registers need codes 0–7, plus 8 for ZERO and 8–15 for
the window chunks. 4 bits would do; 5 keeps v1.0's layout and leaves room for 16 vector registers.</td></tr>
<tr><td>IMM12</td><td class="num">12</td><td>Largest values: base address 0x540 (1 344), loop count 128, PKOUT
offset 31, post-increments ±16. Unsigned range 0–4 095, signed ±2 047. It also carries small sub-fields (shift
amounts, flags, the CSR index).</td></tr>
</table></div>
<h3>What a register field means depends on the opcode</h3>
<div class="tbl"><table>
<tr><th>Field kind</th><th>Codes 0–7</th><th>Code 8 and up</th></tr>
<tr><td>vector source</td><td>V0–V7</td><td>8–15 = W0–W7, the window chunks (VMAC only)</td></tr>
<tr><td>scalar</td><td>S0–S7</td><td>8 = ZERO</td></tr>
<tr><td>address</td><td>A0–A7</td><td>8 = ZERO (base for AGU_SET)</td></tr>
<tr><td>CSR</td><td colspan="2">index in IMM12[3:0]</td></tr>
</table></div>
<p>v1.0 used one global 2-bit tag in every register field (00 vector, 01 scalar, 10 CSR, 11 immediate). The CSR tag
sat in bits [4:3] while the CSR index needed bits [3:0], so bit 3 was used twice and only 8 of the 16 CSRs could be
named. Letting the opcode decide what a field means removes the tag bits altogether.</p>
<h3>One word, decoded</h3>
<div class="tbl"><table>
<tr><th>Word</th><th>OPCODE</th><th>DST</th><th>SRC1</th><th>SRC2</th><th>IMM12</th><th>Meaning</th></tr>
<tr><td class="mono">0010400F</td><td class="mono">00000 VMAC</td><td class="mono">00000 —</td>
<td class="mono">01000 W0</td><td class="mono">00100 V4</td><td class="mono">0000 0000 1111</td>
<td>IMM[0] = 1 → .C (start a new sum); IMM[4:1] = 7 → sh = 7. <code>VMAC.C W0, V4, sh=7</code></td></tr>
<tr><td class="mono">B9C00080</td><td class="mono">10111 LOOP</td><td class="mono">00111 len 7</td>
<td class="mono">00000</td><td class="mono">00000</td><td class="mono">0000 1000 0000</td>
<td>count = 128. <code>LOOP 128, 7</code></td></tr>
<tr><td class="mono">500E1000</td><td class="mono">01010 AGU_SET</td><td class="mono">00000 A0</td>
<td class="mono">00111 A7</td><td class="mono">00001 circ</td><td class="mono">0000 0000 0000</td>
<td>A0 = A7 + X_RING (0), circular. <code>AGU_SET A0, A7, X_RING, circ=1</code></td></tr>
<tr><td class="mono">70061001</td><td class="mono">01110 SST</td><td class="mono">00000</td>
<td class="mono">00011 A3</td><td class="mono">00001 S1</td><td class="mono">0000 0000 0001</td>
<td>M[A3] = S1, then A3 += 1. <code>SST S1, [A3]+1</code></td></tr>
</table></div>
<p class="say">These are the assembler's real output (<code>isa_sim.py</code>), not hand-written.</p>
</section>

<section id="opcodes">
<h2>All 32 opcodes</h2>
<p>The origin column says where each instruction came from; the last column is how many times it runs per block in
the verified program. Click a mnemonic for its full justification on the
<a href="isa-origins.html#cards">origins page</a>.</p>
<div class="tbl"><table>
<tr><th>Group</th><th>Code</th><th>Mnemonic</th><th>Operation</th><th>Origin</th><th class="num">Runs / block</th></tr>
{rows}
</table></div>
</section>

<section id="modes">
<h2>Addressing modes</h2>
<p>An addressing mode is the rule for working out <em>which memory word</em> an instruction reads or writes. All
addresses come from the address registers A0–A7, computed by the shared {g("agu", "address generator (AGU)")}.</p>
<div class="tbl"><table>
<tr><th>Mode</th><th>Example</th><th>In plain words</th><th>Address arithmetic</th><th>Used for</th></tr>
<tr><td>{g("postinc", "Post-increment")}</td><td class="mono">VLD V4, [A2]+16</td><td>use the address in A2, then move
A2 on by 16, ready for the next chunk</td><td>address = A2; A2 += 16</td>
<td>walking through w, y, e, g in 16-word chunks; single-word stores with +1</td></tr>
<tr><td>Base + offset</td><td class="mono">AGU_SET A0, A7, X_RING</td><td>set A0 to “where this block starts” (A7)
plus the start of the X ring</td><td>A0 = A7 + X_RING</td><td>pointing at this block's data inside a ring</td></tr>
<tr><td>{g("ring", "Circular")}</td><td class="mono">… circ=1</td><td>when the pointer runs off the end of the
512-word ring, it continues at the start, like a clock hand</td><td>keep bits [12:9]; add only in bits [8:0]</td>
<td>the input rings, so old samples never need to be copied</td></tr>
<tr><td>{g("window", "Sliding window")}</td><td class="mono">WSLIDE [A0], len=64</td><td>shift the window along by
one sample and fetch just the one new sample at A0</td><td>read M[A0]; A0 += 1</td>
<td>next row (Phase 1) or column (Phase 3) of X with one memory read</td></tr>
</table></div>
<div class="key"><p><strong>Why these are enough.</strong> Once w is stored reversed, every access in the algorithm
is an aligned 16-word chunk, a single word, or “the same window moved by one”. There are no strides, gathers or
unaligned vectors, so the address generator is one adder and a mask. The lecture's general vector machine needs a
stride register (VSTR), a length register (VLEN) and a mask register (VMASK); this algorithm needs none of them,
which is also how MMX was designed (fixed width, stride always 1).</p></div>
<h3>Why storing w reversed makes this work: a tiny example</h3>
<p>Take L = 4 taps and B = 3 outputs, so <code>x_full = x0 … x6</code>. The golden model builds
<code>X[i] = x_full[i+L : i : −1]</code>:</p>
<div class="tbl"><table>
<tr><th>Row</th><th>X[i, 0]</th><th>X[i, 1]</th><th>X[i, 2]</th><th>X[i, 3]</th><th>y[i] = X[i] · w</th></tr>
<tr><td>0</td><td>x4</td><td>x3</td><td>x2</td><td>x1</td><td>x4·w0 + x3·w1 + x2·w2 + x1·w3</td></tr>
<tr><td>1</td><td>x5</td><td>x4</td><td>x3</td><td>x2</td><td>x5·w0 + x4·w1 + x3·w2 + x2·w3</td></tr>
<tr><td>2</td><td>x6</td><td>x5</td><td>x4</td><td>x3</td><td>x6·w0 + x5·w1 + x4·w2 + x3·w3</td></tr>
</table></div>
<ul>
<li>Rows run <em>backwards</em> in memory. Store <code>w_rev = [w3, w2, w1, w0]</code> and row 0 becomes
<code>x1·w_rev[0] + x2·w_rev[1] + x3·w_rev[2] + x4·w_rev[3]</code>: memory read forwards from x1. Row 1 starts at
x2, row 2 at x3. Each row is the previous one moved by one sample, which is what WSLIDE does.</li>
<li>Columns: column 3 of X is <code>x1, x2, x3</code> and column 0 is <code>x4, x5, x6</code>. In w_rev order
(k = L−1−j), column k starts at x_full[k+1]: again forwards and again moving by one sample. So Phase 3 uses the same
window hardware with length B instead of L.</li>
<li>v1.0 read rows forwards from x_full[0] with w in normal order: <code>x0·w0 + x1·w1 + x2·w2 + x3·w3</code>.
That is a different filter (mirrored and shifted by one sample), so it converges to a mirrored spike. Running the
same audio through v1.0's access pattern reported <b>+7 where the true delay is −7</b>.</li>
</ul>
</section>

<section id="fixed">
<h2>Where every shift amount comes from</h2>
<p>The shift fields in VMAC, VREDUCE and VSCALE exist because the datapath is fixed point. x, d, y, e are Q1.15
(15 fractional bits); w and g are Q2.30 (30 fractional bits); μ is Q1.15.</p>
<div class="tbl"><table>
<tr><th>Step</th><th>Instruction</th><th>Formats in → out</th><th>Shift and why</th></tr>
<tr><td>P1 multiply</td><td class="mono">VMAC W, V, sh=7</td><td>x (Q1.15) × w (Q2.30 → Q2.23) → 38 fractional bits,
41-bit product</td><td>sh = 7: the DSP48E1 A port is 25 bits, so the 32-bit weight drops its 7 lowest bits</td></tr>
<tr><td>P1 accumulate</td><td class="mono">4 × VMAC + tree</td><td>64 products → at most 47 bits</td><td>fits the
48-bit P register; the adder tree is ~52 bits wide</td></tr>
<tr><td>P1 result</td><td class="mono">VREDUCE sh=23, rnd, sat16</td><td>38 fractional bits → Q1.15</td>
<td>38 − 15 = 23; round to nearest; clamp to 16 bits</td></tr>
<tr><td>P2 error</td><td class="mono">VSUB sat16</td><td>Q1.15 − Q1.15 → Q1.15</td><td>no shift; clamp</td></tr>
<tr><td>P3 multiply</td><td class="mono">VMAC W, V</td><td>x (Q1.15) × e (Q1.15) → 30 fractional bits, 32-bit
product</td><td>no shift: e already fits the A port</td></tr>
<tr><td>P3 accumulate</td><td class="mono">8 × VMAC + tree</td><td>128 products → at most 39 bits</td><td>—</td></tr>
<tr><td>P3 result</td><td class="mono">VREDUCE sh=7</td><td>sum → mean gradient, Q2.30</td><td>7 = log2 128:
dividing by B is a shift, so μ/B needs no divider</td></tr>
<tr><td>P4 step</td><td class="mono">VSCALE pre=7, post=8</td><td>g (Q2.30 → Q2.23) × μ (Q1.15) → 38 fractional bits
→ Q2.30</td><td>pre = 7 for the 25-bit A port; post = 38 − 30 = 8</td></tr>
<tr><td>P4 add</td><td class="mono">VADD</td><td>Q2.30 + Q2.30</td><td>clamp at 32 bits</td></tr>
<tr><td>P5 peak</td><td class="mono">PKOUT 31</td><td>index → τ</td><td>31 = L−1−L/2, because w is reversed</td></tr>
</table></div>
</section>

<section id="program">
<h2>The microprogram, phase by phase</h2>
<p>One pass per block: 78 instructions stored (312 bytes), 1 709 executed, 2 695 cycles. The encodings in the full
listing below are the assembler's actual output.</p>
<div class="tbl"><table>
<tr><th>Phase</th><th>What the instructions do</th><th class="num">Cycles</th><th>Why that many</th></tr>
<tr><td>0 · wait, setup</td><td><code>SYNC 1</code> waits until the input writer has a full new block.
<code>AGU_SET A7, A7, 0, circ=1</code> marks the block base as circular; its value carries over from the last block
(0 after a reset). <code>CSR_RD S0, MU</code> reads μ, so the ARM can change it at any time.</td><td class="num">5</td>
<td>3 instructions + 2 cycles to fill fetch/decode</td></tr>
<tr><td>1 · y = X w</td><td>4 × <code>VLD</code> put all 64 weights in V4–V7 for the whole phase. <code>AGU_SET A0, A7,
X_RING</code> points at x_full[1]; 4 × <code>WLD</code> fill the window with x_full[1…64] and leave A0 at x_full[65],
the next sample WSLIDE needs. Then <code>LOOP 128, 7</code>: 4 VMAC, VREDUCE, WSLIDE, SST.</td>
<td class="num">1 548</td><td>12 setup + 128 rows × 12 cycles (timeline below)</td></tr>
<tr><td>2 · e = d − y</td><td><code>AGU_SET A1, A7, D_RING</code> points at d_delayed[0]: the center-tap delay was
applied when the D ring was written. <code>LOOP 8, 4</code>: VLD d, VLD y, VSUB (clamped), VST e.</td>
<td class="num">44</td><td>4 setup + 8 × 5 (one stall waiting for the second load)</td></tr>
<tr><td>3 · g = Xᵀ e</td><td>8 × <code>VLD</code> put all 128 errors in V0–V7. A0 back to x_full[1]; 8 × <code>WLD</code>
fill the window with x_full[1…128]. <code>LOOP 64, 11</code>: 8 VMAC, VREDUCE (÷B), WSLIDE len=128, SST.</td>
<td class="num">1 044</td><td>20 setup + 64 columns × 16 cycles</td></tr>
<tr><td>4 · w += μg</td><td><code>LOOP 4, 5</code>: VLD g, VLD w (no increment: the store goes back to the same
place), VSCALE by μ, VADD, VST w with +16.</td><td class="num">31</td><td>3 setup + 4 × 7 (VADD waits 2 cycles for
the DSP)</td></tr>
<tr><td>5 · τ</td><td>PKCLR, then <code>LOOP 4, 2</code>: VLD w, PKMAX. <code>PKOUT 31</code> writes τ.
<code>AGU_ADD A7, 128</code> moves to the next block (wrapping in the ring). IRQ, HALT.</td><td class="num">23</td>
<td>PKOUT waits for the 5-stage comparator tree</td></tr>
<tr><td><b>Total</b></td><td></td><td class="num"><b>2 695</b></td><td>27.0 µs at 100 MHz; the same for every
block</td></tr>
</table></div>

<h3>One Phase-1 row, cycle by cycle</h3>
<p>The scoreboard lets an instruction issue only when its inputs are ready. This is where the 12 cycles per row go:</p>
<div class="tbl"><table class="tl">
<tr><th>Cycle</th><th>Issues</th><th>In plain words</th><th>Why it waits (or not)</th></tr>
<tr><td>0</td><td class="mono">VMAC.C W0, V4, sh=7</td><td>multiply samples 1–16 of this row by weights 0–15 and
start new running sums</td><td>new sum for row i</td></tr>
<tr><td>1–3</td><td class="mono">VMAC W1…W3, V5…V7</td><td>the same for the next 48 samples and weights, adding to
the sums</td><td>back-to-back: the DSP accumulates internally</td></tr>
<tr><td class="stall">4–5</td><td class="stall">stall</td><td class="stall">wait</td><td>VREDUCE needs VACC; the
DSP pipeline takes 3 cycles</td></tr>
<tr><td>6</td><td class="mono">VREDUCE S1, sh=23</td><td>add the 16 sums into one number y[i]</td><td>adder tree
starts; y[i] ready at cycle 11</td></tr>
<tr><td>7</td><td class="mono">WSLIDE [A0], len=64</td><td>move the window on by one sample for the next row</td>
<td>doesn't need S1, so it goes at once</td></tr>
<tr><td class="stall">8–10</td><td class="stall">stall</td><td class="stall">wait</td><td>SST needs S1 from the
5-cycle tree</td></tr>
<tr><td>11</td><td class="mono">SST S1, [A3]+1</td><td>write y[i] to memory</td><td>the loop jumps back with no
bubble</td></tr>
</table></div>
<p>5 of the 12 cycles are stalls. Storing y[i−1] during row i's stall slots (software pipelining) would bring a row
to about 8 cycles. It isn't needed: the whole block already takes 1 % of the time available. The Phase-3 column has
the same shape: 8 VMACs, 2 stalls, VREDUCE, WSLIDE, 3 stalls, SST = 16 cycles.</p>
<p><b>v1.0 for comparison.</b> v1.0's Phase-1 listing spent 32 instructions per row: 4 × (VLD, VLD, VMAC, AGU_INC,
AGU_INC, LOOP_DEC), plus clears, the reduce, the store, the slide and the loop. v1.1 needs 7. The saving comes from
post-increment, keeping w in registers, VMAC.C, the window register and the zero-overhead LOOP.</p>

<details><summary>Full listing with encodings</summary><div><pre><code>{asm}</code></pre></div></details>
</section>

<section id="changes">
<h2>What changed from v1.0, and why</h2>
<p>All 16 problems were found by checking v1.0 against the golden model, then confirmed by running the
instruction-level simulator.</p>
<div class="tbl"><table>
<tr><th>#</th><th>v1.0 problem</th><th>Evidence</th><th>v1.1 fix</th></tr>
{chg}
</table></div>
</section>
"""
    toc = [("what", "What an ISA is"), ("format", "Format"), ("opcodes", "Opcodes"), ("modes", "Addressing modes"),
           ("fixed", "Shift amounts"), ("program", "Microprogram"), ("changes", "Changes from v1.0")]
    return toc, body


# ---------------------------------------------------------------------------------------------------- index + Q&A
def index_section():
    return """
<section id="origin">
<h2>Where the ISA came from</h2>
<div class="key">
<p><strong>If asked “did you design this ISA or copy it?”</strong></p>
<p>“The organisation comes from Mahmood &amp; Al-Jbaar: one control unit, identical lanes with their own memory.
Rakindu's v1.0 turned that into a 32-instruction ISA for Block-LMS. In v1.1 we kept 28 of those slots, reworked the
addressing and looping, and added four instructions. Each instruction has a precedent in known machines, such as the
CRAY-1, MMX, NEON and DSPs. What is ours is the selection, and the sliding window, reversed weights and ring
buffers.”</p>
<p>20 of the 32 run every block. Two are for NLMS, three are utility, and seven are weak (they cost only decode,
except SMUL, which costs 3 DSPs). Say this before an examiner finds it.</p>
</div>
<p>Details, one card per instruction: <a href="isa-origins.html">ISA origins &amp; justification</a>.</p>
</section>
"""


QA_PROVENANCE = ("Where the ISA came from", [
    ("Did you design this ISA yourselves, or take it from somewhere?",
     "Both, in layers. The organisation (one control unit broadcasting each instruction to lanes that have their own "
     "registers and memory, a lane-enable mask, category bits for pre-decode) comes from Mahmood &amp; Al-Jbaar 2011, "
     "via Rakindu's v1.0 draft. v1.0 defined the format and all 32 slots for Block-LMS. v1.1 kept 28 of them (18 as "
     "they were, 6 renamed, 4 reworked), dropped 4 and added 4 (WLD, SST, SLD, PKCLR). The individual operations "
     "have precedents in known ISAs; the selection, the sliding window, the reversed weights, the ring buffers and "
     "the peak detector are specific to this design."),
    ("What exactly did you take from the Mahmood paper?",
     "The organisation: identical lanes, each with its own arithmetic units, vector register file and local memory, "
     "driven by one instruction stream, with scalar support alongside. v1.0 also took the work-mask register (kept as "
     "CSR MASK_WORK) and the lane-network mask (dropped, because the input writer broadcasts Mic 1). The 2-bit "
     "category field in the opcode is v1.0's version of the paper's pre-decode step. We could check only the "
     "abstract, so confirm with Rakindu whether any mnemonics came straight from the paper's instruction table."),
    ("Why not use an existing ISA such as RISC-V V or NEON?",
     "A general vector ISA brings machinery this algorithm never uses: vector-length and stride registers, masks, "
     "gather/scatter, branches (the lecture's list of vector features). All of it costs area and verification time. "
     "Block-LMS needs unit stride, fixed lengths, counted loops and a few special operations. That is the trade MMX "
     "made (fixed width set by the opcode, stride always 1). We borrow semantics from those ISAs where they fit; "
     "each instruction's card names its precedent."),
    ("The Cortex-A9 has NEON. Why not just run it there?",
     "It could: about 18 M MAC/s is within its reach, and we say so. The accelerator gives a fixed 27 µs latency that "
     "doesn't depend on the OS, leaves the ARM free for triangulation and I/O, and has ~99× headroom for longer "
     "filters or more microphones. And the accelerator is the subject of the course project."),
    ("Twelve opcodes are never executed. Why are they there?",
     "20 opcodes run every block. SDIV and SADD are for block-NLMS, which simulated best (88 % within ±1 sample). "
     "VMOV, SLD and CSR_WR are utility and debug. VABS, VMUL, SMUL, SSUB, SMOV, SIMM and NOP came from v1.0 and have "
     "weak cases; all except SMUL cost only decode. SMUL costs 3 DSP48E1, and we will decide on it before RTL. "
     "Twenty needed instructions already require a 5-bit opcode, so the spare codes cost nothing."),
    ("Why exactly 32 instructions?",
     "32 is not a target. 5 opcode bits give 32 codes. 20 instructions are needed every block, which already rules "
     "out a 4-bit opcode (16 codes)."),
])

QA_ISA_EXTRA = [
    ("Why does VMAC accumulate into a separate accumulator and not a vector register?",
     "A Phase-1 product is 41 bits and a row adds 64 of them (47 bits). A 32-bit vector register would overflow, and "
     "writing it back every cycle costs register-file bandwidth. The DSP48E1 has a 48-bit P register that accumulates "
     "internally at full speed, so VACC is that register. VMAC.C starts a new sum for free (OPMODE Z = 0)."),
    ("Why no vector length, stride or mask registers, like the lecture's vector processor?",
     "L = 64 and B = 128 are fixed multiples of 16, every access is unit-stride once w is reversed, and there are no "
     "per-element conditions. VLEN, VSTR and VMASK would be hardware with nothing to do."),
    ("There are no conditional branches. What if you need a decision?",
     "The algorithm has none: loop counts and addresses never depend on the data, and the cycle count is identical "
     "for every block. The one decision we can foresee, freezing the filter in silence, needs no branch: make the "
     "step size zero (μ_eff from SDIV, or the ARM writes MU = 0). A spare opcode could hold a skip or select "
     "instruction later."),
    ("How is the division by B free?",
     "B = 128 = 2⁷. VREDUCE shifts its sum right by 7 in Phase 3, which turns the gradient sum into the mean. The "
     "update is then just μ times the mean."),
    ("How would you add NLMS?",
     "Once per block: VMAC each of the 8 aligned chunks of x_full[1…128] with itself and VREDUCE to get the power "
     "(with B and L powers of two, L·Pₓ is just a shift of Σx²), add ε with SADD, divide with SDIV, and use the "
     "result instead of μ in VSCALE. That is about 20 instructions and a 34-cycle division. The ISA already supports "
     "it; the fixed-point scaling study is open item 2."),
]

QA_UARCH_EXTRA = [
    ("Why a scoreboard, if the program never changes?",
     "The latencies might. If synthesis forces an extra pipeline stage in the adder tree, a statically scheduled "
     "program full of NOPs would have to be rewritten; with interlocks it stays correct. It costs about 20 small "
     "ready-time counters."),
    ("Why is the AGU shared but the scalar registers are per PE?",
     "All three PEs access the same address at the same time: only the data differs. So one set of address "
     "registers serves all of them, which is the SIMD split (control shared, data replicated). Scalar registers hold "
     "results such as y[i], which differ per PE."),
    ("Why are the rings exactly 512 words?",
     "The live data is 191 samples (x_full[1…191]), plus room for the next 128-sample block: 319 words. That is "
     "more than 256, so 512 is the smallest power of two that fits. With a power of two, the wrap is just keeping "
     "the low 9 address bits."),
]


def extend_qa(qa):
    """Insert the provenance group after 'Motivation' and add the extra ISA / microarchitecture questions."""
    names = [g for g, _ in qa]
    if QA_PROVENANCE[0] not in names:
        qa.insert(names.index("Motivation") + 1 if "Motivation" in names else 0, QA_PROVENANCE)
    for grp, items in qa:
        extra = {"ISA": QA_ISA_EXTRA, "Microarchitecture & memory": QA_UARCH_EXTRA}.get(grp, [])
        have = {q for q, _ in items}
        items.extend(x for x in extra if x[0] not in have)
