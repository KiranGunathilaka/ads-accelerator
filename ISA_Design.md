# ISA Design for the Block-LMS SIMD Accelerator
### Sound Source Localization — TDOA via Centered Block-LMS

**Document Version:** 1.1
**Authors:** Rakindu (v1.0: algorithm mapping, ISA draft) · Kiran Gunathilaka (v1.1: memory addressing, fetch/control, microarchitecture, verification)
**Project:** ADS Semester 7 — SIMD Processor Design
**Target:** Digilent Zybo (Zynq-7000: Cortex-A9 PS + 7-series PL with DSP48E1), accelerator written as vendor-neutral Verilog behind standard AXI interfaces
**Reference Paper:** Mahmood & Al-Jbaar, "Design and implementation of SIMD Vector Processor on FPGA," IEEE ISIICT 2011

---

## Changelog v1.0 → v1.1

Every item below was found by checking v1.0 against `simulation_py/realtime_simulation.py` (the golden model) and then confirmed with the new instruction-level simulator (`simulation_py/isa_sim.py`).

| # | v1.0 problem | Evidence | v1.1 fix |
|---|---|---|---|
| 1 | No way to loop: the listings use `LOOP_DEC`, but it is not in the opcode table and all 32 opcodes were taken. | §8 listings vs §6 table | `LOOP count, len` — zero-overhead hardware loop (2-level loop stack in the control unit). |
| 2 | `VST_S` (scalar store) used in Phases 1 and 3 but not defined. | §8.2, §8.4 | `SST` / `SLD` scalar memory ops. |
| 3 | AGU pointers cannot be selected: 7 pointers are used (`x_ptr`, `w_ptr`, `d_ptr`, `y_ptr`, `e_ptr`, `g_ptr`, `col_ptr`) but `AGU_SET`/`AGU_INC`/`VLD` have no pointer field, so three consecutive `AGU_SET`s overwrite each other. | §8.3 | Eight address registers A0–A7; every load/store names one and post-increments it. |
| 4 | X indexing wrong. `X[i] = x_full[i+L : i : -1]` is **reversed**, so row i is `x_full[i+L … i+1]` and column j starts at `x_full[L−j]`, not `x_full[j]`. Phase 1 read x and w both ascending from `x_full[0]`. | Simulated v1.0's access pattern: reports **+7** where the golden model gives **−7** (sign flipped). | Store w reversed (`w_rev[k] = w[L−1−k]`). Then row i = `x_full[i+1 … i+L]` and column k = `x_full[k+1 … k+B]`: both ascending, both start at `x_full[1]`. |
| 5 | A 16-element load from an *arbitrary* offset (the sliding window) cannot come out of one BRAM port in 1–2 cycles. | §8.2 cycle table | 16 banks (one per lane) + **aligned-only** vector access + a sliding-window shift register (`WLD`/`WSLIDE`). No rotator or crossbar. |
| 6 | Memory map: `d_delayed = [d_hist | d_block[0:96]]` is not contiguous (d_hist at 0xC00, d_del at 0x300); the ping-pong buffers promised in §9 do not fit in the 896 B left; `x_hist` duplicates the head of `x_full`. | §4.1, §9 | Two 512-word **circular rings** (X, D) with hardware modulo addressing: history stays in place, no copies, DMA fills block n+1 while n is processed. |
| 7 | Register encoding: tag `10` = CSR with index in bits [3:0] — but bit 3 is part of the tag, so only 8 of 16 CSRs are reachable. | §5.2 | Operand fields are typed by the opcode; the CSR index lives in IMM12. |
| 8 | `SACC_CLR V2` clears a vector register with a scalar-only instruction. | §8.2 | `VMAC.C` clears the accumulator as part of the first multiply (DSP48 OPMODE). |
| 9 | float32 datapath on DSP48 slices, which are integer multipliers. | §13.3 | Fixed-point formats (§4.4), verified: fixed-point τ = float τ on 99.6 % of blocks. |
| 10 | Timing assumed fs = 16 kHz and ~7 400 cycles. `source2.wav` is **48 kHz**. | `wav.read` | Measured **2 695 cycles/block** (27 µs @ 100 MHz) against a 2 667 µs block period. |
| 11 | "ARM has almost no headroom" (§1.2) — at B=128, L=64, 48 kHz the load is ≈ 18 M MAC/s, which a Cortex-A9 can sustain. | arithmetic | §1.2 rewritten: the case is deterministic latency, freeing the PS, and headroom to scale L / pairs / fs. |
| 12 | "DSP48E2" with a Cortex-A9: DSP48E2 is UltraScale; Zynq-7000 has DSP48E1 (25 × 18, 48-bit P). | datasheets | DSP48E1 throughout. |
| 13 | `PKIDX_OUT` computes `center_tap − peak_idx` after `SSUB` already did (double subtraction). | §8.6 | `PKOUT imm` writes `k* − imm` once, with imm = L−1−L/2 for the reversed weights. |
| 14 | `d_block` must reach all 3 PEs (§13.6 proposed a future `VNET_RCV`). | §13.6 | The input writer broadcasts mic1 into every PE's D ring as it streams in. |
| 15 | IRQ cleared by `CTRL.RESET`, but RESET also resets AGU pointers, which now hold the ring position. | §12 | IRQ cleared by writing 1 to `STATUS.DONE`; soft reset is separate. |
| 16 | μ = 0.05 with μ/B lags the moving source by ≈ 3.7 s (47 % of blocks within ±1 sample). | `tracking_study.py` | μ is a CSR: μ = 0.5 → 85.6 %; block-NLMS (μ = 0.64) → 88 %. `SDIV` kept for NLMS normalisation. |

---

## Table of Contents

1. [System Overview & Motivation](#1-system-overview--motivation)
2. [The Algorithm: What the Hardware Must Do](#2-the-algorithm-what-the-hardware-must-do)
3. [Processor Cluster Architecture Summary](#3-processor-cluster-architecture-summary)
4. [Memory Map, Addressing & Register Files](#4-memory-map-addressing--register-files)
5. [Instruction Format](#5-instruction-format)
6. [Instruction Set — Complete Opcode Table](#6-instruction-set--complete-opcode-table)
7. [Instruction Descriptions — Detailed Semantics](#7-instruction-descriptions--detailed-semantics)
8. [Microprogram (Phase-by-Phase)](#8-microprogram-phase-by-phase)
9. [Execution Flow & Streaming](#9-execution-flow--streaming)
10. [Timing, Latency, and Throughput](#10-timing-latency-and-throughput)
11. [Control & Status Registers (CSRs)](#11-control--status-registers-csrs)
12. [Interrupt & Handshake Protocol](#12-interrupt--handshake-protocol)
13. [Microarchitecture](#13-microarchitecture)
14. [Verification](#14-verification)
15. [Open Items](#15-open-items)

---

## 1. System Overview & Motivation

### 1.1 The Application Context

The application estimates the **Time Difference of Arrival (TDOA)** of a sound source using **four microphones** in a 3D tetrahedron (10 cm spacing). Mic 1 is the reference. Three independent centered Block-LMS adaptive filters estimate the delay of each other mic relative to Mic 1:

| Filter | Signal `x` | Reference `d` | Output | Runs on |
|--------|-----------|---------------|--------|---------|
| LMS-21 | Mic 2 | Mic 1 | τ21 (samples) | PE0 |
| LMS-31 | Mic 3 | Mic 1 | τ31 | PE1 |
| LMS-41 | Mic 4 | Mic 1 | τ41 | PE2 |

The C program on the ARM reads τ21, τ31, τ41 and solves the hyperbolic (TDOA) equations for the 3D position.

At 48 kHz and 10 cm spacing the largest possible delay is 0.1 m / 343 m/s × 48 000 ≈ **14 samples**, well inside the ±32-sample range of a 64-tap centered filter.

### 1.2 The Computational Problem

Per block of B samples, each filter does:

| Phase | Operation | Work (B=128, L=64) |
|-------|-----------|------------|
| 1 Filter | `y = X w`, X is B×L | 8 192 MACs |
| 2 Error | `e = d_delayed − y` | 128 subtracts |
| 3 Gradient | `g = Xᵀ e` | 8 192 MACs |
| 4 Update | `w += (μ/B) g` | 64 MACs |
| 5 Peak | `argmax |w|` | 64 compares |

Three filters at 48 kHz: 3 × 2 × L × fs ≈ **18.4 M MAC/s**. That is within reach of a Cortex-A9 in software, so the accelerator is **not** justified by raw throughput at these parameters. It is justified by:

- **Deterministic latency** — 27 µs per block, independent of OS scheduling.
- **Freeing the PS** for triangulation, tracking and I/O.
- **Headroom** — the cluster is busy 1 % of the block period, so longer filters (L = 256), more mic pairs, or higher sample rates fit without new hardware.
- It is a clean example of data-level parallelism for the course: one instruction stream, 3 × 16 lanes.

### 1.3 Why Three SIMD Processors?

The three filters are independent and share only the reference `d`. One control unit broadcasts **one instruction and one memory address** per cycle; three PEs execute them on their own data (Mic 2/3/4). Each PE is itself 16 lanes wide, so every `VMAC` performs 48 multiply-accumulates.

```
                  ARM Cortex-A9 (C driver)
                  │ AXI4-Lite (M_AXI_GP0)           ▲ IRQ_F2P
                  ▼                                 │
      ┌──────────────────────────── SIMD cluster ───────────────────────┐
DDR → │ AXI DMA ─AXI4-Stream→ Input writer ──┐      Control unit (shared)│
(HP0) │                                      │  IMEM→Fetch→Decode→AGU    │
      │                                      ▼        │ control word + address
      │                  ┌──── PE0 (Mic2) ◄──┴────────┤ (broadcast)
      │                  ├──── PE1 (Mic3) ◄───────────┤
      │                  └──── PE2 (Mic4) ◄───────────┘
      └──────────────────────────────────────────────────────────────────┘
```

---

## 2. The Algorithm: What the Hardware Must Do

Golden model: `RealTimeCenteredNLMS.process_block()` in `simulation_py/realtime_simulation.py`.

```
-- One block (B samples) arrives. L = filter length, CT = L/2 --
INPUT:  x_block[B], d_block[B]
STATE:  w[L]  (persistent), x history (L samples), d history (CT samples)

x_full[L+B] = [x_history | x_block]
d_full[CT+B] = [d_history | d_block];   d_delayed = d_full[0 : B]

X[i, j] = x_full[i+L−j]            (row i = x_full[i+L … i+1], REVERSED)

Phase 1:  y[i] = Σ_j X[i,j] w[j]
Phase 2:  e[i] = d_delayed[i] − y[i]
Phase 3:  g[j] = Σ_i X[i,j] e[i]
Phase 4:  w[j] += (μ/B) g[j]
Phase 5:  τ = CT − argmax_j |w[j]|
```

**Hardware form (v1.1).** Store `w_rev[k] = w[L−1−k]`. Substituting j = L−1−k:

```
y[i]      = Σ_k x_full[i+1+k] · w_rev[k]     row i    = x_full[i+1 … i+L]   (ascending)
g_rev[k]  = Σ_i x_full[k+1+i] · e[i]         column k = x_full[k+1 … k+B]   (ascending)
w_rev    += μ · g_rev / B                    (element-wise, order-independent)
τ         = k* − (L−1−CT)      where k* = argmax_k |w_rev[k]|    (= k* − 31 for L = 64)
```

Both phases read unit-stride windows that start at `x_full[1]` and move by **one sample** per row / column. This is what the sliding-window register (§4.3) exploits. `x_full[0]` is never used.

---

## 3. Processor Cluster Architecture Summary

| Unit | Where | Size | Purpose |
|------|-------|------|---------|
| AXI4-Lite slave | cluster | 16 CSRs + IMEM window | ARM configures, loads program, reads τ |
| Input writer | cluster | AXI4-Stream slave, 64-bit | Unpacks {mic4,mic3,mic2,mic1}; writes rings; counts samples |
| Control unit | cluster (shared) | IMEM 512×32, PC, 2-level loop stack, scoreboard | Fetch / decode / issue, broadcast |
| AGU | cluster (shared) | A0–A7 (13-bit + circular flag) | Post-increment, modulo-512 ring addressing |
| Local data memory | per PE | 16 banks × 512 × 32 bit (16 BRAM18) | Rings, w_rev, y, e, g |
| Sliding-window register WIN | per PE | 128 × 16 bit shift register | Current row / column of X |
| VRF | per PE | 8 × 16 lanes × 32 bit | w chunks, e chunks, temporaries |
| MAC lanes | per PE | 16 × DSP48E1 (25×18, 48-bit P) | `VMAC`, `VSCALE`, `VMUL`; P register = accumulator VACC |
| Adder tree | per PE | 16→1, 4 pipelined stages + round/shift/saturate | `VREDUCE` |
| Vector ALU | per PE | 16 × 32-bit, saturating | `VADD`, `VSUB`, `VABS`, `VMOV` |
| Peak detector | per PE | 16-input comparator tree + running max/index | `PKMAX`, `PKOUT` |
| Scalar unit | per PE | S0–S7 (32 bit), add/sub/mul/div | results, μ, loop-invariant scalars |

**VLEN = 16** lanes per PE; **3 PEs** → 48 MACs per `VMAC`.

---

## 4. Memory Map, Addressing & Register Files

### 4.1 Local Data Memory (per PE)

Word-addressed (one word = 32 bits). **16 banks, one per lane, word-interleaved:** word address `a` lives in bank `a mod 16`, row `a / 16`. Every vector access (`VLD`, `VST`, `WLD`) must be **16-aligned**, so it reads or writes exactly one row across all 16 banks in one cycle — no rotator or crossbar. Scalar accesses (`SST`, `SLD`, the single sample of `WSLIDE`) touch one bank (per-bank write enables, 16:1 read mux).

Each bank is one BRAM18 in simple-dual-port 512 × 36 mode → 8 192 words (32 KB) per PE. The map below uses 1 408 words (B = 128, L = 64); the rest is free for larger B and L.

| Region | Base | Words | Contents | Written by |
|--------|------|-------|----------|-----------|
| X ring | 0x000 | 512 | this PE's mic (x), circular | input writer |
| D ring | 0x200 | 512 | Mic 1 (d), circular | input writer (broadcast) |
| `w_rev` | 0x400 | 64 | weights, **reversed**, persistent across blocks | Phase 4 |
| `y` | 0x440 | 128 | filter output | Phase 1 |
| `e` | 0x4C0 | 128 | error | Phase 2 |
| `g` | 0x540 | 64 | mean gradient (reversed order) | Phase 3 |
| free | 0x580 | 6 784 | — | — |

Port use: read port = PE; write port = PE stores, or the input writer when the PE is not storing. The PE has priority and the input writer stalls through AXI4-Stream back-pressure (`TREADY` low). Audio arrives at 48 kHz against a 100 MHz clock, so this never limits throughput.

### 4.2 Circular X / D Rings (replaces x_hist, d_hist and ping-pong buffers)

The input writer keeps a sample counter t and writes

```
X ring:  M[X_RING + ((t + XOFF) mod 512)] = mic(p+2)[t]      XOFF = L − 1  (CSR)
D ring:  M[D_RING + ((t + DOFF) mod 512)] = mic1[t]          DOFF = L / 2  (CSR, = center tap)
```

For block n, the block base is `A7 = (n·B) mod 512`. Then:

- `x_full[1]` of block n is at `X_RING + A7` (16-aligned because B is a multiple of 16), and `x_full[j]` at `X_RING + ((A7 + j − 1) mod 512)`.
- `d_delayed[0]` is at `D_RING + A7`: the center-tap delay comes for free from DOFF.
- The last L−1 samples of block n are exactly `x_full[1 … L−1]` of block n+1, already in place, so **no history copy is needed**.
- While block n is read (191 words), the DMA fills block n+1 into the next 128 words. The ring has room for the writer to run up to 449 − 128 = 321 samples (≈ 6.7 ms) further ahead before it would overwrite live data. If it gets that far ahead, `TREADY` is held low and `STATUS.OVERRUN` is set.

### 4.3 Sliding-Window Register (WIN)

A 128 × 16-bit shift register per PE (length = max(B, L), a synthesis parameter), readable as eight 16-lane chunks W0–W7:

- `WLD Wc, [An]+16` loads one aligned row into chunk c (fills the window).
- `WSLIDE [An], len=n` shifts elements 0…n−1 left by one and inserts `M[An]` at position n−1, then `An += 1`. This is the next row (Phase 1, n = L) or the next column (Phase 3, n = B).

So after one fill, each row or column costs **one** memory read instead of L or B. This is the "sliding window" box of the v1.0 draw.io diagram, made concrete.

### 4.4 Number Formats

| Quantity | Format | Storage | Notes |
|----------|--------|---------|-------|
| x, d, y, e | Q1.15 | 16-bit, sign-extended in 32-bit words | what the audio codec / WAV provides |
| w (`w_rev`) | Q2.30 | 32-bit | multiplied as Q2.23 (top 25 bits) on the DSP48E1 A port |
| VACC | 48-bit | DSP48E1 P register | Phase 1: Q3.38 · Phase 3: Q9.30 |
| g | Q2.30 | 32-bit | mean gradient: `VREDUCE` shifts by log2 B (divide by B is free) |
| μ | Q1.15 | CSR | 0.05 → 1 638, 0.5 → 16 384 |

16-bit (Q15) weights were also simulated: small updates are lost and accuracy drops (43.4 % vs 47.0 % within ±1 sample at μ = 0.05). That is why w is stored in 32 bits.

### 4.5 Vector Register File (per PE)

8 registers V0–V7, each 16 × 32 bit. No fixed roles; the microprogram uses:

| Phase | Use |
|-------|-----|
| 1 | V4–V7 hold all 64 `w_rev` taps for the whole phase |
| 2 | V0 = d chunk, V1 = y chunk |
| 3 | V0–V7 hold all 128 `e` samples for the whole phase |
| 4 | V0 = g chunk, V1 = w chunk |
| 5 | V0 = w chunk |

The vector accumulator **VACC** (16 × 48 bit) is separate: it is the P register of each lane's DSP48E1.

### 4.6 Scalar Registers (per PE) and Address Registers (shared)

| Register | Use in the microprogram |
|----------|-----|
| S0 | μ (Q1.15), loaded from CSR each block |
| S1 | `VREDUCE` result (y[i] or g[k]) |
| S2–S7 | free |
| A0 | X ring pointer (circular) |
| A1 | D ring pointer (circular) |
| A2, A3 | linear pointers (w_rev, y, e, g) |
| A7 | block base, circular, **persists across blocks** |

Address registers live in the shared AGU because all PEs use the same addresses. Each is 13 bits plus a circular flag; a circular register wraps inside the 512-word aligned region that contains it.

---

## 5. Instruction Format

All instructions are **32 bits**, fixed format → single-cycle decode.

```
 31      27 26    22 21    17 16    12 11              0
 ┌─────────┬────────┬────────┬────────┬────────────────┐
 │ OPCODE  │  DST   │  SRC1  │  SRC2  │     IMM12      │
 │  [5b]   │  [5b]  │  [5b]  │  [5b]  │     [12b]      │
 └─────────┴────────┴────────┴────────┴────────────────┘
```

`OPCODE[4:3]` = group: `00` vector arithmetic, `01` memory/AGU, `10` scalar/loop, `11` control/result.

### 5.1 Operand Fields (typed by the opcode)

| Field kind | Codes | Meaning |
|------------|-------|---------|
| vector source | 0–7 | V0–V7 |
| | 8–15 | W0–W7 (window chunks; `VMAC` SRC1 only) |
| scalar | 0–7 | S0–S7 |
| | 8 | ZERO (reads as 0) |
| address | 0–7 | A0–A7 |
| | 8 | ZERO (for `AGU_SET` base) |
| CSR | — | index in IMM12[3:0] |

This replaces the v1.0 global tag scheme (§5.2 of v1.0), whose CSR tag left only 3 index bits.

---

## 6. Instruction Set — Complete Opcode Table

Orange-highlighted on the slide = new in v1.1.

### 6.1 Group 00 — Vector Arithmetic

| Opcode | Mnemonic | Operation | Fields |
|--------|----------|-----------|--------|
| 00000 | `VMAC` | `VACC (=│+=) SRC1 × (SRC2 >> sh)` | SRC1 ∈ V/W, SRC2 ∈ V, IMM[0] = CLR, IMM[4:1] = sh |
| 00001 | `VSUB` | `Vd = sat(Va − Vb)` | IMM[0] = saturate to 16 bit (else 32) |
| 00010 | `VADD` | `Vd = sat(Va + Vb)` | IMM[0] as above |
| 00011 | `VSCALE` | `Vd = sat(((Va >> pre) × Ss) >> post)` | SRC2 = S, IMM[3:0] = pre, IMM[8:4] = post |
| 00100 | `VABS` | `Vd = │Va│` | |
| 00101 | `VMOV` | `Vd = Va`, or splat `Ss` to all lanes if IMM[0] | |
| 00110 | `VREDUCE` | `Sd = sat(round(Σ VACC >> sh))` | IMM[4:0] = sh, IMM[5] = round, IMM[6] = sat16 |
| 00111 | `VMUL` | `Vd = sat((Va × Vb) >> sh)` | IMM[4:0] = sh |

### 6.2 Group 01 — Memory / AGU

| Opcode | Mnemonic | Operation |
|--------|----------|-----------|
| 01000 | `VLD Vd, [An]+imm` | `Vd = M[An … An+15]` (aligned); `An += sext(imm)` |
| 01001 | `VST Vs, [An]+imm` | `M[An … An+15] = Vs` (aligned); `An += sext(imm)` |
| 01010 | `AGU_SET An, Am│ZERO, imm, circ` | `An = Am + imm`; circular flag = SRC2[0] |
| 01011 | `AGU_ADD An, imm` | `An += sext(imm)` (wraps if circular) |
| 01100 | `WLD Wc, [An]+imm` | window chunk c = low 16 bits of `M[An … An+15]`; `An += imm` |
| 01101 | `WSLIDE [An], len=n` | `WIN[0…n−2] = WIN[1…n−1]; WIN[n−1] = M[An]; An += 1` |
| 01110 | `SST Ss, [An]+imm` | `M[An] = Ss`; `An += imm` |
| 01111 | `SLD Sd, [An]+imm` | `Sd = M[An]`; `An += imm` |

### 6.3 Group 10 — Scalar / Loop

| Opcode | Mnemonic | Operation |
|--------|----------|-----------|
| 10000 | `SMUL` | `Sd = Sa × Sb` |
| 10001 | `SADD` | `Sd = Sa + Sb + sext(imm)` |
| 10010 | `SSUB` | `Sd = Sa − Sb + sext(imm)` |
| 10011 | `SDIV` | `Sd = (Sa << imm) / Sb` — iterative, once per block (NLMS normalisation) |
| 10100 | `SMOV` | `Sd = Sa` |
| 10101 | `SIMM` | `Sd = sext(imm)` |
| 10110 | `CSR_RD` | `Sd = CSR[imm]` |
| 10111 | `LOOP count, len` | repeat the next `len` (DST field, 1–31) instructions `count` (IMM12) times, zero overhead |

### 6.4 Group 11 — Control / Result

| Opcode | Mnemonic | Operation |
|--------|----------|-----------|
| 11000 | `PKMAX Va` | 16-lane │·│ comparator tree vs running max; index counter += 16 |
| 11001 | `PKOUT imm` | `CSR[TAU_pe] = peak_idx − imm` (each PE writes its own τ CSR) |
| 11010 | `SYNC imm` | 0: memory fence · 1: stall until the input writer has a full new block |
| 11011 | `PKCLR` | reset peak detector (max = −1, index = 0, counter = 0) |
| 11100 | `IRQ` | set `STATUS.DONE`; raise `IRQ_F2P` if `CTRL.IRQ_EN` |
| 11101 | `NOP` | |
| 11110 | `HALT` | PC ← 0; wait for `CTRL.START`, or restart at once if `CTRL.AUTO` |
| 11111 | `CSR_WR` | `CSR[imm] = Ss` |

### 6.5 What happened to the v1.0 opcodes

| v1.0 | v1.1 |
|------|------|
| `VSUB_V`, `VADD_V`, `VMOV_V`, `VMUL_V` | renamed `VSUB`, `VADD`, `VMOV`, `VMUL` |
| `AGU_INC` | post-increment on every load/store + `AGU_ADD` |
| `AGU_SLIDE` | `WSLIDE` (moves the window, not just a pointer) |
| `AGU_COL` | removed: with reversed w, columns use the same window as rows |
| `VLD_S` | `SLD` + `VMOV` splat |
| `VLD_CSR` | `CSR_RD` (moved to the scalar group) |
| `SACC_CLR` | `VMAC.C` (vector) / `SIMM Sd, 0` (scalar) |
| `LOOP_SET` (+ undefined `LOOP_DEC`) | `LOOP` |
| `PHASE_END` | `PKCLR` (phase can still be written to `CSR` via `CSR_WR` for debug) |
| `PKIDX_OUT` | `PKOUT` |
| `IRQ_FIRE` | `IRQ` |
| (undefined `VST_S`) | `SST` |
| new | `WLD`, `WSLIDE`, `SLD`, `AGU_ADD` |

---

## 7. Instruction Descriptions — Detailed Semantics

### 7.1 `VMAC` — Vector Multiply-Accumulate
```
VMAC[.C] Va|Wc, Vb [, sh=n]          encoding: 00000 | 00000 | SRC1 | SRC2 | IMM = n<<1 | C
per lane i:  prod = SRC1[i] × (Vb[i] >> n)
             VACC[i] = C ? prod : VACC[i] + prod
```
Maps to one DSP48E1 per lane: SRC1 (a 16-bit sample, usually a window chunk) enters the 18-bit B port, `Vb >> n` (25 bits) the A port, and VACC is the 48-bit P register. `.C` selects OPMODE Z = 0 instead of P. Back-to-back `VMAC`s accumulate every cycle through the internal P feedback. Phase 1 uses `sh=7` to turn Q2.30 weights into Q2.23 for the 25-bit port.

### 7.2 `VREDUCE` — Adder Tree
```
VREDUCE Sd, sh=n [, rnd=1] [, sat16=1]
Sd = saturate( (Σ_i VACC[i] + (rnd ? 2^(n−1) : 0)) >> n )
```
4 pipelined adder stages (16→8→4→2→1, 52-bit) plus one round/shift/saturate stage: result is ready 5 cycles after issue. Phase 1: `sh=23, rnd, sat16` → y in Q1.15. Phase 3: `sh=log2 B` → mean gradient in Q2.30.

### 7.3 `WLD` / `WSLIDE` — Sliding Window
See §4.3. `WSLIDE` reads one word (single bank) and its result is usable 2 cycles later.

### 7.4 `VLD` / `VST` / `SST` / `SLD` — Memory with Post-Increment
The AGU supplies `An` as the address and adds the signed IMM12 afterwards. Vector accesses assert if the address is not 16-aligned (the program never issues one). If An is circular, the increment wraps within its 512-word region.

### 7.5 `AGU_SET` / `AGU_ADD`
`AGU_SET A0, A7, X_RING, circ=1` makes A0 point at `x_full[1]` of the current block. `AGU_ADD A7, B` advances the block base at the end of each block.

### 7.6 `LOOP` — Zero-Overhead Hardware Loop
`LOOP count, len` pushes {start = PC+1, end = PC+len, count} onto a 2-entry loop stack. When the fetch PC reaches `end` and count > 1, the next fetch PC is `start` with no bubble. This is the missing `LOOP_DEC` of v1.0; there are no branch instructions, because the program's control flow is completely regular.

### 7.7 `PKMAX` / `PKOUT` — Peak Detection
`PKMAX V0` finds the lane with the largest │V0[i]│ (4-stage comparator tree, lower lane wins ties) and compares it with the running max (strict `>`, so the earliest index wins — same as `numpy.argmax`). After L/16 calls, `PKOUT 31` writes `k* − 31` = τ into this PE's τ CSR.

### 7.8 `SYNC 1` — Wait for Data
Stalls issue until `SAMPLES_IN ≥ (blocks_done + 1) · B`. Together with `HALT` + `CTRL.AUTO`, the cluster free-runs: every new block starts automatically.

---

## 8. Microprogram (Phase-by-Phase)

The complete per-block program for B = 128, L = 64: **78 instructions (312 bytes of IMEM)**. It is generated and run by `simulation_py/isa_sim.py`; the encodings below are its output.

```asm
; ---- Phase 0: wait + setup ----
  0 D0000001  SYNC    1                       ; wait for a full new block
  1 51CE1000  AGU_SET A7, A7, 0, circ=1       ; A7 = block base, circular in the 512-word ring
  2 B0000002  CSR_RD  S0, MU                  ; S0 = mu (Q1.15)
; ---- Phase 1: y = X w  (row i = x_full[i+1 .. i+L]) ----
  3 50900400  AGU_SET A2, ZERO, W_BASE
  4 41040010  VLD     V4, [A2]+16             ; w_rev[0..15]
  5 41440010  VLD     V5, [A2]+16
  6 41840010  VLD     V6, [A2]+16
  7 41C40010  VLD     V7, [A2]+16             ; w_rev resident in V4..V7
  8 500E1000  AGU_SET A0, A7, X_RING, circ=1  ; A0 -> x_full[1]
  9 60000010  WLD     W0, [A0]+16
 10 60400010  WLD     W1, [A0]+16
 11 60800010  WLD     W2, [A0]+16
 12 60C00010  WLD     W3, [A0]+16             ; WIN = x_full[1..64], A0 -> x_full[65]
 13 50D00440  AGU_SET A3, ZERO, Y_BASE
 14 B9C00080  LOOP    128, 7
 15 0010400F    VMAC.C  W0, V4, sh=7
 16 0012500E    VMAC    W1, V5, sh=7
 17 0014600E    VMAC    W2, V6, sh=7
 18 0016700E    VMAC    W3, V7, sh=7
 19 30400077    VREDUCE S1, sh=23, rnd=1, sat16=1   ; y[i]
 20 68000040    WSLIDE  [A0], len=64                ; next row
 21 70061001    SST     S1, [A3]+1
; ---- Phase 2: e = d_delayed - y ----
 22 504E1200  AGU_SET A1, A7, D_RING, circ=1  ; A1 -> d_delayed[0]
 23 50D00440  AGU_SET A3, ZERO, Y_BASE
 24 509004C0  AGU_SET A2, ZERO, E_BASE
 25 B9000008  LOOP    8, 4
 26 40020010    VLD     V0, [A1]+16
 27 40460010    VLD     V1, [A3]+16
 28 08001001    VSUB    V0, V0, V1, sat16=1
 29 48040010    VST     V0, [A2]+16
; ---- Phase 3: g_rev = X^T e  (column k = x_full[k+1 .. k+B]) ----
 30 509004C0  AGU_SET A2, ZERO, E_BASE
 31-38        VLD     V0..V7, [A2]+16         ; e resident in V0..V7
 39 500E1000  AGU_SET A0, A7, X_RING, circ=1
 40-47        WLD     W0..W7, [A0]+16         ; WIN = x_full[1..128]
 48 50D00540  AGU_SET A3, ZERO, G_BASE
 49 BAC00040  LOOP    64, 11
 50 00100001    VMAC.C  W0, V0
 51-57          VMAC    W1..W7, V1..V7
 58 30400007    VREDUCE S1, sh=7              ; mean gradient (÷B by shift), Q2.30
 59 68000080    WSLIDE  [A0], len=128         ; next column
 60 70061001    SST     S1, [A3]+1
; ---- Phase 4: w_rev += mu * g ----
 61 50900540  AGU_SET A2, ZERO, G_BASE
 62 50D00400  AGU_SET A3, ZERO, W_BASE
 63 B9400004  LOOP    4, 5
 64 40040010    VLD     V0, [A2]+16
 65 40460000    VLD     V1, [A3]+0
 66 18000087    VSCALE  V0, V0, S0, pre=7, post=8
 67 10420000    VADD    V1, V1, V0
 68 48061010    VST     V1, [A3]+16
; ---- Phase 5: tau = argmax|w_rev| - (L-1-CT) ----
 69 50D00400  AGU_SET A3, ZERO, W_BASE
 70 D8000000  PKCLR
 71 B8800004  LOOP    4, 2
 72 40060010    VLD     V0, [A3]+16
 73 C0000000    PKMAX   V0
 74 C800001F  PKOUT   31                      ; CSR[TAU_pe] = k* - 31
 75 59C00080  AGU_ADD A7, 128                 ; next block base
 76 E0000000  IRQ
 77 F0000000  HALT
```

The Phase 1 and Phase 3 bodies are hand-unrolled for L/16 = 4 and B/16 = 8. Larger B or L need either the 2-level loop stack or, when w or e no longer fit in 8 vector registers (L > 128 or B > 128), one `VLD` per `VMAC`.

---

## 9. Execution Flow & Streaming

```
ARM (once):   load IMEM · write μ, B, L, XOFF, DOFF · CTRL = SRESET, then IRQ_EN | AUTO | START
ARM (per block of audio): flush D-cache · start AXI DMA (MM2S) → AXI4-Stream → input writer
Cluster:      SYNC 1 → P0 … P5 → IRQ → HALT → (AUTO) back to SYNC 1
ARM ISR:      read TAU21/31/41 · write STATUS.DONE = 1 (clears IRQ) · triangulate
```

Streaming replaces v1.0's ping-pong buffers. The DMA keeps writing into the rings while the PEs process the previous block (§4.2); `SYNC 1` makes the program wait only if data is late.

---

## 10. Timing, Latency, and Throughput

Measured by running the §8 program in `isa_sim.py` with a single-issue, in-order timing model: load/`WLD`/`WSLIDE` result latency 2 cycles, DSP operations 3, `VREDUCE` and `PKMAX` 5, `SDIV` 34; stalls on read-after-write; `VMAC→VMAC` accumulation has no stall; 2 cycles to fill fetch/decode.

| Phase | Cycles | Per item |
|-------|-------:|---------|
| P0 setup (incl. pipeline fill) | 5 | |
| P1 filter | 1 548 | ≈ 12 per row (4 VMAC + stalls + VREDUCE + WSLIDE + SST) |
| P2 error | 44 | |
| P3 gradient | 1 044 | 16 per column |
| P4 update | 31 | |
| P5 peak | 23 | |
| **Total** | **2 695** | **27.0 µs at 100 MHz** |

- Block period: 128 / 48 kHz = **2 667 µs** → the cluster is busy **1.0 %** (≈ 99× headroom).
- Cycle count is data-independent (identical for all 600 simulated blocks).
- Most remaining cycles are `VREDUCE`→`SST` stalls. Software-pipelining the store of y[i−1] behind row i's `VMAC`s would bring Phase 1 to ≈ 8 cycles/row; not needed for real time.
- 100 MHz is a standard `FCLK_CLK0` setting for the PL and conservative for pipelined DSP48E1 datapaths; the real Fmax comes from synthesis.

---

## 11. Control & Status Registers (CSRs)

AXI4-Lite address map: CSR k at byte offset `4k` (0x00–0x3C); IMEM word i at `0x800 + 4i` (write-only from the ARM).

| CSR | Name | R/W | Description |
|-----|------|-----|-------------|
| 0x0 | `CTRL` | R/W | [0] START · [1] SRESET · [2] IRQ_EN · [3] AUTO (restart on next block) · [4] WCLR (zero w on SRESET) |
| 0x1 | `STATUS` | R/W1C | [0] BUSY · [1] DONE (write 1 to clear IRQ) · [2] OVERRUN |
| 0x2 | `MU` | R/W | μ in Q1.15 |
| 0x3 | `B` | R/W | block size (block-ready threshold) |
| 0x4 | `L` | R/W | filter length (informational; program is assembled for B, L) |
| 0x5 | `TAU21` | R | τ from PE0 (signed) |
| 0x6 | `TAU31` | R | τ from PE1 |
| 0x7 | `TAU41` | R | τ from PE2 |
| 0x8 | `MASK_WORK` | R/W | PE enable mask (Mahmood's Mask_Work_Reg) |
| 0x9 | `XOFF` | R/W | X-ring write offset (= L − 1) |
| 0xA | `DOFF` | R/W | D-ring write offset (= L/2, the center tap) |
| 0xB | `SAMPLES_IN` | R | input writer sample counter |
| 0xC | `CYCLE_LO` | R | cycle counter (profiling) |
| 0xD | `CYCLE_HI` | R | |
| 0xE | `ERR_CODE` | R | |
| 0xF | `VERSION` | R | 0x0101 |

`MASK_NET` (v1.0 0x9) was dropped: the input writer's broadcast of Mic 1 removes the need for a lane network. `BUF_PTR` (v1.0 0xA) belongs to the DMA, which the ARM programs directly.

### ARM driver sketch (Xilinx standalone BSP)

```c
void accel_init(const uint32_t *prog, int n) {
    for (int i = 0; i < n; i++) Xil_Out32(ACCEL + 0x800 + 4*i, prog[i]);   // load IMEM
    Xil_Out32(ACCEL + 4*CSR_MU,   (uint32_t)(0.5f * 32768));               // Q1.15
    Xil_Out32(ACCEL + 4*CSR_B,    128);
    Xil_Out32(ACCEL + 4*CSR_L,    64);
    Xil_Out32(ACCEL + 4*CSR_XOFF, 63);
    Xil_Out32(ACCEL + 4*CSR_DOFF, 32);
    Xil_Out32(ACCEL + 4*CSR_CTRL, CTRL_SRESET);
    Xil_Out32(ACCEL + 4*CSR_CTRL, CTRL_IRQ_EN | CTRL_AUTO | CTRL_START);
}

void send_block(int16_t *interleaved4, size_t bytes) {       // {m1,m2,m3,m4} per sample
    Xil_DCacheFlushRange((UINTPTR)interleaved4, bytes);      // HP0 is not cache-coherent
    XAxiDma_SimpleTransfer(&dma, (UINTPTR)interleaved4, bytes, XAXIDMA_DMA_TO_DEVICE);
}

void accel_isr(void *ref) {
    int32_t t21 = Xil_In32(ACCEL + 4*CSR_TAU21);
    int32_t t31 = Xil_In32(ACCEL + 4*CSR_TAU31);
    int32_t t41 = Xil_In32(ACCEL + 4*CSR_TAU41);
    Xil_Out32(ACCEL + 4*CSR_STATUS, STATUS_DONE);             // W1C: clears IRQ_F2P
    triangulate(t21, t31, t41);
}
```

---

## 12. Interrupt & Handshake Protocol

```
ARM                                   SIMD cluster
 │── IMEM + CSRs (AXI4-Lite) ─────────→│
 │── CTRL = IRQ_EN|AUTO|START ────────→│  PC=0: SYNC 1 (waits for data)
 │── start DMA (block n) ──→ DMA ──AXIS→│  input writer fills rings
 │                                     │  P0…P5  (27 µs)
 │←────────────── IRQ_F2P ─────────────│  IRQ, HALT → AUTO restart → SYNC 1
 │── read TAU21/31/41 ────────────────→│
 │── STATUS.DONE = 1 (clear) ─────────→│
```

The IRQ is level-triggered and stays high until the ARM clears `STATUS.DONE`. The ARM never has to poll. `SRESET` clears A7, the sample counter and the rings, and keeps `w_rev` unless `CTRL.WCLR` is set.

---

## 13. Microarchitecture

Diagrams: `presentation/figures/microarch.png` (full detail) and `slide_microarch.png` (slide version), both from `presentation/draw_microarch.py`; the PE datapath (registers, muxes, DSP48E1 lanes, adder tree, with the control unit's fetch path and AGU) is `presentation/figures/pe_datapath.png` from `presentation/draw_datapath.py`.

### 13.1 System (Zynq-7000)

| Block | Implementation | Interface |
|-------|----------------|-----------|
| ARM Cortex-A9 | Zynq PS, C program | `M_AXI_GP0` → AXI Interconnect → accelerator AXI4-Lite slave |
| DMA | Xilinx AXI DMA (MM2S) or Alex Forencich `verilog-axi` `axi_dma` (MIT) | reads DDR over `S_AXI_HP0`, outputs 64-bit AXI4-Stream |
| Accelerator | custom Verilog | AXI4-Lite slave + AXI4-Stream slave + level IRQ → `IRQ_F2P` |

The accelerator only relies on standard AXI4-Lite and AXI4-Stream, inferred RAM and inferred `a*b+c`. Nothing inside it is Xilinx-specific, so any AXI system (or a direct I²S microphone front-end feeding the stream) can drive it.

### 13.2 Control Unit (shared)

```
IMEM (512×32, BRAM18) → Fetch (PC, loop stack ×2) → Decode/Issue (scoreboard) → AGU (A0–A7) → broadcast
                                                                     Sequencer: SYNC / HALT / IRQ / START / AUTO
```

- **Fetch:** PC → IMEM (1-cycle BRAM read). Next PC = loop start if `PC == loop.end && loop.count > 1`, else PC + 1. No branches, so no branch penalty.
- **Decode / issue:** single issue, in order. A small scoreboard holds the ready-cycle of V0–V7, W, S0–S7, VACC and the peak register, and stalls issue on read-after-write hazards (latencies in §10).
- **AGU:** 8 × 13-bit registers + circular flags. Effective address and post-increment are computed in the issue cycle; circular wrap = keep the upper bits and add only within the low 9 bits.
- **Broadcast:** one decoded control word + one address per cycle go to all PEs. Everything per PE is data; everything shared is control, which is exactly the SIMD split.

### 13.3 Processing Element

```
          ┌─ 16 banks (BRAM18) ─┐    VLD/VST     ┌── VRF V0–V7 ──┐
input ──→ │ X ring · D ring ·   │ ←────────────→ │ 16 × 32 bit    │──→ Vector ALU (add/sub/abs/sat)
writer    │ w_rev · y · e · g   │                └───────┬────────┘
          └──────┬──────────────┘                        │ w or e (A port, 25 bit)
                 │ WLD (16) / WSLIDE (1)                  ▼
          ┌──────▼──────────────┐  x (B port) ┌── 16 × DSP48E1 ──┐   VACC = P (48 bit)
          │ WIN 128 × 16 bit    │ ──────────→ │ ×, +             │──→ adder tree 16→1 → S regs → SST
          └─────────────────────┘             └──────────────────┘
                                                VRF → peak detector (│·│ tree + running max) → τ CSR
```

### 13.4 Resources (from the architecture; LUT/Fmax need synthesis)

| Resource | Cluster needs | Zybo Z7-10 (XC7Z010) | Zybo Z7-20 (XC7Z020) |
|----------|---------------|----------------------|----------------------|
| DSP48E1 | 51 (3 × 16 lanes + 3 scalar) | 80 → 64 % | 220 → 23 % |
| BRAM18 | 49 (3 × 16 banks + 1 IMEM) | 120 → 41 % | 280 → 18 % |
| Clock | 100 MHz | | |
| Peak compute | 48 MAC/cycle = 4.8 GMAC/s | | |

The biggest LUT consumers are expected to be the adder trees (3 × 15 adders ≈ 50 bits), the window registers (3 × 2 048 FF + 8:1 chunk muxes) and the vector ALUs. On the Z7-10 this should be checked early; if it is tight, one peak detector can be time-shared between PEs (Phase 5 is only 23 cycles).

---

## 14. Verification

| Check | Tool | Result |
|-------|------|--------|
| Fixed-point datapath vs float golden model, whole 126.8 s scenario | `feasibility_run.py` | identical τ on **99.6 %** of 47 547 blocks |
| ISA program (§8) vs fixed-point model, incl. ring wrap-around | `isa_sim.py 600` | **600 / 600** blocks bit-exact (τ and all 64 weights, 3 PEs) |
| Accuracy vs true delay (μ = 0.5) | `feasibility_run.py` | **85.6 %** of blocks within ±1 sample |
| v1.0 access pattern | ad-hoc run | reports **−τ** (sign flipped) |
| Tracking vs μ / NLMS | `tracking_study.py` | μ/B: 0.05 → 47 %, 0.5 → 85.6 %; NLMS μ = 0.64 → 88 % |

Signal-content limits seen in the scenario: 66–90 s of `source2.wav` is bass-only (spectral centroid 108–222 Hz) and the last 7 s fade to silence. TDOA estimates freeze there because a narrowband low-frequency signal has no sharp correlation peak. That is a property of the input, not of the accelerator. Remedies are PHAT/pre-whitening or holding the last estimate when coherence is low.

---

## 15. Open Items

1. **RTL + synthesis** of one PE to get LUT/FF counts and Fmax on the Z7-10.
2. **NLMS normalisation** in hardware: `VMAC W×W` + `VREDUCE` for block power, one `SDIV` per block, then `VSCALE`. The ISA already supports it; it needs a fixed-point scaling study.
3. **Sub-sample delay:** parabolic interpolation around the peak (3 weights) on the ARM — needs no hardware.
4. **Software pipelining** of the Phase 1/3 loops if the cycle budget ever matters.
5. Choose μ (0.5 recommended from simulation, or NLMS).

---

*End of Document — ISA_Design.md v1.1*
