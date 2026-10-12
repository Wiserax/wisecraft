# Progression, the curve across sessions, and retention

Balance answers "is this stage fair". Meta answers "why come back tomorrow, and does the game still feel fair
on day 7". The inner curve (waves inside a stage) belongs to the **game-balance** skill; this file is the
curve across stages, sessions and days, and the loops around it.

## 1. The curve across sessions
- **Across a chapter: a rising sawtooth.** Ten stages rising to stage 10, the hardest. Boss stages are local
  peaks with a breather after. A finale easier than stage 5 is a bug.
- **Across chapters: dip, then climb.** A new chapter opens a little easier than the last one ended, with
  one new mechanic or enemy, then climbs past it.
- **Walls are measured in tries.** The difficulty index counts tries per stage (capped at 5) per player-model
  bot. Targets that worked: a casual human needs at most 4-6 tries on any stage; a novice falls a few times
  per chapter; nobody needs the cap twice in a row. Two caps in a row is a wall: the player quits there.
- **A soft gate is a wall with an answer.** The answer comes from the meta: a soft-currency upgrade, a new
  tower from the vault, the rescue gift. Size it so a free player gets through in one or two sessions of
  play. If the only answer is money, it is a paywall.
- **Time to the next goal stays short.** In any session there is always something about to happen: the next
  upgrade (minutes), the next pass tier or chest (a session), the next chapter or tower (days). Plot all
  three against play time.

## 2. Rescue gifts: only after a fall
From the note
[rescue gifts only after a fall, and never over a win screen](../../../knowledge/games/horde-tower-defense-mobile-web/rescue-gifts-only-after-a-fall-and-never-over-a-win-screen.md):
- **A gift needs a fall.** Triggers on playtime ("8 minutes and no gift yet") and on an empty shop fired for
  the best players, made the game feel easy and cheapened the rescue.
- **It follows the stage being fought.** Resolve the stage when the chest is opened, not when it was offered;
  a chest opened late blessed a stage the player had already passed.
- **Nothing opens over a win.** A chest waiting at a chapter win moves to the next chapter's first stage.
- **A blessing helps; it does not win.** In early simulations 63 of 63 blessed runs cleared their stage. The
  blessing that shipped is ×1.5 damage and ×1.75 walls; the passive bot's blessed retry still wins with
  90-94 % walls (generous, and said so).
- **A used blessing must not block later offers;** an unused one waits. A pending blessing that blocked
  offers produced walls of 14-24 falls in later chapters in simulation.
- **Keep the cooldown short** (3 minutes of battle). A 20-minute cooldown became the pace of the game.
- **Tie it to the curve.** The welcome gift unlocks at 1.25 minutes of battle, just before the first stage's
  mini-boss, so a player who buys nothing falls there and is offered it. Move one, check the other.

## 3. Rewards: paid the instant the run ends
From the note
[pay rewards the instant the run ends; the celebration only presents them](../../../knowledge/games/horde-tower-defense-mobile-web/pay-rewards-the-instant-the-run-ends-the-celebration-only-pr.md):
- Settle the profile on the frame the run ends, keyed on the run's id; clear the resumable run in the same
  write. Everything after (slow motion, fireworks, the wallet count-up) only presents numbers already paid.
- Settling the same run twice returns "duplicate" and pays nothing. Test it, including across a save round
  trip (a reload).
- The same rule covers every grant: gacha opens, offer purchases, pass claims, daily rewards. Double taps and
  reloads are tested in a real browser (the **game-qa** skill).

## 4. Traps in progression design (each cost a day)
- **Checkpoints must not keep the whole run build.** A checkpoint that restores every upgrade turns the rest
  of the chapter into a walk. Restore the stage, not the build, or a reduced build.
- **"Push on" is a trap unless the payoff is real.** Run the bots through "continue right after a clear" and
  check they can win it. If they can't, the button is a way to lose.
- **Progression paid in soft currency pulls chapters forward** (see `currencies-and-sinks.md`).
- **Longer waves pay more per stage,** so the chapter gets shorter. Hold gold per stage when you stretch time.

## 5. Retention loops
| Loop | Length | Examples | Rule |
|---|---|---|---|
| Core | one run (about 3 min) | fight → reward → upgrade → next fight | a reward and a choice every run |
| Session | 10-20 min | the next stage, a chest that opens after 3 wins | end the session on something to look forward to |
| Daily | 1 day | daily goals, a free gacha open, a login calendar | about 10 minutes of play covers the dailies |
| Weekly | 7 days | weekly quests, a weekend event | completable in 4-5 play days |
| Season | 4-5 weeks | the pass, an event chapter | see `shop-offers-and-pass.md` |
| Long | months | collection, chapters, star-ups | a visible long goal from week 1 |

**Streaks without punishment.** A login calendar advances on days played, not calendar days, so one missed
day doesn't reset a week. Offer one streak freeze a week. A comeback bonus after 7+ days away (free, then an
optional pack) brings players back; a streak that resets drives them away for good.

## 6. The first session and the first week
| When | What must have happened |
|---|---|
| 0-5 s | the player is playing, not reading; the first card is affordable within about 5 s |
| 1-3 min | the first upgrade was felt; the first mini-boss; something new every 5 s |
| end of session 1 | first stage cleared; a chest or the first vault open (free); a reason to return tomorrow |
| day 1 | dailies introduced; the first fall and the rescue gift for players who struggle |
| day 2 | the free daily open; a new tower or mechanic |
| day 3-7 | the first chapter clear; the pass shown with its first free rewards already earned; the first weekend event |

## 7. Metrics and rough ranges
Read the game's own history first: a game's previous month is a better benchmark than any industry figure.
The ranges below are **rough, commonly quoted figures for casual free-to-play mobile games**; they vary a lot
by genre, platform, traffic source and year, and web games often sit lower on D1. Use them only to notice
when a number is far off.

| Metric | Rough healthy range | First thing to check when it's low |
|---|---|---|
| D1 retention | 30-45 % | the first session (boot time, the tutorial, the first fall) |
| D7 retention | 10-20 % | the first wall; dailies; the chapter-1 curve |
| D30 retention | 3-8 % | long goals, events, content runway |
| Payer conversion | 1-5 % of players | starter pack timing and value |
| Session length | 5-15 min | stage length, the session loop |
| Sessions a day | 2-4 | dailies, timers, a reason to return |

**"Players quit on day 2."** Split D1 retention by what happened in session 1: cleared stage 1 or not, fell
or not, got the gift or not, opened the vault or not. The group that leaves points at the cause. Then check
the funnel (boot → first fight → first clear → hub → second fight) for the step where most players drop.
