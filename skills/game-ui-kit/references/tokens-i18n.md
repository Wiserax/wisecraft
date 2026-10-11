# Tokens and text rules

## Fonts
| Font | Use | Licence |
|---|---|---|
| Lilita One | display, buttons | SIL OFL |
| DM Sans | body | SIL OFL |
| Silkscreen | pixel chat log, tiny HUD labels | SIL OFL |

Load from Google Fonts or self-host the OFL files. Keep the licence text beside self-hosted files and name
the fonts in the credits.

## Colour tokens
| Token | Value | Use |
|---|---|---|
| Gold primary | `#ffe27a → #f2a91a` | the one golden call to action, claims |
| Green go | `#7ee05a → #3fae2f` | confirm, next, "after" frames on boards |
| Purple premium | `#b27aff → #7b3fd6` | premium currency, paid opens |
| Night background | `#150d22` / `#20152f` | panels, boards |

## Rarity colours
| Rarity | Value |
|---|---|
| common | `#9fb3a6` |
| rare | `#4aa8ff` |
| epic | `#b46cff` |
| legendary | `#ffc531` |
| cursed | `#ff3d5a` |

## i18n (EN/ES)
- **The keys are the English text.** A missing translation then shows English, not a key name.
- **Spanish runs about 25% longer,** so let tight buttons shrink or wrap.
- **Spanish numbers:** `1.234`, percentages with a non-breaking space (`25 %`).
- **Singular and plural forms everywhere** ("+1 gema").
- **Check every new screen at 390 and 320 in both languages, and in WebKit.** Spanish on a 320 px phone is
  the tightest case.
- Keep the **EN | ES** switch in the hub top bar. It dropped out of the hub once and needed its own release
  to come back.

## Motion tokens
The feel layer (taps, windows, claims, counters, tab crossfades) is global, not per screen. Its numbers live
in the **game-feel-audio** skill. A new screen gets them for free if it uses the shared button and modal
classes.
