#!/usr/bin/env bash
# Integrated loudness, range and true peak (EBU R128) without playing audio. Fallback for `wise loudness`.
# Usage: loudness.sh file.(mp4|wav|mp3)   (needs ffmpeg)
set -euo pipefail
ffmpeg -nostats -hide_banner -i "$1" -af ebur128=peak=true -f null - 2>&1 | sed -n '/Summary:/,$p'
echo "Targets: trailer/social ~ -15 LUFS integrated, true peak <= -1.5 dBTP; in-game music ~ -20 LUFS short-term, SFX <= music + 6 dB."
