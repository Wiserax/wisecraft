# Shot list: <game, described neutrally>, <length> s <vertical | 16:9>

- **Sells:** <one sentence, e.g. "8,000 enemies, one fort, your taps.">
- **Build:** <version + commit, a frozen checkout>
- **Output:** <1080x1920 | 1920x1080>, <30 | 60> fps
- **Music:** <title, artist>, <BPM> BPM, first beat at <s> s, licence: <where it is kept>
- **Cutdowns:** <15 s? 16:9? square?>

Take fps = output fps / speed. Game time = output seconds x speed (+ about 0.5 s handles each side).

| # | Beats | Moment (3 words) | Staging (debug calls, pins, forced rolls) | Camera (move, from, to) | Speed | Take fps | Game time (s) | Words (hook / title) | Aspect | Take file |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 4 | hook: | | | 0.5 | | | | both | takes/01-hook.mp4 |
| 2 | 3 | loop: player taps | | | 1 | | | | both | |
| 3 | 2 | loop: payoff | | | 1 | | | | both | |
| 4 | | escalation: | | | | | | | | |
| 5 | | escalation: | | | | | | | | |
| 6 | | escalation: | | | | | | | | |
| 7 | | escalation: | | | | | | | | |
| 8 | 8 | finale: close | | | 0.25 | | | | both | |
| 9 | 4 | celebration | | | 1 | | | | both | |
| 10 | 8 | end card (logo + PLAY FREE), held | - | - | - | - | - | PLAY FREE | both | card |

## Checks before capture
- [ ] The hook is the most spectacular moment, not a logo or a menu
- [ ] The player's action is on screen by 8 s
- [ ] Each shot names one idea; each is bigger than the last
- [ ] The finale is a close shot, and the longest
- [ ] In-game slow motion and hit-stops off for takes
- [ ] 16:9 shots planned as their own takes, not crops
- [ ] Words fit one line and stay out of the platform overlay zones

## NOTES (fill in during capture)
- Staged vs played, per shot:
- Forced rolls / pinned values:
- Known weak spots:
- Not checked: nobody has watched it in motion or heard it.
