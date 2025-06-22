# --- START OF FILE FNote.py ---

import tkinter as tk
from tkinter import ttk, filedialog, BooleanVar, StringVar, Text, Scrollbar, messagebox, IntVar
import vlc
import tinytag
import os
import random
import json
import pystray
from PIL import Image, ImageTk
import winshell
import shutil
import sys
import argparse
import threading
import time
import psutil
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
from comtypes import COMError
import logging
import zipfile
import re
import uuid
from pathlib import Path

APP_NAME = "FNote"
LOG_FILE = 'fnote.log'
MEM_SETTINGS_FILE = "FMem.json"
CONF_SETTINGS_FILE = "FConf.json"
TEMP_PLAYLIST_DIR = 'temp_playlist_extract'
PLAYLISTS_DIR_NAME = 'playlists'
ICON_FILENAME = "icon.ico"
DEFAULT_THEME = {
    "BG_COLOR": "#f9f9f9",
    "FG_COLOR": "#2e2e2e",
    "BUTTON_COLOR": "#e8e8e8",
    "BUTTON_FG_COLOR": "#2e2e2e",
    "ACTIVE_BG_COLOR": "#fdd5b0",
    "ACTIVE_FG_COLOR": "#2e2e2e",
    "LIST_SELECT_COLOR": "#fdd5b0",
    "ACCENT_COLOR": "#ffbb77",
    "DRAG_HIGHLIGHT_COLOR": "#fdd5b0"
}
DEFAULT_IGNORE_LIST = ["FxSound.exe", "obs64.exe", "python", "FNote.exe",
                        "VoicemeeterBanana.exe", "VoicemeeterPotato.exe",
                        "vbcable_controlpanel.exe",
                        "discord.exe", "teams.exe", "zoom.exe", "skype.exe",
                        "steam.exe", "epicgameslauncher.exe", "riotclientux.exe",
                        "nahimic.exe", "dolbyaccess.exe", "dtssoundunbound.exe", "sonicaudio.exe",
                        "streamlabsdesktop.exe", "xsplit.exe", "nvidia_container.exe",
                        "wallpaper32.exe", "wallpaper64.exe",
                        "livesplit.exe", "systemsounds", "audiodg.exe", "svchost.exe", "lsass.exe", "winlogon.exe", "services.exe", "taskhostw.exe", "ShellExperienceHost.exe", "RuntimeBroker.exe", "explorer.exe"]
AUDIO_EXTENSIONS = ('.mp3', '.m4a', '.m4b', '.ogg', '.oga', '.flac', '.wav', '.aac', '.wma', '.ac3', '.ec3', '.aif', '.aiff', '.ape', '.alac', '.opus', '.amr', '.au', '.caf', '.dff', '.dsf', '.spx', '.gsm', '.wv', '.tta', '.dts', '.mod', '.it', '.s3m', '.xm', '.mtm', '.umx', '.669', '.stm')
PLAYLIST_ZIP_EXTENSION = ".zip"
PLAYLIST_ORDER_JSON_FILENAME = "playlist_order.json"
MUSIC_FILE_FILTER = ("Audio files", "*.mp3;*.m4a;*.m4b;*.ogg;*.oga;*.flac;*.wav;*.aac;*.wma;*.ac3;*.ec3;*.aif;*.aiff;*.ape;*.alac;*.opus;*.amr;*.au;*.caf;*.dff;*.dsf;*.spx;*.gsm;*.wv;*.tta;*.dts;*.mod;*.it;*.s3m;*.xm;*.mtm;*.umx;*.669;*.stm")
ALL_FILES_FILTER = ("All files", "*.*")
AUDIO_PLAYLIST_FILE_FILTER = (
    ("Audio files and Playlists", f"*.mp3;*.m4a;*.m4b;*.ogg;*.oga;*.flac;*.wav;*.aac;*.wma;*.ac3;*.ec3;*.aif;*.aiff;*.ape;*.alac;*.opus;*.amr;*.au;*.caf;*.dff;*.dsf;*.spx;*.gsm;*.wv;*.tta;*.dts;*.mod;*.it;*.s3m;*.xm;*.mtm;*.umx;*.669;*.stm;*{PLAYLIST_ZIP_EXTENSION}"),
    MUSIC_FILE_FILTER,
    ("Zip files (Playlists)", f"*{PLAYLIST_ZIP_EXTENSION}"),
    ALL_FILES_FILTER
)
ICON_SIZE = (24, 24)
PROGRESS_BAR_UPDATE_INTERVAL = 250
AUDIO_CHECK_INTERVAL = 500 # How often to check for external audio
VOLUME_FADE_STEP_INTERVAL = 30 # Milliseconds between volume fade steps
SEEK_END_THRESHOLD_MS = 100
LOOP_TYPES = ["Loop playlist", "Loop song", "No loop"]
DEFAULT_LOOP_TYPE = "Loop playlist"
DEFAULT_AUTO_DUCK_ENABLED = False
DEFAULT_DUCK_VOLUME_LEVEL = 20 # Default volume percent when ducking
DEFAULT_DUCK_FADE_DURATION_MS = 500 # Default fade time in milliseconds

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        base_path = Path(".")
    return str(base_path / "assets" / relative_path)

class FNote:
    """Music player application class."""

    def __init__(self, master):
        """Initialize the FNote music player."""
        self.master = master
        master.title(APP_NAME)
        master.geometry("900x600")
        master.minsize(400, 300)
        try:
            master.iconbitmap(resource_path(ICON_FILENAME))
        except tk.TclError:
            pass

        self.app_theme = self.load_theme()
        master.configure(bg=self.app_theme['BG_COLOR'])

        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()
        self.next_media = None
        self.next_song_path_preload = None

        self.playlists = {"default": []}
        self.current_playlist_name = "default"
        self.current_song_index = 0
        self.is_paused = False # User-initiated pause
        self.tray_icon = None
        self.is_minimized_to_tray = BooleanVar()
        self.is_in_tray = BooleanVar()
        self.run_at_startup = BooleanVar()
        self.volume = 70 # User's intended volume level
        self.current_song_path = None
        self.current_playing_index = None
        self.last_playing_index = None
        self.shuffle_enabled = BooleanVar(value=False)
        self.startup_playlist_name = StringVar(value="None")
        self.next_shuffled_song_index = None
        self.shuffled_playlist_indices = []
        self.current_shuffled_index = 0
        self.loop_type = StringVar(value=DEFAULT_LOOP_TYPE)

        # --- Ducking Settings ---
        self.auto_duck_enabled = BooleanVar(value=DEFAULT_AUTO_DUCK_ENABLED)
        self.duck_volume_level = IntVar(value=DEFAULT_DUCK_VOLUME_LEVEL)
        self.duck_fade_duration_ms = IntVar(value=DEFAULT_DUCK_FADE_DURATION_MS)
        self.is_currently_ducked = False # State flag: volume is lowered due to external audio
        self.original_volume_before_duck = None # Store user volume before ducking
        self.volume_change_timer = None # Timer ID for smooth volume changes
        # --- End Ducking Settings ---

        self.ignore_list = DEFAULT_IGNORE_LIST.copy()
        self.debug_window = None
        self.show_debug_var = BooleanVar(value=False)

        self.drag_start_index = None
        self.last_highlighted_index = None
        self.rename_dialog_open = False
        self.is_renaming_playing_song = False
        self.song_rename_dialog_open = False

        self.load_settings() # Load settings before creating UI that uses them
        self.load_icons()
        self.setup_styles()
        self.create_ui()
        self.update_playlist_dropdown()
        self.set_volume(self.volume) # Apply loaded volume to player and slider

        parser = argparse.ArgumentParser()
        parser.add_argument('--startup', action='store_true', help='Launched from startup')
        parser.add_argument('playlist_file', nargs='?', help='Path to a playlist file to import')
        args = parser.parse_args()
        self.launched_from_startup = args.startup

        if self.launched_from_startup:
            self.master.after(0, self.start_in_tray_startup)

        if args.playlist_file:
            playlist_file_path = args.playlist_file
            if playlist_file_path.lower().endswith(PLAYLIST_ZIP_EXTENSION.lower()):
                if not os.path.exists(playlist_file_path):
                    messagebox.showerror("Playlist Import Error", f"Playlist file not found: {playlist_file_path}")
                else:
                    self.master.after(100, lambda: self.import_playlist(playlist_file_path))

        master.protocol("WM_DELETE_WINDOW", self.on_close)
        master.bind("<Map>", self.on_restore)

        self.audio_lock = threading.Lock()
        self.external_audio_active = False
        self.audio_detection_thread = None
        self.start_audio_detection()
        # self.paused_by_external = False # Removed, replaced by ducking logic
        # self.resume_timer = None # Removed, replaced by ducking logic
        self.master.after(AUDIO_CHECK_INTERVAL, self.check_audio_state) # Start audio state checking loop

        self.progress_bar_active = False
        self.progress_bar_value = 0
        self.media_duration = 0

        master.bind("<space>", self.toggle_play_pause_shortcut)
        master.bind("<Down>", self.next_song_shortcut)
        master.bind("<s>", self.next_song_shortcut)
        master.bind("<Up>", self.prev_song_shortcut)
        master.bind("<w>", self.prev_song_shortcut)
        master.bind("<Left>", self.volume_down_shortcut)
        master.bind("<a>", self.volume_down_shortcut)
        master.bind("<Right>", self.volume_up_shortcut)
        master.bind("<d>", self.volume_up_shortcut)
        master.bind("<Delete>", self.delete_song_shortcut)
        master.bind("<Control-s>", self.shuffle_playlist_shortcut)
        master.bind("<F2>", self.rename_song_shortcut)

    # ... (resource_path remains the same) ...

    # --- UI Creation and Related Methods ---

    def load_theme(self):
        """Load application theme settings."""
        return DEFAULT_THEME

    def create_ui(self):
        """Create the main UI elements."""
        self.create_top_bar()
        self.create_playlist_area()
        self.create_controls_area()

    # ... (export_playlist, import_playlist, get_unique_playlist_name remain the same) ...

    def create_top_bar(self):
        """Create the top bar with song label, settings button and progress bar."""
        top_bar = ttk.Frame(self.master, style="Light.TFrame")
        top_bar.pack(fill=tk.X)

        # --- Modified: Expanded frame for progress bar to take priority ---
        progress_bar_parent_frame = ttk.Frame(top_bar, style="Light.TFrame")
        progress_bar_parent_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=5)
        self.create_progress_bar_frame(progress_bar_parent_frame)
        # --- End Modification ---

        self.current_song_label = ttk.Label(top_bar, text="No song playing", font=("Arial", 12), style="Light.TLabel", anchor='w', justify='left')
        self.current_song_label.pack(side=tk.LEFT, padx=(0, 10), pady=5, fill=tk.X, expand=False) # Don't expand label

        settings_button = ttk.Button(top_bar, image=self.setting_icon, command=self.open_settings_window, style="Light.TButton")
        settings_button.pack(side=tk.RIGHT, padx=10, pady=5)


    def create_progress_bar_frame(self, parent_frame):
        """Create the progress bar frame with time labels and progress bar."""
        # This frame now exists within progress_bar_parent_frame passed from create_top_bar
        progress_bar_frame = ttk.Frame(parent_frame, style="Light.TFrame")
        # Pack within its immediate parent
        progress_bar_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.elapsed_time_label = ttk.Label(progress_bar_frame, text="00:00", font=("Arial", 10), style="Light.TLabel")
        self.elapsed_time_label.pack(side=tk.LEFT)

        self.progress_bar = ttk.Progressbar(progress_bar_frame, orient="horizontal", length=200, mode="determinate", style="Light.Horizontal.TProgressbar")
        # Ensure progress bar expands
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.progress_bar.bind("<Button-1>", self.on_progress_bar_click)
        self.progress_bar.bind("<B1-Motion>", self.on_progress_bar_drag)

        self.remaining_time_label = ttk.Label(progress_bar_frame, text="00:00", font=("Arial", 10), style="Light.TLabel")
        self.remaining_time_label.pack(side=tk.LEFT)

    # ... (on_progress_bar_click, on_progress_bar_drag, _seek_progress_bar, _update_time_labels remain the same) ...

    def create_settings_frame(self, settings_window):
        """Create the settings frame and its widgets with tabs."""
        settings_notebook = ttk.Notebook(settings_window, style="Light.TNotebook")

        player_tab = ttk.Frame(settings_notebook, style="Light.TFrame")
        system_tab = ttk.Frame(settings_notebook, style="Light.TFrame")

        settings_notebook.add(player_tab, text="Player")
        settings_notebook.add(system_tab, text="System")
        settings_notebook.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # --- Modified: Ducking Settings ---
        ducking_frame = ttk.LabelFrame(player_tab, text="External Audio Handling", style="Light.TLabelframe")
        ducking_frame.pack(pady=10, padx=10, fill=tk.X, anchor="w")

        ttk.Checkbutton(ducking_frame, text="Adjust volume when external audio is detected",
                        variable=self.auto_duck_enabled, command=self.save_settings,
                        style="Light.TCheckbutton").grid(row=0, column=0, columnspan=2, pady=5, padx=5, sticky="w")

        ttk.Label(ducking_frame, text="Ducked Volume Level (%):", style="Light.TLabel").grid(row=1, column=0, pady=(5,0), padx=5, sticky="w")
        duck_volume_spinbox = ttk.Spinbox(ducking_frame, from_=0, to=100, textvariable=self.duck_volume_level,
                                          command=self.save_settings, width=5, style="Light.TSpinbox")
        duck_volume_spinbox.grid(row=1, column=1, pady=(5,0), padx=5, sticky="w")
        # Add validation if needed later

        ttk.Label(ducking_frame, text="Fade Duration (ms):", style="Light.TLabel").grid(row=2, column=0, pady=(5,10), padx=5, sticky="w")
        fade_duration_spinbox = ttk.Spinbox(ducking_frame, from_=0, to=5000, increment=50, textvariable=self.duck_fade_duration_ms,
                                            command=self.save_settings, width=5, style="Light.TSpinbox")
        fade_duration_spinbox.grid(row=2, column=1, pady=(5,10), padx=5, sticky="w")
        # --- End Ducking Settings ---


        ttk.Label(player_tab, text="External audio blacklist (one per line, requires restart):", style="Light.TLabel").pack(pady=(10, 5), padx=10, anchor="w")
        self.ignore_list_text = Text(player_tab, height=5, width=40, bg=self.app_theme['BG_COLOR'], fg=self.app_theme['FG_COLOR'], highlightthickness=0, bd=1, relief="solid")
        self.ignore_list_text.pack(padx=10, anchor="w", fill=tk.X)
        self.ignore_list_text.insert(tk.END, "\n".join(self.ignore_list))

        restore_defaults_button = ttk.Button(player_tab, text="Restore Default Ignore List", command=self.restore_default_ignore_list, style="Light.TButton")
        restore_defaults_button.pack(pady=(5, 10), padx=10, anchor="w")

        ttk.Checkbutton(player_tab, text="Show Debug Window", style="Light.TCheckbutton",
                        variable=self.show_debug_var, command=self.toggle_debug_window).pack(pady=5, padx=10, anchor="w")

        ttk.Label(player_tab, text="Loop type:", style="Light.TLabel").pack(pady=(10, 5), padx=10, anchor="w")
        self.loop_type_dropdown = ttk.Combobox(player_tab, textvariable=self.loop_type, style="Light.TCombobox", values=LOOP_TYPES, state='readonly')
        self.loop_type_dropdown.pack(padx=10, anchor="w", fill=tk.X)
        self.loop_type_dropdown.set(self.loop_type.get())
        self.loop_type_dropdown.bind("<<ComboboxSelected>>", lambda event: self.save_settings())

        # --- System Tab remains the same ---
        ttk.Checkbutton(system_tab, text="Hide to System Tray", style="Light.TCheckbutton",
                        command=self.toggle_tray_setting, variable=self.is_in_tray).pack(pady=5, padx=10, anchor="w")

        ttk.Checkbutton(system_tab, text="Run on Startup", style="Light.TCheckbutton",
                        variable=self.run_at_startup, command=self.toggle_run_at_startup).pack(pady=5, padx=10, anchor="w")

        ttk.Label(system_tab, text="Startup Playlist:", style="Light.TLabel").pack(pady=(10, 5), padx=10, anchor="w")
        self.startup_playlist_dropdown = ttk.Combobox(system_tab, textvariable=self.startup_playlist_name, style="Light.TCombobox", values=list(self.playlists.keys()) + ["None"])
        self.startup_playlist_dropdown.pack(padx=10, anchor="w", fill=tk.X)
        self.startup_playlist_dropdown.set(self.startup_playlist_name.get())

        return settings_notebook

    # ... (restore_default_ignore_list remains the same) ...
    # ... (create_playlist_area, on_drag_start, on_drag_motion, on_drag_release, _reorder_song_in_playlist remain the same) ...
    # ... (create_playlist_dropdown, create_playlist_buttons, create_controls_area remain the same) ...
    # ... (create_playback_buttons, create_volume_control remain the same) ...

    def on_media_player_end_reached(self, event):
        """Event handler when media player reaches the end of a song. Calls next song logic in main thread."""
        # Reset ducking state cleanly before starting next song
        if self.volume_change_timer:
            self.master.after_cancel(self.volume_change_timer)
            self.volume_change_timer = None
        self.is_currently_ducked = False
        self.original_volume_before_duck = None
        # Proceed to next song
        self.master.after(0, self._play_next_media_or_auto_next)

    # ... (_play_next_media_or_auto_next remains the same) ...
    # ... (load_icons, _load_icon remain the same) ...

    def setup_styles(self):
        """Configure ttk styles for the application."""
        style = ttk.Style()
        style.theme_use("default")

        style_config = {
            "Light.TFrame": {"background": self.app_theme['BG_COLOR']},
            "Light.TLabel": {"background": self.app_theme['BG_COLOR'], "foreground": self.app_theme['FG_COLOR']},
            "Light.TButton": {
                "background": self.app_theme['BUTTON_COLOR'], "foreground": self.app_theme['BUTTON_FG_COLOR'],
                "relief": "flat", "borderwidth": 0, "highlightthickness": 0, "padding": 5, "font": ("Arial", 9)
            },
            "Light.TCheckbutton": {
                "background": self.app_theme['BG_COLOR'], "foreground": self.app_theme['FG_COLOR'],
                "relief": "flat", "borderwidth": 0, "highlightthickness": 0
            },
            "Light.Horizontal.TScale": {
                "background": self.app_theme['BG_COLOR'], "foreground": self.app_theme['FG_COLOR'],
                "troughcolor": "#d0d0d0", "sliderrelief": tk.FLAT, "troughrelief": tk.FLAT,
                "highlightthickness": 0, "bordercolor": self.app_theme['ACCENT_COLOR'],
                "sliderlength": 15, "gripcolor": self.app_theme['ACCENT_COLOR'], "thumbrelief": tk.RAISED
            },
            "Light.TCombobox": {
                "fieldbackground": self.app_theme['BG_COLOR'], "background": self.app_theme['BUTTON_COLOR'],
                "foreground": self.app_theme['BUTTON_FG_COLOR'], "arrowcolor": self.app_theme['BUTTON_FG_COLOR'],
                "bordercolor": self.app_theme['BG_COLOR'], "lightcolor": self.app_theme['BG_COLOR'],
                "darkcolor": self.app_theme['BG_COLOR'], "relief": "flat", "borderwidth": 2,
                "highlightthickness": 0, "padding": 5
            },
            "Light.Horizontal.TProgressbar": {
                "troughcolor": "#d0d0d0", "background": self.app_theme['ACCENT_COLOR'],
                "lightcolor": self.app_theme['ACCENT_COLOR'], "darkcolor": self.app_theme['ACCENT_COLOR'],
                "bordercolor": self.app_theme['BG_COLOR'], "borderwidth": 0, "relief": tk.FLAT
            },
            "Light.TNotebook": {
                "background": self.app_theme['BG_COLOR'], "borderwidth": 0, "highlightthickness": 0
            },
            "Light.TNotebook.Tab": {
                "background": self.app_theme['BUTTON_COLOR'], "foreground": self.app_theme['BUTTON_FG_COLOR'],
                "borderwidth": 0, "padding": [10, 5], "relief": "flat", "highlightthickness": 0
            },
             # --- Style for Spinbox ---
            "Light.TSpinbox": {
                 "fieldbackground": self.app_theme['BG_COLOR'], "background": self.app_theme['BUTTON_COLOR'],
                 "foreground": self.app_theme['FG_COLOR'], "arrowcolor": self.app_theme['FG_COLOR'],
                 "arrowsize": 10, "relief": "flat", "borderwidth": 1, "padding": 2
            },
            # --- Style for LabelFrame ---
            "Light.TLabelframe": {
                "background": self.app_theme['BG_COLOR'], "padding": [10, 5]
            },
            "Light.TLabelframe.Label": {
                "background": self.app_theme['BG_COLOR'], "foreground": self.app_theme['FG_COLOR']
            }
        }

        for style_name, config in style_config.items():
            style.configure(style_name, **config)

        style_map_config = {
            "Light.TButton": {
                "background": [("active", self.app_theme['ACTIVE_BG_COLOR'])],
                "foreground": [("active", self.app_theme['ACTIVE_FG_COLOR'])]
            },
            "Light.TCheckbutton": {
                "background": [("active", self.app_theme['ACTIVE_BG_COLOR'])],
                "foreground": [("active", self.app_theme['ACTIVE_FG_COLOR'])]
            },
            "Light.TCombobox": {
                "fieldbackground": [("readonly", self.app_theme['BG_COLOR'])],
                "selectbackground": [("readonly", self.app_theme['BG_COLOR'])],
                "selectforeground": [("readonly", self.app_theme['FG_COLOR'])],
                "background": [("active", self.app_theme['ACTIVE_BG_COLOR'])],
                "foreground": [("active", self.app_theme['ACTIVE_FG_COLOR'])]
            },
            "Light.TNotebook.Tab": {
                "background": [("selected", self.app_theme['ACTIVE_BG_COLOR'])],
                "foreground": [("selected", self.app_theme['ACTIVE_FG_COLOR'])],
                "expand": [("selected", [1, 1, 1, 1])]
            },
            "Light.TSpinbox": {
                "background": [("active", self.app_theme['ACTIVE_BG_COLOR']),
                               ("focus", self.app_theme['ACTIVE_BG_COLOR'])],
                "foreground": [("active", self.app_theme['ACTIVE_FG_COLOR']),
                               ("focus", self.app_theme['ACTIVE_FG_COLOR'])]
            }
        }

        for style_name, map_config in style_map_config.items():
            style.map(style_name, **map_config)


    # ... (open_settings_window remains similar, calls create_settings_frame) ...

    def close_settings_window(self):
        """Close the settings window and save settings."""
        if hasattr(self, 'settings_window') and self.settings_window:
            # Validate spinbox values before saving (optional but good practice)
            try:
                _ = self.duck_volume_level.get()
                _ = self.duck_fade_duration_ms.get()
            except tk.TclError:
                messagebox.showerror("Settings Error", "Invalid numeric value entered for ducking settings.")
                return # Don't close if invalid

            self.ignore_list = [line.strip() for line in self.ignore_list_text.get("1.0", tk.END).strip().split('\n') if line.strip()]
            self.save_settings()
            self.start_audio_detection() # Restart detection if ignore list changed
            self.settings_window.destroy()
            self.settings_window = None

    def toggle_mute(self):
        """Toggle mute/unmute and update volume icon, interacts with ducking."""
        # Cancel any ongoing fade first
        if self.volume_change_timer:
            self.master.after_cancel(self.volume_change_timer)
            self.volume_change_timer = None
            # Decide state based on target: if restoring, finish restore; if ducking, stay ducked conceptually
            if not self.is_currently_ducked and self.original_volume_before_duck is not None:
                 # If it was restoring, finish setting the intended volume
                 self.volume = self.original_volume_before_duck
                 self.original_volume_before_duck = None
                 # Don't set player volume yet, handle below

        if self.media_player.audio_get_volume() == 0: # Currently muted, unmute requested
             target_vol = self.volume # Restore to user's intended volume
             if self.is_currently_ducked: # If should be ducked, restore to ducked level instead
                 target_vol = self.duck_volume_level.get()

             self.media_player.audio_set_volume(target_vol)
             self.volume_slider.set(target_vol) # Update slider to reflect actual level
             self.volume_icon_label.config(image=self.volume_icon)
             # Note: We don't clear is_currently_ducked here. If external audio is still playing,
             # check_audio_state will keep it ducked or re-duck if needed.
        else: # Currently playing, mute requested
            # No need to store self.volume again, it's the user's intended level
            self.media_player.audio_set_volume(0)
            self.volume_slider.set(0)
            self.volume_icon_label.config(image=self.volume_mute_icon)

        # No need to save settings here, mute is temporary state, self.volume holds user preference

    # ... (toggle_tray_setting, start_in_tray_startup, _create_tray_menu, hide_to_tray, run_tray_icon, show_from_tray, restore_window, toggle_play_pause_from_tray, _toggle_play_pause_and_update_tray remain the same) ...
    # ... (get_external_audio_state, get_audio_processes, monitor_audio remain the same) ...
    # ... (play_first_song, toggle_run_at_startup, add_to_startup, remove_from_startup remain the same) ...

    def set_volume(self, volume_str):
        """
        Set the volume of the media player based on slider/shortcut.
        This is the USER INTENDED volume. Handles interaction with ducking.
        """
        try:
            new_volume = int(float(volume_str))
            new_volume = max(0, min(100, new_volume))
        except ValueError:
            return # Ignore invalid input

        # User is manually changing volume, override any active ducking/restoration
        if self.volume_change_timer:
            self.master.after_cancel(self.volume_change_timer)
            self.volume_change_timer = None
            self.write_debug("Manual volume change interrupted fade.")

        self.volume = new_volume # Store user's preference
        self.is_currently_ducked = False # Manual change resets ducked state
        self.original_volume_before_duck = None

        if self.media_player.get_media():
            # Set player volume immediately only if not muted
            if self.media_player.audio_get_volume() != 0: # Check if player is currently muted
                 self.media_player.audio_set_volume(self.volume)

        # Update icon based on the *intended* volume, unless muted (handled by toggle_mute)
        if self.media_player.audio_get_volume() != 0:
             self.volume_icon_label.config(image=self.volume_mute_icon if self.volume == 0 else self.volume_icon)

        # Don't save settings on every drag, only when necessary (e.g., window close, explicit save)
        # self.save_settings() # Removed for performance

    # ... (_read_metadata, add_music, _update_ui_after_add_music remain the same) ...

    def play_song(self, song_path):
        """Play the song at the given path."""
        self.write_debug(f"Playing song: {song_path}")
        try:
            media = self.instance.media_new(song_path)
            self._set_media_and_play(media, song_path)
        except Exception as e:
            logging.error(f"Error playing song: {e}")
            self.write_debug(f"Error playing song: {e}")
            self.current_song_label.config(text="Error playing song")

    def _set_media_and_play(self, media, song_path):
        """Set media to player and start playing, update UI, consider ducking state."""
        if self.media_player.get_media():
            self.media_player.stop()
            self.media_player.get_media().release()

        self.media_player.set_media(media)
        self.media_player.play()
        self.is_paused = False # User pause reset
        self.pause_button.config(image=self.pause_icon)
        if self.tray_icon:
            self.tray_icon.menu = self._create_tray_menu()
            self.tray_icon.update_menu()

        try:
            playlist = self.playlists[self.current_playlist_name]
            song_index = next((index for (index, d) in enumerate(playlist) if d["path"] == song_path), None)
            if song_index is not None:
                self.current_song_index = song_index
            else:
                self.current_song_index = 0
                self.write_debug(f"Song {song_path} index not found, reset to 0.")
        except ValueError:
            self.write_debug(f"Song {song_path} not found in current playlist")
            self.current_song_index = 0

        self.current_playing_index = self.current_song_index
        self.current_song_path = song_path

        # --- Set initial volume considering duck state ---
        target_volume = self.volume # Default to user's intended volume
        if self.is_currently_ducked:
             target_volume = self.duck_volume_level.get()
             self.write_debug(f"New song started while ducked, setting volume to {target_volume}")
        # Apply immediately, no fade needed here, check_audio_state handles fades
        self.media_player.audio_set_volume(target_volume)
        # Also update slider to match initial playing volume
        self.volume_slider.set(target_volume)
        # --- End volume setting ---

        self.progress_bar["value"] = 0
        self.elapsed_time_label.config(text="00:00")
        self.remaining_time_label.config(text="00:00")
        self.progress_bar_active = False

        # Parse media *after* setting it and *before* getting duration
        if not media.is_parsed():
             media.parse_with_options(0, 0) # Use parse_with_options or ensure parse happens
             # Add a small delay if needed for parsing to complete, though usually not required
             # time.sleep(0.05) # Example, adjust if needed

        # Retry getting duration after parse
        retry_count = 0
        while retry_count < 5 and (self.media_duration := media.get_duration()) <= 0:
            time.sleep(0.05) # Small delay before retrying
            media.parse_with_options(0,0) # Re-parse just in case
            retry_count += 1
            if retry_count > 1:
                 self.write_debug(f"Retrying get_duration ({retry_count})...")

        if self.media_duration <= 0:
            self.write_debug(f"Warning: Could not get duration for {song_path}")
            self.media_duration = 0 # Ensure it's 0 if invalid


        self.update_progress_bar() # Start progress updates
        self._update_song_label(song_path)
        self.update_song_list_selection()
        self._preload_next_song()

    # ... (_update_song_label, update_progress_bar remain the same) ...
    # ... (play_selected_song, update_song_list_selection remain the same) ...

    def pause_song(self):
        """Pause or resume playback (user-initiated) and update button."""
        if not self.current_song_path and not self.media_player.get_media():
            return # Do nothing if no song is loaded

        # User wants to pause/play, cancel any ducking fade operations
        if self.volume_change_timer:
            self.master.after_cancel(self.volume_change_timer)
            self.volume_change_timer = None
            self.write_debug("User play/pause interrupted fade.")
            # Restore intended volume if fade was interrupted, respecting duck state
            current_actual_vol = self.volume if not self.is_currently_ducked else self.duck_volume_level.get()
            self.media_player.audio_set_volume(current_actual_vol)
            self.volume_slider.set(current_actual_vol)

        if self.media_player.is_playing():
            self.media_player.pause()
            self.is_paused = True # Set user pause flag
            self.pause_button.config(image=self.play_icon)
            if self.tray_icon: self.tray_icon.update_menu() # Update tray immediately
        elif self.media_player.get_media(): # It's paused or stopped but media loaded
            # Check if *player* is paused (might be due to ducking or user)
            # If user explicitly paused (self.is_paused is True), then unpause
            if self.is_paused:
                 self.media_player.play()
                 self.is_paused = False
                 self.pause_button.config(image=self.pause_icon)
                 if self.tray_icon: self.tray_icon.update_menu()
            # If it wasn't user-paused, it might be stopped or paused by ducking logic.
            # Let check_audio_state handle resuming from ducking pause if needed.
            # If stopped, play() starts it. If paused by ducking, play() resumes.
            elif not self.media_player.is_playing():
                 self.media_player.play() # Attempt to play
                 self.is_paused = False # Clear user pause flag
                 self.pause_button.config(image=self.pause_icon)
                 if self.tray_icon: self.tray_icon.update_menu()

    # ... (next_song, next_song_auto, _play_next_shuffled_song remain the same) ...
    # ... (prev_song, _play_previous_shuffled_song remain the same) ...
    # ... (shuffle_playlist, _generate_shuffled_indices remain the same) ...
    # ... (delete_songs, _delete_songs_thread, _update_ui_after_delete_songs remain the same) ...
    # ... (rename_playlist, _close_rename_dialog, _rename_playlist_handler remain the same) ...
    # ... (rename_song, _reset_rename_playing_song_flag, _close_song_rename_dialog, _rename_song_handler remain the same) ...

    def save_settings(self):
        """Save application settings to JSON files. Runs in a thread."""
        conf_settings = {
            'current_playlist': self.current_playlist_name,
            'volume': self.volume,
            'run_at_startup': self.run_at_startup.get(),
            'is_in_tray': self.is_in_tray.get(),
            # --- Ducking settings ---
            'auto_duck_enabled': self.auto_duck_enabled.get(),
            'duck_volume_level': self.duck_volume_level.get(),
            'duck_fade_duration_ms': self.duck_fade_duration_ms.get(),
            # --- End Ducking settings ---
            'ignore_list': self.ignore_list,
            'startup_playlist_name': self.startup_playlist_name.get(),
            'shuffle_enabled': self.shuffle_enabled.get(),
            'loop_type': self.loop_type.get()
        }
        mem_settings = {
            'playlists': self.playlists,
        }
        def _save_settings_thread():
            """Thread function to save settings to files."""
            try:
                with open(CONF_SETTINGS_FILE, 'w') as f:
                    json.dump(conf_settings, f, indent=4)
                with open(MEM_SETTINGS_FILE, 'w') as f:
                    json.dump(mem_settings, f, indent=4, default=list) # default=list might not be needed anymore
            except Exception as e:
                logging.error(f"Error saving settings: {e}")
        threading.Thread(target=_save_settings_thread, daemon=True).start()


    def load_settings(self):
        """Load application settings from JSON files."""
        mem_settings_exists = os.path.exists(MEM_SETTINGS_FILE)
        conf_settings_exists = os.path.exists(CONF_SETTINGS_FILE)

        if mem_settings_exists and conf_settings_exists:
            self._load_new_settings()
        else:
            self.write_debug("No settings file found, using default settings.")
            # Set defaults explicitly before saving
            self.volume = 70
            self.auto_duck_enabled.set(DEFAULT_AUTO_DUCK_ENABLED)
            self.duck_volume_level.set(DEFAULT_DUCK_VOLUME_LEVEL)
            self.duck_fade_duration_ms.set(DEFAULT_DUCK_FADE_DURATION_MS)
            self.save_settings() # Save defaults if files don't exist

        # Update UI elements that depend on loaded settings if they exist
        if hasattr(self, 'volume_slider'):
             self.volume_slider.set(self.volume)
        if hasattr(self, 'ignore_list_text'):
            self.ignore_list_text.delete("1.0", tk.END)
            self.ignore_list_text.insert(tk.END, "\n".join(self.ignore_list))
        if hasattr(self, 'startup_playlist_dropdown'):
            self.startup_playlist_dropdown.set(self.startup_playlist_name.get())
        if hasattr(self, 'loop_type_dropdown'):
            self.loop_type_dropdown.set(self.loop_type.get())
        # No need to update ducking UI here, it's done during UI creation


    def _load_new_settings(self):
        """Load settings from the new FMem.json and FConf.json files."""
        try:
            with open(CONF_SETTINGS_FILE, 'r') as f:
                conf_settings = json.load(f)
                self.current_playlist_name = conf_settings.get('current_playlist', "default")
                self.volume = conf_settings.get('volume', 70) # Load intended volume
                self.run_at_startup.set(conf_settings.get('run_at_startup', False))
                self.is_in_tray.set(conf_settings.get('is_in_tray', False))
                # --- Ducking settings ---
                self.auto_duck_enabled.set(conf_settings.get('auto_duck_enabled', DEFAULT_AUTO_DUCK_ENABLED))
                self.duck_volume_level.set(conf_settings.get('duck_volume_level', DEFAULT_DUCK_VOLUME_LEVEL))
                self.duck_fade_duration_ms.set(conf_settings.get('duck_fade_duration_ms', DEFAULT_DUCK_FADE_DURATION_MS))
                 # --- End Ducking settings ---
                self.ignore_list = conf_settings.get('ignore_list', DEFAULT_IGNORE_LIST.copy())
                self.startup_playlist_name.set(conf_settings.get('startup_playlist_name', "None"))
                self.shuffle_enabled.set(conf_settings.get('shuffle_enabled', False))
                self.loop_type.set(conf_settings.get('loop_type', DEFAULT_LOOP_TYPE))

            if hasattr(self, 'shuffle_button'):
                self.shuffle_button.config(image=self.shuffle_on_icon if self.shuffle_enabled.get() else self.shuffle_icon)

        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.warning(f"Config settings file error: {e}. Using defaults.")
            self.write_debug(f"Config settings file error: {e}. Using defaults.")
            # Reset to defaults if file is bad
            self.volume = 70
            self.auto_duck_enabled.set(DEFAULT_AUTO_DUCK_ENABLED)
            self.duck_volume_level.set(DEFAULT_DUCK_VOLUME_LEVEL)
            self.duck_fade_duration_ms.set(DEFAULT_DUCK_FADE_DURATION_MS)

        except Exception as e:
            logging.error(f"Error loading config settings: {e}")
            self.write_debug(f"Error loading config settings: {e}")

        # Load playlists in a separate thread (remains the same)
        def _load_mem_settings_thread():
             # ... (playlist loading logic is unchanged) ...
            try:
                with open(MEM_SETTINGS_FILE, 'r') as f:
                    mem_settings = json.load(f)
                    loaded_playlists = mem_settings.get('playlists', {"default": []})
                     # Migration logic (remains the same)
                    for playlist_name, playlist_content in loaded_playlists.items():
                        if isinstance(playlist_content, list) and playlist_content and isinstance(playlist_content[0], str):
                            migrated_playlist_data = []
                            for song_path in playlist_content:
                                metadata = self._read_metadata(song_path)
                                migrated_playlist_data.append({'path': song_path, 'metadata': metadata})
                            loaded_playlists[playlist_name] = migrated_playlist_data
                    self.playlists = loaded_playlists
                    # Update UI in main thread after loading
                    self.master.after(0, self.update_playlist_dropdown)
                    self.master.after(0, self.update_song_list_ui)


            except (FileNotFoundError, json.JSONDecodeError):
                 self.write_debug("Memory settings file not found or corrupted, using default memory settings.")
            except Exception as e:
                logging.error(f"Error loading memory settings: {e}")
                self.write_debug(f"Error loading memory settings: {e}")
        threading.Thread(target=_load_mem_settings_thread, daemon=True).start()

    # --- Ducking Logic ---

    def check_audio_state(self):
        """Periodically check external audio state and trigger volume ducking/restoration."""
        try:
            if not self.auto_duck_enabled.get() or self.is_paused: # Don't duck if user paused
                # If ducking was active but is now disabled or user paused, restore volume
                if self.is_currently_ducked and self.original_volume_before_duck is not None:
                    self.write_debug("Auto-duck disabled or user paused, restoring volume.")
                    self._start_smooth_volume_change(self.original_volume_before_duck, self._restoration_complete)
                    # State reset happens in _restoration_complete or if interrupted
                self.master.after(AUDIO_CHECK_INTERVAL, self.check_audio_state)
                return

            external_active = self.get_external_audio_state()

            if external_active:
                # External audio detected, start ducking if not already ducked and playing
                if not self.is_currently_ducked and self.media_player.is_playing():
                    current_vol = self.media_player.audio_get_volume()
                    target_duck_vol = self.duck_volume_level.get()
                    if current_vol > target_duck_vol: # Only duck if current volume is higher
                        self.write_debug(f"External audio detected. Ducking volume from {current_vol} to {target_duck_vol}...")
                        self.original_volume_before_duck = current_vol # Store before starting fade
                        self.is_currently_ducked = True # Set flag before starting fade
                        self._start_smooth_volume_change(target_duck_vol, self._ducking_complete)
                    elif not self.volume_change_timer: # Already at or below target, ensure flag is set
                         self.is_currently_ducked = True
                         self.original_volume_before_duck = current_vol # Store current as original

            else:
                # External audio stopped, restore volume if currently ducked
                if self.is_currently_ducked:
                    if self.original_volume_before_duck is not None:
                        current_vol = self.media_player.audio_get_volume()
                        target_restore_vol = self.original_volume_before_duck
                        if current_vol < target_restore_vol: # Only restore if below original
                             self.write_debug(f"External audio stopped. Restoring volume from {current_vol} to {target_restore_vol}...")
                             # Don't reset is_currently_ducked yet, do it in callback
                             self._start_smooth_volume_change(target_restore_vol, self._restoration_complete)
                        elif not self.volume_change_timer: # Already at or above target, reset state
                             self.is_currently_ducked = False
                             self.original_volume_before_duck = None
                    else:
                         # Should not happen if ducking started correctly, but reset state just in case
                         self.is_currently_ducked = False
                         self.original_volume_before_duck = None # Ensure clean state

        except Exception as e:
             logging.error(f"Error in check_audio_state: {e}")
             self.write_debug(f"Error in check_audio_state: {e}")
        finally:
             # Schedule next check regardless of errors in this cycle
             self.master.after(AUDIO_CHECK_INTERVAL, self.check_audio_state)


    def _start_smooth_volume_change(self, target_volume, completion_callback=None):
        """Initiates a smooth volume change towards the target."""
        if self.volume_change_timer: # Cancel any existing fade
            self.master.after_cancel(self.volume_change_timer)
            self.volume_change_timer = None

        current_volume = self.media_player.audio_get_volume()
        target_volume = max(0, min(100, int(target_volume))) # Clamp target

        if current_volume == target_volume:
            self.write_debug(f"Volume already at target ({target_volume}). No fade needed.")
            if completion_callback:
                completion_callback() # Call completion immediately if already at target
            return

        duration_ms = self.duck_fade_duration_ms.get()
        if duration_ms <= 0: # Instant change if duration is 0 or less
             self.media_player.audio_set_volume(target_volume)
             self.volume_slider.set(target_volume)
             self.write_debug(f"Instant volume change to {target_volume}.")
             if completion_callback:
                 completion_callback()
             return

        delta_volume = target_volume - current_volume
        # Calculate steps based on interval, ensure at least one step
        num_steps = max(1, duration_ms // VOLUME_FADE_STEP_INTERVAL)
        step_value = delta_volume / num_steps # Can be float

        # Clamp step_value magnitude to avoid huge jumps if duration is tiny
        # max_step = 10 # Example limit
        # step_value = max(-max_step, min(max_step, step_value))
        # if abs(step_value) < 0.1: # Prevent infinite loops with tiny steps
        #     step_value = 0.1 * (1 if delta_volume > 0 else -1)

        self._smooth_volume_change_step(target_volume, step_value, completion_callback)

    def _smooth_volume_change_step(self, target_volume, step_value, completion_callback):
        """Performs one step of the volume fade and schedules the next."""
        current_volume = self.media_player.audio_get_volume()
        next_volume = current_volume + step_value

        # Check if target is reached or overshot
        is_increasing = step_value > 0
        reached_target = False
        if is_increasing and next_volume >= target_volume:
            next_volume = target_volume
            reached_target = True
        elif not is_increasing and next_volume <= target_volume:
            next_volume = target_volume
            reached_target = True

        # Clamp volume just in case
        next_volume = max(0, min(100, int(round(next_volume))))

        # Set player volume and update slider
        if self.media_player.get_media() and self.media_player.audio_get_volume() != 0: # Don't change if muted
            self.media_player.audio_set_volume(next_volume)
            self.volume_slider.set(next_volume) # Update slider visually

        if reached_target:
            self.write_debug(f"Smooth volume change reached target: {target_volume}")
            self.volume_change_timer = None
            if completion_callback:
                completion_callback()
        else:
            # Schedule next step
            self.volume_change_timer = self.master.after(VOLUME_FADE_STEP_INTERVAL,
                                                          self._smooth_volume_change_step,
                                                          target_volume, step_value, completion_callback)

    def _ducking_complete(self):
        """Callback function when volume ducking fade finishes."""
        self.write_debug("Volume ducking fade complete.")
        # State (is_currently_ducked = True) remains set

    def _restoration_complete(self):
        """Callback function when volume restoration fade finishes."""
        self.write_debug("Volume restoration fade complete.")
        # Reset state flags now that restoration is done
        self.is_currently_ducked = False
        self.original_volume_before_duck = None

    # --- End Ducking Logic ---

    # ... (start_audio_detection remains the same) ...
    # ... (on_minimize, on_restore, on_close, on_close_tray remain the same) ...

    def cleanup_and_exit(self):
        """Cleanup resources and exit the application."""
        # Attempt to save settings one last time
        try:
             self.save_settings()
             # Give save thread a moment
             time.sleep(0.1)
        except Exception as e:
             logging.error(f"Error during final save: {e}")

        if self.volume_change_timer:
            self.master.after_cancel(self.volume_change_timer) # Stop any fades

        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None

        # Stop audio detection thread gracefully if possible (though daemon should exit)
        # No explicit stop needed for daemon thread, but good practice if it were non-daemon

        # Stop VLC
        if self.media_player:
            if self.media_player.get_media():
                self.media_player.stop()
                # Explicitly release media to prevent potential hangs
                current_media = self.media_player.get_media()
                if current_media:
                    current_media.release()
                    self.media_player.set_media(None) # Detach media
            self.media_player.release()
            self.media_player = None
        if self.next_media:
            self.next_media.release()
            self.next_media = None
        if self.instance:
            self.instance.release()
            self.instance = None


        self.toggle_debug_window(force_destroy=True) # Close debug window

        # Destroy Tkinter root
        try:
             if self.master:
                  self.master.quit()
                  self.master.destroy()
        except tk.TclError:
             pass # Ignore errors if window already gone
        except Exception as e:
             logging.error(f"Error during Tkinter destroy: {e}")

        # Explicitly exit process
        sys.exit(0)


    # ... (create_new_playlist, _add_new_playlist_handler, delete_current_playlist remain the same) ...
    # ... (switch_playlist, update_playlist_dropdown, update_song_list_ui, _update_song_list_ui_callback remain the same) ...
    # ... (toggle_debug_window, _hide_debug_window, write_debug, _on_main_destroy remain the same) ...
    # ... (_preload_next_song, _clear_preload_media remain the same) ...


if __name__ == '__main__':
    root = tk.Tk()
    try:
        # Check for VLC instance early
        vlc_instance_test = vlc.Instance()
        vlc_instance_test.release()
    except Exception as e:
        messagebox.showerror("VLC Error", f"VLC media player library not found or failed to initialize.\nError: {e}\nPlease install VLC media player and ensure its libraries are accessible.\nDownload: https://www.videolan.org/vlc/")
        root.destroy()
        sys.exit(1) # Use non-zero exit code for error

    player = FNote(root)
    root.mainloop()

# --- END OF FILE FNote.py ---