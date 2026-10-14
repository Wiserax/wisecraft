# The player panel: test a design with personas before building it

A design that one person likes is a guess. Run it past a panel of players who would actually meet the game,
and a publisher who decides whether it ships. Each reviewer is a separate subagent: they don't see each other's
answers, so they don't converge on the first opinion.

## The default panel (4 personas in 3 reviewers)
| Reviewer | Personas | What they catch |
|---|---|---|
| Hardcore + midcore | **Hardcore:** 3+ h/day, the genre's top games for 1,000+ h; hates fake depth and pay-to-win. **Midcore:** 45 min/day on a commute, one hand, quits if confused for 30 s | shallow builds, dead time, unbelievable bots, balance between classes |
| Casual + non-reader | **Casual:** match-3 / runner player, 15-minute sessions, never reads tutorials, decides in 60 s. **Non-reader:** a 9-year-old or a foreign-language market; pictures, colours and motion only | every wordless signal that fails, the first 60 seconds, fear points |
| Publisher | The green-light meeting: USPs, market, pillars, scope for the deadline, the test hypothesis, scalability, risks, verdict | over-scope, me-too features, unmeasurable tests, store-policy risk |

Swap personas when the genre needs it (an idle game wants an "AFK optimiser", a puzzle game a "daily
puzzler"). Keep at least one player who reads nothing.

## What every reviewer gets
- The **board PNG** (they must look at it; say so in the prompt), DESIGN.md, and any real engine frames, so
  they judge the look we can build, not the concept art.
- The constraints, stated plainly: team size, deadline, no real multiplayer, web build, wordless.
- A **fixed question list** and an output path: `review-vN/REVIEW-<group>.md`, under 900 words, writing
  nothing else.

## The question lists

### Players (hardcore and midcore), per persona, first person, no politeness
1. The 5-second read: from the board alone, what is this game and what do you do in a session?
2. Confusion: the screens or icons you don't understand (by number), and your guess at them.
3. The core loop: is it fun? Where's the dead time? Is the session length right?
4. Depth: is it enough build-crafting for the genre? Is the twist meaningful or cosmetic?
5. Bots or opponents: are they believable? What breaks the illusion?
6. Class balance (e.g. ranged vs melee): what do you expect?
7. Would you play D1 / D7? Rate 1-10, and why.
8. Your top 3 concrete changes.
Then combined: agreements, disagreements, and the 5 highest-impact fixes ranked, with screen numbers.

### Players (casual and non-reader)
1. Pictures only (ignore the captions): walk every screen; for each, say UNDERSTOOD / GUESSED / LOST, and what
   you'd tap.
2. Rate every diegetic signal in the design's table: clear / unclear / wrong guess.
3. The first 60 seconds: would you keep playing? The first moment of fun or confusion?
4. Fear points: where you'd quit or feel stupid.
5. Would you play again tomorrow? Rate 1-10.
6. Your top 3 concrete changes.
Then combined: the signals that need fixing, ranked, each with a concrete wordless alternative.

### Publisher
1. The 3 strongest USPs, ranked, each as a one-line ad hook; the 3-second ad.
2. The market: closest competitors; what's differentiated and what's me-too.
3. The 3 pillars to nail; what is NOT a pillar (cut it).
4. Scope for the deadline: MUST / SHOULD / LATER; the smallest build that tests the hypothesis.
5. The test hypothesis, the events to log, and go/kill thresholds (D1, session length, runs per user).
6. Scalability: the content cadence, what makes it live, monetisation and store-policy risk.
7. Risks, ranked, with mitigations.
8. The verdict: green-light / green-light with changes / kill.

## Reading the panel
- **Count agreements, not volume.** A fix that 3 reviewers ask for is a must; one loud voice is a maybe.
- **The non-reader decides the UI.** If a signal is LOST for them, it changes, whatever the others say.
- **The publisher decides the scope.** Their MUST list is the build plan unless the producer overrides it.
- **Players decide the fun.** If two personas name the same dead time, cut it.
- Write `review-vN/SYNTHESIS.md`: the ranked fixes, who asked for each, and what v(N+1) changes. Then re-run
  the panel on v(N+1) with the same prompts plus "here is what changed; did it fix your issues?". Stop when no
  reviewer has a LOST screen and the publisher says green-light; usually 2 rounds.
