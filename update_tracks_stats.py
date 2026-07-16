#!/usr/bin/env python3
"""Update tracks.json with statistics computed from all stream JSON files."""

import json
from collections import defaultdict
from pathlib import Path

STREAMS_FOLDER = Path(__file__).parent / "tim-tams-viewer/public/data/streams"
TRACKS_FILE = Path(__file__).parent / "tim-tams-viewer/public/data/tracks.json"


def main() -> None:
    if not STREAMS_FOLDER.exists():
        print(f"Error: Streams folder does not exist: {STREAMS_FOLDER}")
        return

    if not TRACKS_FILE.exists():
        print(f"Error: Tracks file does not exist: {TRACKS_FILE}")
        return

    # Load existing tracks
    tracks_data = json.loads(TRACKS_FILE.read_text(encoding="utf-8"))
    tracks = tracks_data["tracks"]

    # Build a lookup: (artist, song_title) -> index in tracks list
    track_lookup: dict[tuple[str, str], int] = {}
    for i, track in enumerate(tracks):
        key = (track["artist"].lower(), track["title"].lower())
        track_lookup[key] = i

    # Also build an alias lookup: (alias_artist, alias_title) -> index
    # Aliases are stored as "{artist}, {song_title}" in a single string,
    # so we split them into separate keys for lookup.
    alias_lookup: dict[tuple[str, str], int] = {}
    for i, track in enumerate(tracks):
        for alias in track.get("aliases", []):
            # Split alias on the first comma to get alias artist and title
            parts = alias.split(",", 1)
            if len(parts) == 2:
                alias_artist = parts[0].strip().lower()
                alias_title = parts[1].strip().lower()
                alias_lookup[(alias_artist, alias_title)] = i

    def find_track_index(artist: str, title: str) -> int | None:
        """Find the index of a track by artist and title, checking aliases."""
        key = (artist.lower(), title.lower())
        if key in track_lookup:
            return track_lookup[key]
        if key in alias_lookup:
            return alias_lookup[key]
        return None

    # Accumulate stats across all stream files
    # track_index -> {count, last_date, date_counts: {date: count}}
    track_stats: dict[int, dict] = defaultdict(lambda: {
        "count": 0,
        "last_date": "",
        "date_counts": defaultdict(int),
    })

    stream_files = sorted(STREAMS_FOLDER.glob("timestamps_*.json"))
    print(f"Processing {len(stream_files)} stream file(s)...\n")

    for stream_file in stream_files:
        content = stream_file.read_text(encoding="utf-8")
        stream_data = json.loads(content)
        date = stream_data["date"]

        for song in stream_data.get("songs", []):
            artist = song.get("artist", "")
            title = song.get("song_title", "")

            if not artist or not title:
                continue

            idx = find_track_index(artist, title)
            if idx is not None:
                stats = track_stats[idx]
                stats["count"] += 1
                stats["date_counts"][date] += 1
                if date > stats["last_date"]:
                    stats["last_date"] = date
            else:
                print(
                    f"  ⚠️  Warning ({stream_file.name}): "
                    f"'{artist} / {title}' not found in tracks.json"
                )

    # Update tracks with computed stats
    updated_count = 0
    for idx, stats in track_stats.items():
        track = tracks[idx]
        total = stats["count"]
        last_date = stats["last_date"]

        # Find date with most reproductions
        date_counts = stats["date_counts"]
        if date_counts:
            best_date = max(date_counts, key=date_counts.get)
            best_count = date_counts[best_date]
        else:
            best_date = ""
            best_count = 0

        track["number_of_times_played"] = total
        track["last_time_played"] = last_date
        track["date_with_most_reproductions"] = best_date
        track["most_reproductions_record"] = best_count
        updated_count += 1

    # Write back
    TRACKS_FILE.write_text(
        json.dumps(tracks_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Updated {updated_count} track(s) with statistics.")
    print(f"Output saved to: {TRACKS_FILE}")


if __name__ == "__main__":
    main()
