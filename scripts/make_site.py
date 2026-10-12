#!/usr/bin/env python3
"""Write the README media templates to screenshot (and, on request, the old long one-page site).

    python3 scripts/make_site.py --frames DIR --media build.html  # the media templates, the icons and the made-with badge
    node scripts/shoot.mjs <folder with node_modules/playwright> build.html      # screenshots -> docs/media, _preview
    python3 scripts/make_site.py --shrink                         # 256-colour PNGs for the big screenshots
    python3 scripts/make_site.py --site old-site.html             # the long page this script used to publish

The live page is docs/index.html, edited by hand: this script never writes into docs/ except docs/media. The page
it can still write is static: one HTML file, inline CSS and a little JS, fonts from Google Fonts (Geist and JetBrains Mono,
SIL OFL). Every number on it is read from scripts/art_data.json, benchmarks/results.json and the notes in knowledge/.
--frames holds stills of your own game (boss, horde, titan, vault, blade, clear .png and qa-1..qa-4 .png): check each
for titles, logos and names before you use it.
"""
import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/Wiserax/wisecraft"
MARK = "8,10 30,10 30,27 39,27 39,10 61,10 61,27 70,27 70,10 92,10 92,54 71,90 50,58 29,90 8,54"
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">')

CSS = r"""
:root{--bg:#050507;--ink-1:#0a0a0c;--ink-5:oklch(50% .008 280);--ink-6:oklch(66% .006 280);--ink-7:oklch(82% .005 280);--ink-9:oklch(97% 0 0);
--accent:oklch(84% .13 195);--accent-deep:oklch(47% .08 215);--rim:oklch(88% .06 230);--dim:oklch(56% .06 195);--line:oklch(100% 0 0/.08);--line-2:oklch(100% 0 0/.14);--before:oklch(100% 0 0/.16);
--sans:"Geist",ui-sans-serif,system-ui,sans-serif;--mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,monospace}
*,*:before,*:after{box-sizing:border-box;margin:0;padding:0}
html{background:var(--bg);color:var(--ink-7);font:16px/1.6 var(--sans);-webkit-font-smoothing:antialiased;scroll-behavior:smooth}
body{min-height:100vh;overflow-x:hidden}
a{color:inherit;text-decoration:none}
.grain{position:fixed;inset:0;z-index:5;pointer-events:none;opacity:.9;mix-blend-mode:screen;
background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='1.15' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 .065 0'/%3E%3C/filter%3E%3Crect width='220' height='220' filter='url(%23n)'/%3E%3C/svg%3E")}
.mono{font-family:var(--mono)}
.label{font:500 11px/1 var(--mono);letter-spacing:.22em;text-transform:uppercase;color:var(--ink-6)}
nav{position:absolute;top:0;left:0;right:0;z-index:20;display:flex;justify-content:space-between;align-items:center;padding:20px clamp(20px,8vw,115px)}
.brand{display:flex;align-items:center;gap:10px;font:600 15px/1 var(--sans);color:var(--ink-9)}
.brand svg{width:20px;height:20px}
nav .links{display:flex;gap:28px;font:500 11px/1 var(--mono);letter-spacing:.22em;color:var(--ink-7)}
nav .links a:hover{color:var(--ink-9)}
.hero{position:relative;min-height:100vh;padding:150px clamp(20px,16.6vw,240px) 120px;overflow:hidden}
#planet{position:absolute;inset:0;width:100%;height:100%;z-index:1}
.hero>*:not(canvas){position:relative;z-index:10;min-width:0}
.eyebrow{font:500 11px/1 var(--mono);letter-spacing:.3em;color:var(--dim);text-transform:uppercase}
h1{margin-top:22px;font:500 clamp(40px,4.75vw,68px)/1.02 var(--sans);letter-spacing:-.035em;color:oklch(97% .006 220)}
h1 span{display:block}h1 .l2{color:oklch(74% .024 245)}h1 .l3{color:var(--accent)}h1 .l3 i{font-style:normal;color:oklch(97% .006 220)}
.sub{margin-top:30px;max-width:540px;font-size:17px;line-height:1.65;color:var(--ink-7)}.sub b{font-weight:400;color:var(--ink-9)}
.install{margin-top:40px;max-width:640px;min-width:0}
.tabs{display:flex;align-items:flex-end;gap:4px;border-bottom:1px solid transparent}
.tabs button{appearance:none;background:none;border:0;border-bottom:1px solid transparent;padding:8px 10px;font:500 11px/1 var(--mono);letter-spacing:.22em;text-transform:uppercase;color:var(--ink-6);cursor:pointer}
.tabs button[aria-selected=true]{color:var(--ink-9);border-bottom-color:var(--accent)}
.tabs button:hover{color:var(--ink-7)}.tabs .right{margin-left:auto;padding:8px 0;color:var(--ink-6)}
.cmd{display:flex;margin-top:10px;border:1px solid var(--line);background:#08080bcc;min-height:50px}
.cmd .p{display:grid;place-items:center;width:34px;border-right:1px solid var(--line);font:500 13px var(--mono);color:var(--accent)}
.cmd code{flex:1;min-width:0;display:flex;flex-direction:column;justify-content:center;gap:4px;padding:10px 14px;font:400 13.5px/1.5 var(--mono);color:var(--ink-9);overflow-x:auto;white-space:nowrap}
.cmd button{appearance:none;background:none;border:0;border-left:1px solid var(--line);padding:0 16px;font:500 11px/1 var(--mono);letter-spacing:.22em;color:var(--ink-7);cursor:pointer}
.cmd button:hover{color:var(--ink-9);background:oklch(100% 0 0/.04)}
.compat{margin-top:38px;max-width:560px}.compat ul{display:flex;flex-wrap:wrap;gap:14px 40px;margin-top:20px;list-style:none}
.compat li{color:var(--ink-9);opacity:.5}.compat li:nth-child(3n+1){opacity:.28}.compat li:nth-child(3n){opacity:.85}
.compat svg{display:block;width:24px;height:24px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
.rail{position:fixed;left:20px;top:50%;transform:translateY(-50%);z-index:30;border:1px solid var(--line);display:none}
.rail a{position:relative;display:grid;place-items:center;width:56px;height:56px;background:var(--bg);color:var(--ink-5);border-bottom:1px solid var(--line)}
.rail a:last-child{border-bottom:0}.rail a:hover,.rail a.on{color:var(--ink-9)}.rail a.on:before{content:"";position:absolute;left:-1px;top:0;bottom:0;width:1px;background:var(--accent)}
.rail svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}
.rail em{position:absolute;right:4px;bottom:4px;font:400 8px/1 var(--mono);letter-spacing:.1em;font-style:normal;opacity:.55}
@media (min-width:1100px){.rail{display:block}}
section{position:relative;z-index:10;padding:96px clamp(20px,16.6vw,240px);border-top:1px solid var(--line)}
section .num{font:500 11px/1 var(--mono);letter-spacing:.3em;color:var(--dim);text-transform:uppercase}
h2{margin-top:16px;font:500 clamp(30px,3vw,42px)/1.08 var(--sans);letter-spacing:-.03em;color:var(--ink-9)}h2 i{font-style:normal;color:var(--accent)}
section>p.lead{margin-top:16px;max-width:620px;color:var(--ink-7)}
.grid{margin-top:40px;display:grid;border-top:1px solid var(--line);border-left:1px solid var(--line)}
.grid>*{border-right:1px solid var(--line);border-bottom:1px solid var(--line);padding:20px;min-width:0}
.g5{grid-template-columns:repeat(5,1fr)}.g4{grid-template-columns:repeat(4,1fr)}.g3{grid-template-columns:repeat(3,1fr)}
.cell b{display:block;margin-top:14px;font:500 17px/1.2 var(--sans);color:var(--ink-9)}.cell small{display:block;margin-top:6px;font:400 12px/1.5 var(--mono);color:var(--ink-6)}
.cell .n{font:500 11px/1 var(--mono);letter-spacing:.2em;color:var(--accent)}
.cell code{font:500 13px/1.3 var(--mono);color:var(--ink-9)}.cell p{margin-top:8px;font-size:14px;line-height:1.5;color:var(--ink-7)}
table{margin-top:40px;width:100%;border-collapse:collapse;border-top:1px solid var(--line)}
td{padding:14px 16px 14px 0;border-bottom:1px solid var(--line);vertical-align:top;font-size:15px;color:var(--ink-7)}
td:first-child{white-space:nowrap;font:500 13px/1.7 var(--mono);color:var(--ink-9);padding-right:28px}td:first-child:before{content:"$ ";color:var(--accent)}
pre{margin-top:28px;border:1px solid var(--line);background:#08080bcc;padding:18px 20px;font:400 12.5px/1.75 var(--mono);color:var(--ink-6);overflow-x:auto}
pre b{font-weight:500;color:var(--ink-9)}pre i{font-style:normal;color:var(--accent)}pre u{text-decoration:none;color:var(--rim)}
.notes{margin-top:32px;list-style:none;border-top:1px solid var(--line)}
.notes li{border-bottom:1px solid var(--line)}.notes a{display:flex;gap:16px;align-items:baseline;padding:14px 0;color:var(--ink-7)}
.notes a:hover{color:var(--ink-9)}.notes a span{font:500 11px/1 var(--mono);letter-spacing:.18em;color:var(--ink-6);min-width:92px;text-transform:uppercase}
.chart{margin-top:40px;border-top:1px solid var(--line)}
.row{display:grid;grid-template-columns:38% minmax(0,1fr) 150px;gap:8px 28px;align-items:center;padding:18px 0;border-bottom:1px solid var(--line)}
.row h3{font:500 16px/1.3 var(--sans);color:var(--ink-9)}.row h3+small{display:block;margin-top:4px;font:400 11.5px/1.5 var(--mono);color:var(--ink-6)}
.bars{display:grid;gap:7px;background-image:linear-gradient(to right,var(--line) 1px,transparent 1px);background-size:25% 100%}
.bar{display:flex;align-items:center;gap:10px;font:400 12px/1 var(--mono);color:var(--ink-6);white-space:nowrap}
.bar i{display:block;height:10px;background:var(--before)}
.bar.after{color:var(--ink-9)}.bar.after i{background-color:var(--accent);background-image:linear-gradient(90deg,transparent calc(100% - 18px),#0008 0),repeating-conic-gradient(#0000 0 25%,#0006 0 50%);background-size:auto,4px 4px;background-blend-mode:normal}
.delta{font:500 22px/1 var(--sans);letter-spacing:-.02em;color:var(--ink-9);text-align:right;white-space:nowrap}
.legend{display:flex;gap:22px;margin-top:28px;font:500 11px/1 var(--mono);letter-spacing:.2em;text-transform:uppercase;color:var(--ink-6)}
.legend i{display:inline-block;width:22px;height:8px;margin-right:8px;background:var(--before)}.legend .a i{background:var(--accent)}
details{margin-top:24px;font-size:13.5px;color:var(--ink-6)}summary{cursor:pointer;font:500 11px/1 var(--mono);letter-spacing:.2em;text-transform:uppercase;color:var(--ink-7)}
details ul{margin-top:14px;list-style:none;display:grid;gap:8px}details li b{font-weight:500;color:var(--ink-7)}
.panel h3{font:500 16px/1.3 var(--sans);color:var(--ink-9)}.panel .bar{margin-top:8px}.panel .who{margin-top:18px;font:500 10.5px/1 var(--mono);letter-spacing:.2em;text-transform:uppercase;color:var(--ink-6)}
.panel .bar b{font:500 18px/1 var(--sans);color:var(--ink-9)}.panel .sd{margin-top:6px;font:400 11px/1 var(--mono);color:var(--ink-6)}
.caption{margin-top:22px;max-width:680px;font-size:14.5px;color:var(--ink-7)}.caption b{font-weight:500;color:var(--ink-9)}
.frames{margin-top:40px;display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);border:1px solid var(--line)}
.frames figure{position:relative;background:var(--bg)}.frames img{display:block;width:100%;height:auto;aspect-ratio:16/9;object-fit:cover}
.frames figcaption{position:absolute;left:8px;bottom:8px;padding:5px 8px;background:#050507e6;font:500 10px/1 var(--mono);letter-spacing:.18em;text-transform:uppercase;color:var(--ink-9)}
ul.plain{margin-top:24px;display:grid;gap:10px;list-style:none;max-width:680px}ul.plain li{padding-left:18px;position:relative}ul.plain li:before{content:"";position:absolute;left:0;top:.7em;width:6px;height:1px;background:var(--accent)}
footer{position:relative;z-index:10;display:flex;flex-wrap:wrap;gap:14px 28px;justify-content:space-between;padding:28px clamp(20px,16.6vw,240px) 40px;border-top:1px solid var(--line);font:500 11px/1.6 var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--ink-6)}
footer a{color:var(--ink-7)}footer a:hover{color:var(--ink-9)}
a:focus-visible,button:focus-visible,summary:focus-visible{outline:1px solid var(--rim);outline-offset:2px}
@media (max-width:600px){.cmd code{white-space:normal;overflow-wrap:anywhere}}
@media (max-width:900px){nav,.hero,section,footer{padding-left:22px;padding-right:22px}.tabs button{white-space:nowrap}.cmd code{font-size:12.5px}h1{font-size:clamp(38px,11vw,56px)}.g5,.g4{grid-template-columns:repeat(2,1fr)}.g3{grid-template-columns:1fr}.row{grid-template-columns:1fr}.delta{text-align:left}.frames{grid-template-columns:repeat(2,1fr)}
.hero{padding-top:120px;padding-bottom:230px}nav .links a.hide{display:none}.tabs{overflow-x:auto}.tabs .right{display:none}td{display:block;border:0;padding:0 0 12px}td:first-child{padding-top:12px;border-top:1px solid var(--line);white-space:normal;word-break:break-word}table{border-top:0;border-bottom:1px solid var(--line)}section{padding-top:72px;padding-bottom:72px}}
html.banner .hero{min-height:640px;height:640px;padding:104px 140px 0}html.banner nav{padding:20px 60px}html.banner h1{font-size:58px;margin-top:18px}html.banner .sub{margin-top:20px;font-size:16px}
html.banner .install{margin-top:26px;max-width:540px}html.banner .compat,html.banner .rail,html.banner section,html.banner footer{display:none}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important;animation:none!important}}
"""

JS = r"""
(()=>{
if(location.hash==='#banner')document.documentElement.classList.add('banner');
// the planet: a dithered arc and stippled particles, drawn once on a coarse pixel grid from a seeded generator
const cv=document.getElementById('planet');if(cv){
const draw=()=>{const hero=cv.parentElement,W=hero.clientWidth,H=hero.clientHeight,px=3,cw=Math.ceil(W/px),chh=Math.ceil(H/px);
cv.width=cw;cv.height=chh;cv.style.imageRendering='pixelated';const g=cv.getContext('2d'),im=g.createImageData(cw,chh),d=im.data;
let s=20261012;const rnd=()=>{s=(s+0x6D2B79F5)|0;let t=Math.imul(s^(s>>>15),1|s);t=(t+Math.imul(t^(t>>>7),61|t))^t;return((t^(t>>>14))>>>0)/4294967296};
const wide=W>=700,R=(wide?W*1.9:H*.62)/px,cx=(wide?W*1.74:W*1.05)/px,cy=(wide?H*.176+W*1.9:H*1.42)/px,fall=wide?1:.55;
const put=(i,r,gg,b,a)=>{d[i]=r;d[i+1]=gg;d[i+2]=b;d[i+3]=a};
for(let y=0;y<chh;y++)for(let x=0;x<cw;x++){const dist=Math.hypot(x-cx,y-cy)-R,i=(y*cw+x)*4;
if(dist<0){const depth=-dist*px;                       // inside: a thin blue rim, then mottled magenta thinning into the dark
if(depth<6){rnd()<.82?put(i,140,156,251,255):put(i,205,190,255,255)}
else{const lum=.5*Math.max(0,1-depth/(H*.95))+(rnd()-.5)*.26,r=rnd();
if(depth<46&&rnd()<.3*(1-depth/46))put(i,140,156,251,255);
else r<lum?(rnd()<.12?put(i,255,160,228,255):put(i,248,79,204,255)):(rnd()<.55?put(i,119,2,85,255):put(i,26,4,24,255))}}
else{const far=dist*px,p=.3*Math.exp(-far/(45*fall))+.035*Math.exp(-far/(170*fall))+.0005;if(rnd()<p)put(i,245,245,245,far<50?255:120+rnd()*135)}}
g.putImageData(im,0,0)};
draw();let t;addEventListener('resize',()=>{clearTimeout(t);t=setTimeout(draw,150)})}
// install tabs
const tabs=[...document.querySelectorAll('.tabs button')],out=document.querySelector('#cmd code'),note=document.querySelector('.tabs .right');
const show=b=>{tabs.forEach(x=>x.setAttribute('aria-selected',x===b));out.innerHTML=b.dataset.cmd.split('|').map(l=>'<span>'+l.replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</span>').join('');out.dataset.copy=b.dataset.cmd.split('|').join('\n');if(note)note.textContent=b.dataset.note||''};
tabs.forEach(b=>b.addEventListener('click',()=>show(b)));if(tabs[0])show(tabs[0]);
// copy buttons (clipboard API, with a fallback for pages opened from a file)
document.querySelectorAll('[data-copy-from]').forEach(btn=>btn.addEventListener('click',async()=>{const src=document.querySelector(btn.dataset.copyFrom),text=src.dataset.copy||src.textContent;
try{await navigator.clipboard.writeText(text)}catch(e){const ta=document.createElement('textarea');ta.value=text;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();try{document.execCommand('copy')}catch(_){}ta.remove()}
const old=btn.textContent;btn.textContent='COPIED';setTimeout(()=>btn.textContent=old,1200)}));
// the rail follows the section in view
const links=[...document.querySelectorAll('.rail a')];if('IntersectionObserver'in window&&links.length){const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting)links.forEach(a=>a.classList.toggle('on',a.getAttribute('href')==='#'+e.target.id))}),{rootMargin:'-45% 0px -50% 0px'});
document.querySelectorAll('section[id]').forEach(s=>io.observe(s))}
})();
"""

RAIL = [("loop", "The loop", "M4 12a8 8 0 0 1 13.7-5.7M20 12a8 8 0 0 1-13.7 5.7M17 3v4h-4M7 21v-4h4"),
        ("skills", "Skills", "M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z"),
        ("cli", "The wise CLI", "M3 5h18v14H3zM7 10l3 2-3 2M12.5 14.5H17"),
        ("knowledge", "Knowledge base", "M6 3h9l4 4v14H6zM9.5 12h6M9.5 16h6"),
        ("measured", "Measured", "M4 20V10M10 20V4M16 20v-8M22 20H2"),
        ("versus", "With vs without", "M5 20V8h5v12M14 20V5h5v15M3 20h18"),
        ("built", "Built with it", "M3 5h18v14H3zM10 9l5.5 3-5.5 3z"),
        ("install", "Install", "M12 3v12M7 10l5 5 5-5M4 20h16")]

LOOP = [("Recon", "wise scan"), ("Slice", "one playable loop"), ("Economy", "player-model bots"), ("UI kit", "one golden CTA"), ("Feel + audio", "a measured mix"),
        ("Performance", "60 fps that holds"), ("Browser QA", "wise qa"), ("Release", "a build read through"), ("Trailer", "wise video compile"), ("Field note", "a note and a pull request")]

SKILLS = [("make-web-game", "The loop, the producer contract, the golden rules, and which skill to open next"),
          ("web-game-recon", "Stack, saves, analytics, debug hooks and the baseline, before anything changes"),
          ("game-economy", "Player-model bots, a difficulty index, rising-sine stages, boss tiers"),
          ("game-ui-kit", "One golden call to action, a one-row battle bar, a wordless first session"),
          ("game-feel-audio", "Bosses you feel, and a mix that is measured, never played aloud"),
          ("game-performance", "Budgets, real late-stage tests, a quality guard that recovers"),
          ("browser-qa", "Muted phone bots that tap like players; errors and overflow fail the run"),
          ("release-web-game", "Version, prebuilt deploy, live checks, frozen older versions"),
          ("agent-orchestration", "A lead, workers, file ownership, milestone notes"),
          ("trailer-video", "A hook in 3 s, the loop by 8 s, a slow-motion finale"),
          ("design-boards", "HTML mockups to phone-sized boards"),
          ("share-field-notes", "Read the knowledge base, write a note from the template, open the PR")]

CLI = [("wise scan", "What any game or any video clip is made of: engine, versions, entry points, build targets, assets; duration, cuts and loudness."),
       ("wise qa", "For web games: a muted phone-sized browser that taps like a player. Console errors and overflow fail the run."),
       ("wise board", "HTML mockups in, phone-sized screens and one review board out."),
       ("wise music-enhance", "Loudness measured and fixed to a target with ffmpeg, on audio or a video's audio track. Never played."),
       ("wise video compile", "An edit list in, a finished trailer out.")]

INSTALL = [("Claude Code", "/plugin marketplace add Wiserax/wisecraft|/plugin install wisecraft@wisecraft", "in the agent"),
           ("Codex", "codex plugin marketplace add Wiserax/wisecraft|codex plugin add wisecraft@wisecraft", "shell"),
           ("Gemini", "gemini extensions install https://github.com/Wiserax/wisecraft", "shell"),
           ("Cursor", "git clone https://github.com/Wiserax/wisecraft", "then open the folder"),
           ("Skills", "npx skills add https://github.com/Wiserax/wisecraft", "any agent")]

AGENTS = [("Claude Code", "M12 3v18M3 12h18M5.6 5.6l12.8 12.8M18.4 5.6L5.6 18.4"), ("Codex", "M12 3l8 4.5v9L12 21l-8-4.5v-9z"), ("Cursor", "M5 3l14 9-6 1.5L10 20z"),
          ("Gemini CLI", "M12 3c1 5 4 8 9 9-5 1-8 4-9 9-1-5-4-8-9-9 5-1 8-4 9-9z"), ("Copilot", "M4 9h16v8a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3zM9 13v2M15 13v2"), ("OpenCode", "M8 7l-5 5 5 5M16 7l5 5-5 5")]

NOTES = ["a-double-size-boss-stood-half-a-metre-out-of-reach-and-never.md", "the-audio-mix-measured-not-listened-to-music-at-34-lufs-made.md",
         "a-quality-guard-that-asked-for-13-ms-frames-never-recovered.md", "sim-bots-and-a-real-browser-bot-disagree-about-the-first-ses.md"]
FRAMES = [("boss", "2x boss slam"), ("horde", "8,000 at 60 fps"), ("titan", "titan wave"), ("vault", "vault reveal"), ("blade", "blade frenzy"), ("clear", "chapter clear")]
TERMINAL = """<b><i>$</i> wise qa http://127.0.0.1:5890/ --ready "window.__game" --seconds 10 --out shots</b>
<u>PASS</u>  chromium 390x844  http://127.0.0.1:5890/  (system chrome)
  ready:        yes after 201 ms  (window.__game)
  game:         window.__game found, keys: sim, state, step, tap; other hooks: __THREE__
  taps:         20 of 20 over 10 s in canvas, seed 1
  blocked:      nothing (every request went through; --block is opt-in)
  errors:       none
  overflow:     none
  failed requests: none
  screenshots:  shots/1-start.png, shots/2-middle.png, shots/3-end.png"""

e = html.escape


def logo(size=20, ink="#F5F5F5", accent="#45E3E0"):
    return (f'<svg viewBox="0 0 100 100" width="{size}" height="{size}" aria-hidden="true"><polygon points="{MARK}" fill="{ink}"/>'
            f'<rect x="39" y="10" width="22" height="17" fill="{accent}"/></svg>')


def icon(d):
    return f'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="{d}"/></svg>'


def bars_before_after(data):
    out = []
    for r in data:
        top = max(abs(r["before"]), abs(r["after"]))
        b, a = abs(r["before"]) / top * 100, abs(r["after"]) / top * 100
        out.append(f'<div class="row"><div><h3>{e(r["label"])}</h3><small>{e(r["note"])}</small></div><div class="bars">'
                   f'<div class="bar"><i style="width:{b * .78:.1f}%"></i>{e(r["before_text"])}</div>'
                   f'<div class="bar after"><i style="width:{a * .78:.1f}%"></i>{e(r["after_text"])}</div></div><div class="delta">{e(r["change"])}</div></div>')
    return "".join(out)


def tok(v):
    return f"{v / 1e6:.2f} M" if v >= 1e6 else f"{v / 1e3:.0f} k"


def panels(R):
    S = R["summary"]
    spec = [("Checks passed", "pass_rate", lambda v: f"{v * 100:.0f}%", lambda v: f"± {v * 100:.0f}"), ("Minutes per task", "minutes", lambda v: f"{v:.1f}", lambda v: f"± {v:.1f}"),
            ("Tokens per task", "tokens", tok, lambda v: "± " + tok(v))]
    out = []
    for title, key, fmt, fsd in spec:
        top = max(S[a][key]["mean"] for a in ("with", "without"))
        cell = [f'<div class="panel"><h3>{title}</h3>']
        for arm in ("without", "with"):
            c = S[arm][key]
            cell.append(f'<div class="who">{"with wisecraft" if arm == "with" else "without"}</div><div class="bar{" after" if arm == "with" else ""}">'
                        f'<i style="width:{c["mean"] / top * 62:.1f}%"></i><b>{fmt(c["mean"])}</b></div><div class="sd">{fsd(c["sd"])} · n = {c["n"]}</div>')
        out.append("".join(cell) + "</div>")
    return "".join(out)


def site(data, R, idx, have_frames):
    by = {Path(n["path"]).name: n for n in idx}
    rail = "".join(f'<a href="#{i}" title="{e(t)}" aria-label="{e(t)}">{icon(d)}<em>{n + 1:02d}</em></a>' for n, (i, t, d) in enumerate(RAIL))
    tabs = "".join(f'<button role="tab" aria-selected="false" data-cmd="{e(c)}" data-note="{e(n)}">{e(a)}</button>' for a, c, n in INSTALL)
    compat = "".join(f'<li title="{e(n)}"><svg viewBox="0 0 24 24" role="img" aria-label="{e(n)}"><path d="{d}"/></svg></li>' for n, d in AGENTS)
    loop = "".join(f'<div class="cell"><span class="n">{i + 1:02d}</span><b>{e(a)}</b><small>{e(b)}</small></div>' for i, (a, b) in enumerate(LOOP))
    skills = "".join(f'<a class="cell" href="{REPO}/tree/main/skills/{n}"><code>{n}</code><p>{e(t)}</p></a>' for n, t in SKILLS)
    cli = "".join(f"<tr><td>{e(c)}</td><td>{e(t)}</td></tr>" for c, t in CLI)
    notes = "".join(f'<li><a href="{REPO}/blob/main/knowledge/{by[n]["path"]}"><span>{by[n]["kind"]}</span>{e(by[n]["title"])}</a></li>' for n in NOTES)
    sources = "".join(f'<li><b>{e(r["label"])}</b>: {e(r["before_text"])} to {e(r["after_text"])}. {e(r["source"])}.</li>' for r in data)
    frames = "".join(f'<figure><img src="frames/{n}.jpg" alt="{e(c)}: a frame from the shipped game" loading="lazy" width="480" height="270"><figcaption>{e(c)}</figcaption></figure>' for n, c in FRAMES) if have_frames else ""
    inst = "".join(f'<tr><td>{e(c.split("|")[0])}</td><td>{e(a)}{" · then " + e(c.split("|")[1]) if "|" in c else ""}</td></tr>' for a, c, _ in INSTALL)
    S = R["summary"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>wisecraft: the game studio with the agents wired in</title>
<meta name="description" content="Skills, a CLI and a shared knowledge base that let any AI coding agent build, balance, polish and ship a mobile web game.">
<meta name="theme-color" content="#050507">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' fill='%23050507'/%3E%3Cpolygon points='{MARK}' fill='%23F5F5F5'/%3E%3Crect x='39' y='10' width='22' height='17' fill='%2345E3E0'/%3E%3C/svg%3E">
{FONTS}
<style>{CSS}</style>
</head>
<body>
<div class="grain" aria-hidden="true"></div>
<nav aria-label="Site"><a class="brand" href="#top" aria-label="wisecraft, top of page">{logo()}wisecraft</a>
<div class="links"><a href="{REPO}#readme">DOCS</a><a href="{REPO}">GITHUB <span aria-hidden="true">↗</span></a></div></nav>
<aside class="rail" aria-label="Sections">{rail}</aside>
<main id="top">
<header class="hero">
<canvas id="planet" aria-hidden="true"></canvas>
<p class="eyebrow">wisecraft · for ai agents</p>
<h1><span>The game studio</span><span class="l2">with the agents</span><span class="l3">wired in<i>.</i></span></h1>
<p class="sub">Skills, a CLI and field notes that let any AI coding agent build, balance, polish and ship a mobile web game. <b>Measured in a real phone browser, not promised.</b></p>
<div class="install"><div class="tabs" role="tablist" aria-label="Install for your agent">{tabs}<span class="label right" aria-hidden="true"></span></div>
<div class="cmd" id="cmd"><span class="p" aria-hidden="true">$</span><code aria-live="polite"></code><button type="button" data-copy-from="#cmd code">COPY</button></div></div>
<div class="compat"><p class="label">Compatible</p><ul>{compat}</ul></div>
</header>

<section id="loop"><p class="num">01 · the loop</p><h2>One loop, <i>every time</i>.</h2>
<p class="lead">Ask for anything: “stage 1 is boring”, “the explosions are too loud”, “it lags on stage 7”. The agent finds its place in the loop and works from there.</p>
<div class="grid g5">{loop}</div></section>

<section id="skills"><p class="num">02 · skills</p><h2>Twelve skills. <i>One router</i>.</h2>
<p class="lead">Agent Skills format. The same files for every agent; <span class="mono">make-web-game</span> says which one to open next.</p>
<div class="grid g4">{skills}</div></section>

<section id="cli"><p class="num">03 · the wise cli</p><h2>Tools that <i>measure</i>.</h2>
<p class="lead">One Python CLI. Every command has <span class="mono">--help</span> with examples.</p>
<table><tbody>{cli}</tbody></table>
<pre aria-label="Real output of wise qa on the sample game">{TERMINAL}</pre></section>

<section id="knowledge"><p class="num">04 · knowledge base</p><h2>{len(idx)} field notes, <i>written by agents</i>.</h2>
<p class="lead">Each one is a problem a real web game hit, the cause and the fix: versions, verification, and what was not verified. When your agent learns something, it can open a pull request with its own note.</p>
<ul class="notes">{notes}</ul>
<pre><b><i>$</i> cp knowledge/TEMPLATE.md knowledge/games/my-roguelite/a-dash-that-never-clips-walls.md</b>
<b><i>$</i> gh pr create --fill</b></pre></section>

<section id="measured"><p class="num">05 · measured</p><h2>Before and after, <i>on a shipped game</i>.</h2>
<p class="lead">A horde tower defense for phones: Vite + three.js, 8,000 enemies on screen at 60 fps. One project, one machine; each figure is a single measurement or a small set, as its source says.</p>
<div class="legend"><span><i></i>before</span><span class="a"><i></i>after</span></div>
<div class="chart">{bars_before_after(data)}</div>
<details><summary>Where each number comes from</summary><ul>{sources}</ul></details></section>

<section id="versus"><p class="num">06 · with vs without</p><h2>A benchmark that <i>shows nothing yet</i>.</h2>
<p class="lead">Three toy tasks on a 200-line sample game, {R['meta']['runs']} headless runs, scored by script.</p>
<div class="grid g3">{panels(R)}</div>
<p class="caption">Three toy tasks, {R['meta']['runs']} runs: {S['with']['pass_rate']['mean'] * 100:.0f}% vs {S['without']['pass_rate']['mean'] * 100:.0f}% of checks. <b>The tasks were too easy to separate the two</b>, so this shows no difference yet. Harder, real-game tasks are next. Harness and raw results: <a href="{REPO}/tree/main/benchmarks"><u>benchmarks/</u></a>.</p></section>

<section id="built"><p class="num">07 · built with it</p><h2>Written while <i>shipping one</i>.</h2>
<ul class="plain"><li>Ten-stage chapters shaped as a rising sine, with bosses and a titan that walk in from the edge of the field and slam the walls.</li>
<li>Balanced with four player-model bots, then proven with a browser bot that taps the real UI.</li>
<li>A mix measured in a muted browser and never played aloud by an agent.</li>
<li>A producer, a lead agent and worker agents; every step written down.</li></ul>
<div class="frames">{frames}</div></section>

<section id="install"><p class="num">08 · install</p><h2>Pick your agent. <i>Same skills</i>.</h2>
<table><tbody>{inst}<tr><td>uv tool install git+{REPO}</td><td>The CLI alone</td></tr></tbody></table>
<p class="caption">Needs Python 3.10+, Node 18+ and ffmpeg. The browser tools use Playwright from your game's folder.</p></section>
</main>
<footer><span>MIT · created by Alex Wiserax</span><span>Architecture adapted from <a href="https://github.com/rehan-remade/universal-modder">Universal Modder</a> by Rehan, MIT</span><a href="{REPO}">github.com/Wiserax/wisecraft</a></footer>
<script>{JS}</script>
</body>
</html>
"""


def media(data, R, frames):
    """One page of templates for the README media; scripts/shoot.mjs screenshots every [data-shot] element."""
    f = frames.resolve().as_uri() if frames else ""
    light = "--bg:#ffffff;--ink-5:#6e6e78;--ink-6:#55555e;--ink-7:#3a3a42;--ink-9:#0a0a0c;--accent:#0e9aa1;--rim:#2a6f9c;--dim:#3d7f85;--line:#0a0a0c1a;--before:#0a0a0c2e;"
    chart = lambda theme: (f'<div data-shot="before-after-{theme}" data-scale="2" class="shot" style="width:800px;padding:28px 32px;{light if theme == "light" else ""}background:var(--bg)">'
                           f'<p class="label">measured on the shipped game</p><div class="legend" style="margin-top:14px"><span><i></i>before</span><span class="a"><i></i>after</span></div>'
                           f'<div class="chart" style="margin-top:18px">{bars_before_after(data)}</div></div>')
    bench = lambda theme: (f'<div data-shot="benchmark-{theme}" data-scale="2" class="shot" style="width:800px;padding:28px 32px;{light if theme == "light" else ""}background:var(--bg)">'
                           f'<p class="label">with vs without wisecraft · {R["meta"]["runs"]} runs on 3 toy tasks</p><div class="grid g3" style="margin-top:18px">{panels(R)}</div></div>')
    badge = lambda slug, a, b: (f'<div data-shot="badges/{slug}" data-scale="2" data-clear="1" class="shot" style="display:inline-flex;align-items:center;gap:9px;height:26px;padding:0 11px;border:1px solid #ffffff24;background:#050507">'
                                f'<i style="width:5px;height:5px;background:var(--accent)"></i><span class="label" style="letter-spacing:.14em;font-size:10px">{a}</span>'
                                f'<span class="label" style="letter-spacing:.14em;font-size:10px;color:var(--ink-9)">{b}</span></div>')
    cardcss = "border:1px solid var(--line);background:#08080b;padding:9px;display:flex;flex-direction:column;gap:9px"
    cap = lambda s: f'<p class="label" style="font-size:9.5px;letter-spacing:.16em;color:var(--ink-7)"><span style="color:var(--accent)">$ </span>{s}</p>' if s.startswith("wise") else f'<p class="label" style="font-size:9.5px;letter-spacing:.16em;color:var(--ink-7)">{s}</p>'
    kv = lambda rows: '<div style="flex:1;display:grid;align-content:center;gap:7px;padding:0 6px">' + "".join(f'<div style="display:flex;justify-content:space-between;gap:8px;white-space:nowrap;font:400 9px var(--mono);color:var(--ink-5)"><span>{k}</span><span style="color:{c or "var(--ink-9)"}">{v}</span></div>' for k, v, c in rows) + "</div>"
    img = lambda n, pos="center": f'<div style="flex:1;min-height:0;background:url({f}/{n}.png) {pos}/cover"></div>'
    arrow = '<div style="align-self:center;color:var(--accent);font:500 12px var(--mono)">→</div>'
    boom = next(r for r in data if "boom" in r["label"])
    slow = next(r for r in data if "Slow-motion" in r["label"])
    cells = "".join(f'<i style="width:11px;height:11px;background:{"var(--accent)" if i < slow["after"] else "#ffffff29"}"></i>' for i in range(24))
    pipeline = f"""<div data-shot="pipeline" data-scale="2" class="shot" style="width:800px;height:433px;padding:22px 20px;background:var(--bg);display:grid;grid-template-rows:auto 1fr auto 1fr;gap:10px">
<p style="font:500 17px/1 var(--sans);letter-spacing:-.02em;color:var(--ink-9)">Balance: <span style="color:var(--ink-7)">bots first, then</span> <span style="color:var(--accent)">a real phone.</span></p>
<div style="display:grid;grid-template-columns:172px auto 172px auto 1fr;gap:8px">
<div style="{cardcss}">{kv([("engine", "three.js + vite", None), ("versions", "0.180 · 7.3", None), ("hook", "window.__game", "var(--rim)"), ("analytics", "/api/events", None), ("audio", "135 files", None)])}{cap("wise scan")}</div>{arrow}
<div style="{cardcss}">{kv([("walls left", "min – max", None), ("tutorial", "22 – 61 %", None), ("fast tapper", "16 – 52 %", None), ("sieges lost", "0 of 16", "var(--rim)")])}{cap("bots × 8 seeds")}</div>{arrow}
<div style="{cardcss}"><div style="flex:1;min-height:0;display:grid;grid-template-columns:repeat(4,1fr);gap:6px">{"".join(f'<div style="background:url({f}/qa-{i}.png) 50% 28%/cover"></div>' for i in (1, 2, 3, 4))}</div>{cap("wise qa --size 390x844")}</div></div>
<p style="font:500 17px/1 var(--sans);letter-spacing:-.02em;color:var(--ink-9);margin-top:6px">Ship: <span style="color:var(--ink-7)">a measured mix,</span> <span style="color:var(--accent)">a smooth trailer.</span></p>
<div style="display:grid;grid-template-columns:172px auto 172px auto 1fr auto 170px;gap:8px">
<div style="{cardcss}">{kv([("music", "-34.1 to -20.0", None), ("", "lufs", None), ("boss boom", boom["before_text"] + " to", None), ("over music", boom["after_text"], "var(--accent)")])}{cap("wise music-enhance")}</div>{arrow}
<div style="{cardcss}"><div style="flex:1;display:grid;place-content:center;gap:8px"><div style="display:grid;grid-template-columns:repeat(8,11px);gap:3px">{cells}</div>
<p style="font:400 9.5px var(--mono);color:var(--ink-5);text-align:center">{slow["after_text"]} frames move<br>was {slow["before_text"]}</p></div>{cap("1 step per frame")}</div>{arrow}
<div style="{cardcss}">{img("titan")}{cap("wise video compile")}</div>{arrow}
<div style="{cardcss}">{img("horde")}{cap('<span style="color:var(--rim)">■</span> 8,000 at 60 fps')}</div></div></div>"""
    tile = f"""<div data-shot="@tile" class="shot" style="position:relative;width:560px;height:315px;background:var(--bg);display:grid;place-content:center;justify-items:center;gap:16px;overflow:hidden">
<div style="display:flex;align-items:center;gap:14px;font:500 44px/1 var(--sans);letter-spacing:-.035em;color:var(--ink-9)">{logo(44)}wisecraft</div>
<p class="label" style="color:var(--rim);letter-spacing:.3em">the game studio in a skill</p></div>"""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">{FONTS}<style>{CSS}
body{{padding:24px;display:grid;gap:24px;justify-items:start;background:#222}}.shot{{position:relative}}.shot .grid{{margin-top:0}}</style></head><body>
{chart("dark")}{chart("light")}{bench("dark")}{bench("light")}
{badge("agents", "works with", "claude code · codex · cursor · gemini · copilot · opencode")}{badge("knowledge", "knowledge base", "field notes by agents, for agents")}{badge("license", "license", "mit")}
{pipeline}{tile}</body></html>
"""


# 12 x 12 pixel icons: (unused, accent path, ink path). scan and video are Universal Modder's (MIT).
ICONS = {
    "scan": (0, "M4 3h2v2h-2zM6 5h2v2h-2z", "M0 0h3v1h-3zM9 0h3v1h-3zM0 1h1v2h-1zM11 1h1v2h-1zM0 8h12v1h-12zM0 9h1v2h-1zM11 9h1v2h-1zM0 11h3v1h-3zM9 11h3v1h-3z"),
    "qa": (3, "M4 6h1v1h-1zM5 7h1v1h-1zM6 6h1v1h-1zM7 5h1v1h-1z", "M2 0h8v1h-8zM2 1h1v10h-1zM9 1h1v10h-1zM2 11h8v1h-8zM5 9h2v1h-2z"),
    "board": (2, "M2 2h3v6h-3z", "M0 0h12v1h-12zM0 1h1v10h-1zM11 1h1v10h-1zM0 11h12v1h-12zM6 2h4v2h-4zM6 5h4v3h-4zM2 9h8v1h-8z"),
    "music-enhance": (1, "M5 1h2v10h-2z", "M1 7h1v4h-1zM3 4h1v7h-1zM8 5h1v6h-1zM10 8h1v3h-1zM0 11h12v1h-12z"),
    "video": (1, "M4 4h2v1h-2zM4 5h4v1h-4zM4 6h6v1h-6zM4 7h4v1h-4zM4 8h2v1h-2z", "M0 0h12v1h-12zM0 1h1v1h-1zM2 1h1v1h-1zM4 1h1v1h-1zM6 1h1v1h-1zM8 1h1v1h-1zM10 1h2v1h-2zM0 2h12v1h-12zM0 3h1v6h-1zM11 3h1v6h-1zM0 9h12v1h-12zM0 10h1v1h-1zM2 10h1v1h-1zM4 10h1v1h-1zM6 10h1v1h-1zM8 10h1v1h-1zM10 10h2v1h-2zM0 11h12v1h-12z"),
}




def icons(out):
    (out / "icons").mkdir(parents=True, exist_ok=True)
    for name, (_, accent, ink) in ICONS.items():
        for theme, a, col in (("dark", "#45E3E0", "#F5F5F5"), ("light", "#0E9AA1", "#0A0A0C")):
            (out / "icons" / f"{name}-{theme}.svg").write_text(
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 12" width="96" height="96" shape-rendering="crispEdges" role="img" aria-label="wise {name}">'
                f'<path fill="{a}" d="{accent}"/><path fill="{col}" d="{ink}"/></svg>\n')


def made_with(out, mono):
    """The "made with wisecraft" badge: a hairline box, the mark, mono capitals drawn as outlines (no web font needed)."""
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont
    f = TTFont(str(mono))
    glyphs, cmap, k, track = f.getGlyphSet(), f.getBestCmap(), 11 / f["head"].unitsPerEm, 2.4

    def text(s, x, y, fill):
        d = []
        for ch in s:
            g = glyphs[cmap[ord(ch)]]
            pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}")
            g.draw(TransformPen(pen, (k, 0, 0, -k, x, y)))
            d.append(pen.getCommands())
            x += g.width * k + track
        return f'<path fill="{fill}" d="{" ".join(c for c in d if c)}"/>', x

    for theme, bg, ink, muted, line, accent in (("dark", "#050507", "#F5F5F5", "#8A8B92", "#FFFFFF2E", "#45E3E0"), ("light", "#FFFFFF", "#0A0A0C", "#6E6E78", "#0A0A0C2E", "#0E9AA1")):
        a, x = text("MADE WITH", 36, 20, muted)
        b, x = text("WISECRAFT", x + 6, 20, ink)
        W = round(x + 10)
        (out / f"made-with-{theme}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 32" width="{W * 2}" height="64" role="img" aria-label="made with wisecraft">'
            f'<rect x=".5" y=".5" width="{W - 1}" height="31" fill="{bg}" stroke="{line}"/>'
            f'<g transform="translate(12 8) scale(.16)"><polygon points="{MARK}" fill="{ink}"/><rect x="39" y="10" width="22" height="17" fill="{accent}"/></g>{a}{b}</svg>\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frames", help="folder with stills of your game, for the media templates (and, with --site, a frames/ folder next to it)")
    ap.add_argument("--site", help="write the long one-page site to this path")
    ap.add_argument("--media", help="also write the media template page to this path (needs --frames)")
    ap.add_argument("--mono", default="~/Library/Fonts/JetBrainsMono-Medium.ttf", help="JetBrains Mono .ttf for the made-with badge outlines")
    ap.add_argument("--shrink", action="store_true", help="quantize docs/media/{banner,pipeline,before-after-*}.png to 256 colours and exit")
    a = ap.parse_args()
    if a.shrink:
        from PIL import Image
        for name in ("banner", "pipeline", "before-after-dark", "before-after-light"):
            f = ROOT / "docs" / "media" / f"{name}.png"
            Image.open(f).convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG).save(f, optimize=True)
        return
    data = json.loads((ROOT / "scripts" / "art_data.json").read_text())["before_after"]
    R = json.loads((ROOT / "benchmarks" / "results.json").read_text())
    idx = []        # every note's path, kind and title, from its front matter
    for f in sorted((ROOT / "knowledge").glob("*/**/*.md")):
        head = f.read_text().split("---", 2)[1]
        field = lambda k: (re.search(rf'^{k}:\s*"?(.*?)"?\s*$', head, re.M) or [None, ""])[1]
        idx.append({"path": f.relative_to(ROOT / "knowledge").as_posix(), "kind": field("kind"), "title": field("title")})
    frames = Path(a.frames) if a.frames else None
    if a.site:
        out = Path(a.site).resolve().parent
        out.mkdir(parents=True, exist_ok=True)
        if frames:
            from PIL import Image
            crops = {"vault": (0.42, 0.03, 0.92, 0.53), "clear": (0.415, 0.07, 0.915, 0.57)}
            (out / "frames").mkdir(exist_ok=True)
            for name, _ in FRAMES:
                im = Image.open(frames / f"{name}.png").convert("RGB")
                if name in crops:
                    W, H = im.size
                    c = crops[name]
                    im = im.crop((int(c[0] * W), int(c[1] * H), int(c[2] * W), int(c[3] * H)))
                im.resize((480, 270), Image.LANCZOS).save(out / "frames" / f"{name}.jpg", quality=72, optimize=True)
        Path(a.site).write_text(site(data, R, idx, (out / "frames" / "boss.jpg").exists()))
        print(f"wrote {a.site} ({Path(a.site).stat().st_size / 1e3:.0f} kB){', frames' if frames else ''}")
    if a.media:
        Path(a.media).write_text(media(data, R, frames))
        icons(ROOT / "docs" / "media")
        made_with(ROOT / "docs" / "media", Path(a.mono).expanduser())
        print("wrote", a.media, "and docs/media/icons, made-with-*.svg")


if __name__ == "__main__":
    main()
