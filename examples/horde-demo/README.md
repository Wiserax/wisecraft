# Horde demo

A deliberately unfinished horde defense: about 200 lines of Vite + three.js. It is the sample game the Wisecraft
docs and benchmark run on, and a small place to try the skills.

```bash
npm install
npm test          # the sim's rules, in node
npm run dev       # http://127.0.0.1:5173
```

What it has: a fort, one turret, enemies that walk in from the rim, taps that hit a small area, ten waves, a
seeded simulation with no browser code in it (`src/sim.js`), a debug hook (`window.__game`), one analytics call
per wave to `/api/events`.

What is wrong with it, on purpose:
- the first stage is boring and far too easy: four enemies a wave, and the walls never take a hit;
- there is no boss;
- nothing is ready for a release: no version shown, no build check, no README for players.

Those are the three benchmark tasks (`benchmarks/`). Keep the sim's public API (`createSim`, `step`, `tap`,
`state`, `on`) when you change it: the scripted checks call it.
