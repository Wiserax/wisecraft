# UI kit (mobile portrait)

## Hub
- **The scene is the screen:** the fort or base fills the hub. Top bar: rank ring, soft and premium currency pills (short numbers 12.6K), **EN | ES** switch, settings gear.
- **Bottom nav, at most 5 tabs:** Shop · Workshop · Battle · Towers · Armory. Locked tabs show a padlock, not an empty slot.
- **Side rails, 3 left and 3 right:** Daily login, Pass, Challenges | Vault, Events, Race. Each has an icon plus a tiny label or timer (CLAIM!, 22d 1h). A red dot shows only when something is claimable. Locked features are visible but greyed, never hidden, or players never discover them.
- **One golden call to action at a time,** by priority: tutorial step → free vault open → gift → ready build → PLAY. Everything else is a quiet dot.
- Chapter card with a looping preview of the next chapter (lazy-loaded muted `<video playsinline>` + a poster), and a Chapters sheet with all chapters (▶ Preview for locked ones).

## Battle HUD
- **One slim row (~36 px):** stage + wave progress, gold, the **1×/2× speed** button, mute, pause. Everything else goes in the pause menu. Event chips show for 5 s, then fade.
- Skills (blade, overcharge) are optional: icons that fill, no nagging pulses or "use me" prompts. Overcharge: a liquid-electric bubble with an icon and no text.
- **Pixel-font chat log** (Silkscreen) instead of toasts: "TITAN FELLED · WALLS REPAIRED".
- Upgrade dock: 2 full rows visible at 320×568; tap to buy, hold for details; ×1/×5/MAX. Pin the key crowd answer (pierce) first once unlocked.

## Wordless FTUE
- Gold rings, a tapping hand and one-word chips (FREE, BUILD). No paragraphs, so non-native speakers can play.
- The first ring never sits on the player's own base; point at the field until an enemy arrives.
- Teach a new rule the first time it fires, with one golden diegetic cue in the world.

## Result and celebration screens
- Icons + numbers + one short line: "879 🪙 +25% · Next: stage 7". The primary button says what it does (NEXT STAGE / NEXT CHAPTER, never "Defend again" after a win).
- Chapter clear: slow motion → flash → fireworks and confetti → medallion turns gold → stars land → rewards fly to the wallet → the next chapter card slides up. **Pay rewards the instant the run ends**; only the show waits (a reload mid-celebration must not lose or double them).

## Fonts and tokens
- Lilita One (display, buttons), DM Sans (body), Silkscreen (pixel log). Load from Google Fonts or self-host the OFL files.
- Gold primary (#ffe27a → #f2a91a), green go (#7ee05a → #3fae2f), purple premium (#b27aff → #7b3fd6), night background (#150d22 / #20152f).
- Rarity colours: common #9fb3a6, rare #4aa8ff, epic #b46cff, legendary #ffc531, cursed #ff3d5a.

## i18n (EN/ES)
- The keys are the English text; Spanish runs about 25% longer, so let tight buttons shrink or wrap.
- Spanish numbers: `1.234`, percentages with a non-breaking space (`25 %`). Singular and plural forms everywhere ("+1 gema").
- Check every new screen at 390 and 320 in both languages, and in WebKit.

## Anti-patterns we removed
- 8 things pulsing at once after the first session.
- A notice covering the top bar for 6 s.
- "10 TOWERS!" over a single card.
- Text-heavy result cards.
- Empty hubs that hide every feature behind dots.
