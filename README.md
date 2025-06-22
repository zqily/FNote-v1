# FNote

![fnote1](https://github.com/user-attachments/assets/99bcc2e6-5040-4aca-873d-8be87e0215f0)

**FNote** is a lightweight, minimalist music player for Windows with a killer feature: it intelligently pauses your music when other applications start making noise. Whether you're jumping into a game, watching a video, or joining a voice call, FNote gets out of the way, ensuring you never have to manually pause your tunes again.

Built with Python and Tkinter, it's designed to be a simple, "set it and forget it" companion for your daily workflow and entertainment.

## ✨ Key Features

*   **Intelligent Auto-Pause**: Automatically pauses playback when it detects audio from other applications (games, web browsers, communication apps like Discord/Teams, etc.) and resumes when the other audio stops.
*   **Self-Contained Playlist Management**: Create multiple playlists. When you add songs, FNote copies them into a dedicated folder for that playlist, keeping your music organized and portable.
*   **Easy Playlist Sharing**: Export any playlist (songs and all) into a single `.zip` file. Simply drag-and-drop this file onto FNote on another computer to import the entire playlist.
*   **System Integration**:
    *   **Run on Startup**: Configure FNote to launch automatically when you log in to Windows.
    *   **Minimize to Tray**: Hides in the system tray instead of cluttering your taskbar.
*   **Lightweight & Simple UI**: A clean, no-frills interface that's easy to navigate.
*   **Standard Player Controls**: All the essentials are here: play/pause, next/previous, shuffle, loop modes (playlist, song, none), and volume control.
*   **Drag & Drop Song Reordering**: Easily change the order of songs within a playlist.
*   **Full Keyboard Shortcut Support**: Control every primary function without touching your mouse.
*   **Customizable Blacklist**: Have an app you want FNote to ignore? Add it to the blacklist in the settings.

## ⚙️ Requirements & Installation

FNote is designed for **Windows**.

### 1. Prerequisite: VLC Media Player
FNote uses the VLC engine for robust audio playback. You **must** have VLC Media Player installed on your system.

*   **[Download VLC Media Player (Official Site)](https://www.videolan.org/vlc/)**

Make sure you install the correct version for your system (64-bit is recommended).

### 2. Setting up FNote

You will need Python 3.8 or newer.

```bash
# 1. Clone the repository
git clone https://github.com/your-username/your-repository-name.git
cd your-repository-name

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
.\venv\Scripts\activate

# 3. Install the required Python packages
pip install -r requirements.txt
```

#### `requirements.txt`
If a `requirements.txt` file is not included, create one with the following content:
```
python-vlc
tinytag
pystray
Pillow
winshell
psutil
pycaw
comtypes
```

### 3. Running the Application
Once the dependencies are installed, you can run FNote with:
```bash
python FNote.py
```
You can also import a playlist file directly from the command line:
```bash
python FNote.py "C:\path\to\my_exported_playlist.zip"
```

## 🚀 How It Works

### Auto-Pause Explained
FNote actively listens to the Windows Audio Mixer. When it sees an application that isn't on its `ignore_list` (like FNote itself, or system sounds) producing audio, it triggers a pause. Once that application goes silent for a brief moment, FNote resumes your music. You can customize the list of ignored applications in `Settings -> Player`.

### Playlist Management
FNote takes a self-contained approach.
*   When you create a new playlist (e.g., "Workout"), a corresponding folder is created inside the `playlists` directory.
*   When you add songs to the "Workout" playlist, the audio files are **copied** into the `playlists/Workout` folder.
*   This means your original files are untouched, and the playlist is entirely portable. Deleting a playlist from FNote also deletes its associated folder and all the songs within it.

## ⌨️ Keyboard Shortcuts

| Key(s)           | Action                  |
| ---------------- | ----------------------- |
| `Space`          | Toggle Play / Pause     |
| `Down` or `s`    | Next Song               |
| `Up` or `w`      | Previous Song           |
| `Right` or `d`   | Volume Up (+5)          |
| `Left` or `a`    | Volume Down (-5)        |
| `Delete`         | Delete Selected Song(s) |
| `Ctrl` + `s`     | Toggle Shuffle          |
| `F2`             | Rename Selected Song    |


## 🏗️ Building from Source

You can package FNote into a single `.exe` file using PyInstaller.

1.  Make sure PyInstaller is installed: `pip install pyinstaller`
2.  Run the following command from the project's root directory:

```bash
pyinstaller --onefile --windowed --add-data "assets;assets" --icon="assets/icon.ico" FNote.py
```
This will create a `dist` folder containing `FNote.exe`, which can be run on any Windows machine (that has VLC installed).

## 🤝 Contributing

Contributions are welcome! If you have ideas for new features, bug fixes, or improvements, feel free to fork the repository, make your changes, and submit a pull request.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
