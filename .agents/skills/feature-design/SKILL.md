---
name: feature-design
description: Turn a game or feature idea into a design the team can build by a deadline, and test it before writing code. Covers the core loop as a numbered cycle, a wordless and diegetic interface map (a board of phone screens with arrows, a loop row and captions), a player panel of persona subagents (hardcore, midcore, casual, non-reader) plus a publisher who judges USPs, market, pillars, the scope for the deadline, the test hypothesis with go/kill thresholds, scalability and risks, and iteration rounds until the panel and the publisher agree. Delivers DESIGN.md, the board PNG, the reviews and a synthesis. Use when the user says "design the game", "what's the core loop", "make an interface map", "how will the game be played", "verify it with players", "think as a publisher", "what are the USPs", "can we ship this by Friday", "scope it to N days", or brings a concept doc for a new prototype or feature.
---

# Feature design: from an idea to a tested, buildable design

The producer reads boards, not documents, and a design is only good once players and a publisher have
picked at it. This skill runs the whole loop: cycle → interface map → panel → synthesis → v2 → panel again →
deliver. Plan for **2 rounds**; a round takes about 30-60 minutes with agents.

## 0. Inputs (gather, don't ask)
- The concept: the producer's doc or messages, plus any reference games they named.
- **The constraints, written down:** the deadline (e.g. "Wed → release Fri"), team size, platform (web,
  phone), orientation, "no real multiplayer", wordless or not.
- **Real engine frames,** if anything runs. Mockups over real screenshots beat CSS-only screens, and the
  panel must judge the look you can actually build, not concept art.
- The studio's test metrics, if known (the **game-meta** skill reads real data).

## 0b. References from the producer
When the producer pastes screenshots of other games ("like Roboquest", "close to Shape of Dreams"), save them
first into `<design>/references/` with descriptive names (`roboquest-compare-stats.png`), then cite them on
the board and in the reviewer prompts. Copy the **mechanic**, not the art style.

## 1. The cycle (the core loop as numbered steps)
Write the run or session as **10-12 numbered steps**: screen · what the player does · what happens. Mark the
**loop** explicitly (which steps repeat, and what interrupts them: a boss every N, a death). One step = one
board screen. If a step has no clear player action, it's dead time: cut it or merge it.

## 2. The interface: wordless, or short text
Ask which mode the game is in. **Wordless:** every number becomes an object (below). **Short text** (an
action-RPG shop, loot): a name ≤ 2 words, ≤ 2 stat chips, 1 effect line ≤ 7 words, "hold for details";
verbs a 9-year-old reads ("Sell", not "Dismantle"); a compare that shows every stat you lose.

### Wordless mode
Give every piece of information a signal in the world: a size, fill, count of objects, colour or motion.
Use the catalogue in `references/wordless-ui.md` (proven signals and the ones that failed panel reviews).
Put the table in DESIGN.md: information → signal.

## 3. DESIGN.md and the board
- **DESIGN.md:** start from `assets/DESIGN.template.md`. Sections: the cycle, wordless signals, content for
  the deadline (MUST/SHOULD/LATER), the test (hypothesis, events, go/kill), the gates per day, and open
  choices with defaults.
- **Two kinds of screens, used together:** AI concept frames of the whole flow (fast to make, and they sell
  the feel: brief an image agent with the exact style reference and one frame per step), plus **exact HTML UI
  specs** for the screens that carry rules (a shop card, a drop label, a compare/replace panel). The build
  follows the HTML spec; concept frames drift (wrong wording, extra HUD).
- **The board:** one `.screen` per step at 390×844 (or landscape), rendered with `wise board`
  (the **design-boards** skill). Use `assets/board-flow.html`: rows of screens with ➜ arrows, a dashed
  **loop row** saying what repeats, captions as "N · what happens" plus one line of why, and a red line for
  what's cut. Put real engine frames behind the overlays and real model renders for key objects. Say on the
  board which parts are placeholders.
- Look at the rendered board yourself before showing anyone: wrong-order backdrops (an item visible before
  it's earned), leftover text and emoji that read as words are the usual misses.

## 4. The player panel (round 1)
Run the reviewers in `references/player-panel.md` as **parallel subagents** (they must not see each other):
hardcore + midcore, casual + non-reader, publisher. Each looks at the board PNG, DESIGN.md and the real
frames, answers a fixed question list, and writes `review-v1/REVIEW-<group>.md`. Respect the studio's agent
limit (for example at most 4 workers at once).

## 5. Synthesis and v2
- `review-v1/SYNTHESIS.md`: a table of fix · who asked · what v2 changes. **Count agreements:** a fix 3
  reviewers want is a must. The non-reader decides the UI; the publisher decides the scope; the players decide
  the fun.
- Write `DESIGN-v2.md` and a new board (`board-v2.png`). Put the scores of round 1 on the board's subtitle.
- **Typical v1 → v2 moves:**
  - promote the one novel mechanic to the first 20 seconds;
  - cut every system that isn't the hypothesis;
  - replace abstract HUD signals with objects;
  - make ads the same size as the free choice;
  - remove stray words.

### When the producer rejects a direction
"Too heavy / boring" means you added systems, not fun. Go back to the one image or moment they liked, ask
what the loop around it is, and restart the cycle from there (v3 → v4 in the worked example). Keep the panel:
resume the same reviewers on the new direction.

## 6. Round 2 and stop
Resume the **same** reviewers (they keep their context) with: "here is v2 and what changed; mark each of your
issues FIXED / PARTLY / NOT; any new problems; new ratings; the top 3 remaining." Write `review-v2/`.
Stop when no screen is LOST for the non-reader and the publisher says green-light; otherwise one more
round on the remaining issues only.

## 7. The publisher lens, also for you
Answer `references/publisher-lens.md` yourself before reading the publisher's review:
- the 3 USPs as ad lines and the 3-second ad;
- the market;
- the pillars and non-pillars;
- MUST / SHOULD / LATER sized to the deadline, with a playable build every day;
- the hypothesis, events, go/kill thresholds;
- scalability, monetisation and policy risk (bots are fine; never claim "real players").

## 8. Deliver
- Send the producer **one image** (the latest board) plus a short summary:
  - the scores per persona, v1 → v2;
  - the publisher verdict;
  - the hook;
  - the cut list;
  - the build gates by day.
- Keep everything in one folder: `DESIGN*.md`, `board*.png`, `review-v*/`. Don't publish it anywhere unless
  asked.
- Then the build starts from the MUST list (the **make-web-game** loop: vertical slice first).

## References
- `references/player-panel.md`: the personas, the exact question lists, how to read the panel and when to stop.
- `references/wordless-ui.md`: diegetic signals that work, the ones that failed, and how to verify them.
- `references/publisher-lens.md`: USPs, market, pillars, scope, test thresholds, scalability, verdict.
- `references/example-graft.md`: a full run of this skill (a 3-day prototype), with the scores and what changed.
- `assets/DESIGN.template.md`, `assets/board-flow.html`.
