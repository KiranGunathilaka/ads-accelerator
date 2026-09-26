# ISA Design for the Block-LMS SIMD Accelerator
### Sound Source Localization — TDOA via Centered NLMS

**Document Version:** 1.0  
**Author:** Rakindu  
**Project:** ADS Semester 7 — SIMD Processor Design  
**Reference Paper:** Mahmood & Al-Jbaar, "Design and implementation of SIMD Vector Processor on FPGA," IEEE ISIICT 2011

---

## Table of Contents

1. [System Overview & Motivation](#1-system-overview--motivation)
2. [The Algorithm: What the Hardware Must Do](#2-the-algorithm-what-the-hardware-must-do)
3. [Processor Cluster Architecture Summary](#3-processor-cluster-architecture-summary)
4. [Memory Map & Register File Design](#4-memory-map--register-file-design)
5. [Instruction Format](#5-instruction-format)
6. [Instruction Set — Complete Opcode Table](#6-instruction-set--complete-opcode-table)
7. [Instruction Descriptions — Detailed Semantics](#7-instruction-descriptions--detailed-semantics)
8. [Micro-Architecture Mapping (Phase-by-Phase)](#8-micro-architecture-mapping-phase-by-phase)
9. [Execution Flow: A Complete Block-LMS Block](#9-execution-flow-a-complete-block-lms-block)
10. [Timing, Latency, and Throughput Analysis](#10-timing-latency-and-throughput-analysis)
11. [Control & Status Registers (CSRs)](#11-control--status-registers-csrs)
12. [Interrupt & Handshake Protocol](#12-interrupt--handshake-protocol)
13. [Things You Would Have Missed — Completeness Additions](#13-things-you-would-have-missed--completeness-additions)

---

## 1. System Overview & Motivation

### 1.1 The Application Context

The application estimates the **Time Difference of Arrival (TDOA)** of a sound source using **four microphones** arranged in a 3D tetrahedral configuration. One microphone (Mic 1) is the reference. Three independent NLMS adaptive filters track the cross-correlation between each pair:

| Filter | Signal `x` | Reference `d` | Output |
|--------|-----------|---------------|--------|
| LMS-21 | Mic 2 | Mic 1 | tau_21 (delay in samples) |
| LMS-31 | Mic 3 | Mic 1 | tau_31 |
| LMS-41 | Mic 4 | Mic 1 | tau_41 |

The three delay estimates (tau_21, tau_31, tau_41) are then used upstream (e.g., MUSIC, SRP-PHAT) by the ARM host to triangulate the 3D position of the source.

### 1.2 The Computational Problem

The Python reference implementation (`realtime_simulation.py`) runs one `process_block()` call per filter per block. A single call involves:

```
B  = block size        (e.g., 128 samples)
L  = filter length     (e.g., 64 taps)
```

The four operations inside `process_block()`:

| Phase | Operation | Complexity |
|-------|-----------|------------|
| Phase 1: Filter | `y = X @ w` where X is B×L | O(B×L) = 8192 MACs |
| Phase 2: Error  | `e = d_delayed - y` | O(B) = 128 subs |
| Phase 3: Gradient | `g = X_T @ e` | O(L×B) = 8192 MACs |
| Phase 4: Weight Update | `w += (mu/B) × g` | O(L) = 64 MACs |
| Phase 5: Peak Detection | `argmax(|w|)` | O(L) = 64 compares |

**Total per filter call:** ~16,512 floating-point operations.  
**Total per block (3 filters):** ~49,536 operations.

On a bare ARM Cortex-A9 at ~500 MHz with scalar FPU, this leaves almost no headroom for audio I/O, host logic, or 3D triangulation. The SIMD cluster brings this down to **predictable, deterministic latency**, freeing the ARM completely.

### 1.3 Why Three SIMD Processors?

The three filter computations (LMS-21, LMS-31, LMS-41) are **perfectly independent** of each other — they share only the reference signal `d_block`. This is **data-level parallelism at the task level**. Rather than time-multiplexing one processor across three filters, we instantiate **three identical SIMD processors** running the same instruction sequence on different data. This is textbook SIMD (Single Instruction, Multiple Data) at the coarse-grained level: one control unit broadcasts instructions; three processing clusters execute them concurrently.

```
                    ┌────────────────────────┐
                    │    ARM Host (AXI-Lite)  │
                    │  - Configures mu, B, L  │
                    │  - Reads tau_21,31,41   │
                    └────────────┬───────────┘
                                 │ Broadcast ISA instruction stream
                    ┌────────────▼───────────┐
                    │   Global Sequencer /   │
                    │   Control Unit (CU)    │
                    └──┬──────────┬──────┬───┘
                       │          │      │  (same instr, diff data)
              ┌────────▼──┐ ┌────▼───┐ ┌▼────────┐
              │  SIMD-PE 0│ │SIMD-PE1│ │SIMD-PE 2│
              │  (Mic2↔1) │ │(Mic3↔1)│ │(Mic4↔1) │
              │  → tau_21  │ │→ tau_31 │ │→ tau_41 │
              └───────────┘ └────────┘ └─────────┘
```

The Mahmood 2011 architecture directly supports this model: the **Mask_Work_Reg** CSR selects which lanes are active, and the same instruction word is broadcast to all active PEs simultaneously.

---

## 2. The Algorithm: What the Hardware Must Do

The hardware must implement the following pseudocode for each of the three filter pairs. This drives every instruction in the ISA.

```
-- One block (B samples) arrives. L = filter length, center_tap = L//2 --

INPUT:  x_block[B], d_block[B]          -- from DMA/ping-pong buffer
STATE:  w[L], x_history[L], d_history[center_tap]   -- in scratchpad

-- Step 0: Concatenate history (handled by AGU sliding-window)
x_full[L+B]  = [x_history | x_block]
d_full[ct+B] = [d_history | d_block]
d_delayed[B] = d_full[0 : B]           -- center-tapped reference

-- Step 1: Build BxL data matrix X via AGU sliding window (no physical build)
--         X[i, :] = x_full[i+L : i : -1]   for i in 0..B-1

-- Phase 1: Filter — y[B] = X[B,L] @ w[L]
for i in 0..B-1:
    y[i] = dot(X[i], w)               -- L MACs

-- Phase 2: Error — e[B] = d_delayed[B] - y[B]
for i in 0..B-1:
    e[i] = d_delayed[i] - y[i]        -- 1 subtract

-- Phase 3: Gradient — g[L] = X_T[L,B] @ e[B]
for j in 0..L-1:
    g[j] = dot(column_j_of_X, e)      -- B MACs

-- Phase 4: Weight Update — w[L] += (mu/B) × g[L]
scaled_mu = mu / B
for j in 0..L-1:
    w[j] = w[j] + scaled_mu * g[j]    -- 1 MAC

-- Phase 5: Peak Detection
peak_idx = argmax(abs(w))
estimated_delay = center_tap - peak_idx
OUTPUT: estimated_delay → CSR result register → ARM IRQ
```

This 5-phase structure maps **directly and bijectively** to the 5 categories of instructions in the ISA below.

---

## 3. Processor Cluster Architecture Summary

Each SIMD PE contains the following hardware units (based on arch.txt and Mahmood 2011):

| Unit | Width | Purpose |
|------|-------|---------|
| **Vector Register File (VRF)** | 16 × 32-bit elements per register | Holds operand vectors for MAC lanes |
| **MAC Lanes** | 16 parallel DSP48 slices | Each performs `a × b + acc` per cycle |
| **Adder Tree** | 4-level binary reduction | Sums 16 lane outputs → 1 scalar in 4 cycles |
| **Address Generation Unit (AGU)** | 32-bit address arithmetic | Generates sliding-window addresses; two independent pointers |
| **Scratchpad Memory** | 4 KB BRAM | Holds `x_full`, `d_delayed`, `w`, `y`, `e`, `g` |
| **Scalar ALU** | 32-bit FP | Step-size multiply, peak-index compare, result arithmetic |
| **Control Status Registers (CSRs)** | 16 × 32-bit | Configuration (mu, B, L), results (tau), flags |
| **Peak Detector** | Comparator + index register | Sweeps `w`, tracks max(|w[j]|) and its index |

**Vector width = 16 elements** — this is the key parallelism degree (VLEN). All vector instructions operate on **chunks of 16** elements at a time.

---

## 4. Memory Map & Register File Design

### 4.1 Scratchpad Memory Layout

The 4 KB scratchpad is partitioned as follows (assumes B=128, L=64, 32-bit floats):

| Region | Symbol | Size (elements) | Size (bytes) | Address Range |
|--------|--------|-----------------|--------------|---------------|
| Input signal (x) | `x_full` | L+B = 192 | 768 B | 0x000 – 0x2FF |
| Reference signal (d_delayed) | `d_del` | B = 128 | 512 B | 0x300 – 0x4FF |
| Filter weight vector | `w` | L = 64 | 256 B | 0x500 – 0x5FF |
| Output vector | `y` | B = 128 | 512 B | 0x600 – 0x7FF |
| Error vector | `e` | B = 128 | 512 B | 0x800 – 0x9FF |
| Gradient vector | `g` | L = 64 | 256 B | 0xA00 – 0xAFF |
| x_history (for next block) | `x_hist` | L = 64 | 256 B | 0xB00 – 0xBFF |
| d_history (for next block) | `d_hist` | center_tap = 32 | 128 B | 0xC00 – 0xC7F |
| Reserved / alignment | — | — | ~896 B | 0xC80 – 0xFFF |

> **Total used: ~3.2 KB**, comfortably within 4 KB.

### 4.2 Vector Register File (VRF)

Each PE has **8 vector registers** (V0–V7), each holding **16 × 32-bit** elements:

| Register | Dedicated Use | Description |
|----------|--------------|-------------|
| V0 | Input window row / column chunk | Loaded by AGU; one 16-element chunk of `x_full` |
| V1 | Weight vector chunk | Loaded by AGU; 16 elements of `w` |
| V2 | Partial product accumulator | Holds 16-element products from V0×V1; feeds Adder Tree |
| V3 | Error vector chunk | Loaded for Phase 2 (error) and Phase 3 (gradient) |
| V4 | Gradient accumulator chunk | Accumulates 16 gradient partial sums |
| V5 | Output vector `y` / scratch | Stores computed `y` values before subtraction |
| V6 | General purpose / temp | Used by scalar operations, broadcasts |
| V7 | Mask / control scratch | Used for conditional masking during peak detection |

### 4.3 Scalar Registers

| Register | Symbol | Use |
|----------|--------|-----|
| S0 | `mu_scaled` | Holds `mu/B` — the normalized step size |
| S1 | `acc` | Running dot-product accumulator (scalar result from Adder Tree) |
| S2 | `peak_val` | Current maximum `|w[j]|` during peak scan |
| S3 | `peak_idx` | Index of current maximum |
| S4 | `loop_ctr` | General-purpose loop counter |
| S5 | `temp` | Temporary scalar (intermediate computations) |
| S6 | `B_reg` | Block size B (loaded from CSR at init) |
| S7 | `L_reg` | Filter length L (loaded from CSR at init) |

---

## 5. Instruction Format

All instructions are **32 bits wide**, using a **4-field fixed-length format**. This enables single-cycle decode and a simple, uniform pipeline.

```
 31      27 26    22 21    17 16    12 11              0
 ┌─────────┬────────┬────────┬────────┬────────────────┐
 │  OPCODE │  DST   │  SRC1  │  SRC2  │    IMM12       │
 │  [5b]   │  [5b]  │  [5b]  │  [5b]  │    [12b]       │
 └─────────┴────────┴────────┴────────┴────────────────┘
```

### 5.1 Field Definitions

| Field | Bits | Width | Description |
|-------|------|-------|-------------|
| `OPCODE` | [31:27] | 5 bits | Identifies instruction type — allows up to **32 opcodes** |
| `DST` | [26:22] | 5 bits | Destination: V0–V7 (3 bits used), S0–S7 (3 bits), or CSR index |
| `SRC1` | [21:17] | 5 bits | Source operand 1: same encoding as DST |
| `SRC2` | [16:12] | 5 bits | Source operand 2, or AGU base register index |
| `IMM12` | [11:0] | 12 bits | Immediate value: scratchpad offset (byte-addressed), loop count, shift |

### 5.2 Register Encoding (DST / SRC fields)

```
Bit[4:3] = "00" → Vector register  V0–V7  (bit[2:0])
Bit[4:3] = "01" → Scalar register  S0–S7  (bit[2:0])
Bit[4:3] = "10" → CSR index        0–15   (bit[3:0])
Bit[4:3] = "11" → Immediate mode   (value in IMM12)
```

### 5.3 Instruction Type Tags (bits [31:30])

To aid the decode unit (matching Mahmood's pre-decode / supplement-decode pipeline), the **two MSBs of OPCODE** indicate the broad category:

| Tag [31:30] | Category | Action in Pre-Decode |
|-------------|----------|---------------------|
| `00` | Vector arithmetic | Broadcast to all active MAC lanes |
| `01` | Vector memory (load/store) | Signal AGU; activate memory bus |
| `10` | Scalar / control | Route to scalar ALU only |
| `11` | Special (peak/sync/IRQ) | Route to peak detector or CU |

---

## 6. Instruction Set — Complete Opcode Table

### 6.1 Category 0 — Vector Arithmetic (tag `00`)

| Mnemonic | OPCODE[4:0] | Operation | Description |
|----------|-------------|-----------|-------------|
| `VMAC` | `00000` | V_DST[i] += SRC1[i] × SRC2[i] | **Vector Multiply-Accumulate** — core LMS instruction |
| `VSUB_V` | `00001` | V_DST[i] = SRC1[i] − SRC2[i] | **Vector Element-wise Subtract** — computes error vector `e` |
| `VADD_V` | `00010` | V_DST[i] = SRC1[i] + SRC2[i] | **Vector Element-wise Add** — weight update add step |
| `VSCALE` | `00011` | V_DST[i] = SRC1[i] × S_src | **Vector Scale by Scalar** — scales gradient by `mu/B` |
| `VABS` | `00100` | V_DST[i] = abs(SRC1[i]) | **Vector Absolute Value** — used in peak detection |
| `VMOV_V` | `00101` | V_DST[i] = SRC1[i] | **Vector Move** — register-to-register copy |
| `VREDUCE` | `00110` | S_DST = Sum(V_SRC[i]) for i=0..15 | **Vector Reduce (Adder Tree)** — 16 → 1 scalar sum |
| `VMUL_V` | `00111` | V_DST[i] = SRC1[i] × SRC2[i] | **Vector Element Multiply** (no accumulate) |

### 6.2 Category 1 — Vector Memory / AGU (tag `01`)

| Mnemonic | OPCODE[4:0] | Operation | Description |
|----------|-------------|-----------|-------------|
| `VLD` | `01000` | V_DST = Mem[AGU_ptr .. +15] | **Vector Load** — load 16 elements from scratchpad |
| `VST` | `01001` | Mem[AGU_ptr .. +15] = V_SRC | **Vector Store** — store 16 elements to scratchpad |
| `AGU_SET` | `01010` | AGU_ptr = IMM12 | **AGU Set Base** — initialise read pointer to scratchpad offset |
| `AGU_INC` | `01011` | AGU_ptr += 16 | **AGU Advance** — slide window by VLEN (16 elements) |
| `AGU_SLIDE` | `01100` | AGU_ptr = BASE + row_ctr | **AGU Slide (Phase 1)** — advance base by 1 sample for next sliding window row |
| `AGU_COL` | `01101` | AGU_ptr = COL_ptr (strided) | **AGU Column Access** — switches to column (stride=1, offset=col) mode for Phase 3 |
| `VLD_S` | `01110` | V_DST = broadcast(Mem[IMM12]) | **Scalar Broadcast Load** — load one scalar and fill all 16 lanes |
| `VLD_CSR` | `01111` | S_DST = CSR[SRC1] | **CSR Load** — load a CSR value into a scalar register |

### 6.3 Category 2 — Scalar / Control (tag `10`)

| Mnemonic | OPCODE[4:0] | Operation | Description |
|----------|-------------|-----------|-------------|
| `SMUL` | `10000` | S_DST = S_SRC1 × S_SRC2 | **Scalar Multiply** — computes `mu/B` at init |
| `SADD` | `10001` | S_DST = S_SRC1 + S_SRC2 | **Scalar Add** — accumulates scalar partial sums |
| `SSUB` | `10010` | S_DST = S_SRC1 − S_SRC2 | **Scalar Subtract** — computes `center_tap - peak_idx` for tau |
| `SDIV` | `10011` | S_DST = S_SRC1 / S_SRC2 | **Scalar Divide** — computes `mu/B` |
| `SMOV` | `10100` | S_DST = S_SRC1 | **Scalar Move** — copies scalar register |
| `SIMM` | `10101` | S_DST = IMM12 (sign-extended) | **Scalar Immediate Load** — loads constant |
| `SACC_CLR` | `10110` | S_DST = 0.0f | **Scalar Accumulator Clear** — resets dot-product accumulator |
| `LOOP_SET` | `10111` | loop_ctr = IMM12 | **Loop Counter Set** — initialise hardware loop counter |

### 6.4 Category 3 — Special / Control Flow (tag `11`)

| Mnemonic | OPCODE[4:0] | Operation | Description |
|----------|-------------|-----------|-------------|
| `PKMAX` | `11000` | if abs(V_SRC[i]) > peak_val → update | **Peak Max Update** — compare 16 abs values vs running max |
| `PKIDX_OUT` | `11001` | CSR[RESULT] = center_tap − peak_idx | **Peak Index Output** — write delay estimate to result CSR |
| `SYNC` | `11010` | stall until memory ops complete | **Synchronise** — pipeline fence |
| `PHASE_END` | `11011` | notify CU; advance phase counter | **Phase End Signal** |
| `IRQ_FIRE` | `11100` | assert IRQ line to ARM | **Fire Interrupt** |
| `NOP` | `11101` | no operation | **No-Op** — pipeline alignment |
| `HALT` | `11110` | stop execution | **Halt** — awaits next DMA/START |
| `CSR_WR` | `11111` | CSR[DST] = S_SRC1 | **CSR Write** — write scalar result to CSR |

---

## 7. Instruction Descriptions — Detailed Semantics

### 7.1 `VMAC` — Vector Multiply-Accumulate

```
VMAC V_DST, V_SRC1, V_SRC2
```

**Encoding:**
```
31    27 | 26   22 | 21   17 | 16   12 | 11      0
 00000   |  DST    |  SRC1   |  SRC2   |  000...0
```

**Operation (per lane i = 0..15):**
```
V_DST[i] <- V_DST[i] + V_SRC1[i] * V_SRC2[i]
```

**Use:** This is the **innermost loop body** for both Phase 1 (filter) and Phase 3 (gradient). 

- Phase 1: `SRC1` = data window row chunk, `SRC2` = weight vector chunk, `DST` = accumulator register (V2)
- Phase 3: `SRC1` = column chunk of X, `SRC2` = error vector chunk, `DST` = gradient accumulator (V4)

**Hardware Execution:**
- All 16 DSP48 slices fire simultaneously (1 clock cycle for 16 products)
- 16 partial sums accumulated back into destination register elements
- The adder tree is **not used** here — VMAC accumulates per-lane (no horizontal reduction yet)
- Latency: **1 clock cycle** (DSP48 pipelined, fully registered)

**Design Rationale:** VMAC deliberately accumulates *within* V_DST rather than outputting to a separate register. This allows the inner loop to read, multiply, and accumulate without a separate VADD, matching how NumPy's `np.dot` works internally.

---

### 7.2 `VREDUCE` — Vector Reduction (Adder Tree)

```
VREDUCE S_DST, V_SRC
```

**Encoding:**
```
31    27 | 26   22 | 21   17 | 16   12 | 11      0
 00110   |  S_DST  |  V_SRC  |  00000  |  000...0
```

**Operation:**
```
S_DST <- V_SRC[0] + V_SRC[1] + ... + V_SRC[15]
```

**Hardware Execution:**
- A **4-level binary adder tree** (16→8→4→2→1) reduces the 16 values
- Each level is registered (pipelined) for maximum clock frequency
- Total latency: **4 clock cycles** (one per tree level)
- Result deposited into scalar register `S_DST` on cycle 4

**Use:** After the inner VMAC loop completes for one window row (Phase 1) or one column (Phase 3), `VREDUCE` collapses the 16-element partial sum vector into a single scalar that is then accumulated via `SADD` into `S1`.

---

### 7.3 `VSUB_V` — Vector Subtract (Error Phase)

```
VSUB_V V_DST, V_SRC1, V_SRC2
```

**Operation:**
```
V_DST[i] <- V_SRC1[i] - V_SRC2[i],  for i = 0..15
```

**Use:** Phase 2. `SRC1` holds a 16-element chunk of `d_delayed`; `SRC2` holds the corresponding chunk of `y`. Executed B/16 = 8 times (for B=128) to produce the complete error vector `e`. **Immediately followed by `VST`** to write `e` back to scratchpad.

---

### 7.4 `VSCALE` — Vector Scale by Scalar

```
VSCALE V_DST, V_SRC, S_SRC
```

**Encoding:**
```
31    27 | 26   22 | 21   17 | 16   12 | 11      0
 00011   |  V_DST  |  V_SRC  |  S_SRC  |  000...0
```

**Operation:**
```
V_DST[i] <- V_SRC[i] * S_SRC,  for i = 0..15
```

**Use:** Phase 4. Multiplies each element of `g` (the gradient vector) by the scalar `mu/B`. This is the "step-size scaling" step before the weight update.

**Hardware:** The scalar `S_SRC` value is **broadcast** to all 16 DSP multipliers simultaneously. One side of every multiplier gets the same scalar; the other side gets the corresponding element from V_SRC.

---

### 7.5 `AGU_SLIDE` — Sliding Window Advance

```
AGU_SLIDE
```

**Operation (implicit, no operands):**
```
AGU_base_ptr <- AGU_base_ptr + 1 element (4 bytes)
V2 accumulator <- clear for next row
```

**Use:** After computing `y[i]` for one window row, this instruction moves the AGU's base pointer forward by exactly **one sample** to set up the next sliding window row for `y[i+1]`. 

This is the hardware equivalent of the Python loop:
```python
X = np.array([x_full[i + L : i : -1] for i in range(B)])
```
The sliding window is **never physically built** in memory — the AGU generates each row's addresses on the fly by advancing the base pointer.

---

### 7.6 `AGU_COL` — Column-Wise Access (Phase 3 Mode)

```
AGU_COL S_col_idx
```

**Operation:**
```
AGU_ptr    <- BASE_xfull + col_idx * sizeof(float)
AGU_stride <- 1 element (unit stride along column)
```

**Use:** Phase 3 accesses the data matrix **transposed** (column by column). Column `j` of the B×L matrix `X` corresponds to `x_full[j], x_full[j+1], ..., x_full[j+B-1]` — a unit-stride access starting at offset `j`. The AGU computes this with a simple base+offset and stride=1, so no special striding hardware is needed.

---

### 7.7 `PKMAX` — Peak Maximum Update

```
PKMAX V_SRC
```

**Encoding:**
```
31    27 | 26   22 | 21   17 | 16   12 | 11      0
 11000   |  00000  |  V_SRC  |  00000  |  000...0
```

**Operation:**
```
for i = 0..15:
    abs_val = abs(V_SRC[i])
    if abs_val > peak_val:
        peak_val <- abs_val
        peak_idx <- current_element_index  (tracked by AGU position)
```

**Hardware:** The 16-element comparison is performed in a **tree of comparators** (4 levels, same topology as adder tree). The local maximum and its index bubble up to produce one winner per PKMAX call. The winner is then compared to the running `peak_val` register by the scalar ALU. Executed L/16 = 4 times to scan all of `w`.

---

### 7.8 `IRQ_FIRE` — Fire ARM Interrupt

```
IRQ_FIRE
```

**Operation:**
```
assert GPIO_IRQ_line <- 1
CSR[STATUS] <- STATUS_DONE
```

**Use:** Final instruction in the processing sequence. After `PKIDX_OUT` writes tau to the result CSR, `IRQ_FIRE` pulses the interrupt line connected to the ARM's GIC. The ARM ISR reads the three tau values (one per PE) from the CSR bank via AXI-Lite and proceeds with 3D triangulation.

---

## 8. Micro-Architecture Mapping (Phase-by-Phase)

This section maps each algorithmic phase to the exact sequence of instructions and hardware events.

### 8.1 Phase 0 — Initialisation (per block)

Executed once per block before the main phases.

```asm
; Load configuration from CSRs
VLD_CSR   S6, CSR_B          ; S6 = B (block size, e.g. 128)
VLD_CSR   S7, CSR_L          ; S7 = L (filter length, e.g. 64)
VLD_CSR   S5, CSR_MU         ; S5 = mu (step size, e.g. 0.05)

; Compute normalised step size: mu_scaled = mu / B
SDIV      S0, S5, S6         ; S0 = mu/B
; (alternative: SMUL S0, S5, S_recipB  if reciprocal precomputed)

; Set AGU base pointers
AGU_SET   0x000              ; x_full starts at offset 0x000
SIMM      S4, 0              ; loop counter = 0 (row index i)
```

---

### 8.2 Phase 1 — Filter: `y[B] = X[B,L] @ w[L]`

**Goal:** Compute the output of the adaptive filter for every one of the B input samples.

**Loop structure:** Outer loop over rows (i = 0..B-1), inner loop over chunks (k = 0..L/16-1).

```asm
; ── Phase 1: Filter ──────────────────────────────────────────
LOOP_SET  B                  ; outer loop: B rows (= 128)
AGU_SET   0x000              ; x pointer starts at x_full[0]

OUTER_LOOP_P1:
    SACC_CLR  S1             ; clear dot-product accumulator
    AGU_SET   0x500          ; reset w pointer to start of w[]
    LOOP_SET  L_DIV_16       ; inner loop: 4 chunks (L=64, VLEN=16)

    INNER_LOOP_P1:
        VLD     V0, x_ptr    ; load 16 samples of current row of X
        VLD     V1, w_ptr    ; load 16 weights
        VMAC    V2, V0, V1   ; V2[i] += V0[i] * V1[i]   (16 MACs in 1 cycle)
        AGU_INC              ; advance x_ptr by 16
        AGU_INC              ; advance w_ptr by 16
        LOOP_DEC → INNER_LOOP_P1

    VREDUCE S1, V2           ; sum V2[0..15] → S1  (4 cycles: adder tree)
    SACC_CLR  V2             ; clear V2 for next row (VMOV_V V2, 0)
    VST_S   S1, y_ptr        ; store y[i] → y[] region in scratchpad
    AGU_SLIDE                ; slide x_ptr base by +1 sample
    LOOP_DEC → OUTER_LOOP_P1
; ─────────────────────────────────────────────────────────────
```

**Hardware events per inner loop iteration:**
```
Cycle 1:  AGU issues 16 scratchpad read addresses for V0
Cycle 2:  Scratchpad returns 16 elements; loaded into V0
Cycle 3:  AGU issues 16 addresses for V1
Cycle 4:  Scratchpad returns V1
Cycle 5:  16 DSP48s multiply V0[i] × V1[i] simultaneously
Cycle 6:  16 products accumulated back into V2[i]
```
→ 4 inner iterations × ~6 cycles = 24 + VREDUCE (4 cycles) + VST (2 cycles) = **~30 cycles per row**
→ 128 rows × 30 cycles = **~3,840 cycles for Phase 1**

---

### 8.3 Phase 2 — Error: `e[B] = d_delayed[B] - y[B]`

```asm
; ── Phase 2: Error ───────────────────────────────────────────
SYNC                         ; ensure Phase 1 stores complete
AGU_SET   0x300              ; d_delayed at 0x300
AGU_SET   0x600              ; y[] at 0x600   (dual AGU pointers)
AGU_SET   0x800              ; e[] at 0x800
LOOP_SET  B_DIV_16           ; 8 chunks

ERROR_LOOP:
    VLD     V5, d_ptr        ; load 16 d_delayed samples → V5
    VLD     V3, y_ptr        ; load 16 y values → V3
    VSUB_V  V3, V5, V3       ; V3[i] = d_delayed[i] - y[i]
    VST     V3, e_ptr        ; store 16 error samples
    AGU_INC (d_ptr)
    AGU_INC (y_ptr)
    AGU_INC (e_ptr)
    LOOP_DEC → ERROR_LOOP
; ─────────────────────────────────────────────────────────────
```

→ 8 chunks × ~5 cycles = **~40 cycles for Phase 2**

---

### 8.4 Phase 3 — Gradient: `g[L] = X_T[L,B] @ e[B]`

This is the most complex phase. It accesses the data matrix **column by column** instead of row by row. Column `j` corresponds to samples of `x_full` at positions starting at offset `j` with unit stride — a standard sequential access that the AGU handles easily.

**Chunking arithmetic (matches arch.txt exactly):**
- Inner loop: B/VLEN = 128/16 = **8 iterations** per column
- Outer loop: L = **64 columns**
- Total inner iterations: 8 × 64 = **512 VMAC operations**

```asm
; ── Phase 3: Gradient ────────────────────────────────────────
SYNC                         ; ensure error stores complete
SIMM      S4, 0              ; column index j = 0
LOOP_SET  L                  ; outer loop: L columns (= 64)

OUTER_LOOP_P3:
    SACC_CLR  S1             ; clear gradient accumulator for g[j]
    SACC_CLR  V4             ; clear gradient partial product vector
    AGU_COL   S4             ; set AGU to column j of X (= x_full offset j)
    AGU_SET   0x800          ; e pointer reset to e[0]
    LOOP_SET  B_DIV_16       ; inner loop: 8 chunks (B=128, VLEN=16)

    INNER_LOOP_P3:
        VLD     V0, col_ptr  ; 16 elements of column j
        VLD     V3, e_ptr    ; 16 elements of e
        VMAC    V4, V0, V3   ; V4[i] += col[i] * e[i]
        AGU_INC (col_ptr)
        AGU_INC (e_ptr)
        LOOP_DEC → INNER_LOOP_P3

    VREDUCE S1, V4           ; g[j] = sum(V4)
    SACC_CLR  V4
    VST_S   S1, g_ptr        ; store g[j]
    SADD    S4, S4, 1        ; j++
    AGU_INC (g_ptr)
    LOOP_DEC → OUTER_LOOP_P3
; ─────────────────────────────────────────────────────────────
```

→ 64 columns × (8 × ~6 + 4 + 2) = 64 × 54 = **~3,456 cycles for Phase 3**

---

### 8.5 Phase 4 — Weight Update: `w[L] += (mu/B) × g[L]`

```asm
; ── Phase 4: Weight Update ───────────────────────────────────
SYNC
AGU_SET   0xA00              ; g[] at 0xA00
AGU_SET   0x500              ; w[] at 0x500
LOOP_SET  L_DIV_16           ; 4 chunks

WEIGHT_LOOP:
    VLD     V4, g_ptr        ; load 16 gradient elements
    VLD     V1, w_ptr        ; load 16 current weights
    VSCALE  V4, V4, S0       ; V4[i] *= mu_scaled  (= mu/B)
    VADD_V  V1, V1, V4       ; V1[i] += V4[i]      (weight update)
    VST     V1, w_ptr        ; store updated weights back
    AGU_INC (g_ptr)
    AGU_INC (w_ptr)
    LOOP_DEC → WEIGHT_LOOP
; ─────────────────────────────────────────────────────────────
```

→ 4 chunks × ~7 cycles = **~28 cycles for Phase 4**

---

### 8.6 Phase 5 — Peak Detection: `argmax(|w[L]|)`

```asm
; ── Phase 5: Peak Detection ──────────────────────────────────
SYNC
AGU_SET   0x500              ; w[] at 0x500
SIMM      S2, 0              ; peak_val = 0.0f
SIMM      S3, 0              ; peak_idx = 0
LOOP_SET  L_DIV_16           ; 4 chunks

PEAK_LOOP:
    VLD     V6, w_ptr        ; load 16 weights
    VABS    V7, V6           ; V7[i] = |V6[i]|
    PKMAX   V7               ; compare 16 values vs peak_val, update peak_idx
    AGU_INC (w_ptr)
    LOOP_DEC → PEAK_LOOP

; Compute delay estimate: tau = center_tap - peak_idx
SIMM      S5, L_HALF         ; S5 = center_tap = L/2 = 32
SSUB      S3, S5, S3         ; S3 = center_tap - peak_idx
PKIDX_OUT                    ; write S3 to result CSR
IRQ_FIRE                     ; signal ARM: tau is ready
HALT                         ; wait for next block
; ─────────────────────────────────────────────────────────────
```

→ 4 chunks × ~5 cycles + overhead = **~25 cycles for Phase 5**

---

## 9. Execution Flow: A Complete Block-LMS Block

```
TIME (cycles) →
   0    10   3850  3890  7346  7374  7400
   │     │    │     │     │     │    │
   ┌─────┐    │     │     │     │    │
   │ P0  │    │     │     │     │    │
   └─────┴────┴─────┴─────┴─────┴────┘
         │  Phase 1 │  P2 │  Phase 3 │P4│P5│
         │  (3840c) │(40c)│  (3456c) │  │  │
```

**All three PEs run this sequence in lockstep, concurrently, on different mic pairs.**

While this PE processes block N, the DMA is already filling the ping-pong buffer with block N+1. The ARM never stalls.

### Ping-Pong Buffer Protocol

```
                Buffer A                 Buffer B
Block N-1:  [filled by DMA] ──→ SIMD processes A
Block N:    [filled by DMA] ──→ SIMD processes B (while DMA fills A with N+1)
```

The CU toggles the AGU base pointer between two buffer regions in scratchpad on each `HALT` → `START` cycle.

---

## 10. Timing, Latency, and Throughput Analysis

### 10.1 Per-Phase Cycle Counts (B=128, L=64, VLEN=16)

| Phase | Operation Count | Cycles (approx) | Bottleneck |
|-------|----------------|-----------------|-----------|
| Init | — | 10 | CSR loads, scalar divides |
| Phase 1 | 128 × 64 = 8,192 MACs | ~3,840 | VMAC throughput |
| Phase 2 | 128 subtracts | ~40 | Memory bandwidth |
| Phase 3 | 64 × 128 = 8,192 MACs | ~3,456 | VMAC + column AGU |
| Phase 4 | 64 MACs + 64 adds | ~28 | — |
| Phase 5 | 64 compares | ~25 | — |
| **Total** | **~16,576 ops** | **~7,400 cycles** | |

### 10.2 Throughput

At an FPGA clock of **100 MHz** (realistic for Spartan 7 / Artix 7):

```
Time per block = 7,400 cycles / 100 MHz = 74 us
```

At B=128, fs=16 kHz → block period = 128/16000 = **8 ms**.
The SIMD cluster finishes in 74 us, leaving **7.93 ms idle** — a 99% duty-cycle margin.

### 10.3 Speedup over ARM Scalar

An ARM Cortex-A9 single-precision FP dot product runs at ~1 FLOP/cycle. At 667 MHz, all phases for 3 filters ≈ **~200 us on ARM**.
SIMD cluster (3 PEs in parallel): **74 us**, and the ARM is completely free.

**Effective speedup: ~2.7×** from SIMD alone, plus full ARM release for host tasks.

---

## 11. Control & Status Registers (CSRs)

The CU exposes a 16-register CSR bank accessible from the ARM over AXI-Lite.

| CSR Index | Name | R/W | Description |
|-----------|------|-----|-------------|
| 0x00 | `CSR_CTRL` | R/W | Bit 0: START. Bit 1: RESET. Bit 2: IRQ_EN |
| 0x01 | `CSR_STATUS` | R | Bit 0: BUSY. Bit 1: DONE. Bit 2: ERROR |
| 0x02 | `CSR_MU` | R/W | Step size mu (IEEE 754 float32) |
| 0x03 | `CSR_B` | R/W | Block size B (uint32) |
| 0x04 | `CSR_L` | R/W | Filter length L (uint32) |
| 0x05 | `CSR_TAU21` | R | tau_21 delay estimate (PE 0 result, int32) |
| 0x06 | `CSR_TAU31` | R | tau_31 delay estimate (PE 1 result, int32) |
| 0x07 | `CSR_TAU41` | R | tau_41 delay estimate (PE 2 result, int32) |
| 0x08 | `CSR_MASK_WORK` | R/W | Active PE mask (bit i = PE i active) |
| 0x09 | `CSR_MASK_NET` | R/W | Interconnect mask (lane-to-lane comms) |
| 0x0A | `CSR_BUF_PTR` | R/W | Base address of input data in system memory |
| 0x0B | `CSR_PHASE` | R | Current executing phase (0–5, debug) |
| 0x0C | `CSR_CYCLE_LO` | R | Cycle counter (low 32 bits, for profiling) |
| 0x0D | `CSR_CYCLE_HI` | R | Cycle counter (high 32 bits) |
| 0x0E | `CSR_ERR_CODE` | R | Error code if CSR_STATUS[2] is set |
| 0x0F | `CSR_RESERVED` | — | Reserved for future use |

### ARM Startup Sequence (Pseudo-C)

```c
void start_simd_block(float mu, int B, int L) {
    // 1. Write config
    csr_write(CSR_MU, float_to_bits(mu));
    csr_write(CSR_B, B);
    csr_write(CSR_L, L);
    // 2. Fire
    csr_write(CSR_CTRL, 0x1);  // START bit
    // 3. ARM is free; IRQ handler will collect results
}

void simd_irq_handler(void) {
    int tau21 = csr_read(CSR_TAU21);  // PE 0 result
    int tau31 = csr_read(CSR_TAU31);  // PE 1 result
    int tau41 = csr_read(CSR_TAU41);  // PE 2 result
    compute_3d_position(tau21, tau31, tau41);
    csr_write(CSR_CTRL, 0x2);  // RESET: clear DONE flag, ready for next block
}
```

---

## 12. Interrupt & Handshake Protocol

The handshake follows a **fire-and-forget with interrupt** pattern — the ARM never polls.

```
ARM                              SIMD Cluster (CU + 3 PEs)
 │                                      │
 │── CSR_WR(MU, B, L) ──────────────────→│
 │── CSR_WR(CTRL, START=1) ─────────────→│
 │                                      │ DMA: load x_block, d_block
 │    (ARM does other work here)        │ Execute Phase 0–5 (74 us)
 │                                      │ IRQ_FIRE instruction
 │←── IRQ ────────────────────────────── │
 │── CSR_RD(TAU21, TAU31, TAU41) ───────→│
 │── CSR_WR(CTRL, RESET=1) ─────────────→│
 │                                      │ PEs HALT, await next START
```

**IRQ is level-triggered.** It is cleared by the ARM writing CSR_CTRL[RESET]. This prevents spurious re-triggering in the GIC.

---

## 13. Things You Would Have Missed — Completeness Additions

The following items were not explicitly mentioned in your description but are **required for a complete, working system**.

### 13.1 History Buffer Management

The Python code maintains `x_history[L]` and `d_history[center_tap]` between blocks:
```python
self.x_history = x_full[-self.L:]
self.d_history = d_full[-self.center_tap:]
```

**In hardware:** After Phases 1–5 complete, the CU must issue scratchpad-to-scratchpad copies:
- Copy last L elements of `x_full` → `x_hist` region (0xB00)
- Copy last `center_tap` elements of `d_full` → `d_hist` region (0xC00)
- On the next block, the AGU constructs `x_full` as `[x_hist | new x_block]`

This uses `VLD` + `VST` pairs — no new instruction needed — but **must be explicitly sequenced** by the CU's microprogram before `HALT`.

### 13.2 Normalisation in NLMS

The Python code uses **Normalized** LMS (NLMS). The true NLMS update divides by the input power:
```
w = w + (mu / (||x||^2 + epsilon)) * gradient
```

The code approximates this with `mu/B`. For a more accurate implementation the ISA already supports this via `VMAC` + `VREDUCE` to compute `||x||^2`, followed by `SDIV`. This is flagged as an **enhancement path** that requires no new instructions.

### 13.3 Data Type Recommendation

All signals are IEEE 754 float32. DSP48E2 slices are **integer multipliers**, not FP. For a proper FPGA implementation:

- **Option A:** Xilinx Floating-Point IP cores (adds ~5 cycle latency per operation)
- **Option B (Recommended):** **Q15 fixed-point** (16-bit signed) — fits natively in DSP48E2, doubles effective VLEN to 32, no IP license needed, standard in DSP accelerators

Fixed-point Q15 requires a scale analysis but is entirely compatible with the ISA — only the internal hardware of the MAC lanes changes.

### 13.4 Adder Tree Precision

When using VMAC with L=64 iterations, 16 values accumulate per lane. With 4 inner VMAC iterations per row, **64 values** are summed. In Q15 format, a **40-bit accumulator** (standard DSP48 cascade mode) prevents overflow without explicit saturation logic.

### 13.5 Selective Reset on ARM RESET Command

When the ARM writes `CSR_CTRL[RESET]`:
- All VRF registers (V0–V7) ← 0
- `y`, `e`, `g` scratchpad regions ← 0
- Peak detection registers ← 0
- **w[] is preserved** — it holds the adaptive filter state across blocks and must NOT be cleared
- AGU pointers reset to Phase 0 starting positions

### 13.6 Lane Interconnect for Reference Signal Distribution

Per Mahmood 2011, the `Mask_Net_Reg` CSR enables lanes to exchange data via local memory interconnect (Mesh/Star). For this application, `d_block` (reference signal) must reach all 3 PEs:
- If DMA can write to 3 scratchpads in one burst → no interconnect needed
- If DMA can only write to one PE → PE 0 receives `d_block`, then broadcasts to PE 1 and PE 2 via `CSR_MASK_NET`-controlled lane network using a **`VNET_RCV`** instruction (future addition)

### 13.7 Instruction Memory Size

The 5-phase microprogram takes approximately 80–120 instructions. At 32-bit/instruction, that is ≤480 bytes — **one 512-byte BRAM block** suffices, with room for future extensions.

The CU has its own **PC register** and FSM:
1. On `PHASE_END` → increment phase pointer; jump to next phase start
2. On `HALT` → wait for `CSR_CTRL[START]` assertion from ARM
3. On DMA-complete IRQ → auto-trigger Phase 0

---

## Summary: Instruction Set Quick Reference

| Mnemonic | Opcode[4:0] | Category | Cycle Cost | Primary Use |
|----------|------------|----------|-----------|-------------|
| `VMAC` | 00000 | Vec Arith | 1 | Phase 1 & 3 inner loop |
| `VSUB_V` | 00001 | Vec Arith | 1 | Phase 2 error |
| `VADD_V` | 00010 | Vec Arith | 1 | Phase 4 weight add |
| `VSCALE` | 00011 | Vec Arith | 1 | Phase 4 mu/B scaling |
| `VABS` | 00100 | Vec Arith | 1 | Phase 5 abs value |
| `VMOV_V` | 00101 | Vec Arith | 1 | Register copy / clear |
| `VREDUCE` | 00110 | Vec Arith | 4 | Dot product completion |
| `VMUL_V` | 00111 | Vec Arith | 1 | General multiply |
| `VLD` | 01000 | Vec Mem | 2 | Load 16 elements |
| `VST` | 01001 | Vec Mem | 2 | Store 16 elements |
| `AGU_SET` | 01010 | Vec Mem | 1 | Set AGU base |
| `AGU_INC` | 01011 | Vec Mem | 1 | Advance by VLEN |
| `AGU_SLIDE` | 01100 | Vec Mem | 1 | Slide window by 1 |
| `AGU_COL` | 01101 | Vec Mem | 1 | Set column-mode access |
| `VLD_S` | 01110 | Vec Mem | 2 | Broadcast scalar load |
| `VLD_CSR` | 01111 | Vec Mem | 2 | CSR → scalar register |
| `SMUL` | 10000 | Scalar | 2 | Scalar multiply |
| `SADD` | 10001 | Scalar | 1 | Scalar add |
| `SSUB` | 10010 | Scalar | 1 | tau = center_tap − idx |
| `SDIV` | 10011 | Scalar | 8–16 | mu/B computation |
| `SMOV` | 10100 | Scalar | 1 | Scalar register copy |
| `SIMM` | 10101 | Scalar | 1 | Load immediate |
| `SACC_CLR` | 10110 | Scalar | 1 | Clear accumulator |
| `LOOP_SET` | 10111 | Scalar | 1 | Set loop counter |
| `PKMAX` | 11000 | Special | 4 | Phase 5 peak scan |
| `PKIDX_OUT` | 11001 | Special | 1 | Write tau to CSR |
| `SYNC` | 11010 | Special | var | Memory fence |
| `PHASE_END` | 11011 | Special | 1 | Signal CU |
| `IRQ_FIRE` | 11100 | Special | 1 | Interrupt ARM |
| `NOP` | 11101 | Special | 1 | Pipeline fill |
| `HALT` | 11110 | Special | — | Await next block |
| `CSR_WR` | 11111 | Special | 2 | Write result to CSR |

---

*End of Document — ISA_Design.md*
