#!/usr/bin/env python3
"""Convert timestamp text files to JSON format."""

import json
import re
from pathlib import Path

# Internal configuration
INPUT_FOLDER = Path(__file__).parent / "old_strems"
OUTPUT_FOLDER = Path(__file__).parent / "tim-tams-viewer/public/data/streams"

# Pattern for "events": uppercase letters, spaces, and hyphens, ending with " -"
# e.g. "F R A N K - M O V E S -", "C R A Z Y - B U S -", "L A P - O N E - O F - T H E - B I N -"
EVENT_PATTERN = re.compile(r"^[A-Z][A-Z -]* -$")


def parse_timestamp_file(filepath: Path) -> tuple[dict, list[str]]:
    """Parse a single timestamp file and return its data as a dictionary.

    Returns:
        A tuple of (data dict, list of warning messages).
    """
    content = filepath.read_text(encoding="utf-8")
    warnings: list[str] = []

    # Extract date and time from the header comment
    header_match = re.search(
        r"# Timestamps started:\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})",
        content,
    )
    if not header_match:
        raise ValueError(f"Could not find header in {filepath}")

    date_str = header_match.group(1)
    time_str = header_match.group(2)

    songs = []
    events = []

    # Match lines like: 00:05:30 - Artist, Song Title
    song_pattern = re.compile(r"^(\d{2}:\d{2}:\d{2})\s+-\s+(.+)$", re.MULTILINE)

    # Also track all non-empty, non-comment lines to detect unparseable ones
    all_lines = re.findall(r"^[^\s#].*$", content, re.MULTILINE)
    parsed_times = set()

    for match in song_pattern.finditer(content):
        song_time = match.group(1)
        artist_song = match.group(2).strip()
        parsed_times.add(song_time)

        # Check if this is an "event" (no comma, uppercase spaced pattern)
        if not re.search(r",", artist_song) and EVENT_PATTERN.fullmatch(artist_song):
            events.append({
                "time": song_time,
                "name": artist_song,
            })
            continue

        # Split on the first comma to separate artist and song title
        parts = artist_song.split(",", 1)
        artist = parts[0].strip()
        song_title = parts[1].strip() if len(parts) > 1 else ""

        # Warn if artist or song_title is empty
        if not artist:
            warnings.append(
                f"Line '{song_time} - {artist_song}': artist is empty"
            )
        if not song_title:
            warnings.append(
                f"Line '{song_time} - {artist_song}': song title is empty"
            )

        songs.append(
            {
                "time": song_time,
                "artist": artist,
                "song_title": song_title,
            }
        )

    # Detect unparseable lines (non-empty, non-comment lines that weren't matched)
    for line in all_lines:
        line_time_match = re.match(r"^(\d{2}:\d{2}:\d{2})\s+-", line)
        if line_time_match:
            line_time = line_time_match.group(1)
            if line_time not in parsed_times:
                warnings.append(f"Unparseable line: '{line}'")

    if not songs and not events:
        warnings.append(f"No songs or events found in {filepath.name}")

    return {
        "date": date_str,
        "time": time_str,
        "songs": songs,
        "events": events,
    }, warnings


def convert_file(input_path: Path) -> None:
    """Convert a single timestamp file to JSON and write to output folder."""
    data, warnings = parse_timestamp_file(input_path)

    # Print warnings before the success message
    for warning in warnings:
        print(f"  ⚠️  Warning ({input_path.name}): {warning}")

    # Generate output filename: timestamps_YYYY-MM-DD_HH-MM-SS.json
    output_filename = (
        f"timestamps_{data['date']}_{data['time'].replace(':', '-')}.json"
    )
    output_path = OUTPUT_FOLDER / output_filename

    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"  ✅ Converted: {input_path.name} -> {output_path.name}")


def main() -> None:
    """Find all timestamp files in the input folder and convert them."""
    if not INPUT_FOLDER.exists():
        print(f"Error: Input folder does not exist: {INPUT_FOLDER}")
        return

    timestamp_files = sorted(INPUT_FOLDER.glob("timestamps_*.txt"))

    if not timestamp_files:
        print(f"No timestamp files found in {INPUT_FOLDER}")
        return

    print(f"Found {len(timestamp_files)} timestamp file(s)\n")

    total_warnings = 0

    for filepath in timestamp_files:
        try:
            convert_file(filepath)
        except Exception as e:
            print(f"  ❌ Error processing {filepath.name}: {e}")
            total_warnings += 1

    if total_warnings > 0:
        print(f"\n⚠️  {total_warnings} file(s) had errors.")

    print(f"\nDone! Output saved to: {OUTPUT_FOLDER}")


if __name__ == "__main__":
    main()
