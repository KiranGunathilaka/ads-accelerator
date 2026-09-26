"""
Instruction-level simulator for the Block-LMS SIMD cluster, ISA v1.1 (see ISA_Design.md).

- 3 PEs x 16 lanes in lockstep, one shared control unit (PC, hardware loops, AGU).
- Bit-accurate fixed-point datapath (same formats as fixed_point_model.py).
- Simple timing model: single-issue, in-order, stall on read-after-write hazards.
- Streams the four microphone channels through the input writer into the circular
  X / D rings exactly as the AXI4-Stream slave would, then runs the microprogram once
  per block and checks tau and w_rev against FixedPointBlockLMS bit-for-bit.

Usage:  python3 simulation_py/isa_sim.py [num_blocks]
"""
import re
import sys
import numpy as np

# ---------------------------------------------------------------- parameters
VLEN, NPE, WLEN = 16, 3, 128           # lanes per PE, PEs, sliding-window length (max(B, L))
MEM_WORDS = 16 * 512                   # 16 banks x 512 words (one BRAM18 per bank, SDP 512x36)
RING_BITS = 9                          # X and D rings are 512 words
RING = 1 << RING_BITS

X_RING, D_RING = 0x000, 0x200
W_BASE, Y_BASE, E_BASE, G_BASE = 0x400, 0x440, 0x4C0, 0x540

CSR = {"CTRL": 0, "STATUS": 1, "MU": 2, "B": 3, "L": 4, "TAU21": 5, "TAU31": 6, "TAU41": 7,
       "MASK_WORK": 8, "XOFF": 9, "DOFF": 10, "SAMPLES_IN": 11, "CYCLE_LO": 12, "CYCLE_HI": 13,
       "ERR_CODE": 14, "VERSION": 15}

# ---------------------------------------------------------------- opcode table (5-bit)
OPC = {
    # 00 vector arithmetic
    "VMAC": 0b00000, "VSUB": 0b00001, "VADD": 0b00010, "VSCALE": 0b00011,
    "VABS": 0b00100, "VMOV": 0b00101, "VREDUCE": 0b00110, "VMUL": 0b00111,
    # 01 memory / AGU
    "VLD": 0b01000, "VST": 0b01001, "AGU_SET": 0b01010, "AGU_ADD": 0b01011,
    "WLD": 0b01100, "WSLIDE": 0b01101, "SST": 0b01110, "SLD": 0b01111,
    # 10 scalar / loop
    "SMUL": 0b10000, "SADD": 0b10001, "SSUB": 0b10010, "SDIV": 0b10011,
    "SMOV": 0b10100, "SIMM": 0b10101, "CSR_RD": 0b10110, "LOOP": 0b10111,
    # 11 special / control
    "PKMAX": 0b11000, "PKOUT": 0b11001, "SYNC": 0b11010, "PKCLR": 0b11011,
    "IRQ": 0b11100, "NOP": 0b11101, "HALT": 0b11110, "CSR_WR": 0b11111,
}
ZERO = 8                               # operand code for the constant-zero source (S or A fields)


def encode(op, dst=0, s1=0, s2=0, imm=0):
    return (OPC[op] << 27) | ((dst & 31) << 22) | ((s1 & 31) << 17) | ((s2 & 31) << 12) | (imm & 0xFFF)


# ---------------------------------------------------------------- tiny assembler
def _reg(tok):
    tok = tok.strip().upper()
    if tok == "ZERO":
        return ZERO
    m = re.fullmatch(r"([VSAW])(\d)", tok)
    if not m:
        raise ValueError(f"bad register {tok}")
    kind, n = m.group(1), int(m.group(2))
    return n + 8 if kind == "W" else n   # W0-W7 share the vector-source field with bit 3 set


def _mem(tok):
    m = re.fullmatch(r"\[(A\d)\]\+?(-?\d+)?", tok.strip().upper().replace(" ", ""))
    return _reg(m.group(1)), int(m.group(2) or 0)


def _imm(tok, sym):
    tok = tok.strip()
    return int(eval(tok, {}, sym))


def assemble(src, sym):
    prog = []
    phase = 0
    for line in src.splitlines():
        m = re.search(r";\s*-+\s*Phase (\d)", line)
        if m:
            phase = int(m.group(1))
        line = line.split(";")[0].strip()
        if not line:
            continue
        mnem, _, rest = line.partition(" ")
        mnem = mnem.upper()
        flags = set()
        if "." in mnem:
            mnem, *fl = mnem.split(".")
            flags = set(fl)
        args = [a.strip() for a in rest.split(",")] if rest.strip() else []
        kv = {}
        pos = []
        for a in args:
            if "=" in a:
                k, v = a.split("=")
                kv[k.strip().lower()] = _imm(v, sym)
            elif a:
                pos.append(a)
        d = s1 = s2 = imm = 0
        if mnem == "VMAC":                      # VMAC[.C] Va|Wc, Vb, sh=n
            s1, s2 = _reg(pos[0]), _reg(pos[1])
            imm = (1 if "C" in flags else 0) | (kv.get("sh", 0) << 1)
        elif mnem in ("VSUB", "VADD", "VMUL"):  # Vd, Va, Vb [, sat16=1 | sh=n]
            d, s1, s2 = _reg(pos[0]), _reg(pos[1]), _reg(pos[2])
            imm = kv.get("sat16", 0) if mnem != "VMUL" else kv.get("sh", 0)
        elif mnem == "VSCALE":                  # Vd, Va, Ss, pre=n, post=m
            d, s1, s2 = _reg(pos[0]), _reg(pos[1]), _reg(pos[2])
            imm = (kv.get("pre", 0) & 0xF) | ((kv.get("post", 0) & 0x1F) << 4)
        elif mnem in ("VABS",):
            d, s1 = _reg(pos[0]), _reg(pos[1])
        elif mnem == "VMOV":                    # Vd, Va   or   Vd, Ss (splat)
            d = _reg(pos[0])
            if pos[1].upper().startswith("S"):
                s2, imm = _reg(pos[1]), 1
            else:
                s1 = _reg(pos[1])
        elif mnem == "VREDUCE":                 # Sd, sh=n, rnd=1, sat16=1
            d = _reg(pos[0])
            imm = (kv.get("sh", 0) & 31) | (kv.get("rnd", 0) << 5) | (kv.get("sat16", 0) << 6)
        elif mnem in ("VLD", "WLD", "SLD"):     # Vd|Wc|Sd, [An]+inc
            d = _reg(pos[0]) & 7
            s1, imm = _mem(pos[1])
        elif mnem in ("VST", "SST"):            # Vs|Ss, [An]+inc
            s2 = _reg(pos[0])
            s1, imm = _mem(pos[1])
        elif mnem == "WSLIDE":                  # [An], len=n     (post-increment is always +1)
            s1, _ = _mem(pos[0])
            imm = kv["len"]
        elif mnem == "AGU_SET":                 # An, Am|ZERO, offset [, circ=1]
            d, s1, imm = _reg(pos[0]), _reg(pos[1]), _imm(pos[2], sym)
            s2 = kv.get("circ", 0)
        elif mnem == "AGU_ADD":                 # An, inc
            d, imm = _reg(pos[0]), _imm(pos[1], sym)
        elif mnem in ("SADD", "SSUB", "SMUL"):  # Sd, Sa, Sb|ZERO [, imm=n]
            d, s1, s2 = _reg(pos[0]), _reg(pos[1]), _reg(pos[2])
            imm = kv.get("imm", 0)
        elif mnem == "SDIV":                    # Sd, Sa, Sb, pre=n   ->  Sd = (Sa << n) / Sb
            d, s1, s2 = _reg(pos[0]), _reg(pos[1]), _reg(pos[2])
            imm = kv.get("pre", 0)
        elif mnem == "SMOV":
            d, s1 = _reg(pos[0]), _reg(pos[1])
        elif mnem == "SIMM":
            d, imm = _reg(pos[0]), _imm(pos[1], sym)
        elif mnem == "CSR_RD":                  # Sd, CSRNAME
            d, imm = _reg(pos[0]), CSR[pos[1].upper()]
        elif mnem == "CSR_WR":                  # CSRNAME, Ss
            imm, s1 = CSR[pos[0].upper()], _reg(pos[1])
        elif mnem == "LOOP":                    # count, body_len
            imm, d = _imm(pos[0], sym), _imm(pos[1], sym)
        elif mnem == "PKMAX":
            s1 = _reg(pos[0])
        elif mnem == "PKOUT":                   # offset
            imm = _imm(pos[0], sym)
        elif mnem == "SYNC":
            imm = _imm(pos[0], sym) if pos else 0
        elif mnem in ("PKCLR", "IRQ", "NOP", "HALT"):
            pass
        else:
            raise ValueError(f"unknown mnemonic {mnem}")
        prog.append({"op": mnem, "d": d, "s1": s1, "s2": s2, "imm": imm & 0xFFF,
                     "raw_imm": imm, "text": line, "phase": phase,
                     "word": encode(mnem, d, s1, s2, imm)})
    return prog


# ---------------------------------------------------------------- microprogram (B=128, L=64)
def microprogram(B=128, L=64):
    assert B == 128 and L == 64, "this hand-unrolled listing is for B=128, L=64"
    sym = dict(B=B, L=L, CT=L // 2, X_RING=X_RING, D_RING=D_RING, W_BASE=W_BASE,
               Y_BASE=Y_BASE, E_BASE=E_BASE, G_BASE=G_BASE, LOG2B=B.bit_length() - 1)
    vld_e = "\n".join(f"        VLD     V{i}, [A2]+16" for i in range(8))
    wld_8 = "\n".join(f"        WLD     W{i}, [A0]+16" for i in range(8))
    vmac_8 = "\n".join(f"          VMAC{'.C' if i == 0 else ''}  W{i}, V{i}" for i in range(8))
    src = f"""
; ================= per-block microprogram, one pass per block =================
        SYNC    1                       ; stall until the input writer has a full new block
        AGU_SET A7, A7, 0, circ=1       ; A7 = block base, kept circular inside the 512-word ring
        CSR_RD  S0, MU                  ; S0 = mu (Q1.15)
; ---- Phase 1: y = X w   (row i = x_full[i+1 .. i+L], w stored reversed) ----
        AGU_SET A2, ZERO, W_BASE
        VLD     V4, [A2]+16
        VLD     V5, [A2]+16
        VLD     V6, [A2]+16
        VLD     V7, [A2]+16             ; w_rev resident in V4..V7
        AGU_SET A0, A7, X_RING, circ=1  ; A0 -> x_full[1] of this block (16-aligned)
        WLD     W0, [A0]+16
        WLD     W1, [A0]+16
        WLD     W2, [A0]+16
        WLD     W3, [A0]+16             ; window = x_full[1..64], A0 -> x_full[65]
        AGU_SET A3, ZERO, Y_BASE
        LOOP    B, 7
          VMAC.C  W0, V4, sh=7          ; VACC  = x * (w >> 7)   (Q2.30 -> Q2.23 on 25-bit port)
          VMAC    W1, V5, sh=7
          VMAC    W2, V6, sh=7
          VMAC    W3, V7, sh=7
          VREDUCE S1, sh=23, rnd=1, sat16=1   ; y[i] in Q1.15
          WSLIDE  [A0], len=L           ; window <- next row (one new sample)
          SST     S1, [A3]+1
; ---- Phase 2: e = d_delayed - y ----
        AGU_SET A1, A7, D_RING, circ=1  ; A1 -> d_delayed[0]
        AGU_SET A3, ZERO, Y_BASE
        AGU_SET A2, ZERO, E_BASE
        LOOP    B/16, 4
          VLD     V0, [A1]+16
          VLD     V1, [A3]+16
          VSUB    V0, V0, V1, sat16=1
          VST     V0, [A2]+16
; ---- Phase 3: g_rev = X^T e   (column k = x_full[k+1 .. k+B]) ----
        AGU_SET A2, ZERO, E_BASE
{vld_e}
        AGU_SET A0, A7, X_RING, circ=1
{wld_8}
        AGU_SET A3, ZERO, G_BASE
        LOOP    L, 11
{vmac_8}
          VREDUCE S1, sh=LOG2B          ; mean gradient (divide by B is the shift), Q2.30
          WSLIDE  [A0], len=B
          SST     S1, [A3]+1
; ---- Phase 4: w_rev += mu * g ----
        AGU_SET A2, ZERO, G_BASE
        AGU_SET A3, ZERO, W_BASE
        LOOP    L/16, 5
          VLD     V0, [A2]+16
          VLD     V1, [A3]+0
          VSCALE  V0, V0, S0, pre=7, post=8
          VADD    V1, V1, V0
          VST     V1, [A3]+16
; ---- Phase 5: tau = argmax|w_rev| - (L-1-CT) ----
        AGU_SET A3, ZERO, W_BASE
        PKCLR
        LOOP    L/16, 2
          VLD     V0, [A3]+16
          PKMAX   V0
        PKOUT   L-1-CT                  ; CSR[TAU_pe] = k* - (L-1-CT)
        AGU_ADD A7, B                   ; next block base (wraps inside the ring)
        IRQ
        HALT
"""
    return assemble(src, sym), src


# ---------------------------------------------------------------- machine
LAT = {"VLD": 2, "WLD": 2, "SLD": 2, "WSLIDE": 2, "VMAC": 3, "VSCALE": 3, "VMUL": 3,
       "VREDUCE": 5, "PKMAX": 5, "SDIV": 34}   # result latency in cycles; everything else is 1


def sat(v, bits):
    lo, hi = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
    return np.clip(v, lo, hi)


class Cluster:
    def __init__(self, B, L, mu):
        self.B, self.L = B, L
        self.mem = np.zeros((NPE, MEM_WORDS), dtype=np.int64)
        self.V = np.zeros((NPE, 8, VLEN), dtype=np.int64)
        self.VACC = np.zeros((NPE, VLEN), dtype=np.int64)
        self.WIN = np.zeros((NPE, WLEN), dtype=np.int64)
        self.S = np.zeros((NPE, 9), dtype=np.int64)        # S0..S7 + constant zero at index 8
        self.A = np.zeros(9, dtype=np.int64)               # A0..A7 (shared AGU) + zero
        self.circ = np.zeros(9, dtype=bool)
        self.pk_val = np.zeros(NPE, dtype=np.int64)
        self.pk_idx = np.zeros(NPE, dtype=np.int64)
        self.pk_ctr = 0
        self.csr = np.zeros(16, dtype=np.int64)
        self.csr[CSR["MU"]], self.csr[CSR["B"]], self.csr[CSR["L"]] = int(round(mu * 32768)), B, L
        self.csr[CSR["XOFF"]], self.csr[CSR["DOFF"]] = L - 1, L // 2
        self.csr[CSR["VERSION"]] = 0x0101
        self.tau = np.zeros(NPE, dtype=np.int64)
        self.t_in = 0              # input samples written
        self.blocks_done = 0
        self.cycles = 0
        self.irq = False

    # --- input writer: one AXI4-Stream beat = {mic4, mic3, mic2, mic1} ---
    def stream_in(self, beats_q15):
        for m1, m2, m3, m4 in beats_q15:
            xa = X_RING + ((self.t_in + self.csr[CSR["XOFF"]]) & (RING - 1))
            da = D_RING + ((self.t_in + self.csr[CSR["DOFF"]]) & (RING - 1))
            self.mem[:, xa] = (m2, m3, m4)       # PE p gets mic p+2
            self.mem[:, da] = m1                 # reference mic broadcast to all PEs
            self.t_in += 1
        self.csr[CSR["SAMPLES_IN"]] = self.t_in

    # --- AGU ---
    def ea(self, an):
        p = int(self.A[an])
        if self.circ[an]:
            base = p & ~(RING - 1)
            return base | (p & (RING - 1))
        return p

    def post_inc(self, an, inc):
        p = int(self.A[an])
        if self.circ[an]:
            base = p & ~(RING - 1)
            self.A[an] = base | ((p + inc) & (RING - 1))
        else:
            self.A[an] = p + inc

    def vsrc(self, code):
        if code >= 8:
            c = code - 8
            return self.WIN[:, c * VLEN:(c + 1) * VLEN]
        return self.V[:, code]

    # --- run one pass of the program (one block) with the timing model ---
    def run(self, prog, phase_of=None):
        pc, loops, ready, cyc = 0, [], {}, 2         # 2 cycles to fill fetch/decode
        self.phase_cycles = {}
        csr_ready_after = 0
        while True:
            ins = prog[pc]
            op = ins["op"]
            reads, writes = self._deps(ins)
            stall = max([ready.get(r, 0) - cyc for r in reads] + [0])
            cyc += stall
            if phase_of is not None:
                ph = phase_of[pc]
                self.phase_cycles[ph] = self.phase_cycles.get(ph, 0) + stall + 1
            self._exec(ins)
            for w in writes:
                ready[w] = cyc + LAT.get(op, 1)
            cyc += 1
            if op == "HALT":
                break
            if op == "LOOP":
                loops.append([pc + 1, pc + ins["d"], ins["raw_imm"]])
            # zero-overhead loop-back
            nxt = pc + 1
            while loops and pc == loops[-1][1]:
                if loops[-1][2] > 1:
                    loops[-1][2] -= 1
                    nxt = loops[-1][0]
                    break
                loops.pop()
            pc = nxt
        self.cycles += cyc
        self.blocks_done += 1
        return cyc

    def _deps(self, ins):
        op, d, s1, s2 = ins["op"], ins["d"], ins["s1"], ins["s2"]
        V = lambda c: ("W", c - 8) if c >= 8 else ("V", c)
        if op == "VMAC":
            # DSP48E1 accumulates through its internal P feedback, so VMAC -> VMAC needs no stall;
            # only VREDUCE has to wait for the 3-stage DSP pipeline to drain.
            return [V(s1), V(s2)], [("VACC",)]
        if op in ("VSUB", "VADD", "VMUL"):
            return [V(s1), V(s2)], [V(d)]
        if op == "VSCALE":
            return [V(s1), ("S", s2)], [V(d)]
        if op in ("VABS",):
            return [V(s1)], [V(d)]
        if op == "VMOV":
            return ([("S", s2)] if ins["imm"] & 1 else [V(s1)]), [V(d)]
        if op == "VREDUCE":
            return [("VACC",)], [("S", d)]
        if op == "VLD":
            return [], [("V", d)]
        if op == "WLD":
            return [], [("W", d)]
        if op == "WSLIDE":
            return [], [("W", c) for c in range(8)]
        if op == "SLD":
            return [], [("S", d)]
        if op == "VST":
            return [V(s2)], []
        if op == "SST":
            return [("S", s2)], []
        if op in ("SADD", "SSUB", "SMUL"):
            return [("S", s1), ("S", s2)], [("S", d)]
        if op == "SDIV":
            return [("S", s1), ("S", s2)], [("S", d)]
        if op == "SMOV":
            return [("S", s1)], [("S", d)]
        if op in ("SIMM", "CSR_RD"):
            return [], [("S", d)]
        if op == "CSR_WR":
            return [("S", s1)], []
        if op == "PKMAX":
            return [V(s1)], [("PK",)]
        if op == "PKOUT":
            return [("PK",)], []
        return [], []

    def _exec(self, ins):
        op, d, s1, s2, imm, raw = ins["op"], ins["d"], ins["s1"], ins["s2"], ins["imm"], ins["raw_imm"]
        simm = raw if raw < 2048 else raw - 4096                 # sign-extended IMM12
        if op == "VMAC":
            a = self.vsrc(s1)                                    # 16-bit sample / window side (18-bit B port)
            b = self.vsrc(s2) >> ((imm >> 1) & 0xF)              # 25-bit A port after optional shift
            prod = a * b
            self.VACC = prod if imm & 1 else self.VACC + prod
        elif op == "VSUB":
            self.V[:, d] = sat(self.vsrc(s1) - self.vsrc(s2), 16 if imm & 1 else 32)
        elif op == "VADD":
            self.V[:, d] = sat(self.vsrc(s1) + self.vsrc(s2), 16 if imm & 1 else 32)
        elif op == "VMUL":
            self.V[:, d] = sat((self.vsrc(s1) * self.vsrc(s2)) >> (imm & 31), 32)
        elif op == "VSCALE":
            pre, post = imm & 0xF, (imm >> 4) & 0x1F
            self.V[:, d] = sat(((self.vsrc(s1) >> pre) * self.S[:, s2][:, None]) >> post, 32)
        elif op == "VABS":
            self.V[:, d] = sat(np.abs(self.vsrc(s1)), 32)
        elif op == "VMOV":
            self.V[:, d] = np.repeat(self.S[:, s2][:, None], VLEN, 1) if imm & 1 else self.vsrc(s1)
        elif op == "VREDUCE":
            sh, rnd, s16 = imm & 31, (imm >> 5) & 1, (imm >> 6) & 1
            tot = self.VACC.sum(axis=1)
            if rnd and sh:
                tot = tot + (1 << (sh - 1))
            self.S[:, d] = sat(tot >> sh, 16 if s16 else 32)
        elif op in ("VLD", "WLD"):
            a = self.ea(s1)
            assert a % VLEN == 0, f"unaligned vector access at {a:#x}: {ins['text']}"
            data = self.mem[:, a:a + VLEN]
            if op == "VLD":
                self.V[:, d] = data
            else:
                self.WIN[:, d * VLEN:(d + 1) * VLEN] = sat(data, 16)
            self.post_inc(s1, simm)
        elif op == "VST":
            a = self.ea(s1)
            assert a % VLEN == 0, f"unaligned vector access at {a:#x}: {ins['text']}"
            self.mem[:, a:a + VLEN] = self.vsrc(s2)
            self.post_inc(s1, simm)
        elif op == "SLD":
            self.S[:, d] = self.mem[:, self.ea(s1)]
            self.post_inc(s1, simm)
        elif op == "SST":
            self.mem[:, self.ea(s1)] = self.S[:, s2]
            self.post_inc(s1, simm)
        elif op == "WSLIDE":
            n = raw
            self.WIN[:, :n - 1] = self.WIN[:, 1:n].copy()
            self.WIN[:, n - 1] = sat(self.mem[:, self.ea(s1)], 16)
            self.post_inc(s1, 1)
        elif op == "AGU_SET":
            self.A[d] = (0 if s1 == ZERO else self.A[s1]) + raw
            self.circ[d] = bool(s2 & 1)
        elif op == "AGU_ADD":
            self.post_inc(d, simm)
        elif op == "SADD":
            self.S[:, d] = sat(self.S[:, s1] + self.S[:, s2] + simm, 32)
        elif op == "SSUB":
            self.S[:, d] = sat(self.S[:, s1] - self.S[:, s2] + simm, 32)
        elif op == "SMUL":
            self.S[:, d] = sat(self.S[:, s1] * self.S[:, s2], 32)
        elif op == "SDIV":                                        # iterative divider, used once per block (NLMS)
            den = np.where(self.S[:, s2] == 0, 1, self.S[:, s2])
            self.S[:, d] = sat(np.floor_divide(self.S[:, s1] << (imm & 31), den), 32)
        elif op == "SMOV":
            self.S[:, d] = self.S[:, s1]
        elif op == "SIMM":
            self.S[:, d] = simm
        elif op == "CSR_RD":
            self.S[:, d] = self.csr[imm & 15]
        elif op == "CSR_WR":
            self.csr[imm & 15] = self.S[0, s1]
        elif op == "PKCLR":
            self.pk_val[:], self.pk_idx[:], self.pk_ctr = -1, 0, 0
        elif op == "PKMAX":
            v = np.abs(self.vsrc(s1))
            li = np.argmax(v, axis=1)                             # comparator tree, lower lane wins ties
            lv = v[np.arange(NPE), li]
            upd = lv > self.pk_val
            self.pk_val = np.where(upd, lv, self.pk_val)
            self.pk_idx = np.where(upd, self.pk_ctr + li, self.pk_idx)
            self.pk_ctr += VLEN
        elif op == "PKOUT":
            self.tau = self.pk_idx - simm
            self.csr[CSR["TAU21"]:CSR["TAU41"] + 1] = self.tau
        elif op == "IRQ":
            self.irq = True
        elif op in ("SYNC", "LOOP", "NOP", "HALT"):
            pass                                                 # SYNC 1 is satisfied by the caller
        else:
            raise NotImplementedError(op)


# ---------------------------------------------------------------- verification against the fixed-point model
def main():
    import os, contextlib, io
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    from realtime_simulation import generate_moving_source_signals
    from fixed_point_model import FixedPointBlockLMS, to_q15

    nblocks = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    B, L, MU = 128, 64, 0.05
    prog, _ = microprogram(B, L)
    print(f"microprogram: {len(prog)} instructions ({len(prog) * 4} bytes of IMEM)")

    with contextlib.redirect_stdout(io.StringIO()):
        fs, mics, _ = generate_moving_source_signals("source2.wav")
    q = to_q15(mics)
    start = int(20 * fs)                   # start 20 s into the recording (plenty of signal)
    cl = Cluster(B, L, MU)
    ref = [FixedPointBlockLMS(L, B, MU, 32) for _ in range(3)]
    mism, cyc = 0, []
    for b in range(nblocks):
        s = start + b * B
        cl.stream_in(q[:, s:s + B].T)
        assert cl.t_in - cl.blocks_done * B >= B      # SYNC 1 condition
        cyc.append(cl.run(prog, [i["phase"] for i in prog]))
        t_ref = [ref[p].process_block(q[p + 1, s:s + B], q[0, s:s + B]) for p in range(3)]
        w_hw = np.stack([cl.mem[p, W_BASE:W_BASE + L] for p in range(3)])
        w_ref = np.stack([r.w_rev for r in ref])
        if not (np.array_equal(cl.tau, t_ref) and np.array_equal(w_hw, w_ref)):
            mism += 1
            if mism < 4:
                print(f"block {b}: tau hw={cl.tau.tolist()} ref={t_ref}  max|dw|={np.abs(w_hw - w_ref).max()}")
    print(f"{nblocks} blocks: {nblocks - mism} bit-exact matches (tau AND all 64 weights, 3 PEs), {mism} mismatches")
    print(f"cycles per block: {cyc[0]} (constant: {len(set(cyc)) == 1})  per phase: {cl.phase_cycles}")
    print(f"final tau = {cl.tau.tolist()}")


if __name__ == "__main__":
    main()
