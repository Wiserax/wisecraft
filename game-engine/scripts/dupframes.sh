#!/usr/bin/env bash
# Count near-duplicate frames in a video (stutter check for slow motion). Usage: dupframes.sh video.mp4
set -euo pipefail
v="$1"
total=$(ffprobe -v error -select_streams v -count_frames -show_entries stream=nb_read_frames -of csv=p=0 "$v")
kept=$(ffmpeg -hide_banner -i "$v" -vf "mpdecimate=hi=768:lo=320:frac=0.33,showinfo" -an -f null - 2>&1 | grep -c "Parsed_showinfo.* n:" || true)
echo "frames: $total  unique: $kept  near-duplicates: $((total - kept))"
echo "Only a deliberate logo/end-card hold should account for near-duplicates."
