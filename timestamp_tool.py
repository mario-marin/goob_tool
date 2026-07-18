#!/usr/bin/env python3
"""
Goob Timestamp Tool
A GUI tool for creating timestamps while watching streams.
Tracks elapsed time and saves timestamps to a date-stamped file.
"""

import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import os
import re
import threading
from pathlib import Path

# Debugging toggle - set to False to disable debug logging
DEBUG_MODE = False

# Static tracks JSON file path 
TRACKS_JSON_FILE = Path(__file__).parent / "tim-tams-viewer/public/data/tracks.json"


class TimestampTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Goob Timestamp Tool")
        self.root.geometry("1080x540")
        self.root.resizable(True, True)

        # Record when the stopwatch was started (in Adelaide time)
        self.opening_time = None
        self.save_file = None

        # Loaded timestamp state
        self.loaded_timestamp = False

        # Stopwatch state
        self.elapsed_seconds = 0
        self.running = False
        self.after_id_stopwatch = None
        self.after_id_save = None

        # Date/time override state
        self.use_override = False
        self.override_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.override_time_var = tk.StringVar(value=datetime.now().strftime("%H:%M"))

        # === Goob Tracks: JSON file path ===
        self.tracks_json_file = TRACKS_JSON_FILE

        self._build_ui()
        # Set initial pane sizes to 540 pixels each for 1080p screen
        self.root.after(100, self._set_pane_sizes)
        # Load tracks list after UI is built
        self.root.after(200, self._load_tracks_list)

    def _set_pane_sizes(self):
        """Set the initial sizes of the paned window sections."""
        # Get the paned window widget
        paned_window = None
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.PanedWindow):
                paned_window = widget
                break
        
        if paned_window:
            # Get the two child frames
            children = paned_window.children
            if len(children) >= 2:
                first_child = list(children.values())[0]
                second_child = list(children.values())[1]
                paned_window.paneconfig(first_child, width=540)
                paned_window.paneconfig(second_child, width=540)

    def _get_default_save_file(self):
        """Get default save file path based on when the script was opened."""
        timestamp_str = self.opening_time.strftime("%Y-%m-%d_%H-%M-%S")
        default_name = f"timestamps_{timestamp_str}.txt"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, default_name)

    def _build_ui(self):
        # --- Main container ---
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Split pane: Timtam Section (left) | Goob Tracks (right) ---
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # ==================== LEFT: Timtam Section ====================
        timtam_frame = ttk.LabelFrame(paned_window, text="Timtam Section", padding="10")
        paned_window.add(timtam_frame, weight=1)

        # --- Stopwatch Section (Smaller) ---
        stopwatch_frame = ttk.LabelFrame(timtam_frame, text="Stopwatch", padding="5")
        stopwatch_frame.pack(fill=tk.X, pady=(0, 10))

        self.time_label = tk.Label(
            stopwatch_frame,
            text="00:00:00",
            font=("monospace", 20, "bold"),
            anchor="center",
            fg="#2c3e50"
        )
        self.time_label.pack(fill=tk.X, pady=(0, 5))

        btn_frame = ttk.Frame(stopwatch_frame)
        btn_frame.pack(fill=tk.X)

        self.start_btn = ttk.Button(
            btn_frame, text="Start", width=10, command=self.toggle_stopwatch
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.reset_btn = ttk.Button(
            btn_frame, text="Reset", width=10, command=self.reset_stopwatch
        )
        self.reset_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Date/time override frame (to the right of Reset button)
        override_frame = ttk.Frame(btn_frame)
        override_frame.pack(side=tk.LEFT, padx=(15, 0))

        self.override_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            override_frame,
            text="Override",
            variable=self.override_var,
            command=self._on_override_toggle,
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(override_frame, text="Date:").pack(side=tk.LEFT, padx=(0, 2))
        self.override_date_entry = ttk.Entry(override_frame, textvariable=self.override_date_var, width=12)
        self.override_date_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(override_frame, text="Time:").pack(side=tk.LEFT, padx=(0, 2))
        self.override_time_entry = ttk.Entry(override_frame, textvariable=self.override_time_var, width=8)
        self.override_time_entry.pack(side=tk.LEFT, padx=(0, 5))

        self.override_status = ttk.Label(override_frame, text="", foreground="gray", font=("sans-serif", 8))
        self.override_status.pack(side=tk.LEFT, padx=(5, 0))

        # Keep the status label, but remove the save file button
        self.status_label = ttk.Label(
            stopwatch_frame,
            text="Not saving",
            font=("sans-serif", 9),
            foreground="gray",
        )
        self.status_label.pack(anchor=tk.E, pady=(5, 0))

        # --- File Operations Section ---
        file_ops_frame = ttk.LabelFrame(timtam_frame, text="File Operations", padding="5")
        file_ops_frame.pack(fill=tk.X, pady=(10, 10))

        self.load_file_btn = ttk.Button(
            file_ops_frame, text="Load File", width=18, command=self.load_file
        )
        self.load_file_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.correct_timestamps_btn = ttk.Button(
            file_ops_frame, text="Timestamp Correction", width=18, command=self.correct_timestamps
        )
        self.correct_timestamps_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.export_btn = ttk.Button(
            file_ops_frame, text="Export", width=18, command=self.export_timestamps
        )
        self.export_btn.pack(side=tk.LEFT, padx=(0, 5))

        # --- Stream Operations Section ---
        stream_ops_frame = ttk.LabelFrame(timtam_frame, text="Stream Operations", padding="5")
        stream_ops_frame.pack(fill=tk.X, pady=(10, 10))

        # Row 1: Add Timestamp, Frank Moves, Fronk Times, Apply Last
        row1_frame = ttk.Frame(stream_ops_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 5))

        self.add_btn = ttk.Button(
            row1_frame, text="Add Timestamp", width=18, command=self.add_timestamp
        )
        self.add_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.frank_moves_btn = ttk.Button(
            row1_frame, text="Frank Moves", width=18, command=self.add_frank_moves
        )
        self.frank_moves_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.fronk_times_btn = ttk.Button(
            row1_frame, text="Fronk Times", width=18, command=self.add_fronk_times
        )
        self.fronk_times_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.apply_last_btn = ttk.Button(
            row1_frame, text="Apply Last", width=18, command=self.apply_last
        )
        self.apply_last_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.apply_last_ii_btn = ttk.Button(
            row1_frame, text="Apply Last II", width=18, command=self.apply_last_ii
        )
        self.apply_last_ii_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Row 2: Pyzam button and text box
        row2_frame = ttk.Frame(stream_ops_frame)
        row2_frame.pack(fill=tk.X)

        self.pyzam_btn = ttk.Button(
            row2_frame, text="Pyzam", width=10, command=self.run_pyzam
        )
        self.pyzam_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.pyzam_result_var = tk.StringVar(value="")
        pyzam_entry = ttk.Entry(row2_frame, textvariable=self.pyzam_result_var, width=40)
        pyzam_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.copy_btn = ttk.Button(
            row2_frame, text="Copy", width=8, command=self.copy_pyzam_result
        )
        self.copy_btn.pack(side=tk.LEFT, padx=(5, 0))

        self.apply_btn = ttk.Button(
            row2_frame, text="Apply", width=8, command=self.apply_pyzam
        )
        self.apply_btn.pack(side=tk.LEFT, padx=(5, 0))

        # --- Timestamps Section ---
        timestamps_frame = ttk.LabelFrame(timtam_frame, text="Timestamps", padding="10")
        timestamps_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 10))

        # Text box with scrollbar
        text_container = ttk.Frame(timestamps_frame)
        text_container.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_box = tk.Text(
            text_container,
            wrap=tk.WORD,
            font=("monospace", 11),
            yscrollcommand=scrollbar.set,
            height=12,
        )
        self.text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_box.yview)

        # --- Bottom bar (status + Adelaide clock) ---
        self.bottom_bar = ttk.Frame(timtam_frame)
        self.bottom_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_bar = ttk.Label(
            self.bottom_bar,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2),
        )
        self.status_bar.pack(fill=tk.X, side=tk.LEFT, expand=True)

        self.adelaide_clock = ttk.Label(
            self.bottom_bar,
            text="",
            font=("monospace", 9),
            foreground="gray",
        )
        self.adelaide_clock.pack(side=tk.RIGHT)
        self._update_adelaide_clock()

        # ==================== RIGHT: Goob Tracks Section ====================
        goob_tracks_frame = ttk.LabelFrame(paned_window, text="Goob Tracks", padding="10")
        paned_window.add(goob_tracks_frame, weight=1)

        # --- Add Track form ---
        add_track_frame = ttk.LabelFrame(goob_tracks_frame, text="Add New Track", padding="5")
        add_track_frame.pack(fill=tk.X, pady=(5, 5))

        # Title
        ttk.Label(add_track_frame, text="Title:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.track_title_var = tk.StringVar()
        ttk.Entry(add_track_frame, textvariable=self.track_title_var, width=30).grid(
            row=0, column=1, padx=(0, 10), pady=2, sticky=tk.W
        )

        # Artist
        ttk.Label(add_track_frame, text="Artist:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.track_artist_var = tk.StringVar()
        ttk.Entry(add_track_frame, textvariable=self.track_artist_var, width=30).grid(
            row=1, column=1, padx=(0, 10), pady=2, sticky=tk.W
        )

        # YouTube
        ttk.Label(add_track_frame, text="YouTube:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.track_youtube_var = tk.StringVar()
        ttk.Entry(add_track_frame, textvariable=self.track_youtube_var, width=30).grid(
            row=2, column=1, padx=(0, 10), pady=2, sticky=tk.W
        )

        # Description
        ttk.Label(add_track_frame, text="Description:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.track_description_var = tk.StringVar()
        ttk.Entry(add_track_frame, textvariable=self.track_description_var, width=30).grid(
            row=3, column=1, padx=(0, 10), pady=2, sticky=tk.W
        )

        # Add button
        self.add_track_btn = ttk.Button(
            add_track_frame,
            text="Add Track",
            command=self._add_track,
        )
        self.add_track_btn.grid(row=4, column=0, columnspan=2, pady=(10, 0))

        # --- Track list (with copy buttons) ---
        track_list_frame = ttk.LabelFrame(goob_tracks_frame, text="Tracks", padding="5")
        track_list_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 5))

        # Canvas + scrollbar for scrollable track list
        canvas_container = ttk.Frame(track_list_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)

        self.tracks_canvas = tk.Canvas(canvas_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.tracks_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.tracks_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.tracks_canvas.configure(scrollregion=self.tracks_canvas.bbox("all"))
        )

        self.tracks_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.tracks_canvas.configure(yscrollcommand=scrollbar.set)

        self.tracks_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mouse wheel scrolling support
        self.tracks_canvas.bind_all("<MouseWheel>", self._on_canvas_mousewheel)

        # --- Status bar for Goob Tracks ---
        self.goob_status_label = ttk.Label(
            goob_tracks_frame,
            text="",
            foreground="gray",
            font=("sans-serif", 8),
        )
        self.goob_status_label.pack(anchor=tk.E, pady=(5, 0))

    def _on_canvas_mousewheel(self, event):
        """Handle mouse wheel scrolling on the tracks canvas."""
        self.tracks_canvas.yview_scroll(int(-1*(event.delta / 120)), "units")

    def _copy_youtube_link(self, youtube_url):
        """Copy a YouTube URL to the clipboard."""
        if youtube_url:
            self.root.clipboard_clear()
            self.root.clipboard_append(youtube_url)
            self.goob_status_label.config(text=f"Copied: {youtube_url}")
        else:
            self.goob_status_label.config(text="No YouTube link to copy")

    def _update_adelaide_clock(self):
        """Update the Adelaide, Australia clock display."""
        adelaide_time = datetime.now(ZoneInfo("Australia/Adelaide"))
        self.adelaide_clock.config(text=f"Adelaide Time  {adelaide_time.strftime('%Y-%m-%d')}  {adelaide_time.strftime('%H:%M:%S')}")
        self.root.after(1000, self._update_adelaide_clock)

    def _format_time(self, total_seconds):
        """Format seconds into HH:MM:SS."""
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _update_display(self):
        """Update the stopwatch display."""
        self.time_label.config(text=self._format_time(self.elapsed_seconds))

    def _on_override_toggle(self):
        """Handle the override checkbox toggle."""
        if self.override_var.get():
            # Only pre-fill with current Adelaide time if the fields are empty
            if not self.override_date_var.get() or not self.override_time_var.get():
                adelaide_now = datetime.now(ZoneInfo("Australia/Adelaide"))
                self.override_date_var.set(adelaide_now.strftime("%Y-%m-%d"))
                self.override_time_var.set(adelaide_now.strftime("%H:%M"))
            self.override_status.config(text="Will be used on Start", foreground="darkgreen")
        else:
            self.override_status.config(text="", foreground="gray")

    def toggle_stopwatch(self):
        """Start or stop the stopwatch."""
        if self.running:
            self._stop()
        else:
            self._start()

    def _start(self):
        """Start the stopwatch."""
        self.running = True
        self.start_btn.config(text="Stop")
        # Set opening_time and save_file only when Start is pressed (not when loading a file)
        if self.opening_time is None and self.loaded_timestamp is False:
            if self.override_var.get():
                self.use_override = True
                try:
                    override_dt = datetime.strptime(
                        f"{self.override_date_var.get()} {self.override_time_var.get()}",
                        "%Y-%m-%d %H:%M",
                    )
                    self.opening_time = override_dt.replace(tzinfo=ZoneInfo("Australia/Adelaide"))
                except ValueError:
                    self.opening_time = datetime.now(ZoneInfo("Australia/Adelaide"))
                    self.use_override = False
                    self.override_status.config(text="Invalid date/time format", foreground="red")
                    self.root.after(3000, lambda: self.override_status.config(text="", foreground="gray"))
            else:
                self.use_override = False
                self.opening_time = datetime.now(ZoneInfo("Australia/Adelaide"))
            self.save_file = self._get_default_save_file()
        self._tick()
        self._periodic_save()
        self.status_label.config(text=f"Saving to: {os.path.basename(self.save_file)}")

    def _stop(self):
        """Stop the stopwatch."""
        self.running = False
        self.start_btn.config(text="Start")
        if self.after_id_stopwatch:
            self.root.after_cancel(self.after_id_stopwatch)
            self.after_id_stopwatch = None
        if self.after_id_save:
            self.root.after_cancel(self.after_id_save)
            self.after_id_save = None
        self.status_label.config(text="Not saving")

    def _tick(self):
        """Update the stopwatch every second."""
        if self.running:
            self.elapsed_seconds += 1
            self._update_display()
            self.after_id_stopwatch = self.root.after(1000, self._tick)

    def reset_stopwatch(self):
        """Reset the stopwatch to zero."""
        self._stop()
        self.elapsed_seconds = 0
        self._update_display()
        self.status_bar.config(text="Stopwatch reset")

    def add_timestamp(self):
        """Add a timestamp with placeholder values."""
        time_str = self._format_time(self.elapsed_seconds)
        timestamp_line = f"{time_str} - _artist_, _song_"
        self.text_box.insert(tk.END, timestamp_line + "\n")
        self.text_box.see(tk.END)
        self.status_bar.config(text=f"Added: {timestamp_line}")
        # Note: _periodic_save() handles saving to file every second automatically

    def add_frank_moves(self):
        """Add a Frank Moves timestamp."""
        time_str = self._format_time(self.elapsed_seconds)
        timestamp_line = f"{time_str} - F R A N K - M O V E S -"
        self.text_box.insert(tk.END, timestamp_line + "\n")
        self.text_box.see(tk.END)
        self.status_bar.config(text=f"Added: {timestamp_line}")

    def add_fronk_times(self):
        """Add a Fronk Times timestamp."""
        time_str = self._format_time(self.elapsed_seconds)
        timestamp_line = f"{time_str} - Esther Abrami, No.9 Frank's Waltz"
        self.text_box.insert(tk.END, timestamp_line + "\n")
        self.text_box.see(tk.END)
        self.status_bar.config(text=f"Added: {timestamp_line}")

    def load_file(self):
        """Open a file dialog to load a file's contents into the text box."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = filedialog.askopenfilename(
            title="Load Timestamp File",
            initialdir=script_dir,
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.save_file = file_path
                self.status_label.config(text=f"Saving to: {os.path.basename(self.save_file)}")
                self.text_box.delete("1.0", tk.END)
                self.text_box.insert(tk.END, content)
                self.text_box.see(tk.END)
                self.status_bar.config(text=f"Loaded: {os.path.basename(file_path)}")
                self.loaded_timestamp = True
            except Exception as e:
                self.status_bar.config(text=f"Error loading file: {e}")

    def correct_timestamps(self):
        """Open a dialog to correct timestamps by a fixed offset with a calculator."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Timestamp Correction")
        dialog.geometry("450x350")
        dialog.transient(self.root)
        dialog.grab_set()

        # Get content to extract first and last timestamps
        content = self.text_box.get("1.0", tk.END)
        lines = content.split("\n")
        
        first_ts = ""
        last_ts = ""
        
        # Find first valid timestamp
        for line in lines:
            match = re.match(r"^(\d{2}:\d{2}:\d{2}) - (.+)$", line.strip())
            if match:
                first_ts = match.group(1)
                break
        
        # Find last valid timestamp
        for line in reversed(lines):
            match = re.match(r"^(\d{2}:\d{2}:\d{2}) - (.+)$", line.strip())
            if match:
                last_ts = match.group(1)
                break

        # Frame for timestamp inputs
        ts_frame = ttk.Frame(dialog)
        ts_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        # First timestamp row
        ttk.Label(ts_frame, text="First Timestamp:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        first_ts_entry = ttk.Entry(ts_frame, width=12)
        first_ts_entry.insert(0, first_ts)
        first_ts_entry.grid(row=0, column=1, padx=(0, 10))

        ttk.Label(ts_frame, text="Corrected First:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        corrected_first_entry = ttk.Entry(ts_frame, width=12)
        # Pre-fill with hour data (e.g., "00:" from "00:03:15")
        if first_ts:
            corrected_first_entry.insert(0, first_ts[:3])
        corrected_first_entry.grid(row=0, column=3)

        # Last timestamp row
        ttk.Label(ts_frame, text="Last Timestamp:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        last_ts_entry = ttk.Entry(ts_frame, width=12)
        last_ts_entry.insert(0, last_ts)
        last_ts_entry.grid(row=1, column=1, padx=(0, 10), pady=(5, 0))

        ttk.Label(ts_frame, text="Corrected Last:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        corrected_last_entry = ttk.Entry(ts_frame, width=12)
        # Pre-fill with hour data (e.g., "01:" from "01:54:31")
        if last_ts:
            corrected_last_entry.insert(0, last_ts[:3])
        corrected_last_entry.grid(row=1, column=3, pady=(5, 0))

        # Frame for shift calculations
        shift_frame = ttk.Frame(dialog)
        shift_frame.pack(fill=tk.X, padx=10, pady=(5, 5))

        ttk.Label(shift_frame, text="First Shift (s):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        first_shift_var = tk.StringVar(value="0")
        first_shift_entry = ttk.Entry(shift_frame, textvariable=first_shift_var, width=10)
        first_shift_entry.grid(row=0, column=1, padx=(0, 10))

        ttk.Label(shift_frame, text="Last Shift (s):").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        last_shift_var = tk.StringVar(value="0")
        last_shift_entry = ttk.Entry(shift_frame, textvariable=last_shift_var, width=10)
        last_shift_entry.grid(row=0, column=3)

        # Calculate button
        def calculate_shifts():
            try:
                def parse_time_to_seconds(time_str):
                    parts = time_str.split(":")
                    if len(parts) != 3:
                        raise ValueError("Invalid time format")
                    hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
                    return hours * 3600 + minutes * 60 + seconds

                first_seconds = parse_time_to_seconds(first_ts_entry.get())
                corrected_first_seconds = parse_time_to_seconds(corrected_first_entry.get())
                last_seconds = parse_time_to_seconds(last_ts_entry.get())
                corrected_last_seconds = parse_time_to_seconds(corrected_last_entry.get())

                first_shift = corrected_first_seconds - first_seconds
                last_shift = corrected_last_seconds - last_seconds

                first_shift_var.set(str(first_shift))
                last_shift_var.set(str(last_shift))

                # Suggest the smaller absolute shift
                if abs(first_shift) <= abs(last_shift):
                    offset_entry.delete(0, tk.END)
                    offset_entry.insert(0, str(first_shift))
                else:
                    offset_entry.delete(0, tk.END)
                    offset_entry.insert(0, str(last_shift))

            except ValueError:
                self.status_bar.config(text="Invalid timestamp format. Use HH:MM:SS")

        ttk.Button(shift_frame, text="Calculate", command=calculate_shifts).grid(row=1, column=0, columnspan=4, pady=(5, 0))

        # Frame for offset entry and apply button
        offset_frame = ttk.Frame(dialog)
        offset_frame.pack(fill=tk.X, padx=10, pady=(10, 10))

        ttk.Label(offset_frame, text="Enter offset in seconds (positive or negative):").pack(anchor=tk.W)

        offset_entry = ttk.Entry(offset_frame, width=20)
        offset_entry.pack(pady=(5, 10))
        offset_entry.focus_set()

        def apply_correction():
            try:
                offset = int(offset_entry.get())
                content = self.text_box.get("1.0", tk.END)
                corrected_content = self._apply_offset_to_timestamps(content, offset)
                self.text_box.delete("1.0", tk.END)
                self.text_box.insert(tk.END, corrected_content)
                self.text_box.see(tk.END)
                self.status_bar.config(text=f"Applied offset: {offset} seconds")
                dialog.destroy()
            except ValueError:
                self.status_bar.config(text="Invalid input. Please enter a number.")

        ttk.Button(offset_frame, text="Apply", command=apply_correction).pack(pady=(0, 10))

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

    def _apply_offset_to_timestamps(self, content, offset):
        """Apply a time offset to all valid timestamps in the content."""
        import re

        def replace_timestamp(match):
            time_str = match.group(1)
            rest = match.group(2)

            # Parse the timestamp
            parts = time_str.split(":")
            if len(parts) != 3:
                return match.group(0)

            try:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
            except ValueError:
                return match.group(0)

            # Convert to total seconds, apply offset, then convert back
            total_seconds = hours * 3600 + minutes * 60 + seconds
            total_seconds += offset

            # Handle negative results
            if total_seconds < 0:
                total_seconds = 0

            new_hours = total_seconds // 3600
            new_minutes = (total_seconds % 3600) // 60
            new_seconds = total_seconds % 60

            new_time_str = f"{new_hours:02d}:{new_minutes:02d}:{new_seconds:02d}"
            return f"{new_time_str} - {rest}"

        # Match timestamps in format HH:mm:ss - ...
        pattern = r"(\d{2}:\d{2}:\d{2}) - (.*)"
        corrected_content = re.sub(pattern, replace_timestamp, content)
        return corrected_content

    def export_timestamps(self):
        """Export timestamps without header to the system clipboard."""
        content = self.text_box.get("1.0", tk.END)

        # Remove the header if present
        if content.startswith("# Timestamps started:"):
            # Find the end of the header line and the blank line after it
            lines = content.split("\n")
            start_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("# Timestamps started:"):
                    # Skip the header line and the next blank line
                    start_idx = i + 2
                    break

            # Get the remaining lines
            timestamp_lines = lines[start_idx:]
        else:
            # No header, use all lines
            timestamp_lines = content.split("\n")

        # Filter out empty lines and join with double newlines
        non_empty_lines = [line for line in timestamp_lines if line.strip()]
        exported_text = "\n\n".join(non_empty_lines)

        # Copy to clipboard
        self.root.clipboard_clear()
        self.root.clipboard_append(exported_text)
        self.status_bar.config(text="Timestamps copied to clipboard")

    def copy_pyzam_result(self):
        """Copy the pyzam result text box contents to the system clipboard."""
        result = self.pyzam_result_var.get()
        self.root.clipboard_clear()
        self.root.clipboard_append(result)
        self.status_bar.config(text="Pyzam result copied to clipboard")

    def apply_pyzam(self):
        """Apply pyzam result to the last placeholder timestamp."""
        pyzam_text = self.pyzam_result_var.get()
        content = self.text_box.get("1.0", tk.END)
        
        # Remove trailing newline before splitting
        if content.endswith("\n"):
            content = content[:-1]
        
        lines = content.split("\n")

        # Find the last non-blank line in the text box
        last_non_blank_idx = None
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip():
                last_non_blank_idx = i
                break

        if last_non_blank_idx is None:
            self.status_bar.config(text="No placeholder timestamp found")
            return

        # Check if the last non-blank line matches the placeholder pattern
        last_line = lines[last_non_blank_idx]
        if not re.match(r"^\d{2}:\d{2}:\d{2} - _artist_, _song_$", last_line):
            self.status_bar.config(text="Last line is not a placeholder timestamp")
            return

        # Replace _artist_, _song_ with the pyzam text
        time_part = last_line.split(" - ")[0]
        new_line = f"{time_part} - {pyzam_text}"
        lines[last_non_blank_idx] = new_line

        # Update the text box
        self.text_box.delete("1.0", tk.END)
        self.text_box.insert(tk.END, "\n".join(lines))
        self.text_box.see(tk.END)
        self.status_bar.config(text=f"Applied: {pyzam_text}")

    def apply_last(self):
        """Copy artist/song from the last valid timestamp to the last placeholder timestamp."""
        content = self.text_box.get("1.0", tk.END)

        # Remove trailing newline before splitting
        if content.endswith("\n"):
            content = content[:-1]

        lines = content.split("\n")

        # Find the last non-blank line (the target placeholder)
        last_non_blank_idx = None
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip():
                last_non_blank_idx = i
                break

        if last_non_blank_idx is None:
            self.status_bar.config(text="No placeholder timestamp found")
            return

        # Check if the last non-blank line matches the placeholder pattern
        last_line = lines[last_non_blank_idx]
        if not re.match(r"^\d{2}:\d{2}:\d{2} - _artist_, _song_$", last_line):
            self.status_bar.config(text="Last line is not a placeholder timestamp")
            return

        # Find the last valid timestamp (non-placeholder) going backwards
        valid_artist_song = None
        for i in range(last_non_blank_idx - 1, -1, -1):
            line = lines[i]
            if not line.strip():
                continue
            match = re.match(r"^(\d{2}:\d{2}:\d{2}) - (.+)$", line)
            if match:
                artist_song = match.group(2)
                # Skip if it's still a placeholder
                if artist_song != "_artist_, _song_":
                    valid_artist_song = artist_song
                    break

        if valid_artist_song is None:
            self.status_bar.config(text="No valid timestamp found to copy from")
            return

        # Replace _artist_, _song_ in the last line with the valid artist/song
        time_part = last_line.split(" - ")[0]
        new_line = f"{time_part} - {valid_artist_song}"
        lines[last_non_blank_idx] = new_line

        # Update the text box
        self.text_box.delete("1.0", tk.END)
        self.text_box.insert(tk.END, "\n".join(lines))
        self.text_box.see(tk.END)
        self.status_bar.config(text=f"Applied: {valid_artist_song}")

    def apply_last_ii(self):
        """Copy artist/song from the second-to-last valid timestamp to the last placeholder timestamp."""
        content = self.text_box.get("1.0", tk.END)

        # Remove trailing newline before splitting
        if content.endswith("\n"):
            content = content[:-1]

        lines = content.split("\n")

        # Find the last non-blank line (the target placeholder)
        last_non_blank_idx = None
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip():
                last_non_blank_idx = i
                break

        if last_non_blank_idx is None:
            self.status_bar.config(text="No placeholder timestamp found")
            return

        # Check if the last non-blank line matches the placeholder pattern
        last_line = lines[last_non_blank_idx]
        if not re.match(r"^\d{2}:\d{2}:\d{2} - _artist_, _song_$", last_line):
            self.status_bar.config(text="Last line is not a placeholder timestamp")
            return

        # Find the second-to-last valid timestamp (non-placeholder) going backwards
        # First, find the last valid timestamp
        last_valid_idx = None
        for i in range(last_non_blank_idx - 1, -1, -1):
            line = lines[i]
            if not line.strip():
                continue
            match = re.match(r"^(\d{2}:\d{2}:\d{2}) - (.+)$", line)
            if match:
                artist_song = match.group(2)
                if artist_song != "_artist_, _song_":
                    last_valid_idx = i
                    break

        # Now find the one before that
        valid_artist_song = None
        if last_valid_idx is not None:
            for i in range(last_valid_idx - 1, -1, -1):
                line = lines[i]
                if not line.strip():
                    continue
                match = re.match(r"^(\d{2}:\d{2}:\d{2}) - (.+)$", line)
                if match:
                    artist_song = match.group(2)
                    if artist_song != "_artist_, _song_":
                        valid_artist_song = artist_song
                        break

        if valid_artist_song is None:
            self.status_bar.config(text="No second-to-last valid timestamp found to copy from")
            return

        # Replace _artist_, _song_ in the last line with the valid artist/song
        time_part = last_line.split(" - ")[0]
        new_line = f"{time_part} - {valid_artist_song}"
        lines[last_non_blank_idx] = new_line

        # Update the text box
        self.text_box.delete("1.0", tk.END)
        self.text_box.insert(tk.END, "\n".join(lines))
        self.text_box.see(tk.END)
        self.status_bar.config(text=f"Applied: {valid_artist_song}")

    def run_pyzam(self):
        """Run pyzam_json and output results to pyzam.log file."""
        # Clear the pyzam result text field
        self.pyzam_result_var.set("")
        
        # Disable the button while running to prevent multiple executions
        self.pyzam_btn.config(state=tk.DISABLED)
        self.pyzam_btn.config(text="Running...")
        
        # Start pyzam in a separate thread to prevent freezing the GUI
        thread = threading.Thread(target=self._run_pyzam_thread)
        thread.daemon = True
        thread.start()

    def _run_pyzam_thread(self):
        """Helper method to run pyzam in a separate thread."""
        try:
            import subprocess
            import os
            import json

            # Get the script directory for the log file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            log_file = os.path.join(script_dir, "pyzam.log")

            # Run the pyzam command with uv
            cmd = ["uv", "tool", "run", "--python", "3.12", "pyzam", "--json", "--speaker", "--duration", "10"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )

            # Write output to log file if debug mode is enabled
            if DEBUG_MODE:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(result.stdout)
                    if result.stderr:
                        f.write("\n\nErrors:\n")
                        f.write(result.stderr)

            # Parse the JSON output to extract title and subtitle
            pyzam_result = "No match found"
            if result.stdout.strip():
                try:
                    # The output might contain a text line followed by JSON
                    # We need to extract the JSON part from the output
                    output = result.stdout.strip()
                    
                    # Try to find JSON in the output by looking for '{' and '}'
                    start_idx = output.find('{')
                    if start_idx != -1:
                        # Find the matching closing brace
                        brace_count = 0
                        end_idx = -1
                        for i in range(start_idx, len(output)):
                            if output[i] == '{':
                                brace_count += 1
                            elif output[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i + 1
                                    break
                        
                        if end_idx != -1:
                            json_str = output[start_idx:end_idx]
                            data = None
                            
                            # Try to parse as standard JSON first
                            try:
                                data = json.loads(json_str)
                            except json.JSONDecodeError:
                                # If standard JSON fails, try to convert single quotes to double quotes
                                # This handles Python dict representations that use single quotes
                                try:
                                    # Replace single quotes with double quotes, but be careful with strings that contain single quotes
                                    # We'll use a simple approach: replace all single quotes with double quotes
                                    # This works for simple cases where strings don't contain single quotes
                                    converted_str = json_str.replace("'", '"')
                                    data = json.loads(converted_str)
                                except json.JSONDecodeError:
                                    # If that also fails, try using ast.literal_eval which handles Python literals
                                    import ast
                                    try:
                                        data = ast.literal_eval(json_str)
                                    except (ValueError, SyntaxError):
                                        # If all parsing methods fail, skip this entry
                                        data = None
                            
                            # Check if there's a track with title and subtitle
                            if data and 'track' in data and 'title' in data['track'] and 'subtitle' in data['track']:
                                pyzam_result = f"{data['track']['subtitle']}, {data['track']['title']}"
                except Exception as e:
                    pyzam_result = "No match found"

            # Update the result display in the main thread
            self.root.after(0, lambda: self.pyzam_result_var.set(pyzam_result))
            self.root.after(0, lambda: self.status_bar.config(text="Pyzam results saved to pyzam.log"))
            # Re-enable the button
            self.root.after(0, lambda: self.pyzam_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.pyzam_btn.config(text="Pyzam"))
        except subprocess.TimeoutExpired:
            self.root.after(0, lambda: self.status_bar.config(text="Pyzam timed out after 30 seconds"))
            self.root.after(0, lambda: self.pyzam_result_var.set("Pyzam timed out"))
            # Re-enable the button
            self.root.after(0, lambda: self.pyzam_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.pyzam_btn.config(text="Pyzam"))
        except Exception as e:
            self.root.after(0, lambda: self.status_bar.config(text=f"Error running pyzam: {e}"))
            self.root.after(0, lambda: self.pyzam_result_var.set(f"Error: {e}"))
            # Re-enable the button
            self.root.after(0, lambda: self.pyzam_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.pyzam_btn.config(text="Pyzam"))

    def _periodic_save(self):
        """Save the entire text box content to the file every second."""
        content = self.text_box.get("1.0", tk.END)
        try:
            with open(self.save_file, "w", encoding="utf-8") as f:
                # Only add header if it's not already present in the content
                if not content.startswith("# Timestamps started:"):
                    f.write(f"# Timestamps started: {self.opening_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(content)
        except Exception as e:
            self.status_bar.config(text=f"Error saving file: {e}")
        # Reschedule to run again in 1 second
        self.after_id_save = self.root.after(1000, self._periodic_save)

    # ================================================================
    # Goob Tracks methods
    # ================================================================

    def _load_tracks_list(self):
        """Load and display all tracks as rows with copy buttons."""
        # Clear existing track rows
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        try:
            with open(self.tracks_json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            tracks = data.get("tracks", [])
            if not tracks:
                empty_label = ttk.Label(self.scrollable_frame, text="(no tracks found)", foreground="gray", font=("sans-serif", 10))
                empty_label.pack(pady=30)
                return

            for idx, track in enumerate(tracks):
                title = track.get("title", "Untitled")
                artist = track.get("artist", "Unknown")
                youtube = track.get("youtube", "")
                description = track.get("hidden", {}).get("description", "") if isinstance(track.get("hidden"), dict) else track.get("description", "")

                # Add separator between tracks (except before the first one)
                if idx > 0:
                    separator = ttk.Separator(self.scrollable_frame, orient=tk.HORIZONTAL)
                    separator.pack(fill=tk.X, padx=5, pady=(8, 4))

                # Create a row frame for this track with more padding
                row_frame = ttk.Frame(self.scrollable_frame)
                row_frame.pack(fill=tk.X, padx=5, pady=(2, 8))

                # Track info label with larger font and better spacing
                info_text = f"{artist}, {title}"
                if description:
                    info_text += f"\n    {description}"

                info_label = ttk.Label(
                    row_frame,
                    text=info_text,
                    font=("monospace", 10),
                    wraplength=500,
                    justify=tk.LEFT,
                    anchor=tk.W,
                )
                info_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), pady=3)

                # YouTube button (right side) - grayed out if no youtube link
                btn_state = tk.NORMAL if youtube else tk.DISABLED
                youtube_btn = ttk.Button(
                    row_frame,
                    text="youtube",
                    width=8,
                    state=btn_state,
                    command=lambda url=youtube: self._copy_youtube_link(url),
                )
                youtube_btn.pack(side=tk.RIGHT, padx=(5, 0), pady=3)

                # Apply button (right side) - applies artist, title to last placeholder timestamp
                apply_btn = ttk.Button(
                    row_frame,
                    text="Apply",
                    width=8,
                    command=lambda a=artist, t=title: self._apply_track_to_placeholder(a, t),
                )
                apply_btn.pack(side=tk.RIGHT, padx=(5, 0), pady=3)

        except FileNotFoundError:
            error_label = ttk.Label(self.scrollable_frame, text=f"File not found: {self.tracks_json_file}", foreground="red", font=("sans-serif", 10))
            error_label.pack(pady=30)
            self.goob_status_label.config(text=f"File not found: {self.tracks_json_file}")
        except json.JSONDecodeError as e:
            error_label = ttk.Label(self.scrollable_frame, text=f"Invalid JSON: {e}", foreground="red", font=("sans-serif", 10))
            error_label.pack(pady=30)
            self.goob_status_label.config(text=f"Invalid JSON: {e}")
        except Exception as e:
            error_label = ttk.Label(self.scrollable_frame, text=f"Error loading tracks: {e}", foreground="red", font=("sans-serif", 10))
            error_label.pack(pady=30)
            self.goob_status_label.config(text=f"Error loading tracks: {e}")

    def _apply_track_to_placeholder(self, artist, title):
        """Apply artist and title from a track to the last placeholder timestamp line."""
        content = self.text_box.get("1.0", tk.END)

        # Remove trailing newline before splitting
        if content.endswith("\n"):
            content = content[:-1]

        lines = content.split("\n")

        # Find the last non-blank line (the target placeholder)
        last_non_blank_idx = None
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip():
                last_non_blank_idx = i
                break

        if last_non_blank_idx is None:
            self.status_bar.config(text="No placeholder timestamp found")
            return

        # Check if the last non-blank line matches the placeholder pattern
        last_line = lines[last_non_blank_idx]
        if not re.match(r"^\d{2}:\d{2}:\d{2} - _artist_, _song_$", last_line):
            self.status_bar.config(text="Last line is not a placeholder timestamp")
            return

        # Replace _artist_, _song_ with the track's artist and title
        time_part = last_line.split(" - ")[0]
        new_line = f"{time_part} - {artist}, {title}"
        lines[last_non_blank_idx] = new_line

        # Update the text box
        self.text_box.delete("1.0", tk.END)
        self.text_box.insert(tk.END, "\n".join(lines))
        self.text_box.see(tk.END)
        self.status_bar.config(text=f"Applied: {artist}, {title}")

    def _add_track(self):
        """Add a new track entry to the JSON file."""
        title = self.track_title_var.get().strip()
        artist = self.track_artist_var.get().strip()
        youtube = self.track_youtube_var.get().strip()
        description = self.track_description_var.get().strip()

        if not title:
            self.goob_status_label.config(text="Title is required.")
            return

        # Build the new track object.
        #
        # NOTE: If the JSON schema gains new keys in the future, add them here.
        # For each new key, decide whether to:
        #   1. Add a new UI field (Entry / Checkbutton / etc.) and populate it, or
        #   2. Use a sensible default (empty string, 0, False, [], {}, etc.)
        #
        # Example for a new key "genre":
        #   new_track["genre"] = ""
        #
        new_track = {
            "title": title,
            "artist": artist,
            "youtube": youtube,
            "aliases": [],
            "hidden": {
                "description": description,
            },
            "number_of_times_played": 0,
            "last_time_played": "",
            "date_with_most_reproductions": "",
            "most_reproductions_record": 0,
        }

        try:
            with open(self.tracks_json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"tracks": []}

        if "tracks" not in data:
            data["tracks"] = []

        data["tracks"].append(new_track)

        with open(self.tracks_json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Clear form fields
        self.track_title_var.set("")
        self.track_artist_var.set("")
        self.track_youtube_var.set("")
        self.track_description_var.set("")

        # Refresh the list
        self._load_tracks_list()
        self.goob_status_label.config(text=f"Added: {title} by {artist}")

    # ================================================================
    # End Goob Tracks methods
    # ================================================================

    def on_closing(self):
        """Handle window close event."""
        content = self.text_box.get("1.0", tk.END)
        self.root.destroy()


def main():
    root = tk.Tk()
    app = TimestampTool(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
        


