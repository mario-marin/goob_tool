#!/usr/bin/env python3
"""Add bin / youtube-friendly statistics to each stream timestamps JSON file."""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

STREAMS_FOLDER = Path(__file__).parent / "tim-tams-viewer/public/data/streams"
TRACKS_FILE = Path(__file__).parent / "tim-tams-viewer/public/data/tracks.json"
STATISTICS_FILE = Path(__file__).parent / "tim-tams-viewer/public/data/statistics.json"


def main() -> None:
    if not STREAMS_FOLDER.exists():
        print(f"Error: Streams folder does not exist: {STREAMS_FOLDER}")
        return

    if not TRACKS_FILE.exists():
        print(f"Error: Tracks file does not exist: {TRACKS_FILE}")
        return

    # Load tracks and build lookup tables
    tracks_data = json.loads(TRACKS_FILE.read_text(encoding="utf-8"))
    tracks = tracks_data["tracks"]

    # (artist_lower, title_lower) -> track dict
    track_lookup: dict[tuple[str, str], dict] = {}
    for track in tracks:
        key = (track["artist"].lower(), track["title"].lower())
        track_lookup[key] = track

    # alias lookup: (alias_artist_lower, alias_title_lower) -> track dict
    alias_lookup: dict[tuple[str, str], dict] = {}
    for track in tracks:
        for alias in track.get("aliases", []):
            parts = alias.split(",", 1)
            if len(parts) == 2:
                alias_artist = parts[0].strip().lower()
                alias_title = parts[1].strip().lower()
                alias_lookup[(alias_artist, alias_title)] = track

    def find_track(artist: str, title: str) -> dict | None:
        """Find a track by artist and title, checking aliases."""
        key = (artist.lower(), title.lower())
        if key in track_lookup:
            return track_lookup[key]
        if key in alias_lookup:
            return alias_lookup[key]
        return None

    # Process each stream file
    stream_files = sorted(STREAMS_FOLDER.glob("timestamps_*.json"))
    print(f"Processing {len(stream_files)} stream file(s)...\n")

    # Collect per-stream stats for the aggregated statistics.json
    stream_stats: list[dict] = []

    for stream_file in stream_files:
        content = stream_file.read_text(encoding="utf-8")
        stream_data = json.loads(content)

        bin_count = 0
        youtube_friendly_count = 0
        unmatched = []

        for song in stream_data.get("songs", []):
            artist = song.get("artist", "")
            title = song.get("song_title", "")

            if not artist or not title:
                continue

            track = find_track(artist, title)
            if track is not None:
                is_bin = track.get("hidden", {}).get("is_bin", False)
                ignore_stats = track.get("hidden", {}).get("ignore_stats", False)
                if ignore_stats:
                    continue
                if is_bin:
                    bin_count += 1
                else:
                    youtube_friendly_count += 1
            else:
                unmatched.append((artist, title))

        # Write stats back into the stream file
        stream_data["statistics"] = {
            "bin_songs": bin_count,
            "youtube_friendly": youtube_friendly_count,
        }

        if unmatched:
            stream_data["statistics"]["unmatched"] = [
                {"artist": a, "title": t} for a, t in unmatched
            ]

        stream_file.write_text(
            json.dumps(stream_data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        print(
            f"  {stream_file.name}: "
            f"{bin_count} bin, {youtube_friendly_count} youtube-friendly"
        )
        if unmatched:
            print(f"    ⚠️  {len(unmatched)} unmatched song(s)")

        # Collect stats for aggregated file
        stream_stats.append({
            "date": stream_data.get("date", ""),
            "time": stream_data.get("time", ""),
            "bin_songs": bin_count,
            "youtube_friendly": youtube_friendly_count,
        })

    # Build day-of-week averages
    day_totals: dict[str, dict[str, list]] = defaultdict(
        lambda: {"bin_songs": [], "youtube_friendly": []}
    )
    for entry in stream_stats:
        date_str = entry.get("date", "")
        if not date_str:
            continue
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            day_name = dt.strftime("%A")
        except ValueError:
            continue
        day_totals[day_name]["bin_songs"].append(entry["bin_songs"])
        day_totals[day_name]["youtube_friendly"].append(entry["youtube_friendly"])

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    day_of_week: list[dict] = []
    for day_name in day_order:
        totals = day_totals.get(day_name, {"bin_songs": [], "youtube_friendly": []})
        bin_list = totals["bin_songs"]
        yf_list = totals["youtube_friendly"]
        count = len(bin_list)
        if count > 0:
            day_of_week.append({
                "day": day_name,
                "bin_songs": round(sum(bin_list) / count, 2),
                "youtube_friendly": round(sum(yf_list) / count, 2),
                "streams": count,
            })

    # Build time-of-day averages (morning vs evening)
    tod_totals: dict[str, dict[str, list]] = defaultdict(
        lambda: {"bin_songs": [], "youtube_friendly": []}
    )
    for entry in stream_stats:
        time_str = entry.get("time", "")
        if not time_str:
            continue
        try:
            dt = datetime.strptime(time_str, "%H:%M:%S")
            hour = dt.hour
            period = "morning" if hour < 12 else "evening"
        except ValueError:
            continue
        tod_totals[period]["bin_songs"].append(entry["bin_songs"])
        tod_totals[period]["youtube_friendly"].append(entry["youtube_friendly"])

    tod_order = ["morning", "evening"]
    time_of_day: list[dict] = []
    for period in tod_order:
        totals = tod_totals.get(period, {"bin_songs": [], "youtube_friendly": []})
        bin_list = totals["bin_songs"]
        yf_list = totals["youtube_friendly"]
        count = len(bin_list)
        if count > 0:
            time_of_day.append({
                "period": period,
                "bin_songs": round(sum(bin_list) / count, 2),
                "youtube_friendly": round(sum(yf_list) / count, 2),
                "streams": count,
            })

    # Build aggregated statistics.json
    statistics_output = {
        "histograph": stream_stats,
        "sorted_histograph": sorted(
            stream_stats,
            key=lambda s: s["bin_songs"] + s["youtube_friendly"],
            reverse=True,
        ),
        "day_of_week": day_of_week,
        "time_of_day": time_of_day,
    }

    STATISTICS_FILE.write_text(
        json.dumps(statistics_output, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"\nDone. Updated {len(stream_files)} stream file(s).")
    print(f"  Wrote aggregated statistics to {STATISTICS_FILE}")


if __name__ == "__main__":
    main()
