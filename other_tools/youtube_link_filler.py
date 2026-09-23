#!/usr/bin/env python3
"""
YouTube Link Filler Tool
A GUI tool to help fill in missing YouTube links for tracks in a JSON file.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os


class YouTubeLinkFiller:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Link Filler")
        self.root.geometry("700x400")
        self.root.resizable(True, True)

        self.json_file = None
        self.data = None
        self.current_index = 0
        self.filtered_tracks = []

        self._build_ui()

    def _build_ui(self):
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="JSON File", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))

        self.file_var = tk.StringVar(value="No file selected")
        ttk.Entry(file_frame, textvariable=self.file_var, state="readonly").pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10)
        )
        ttk.Button(file_frame, text="Open JSON", command=self._open_file).pack(
            side=tk.RIGHT
        )

        # Track info frame
        info_frame = ttk.LabelFrame(main_frame, text="Track Information", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        # Artist and Title
        ttk.Label(info_frame, text="Track:").pack(anchor=tk.W)
        track_btn_frame = ttk.Frame(info_frame)
        track_btn_frame.pack(fill=tk.X, pady=(2, 8))
        self.track_var = tk.StringVar(value="")
        ttk.Entry(track_btn_frame, textvariable=self.track_var, state="readonly").pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(track_btn_frame, text="Copy", command=self._copy_track).pack(
            side=tk.RIGHT, padx=(5, 0)
        )

        # Last time played
        ttk.Label(info_frame, text="Last Played:").pack(anchor=tk.W)
        self.last_played_var = tk.StringVar(value="")
        ttk.Entry(info_frame, textvariable=self.last_played_var, state="readonly").pack(
            fill=tk.X, pady=(2, 8)
        )

        # Progress label
        self.progress_var = tk.StringVar(value="")
        ttk.Label(info_frame, textvariable=self.progress_var, foreground="gray").pack(
            anchor=tk.W, pady=(0, 5)
        )

        # YouTube URL frame
        url_frame = ttk.LabelFrame(main_frame, text="YouTube URL", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(url_frame, text="Paste YouTube link:").pack(anchor=tk.W)
        self.youtube_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame, textvariable=self.youtube_var)
        url_entry.pack(fill=tk.X, pady=(2, 0))
        url_entry.bind("<Return>", lambda e: self._save_and_continue())

        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="Skip", command=self._skip).pack(
            side=tk.LEFT, expand=True, padx=(0, 5)
        )
        ttk.Button(
            btn_frame, text="Save and Continue", command=self._save_and_continue
        ).pack(side=tk.LEFT, expand=True, padx=(5, 0))

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(
            fill=tk.X, pady=(10, 0)
        )

    def _open_file(self):
        file_path = filedialog.askopenfilename(
            title="Open JSON File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if file_path:
            self.json_file = file_path
            self.file_var.set(os.path.basename(file_path))

            try:
                with open(self.json_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)

                if "tracks" not in self.data:
                    messagebox.showerror(
                        "Error", "JSON file must contain a 'tracks' key."
                    )
                    self.data = None
                    return

                # Filter tracks that have empty youtube URLs
                self.filtered_tracks = [
                    track for track in self.data["tracks"] if not track.get("youtube", "").strip()
                ]

                if not self.filtered_tracks:
                    messagebox.showinfo(
                        "Info", "All tracks already have YouTube links!"
                    )
                    self.status_var.set("All done!")
                    return

                self.current_index = 0
                self._load_current_track()

            except json.JSONDecodeError as e:
                messagebox.showerror("Error", f"Invalid JSON: {e}")
                self.data = None
            except Exception as e:
                messagebox.showerror("Error", f"Error reading file: {e}")
                self.data = None

    def _load_current_track(self):
        if self.current_index >= len(self.filtered_tracks):
            self.status_var.set("All tracks processed!")
            self.track_var.set("")
            self.last_played_var.set("")
            self.youtube_var.set("")
            self.progress_var.set("")
            return

        track = self.filtered_tracks[self.current_index]
        artist = track.get("artist", "Unknown Artist")
        title = track.get("title", "Unknown Title")
        self.track_var.set(f"{artist}, {title}")
        self.last_played_var.set(track.get("last_time_played", "N/A"))
        self.youtube_var.set("")
        self.progress_var.set(
            f"Track {self.current_index + 1} of {len(self.filtered_tracks)}"
        )
        self.status_var.set("Ready to enter YouTube link")

    def _copy_track(self):
        track_text = self.track_var.get()
        if track_text:
            self.root.clipboard_clear()
            self.root.clipboard_append(track_text)
            self.root.update()
            self.status_var.set(f"Copied: {track_text}")

    def _save_and_continue(self):
        if self.current_index >= len(self.filtered_tracks):
            return

        youtube_url = self.youtube_var.get().strip()
        if not youtube_url:
            messagebox.showwarning(
                "Warning", "YouTube URL cannot be empty. Use 'Skip' if you don't have a link."
            )
            return

        # Find the track in the original data and update it
        track = self.filtered_tracks[self.current_index]
        for t in self.data["tracks"]:
            if (
                t.get("title") == track.get("title")
                and t.get("artist") == track.get("artist")
            ):
                t["youtube"] = youtube_url
                break

        # Write updated data to disk immediately
        try:
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file: {e}")
            return

        self.current_index += 1
        self._load_current_track()

    def _skip(self):
        if self.current_index >= len(self.filtered_tracks):
            return

        self.current_index += 1
        self._load_current_track()

def main():
    root = tk.Tk()
    app = YouTubeLinkFiller(root)
    root.mainloop()


if __name__ == "__main__":
    main()
