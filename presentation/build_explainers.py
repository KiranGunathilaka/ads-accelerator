"""
Builds the local HTML explainer pages in presentation/explainers/.
Each page is self-contained (figures embedded as data URIs) so it can be opened or shared on its own.

Usage:  python3 presentation/build_explainers.py
"""
import base64
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
OUT = os.path.join(HERE, "explainers")

PAGES = [
    ("index.html", "Briefing"),
    ("algorithm-results.html", "Algorithm & results"),
    ("isa.html", "ISA v1.1"),
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

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..100,500..800'
         '&family=JetBrains+Mono:wght@400;600&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&display=swap">')


def img(name):
    with open(os.path.join(FIG, name), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def figure(name, alt, caption):
    return (f'<figure><div class="frame"><img src="{img(name)}" alt="{alt}"></div>'
            f'<figcaption>{caption}</figcaption></figure>')


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
         ["The fixed-point estimate (blue) follows the true delay (black) for all three mic pairs over 126.8 s of "
          "moving-source audio.",
          "Grey bands: 66–90 s is bass-only music and after 120 s the audio fades out. With no broadband content, "
          "no TDOA method can lock on, so the estimate holds.",
          "Bars: fixed-point with 32-bit weights matches float. μ sets the tracking lag: μ = 0.05 → 47 % of blocks "
          "within ±1 sample, μ = 0.5 → 85.6 %.",
          "Weights plot: the filter learns a delayed impulse, and its peak position is the delay."],
         "“It works, it works in fixed point, and μ is the knob.”"),
        ("isa.png", "2 · Instruction Set (v1.1)",
         ["Fixed 32-bit format, 5-bit opcode, 32 instructions in 4 groups.",
          "Orange = new memory-addressing and loop instructions. v1.0 had no working loop instruction and no way "
          "to choose an address pointer.",
          "Addressing modes: post-increment, circular rings, and the sliding window.",
          "Phase-1 loop: 7 instructions per output sample, and w stays in registers."],
         "“The whole block is 78 instructions, and we ran them in an instruction-level simulator.”"),
        ("microarch.png", "3 · Microarchitecture",
         ["ARM runs the C driver: it loads the program, sets μ/B/L, starts the DMA and takes the interrupt.",
          "Standard IP (AXI DMA, interconnect) sits outside. The cluster is plain Verilog behind AXI4-Lite + "
          "AXI4-Stream.",
          "One control unit broadcasts one instruction and one address per cycle to 3 PEs (one per mic pair).",
          "Each PE: 16 memory banks, the window register, 8 vector registers, 16 DSP48E1 MAC lanes, an adder tree "
          "and a peak detector."],
         "“SIMD at two levels: 3 PEs × 16 lanes = 48 MACs per instruction.”"),
        ("memory.png", "4 · Memory & Addressing",
         ["Storing w reversed makes every row and column of X an ascending window starting at x_full[1]. "
          "v1.0's pattern would have reported −τ.",
          "The window register shifts in one sample per row or column instead of reloading 16-wide unaligned "
          "vectors.",
          "Circular rings: the input writer stores sample t at (t + L−1) mod 512. History stays in place and "
          "the DMA fills the next block alongside.",
          "Aligned-only 16-bank memory needs no crossbar or rotator. The map uses 1 408 of 8 192 words."],
         "“No copies, no crossbar, one memory read per row.”"),
        ("feasibility.png", "5 · Timing & Feasibility",
         ["Cycle counts are measured by running the program: 2 695 cycles = 27 µs at 100 MHz.",
          "Block period is 2 667 µs, so the cluster is busy 1 % of the time (≈ 99× headroom).",
          "Resources follow from the architecture: 51 DSP48E1 and 49 BRAM18, which fits Zybo Z7-10 and Z7-20. "
          "LUTs and Fmax come after synthesis.",
          "Verification: 600/600 blocks bit-exact (ISA vs fixed-point); 99.6 % fixed = float."],
         "“Feasible with a lot of room. The next step is RTL for one PE plus synthesis.”"),
    ]
    s_html = ""
    for fig, title, pts, say in slides:
        s_html += (f'<div class="slide"><img src="{img(fig)}" alt="Slide figure: {title}"><div><h3>{title}</h3><ul>'
                   + "".join(f"<li>{p}</li>" for p in pts) + f'</ul><p class="say">Line to land: {say}</p></div></div>')
    body = f"""
<section id="claims">
<h2>What we claim today</h2>
<div class="stats">
  <div class="stat"><b>85.6 %</b><span>of blocks within ±1 sample of the true delay (μ = 0.5, fixed-point)</span></div>
  <div class="stat"><b>99.6 %</b><span>of blocks where fixed-point τ equals the float golden model</span></div>
  <div class="stat"><b>600 / 600</b><span>blocks bit-exact: ISA program vs fixed-point model</span></div>
  <div class="stat"><b>27 µs</b><span>per block (2 695 cycles at 100 MHz) against a 2 667 µs budget</span></div>
</div>
<p>The application is a good fit for the accelerator. Block-LMS is two matrix–vector products per block with
perfectly regular addressing. The three mic pairs run identical code, so one instruction stream drives three PEs.
Every number above was produced by a script in the repo, not estimated by hand.</p>
</section>

<section id="slides">
<h2>Slide-by-slide</h2>
<p>Five slides, one diagram each. The Canva speaker notes carry the same points.</p>
{s_html}
</section>

<section id="changed">
<h2>What changed since week 2</h2>
<ul>
<li><b>ISA v1.0 → v1.1.</b> 16 issues fixed. The important ones: there was no working loop instruction, address
pointers could not be selected, the X indexing reported −τ, and the memory map could not hold d_delayed contiguously
or fit the promised ping-pong buffers. Full list on the <a href="isa.html#changes">ISA page</a>.</li>
<li><b>Microarchitecture completed.</b> The red “PC? instructions?” box from the draw.io draft is now the control
unit: IMEM, fetch with hardware loops, scoreboard, AGU and sequencer. The “DRAFT” AGU has a register model, and the
“sliding window” idea is a concrete register.</li>
<li><b>Number format decided by evidence.</b> Q1.15 samples and Q2.30 weights on DSP48E1, verified against float.</li>
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
<tr><td><code>presentation/figures/</code></td><td>Slide figures (regenerate with <code>plot_results.py</code>, <code>draw_*.py</code>)</td></tr>
</table></div>
</section>
"""
    toc = [("claims", "What we claim"), ("slides", "Slide-by-slide"), ("changed", "What changed"),
           ("files", "Where things live")]
    return page("index.html", "Feasibility Briefing", "Presenter briefing · 26 Sep 2026",
                "SIMD accelerator for 3-D sound localization",
                "What each of the five slides shows, what to say, and which numbers back it up.", toc, body)


# =====================================================================================================
def build_results():
    body = f"""
<section id="problem">
<h2>The problem in one paragraph</h2>
<p>Four microphones sit on a tetrahedron with 10 cm edges. Sound from one source reaches them at slightly different
times. If we know the three delays of Mic 2, 3 and 4 relative to Mic 1 (τ21, τ31, τ41), the ARM can solve the
hyperbolic TDOA equations for the source position. At 48 kHz, one sample is 343 / 48 000 = 7.15 mm of path
difference. The largest possible delay across a 10 cm baseline is 0.1 / 343 × 48 000 ≈ <b>14 samples</b>.</p>
</section>

<section id="lms">
<h2>Why an adaptive filter finds a delay</h2>
<p>An LMS filter learns weights <code>w</code> so that filtering Mic x predicts Mic 1. If Mic 1 is just Mic x shifted
by τ samples, the best filter is a single spike (a delayed impulse) at tap τ. After adaptation, the position of the
largest weight <em>is</em> the delay.</p>
<p><b>Centered:</b> the reference is delayed by <code>CT = L/2 = 32</code> samples, so the spike sits at
<code>32 − τ</code>. That lets the filter represent negative delays too (the source nearer Mic x than Mic 1), within
±32 samples.</p>
<p><b>Block LMS:</b> the weights change once per block of B = 128 samples instead of every sample. Within a block all
128 outputs are independent, so the work becomes two matrix–vector products. That is what makes it data-parallel;
sample-by-sample LMS has a dependency from every sample to the next.</p>
<div class="tbl"><table>
<tr><th>Phase</th><th>Operation</th><th class="num">Work per filter</th></tr>
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
<li>The source moves once around a 2 m circle at 0.5 m height. Mic signals use per-sample fractional delay
(linear interpolation), so the true delay is fractional and changes continuously.</li>
<li>B = 128, L = 64, 47 547 blocks × 3 filters. The first 0.5 s is excluded from accuracy numbers (convergence).</li>
<li>“Within ±1 sample” compares the integer estimate with the true delay rounded to the nearest sample.</li>
</ul>
</section>

<section id="tracking">
<h2>Tracking results</h2>
{figure("sim_tracking.png", "Estimated versus true delay for the three mic pairs over 127 seconds",
        "Fixed-point accelerator model with μ = 0.5 (blue) against the true TDOA (black). The grey bands mark "
        "bass-only audio (66–90 s) and the fade-out (after 120 s).")}
<h3>Why the estimate freezes in the grey bands</h3>
<p>From 66 to 90 s the music is almost pure bass: its spectral centroid is 108–222 Hz. A low-frequency, narrowband
signal has a very broad correlation peak, because one period is hundreds of samples. So the filter cannot tell a
14-sample shift apart from its neighbours and keeps its old peak. After about 120 s the audio fades to silence. This
is a limit of the input signal, not of the hardware. Real systems add PHAT weighting or pre-whitening, or hold the
last estimate when coherence is low.</p>
</section>

<section id="mu">
<h2>Step size μ decides the tracking lag</h2>
<p>The golden model uses <code>w += (μ/B)·g</code>. Despite the class name, that is not normalised by input power.
With μ = 0.05 the filter reacts slowly and lags the moving source by several seconds. μ is a CSR, so changing it
costs nothing in hardware.</p>
<div class="tbl"><table>
<tr><th>Update rule</th><th class="num">μ</th><th class="num">Mean |error| (samples)</th><th class="num">Within ±1</th><th class="num">Best-fit lag</th></tr>
<tr><td>μ/B (current)</td><td class="num">0.05</td><td class="num">1.88</td><td class="num">47.0 %</td><td class="num">3.67 s</td></tr>
<tr><td>μ/B</td><td class="num">0.2</td><td class="num">1.40</td><td class="num">77.3 %</td><td class="num">2.40 s</td></tr>
<tr><td>μ/B</td><td class="num">0.5</td><td class="num">1.18</td><td class="num">85.6 %</td><td class="num">1.73 s</td></tr>
<tr><td>block NLMS</td><td class="num">0.3</td><td class="num">1.26</td><td class="num">83.8 %</td><td class="num">1.93 s</td></tr>
<tr><td>block NLMS</td><td class="num">0.64</td><td class="num">1.09</td><td class="num">88.0 %</td><td class="num">1.53 s</td></tr>
<tr><td>block NLMS</td><td class="num">1.0</td><td class="num">1.04</td><td class="num">88.8 %</td><td class="num">1.33 s</td></tr>
</table></div>
<p>Block NLMS divides the step by <code>L · P<sub>x</sub></code> (the block's input power), which makes it
independent of loudness. It is stable for 0 &lt; μ &lt; 2. With plain μ/B, a large μ can diverge on loud input,
because the stability limit shrinks as the power grows. That is the reason to prefer NLMS and to keep
<code>SDIV</code> in the ISA (one division per block).</p>
</section>

<section id="fixed">
<h2>Fixed-point results</h2>
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
Δ(sin θ) = 0.0715, about 4° near broadside. Parabolic interpolation around the peak (three weights, on the ARM)
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
OPS = [
    ("00", [("VMAC", "VACC (= or +=) SRC1 × (SRC2 >> sh)", "SRC1 = V or window chunk; .C clears (DSP OPMODE)"),
            ("VSUB", "Vd = sat(Va − Vb)", "sat16 or sat32"), ("VADD", "Vd = sat(Va + Vb)", ""),
            ("VSCALE", "Vd = ((Va >> pre) × Ss) >> post", "μ · g in Phase 4"), ("VABS", "Vd = |Va|", ""),
            ("VMOV", "Vd = Va, or splat Ss", ""), ("VREDUCE", "Sd = sat(round(Σ VACC >> sh))", "adder tree, 5-cycle latency"),
            ("VMUL", "Vd = (Va × Vb) >> sh", "general purpose (power for NLMS)")]),
    ("01", [("VLD", "Vd = M[An..An+15]; An += imm", "aligned"), ("VST", "M[An..An+15] = Vs; An += imm", "aligned"),
            ("AGU_SET", "An = Am/ZERO + imm; circular flag", "<span class='new'>changed</span>"),
            ("AGU_ADD", "An += imm (wraps if circular)", "<span class='new'>new</span>"),
            ("WLD", "window chunk Wc = M[An..An+15]; An += imm", "<span class='new'>new</span>"),
            ("WSLIDE", "WIN shifts left 1; WIN[len−1] = M[An]; An += 1", "<span class='new'>new</span>"),
            ("SST", "M[An] = Ss; An += imm", "<span class='new'>new</span> (v1.0 used an undefined VST_S)"),
            ("SLD", "Sd = M[An]; An += imm", "<span class='new'>new</span>")]),
    ("10", [("SMUL", "Sd = Sa × Sb", ""), ("SADD", "Sd = Sa + Sb + imm", ""), ("SSUB", "Sd = Sa − Sb + imm", ""),
            ("SDIV", "Sd = (Sa << imm) / Sb", "once per block, for NLMS"), ("SMOV", "Sd = Sa", ""),
            ("SIMM", "Sd = imm", ""), ("CSR_RD", "Sd = CSR[imm]", ""),
            ("LOOP", "repeat next len instructions count times", "<span class='new'>new</span>, zero overhead")]),
    ("11", [("PKMAX", "running max of |V| with index", "comparator tree"),
            ("PKOUT", "CSR[TAU_pe] = peak_idx − imm", "imm = L−1−L/2 = 31"),
            ("SYNC", "0: fence · 1: wait for a full block", ""),
            ("PKCLR", "reset peak detector", "<span class='new'>new</span>"), ("IRQ", "DONE + IRQ_F2P", ""),
            ("NOP", "", ""), ("HALT", "PC ← 0; restart on START or AUTO", ""), ("CSR_WR", "CSR[imm] = Ss", "")]),
]
GROUP_NAMES = {"00": "Vector arithmetic", "01": "Memory / AGU", "10": "Scalar / loop", "11": "Control / result"}

CHANGES = [
    ("No way to loop", "LOOP_DEC used everywhere but not in the table; all 32 opcodes taken",
     "LOOP: zero-overhead hardware loop, 2-level stack"),
    ("VST_S undefined", "used to store y[i] and g[j]", "SST / SLD"),
    ("AGU pointer can't be selected", "7 pointers used, but no instruction field names one", "A0–A7, named by every load/store, post-increment"),
    ("X indexing reports −τ", "rows are reversed; column j starts at L−j, not j. Simulated: +7 instead of −7",
     "store w reversed → row i and column k both start at x_full[·+1], ascending"),
    ("Unaligned 16-wide loads", "sliding window needs any start offset; one BRAM port can't deliver it",
     "16 aligned banks + window register (WLD / WSLIDE)"),
    ("Memory map broken", "d_delayed not contiguous; ping-pong buffers don't fit; x_hist redundant",
     "circular X / D rings, no copies"),
    ("CSR encoding clash", "tag bits [4:3] overlap the 4-bit CSR index → only 8 reachable", "operand fields typed by opcode; CSR index in IMM12"),
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


def build_isa():
    rows = ""
    for code, ops in OPS:
        for i, (m, op, note) in enumerate(ops):
            grp = f'<td rowspan="8"><b>{code}</b><br><span class="say">{GROUP_NAMES[code]}</span></td>' if i == 0 else ""
            rows += f"<tr>{grp}<td class='mono'>{code}{i:03b}</td><td class='mono'><b>{m}</b></td><td>{op}</td><td>{note}</td></tr>"
    chg = "".join(f"<tr><td class='num'>{i + 1}</td><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>"
                  for i, (a, b, c) in enumerate(CHANGES))
    listing = open(os.path.join(HERE, "..", "ISA_Design.md")).read()
    start = listing.index("; ---- Phase 0: wait + setup ----")
    end = listing.index("```", start)
    asm = listing[start:end].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    body = f"""
<section id="format">
<h2>Instruction format</h2>
<div class="scroll"><div class="bits">
<div><b>OPCODE</b><span>[31:27] · 5 bits</span></div><div><b>DST</b><span>[26:22] · 5</span></div>
<div><b>SRC1</b><span>[21:17] · 5</span></div><div><b>SRC2</b><span>[16:12] · 5</span></div>
<div><b>IMM12</b><span>[11:0] · 12 bits</span></div></div></div>
<p>Every instruction is 32 bits with the same fields, so decode is one cycle of wiring. <code>OPCODE[4:3]</code>
selects one of four groups of eight. The meaning of a register field depends on the opcode:</p>
<div class="tbl"><table>
<tr><th>Field kind</th><th>Codes 0–7</th><th>Code 8+</th></tr>
<tr><td>vector source</td><td>V0–V7</td><td>8–15 = W0–W7, the window chunks (VMAC only)</td></tr>
<tr><td>scalar</td><td>S0–S7</td><td>8 = ZERO</td></tr>
<tr><td>address</td><td>A0–A7</td><td>8 = ZERO (base for AGU_SET)</td></tr>
<tr><td>CSR</td><td colspan="2">index in IMM12[3:0]</td></tr>
</table></div>
<p>v1.0 used one global 2-bit tag per field. Its CSR tag (<code>10</code>) overlapped bit 3 of the index, so only 8
of the 16 CSRs were reachable. Typing fields by opcode removes the tag bits entirely.</p>
</section>

<section id="opcodes">
<h2>All 32 opcodes</h2>
<div class="tbl"><table>
<tr><th>Group</th><th>Code</th><th>Mnemonic</th><th>Operation</th><th>Notes</th></tr>
{rows}
</table></div>
</section>

<section id="modes">
<h2>Addressing modes</h2>
<div class="tbl"><table>
<tr><th>Mode</th><th>Example</th><th>Used for</th></tr>
<tr><td>Post-increment</td><td class="mono">VLD V4, [A2]+16</td><td>walking through w, y, e, g in 16-word chunks; scalar stores with +1</td></tr>
<tr><td>Circular</td><td class="mono">AGU_SET A0, A7, X_RING, circ=1</td><td>input rings: the pointer wraps inside a 512-word aligned region</td></tr>
<tr><td>Sliding window</td><td class="mono">WSLIDE [A0], len=64</td><td>next row (Phase 1) or column (Phase 3) of X with one memory read</td></tr>
</table></div>
<div class="key"><p><strong>Why these three are enough.</strong> After storing w reversed, every access in the algorithm is either
an aligned 16-word chunk, a single word, or “the same window moved by one”. There are no strides, gathers or
unaligned vectors, so the AGU is an adder and a mask.</p></div>
</section>

<section id="program">
<h2>The microprogram</h2>
<p>One pass per block: 78 instructions, 312 bytes of IMEM. The encodings are the assembler's actual output.</p>
<h3>Phase 1 inner loop, instruction by instruction</h3>
<pre><code>LOOP    128, 7                       <span class="cm">; 128 rows, 7-instruction body, zero overhead</span>
  VMAC.C  W0, V4, sh=7               <span class="cm">; VACC  = x_full[i+1..i+16] × w_rev[0..15]</span>
  VMAC    W1, V5, sh=7               <span class="cm">; VACC += next 16 taps</span>
  VMAC    W2, V6, sh=7
  VMAC    W3, V7, sh=7               <span class="cm">; 64 taps; 48 MACs per VMAC across 3 PEs</span>
  VREDUCE S1, sh=23, rnd=1, sat16=1  <span class="cm">; 16 lanes → y[i] in Q1.15</span>
  WSLIDE  [A0], len=64               <span class="cm">; window → row i+1 (one new sample)</span>
  SST     S1, [A3]+1                 <span class="cm">; y[i] → memory</span></code></pre>
<p>Phase 3 has the same shape. The window is 128 samples (column k = <code>x_full[k+1..k+128]</code>), e sits in
V0–V7, there are 8 VMACs per column, and <code>VREDUCE</code> shifts by 7 to divide by B.</p>
<details><summary>Full listing with encodings</summary><div><pre><code>{asm}</code></pre></div></details>
</section>

<section id="changes">
<h2>What changed from v1.0, and why</h2>
<div class="tbl"><table>
<tr><th>#</th><th>v1.0 problem</th><th>Evidence</th><th>v1.1 fix</th></tr>
{chg}
</table></div>
</section>
"""
    toc = [("format", "Format"), ("opcodes", "Opcodes"), ("modes", "Addressing modes"), ("program", "Microprogram"),
           ("changes", "Changes from v1.0")]
    return page("isa.html", "ISA v1.1", "Instruction set", "Instruction set architecture, v1.1",
                "The format, all 32 instructions, the addressing modes that make the sliding window cheap, and the "
                "exact program the simulator runs.", toc, body)


# =====================================================================================================
def build_uarch():
    body = f"""
<section id="system">
<h2>System view</h2>
{figure("microarch.png", "Block diagram of the Zynq system, SIMD cluster and one processing element",
        "Left to right: Zynq PS (ARM + DDR), standard IP in the PL, and the SIMD cluster. PE0 is drawn in detail; "
        "PE1 and PE2 are identical.")}
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
<h2>Control unit: fetch, decode, loops, AGU</h2>
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
<h2>Processing element datapath</h2>
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
<h2>Memory and addressing</h2>
{figure("memory.png", "Sliding window, circular ring, bank layout and memory map",
        "① reversed weights turn rows and columns into ascending windows, ② circular rings, ③ aligned banks, "
        "④ per-PE memory map.")}
<h3>① Reverse w, and both products read the same window</h3>
<p>The golden model builds <code>X[i] = x_full[i+L : i : -1]</code>, so <code>X[i, j] = x_full[i+L−j]</code>.
Substitute <code>k = L−1−j</code> and store <code>w_rev[k] = w[L−1−k]</code>:</p>
<pre><code>y[i]     = Σ_k x_full[i+1+k] · w_rev[k]      <span class="cm">row i    = x_full[i+1 … i+L]</span>
g_rev[k] = Σ_i x_full[k+1+i] · e[i]          <span class="cm">column k = x_full[k+1 … k+B]</span>
τ        = argmax_k |w_rev[k]| − (L−1−L/2)   <span class="cm">= k* − 31</span></code></pre>
<p>Both products now read ascending windows that start at <code>x_full[1]</code> and move one sample at a time.
v1.0 read x and w ascending from <code>x_full[0]</code> and started column j at offset j. That still converges,
but to a mirrored filter. Run on the same data, it reported <b>+7 where the true delay was −7</b>.</p>

<h3>② The sliding-window register</h3>
<p><code>WLD</code> fills the window with aligned 16-sample chunks: 4 for Phase 1, 8 for Phase 3. After that,
<code>WSLIDE</code> shifts it by one and pulls a single new sample from memory. Each row costs one memory read
instead of four 16-wide loads.</p>
<p><b>Alternative considered:</b> a rotator (16 × 16 crossbar of 32-bit words per read port) would allow a 16-wide
load from any offset. That is the most LUT-hungry structure a PE could have, and it would be needed on every PE. The
window register is 2 048 flip-flops plus an 8:1 chunk multiplexer, and the memory stays aligned-only.</p>

<h3>③ Circular rings instead of copies and ping-pong buffers</h3>
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
<p>Word address a lives in bank <code>a mod 16</code>, row <code>a / 16</code>. An aligned vector access is one row
across all 16 banks in one cycle. Scalar stores (y[i], g[k]) use that bank's write enable. The map (X ring 512,
D ring 512, w_rev 64, y 128, e 128, g 64 words) uses 1 408 of the 8 192 words that 16 BRAM18s provide.</p>
</section>

<section id="timing">
<h2>Timing and resources</h2>
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
<p>Most of the remaining cycles are stalls waiting for <code>VREDUCE</code>. Storing y[i−1] behind row i's VMACs
(software pipelining) would cut Phase 1 to about 8 cycles per row. It isn't needed for real time.</p>
<div class="tbl"><table>
<tr><th>Resource</th><th>Needs</th><th>Zybo Z7-10 (XC7Z010)</th><th>Zybo Z7-20 (XC7Z020)</th></tr>
<tr><td>DSP48E1</td><td>51 = 3 × 16 lanes + 3 scalar</td><td>80 → 64 %</td><td>220 → 23 %</td></tr>
<tr><td>BRAM18</td><td>49 = 3 × 16 banks + IMEM</td><td>120 → 41 %</td><td>280 → 18 %</td></tr>
<tr><td>LUT / FF / Fmax</td><td colspan="3">not yet known; needs RTL + synthesis. The largest expected LUT users are the three adder trees, the window multiplexers and the vector ALUs.</td></tr>
</table></div>
</section>
"""
    toc = [("system", "System"), ("control", "Control unit"), ("pe", "PE datapath"), ("memory", "Memory & addressing"),
           ("timing", "Timing & resources")]
    return page("microarchitecture.html", "Accelerator Microarchitecture", "Microarchitecture",
                "Microarchitecture and memory addressing",
                "How the Zynq system, the shared control unit and each processing element fit together, and the "
                "three addressing ideas that keep the memory simple.", toc, body)


# =====================================================================================================
QA = [
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
        ("Block period", "2 667 µs"),
        ("Max physical delay", "≈ 14 samples (10 cm, 343 m/s)"),
        ("1 sample", "7.15 mm path difference, ≈ 4° near broadside"),
        ("Load (3 filters)", "≈ 18.4 M MAC/s"),
        ("Program", "78 instructions, 312 B IMEM"),
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
                "question to open it.", toc, body)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for fname, html in [("index.html", build_index()), ("algorithm-results.html", build_results()),
                        ("isa.html", build_isa()), ("microarchitecture.html", build_uarch()), ("qa.html", build_qa())]:
        with open(os.path.join(OUT, fname), "w") as f:
            f.write(html)
        print(f"{fname}: {len(html) / 1024:.0f} KB")
