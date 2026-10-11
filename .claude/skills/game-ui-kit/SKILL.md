---
name: game-ui-kit
description: A clean mobile-portrait UI kit for web games. Covers the hub (the scene is the screen, side rails, at most 5 tabs, one golden call to action at a time), a one-row battle bar, the upgrade dock, a wordless first-time tutorial, result and celebration screens, fonts (Lilita One, DM Sans, Silkscreen, all OFL), colour tokens, EN/ES text rules and the 320 px small-phone check. Use when the user says "the hub is cluttered", "too many things blink", "players do not find the feature", "make the tutorial without text", "add Spanish", "it breaks on small phones", "redo the HUD", or asks for any new screen, menu, popup or result card in a mobile web game.
---

# Game UI kit (mobile portrait)

One idea per screen. The player holds a phone in one hand and may not read English. Every rule below removed
something a real player tripped over.

Baseline 390×844; the small-phone check is 320×568. Build every screen in English and Spanish and look at it
in both sizes and in WebKit before calling it done (`wise qa`, the **browser-qa** skill). Show the result as a
board (`wise board`, the **design-boards** skill).

## Hub
- **The scene is the screen:** the fort or base fills the hub. Top bar: rank ring, soft and premium currency
  pills (short numbers 12.6K), **EN | ES** switch, settings gear.
- **Bottom nav, at most 5 tabs:** Shop · Workshop · Battle · Towers · Armory. Locked tabs show a padlock, not
  an empty slot.
- **Side rails, 3 left and 3 right:** Daily login, Pass, Challenges | Vault, Events, Race. Each has an icon
  plus a tiny label or timer (CLAIM!, 22d 1h). A red dot shows only when something is claimable. Locked
  features are visible but greyed, never hidden, or players never discover them.
- **One golden call to action at a time,** by priority: tutorial step → free vault open → gift → ready build
  → PLAY. Everything else is a quiet dot.
- **Chapter card** with a looping preview of the next chapter (lazy-loaded muted `<video playsinline>` + a
  poster), and a Chapters sheet with all chapters (▶ Preview for locked ones). Fetch only the next chapter's
  poster and clip on the hub; a 6 s loop at 640×360 without audio is about 600 KB.

## Battle HUD
- **One slim row (~36 px):** stage + wave progress, gold, the **1×/2× speed** button, mute, pause. Everything
  else goes in the pause menu. Event chips show for 5 s, then fade.
- **Skills** (blade, overcharge) are optional: icons that fill, no nagging pulses or "use me" prompts.
  Overcharge: a liquid-electric bubble with an icon and no text.
- **Pixel-font chat log** (Silkscreen) instead of toasts: "TITAN FELLED · WALLS REPAIRED".
- **Upgrade dock:** 2 full rows visible at 320×568; tap to buy, hold for details; ×1/×5/MAX. Pin the key
  crowd answer (pierce) first once unlocked.
- **Keep the field tappable.** A boss that walks in under the dock can't be seen or tapped; bring big
  enemies in from up the screen.

## Wordless FTUE
- Gold rings, a tapping hand and one-word chips (FREE, BUILD). No paragraphs, so non-native speakers can
  play.
- The first ring never sits on the player's own base; point at the field until an enemy arrives.
- Teach a new rule the first time it fires, with one golden diegetic cue in the world.

## Result and celebration screens
- Icons + numbers + one short line: "879 🪙 +25% · Next: stage 7". The primary button says what it does
  (NEXT STAGE / NEXT CHAPTER, never "Defend again" after a win).
- **Chapter clear:** slow motion → flash → fireworks and confetti → medallion turns gold → stars land →
  rewards fly to the wallet → the next chapter card slides up.
- **Pay rewards the instant the run ends;** only the show waits. A reload mid-celebration must not lose or
  double them. Ship that as a test.

## Fonts
- **Lilita One** (display, buttons), **DM Sans** (body), **Silkscreen** (pixel log, tiny HUD labels). All
  three are under the SIL Open Font License. Load from Google Fonts or self-host the OFL files.
- Treat fonts as optional at boot and time-box them: a slow font request must not hold the splash (the
  **game-performance** skill).

## One idea per screen
Hubs get rails for the important features (events, daily login, pass, vault, race), but only one glowing
call to action at a time.

## Anti-patterns we removed
- 8 things pulsing at once after the first session.
- A notice covering the top bar for 6 s.
- "10 TOWERS!" over a single card.
- Text-heavy result cards.
- Empty hubs that hide every feature behind dots.

## Done means
- One golden call to action on the hub; every rail and tab reachable.
- The battle bar is one row; the dock shows 2 full rows at 320×568.
- A fresh profile finishes the first session without reading a sentence.
- EN and ES at 390 and 320, Chromium and WebKit: `errors []`, no horizontal overflow, no clipped button text.
- A board with the screens, before/after where something changed.

## References
- `references/tokens-i18n.md`: the colour tokens, rarity colours and the EN/ES text rules (number formats,
  plurals, 25% longer strings). Read it when building a new screen or adding a language.
