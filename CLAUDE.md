# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

ADS Semester 7 — design of a SIMD vector accelerator (FPGA, ARM host over AXI-Lite) for 3D sound-source localization. Four mics in a tetrahedron; three independent centered Block-NLMS filters (Mic2/3/4 vs reference Mic1) estimate TDOA delays tau_21, tau_31, tau_41. The architecture is based on Mahmood & Al-Jbaar, "Design and implementation of SIMD Vector Processor on FPGA" (IEEE ISIICT 2011). `onur-comparch-fall2025-lecture29a-simd-afterlecture.pdf` is background lecture material on SIMD.

Not a git repo. No build system, tests, or dependency manifest yet; there is no HDL in the repo yet.

## Layout

- `ISA_Design.md` — the ISA/microarchitecture spec (the main design artifact).
- `simulation_py/realtime_simulation.py` — Python **golden reference model** for the hardware. `RealTimeCenteredNLMS.process_block()` is exactly what each SIMD PE must compute per block.
- `simulation_py/simulation.ipynb` — exploratory notebook showing the algorithm's evolution: sample-by-sample NLMS → centered LMS → centered Block LMS (static source).
- `simulation_py/source.wav`, `source2.wav` — 16-bit PCM source audio.

## Running

Dependencies: `numpy`, `scipy`, `matplotlib` (notebook only).

```bash
python3 simulation_py/realtime_simulation.py   # loads source2.wav relative to the script's dir
```

It synthesizes a source moving in a 2 m-radius circle, simulates the four mic signals with fractional-delay interpolation, then streams blocks (B=128, L=64, mu=0.05) through three filters, printing estimated vs true delays. The notebook opens `source.wav` relative to the current directory, so run it from `simulation_py/`.

## How the Python model maps to the hardware

The ISA doc is written against `process_block()`; keep the two consistent when changing either.

| `process_block()` step | ISA phase | Key instructions |
|---|---|---|
| `x_full = [x_history | x_block]`, `d_delayed = d_full[:B]` | Phase 0 / history copy (§13.1) | `VLD`/`VST`, `AGU_SET` |
| `y = X @ w` | Phase 1 | `VMAC`, `VREDUCE`, `AGU_SLIDE` |
| `e = d_delayed - y` | Phase 2 | `VSUB_V` |
| `g = X.T @ e` | Phase 3 | `VMAC`, `VREDUCE`, `AGU_COL` |
| `w += (mu/B) * g` | Phase 4 | `VSCALE`, `VADD_V` |
| `center_tap - argmax(|w|)` | Phase 5 | `VABS`, `PKMAX`, `PKIDX_OUT`, `IRQ_FIRE` |

Design constants that recur across the spec: VLEN = 16 lanes, 8 vector regs (V0–V7), 8 scalar regs (S0–S7), 16 CSRs, 4 KB scratchpad per PE with a fixed memory map (§4.1, sized for B=128, L=64), 32-bit instructions `OPCODE[5]|DST[5]|SRC1[5]|SRC2[5]|IMM12`, 3 PEs in lockstep driven by one control unit. All 32 opcodes are allocated, so a new instruction means reworking the opcode table.

Things to keep in mind:
- The data matrix `X` is never materialized in hardware; the AGU generates sliding-window addresses. Rows are **reversed** in Python (`X[i] = x_full[i+L : i : -1]`, i.e. indices i+L down to i+1), so column j of `X` is `x_full[L-j .. L-j+B-1]`. The ISA doc's `AGU_COL` text (§7.6, §8.4) describes it as starting at offset `j`; check this indexing when working on Phase 3 or the AGU.
- `w` persists across blocks (it's the adaptive state) and must survive a RESET; `x_history` (L) and `d_history` (center_tap) must also carry over.
- "NLMS" is actually approximated with `mu/B`, not true input-power normalization (§13.2).
- The spec is float32 but recommends Q15 fixed-point for DSP48 slices (§13.3).
- The `realtime_localization_loop()` default args (B=2048, L=256) differ from the values `__main__` and the ISA use (B=128, L=64).
