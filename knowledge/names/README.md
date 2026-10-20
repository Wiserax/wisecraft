# Gamer nicknames for bots

`gamer-nicknames.txt`: 363 invented nicknames, one per line, for bots, fake lobbies, kill feeds and leaderboard
filler. They read like real players from chat-board and online-game culture: numbers, `xX_..._Xx`, leetspeak,
memes, and some in Russian, Chinese and Korean. Written for a roguelike lobby game on 2026-10-20.

- Mostly ASCII; 25 lines use Cyrillic, CJK or Hangul. Check that the game font has those glyphs, or filter
  them out with `grep -v '[^ -~]'`.
- A few are themed on animals and body parts (crabs, snakes, slime, stitched-on parts). Drop them when they
  don't fit the game.
- Three were left out of the copy because store review or a chat filter could flag them (a self-harm meme,
  a drug number, a string a hate-speech filter matches). Keep it that way: no slurs, sexual content,
  self-harm, drugs or real people.
- Pick at random without repeats inside one lobby, and add a number suffix when a game needs more than 363.
