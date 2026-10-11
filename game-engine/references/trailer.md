# Trailer pipeline

## Structure (25–32 s vertical)
1. **Hook, 0–3 s:** the most spectacular in-game moment (a giant boss's glare and stomp) plus one caption that works without sound ("8,000 ZOMBIES. ONE FORT.").
2. **The loop by about 8 s:** a finger taps an upgrade → guns fire faster → the horde melts. Show what the player *does*.
3. **Escalation,** one idea per shot: horde → giants or mini-bosses → gacha reveal → new towers → crowd answer (pierce) → skill (blade) → titan slam.
4. **Hero finale:** the big boss's death up close (collapse + slow motion) → the chapter-clear celebration → logo + PLAY FREE end card, held while the music fades. Never end on a cluttered wide shot.

## Capture
- Scripted takes against the real build (`takes/*.mjs`) with debug hooks to stage moments; parallel shooters on separate ports.
- **Smooth motion:** one simulation step per captured frame; 60 fps for normal speed, 120–240 fps for half or quarter-speed slow motion. Check with a duplicate-frame scan (`scripts/dupframes.sh`): only the logo hold may repeat.
- Lower camera angles and fewer enemies in close shots; eased push-ins and dollies instead of static frames.

## Edit
- A beat-locked EDL (`edl.json`: clip, in, beats, speed, title) on the music's BPM grid; cuts within about 16 ms of the beat. Vary shot lengths (not every shot 2 beats).
- Titles inside vertical safe zones (clear of TikTok and Reels UI), on screen at least 0.6 s.
- Make a 16:9 version by reframing (battle shots recomposed; UI shots as a phone panel + close-up), not by cropping.

## Sound
- The game's own SFX mixed under the music (roars, slams, coins, kill crunches, celebration sting), ducking the music 3–10 dB on impacts. Integrated about -15 LUFS for social, true peak ≤ -1.5 dB (`scripts/loudness.sh`).
- The agent can't listen. Say so, and give the human the file plus a waveform chart.

## Review scorecard (score each out of 10)
Hook · clarity of the loop · one idea per shot · escalation and arc · pacing and rhythm · VFX polish · motion smoothness · sound design and sync · platform fit · brand and call to action. Below 7 on clarity or finale: recut before sharing.
