"""
Builds the local HTML explainer pages in presentation/explainers/.
Each page is self-contained (figures embedded as data URIs) so it can be opened or shared on its own.

Usage:  python3 presentation/build_explainers.py
"""
import base64
import os

import explainer_isa_origins as origins

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
OUT = os.path.join(HERE, "explainers")

PAGES = [
    ("index.html", "Briefing"),
    ("basics.html", "Basics & glossary"),
    ("algorithm-results.html", "Algorithm & results"),
    ("isa.html", "ISA v1.1"),
    ("isa-origins.html", "ISA origins & justification"),
    ("microarchitecture.html", "Microarchitecture & memory"),
    ("qa.html", "Q&A prep"),
]

CSS = """
:root{
  --bg:#fafaf8; --surface:#ffffff; --ink:#131c33; --ink2:#4a5367; --muted:#6c7489; --line:#e2e5ec;
  --navy:#1b2f6b; --accent:#c9501f; --accent-soft:#fcece4; --link:#2459b8; --code-bg:#f2f4f8; --good:#1f7a4d;
  --fig-bg:#ffffff;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    color-scheme:dark;
    --bg:#0f131b; --surface:#161b26; --ink:#e7eaf1; --ink2:#b9c0cf; --muted:#8d95a8; --line:#2a3141;
    --navy:#9db4f0; --accent:#ff8c5a; --accent-soft:#2e1f19; --link:#86b1ff; --code-bg:#1c2230; --good:#5fd39a;
    --fig-bg:#ffffff;
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --bg:#0f131b; --surface:#161b26; --ink:#e7eaf1; --ink2:#b9c0cf; --muted:#8d95a8; --line:#2a3141;
  --navy:#9db4f0; --accent:#ff8c5a; --accent-soft:#2e1f19; --link:#86b1ff; --code-bg:#1c2230; --good:#5fd39a;
  --fig-bg:#ffffff;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 "Source Sans 3","Source Sans Pro","Segoe UI",system-ui,sans-serif}
a{color:var(--link)}
a:focus-visible,summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.shell{display:grid;grid-template-columns:240px minmax(0,1fr);gap:40px;max-width:1240px;margin:0 auto;padding-inline:24px;padding-block:32px 80px}
nav.side{position:sticky;top:24px;align-self:start;display:flex;flex-direction:column;gap:18px}
.brand{font-family:"Archivo","Arial Narrow",sans-serif;font-weight:700;font-stretch:90%;letter-spacing:.02em;color:var(--navy);font-size:15px;line-height:1.3}
.brand small{display:block;color:var(--muted);font-weight:500;letter-spacing:.06em;text-transform:uppercase;font-size:11px;margin-top:4px}
nav.side ol{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:2px;border-left:2px solid var(--line)}
nav.side li a{display:block;padding:6px 12px;margin-left:-2px;border-left:2px solid transparent;color:var(--ink2);text-decoration:none;font-size:14.5px}
nav.side li a:hover{color:var(--ink)}
nav.side li a[aria-current="page"]{border-left-color:var(--accent);color:var(--ink);font-weight:600}
.toc{font-size:13.5px;display:flex;flex-direction:column;gap:4px}
.toc a{color:var(--muted);text-decoration:none}
.toc a:hover{color:var(--ink)}
.toc b{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:600}
main{min-width:0;max-width:880px}
header.page{padding-bottom:20px;margin-bottom:28px;border-bottom:1px solid var(--line)}
.eyebrow{font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);font-weight:600}
h1,h2,h3{font-family:"Archivo","Arial Narrow",sans-serif;color:var(--navy);text-wrap:balance;line-height:1.2}
h1{font-size:clamp(28px,4vw,38px);font-weight:800;font-stretch:88%;margin:6px 0 10px}
h2{font-size:24px;font-weight:700;font-stretch:92%;margin:48px 0 12px;padding-top:8px}
h3{font-size:18px;font-weight:700;margin:28px 0 8px}
p,li{max-width:68ch}
.lede{font-size:18px;color:var(--ink2);max-width:62ch;margin:0}
code,pre,.mono{font-family:"JetBrains Mono",ui-monospace,Menlo,Consolas,monospace;font-size:.88em}
code{background:var(--code-bg);padding:1px 5px;border-radius:4px}
pre{background:var(--code-bg);border:1px solid var(--line);border-radius:8px;padding:14px 16px;overflow-x:auto;line-height:1.5;font-size:13.5px}
pre code{background:none;padding:0}
.cm{color:var(--muted)}
figure{margin:20px 0 26px}
figure .frame{background:var(--fig-bg);border:1px solid var(--line);border-radius:8px;padding:8px;overflow-x:auto}
figure img{display:block;width:100%;height:auto;min-width:640px}
figcaption{font-size:14px;color:var(--muted);margin-top:8px;max-width:72ch}
.tbl{overflow-x:auto;margin:14px 0 22px;border:1px solid var(--line);border-radius:8px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:14.5px;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-weight:600;color:var(--ink2);background:var(--code-bg);font-size:13px;letter-spacing:.02em}
tr:last-child td{border-bottom:none}
td.num,th.num{text-align:right}
.new{color:var(--accent);font-weight:600}
.key{background:var(--accent-soft);border:1px solid color-mix(in srgb,var(--accent) 35%,transparent);border-radius:8px;padding:14px 18px;margin:18px 0}
.key p{margin:.3em 0}
.key strong{color:var(--accent)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:20px 0 8px}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:12px 14px}
.stat b{display:block;font-family:"Archivo","Arial Narrow",sans-serif;font-size:26px;font-weight:800;color:var(--navy);font-variant-numeric:tabular-nums;line-height:1.1}
.stat span{font-size:13.5px;color:var(--ink2)}
.slide{display:grid;grid-template-columns:minmax(0,300px) minmax(0,1fr);gap:20px;padding:18px 0;border-top:1px solid var(--line)}
.slide img{width:100%;height:auto;border:1px solid var(--line);border-radius:6px;background:#fff}
.slide h3{margin-top:0}
.slide ul{margin:.3em 0;padding-left:20px}
.say{font-size:14px;color:var(--muted);margin-top:6px}
details{border:1px solid var(--line);border-radius:8px;background:var(--surface);margin:10px 0}
details>summary{cursor:pointer;padding:12px 16px;font-weight:600;color:var(--ink);list-style-position:outside}
details[open]>summary{border-bottom:1px solid var(--line)}
details>div{padding:4px 18px 10px}
.qa details>summary{font-weight:600}
.pill{display:inline-block;font-size:11.5px;letter-spacing:.05em;text-transform:uppercase;border:1px solid var(--line);border-radius:999px;padding:1px 8px;color:var(--muted);margin-right:6px;vertical-align:2px}
.bits{display:grid;grid-template-columns:5fr 5fr 5fr 5fr 12fr;border:1.5px solid var(--navy);border-radius:6px;overflow:hidden;min-width:560px;font-variant-numeric:tabular-nums}
.bits div{padding:10px 8px;text-align:center;border-right:1px solid var(--navy);background:var(--surface)}
.bits div:last-child{border-right:none}
.bits b{display:block;font-family:"Archivo","Arial Narrow",sans-serif;color:var(--navy)}
.bits span{font-size:12.5px;color:var(--muted)}
.scroll{overflow-x:auto;margin:14px 0}
a.term{color:inherit;text-decoration:underline dotted;text-decoration-color:var(--muted);text-underline-offset:3px}
a.term:hover{color:var(--link);text-decoration-color:var(--link)}
dl.gloss{margin:10px 0 24px}
dl.gloss dt{font-weight:600;color:var(--navy);margin-top:14px;scroll-margin-top:16px}
dl.gloss dd{margin:2px 0 0 0;max-width:68ch;color:var(--ink)}
dl.gloss dd .ours{display:block;color:var(--ink2);font-size:14.5px;margin-top:2px}
tr[id]{scroll-margin-top:16px}
figure.wide img{min-width:1000px}
ol.steps{padding-left:22px}
ol.steps li{margin:6px 0}
.diagram{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:12px;margin:18px 0 8px}
.diagram svg{display:block;width:100%;height:auto;max-width:680px;margin:0 auto}
footer{margin-top:64px;padding-top:16px;border-top:1px solid var(--line);font-size:13.5px;color:var(--muted)}
@media (max-width:860px){
  .shell{grid-template-columns:minmax(0,1fr);gap:20px;padding-inline:16px}
  nav.side{position:static}
  nav.side ol{flex-direction:row;flex-wrap:wrap;border-left:none;gap:6px}
  nav.side li a{border:1px solid var(--line);border-radius:999px;margin:0;padding:4px 12px}
  nav.side li a[aria-current="page"]{border-color:var(--accent)}
  .toc{display:none}
  .slide{grid-template-columns:minmax(0,1fr)}
  figure img{min-width:560px}
}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
"""
CSS += origins.ORIGINS_CSS

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..100,500..800'
         '&family=JetBrains+Mono:wght@400;600&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&display=swap">')


def img(name):
    with open(os.path.join(FIG, name), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def figure(name, alt, caption, wide=False):
    cls = ' class="wide"' if wide else ""
    return (f'<figure{cls}><div class="frame"><img src="{img(name)}" alt="{alt}"></div>'
            f'<figcaption>{caption}</figcaption></figure>')


def g(key, text):
    """Link a term to its definition on the Basics & glossary page."""
    return f'<a class="term" href="basics.html#g-{key}">{text}</a>'


def page(fname, title, eyebrow, h1, lede, toc, body):
    current = ' aria-current="page"'
    nav = "".join(f'<li><a href="{f}"{current if f == fname else ""}>{t}</a></li>' for f, t in PAGES)
    toc_html = "".join(f'<a href="#{a}">{t}</a>' for a, t in toc)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
{FONTS}
<style>{CSS}</style>
</head>
<body>
<div class="shell">
<nav class="side" aria-label="Explainer pages">
  <div class="brand">Block-LMS SIMD Accelerator<small>ADS · application feasibility</small></div>
  <ol>{nav}</ol>
  <div class="toc"><b>On this page</b>{toc_html}</div>
</nav>
<main>
<header class="page">
  <div class="eyebrow">{eyebrow}</div>
  <h1>{h1}</h1>
  <p class="lede">{lede}</p>
</header>
{body}
<footer>Numbers on these pages come from <code>simulation_py/feasibility_run.py</code>, <code>tracking_study.py</code> and
<code>isa_sim.py</code> (26 Sep 2026). Spec: <code>ISA_Design.md</code> v1.1.</footer>
</main>
</div>
</body>
</html>
"""


# =====================================================================================================
def build_index():
    slides = [
        ("slide_simulation.png", "1 · Simulation Results",
         ["Three plots, one per microphone pair: the delay the accelerator estimates (blue) against the true delay "
          "(black) while the source circles the array for 127 s.",
          "Grey bands: from 66 to 90 s the music is bass-only, and after 120 s it fades out. Without broadband "
          "sound no method can measure the delay, so the estimate holds its last value.",
          "Bars: fixed-point matches floating-point exactly (85.6 % both). The step size μ sets how fast the filter "
          "follows the source: μ = 0.05 → 47 %, μ = 0.5 → 85.6 % of blocks within ±1 sample.",
          "Weights: the filter learns a single spike, and the spike's position is the delay (τ21 = 32 − 19 = 13)."],
         "“It works, it works in fixed-point, and μ is the knob.”", "algorithm-results.html"),
        ("slide_isa.png", "2 · Instruction Set (v1.1)",
         ["Every instruction is 32 bits with the same five fields, so decoding is simple wiring.",
          "32 instructions in 4 groups. The orange ones are new in v1.1: they fix memory addressing and add a "
          "hardware loop (v1.0 had no working loop instruction).",
          "The inner loop: 4 × VMAC (64 multiply-adds per PE), VREDUCE, WSLIDE, SST. LOOP repeats it 128 times "
          "with no branch cost."],
         "“The whole block is 78 instructions, and we ran them in an instruction-level simulator.”", "isa.html"),
        ("slide_microarch.png", "3a · Microarchitecture: the system",
         ["The ARM runs our C driver: it writes the settings (μ, B, L), starts the DMA and reads the three delays "
          "when the interrupt arrives.",
          "The AXI DMA (standard IP) streams audio from DDR. Everything in the white box is our own Verilog.",
          "One control unit fetches and decodes each instruction once and sends it to three identical PEs, one per "
          "microphone pair.",
          "Inside each PE the data flows upwards: memory → window / vector registers → 16 MAC lanes → adder tree → "
          "ALUs and peak detector."],
         "“SIMD at two levels: 3 PEs × 16 lanes = 48 multiply-accumulates per instruction.”",
         "microarchitecture.html#system"),
        ("pe_datapath.png", "3b · Microarchitecture: inside one PE",
         ["Top: the control unit wired up. The PC and loop stack pick the next instruction, IMEM holds the program, "
          "decode waits until operands are ready, and the AGU computes addresses.",
          "Bottom: one PE's datapath. Memory banks, the window register (orange), vector registers, the B-port "
          "select, 16 DSP48E1 lanes (multiplier, adder, accumulator), the adder tree, and the scalar and vector "
          "ALUs.",
          "This completes the week-2 draw.io draft: its “PC? instructions?” box is the fetch path, and its AGU "
          "sketch is the address generator."],
         "“Every box here is a Verilog module we will write.”  (Use as a sixth slide, or keep it as a backup "
         "for questions.)", "microarchitecture.html#datapath"),
        ("slide_memory.png", "4 · Memory & Addressing",
         ["Sliding window: after one fill, the next row needs only one new sample from memory.",
          "The weights are stored reversed, so both matrix products read memory forwards. v1.0 read it the wrong "
          "way and reported −τ.",
          "Ring buffer: old samples stay in place, and the DMA fills the next block while this one is processed.",
          "16 banks, aligned rows: one load is one row across all banks, so no crossbar is needed."],
         "“No copies, no crossbar, one memory read per row.”", "microarchitecture.html#memory"),
        ("slide_feasibility.png", "5 · Timing & Feasibility",
         ["The program takes 2 695 cycles per block (measured by running it): 27 µs at 100 MHz. A new block "
          "arrives every 2 667 µs, so the accelerator is busy 1 % of the time.",
          "Resources on the smaller Zybo: 51 of 80 DSP blocks, 49 of 120 BRAM blocks. LUTs and clock speed come "
          "from synthesis.",
          "Verification: 600/600 blocks bit-exact; fixed = float on 99.6 %; 85.6 % within ±1 sample."],
         "“Feasible with a lot of room. The next step is RTL for one PE plus synthesis.”",
         "microarchitecture.html#timing"),
    ]
    s_html = ""
    for fig, title, pts, say, more in slides:
        s_html += (f'<div class="slide"><img src="{img(fig)}" alt="Slide figure: {title}"><div><h3>{title}</h3><ul>'
                   + "".join(f"<li>{p}</li>" for p in pts) + f'</ul><p class="say">Line to land: {say}</p>'
                   f'<p class="say"><a href="{more}">Full detail and explanation →</a></p></div></div>')
    body = f"""
<div class="key"><p><strong>New to the terms?</strong> Start with <a href="basics.html">Basics &amp; glossary</a>.
It explains μ, B, L, τ, LMS, SIMD, PE, lane, DSP48E1 and every other word used here, from zero. On every page,
underlined terms link to their definitions.</p></div>

<section id="claims">
<h2>What we claim today</h2>
<div class="stats">
  <div class="stat"><b>85.6 %</b><span>of blocks within ±1 sample of the true delay (μ = 0.5, fixed-point)</span></div>
  <div class="stat"><b>99.6 %</b><span>of blocks where fixed-point τ equals the floating-point golden model</span></div>
  <div class="stat"><b>600 / 600</b><span>blocks bit-exact: ISA program vs fixed-point model</span></div>
  <div class="stat"><b>27 µs</b><span>per block (2 695 cycles at 100 MHz) against a 2 667 µs budget</span></div>
</div>
<p>The application is a good fit for the accelerator. {g("blocklms", "Block LMS")} is two matrix–vector products
per block, and it reads memory in a perfectly regular pattern. The three microphone pairs run identical code, so
one instruction stream drives three {g("pe", "PEs")}: that is {g("simd", "SIMD")}. Every number above was produced
by a script in the repo, not estimated by hand.</p>
</section>

<section id="slides">
<h2>Slide by slide</h2>
<p>The slide figures are deliberately simple: hardware blocks and headline numbers only. Each one has a detailed
version, with every port, opcode, address and cycle, on the page linked under it. The Canva speaker notes carry the
same points.</p>
{s_html}
</section>

<section id="detail">
<h2>Where the detail went</h2>
<div class="tbl"><table>
<tr><th>Slide shows</th><th>Detail is on</th></tr>
<tr><td>Simulation: 3 tracking plots, 3 bars, weights</td><td><a href="algorithm-results.html">Algorithm &amp; results</a>: all 5 variants incl. 16-bit weights, μ/NLMS table, fixed-point formats</td></tr>
<tr><td>ISA: format, opcode map, inner loop as blocks</td><td><a href="isa.html">ISA</a>: field typing, every opcode with its operation, addressing modes, full 78-instruction listing</td></tr>
<tr><td>Microarchitecture: 3 PEs as hardware blocks</td><td><a href="microarchitecture.html">Microarchitecture</a>: the datapath walk-through, full system figure with ports, CSRs, latencies</td></tr>
<tr><td>Memory: window, ring, banks as pictures</td><td><a href="microarchitecture.html#memory">Memory &amp; addressing</a>: the reversed-w equations, ring offsets, memory map</td></tr>
<tr><td>Feasibility: time bar, 2 gauges, 3 numbers</td><td><a href="microarchitecture.html#timing">Timing &amp; resources</a>: per-phase cycles, full resource table</td></tr>
</table></div>
</section>

{origins.index_section()}
<section id="changed">
<h2>What changed since week 2</h2>
<ul>
<li><b>ISA v1.0 → v1.1.</b> 16 issues fixed. The important ones: there was no working loop instruction, address
pointers could not be selected, the X indexing reported −τ, and the memory map could not hold d_delayed contiguously
or fit the promised ping-pong buffers. Full list on the <a href="isa.html#changes">ISA page</a>.</li>
<li><b>Microarchitecture completed.</b> The red “PC? instructions?” box from the draw.io draft is now the control
unit: IMEM, fetch with hardware loops, scoreboard, AGU and sequencer. The “DRAFT” AGU has a register model, and the
“sliding window” idea is a concrete register. The <a href="microarchitecture.html#datapath">datapath diagram</a>
redraws the draft with every part filled in.</li>
<li><b>Number format decided by evidence.</b> Q1.15 samples and Q2.30 weights on DSP48E1, verified against
floating-point.</li>
<li><b>Real figures corrected.</b> The audio is 48 kHz (v1.0 assumed 16 kHz), and cycles per block are measured
(2 695, not ~7 400).</li>
</ul>
</section>

<section id="files">
<h2>Where things live</h2>
<div class="tbl"><table>
<tr><th>File</th><th>What it is</th></tr>
<tr><td><code>ISA_Design.md</code></td><td>Spec v1.1 with changelog, opcode table, microprogram, CSRs, microarchitecture</td></tr>
<tr><td><code>simulation_py/fixed_point_model.py</code></td><td>Bit-accurate model of one PE</td></tr>
<tr><td><code>simulation_py/isa_sim.py</code></td><td>Assembler + 3-PE instruction-level simulator + timing model</td></tr>
<tr><td><code>simulation_py/feasibility_run.py</code></td><td>Float vs fixed-point over the full 126.8 s scenario</td></tr>
<tr><td><code>simulation_py/tracking_study.py</code></td><td>μ vs NLMS tracking-lag study</td></tr>
<tr><td><code>presentation/figures/slide_*.png</code></td><td>Simplified slide figures (<code>draw_*.py</code>, <code>plot_results.py</code>)</td></tr>
<tr><td><code>presentation/figures/pe_datapath.png</code></td><td>PE datapath diagram (<code>draw_datapath.py</code>)</td></tr>
<tr><td><code>presentation/figures/*.png</code> (others)</td><td>Detailed figures used on these pages</td></tr>
</table></div>
</section>
"""
    toc = [("claims", "What we claim"), ("slides", "Slide by slide"), ("detail", "Where the detail went"), ("origin", "Where the ISA came from"),
           ("changed", "What changed"), ("files", "Where things live")]
    return page("index.html", "Feasibility Briefing", "Presenter briefing · 26 Sep 2026",
                "SIMD accelerator for 3-D sound localization",
                "What each slide shows, what to say, and which numbers back it up. The slides stay simple; every "
                "detail is on the other pages.", toc, body)


# =====================================================================================================
SYMBOLS = [
    # key, symbol, read as, meaning, our value
    ("fs", "f<sub>s</sub>", "sample rate", "How many samples per second each microphone delivers.", "48 000 per second"),
    ("tau", "τ, τ21, τ31, τ41", "“tau”, the delay",
     "What we want: how much later (in samples) the sound reaches Mic 2, 3 or 4 than Mic 1. Positive = that mic "
     "hears it later. The accelerator outputs these three numbers.", "−14 … +14 samples"),
    ("x", "x", "input signal", "The microphone being compared: Mic 2 for PE0, Mic 3 for PE1, Mic 4 for PE2.",
     "16-bit samples"),
    ("d", "d", "desired / reference", "The reference microphone, Mic 1. All three filters use the same d.",
     "16-bit samples"),
    ("B", "B", "block size",
     "How many new samples are processed together. The filter's weights are updated once per block.",
     "128 samples = 2.67 ms"),
    ("L", "L", "filter length, number of taps",
     "How many recent samples the filter looks at. It sets the range of delays the filter can find: about ±L/2.",
     "64 taps → ±32 samples"),
    ("ct", "CT", "center tap",
     "L/2. Mic 1 is delayed by this many samples so that negative delays can be measured too (section 6).", "32"),
    ("w", "w, w[j]", "weights, taps",
     "The L numbers the filter learns. w[j] multiplies the sample from j samples ago. After learning, the largest "
     "one marks the delay.", "64 numbers"),
    ("mu", "μ", "“mu”, step size or learning rate",
     "How big each correction to the weights is. Small μ: smooth but slow to follow a moving source. Large μ: "
     "follows quickly but is noisier, and too large makes the weights blow up. The ARM writes it to a register.",
     "0.5 recommended (0.05 in the original code)"),
    ("y", "y", "filter output", "The filter's prediction of the (delayed) Mic 1 signal.", "one per sample"),
    ("e", "e", "error", "e = d − y: how wrong each prediction was.", "one per sample"),
    ("g", "g", "gradient",
     "For each weight, which way and how much to change it to shrink the error: the average of e × x over the "
     "block.", "64 numbers"),
    ("X", "X", "input matrix",
     "A table with one row per sample in the block. Row i holds the L most recent Mic x samples at that moment. It "
     "is never stored: the window register produces it one row at a time.", "128 rows × 64 columns"),
    ("xfull", "x_full", "history + new block",
     "The last L samples of the previous block followed by the B new ones. Every row of X is a window into it.",
     "192 samples"),
    ("wrev", "w_rev", "reversed weights",
     "The weights stored back to front in hardware, so memory is always read forwards (Microarchitecture page).",
     "64 numbers"),
    ("kstar", "k*", "peak index", "Position of the largest |w_rev|. The delay is τ = k* − 31.", "0 … 63"),
    ("idx", "n, i, j, k", "indexes",
     "n: sample number (time). i: row, the sample within a block. j, k: tap number.", "—"),
    ("px", "P<sub>x</sub>", "input power", "Average of x² over a block. NLMS divides μ by L·P<sub>x</sub>.", "—"),
]

GLOSSARY = [
    ("Signal-processing words", [
        ("tdoa", "TDOA (time difference of arrival)",
         "The difference in arrival time of the same sound at two microphones. Three TDOAs locate a source in 3-D.",
         "τ21, τ31, τ41 in samples."),
        ("sample", "Sample",
         "One measurement of the microphone signal, a 16-bit whole number. Taken 48 000 times per second.", ""),
        ("fir", "FIR filter", "Finite impulse response filter: output = weighted sum of the last L inputs. "
         "See section 4.", "L = 64 taps."),
        ("tap", "Tap", "One weight of a FIR filter and the delayed input sample it multiplies.", ""),
        ("lms", "LMS (least mean squares)", "A way for a filter to learn its weights by repeatedly nudging them to "
         "shrink the error. See section 5.", ""),
        ("nlms", "NLMS (normalised LMS)", "LMS whose step is divided by the input power, so loud and quiet input "
         "adapt at the same speed. Stable for 0 &lt; μ &lt; 2.",
         "Optional: the ISA keeps SDIV for it. Study: 88 % within ±1 sample."),
        ("blocklms", "Block LMS", "LMS that freezes the weights for a block of B samples, then updates once. Makes "
         "the B outputs independent, so they can be computed in parallel. See section 7.", "B = 128."),
        ("centered", "Centered filter", "The reference is delayed by L/2 so the learned spike can sit on either side "
         "of the center: negative and positive delays both fit. See section 6.", "CT = 32."),
        ("gradient", "Gradient", "The direction to change the weights that reduces the error fastest.",
         "g = Xᵀe, computed in Phase 3."),
        ("converge", "Converge / adapt", "The weights settling to their final shape after enough updates.", ""),
        ("lag", "Tracking lag", "How far behind a moving source the estimate runs. Set mainly by μ.",
         "μ = 0.05: 3.7 s. μ = 0.5: 1.7 s."),
        ("float", "Floating-point / fixed-point", "Two ways to store fractions. See section 8.",
         "Hardware uses fixed-point."),
        ("q15", "Q1.15, Q2.30", "Fixed-point formats: 1 (or 2) bits before the binary point, 15 (or 30) after. "
         "Q1.15 holds −1 … +1 in 16 bits; Q2.30 holds −2 … +2 in 32 bits.",
         "Samples, y, e, μ: Q1.15. Weights and gradient: Q2.30."),
        ("saturate", "Saturate, round, shift", "Saturate: clip a too-large result to the largest value instead of "
         "wrapping to a negative number. Round: add half a step before dropping bits. Shift right by k: divide "
         "by 2<sup>k</sup>.", "Division by B = 128 is a shift by 7."),
    ]),
    ("The board and the FPGA", [
        ("zybo", "Zybo", "A Digilent development board built around a Xilinx Zynq-7000 chip.",
         "Z7-10 (smaller) or Z7-20 (larger)."),
        ("zynq", "Zynq-7000", "One chip with two halves: a processor side (PS) and an FPGA side (PL).", ""),
        ("ps", "PS (processing system)", "The ARM side of the Zynq: two ARM Cortex-A9 cores, caches and the DDR "
         "memory controller.", "Runs our C driver and the triangulation."),
        ("pl", "PL (programmable logic)", "The FPGA side of the Zynq, where our accelerator is built.", ""),
        ("fpga", "FPGA", "A chip full of configurable logic, small memories and multipliers that we wire into our own "
         "circuit by writing Verilog.", ""),
        ("ddr", "DDR", "The board's main memory (RAM), shared with the ARM.", "Audio buffers live here."),
        ("rtl", "Verilog, RTL", "Verilog is the hardware description language we write. RTL (register-transfer "
         "level) is the style: registers, and the logic between them.", ""),
        ("ip", "IP core, vendor-neutral", "An IP core is a ready-made hardware block, such as Xilinx's AXI DMA. "
         "Vendor-neutral means our own Verilog uses no Xilinx-only blocks, so it could move to another FPGA.", ""),
        ("synthesis", "Synthesis, LUT, FF, Fmax", "Synthesis turns Verilog into FPGA resources. LUTs (look-up tables) "
         "are the basic logic cells, FFs (flip-flops) store single bits, and Fmax is the fastest clock the result "
         "can run at.", "Not done yet: next step."),
        ("dsp", "DSP48E1", "A hard multiplier block in the Zynq-7000: a 25 × 18-bit multiplier, a 48-bit adder and "
         "a 48-bit result register (P) that can accumulate.", "One per MAC lane: 48 + 3 = 51. Z7-10 has 80."),
        ("bram", "BRAM18", "An 18-kilobit on-chip memory block, used here as 512 words × 32 bits.",
         "One per memory bank: 3 × 16 + 1 = 49. Z7-10 has 120."),
        ("clock", "Clock, cycle", "The accelerator does one step per clock tick. At 100 MHz one cycle is 10 ns.",
         "One block takes 2 695 cycles."),
    ]),
    ("How the ARM and the accelerator talk", [
        ("axi", "AXI", "ARM's standard family of on-chip bus protocols.", ""),
        ("axilite", "AXI4-Lite", "The simple AXI flavour for reading and writing single registers.",
         "The ARM writes settings and the program, and reads τ."),
        ("axistream", "AXI4-Stream", "A one-way flow of data words with a ready/valid handshake.",
         "Audio comes in this way: one 64-bit word = one sample from each of the 4 mics."),
        ("dma", "DMA (direct memory access)", "A helper block that copies data from DDR by itself, so the ARM does "
         "not have to move every sample.", "Xilinx AXI DMA, or the free Forencich core."),
        ("csr", "CSR (control and status register)", "A register the ARM can read or write through AXI4-Lite.",
         "16 of them: CTRL, STATUS, MU, B, L, TAU21, TAU31, TAU41, …"),
        ("irq", "IRQ (interrupt)", "A signal that tells the ARM “results are ready”, so it doesn't have to keep "
         "asking (polling).", "Raised after each block; cleared by the ARM."),
        ("driver", "Driver", "The C code on the ARM that sets up and uses the accelerator.", ""),
        ("cache", "Cache flush", "The ARM keeps copies of memory in its cache. Before the DMA reads a buffer, the ARM "
         "writes the cache back to DDR, because the DMA's port does not see the cache.", ""),
        ("backpressure", "Back-pressure", "When the receiver is not ready, the stream pauses instead of losing "
         "data.", ""),
        ("inputwriter", "Input writer", "Our block that receives the audio stream and writes each mic's samples "
         "into the right PE memories.", "Mic 2 → PE0, Mic 3 → PE1, Mic 4 → PE2; Mic 1 → all three."),
    ]),
    ("Parallel processing", [
        ("simd", "SIMD (single instruction, multiple data)", "One instruction works on many data items at once.",
         "One instruction → 3 PEs × 16 lanes = 48 multiply-accumulates."),
        ("pe", "PE (processing element)", "One copy of the datapath, with its own memory and registers.",
         "3 PEs, one per microphone pair."),
        ("lane", "Lane", "One slice of a PE that handles one number of a vector.",
         "16 lanes per PE, each with one DSP48E1."),
        ("lockstep", "Lockstep, broadcast", "All PEs get the same instruction and address in the same cycle and do "
         "the same thing, each on its own data.", ""),
        ("mac", "MAC (multiply-accumulate)", "acc = acc + a × b. The basic step of a filter.", ""),
        ("vector", "Vector, scalar", "A vector is a group of 16 numbers handled together (one per lane). A scalar is "
         "a single number.", ""),
    ]),
    ("Inside the processor", [
        ("isa", "ISA (instruction set architecture)", "The list of instructions a processor understands and how "
         "each is encoded in bits.", "32 instructions, 32 bits each."),
        ("opcode", "Instruction, opcode, field", "An instruction is one 32-bit command. Its fields are groups of "
         "bits: the opcode says which operation, the others say which registers and constants.", ""),
        ("imm", "Immediate (IMM)", "A constant stored inside the instruction itself, such as an offset, a loop "
         "count or a shift amount.", "12 bits."),
        ("register", "Register, register file", "A register is a small, fast storage slot. A register file is a "
         "group of them with read and write ports.",
         "V0–V7: vectors. S0–S7: scalars. A0–A7: addresses. W0–W7: window chunks."),
        ("microprogram", "Program, microprogram", "Our program for one block: 78 instructions that the ARM loads into "
         "IMEM once.", ""),
        ("imem", "IMEM", "Instruction memory inside the accelerator.", "512 × 32 bit, one BRAM18."),
        ("pc", "PC (program counter)", "The address of the next instruction to fetch.", ""),
        ("fetch", "Fetch, decode, issue", "Fetch: read the next instruction. Decode: work out what it means. Issue: "
         "send it to the units.", ""),
        ("pipeline", "Pipeline, latency", "Work is split into stages so a new instruction can start every cycle. "
         "Latency is how many cycles pass before a result can be used.",
         "Loads: 2 cycles. VREDUCE: 5 cycles."),
        ("stall", "Stall, hazard, scoreboard", "If an instruction needs a result that isn't ready yet (a read-after-"
         "write hazard), it waits: a stall. The scoreboard tracks when each register will be ready.", ""),
        ("loop", "Hardware loop (zero-overhead)", "LOOP tells the fetch unit to repeat the next few instructions N "
         "times. Jumping back costs no cycle, and no branch instruction is needed.", ""),
        ("alu", "ALU", "Arithmetic logic unit: add, subtract, compare. Drawn as a trapezoid with two inputs on the "
         "wide side.", ""),
        ("mux", "Mux (multiplexer)", "A switch that passes one of several inputs, chosen by a control signal.", ""),
        ("addertree", "Adder tree", "Adds 16 numbers into 1 in four levels: 16 → 8 → 4 → 2 → 1.", ""),
        ("acc", "Accumulator (VACC)", "The register that keeps the running sum of the multiply-accumulates.",
         "In each lane it is the DSP48E1's 48-bit P register."),
        ("peak", "Peak detector", "Hardware that finds the largest |w| and where it is.", "Its position gives τ."),
        ("assembler", "Assembler", "A tool that turns text such as VMAC W0, V4 into 32-bit instruction words.",
         "Part of isa_sim.py."),
    ]),
    ("Memory and addressing", [
        ("word", "Word, address", "A word is 32 bits. Memory is addressed in words.", ""),
        ("agu", "AGU (address generation unit)", "Computes memory addresses, so the data units don't have to.",
         "8 address registers, shared by all PEs."),
        ("postinc", "Post-increment", "Use an address, then add a step to it ready for next time.",
         "VLD V4, [A2]+16 loads 16 words, then A2 += 16."),
        ("bank", "Bank, interleaving", "Memory split into 16 independent parts. Word a is in bank a mod 16, so "
         "16 neighbouring words can be read in the same cycle.", ""),
        ("aligned", "Aligned access", "A 16-word access that starts at a multiple of 16: exactly one row across the "
         "banks.", "All our vector loads are aligned."),
        ("crossbar", "Crossbar, rotator", "A large switch network that would allow 16-word loads from any start "
         "address. We avoid needing one.", ""),
        ("ring", "Circular buffer (ring)", "Memory used as a loop: the address wraps from the end back to the start. "
         "Old data stays where it is.", "512 words per mic, per PE."),
        ("window", "Sliding-window register", "A shift register that holds the current row of X and moves by one "
         "sample per row.", "128 × 16 bit per PE."),
        ("memmap", "Memory map", "Which address ranges hold which data.", ""),
    ]),
    ("Checking the design", [
        ("golden", "Golden model", "The Python reference that everything is compared against.",
         "realtime_simulation.py"),
        ("fxmodel", "Fixed-point model", "A Python model that computes exactly what the hardware will: same bit "
         "widths, same rounding.", "fixed_point_model.py"),
        ("bitexact", "Bit-exact", "Every bit of every result matches.", ""),
        ("isasim", "ISA simulator", "Runs the real 32-bit program instruction by instruction on a model of the 3 PEs "
         "and counts cycles.", "isa_sim.py"),
    ]),
]

GOAL_SVG = """<svg viewBox="0 0 660 250" role="img" aria-label="Top view: a sound source on the left and four
microphones on the right; the path to Mic 2 is longer than the path to Mic 1">
<style>
.sv-l{stroke:var(--muted);stroke-width:1.5;stroke-dasharray:5 4;fill:none}
.sv-w{stroke:var(--line);stroke-width:2;fill:none}
.sv-m{fill:var(--surface);stroke:var(--navy);stroke-width:2}
.sv-s{fill:var(--accent)}
.sv-t{fill:var(--ink);font:600 14px 'Source Sans 3',system-ui,sans-serif}
.sv-n{fill:var(--ink2);font:13px 'Source Sans 3',system-ui,sans-serif}
</style>
<path class="sv-w" d="M 150 40 A 110 110 0 0 1 150 180"/><path class="sv-w" d="M 210 20 A 170 170 0 0 1 210 200"/>
<path class="sv-w" d="M 270 5 A 230 230 0 0 1 270 215"/>
<circle class="sv-s" cx="70" cy="110" r="14"/>
<text class="sv-t" x="70" y="146" text-anchor="middle">sound source</text>
<line class="sv-l" x1="84" y1="112" x2="430" y2="160"/><line class="sv-l" x1="84" y1="112" x2="530" y2="160"/>
<line class="sv-l" x1="84" y1="108" x2="480" y2="73"/><line class="sv-l" x1="84" y1="110" x2="480" y2="131"/>
<circle class="sv-m" cx="430" cy="160" r="11"/><circle class="sv-m" cx="530" cy="160" r="11"/>
<circle class="sv-m" cx="480" cy="73" r="11"/><circle class="sv-m" cx="480" cy="131" r="11"/>
<text class="sv-t" x="430" y="192" text-anchor="middle">Mic 1</text>
<text class="sv-t" x="530" y="192" text-anchor="middle">Mic 2</text>
<text class="sv-t" x="480" y="52" text-anchor="middle">Mic 3</text>
<text class="sv-t" x="500" y="126">Mic 4</text>
<text class="sv-n" x="330" y="222" text-anchor="middle">Top view, 10 cm between mics; Mic 4 sits 8 cm above the others.</text>
<text class="sv-n" x="330" y="242" text-anchor="middle">The path to Mic 2 is longer than to Mic 1, so τ21 &gt; 0.</text>
</svg>"""


def build_basics():
    sym_rows = "".join(f'<tr id="g-{k}"><td><b>{s}</b></td><td>{r}</td><td>{m}</td><td>{v}</td></tr>'
                       for k, s, r, m, v in SYMBOLS)
    gloss = ""
    toc_g = []
    for grp, items in GLOSSARY:
        gid = "gl-" + grp.lower().split()[0]
        toc_g.append((gid, grp))
        dl = "".join(f'<dt id="g-{k}">{t}</dt><dd>{d}' + (f'<span class="ours">Here: {o}</span>' if o else "")
                     + "</dd>" for k, t, d, o in items)
        gloss += f'<h3 id="{gid}">{grp}</h3><dl class="gloss">{dl}</dl>'
    body = f"""
<div class="key"><p><strong>How to use this page.</strong> Sections 1–8 explain the idea from the start, in order.
Section 9 is a glossary: every underlined term on the other pages links to its entry here.</p></div>

<section id="goal">
<h2>1. What we are building</h2>
<p>We want to know where a sound comes from. Four microphones sit at the corners of a small pyramid (a regular
tetrahedron with 10 cm edges). Sound travels at about 343 m/s, so it reaches the microphones at slightly different
times: the nearer one hears it first.</p>
<div class="diagram">{GOAL_SVG}</div>
<p>The time difference between two microphones is the <b>TDOA</b> (time difference of arrival). We measure three of
them, each against Mic 1: <b>τ21</b> (Mic 2 vs Mic 1), <b>τ31</b> and <b>τ41</b>. From those three numbers the ARM
processor computes where the source is (triangulation).</p>
<p>The accelerator does one job: it finds τ21, τ31 and τ41 from the live microphone signals, again and again, every
2.7 ms. Everything else (setup, triangulation) is C code on the ARM.</p>
</section>

<section id="samples">
<h2>2. Samples, and why delays are counted in samples</h2>
<ul>
<li>A microphone produces a voltage that rises and falls with the sound. A converter measures it at regular moments.
Each measurement is a <b>sample</b>: a 16-bit whole number.</li>
<li>We take 48 000 samples per second. That is the <b>sample rate</b>, f<sub>s</sub> = 48 kHz: one sample every
1/48 000 s = 20.8 µs.</li>
<li>In 20.8 µs sound travels 343 m/s × 20.8 µs = <b>7.15 mm</b>. So delays are measured in whole samples, and one
sample of delay means about 7 mm more path.</li>
<li>Across 10 cm the largest possible delay is 0.1 m ÷ 343 m/s = 292 µs ≈ <b>14 samples</b>. Every τ lies between
about −14 and +14.</li>
<li><b>Sign:</b> τ21 = (arrival time at Mic 2) − (arrival time at Mic 1). Positive: Mic 2 hears the sound later
(it is farther away). Negative: earlier.</li>
</ul>
</section>

<section id="symbols">
<h2>3. Every symbol, in plain words</h2>
<div class="tbl"><table>
<tr><th>Symbol</th><th>Read it as</th><th>What it means</th><th>Our value</th></tr>
{sym_rows}
</table></div>
</section>

<section id="filter">
<h2>4. What a filter is</h2>
<p>A <b>FIR filter</b> (finite impulse response) makes each output sample as a weighted sum of the last L input
samples:</p>
<pre><code>y[n] = w[0]·x[n] + w[1]·x[n−1] + w[2]·x[n−2] + … + w[L−1]·x[n−L+1]</code></pre>
<p>Each weight is a <b>tap</b>. Each tap costs one multiply and one add, a <b>multiply-accumulate (MAC)</b>, so a
64-tap filter costs 64 MACs per output sample.</p>
<p><b>The key trick.</b> If every weight is 0 except <code>w[5] = 1</code>, the output is the input delayed by 5
samples: <code>y[n] = x[n−5]</code>. A filter can represent a delay. So if a filter learns to turn Mic 2's signal
into Mic 1's, its weights become a single spike, and <b>the position of the spike is the delay</b>.</p>
{figure("sim_weights.png", "Learned filter weights: flat except for one peak at tap 19",
        "What a learned filter looks like: 64 weights, flat except for one spike. Here the spike is at tap 19, "
        "which means τ21 = 32 − 19 = 13 samples (why “32 −” is explained in section 6).")}
</section>

<section id="lms">
<h2>5. How the filter learns: LMS</h2>
<p>We don't know the delay, so we can't write the weights down. <b>LMS</b> (least mean squares) lets the filter
find them by guessing and correcting, thousands of times per second:</p>
<ol class="steps">
<li><b>Predict.</b> Run the filter on Mic x to get y, a guess of Mic 1.</li>
<li><b>Measure the error.</b> e = d − y (d is Mic 1).</li>
<li><b>Correct.</b> Nudge every weight in the direction that makes the error smaller. For tap j the nudge is
μ × e × (the input sample that tap j used). Taps whose inputs line up with the error grow; the others barely
move.</li>
<li><b>Repeat</b> with the next samples.</li>
</ol>
<p>After enough updates the weights settle into a spike at the tap that lines Mic x up with Mic 1. The name
“least mean squares” comes from what the procedure minimises: the average of e².</p>
<h3>What μ does</h3>
<p>μ (“mu”, the step size) scales every correction. With μ = 0.05, the value in the original Python, each block
moves the weights only a little. When the source moves, the spike follows about <b>3.7 s late</b> and 47 % of
estimates are within ±1 sample. With μ = 0.5 the lag drops to <b>1.7 s</b> and 85.6 % are within ±1 sample. Too large
a μ makes the weights overshoot and jitter, and past a limit they blow up. μ is a register the ARM writes (the MU
CSR), so it can change without new hardware.</p>
<h3>NLMS</h3>
<p><b>Normalised LMS</b> divides the step by the input's power (L × P<sub>x</sub>), so loud and quiet sounds adapt at
the same speed, and it is stable for any 0 &lt; μ &lt; 2. The Python class is named “NLMS” but actually uses μ/B,
which is not normalised. Our study shows true block NLMS (μ = 0.64) reaches 88 %.</p>
</section>

<section id="centered">
<h2>6. “Centered”: allowing negative delays</h2>
<p>A filter can only use past samples; it can't look into the future. Suppose Mic 2 hears the sound <i>later</i> than
Mic 1 (τ21 &gt; 0). Then the Mic 2 sample that matches Mic 1's current sample has not arrived yet, and the filter
would need a future input.</p>
<p>The fix is to delay Mic 1 by <b>CT = L/2 = 32 samples</b> before comparing. Now the spike sits at tap
<code>j = 32 − τ</code>, which lies between 0 and 63 for any τ from −31 to +32. That is why the delay is read as
<b>τ = 32 − (spike position)</b>, and why L = 64 taps cover about ±32 samples: more than the ±14 that 10 cm allows.
In hardware the delay of Mic 1 costs nothing: the input writer just stores Mic 1 32 places further along.</p>
</section>

<section id="block">
<h2>7. Block LMS: why 128 samples at a time</h2>
<p>Plain LMS updates the weights after every sample, so sample n+1 has to wait for sample n's update. That chain is
sequential and hard to run in parallel.</p>
<p><b>Block LMS</b> freezes the weights for a block of B = 128 samples. Inside a block all 128 predictions use the
same weights, so they are independent and can be computed in parallel. Then the weights are updated once, with
the average correction of the whole block. Per block, each filter runs five phases:</p>
<div class="tbl"><table>
<tr><th>Phase</th><th>In words</th><th>Math</th><th class="num">Work</th></tr>
<tr><td>1 Filter</td><td>predict all 128 outputs</td><td><code>y = X w</code></td><td class="num">128 × 64 = 8 192 MACs</td></tr>
<tr><td>2 Error</td><td>compare each prediction with Mic 1</td><td><code>e = d_delayed − y</code></td><td class="num">128 subtractions</td></tr>
<tr><td>3 Gradient</td><td>work out the correction for each of the 64 weights</td><td><code>g = Xᵀ e</code></td><td class="num">8 192 MACs</td></tr>
<tr><td>4 Update</td><td>apply the correction</td><td><code>w ← w + (μ/B)·g</code></td><td class="num">64 MACs</td></tr>
<tr><td>5 Peak</td><td>find the largest weight and turn it into τ</td><td><code>τ = 32 − argmax|w|</code></td><td class="num">64 compares</td></tr>
</table></div>
<p><b>X</b> is the 128 × 64 table of input windows: row i holds the 64 most recent Mic x samples at moment i.
<code>X w</code> means “for every row, multiply by the weights and add up”: a matrix–vector product.
<code>Xᵀ e</code> uses the same table by columns. Phases 1 and 3 are 99 % of the work, and both read rows or columns
of the same table. The hardware is built around that.</p>
<h3>Why B = 128 and L = 64</h3>
<p>These are the values the golden model's demo uses, and we kept them. They also suit the hardware well:</p>
<ul>
<li>L = 64 covers delays up to about ±32 samples, more than twice the ±14 that 10 cm allows.</li>
<li>Both are multiples of 16, the number of lanes: a row (64 taps) is exactly 4 vector operations and a column (128
samples) exactly 8.</li>
<li>B is a power of two, so “divide by B” is a right shift by 7 bits, which costs nothing in hardware.</li>
<li>64 weights fit in 4 vector registers and 128 errors in 8, so they stay in registers for a whole phase.</li>
<li>B = 128 at 48 kHz gives a new delay estimate every 2.67 ms (375 per second).</li>
</ul>
<p>A larger B gives fewer, smoother updates; a larger L gives a wider delay range and more work. The accelerator is
busy only 1 % of the time, so L = 256 would still fit.</p>
</section>

<section id="fixed">
<h2>8. Numbers in hardware: fixed-point</h2>
<p>Fractions can be stored as <b>floating-point</b> (a number plus an exponent, like 1.23 × 10⁻⁴) or as
<b>fixed-point</b> (a whole number with an agreed scale). The FPGA's multiplier blocks multiply whole numbers, so
fixed-point is far cheaper.</p>
<p>A <b>Q-format</b> name says how many bits sit before and after the binary point:</p>
<ul>
<li><b>Q1.15</b>: 16 bits, 1 sign bit and 15 fraction bits. Holds −1 to just under +1 in steps of 1/32 768; the
value is the stored integer ÷ 32 768. Audio samples, y and e use it. μ = 0.5 is stored as 16 384.</li>
<li><b>Q2.30</b>: 32 bits, range −2 to +2, steps of about 10⁻⁹. Used for the weights, because each update is tiny.
With 16-bit weights the updates get lost and accuracy drops from 47.0 % to 43.4 %.</li>
<li><b>48-bit accumulator</b>: the DSP48E1's P register. Large enough that sums of 64 or 128 products never
overflow.</li>
</ul>
<p><b>Saturate</b>: if a result is too big for its format, clip it to the largest value instead of letting it wrap
round to a negative number. <b>Round</b>: add half a step before dropping bits. <b>Shift right by k</b>: divide by
2<sup>k</sup>.</p>
<p>Result: fixed-point gives exactly the same τ as floating-point on 99.6 % of 47 547 blocks, with identical
accuracy.</p>
</section>

<section id="glossary">
<h2>9. Glossary</h2>
<p>Grouped by topic. “Here:” notes how the term applies to our design.</p>
{gloss}
</section>

<section id="timing">
<h2>10. How the timing numbers are worked out</h2>
<pre><code>block period  = B / fs            = 128 / 48 000        = 2.667 ms = 2 667 µs
accelerator   = cycles / clock    = 2 695 / 100 MHz     = 26.95 µs ≈ 27 µs
busy fraction = 27 / 2 667                              ≈ 1.0 %   (≈ 99× headroom)
work needed   = 3 filters × 2 products × L × fs
              = 3 × 2 × 64 × 48 000                     ≈ 18.4 million MACs per second
peak compute  = 48 MACs per cycle × 100 MHz             = 4.8 billion MACs per second</code></pre>
<p>The 2 695 cycles come from the ISA simulator running the real program, including every cycle spent waiting for
a result. The count is the same for every block, because the program has no data-dependent branches.</p>
</section>
"""
    toc = [("goal", "1 What we build"), ("samples", "2 Samples"), ("symbols", "3 Every symbol"),
           ("filter", "4 Filters"), ("lms", "5 LMS and μ"), ("centered", "6 Centered"), ("block", "7 Block LMS"),
           ("fixed", "8 Fixed-point"), ("glossary", "9 Glossary"), ("timing", "10 Timing maths")]
    return page("basics.html", "Basics and Glossary", "Start here", "The basics, from zero",
                "Everything the other pages assume: the problem, every symbol (μ, B, L, τ …), how the filter "
                "learns, and every hardware word. No background needed.", toc, body)


# =====================================================================================================
def build_results():
    body = f"""
<section id="problem">
<h2>The problem in one paragraph</h2>
<div class="key"><p><strong>Symbols.</strong> τ, μ, B, L, w, x, d, y, e and g are all defined in plain words in
<a href="basics.html#symbols">Basics §3</a>. Underlined terms link to the glossary.</p></div>
<p>Four microphones sit on a tetrahedron with 10 cm edges. Sound from one source reaches them at slightly different
times. If we know the three delays of Mic 2, 3 and 4 relative to Mic 1 ({g("tau", "τ21, τ31, τ41")}), the ARM can
solve the {g("tdoa", "TDOA")} equations for the source position. At 48 kHz, one {g("sample", "sample")} is
343 / 48 000 = 7.15 mm of path difference. The largest possible delay across a 10 cm baseline is
0.1 / 343 × 48 000 ≈ <b>14 samples</b>.</p>
</section>

<section id="lms">
<h2>Why an adaptive filter finds a delay</h2>
<p>An {g("lms", "LMS")} filter learns {g("w", "weights")} <code>w</code> so that filtering Mic x predicts Mic 1.
If Mic 1 is just Mic x shifted in time, the best filter is a single spike (a delayed impulse): all weights zero except
one. After adaptation, the position of the largest weight <em>is</em> the delay. <a href="basics.html#filter">Basics
§4–5</a> explains this step by step.</p>
<p><b>{g("centered", "Centered")}:</b> the reference is delayed by <code>{g("ct", "CT")} = L/2 = 32</code> samples, so
the spike sits at tap <code>32 − τ</code>. That lets the filter represent negative delays too (sound reaching Mic x
before Mic 1), within about ±32 samples.</p>
<p><b>{g("blocklms", "Block LMS")}:</b> the weights change once per block of {g("B", "B")} = 128 samples instead of
every sample. Within a block all 128 outputs are independent, so the work becomes two matrix–vector products. That is
what makes it data-parallel: in sample-by-sample LMS every sample depends on the update from the one before.</p>
<div class="tbl"><table>
<tr><th>Phase</th><th>Operation</th><th class="num">Work per filter</th></tr>
<tr><td colspan="3" class="say">MAC = one multiply and one add. X is the 128 × 64 table of input windows
(<a href="basics.html#g-X">definition</a>).</td></tr>
<tr><td>1 Filter</td><td><code>y = X w</code> (X is 128 × 64, never stored)</td><td class="num">8 192 MAC</td></tr>
<tr><td>2 Error</td><td><code>e = d_delayed − y</code></td><td class="num">128 sub</td></tr>
<tr><td>3 Gradient</td><td><code>g = Xᵀ e</code></td><td class="num">8 192 MAC</td></tr>
<tr><td>4 Update</td><td><code>w += (μ/B) g</code></td><td class="num">64 MAC</td></tr>
<tr><td>5 Peak</td><td><code>τ = 32 − argmax |w|</code></td><td class="num">64 compare</td></tr>
</table></div>
{figure("sim_weights.png", "Filter weights of the Mic2 filter at 63 s showing a single peak at tap 19",
        "The learned Mic2 filter at t = 63 s: float (black) and fixed-point (blue dashed) overlap. Peak at tap 19, "
        "so τ21 = 32 − 19 = 13 samples.")}
</section>

<section id="setup">
<h2>Simulation setup</h2>
<ul>
<li>Source audio: <code>source2.wav</code>, 48 kHz, 126.8 s (channel 0).</li>
<li>The source moves once around a 2 m circle at 0.5 m height. Each microphone signal is the source audio delayed
by its own exact travel time, which is usually a fraction of a sample (computed by interpolating between samples).
So the true delay changes smoothly and is not a whole number.</li>
<li>{g("B", "B")} = 128, {g("L", "L")} = 64: 47 547 blocks × 3 filters. The first 0.5 s is left out of the
accuracy numbers, because the weights start at zero and need time to {g("converge", "converge")}.</li>
<li>“Within ±1 sample” means the estimate (a whole number) is at most 1 away from the true delay rounded to the
nearest whole sample.</li>
<li>“Float” means the golden model in double-precision floating-point. “Fixed-point” means the bit-accurate model
of the hardware (<a href="basics.html#fixed">Basics §8</a>).</li>
</ul>
</section>

<section id="tracking">
<h2>Tracking results</h2>
{figure("sim_tracking.png", "Estimated versus true delay for the three mic pairs over 127 seconds",
        "Fixed-point accelerator model with μ = 0.5 (blue) against the true TDOA (black). The grey bands mark "
        "bass-only audio (66–90 s) and the fade-out (after 120 s).")}
<h3>How to read this plot</h3>
<p>Each panel is one microphone pair. The black curve is the true delay, computed from the geometry: it rises and
falls smoothly as the source goes round the circle. The blue line is what the fixed-point accelerator model outputs
after each block. It is a staircase because the estimate is a whole number of samples. Where blue sits slightly
right of black, the estimate is running late: that is the {g("lag", "tracking lag")}, set mainly by μ.</p>
<h3>Why the estimate freezes in the grey bands</h3>
<p>From 66 to 90 s the music is almost pure bass: its spectral centroid (the “average frequency”) is 108–222 Hz. A
low-frequency sound looks almost the same when shifted by a few samples, because one wave period is hundreds of
samples long. So the filter cannot tell a 14-sample shift from its neighbours, and it keeps its old peak. After about
120 s the audio fades to silence, and there is nothing left to compare. This is a limit of the input signal, not of
the hardware. Real systems whiten the signal first (PHAT weighting, which equalises all frequencies), or hold the
last estimate when the signal is too poor.</p>
</section>

<section id="mu">
<h2>Step size μ decides the tracking lag</h2>
<p>The golden model uses <code>w += (μ/B)·g</code>: each block, every weight moves by μ times the average
correction. {g("mu", "μ")} is the step size (<a href="basics.html#lms">Basics §5</a>). Despite the class name, that
is not normalised by input power. With μ = 0.05 the filter reacts slowly and lags the moving source by several
seconds. μ is a {g("csr", "CSR")}, so changing it costs nothing in hardware.</p>
<p>Columns: <b>mean |error|</b> is the average distance between estimate and true delay, in samples. <b>Within ±1</b>
is the share of blocks at most one sample off. <b>Best-fit lag</b> is how far the whole estimate curve has to be
shifted in time to line up best with the true curve.</p>
<div class="tbl"><table>
<tr><th>Update rule</th><th class="num">μ</th><th class="num">Mean |error| (samples)</th><th class="num">Within ±1</th><th class="num">Best-fit lag</th></tr>
<tr><td>μ/B (current)</td><td class="num">0.05</td><td class="num">1.88</td><td class="num">47.0 %</td><td class="num">3.67 s</td></tr>
<tr><td>μ/B</td><td class="num">0.2</td><td class="num">1.40</td><td class="num">77.3 %</td><td class="num">2.40 s</td></tr>
<tr><td>μ/B</td><td class="num">0.5</td><td class="num">1.18</td><td class="num">85.6 %</td><td class="num">1.73 s</td></tr>
<tr><td>block NLMS</td><td class="num">0.3</td><td class="num">1.26</td><td class="num">83.8 %</td><td class="num">1.93 s</td></tr>
<tr><td>block NLMS</td><td class="num">0.64</td><td class="num">1.09</td><td class="num">88.0 %</td><td class="num">1.53 s</td></tr>
<tr><td>block NLMS</td><td class="num">1.0</td><td class="num">1.04</td><td class="num">88.8 %</td><td class="num">1.33 s</td></tr>
</table></div>
<p>{g("nlms", "Block NLMS")} divides the step by <code>L · P<sub>x</sub></code> (the block's input power), which
makes it independent of loudness. It is stable for 0 &lt; μ &lt; 2. With plain μ/B, a large μ can diverge on loud input,
because the stability limit shrinks as the power grows. That is the reason to prefer NLMS and to keep
<code>SDIV</code> in the ISA (one division per block).</p>
</section>

<section id="fixed">
<h2>Fixed-point results</h2>
<p>The hardware stores numbers as {g("q15", "fixed-point")} integers, not floating-point
(<a href="basics.html#fixed">Basics §8</a>). The question is whether that changes the answer. It doesn't, as long as
the weights get 32 bits.</p>
{figure("sim_accuracy.png", "Bar chart of accuracy for float and fixed-point variants",
        "Share of blocks within ±1 sample. Blue bars are the hardware formats; grey are references.")}
<div class="tbl"><table>
<tr><th>Quantity</th><th>Format</th><th>Why</th></tr>
<tr><td>x, d, y, e</td><td>Q1.15 (16 bit)</td><td>audio is 16-bit PCM already; fits the DSP48E1 18-bit port</td></tr>
<tr><td>w</td><td>Q2.30 (32 bit), multiplied as Q2.23</td><td>updates are tiny (μ·mean(x·e)); 16-bit weights lose them</td></tr>
<tr><td>accumulator</td><td>48 bit (DSP48E1 P register)</td><td>Phase 1 peaks at ~47 bits, Phase 3 at ~39 bits</td></tr>
<tr><td>g</td><td>Q2.30</td><td>the adder-tree shift by log2 B = 7 turns the sum into the mean, which is the ÷B</td></tr>
</table></div>
<ul>
<li>32-bit weights: fixed-point τ equals float τ on <b>99.6 %</b> of 47 547 blocks (μ = 0.05) and 99.55 % (μ = 0.5).
Accuracy is identical to one decimal.</li>
<li>16-bit weights: only 89.1 % agreement and accuracy drops from 47.0 % to 43.4 %. This is the evidence for storing
w in 32 bits.</li>
</ul>
</section>

<section id="limits">
<h2>Honest limits</h2>
<ul>
<li><b>Integer resolution.</b> One sample equals 7.15 mm of path difference. Across a 10 cm baseline that is
Δ(sin θ) = 0.0715, about 4° of direction when the source is roughly side-on to the pair (broadside). Parabolic interpolation around the peak (three weights, on the ARM)
would give sub-sample resolution.</li>
<li><b>Simulated room.</b> There is no reverberation and no noise, and the mics have equal gains. A real room will
lower accuracy, so the next test should use recorded 4-channel audio.</li>
<li><b>One scenario.</b> Accuracy depends on the audio content, as the bass-only section shows.</li>
</ul>
</section>
"""
    toc = [("problem", "The problem"), ("lms", "Why LMS finds delays"), ("setup", "Setup"), ("tracking", "Tracking"),
           ("mu", "Step size μ"), ("fixed", "Fixed-point"), ("limits", "Limits")]
    return page("algorithm-results.html", "Algorithm and Results", "Simulation", "Algorithm and simulation results",
                "How centered Block-LMS turns into a delay estimate, how well it tracks a moving source, and what "
                "the fixed-point format costs.", toc, body)


# =====================================================================================================
# The ISA content lives in explainer_isa_origins.py, shared by the ISA page and the origins page.
def build_isa():
    toc, body = origins.isa_body(figure)
    return page("isa.html", "ISA v1.1", "Instruction set", "Instruction set architecture, v1.1",
                "What an instruction set is here, the format and why each field is that wide, all 32 instructions "
                "in plain words, the addressing modes, where every shift amount comes from, and the exact program "
                "the simulator runs, phase by phase and cycle by cycle.", toc, body)


def build_origins():
    toc, body = origins.origins_body()
    return page("isa-origins.html", "ISA Origins", "Instruction set",
                "Where the ISA came from, and why every instruction is there",
                "Which of the 32 instructions came from v1.0 or the reference paper and which are new, one card per "
                "instruction with its justification and precedent, an honest look at the 12 the program never "
                "runs, and the reasoning behind every design parameter.", toc, body)

# =====================================================================================================
def build_uarch():
    body = f"""
<div class="key"><p><strong>Two diagrams.</strong> The first shows the whole system as hardware blocks: what
connects to what. The second opens up one {g("pe", "PE")} and shows every register, {g("mux", "mux")} and
{g("alu", "ALU")} with its wires, in the style of the week-2 draw.io draft. Terms are explained in
<a href="basics.html#glossary">the glossary</a>.</p></div>

<section id="system">
<h2>1. The system in one picture</h2>
{figure("slide_microarch.png", "System block diagram: ARM and DDR on the left, DMA, and the accelerator with a shared control unit and three identical PEs",
        "The slide version. Left: the ARM side of the Zynq. Right: the FPGA side, where the white box is our own "
        "Verilog. Instructions come down from the control unit; audio samples come up from the input writer.")}
<h3>Follow the data</h3>
<ol class="steps">
<li><b>Setup, once.</b> The ARM writes our 78-instruction program into the accelerator's instruction memory and
the settings (μ, B, L) into its {g("csr", "control registers")}, over {g("axilite", "AXI4-Lite")}.</li>
<li><b>Audio in.</b> The ARM starts the {g("dma", "DMA")}. It reads 4-microphone audio from {g("ddr", "DDR")}
memory and streams it into the accelerator over {g("axistream", "AXI4-Stream")}: each 64-bit word is one sample from
each of the 4 mics.</li>
<li><b>Sorting.</b> The {g("inputwriter", "input writer")} splits every word: Mic 2 goes to PE0's memory, Mic 3 to
PE1, Mic 4 to PE2, and Mic 1 to all three (every filter compares against Mic 1).</li>
<li><b>Compute.</b> When 128 new samples are in, the control unit runs the program. Every cycle it fetches one
instruction, decodes it once, and sends the same instruction and memory address to all 3 PEs.</li>
<li><b>Result.</b> Each PE's peak detector writes its delay into a register: τ21 from PE0, τ31 from PE1, τ41 from
PE2.</li>
<li><b>Hand-back.</b> The control unit raises an {g("irq", "interrupt")}. The ARM reads the three delays and
computes the source position. Meanwhile the next block is already arriving.</li>
</ol>
<h3>Why this is SIMD</h3>
<p>{g("simd", "SIMD")} means one instruction, many data. Here it happens twice over. The three PEs get the
<i>same</i> instruction but hold <i>different</i> microphones' data (Mic 2, 3, 4). Inside each PE, the 16
{g("lane", "lanes")} apply that instruction to 16 numbers at once. So one <code>VMAC</code> instruction does
3 × 16 = 48 {g("mac", "multiply-accumulates")}. Only the control unit exists once; everything that holds data is
copied per PE. That split, shared control and copied data, is the SIMD architecture of the reference paper (Mahmood
&amp; Al-Jbaar 2011).</p>
<h3>What each block in a PE is for</h3>
<div class="tbl"><table>
<tr><th>Block</th><th>In plain words</th></tr>
<tr><td>Local memory · 16 banks</td><td>This PE's own storage: incoming samples, weights, intermediate results. Split into 16 {g("bank", "banks")} so 16 numbers can be read in one cycle.</td></tr>
<tr><td>Window register</td><td>Holds the current row of the input table X. Moves along by one sample per row, so the next row costs one memory read (<a href="#memory">memory section</a>).</td></tr>
<tr><td>Vector registers</td><td>Eight registers of 16 numbers each. The 64 weights stay here for the whole filter phase.</td></tr>
<tr><td>16 MAC lanes</td><td>Sixteen {g("dsp", "DSP48E1")} multiplier blocks. Each multiplies one sample by one weight and adds to its own running sum, every cycle.</td></tr>
<tr><td>Adder tree</td><td>Adds the 16 running sums into one number: one filter output.</td></tr>
<tr><td>Vector ALU</td><td>Adds and subtracts whole vectors, e.g. error = Mic 1 − prediction, and weights + correction.</td></tr>
<tr><td>Scalar unit</td><td>Single-number registers and arithmetic: holds μ and each adder-tree result before it is stored.</td></tr>
<tr><td>Peak detector</td><td>Scans the 64 weights for the largest and turns its position into τ.</td></tr>
</table></div>
</section>

<section id="datapath">
<h2>2. Inside one PE: the datapath</h2>
{figure("pe_datapath.png", "Datapath: control unit with PC, IMEM, decode, AGU and CSRs on top; one PE with memory, window register, vector registers, 16 DSP48E1 lanes, adder tree and scalar registers below",
        "Top: the shared control unit. Bottom: one PE. Solid arrows are data wires; dashed ‘op’ boxes are the "
        "operation the decoded instruction selects for that unit; orange is the sliding-window path.", wide=True)}
<h3>How it maps to the week-2 draft</h3>
<div class="tbl"><table>
<tr><th>In the week-2 draw.io draft</th><th>In this diagram</th></tr>
<tr><td>Pink “PC? instructions?” box</td><td>The fetch path: PC register, the next-PC {g("mux", "mux")} (PC + 1, or jump back to the loop start), the loop stack, IMEM and the instruction register IR, then decode</td></tr>
<tr><td>“DRAFT” AGU: Offset → ALU → ADR pointer, with feedback</td><td>The {g("agu", "AGU")}: IMM (the offset) and an adder update the address registers A0–A7, with a circular wrap for the rings</td></tr>
<tr><td>Scratchpad memory 4 KB BRAM, “sliding window”</td><td>Local data memory (16 BRAM18 banks) and the window register W0–W7</td></tr>
<tr><td>General-purpose registers S0–S7 + ALU with CTRL-Op</td><td>Scalar registers S0–S7 + scalar ALU with its op box</td></tr>
<tr><td>VRF + MAC lanes (DSP48-0 … 15) with CTRL-Op</td><td>Vector registers V0–V7, the B-port select and » sh, and 16 DSP48E1 lanes, each drawn as ×, + and the P accumulator</td></tr>
<tr><td>Adder tree 16 to 1, feeding back to the registers</td><td>Adder tree → round / shift / saturate → scalar registers</td></tr>
<tr><td>Control State Regs (CSR)</td><td>Control &amp; status registers, reached by the ARM over AXI4-Lite</td></tr>
</table></div>
<h3>Follow one filter output through the hardware</h3>
<p>Phase 1 computes the 128 filter outputs y[i]. One output takes 7 instructions (<a href="isa.html#program">the
loop on the ISA page</a>). This is what each of them does to the wires in the diagram:</p>
<ol class="steps">
<li><b>Before the loop</b>, <code>VLD</code> loads the 64 weights from memory into V4–V7 (the “16 words” wire from
memory into the vector registers). <code>WLD</code> fills the window register W0–W3 with the first 64 input samples
(the same wire, into the window).</li>
<li><b><code>VMAC.C W0, V4</code></b>. The 8 : 1 mux picks window chunk W0 (16 samples) and the B-port select sends
it to the B input of all 16 DSP48E1s. Register V4 (16 weights) goes through <b>» sh</b>, which drops 7 bits so the
32-bit weight fits the multiplier's 25-bit A input. Each lane multiplies its sample by its weight and puts the
product in its P register. <code>.C</code> means start from zero rather than adding to the old value.</li>
<li><b>Three more <code>VMAC</code>s</b> do the same with W1×V5, W2×V6 and W3×V7, each adding to P through the
feedback loop drawn in every lane. Now each lane's P holds the sum of 4 products, and all 64 products are done.</li>
<li><b><code>VREDUCE</code></b>. The {g("addertree", "adder tree")} adds the 16 P values into one number. Round /
shift / saturate turns it back into a 16-bit sample, and it lands in scalar register S1.</li>
<li><b><code>WSLIDE</code></b>. The 16 : 1 mux on top of the memory reads one word, the next input sample (the orange
“1 word” wire). The window shifts along by one and takes it in at the right-hand end. The window now holds the next
row.</li>
<li><b><code>SST</code></b>. S1 goes back to memory through the write-select mux (the “SST” input). The
{g("agu", "AGU")} has already moved the address on by one for the next output.</li>
</ol>
<p>The same hardware does the other phases. Phase 3 (gradient) is the same loop with 8 window chunks and the errors
in V0–V7. Phase 2 (error) and Phase 4 (weight update) use the vector ALU. Phase 5 feeds the weights to the peak
detector.</p>
<h3>Control unit, in plain words</h3>
<ul>
<li><b>PC, +1, next-PC mux, loop stack.</b> The {g("pc", "PC")} holds the address of the next instruction. Normally
it counts up by one. When a <code>LOOP</code> is running and the PC reaches the loop's last instruction, the mux picks
the loop start instead, with no extra cycle.</li>
<li><b>IMEM → IR → decode.</b> The instruction is read from IMEM into the instruction register IR and decoded
into a control word: which unit does what. The {g("stall", "scoreboard")} holds an instruction back until the
results it needs are ready.</li>
<li><b>AGU.</b> The address registers A0–A7 hold where each data stream is in memory. After each access, the
adder adds IMM (the step), and the circular wrap keeps ring addresses inside their 512-word ring.</li>
<li><b>Broadcast bus.</b> The control word and the address go to all three PEs in the same cycle.</li>
</ul>
</section>

<section id="ports">
<h2>3. Full detail: ports, IP and the C driver</h2>
{figure("microarch.png", "Detailed block diagram of the Zynq system, SIMD cluster and one processing element",
        "The detailed version: every Zynq port and IP block, the CSR list, the input writer's routing, and PE0's "
        "internals. PE1 and PE2 are identical.", wide=True)}
<div class="tbl"><table>
<tr><th>Link</th><th>Zynq port / IP</th><th>Carries</th></tr>
<tr><td>ARM → accelerator</td><td><code>M_AXI_GP0</code> → AXI Interconnect → AXI4-Lite slave</td><td>CSRs (μ, B, L, offsets, control), microprogram into IMEM, τ read-back</td></tr>
<tr><td>DDR → accelerator</td><td>AXI DMA (MM2S) on <code>S_AXI_HP0</code> → AXI4-Stream</td><td>64-bit beats: {{mic4, mic3, mic2, mic1}} × 16 bit</td></tr>
<tr><td>accelerator → ARM</td><td><code>IRQ_F2P</code></td><td>“τ ready”, level, cleared by writing STATUS.DONE</td></tr>
</table></div>
<p><b>Vendor-neutral.</b> The cluster only needs AXI4-Lite, AXI4-Stream, inferred RAM and inferred multiply-add.
The DMA can be the Xilinx AXI DMA or the free Forencich <code>verilog-axi</code> core. A direct I²S microphone
receiver could also feed the stream later, with no DDR involved.</p>
<p><b>C driver:</b> load IMEM, write CSRs, set <code>CTRL = IRQ_EN | AUTO | START</code>. Per audio buffer,
<code>Xil_DCacheFlushRange</code> (the HP ports are not cache-coherent), then <code>XAxiDma_SimpleTransfer</code>. The
ISR reads TAU21/31/41, clears DONE and triangulates.</p>
</section>

<section id="control">
<h2>4. Control unit: sizes and latencies</h2>
<p>The red “PC? instructions?” box in the week-2 draw.io is this unit. It is shared by all PEs because they execute
the same instruction at the same time.</p>
<div class="tbl"><table>
<tr><th>Stage</th><th>Hardware</th><th>Detail</th></tr>
<tr><td>IMEM</td><td>512 × 32 BRAM18</td><td>written by the ARM over AXI4-Lite (offset 0x800), read by fetch</td></tr>
<tr><td>Fetch</td><td>PC + 2-entry loop stack {{start, end, count}}</td><td>if PC = end and count &gt; 1: next PC = start, with no bubble. There are no branches, so no branch penalty</td></tr>
<tr><td>Decode / issue</td><td>scoreboard of ready-cycles</td><td>single-issue, in-order; stalls on read-after-write</td></tr>
<tr><td>AGU</td><td>A0–A7, 13 bit + circular flag</td><td>address = An; post-increment by IMM; circular = add in the low 9 bits only</td></tr>
<tr><td>Sequencer</td><td>SYNC / HALT / IRQ / START / AUTO</td><td>SYNC 1 waits until the input writer has B new samples</td></tr>
</table></div>
<h3>Latencies used by the scoreboard</h3>
<p>{g("pipeline", "Latency")} is how many cycles after an instruction starts its result can be used. If the next
instruction needs that result sooner, it waits ({g("stall", "stalls")}). These numbers feed the cycle count in the
ISA simulator.</p>
<div class="tbl"><table>
<tr><th>Instruction</th><th class="num">Result ready after</th><th>Reason</th></tr>
<tr><td>VLD, WLD, SLD, WSLIDE</td><td class="num">2 cycles</td><td>BRAM read + register</td></tr>
<tr><td>VMAC → VREDUCE</td><td class="num">3</td><td>DSP48E1 A/B, M, P registers (VMAC → VMAC accumulates back-to-back)</td></tr>
<tr><td>VREDUCE, PKMAX</td><td class="num">5</td><td>4 tree stages + round/saturate</td></tr>
<tr><td>SDIV</td><td class="num">34</td><td>iterative; once per block only</td></tr>
<tr><td>everything else</td><td class="num">1</td><td></td></tr>
</table></div>
</section>

<section id="pe">
<h2>5. PE blocks: sizes</h2>
<div class="tbl"><table>
<tr><th>Block</th><th>Size</th><th>Role</th></tr>
<tr><td>16 memory banks</td><td>16 × BRAM18 (512 × 32, simple dual-port)</td><td>rings, w_rev, y, e, g. Read port: PE. Write port: PE stores, or the input writer (PE has priority; the stream waits)</td></tr>
<tr><td>Window register WIN</td><td>128 × 16 bit</td><td>current row / column of X, as chunks W0–W7</td></tr>
<tr><td>VRF</td><td>8 × 16 × 32 bit</td><td>w (Phase 1) or e (Phase 3) stays resident for the whole phase</td></tr>
<tr><td>MAC lanes</td><td>16 × DSP48E1</td><td>A port (25 bit) = w&gt;&gt;7 or e; B port (18 bit) = window sample; P (48 bit) = VACC; OPMODE Z = 0 for VMAC.C</td></tr>
<tr><td>Adder tree</td><td>15 adders, 4 stages, ~52 bit</td><td>VREDUCE with round / shift / saturate</td></tr>
<tr><td>Vector ALU</td><td>16 × 32 bit</td><td>VADD / VSUB / VABS / VMOV, saturating</td></tr>
<tr><td>Peak detector</td><td>|·| comparator tree + running max</td><td>PKMAX / PKOUT → this PE's τ CSR</td></tr>
<tr><td>Scalar unit</td><td>S0–S7</td><td>μ, VREDUCE results, SDIV</td></tr>
</table></div>
</section>

<section id="memory">
<h2>6. Memory and addressing</h2>
<p>Three ideas keep the memory simple: store the weights backwards, slide a window instead of reloading it, and
use the input memory as a ring. The slide shows them as pictures; the detailed figure below adds the equations,
offsets and the memory map.</p>
{figure("slide_memory.png", "Sliding window, ring buffer and aligned banks drawn as pictures",
        "The slide version: ① the window moves by one sample per row, ② the ring buffer, ③ one aligned load reads "
        "one row across all 16 banks.")}
{figure("memory.png", "Sliding window, circular ring, bank layout and memory map",
        "① reversed weights turn rows and columns into ascending windows, ② circular rings, ③ aligned banks, "
        "④ per-PE memory map.")}
<h3>① Reverse w, and both products read the same window</h3>
<p><b>In plain words.</b> Each row of X lists recent samples newest-first, so reading it straight from memory would
mean reading backwards. Instead of reading memory backwards, we store the 64 weights backwards once
({g("wrev", "w_rev")}). After that every row and every column of X is a run of consecutive samples read forwards,
and both big products (filter and gradient) can share the same window hardware. The only cost: the peak position
is read from the other end, so τ = k* − 31 instead of 32 − k*.</p>
<p><b>The maths.</b> The golden model builds <code>X[i] = x_full[i+L : i : -1]</code>, so <code>X[i, j] = x_full[i+L−j]</code>.
Substitute <code>k = L−1−j</code> and store <code>w_rev[k] = w[L−1−k]</code>:</p>
<pre><code>y[i]     = Σ_k x_full[i+1+k] · w_rev[k]      <span class="cm">row i    = x_full[i+1 … i+L]</span>
g_rev[k] = Σ_i x_full[k+1+i] · e[i]          <span class="cm">column k = x_full[k+1 … k+B]</span>
τ        = argmax_k |w_rev[k]| − (L−1−L/2)   <span class="cm">= k* − 31</span></code></pre>
<p>Both products now read ascending windows that start at <code>x_full[1]</code> and move one sample at a time.
v1.0 read x and w ascending from <code>x_full[0]</code> and started column j at offset j. That still converges,
but to a mirrored filter. Run on the same data, it reported <b>+7 where the true delay was −7</b>.</p>

<h3>② The sliding-window register</h3>
<p><b>In plain words.</b> Row i+1 of X is row i moved along by one sample: 63 of its 64 samples are the same. So we
keep the current row in a {g("window", "shift register")} and, for the next row, shift it by one and read just the
one new sample, instead of fetching all 64 again.</p>
<p><code>WLD</code> fills the window with aligned 16-sample chunks: 4 for Phase 1, 8 for Phase 3. After that,
<code>WSLIDE</code> shifts it by one and pulls a single new sample from memory. Each row costs one memory read
instead of four 16-wide loads.</p>
<p><b>Alternative considered:</b> a rotator (16 × 16 crossbar of 32-bit words per read port) would allow a 16-wide
load from any offset. That is the most LUT-hungry structure a PE could have, and it would be needed on every PE. The
window register is 2 048 flip-flops plus an 8:1 chunk multiplexer, and the memory stays aligned-only.</p>

<h3>③ Circular rings instead of copies and ping-pong buffers</h3>
<p><b>In plain words.</b> Each block needs the previous 63 samples as well as the 128 new ones. A simple design
would copy those 63 samples to the front of a buffer every block. Instead, the input memory is a
{g("ring", "ring")} of 512 words, like a clock face: new samples are written round and round, and the addresses
wrap from 511 back to 0. The previous block's last samples are already sitting just before the new ones, so nothing
is copied. The DMA can write the next block into the free part of the ring while the PEs work on this one.</p>
<pre><code>input writer:  X_RING[(t + XOFF) mod 512] = mic(p+2)[t]     XOFF = L−1 = 63
               D_RING[(t + DOFF) mod 512] = mic1[t]         DOFF = L/2 = 32  (the center tap)
block n:       A7 = (n·B) mod 512   →  x_full[1] at X_RING+A7,  d_delayed[0] at D_RING+A7</code></pre>
<ul>
<li>The last 63 samples of block n are the first 63 of block n+1, already in place, so there is no history copy.</li>
<li>XOFF = 63 puts <code>x_full[1]</code> on a 16-word boundary, so every vector load is aligned.</li>
<li>While block n is processed (191 live words), the DMA writes block n+1 into the next 128 words. Before it could
overwrite live data, the writer would have to be 321 samples (6.7 ms) past the end of block n. If that happens,
<code>TREADY</code> drops (back-pressure) and <code>STATUS.OVERRUN</code> is set.</li>
<li>The D ring gets the center-tap delay for free through DOFF.</li>
</ul>

<h3>④ Banks and map</h3>
<p><b>In plain words.</b> A normal memory gives one word per cycle, but a lane group needs 16. So each PE's memory is
16 separate {g("bank", "banks")}, and consecutive words go to consecutive banks. Reading 16 consecutive words that
start on a multiple of 16 (an {g("aligned", "aligned")} row) takes one word from each bank, all in the same cycle.
Every load in our program is aligned, so no {g("crossbar", "crossbar")} is needed to reshuffle words between
banks.</p>
<p>Word address a lives in bank <code>a mod 16</code>, row <code>a / 16</code>. An aligned vector access is one row
across all 16 banks in one cycle. Scalar stores (y[i], g[k]) use that bank's write enable. The map (X ring 512,
D ring 512, w_rev 64, y 128, e 128, g 64 words) uses 1 408 of the 8 192 words that 16 BRAM18s provide.</p>
</section>

<section id="timing">
<h2>7. Timing and resources</h2>
<p>How long one block takes, and how much of the FPGA the design uses. The arithmetic behind each number is in
<a href="basics.html#timing">Basics §10</a>.</p>
{figure("feasibility.png", "Cycle breakdown, real-time budget, resource table and verification results",
        "Cycles come from running the program in isa_sim.py, not from hand estimates.")}
<div class="tbl"><table>
<tr><th>Phase</th><th class="num">Cycles</th><th>Per item</th></tr>
<tr><td>0 setup + pipeline fill</td><td class="num">5</td><td></td></tr>
<tr><td>1 filter</td><td class="num">1 548</td><td>≈ 12 per row: 4 VMAC, 2 stall, VREDUCE, WSLIDE, 3 stall, SST</td></tr>
<tr><td>2 error</td><td class="num">44</td><td></td></tr>
<tr><td>3 gradient</td><td class="num">1 044</td><td>16 per column</td></tr>
<tr><td>4 update</td><td class="num">31</td><td></td></tr>
<tr><td>5 peak</td><td class="num">23</td><td></td></tr>
<tr><td><b>total</b></td><td class="num"><b>2 695</b></td><td>27.0 µs at 100 MHz; 1.0 % of the 2 667 µs block period</td></tr>
</table></div>
<p>Phases 1 and 3 are almost all of the time, because they hold the 16 384 multiply-accumulates. A row takes about
12 cycles for 7 instructions; the other 5 are {g("stall", "stalls")}, where an instruction waits for the adder tree's
result. Reordering the loop so y[i−1] is stored while row i is multiplying (software pipelining) would cut Phase 1
to about 8 cycles per row. It isn't needed: we are already 99× faster than real time requires.</p>
<p>Resources: a {g("dsp", "DSP48E1")} is a hard multiplier block and a {g("bram", "BRAM18")} an 18-kilobit memory
block. Both counts follow directly from the architecture. Logic (LUTs) and the maximum clock come from
{g("synthesis", "synthesis")}.</p>
<div class="tbl"><table>
<tr><th>Resource</th><th>Needs</th><th>Zybo Z7-10 (XC7Z010)</th><th>Zybo Z7-20 (XC7Z020)</th></tr>
<tr><td>DSP48E1</td><td>51 = 3 × 16 lanes + 3 scalar</td><td>80 → 64 %</td><td>220 → 23 %</td></tr>
<tr><td>BRAM18</td><td>49 = 3 × 16 banks + IMEM</td><td>120 → 41 %</td><td>280 → 18 %</td></tr>
<tr><td>LUT / FF / Fmax</td><td colspan="3">not yet known; needs RTL + synthesis. The largest expected LUT users are the three adder trees, the window multiplexers and the vector ALUs.</td></tr>
</table></div>
</section>
"""
    toc = [("system", "1 System"), ("datapath", "2 PE datapath"), ("ports", "3 Ports & driver"),
           ("control", "4 Control unit"), ("pe", "5 PE sizes"), ("memory", "6 Memory"), ("timing", "7 Timing")]
    return page("microarchitecture.html", "Accelerator Microarchitecture", "Microarchitecture",
                "Microarchitecture and memory addressing",
                "How the Zynq system, the shared control unit and each processing element fit together, and the "
                "three addressing ideas that keep the memory simple.", toc, body)


# =====================================================================================================
QA = [
    ("Basics", [
        ("What is μ, in one sentence?",
         "The step size: how big each correction to the filter weights is. Small μ is smooth but slow to follow a "
         "moving source (μ = 0.05 lags about 3.7 s); larger μ follows faster (μ = 0.5 lags about 1.7 s) but too "
         "large makes the weights unstable. The ARM sets it through the MU register."),
        ("What are B and L, and why 128 and 64?",
         "B is the block size: 128 new samples are processed together and the weights update once per block, every "
         "2.67 ms. L is the filter length: the filter looks at the last 64 samples, which lets it find delays up to "
         "about ±32 samples (we need ±14). These are the golden model's values. They suit the hardware: both are "
         "multiples of the 16 lanes, B is a power of two so ÷B is a shift, and the weights and errors fit in the 8 "
         "vector registers."),
        ("What does τ mean, and what does its sign mean?",
         "τ21 is how many samples later the sound reaches Mic 2 than Mic 1 (one sample = 20.8 µs ≈ 7 mm of path). "
         "Positive: Mic 2 is farther from the source. Negative: nearer. τ31 and τ41 are the same for Mic 3 and 4."),
        ("How does a filter's weights tell you a delay?",
         "A filter that turns one signal into a delayed copy of itself is all zeros except one weight: a spike. The "
         "position of the spike is the delay. The filter learns to turn Mic x into (delayed) Mic 1, so the spike "
         "position gives τ. Mic 1 is delayed by 32 samples first so negative delays fit too: τ = 32 − spike position."),
        ("What is fixed-point, and why not floating-point?",
         "Fixed-point stores a fraction as a whole number with an agreed scale. Q1.15 means 16 bits, value = integer "
         "÷ 32 768. The FPGA's DSP48E1 multipliers work on whole numbers, so fixed-point is far cheaper than "
         "floating-point, and in simulation it gives the same τ on 99.6 % of blocks."),
        ("What is a PE, and what is a lane?",
         "A PE (processing element) is one full copy of the datapath with its own memory; we have three, one per "
         "microphone pair. A lane is one of the 16 parallel slices inside a PE, each with its own multiplier. One "
         "instruction drives 3 PEs × 16 lanes = 48 multipliers."),
        ("What is SIMD?",
         "Single instruction, multiple data: one instruction is applied to many numbers at the same time. The control "
         "unit (fetch and decode) exists once; the parts that hold data are copied per PE and per lane."),
    ]),
    ("Motivation", [
        ("Why accelerate at all, if the ARM could run L = 64?",
         "At B = 128, L = 64 and 48 kHz the load is about 18 M MAC/s, which a Cortex-A9 can handle. We say so. The "
         "accelerator gives a fixed 27 µs latency independent of the OS, frees the PS for triangulation and I/O, and "
         "leaves ~99× headroom for longer filters (L = 256), more mic pairs or higher sample rates. It is also a "
         "direct demonstration of SIMD for the course."),
        ("Where exactly is the parallelism?",
         "At two levels. The three mic pairs are independent and run identical code: 3 PEs in lockstep, one "
         "instruction stream. Inside each dot product, 16 lanes multiply 16 taps at once. One VMAC is 48 "
         "multiply-accumulates."),
        ("Why Block-LMS instead of normal LMS?",
         "Sample LMS updates w after every sample, so every sample depends on the previous one. Block LMS updates "
         "once per 128 samples, so the 128 outputs of a block are independent and the work becomes two "
         "matrix–vector products, which is data-parallel."),
    ]),
    ("Algorithm & results", [
        ("How does an LMS filter give a delay?",
         "The filter learns to predict Mic 1 from Mic x. If Mic 1 is Mic x shifted by τ, the best filter is a single "
         "spike at tap τ. The index of the largest weight is the delay. The reference is delayed by L/2 = 32 so the "
         "spike can sit on either side: τ = 32 − peak index."),
        ("Why is the accuracy only 47 % with μ = 0.05?",
         "The filter is slow to adapt and lags the moving source by about 3.7 s. μ = 0.5 lags 1.7 s and gets 85.6 % "
         "within ±1 sample; block-NLMS (μ = 0.64) gets 88 %. μ is a CSR, so this is a software setting."),
        ("Why do the estimates freeze around 66–90 s?",
         "That part of the music is bass-only (spectral centroid 108–222 Hz). A narrowband low-frequency signal has "
         "a broad correlation peak, so no delay estimator can resolve a 14-sample shift. After 120 s the audio fades "
         "out. This is a property of the input; PHAT weighting or holding the estimate are the usual fixes."),
        ("What's the angular resolution?",
         "One sample at 48 kHz is 7.15 mm of path difference. Across the 10 cm baseline that is about 4° near "
         "broadside. Sub-sample peak interpolation on the ARM would improve it without hardware changes."),
        ("It's called NLMS in the code. Is it normalised?",
         "No. It scales by μ/B, not by input power. True block-NLMS divides by L·P_x, which the study shows is "
         "slightly better (88 %) and independent of loudness. The ISA keeps SDIV so this costs one division per "
         "block."),
    ]),
    ("ISA", [
        ("What was wrong with v1.0?",
         "Sixteen things; see the ISA page. The blocking ones: no loop instruction (LOOP_DEC was used but not "
         "defined and all opcodes were taken), no way to select an address pointer, X indexing that reports −τ, and "
         "a memory map that couldn't hold d_delayed contiguously or fit the ping-pong buffers."),
        ("How do you loop without branch instructions?",
         "LOOP count, len sets up a hardware loop: the fetch unit jumps back from the last body instruction to the "
         "first with no bubble. The control flow is completely regular, so no conditional branches are needed. "
         "HALT with CTRL.AUTO restarts the program for the next block."),
        ("How do you know the ISA is correct?",
         "isa_sim.py assembles the 78-instruction program into 32-bit words and executes it on a 3-PE model with "
         "the real memory map and ring wrap-around. For 600 blocks, every τ and all 64 weights of all 3 PEs match "
         "the fixed-point model bit for bit. The fixed-point model in turn matches float on 99.6 % of 47 547 blocks."),
        ("Why 32-bit instructions with a 5-bit opcode?",
         "Fixed format means one-cycle decode. Five bits give exactly 32 instructions, enough because the program "
         "is regular. The CSR index moved into IMM12, which fixed v1.0's field clash."),
    ]),
    ("Microarchitecture & memory", [
        ("Why store w reversed?",
         "Rows of X run backwards in time. With w reversed, row i and column k are both ascending windows starting "
         "at x_full[1], so one window register and aligned memory serve both matrix products. It also fixes the "
         "sign error in v1.0."),
        ("What is the window register, and why not a crossbar?",
         "A 128-sample shift register. Fill it once with aligned loads, then each row or column is one shift plus "
         "one sample read. A crossbar/rotator for unaligned 16-wide loads would be the biggest LUT consumer in each "
         "PE; the window register is just flip-flops plus a small multiplexer."),
        ("How is the history (x_history, d_history) handled?",
         "The input writer stores sample t at (t + L − 1) mod 512. The end of one block is already the start of the "
         "next, so nothing is copied. The D ring uses offset L/2, which implements the center-tap delay for free."),
        ("Where is the ping-pong buffer?",
         "The ring replaces it. While block n is processed, the DMA writes block n+1 into the free part of the "
         "ring. SYNC 1 waits if data is late; if the writer gets too far ahead, the stream is back-pressured."),
        ("How does Mic 1 reach all three PEs?",
         "The input writer writes each Mic 1 sample into all three PEs' D rings in the same cycle. There is no "
         "lane-to-lane network."),
        ("Why 16 lanes?",
         "L = 64 and B = 128 are multiples of 16, and 3 × 16 = 48 DSPs fits the Z7-10's 80. VLEN = 32 would need 96 "
         "DSPs, which does not fit the Z7-10."),
        ("Why 3 PEs instead of one PE reused three times?",
         "One PE time-shared over the three pairs would still use only ~3 % of the block period, and it would save "
         "32 DSPs. That is a valid area option. We keep three PEs because it maps the independent pairs onto SIMD "
         "lockstep, as in the reference architecture, and keeps latency at 27 µs."),
        ("Can accumulators overflow?",
         "Phase 1 products are 41 bits (Q2.23 × Q1.15); 64 of them need about 47 bits. Phase 3 products are Q2.30; "
         "128 of them need about 39 bits. Both fit the 48-bit DSP48E1 P register, and results saturate when written "
         "back."),
    ]),
    ("Implementation", [
        ("Will it meet 100 MHz? How many LUTs?",
         "Not known yet. DSP and BRAM counts follow from the architecture (51 DSP48E1, 49 BRAM18). LUTs and Fmax "
         "need RTL and synthesis, which is the next step, starting with one PE on the Z7-10."),
        ("Is it tied to Xilinx?",
         "The cluster uses standard AXI4-Lite and AXI4-Stream, inferred RAM and inferred multiply-add, so it ports. "
         "Zynq-specific parts (PS, AXI DMA, interconnect) are outside it, and the DMA can be the free Forencich core."),
        ("What does the C program do?",
         "It loads the microprogram and CSRs, flushes the cache and starts the DMA for each audio buffer. In the "
         "interrupt it reads τ21, τ31, τ41, clears DONE, and solves the TDOA equations for the 3-D position."),
    ]),
]


origins.extend_qa(QA)


def build_qa():
    sec = ""
    toc = []
    for grp, items in QA:
        aid = grp.lower().replace(" & ", "-").replace(" ", "-")
        toc.append((aid, grp))
        sec += f'<section id="{aid}"><h2>{grp}</h2>'
        for q, a in items:
            sec += f"<details><summary>{q}</summary><div><p>{a}</p></div></details>"
        sec += "</section>"
    nums = [
        ("Sample rate / block / taps", "48 kHz · B = 128 · L = 64 · center tap 32"),
        ("Step size μ", "0.5 recommended (0.05 in the original code); NLMS μ = 0.64"),
        ("1 sample at 48 kHz", "20.8 µs"),
        ("Block period", "2 667 µs"),
        ("Max physical delay", "≈ 14 samples (10 cm, 343 m/s)"),
        ("1 sample", "7.15 mm path difference, ≈ 4° near broadside"),
        ("Load (3 filters)", "≈ 18.4 M MAC/s"),
        ("Program", "78 instructions, 312 B IMEM"),
        ("Opcodes", "32 slots: 28 from v1.0 (18 kept, 6 renamed, 4 reworked) + 4 new; 20 run every block"),
        ("Executed per block", "1 709 instructions, 1 024 of them VMAC"),
        ("Cycles per block", "2 695 → 27.0 µs @ 100 MHz, 1.0 % busy"),
        ("Phase split", "P1 1 548 · P3 1 044 · rest 103"),
        ("Peak compute", "48 MAC/cycle = 4.8 GMAC/s"),
        ("Resources", "51 DSP48E1 · 49 BRAM18"),
        ("Accuracy (μ = 0.5)", "85.6 % within ±1 sample; NLMS 88.0 %"),
        ("Fixed = float", "99.6 % of 47 547 blocks"),
        ("ISA vs fixed-point", "600 / 600 blocks bit-exact"),
        ("v1.0 sign bug", "+7 reported where the golden model gives −7"),
    ]
    num_html = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in nums)
    body = f"""
<section id="numbers">
<h2>Numbers to know</h2>
<div class="tbl"><table><tr><th>What</th><th>Value</th></tr>{num_html}</table></div>
</section>
<div class="qa">{sec}</div>
"""
    toc = [("numbers", "Numbers to know")] + toc
    return page("qa.html", "Examiner Q&A", "Q&A preparation", "Questions we should expect",
                "Short answers for the questions most likely to come up after the feasibility presentation. Tap a "
                "question to open it. The Basics group covers the terms themselves; the glossary has the rest.",
                toc, body)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for fname, html in [("index.html", build_index()), ("basics.html", build_basics()),
                        ("algorithm-results.html", build_results()),
                        ("isa.html", build_isa()), ("isa-origins.html", build_origins()),
                        ("microarchitecture.html", build_uarch()), ("qa.html", build_qa())]:
        with open(os.path.join(OUT, fname), "w") as f:
            f.write(html)
        print(f"{fname}: {len(html) / 1024:.0f} KB")
