#!/usr/bin/env python3
"""Convert timestamp text files to JSON format."""

import json
import re
from collections import defaultdict
from pathlib import Path

# Internal configuration
INPUT_FOLDER = Path(__file__).parent / "old_strems"
OUTPUT_FOLDER = Path(__file__).parent / "tim-tams-viewer/public/data/streams"
EVENTS_FILE = Path(__file__).parent / "tim-tams-viewer/public/data/events.json"

#INPUT_FOLDER = Path(__file__).parent / "test_old_strem"
#OUTPUT_FOLDER = Path(__file__).parent / "test_old_strem/json"

# Pattern for "events": uppercase letters, spaces, and hyphens, ending with " -"
# e.g. "F R A N K - M O V E S -", "C R A Z Y - B U S -", "L A P - O N E - O F - T H E - B I N -"
EVENT_PATTERN = re.compile(r"^[A-Z][A-Z -]* -$")

# Pattern for timestamp filenames: timestamps_YYYY-MM-DD_HH-MM-SS.txt
FILENAME_PATTERN = re.compile(
    r"^timestamps_(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})-(\d{2})\.txt$"
)


def _verify_filename(
    filepath: Path,
    header_date: str,
    header_time: str,
) -> str | None:
    """Verify that the filename matches the header date/time.

    Args:
        filepath: Path to the timestamp file.
        header_date: Date string from the file header (YYYY-MM-DD).
        header_time: Time string from the file header (HH:MM:SS).

    Returns:
        A warning message if the filename doesn't match, or None if it's valid.
    """
    match = FILENAME_PATTERN.match(filepath.name)
    if not match:
        return f"Filename '{filepath.name}' does not match expected pattern 'timestamps_YYYY-MM-DD_HH-MM-SS.txt'"

    file_date = match.group(1)
    file_hour = match.group(2)
    file_minute = match.group(3)
    file_second = match.group(4)
    file_time = f"{file_hour}:{file_minute}:{file_second}"

    if file_date != header_date or file_time != header_time:
        return (
            f"Filename date/time '{file_date} {file_time}' does not match "
            f"header date/time '{header_date} {header_time}'"
        )
    return None


def convert_file(
    input_path: Path,
    date_str: str,
    time_str: str,
    floatplane_link: str | None,
    all_events: dict[str, list[str]],
) -> tuple[list[str], set[str]]:
    """Convert a single timestamp file to JSON and write to output folder.

    Args:
        input_path: Path to the input timestamp file.
        date_str: The date string extracted from the file header.
        time_str: The time string extracted from the file header.
        floatplane_link: The Floatplane link from the header, or None if absent.
        all_events: Shared dict mapping event titles to lists of dates they appeared on.
                    Modified in-place to accumulate occurrences.

    Returns:
        A tuple of (warnings list, set of event titles seen in this file).
    """
    content = input_path.read_text(encoding="utf-8")
    warnings: list[str] = []

    songs = []
    events = []
    seen_events: set[str] = set()

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
            seen_events.add(artist_song)
            all_events.setdefault(artist_song, []).append(date_str)
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
        warnings.append(f"No songs or events found in {input_path.name}")

    # Generate output filename: timestamps_YYYY-MM-DD_HH-MM-SS.json
    output_filename = (
        f"timestamps_{date_str}_{time_str.replace(':', '-')}.json"
    )
    output_path = OUTPUT_FOLDER / output_filename

    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({
            "date": date_str,
            "time": time_str,
            "floatplane_link": floatplane_link,
            "songs": songs,
            "events": events,
        }, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"  ✅ Converted: {input_path.name} -> {output_path.name}")

    return warnings, seen_events


def _update_events_file(
    all_events: dict[str, list[str]],
) -> set[str]:
    """Update events.json with computed statistics from all processed files.

    For each event in events.json, compute:
    - number_of_ocurranses: total occurrences across all files
    - last_ocurrance: the most recent date the event appeared
    - date_with_most_ocurrances: the date with the highest count
    - most_ocurrances_on_a_date: the count on that date

    Events that were never seen in any timestamp file are left with their
    existing values (no change).

    Returns:
        Set of event titles that were found in the processed timestamp files.
    """
    # Load existing events.json
    if EVENTS_FILE.exists():
        events_data = json.loads(EVENTS_FILE.read_text(encoding="utf-8"))
    else:
        events_data = {"events": []}

    seen_titles: set[str] = set()

    for event in events_data["events"]:
        title = event["title"]
        seen_titles.add(title)

        if title in all_events:
            dates = all_events[title]
            total = len(dates)
            last = max(dates) if dates else ""

            # Find the date with the most occurrences
            date_counts: dict[str, int] = defaultdict(int)
            for d in dates:
                date_counts[d] += 1

            best_date = max(date_counts, key=date_counts.get) if date_counts else ""
            best_count = date_counts[best_date] if date_counts else 0

            event["number_of_ocurranses"] = total
            event["last_ocurrance"] = last
            event["date_with_most_ocurrances"] = best_date
            event["most_ocurrances_on_a_date"] = best_count

    # Write back
    EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    EVENTS_FILE.write_text(
        json.dumps(events_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return seen_titles


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

    # Shared accumulator: event_title -> [dates]
    all_events: dict[str, list[str]] = {}
    total_warnings = 0

    for filepath in timestamp_files:
        try:
            # Extract date from the file first (needed for output filename)
            content = filepath.read_text(encoding="utf-8")
            header_match = re.search(
                r"# Timestamps started:\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})",
                content,
            )
            if not header_match:
                raise ValueError(f"Could not find header in {filepath}")
            date_str = header_match.group(1)
            time_str = header_match.group(2)

            # Extract floatplane_link from header (only if it contains a URL)
            floatplane_match = re.search(
                r"^floatplane_link:\s*(https?://.+)$",
                content,
                re.MULTILINE,
            )
            if floatplane_match:
                floatplane_link = floatplane_match.group(1).strip()
            else:
                floatplane_link = None

            # Warn if floatplane_link is missing or blank
            if floatplane_link is None:
                print(f"  ⚠️  Warning ({filepath.name}): floatplane_link is missing or blank")

            # Verify filename matches header date/time
            filename_warning = _verify_filename(filepath, date_str, time_str)
            if filename_warning:
                print(f"  ⚠️  Warning ({filepath.name}): {filename_warning}")

            warnings, seen_events = convert_file(
                filepath, date_str, time_str, floatplane_link, all_events
            )

            for warning in warnings:
                print(f"  ⚠️  Warning ({filepath.name}): {warning}")

        except Exception as e:
            print(f"  ❌ Error processing {filepath.name}: {e}")
            total_warnings += 1

    # Update events.json with accumulated data
    seen_titles = _update_events_file(all_events)

    # Warn about events in events.json that were never seen
    if EVENTS_FILE.exists():
        events_data = json.loads(EVENTS_FILE.read_text(encoding="utf-8"))
        for event in events_data["events"]:
            if event["title"] not in seen_titles:
                print(
                    f"  ⚠️  Warning: Event '{event['title']}' in events.json "
                    f"was not found in any timestamp file."
                )

    if total_warnings > 0:
        print(f"\n⚠️  {total_warnings} file(s) had errors.")

    print(f"\nDone! Output saved to: {OUTPUT_FOLDER}")


if __name__ == "__main__":
    main()
