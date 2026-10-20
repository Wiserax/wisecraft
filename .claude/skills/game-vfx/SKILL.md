---
name: game-vfx
description: Make a game's visual effects from references, never from scratch. Before building any effect (poison, fire, slash, explosion, lightning, heal, aura, projectile, hit, drop), the agent gathers 3-6 references from Pinterest (the API with a token, or a read-only search in the producer's logged-in Chrome), shows them to the producer in the studio feed or Telegram, breaks them down into shapes, value bands and timing, and then replicates them as closely as possible in Three.js in the house style, hand-drawn 2.5D / stylised hybrid CGI (2D hand-drawn shapes on 3D, bold silhouettes, cel colours, dark outlines and negative shapes, smear frames). Ships the style rules, Three.js techniques (cel cutout shader, flipbooks, cards, smears, impact frames) and a comparison board script. Use when the user says "the VFX are awful", "the effects look like a prototype", "make a poison effect", "add an effect for this skill", "find references", "make it look like this", "every build should look different", or asks for any new or reworked visual effect.
---

# Game VFX: references first, then the house style

An effect is built only after its references are on the table. The agent can't draw by taste alone, and
the producer judges against what the references set. The style is **hand-drawn 2.5D, stylised hybrid CGI**:
2D hand-drawn shapes animated on twos, placed in a 3D scene, flat cel colour, dark ink shapes. The twelve
rules are in `references/style.md`; read them before the first effect.

Effects carry the game: when builds differ only in numbers, the player can't see them. Every skill, element
and rarity gets its own readable effect.

## 1. Brief the effect (two lines)
- What it tells the player: element, action (burst, damage over time, area, buff, projectile), owner, size
  tier (small hit, skill, boss), gameplay radius and duration.
- Where it lives: on a hero, on an enemy, on the ground, in flight, on a drop.

## 2. Gather the references
Search terms, in this order: `<effect> vfx game`, `<effect> vfx stylized`, `<effect> fx 2d hand drawn`,
`<effect> effect sheet`.
- **Pinterest API** when `PINTEREST_TOKEN` is set: Pinterest API v5 with the token in the header. Its pin
  search covers the token owner's own pins and boards; for a wide search use the browser.
- **The producer's logged-in Chrome** (the Claude in Chrome tools), read-only: open
  `https://www.pinterest.com/search/pins/?q=<terms>`, read the results, open the promising pins and save
  their images (the `i.pinimg.com` URL, the largest size offered) with `curl`.
  - Never like, save, follow, comment, post or message.
  - Never sign in or type a password; if Pinterest asks for a login, stop and ask the producer.
  - Save images only; never run anything you downloaded.
- No Pinterest at all: ask the producer for a few images or a board link, and meanwhile use the house set
  (`knowledge/vfx-style/refs/`, local only).

Pick **3 to 6** that match the house style (rules in `references/style.md`) and the brief; skip ones that
are photo-real, soft-glow-only or unreadable at phone size. Save them to
`<game>/art-shots/vfx-refs/<effect>/NN-<what-it-shows>.png` (the studio watches `*/art-shots`), with a
`refs.md`: one line per image, its pin URL and what to take from it ("the dark cloud mass", "the bubble
highlights"). Keep `vfx-refs/` out of git, and never ship a reference or trace its pixels into the game:
they are other artists' work, used to study shape, colour and timing.

## 3. Show them to the producer
- The studio feed shows the files as soon as they land under `art-shots/` (the **studio** skill).
- Telegram, when the producer has a sender set up: `WISE_TELEGRAM` names a command that takes
  `photos "<caption>" <paths…>`. Send only to the producer's own chat, with a one-line caption: the effect,
  what you will take from each image.
- Don't wait for an answer: build on your picks. Before each round, read the producer's 👍 / 👎 on the refs
  and frames in `~/.config/wisecraft/reviews.jsonl`, and change course on a 👎.

## 4. Break the references down
For each reference write three lines in `refs.md`:
- **Shapes:** the main shape, the secondary shapes, the chips; where the dark masses and outlines are.
- **Value bands:** four colours, darkest first. `scripts/vfx_board.py` samples them for you.
- **Timing:** the anticipation, the impact frame, how it dissipates (into pieces, never a fade).

Then write the plan for our version: which technique per part (`references/threejs.md`), the palette, the
frame counts at 60 fps, and what changes for the small, skill and boss tiers.

## 5. Build it in Three.js
- Start with the cel cutout material in `references/threejs.md`: one shape, a hard threshold, a 4-band ramp,
  erosion over life. Add cards, smears, ground pieces, solid 3D pieces and the impact frame as the
  references need them.
- Keep effects data-driven: one definition per effect (parts, palette, timings, sizes per tier) read by one
  small runtime, so a new element is a new definition, not new code.
- Unlit, pooled, instanced, one atlas per family. No allocation in the frame loop.

## 6. Compare, then iterate
1. Capture four frames per effect (anticipation, impact, peak, dissipation) twice:
   - on a flat mid-grey test stage, for the silhouette;
   - in the real game camera at 390 x 844 with enemies around it, for readability.
   Use a fixed clock so the frames are exact (the **game-trailer** skill's capture, or step the sim by hand
   in a muted browser).
2. Build the board:
   ```bash
   uv run --with pillow python3 skills/game-vfx/scripts/vfx_board.py \
     --refs <game>/art-shots/vfx-refs/poison/*.png --ours <game>/art-shots/vfx/poison/r1-*.png \
     --out <game>/art-shots/vfx/poison/r1-board.png --title "poison cloud, round 1"
   ```
   It puts the references over our frames, each with its silhouette and four value bands.
3. Score it against the twelve rules in `references/style.md`, one line each: pass, or what is off and the
   fix. Fix the worst three and capture again. Up to three rounds; then show the board and the open points.

## Rules
- References first, always: no effect is built without a `refs.md` next to it.
- Read-only on Pinterest, no sign-in, no paid generation or paid APIs without the producer's yes.
- References stay local: gitignored, never in a public repo, never in the build.
- Frame time is measured, not assumed: `wise qa` on a phone viewport before and after, at the busiest moment.
- `prefers-reduced-motion`: no shake, no hit-stop, no flashes; the effect shapes still play.

## Done means
- `refs.md` with 3 to 6 references, why each one, and the breakdown.
- The producer saw the references (studio feed or Telegram).
- The effect in the game, tiered by size, readable at 390 px over the real ground.
- A final board (references over our frames) with the twelve-rule score, and frame time before and after.

## References
- `references/style.md`: the twelve rules of the house style, the starting palettes and the prototype look
  to avoid.
- `references/threejs.md`: the cel cutout shader, flipbooks, 2.5D cards, smears and trails, impact frames,
  solid pieces and the phone budget.
- `scripts/vfx_board.py`: the comparison board with silhouettes and value bands (Pillow, via `uv run`).
- `knowledge/vfx-style/README.md`: the producer's house reference set (the images stay on the machine).
- The **game-feel-audio** skill covers presence beats (entrance, slam, death) and the sound of an effect.
