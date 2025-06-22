# FNote - The Smart Music Player

![fnote1](https://github.com/user-attachments/assets/43a9d059-db2e-4c78-a80e-502918682a44)


[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

**FNote** is a lightweight, intuitive music player for Windows with a killer feature: it automatically pauses your music when any other application starts making sound and resumes when it's quiet again. No more manually pausing your songs when you start a game, join a video call, or watch a YouTube video!

Built with Python and Tkinter, FNote is designed to be a simple, powerful, and unobtrusive companion for your local music library.

## ✨ Key Features

-   **🎧 Automatic Pause & Resume:** The core feature. FNote listens for audio from other applications (games, browsers, communication apps like Discord/Teams) and intelligently pauses your music. When the other audio stops, FNote seamlessly resumes playback.
-   **📦 Robust Playlist Management:**
    -   Create, rename, and delete multiple playlists.
    -   Import and Export entire playlists (including the music files) as convenient `.zip` archives.
    -   Drag and drop songs within a playlist to reorder them.
-   **📂 Self-Contained Music Library:** When you add music to a playlist, FNote copies the files into a dedicated `playlists` folder, keeping your library organized and portable.
-   **▶️ Full Playback Control:**
    -   Standard controls: Play, Pause, Next, Previous.
    -   Shuffle and Repeat modes (Loop Playlist, Loop Song, No Loop).
    -   Clickable progress bar to seek through tracks.
-   **⌨️ Global Keyboard Shortcuts:** Control playback without focusing the window (Play/Pause, Next/Previous, Volume, etc.).
-   **⚙️ System Integration:**
    -   Option to minimize to the system tray.
    -   Option to run automatically on Windows startup.
-   **✍️ In-App File Management:** Rename or delete songs and their associated files directly from the playlist.
-   **🛠️ Configurable:**
    -   Customize the "ignore list" for the auto-pause feature.
    -   Choose a default playlist to load on startup.
-   **🐞 Debug Window:** An optional debug view to see what the audio detection module is doing in real-time.

## 💾 Installation

There are two ways to install FNote: the easy way for most users, and the developer way for those who want to run from source.

### For Users (Recommended)

This is the simplest method. The application is pre-packaged with all dependencies, including VLC.

1.  Go to the [**Releases**](https://github.com/zqily/FNote-v1/releases/) page of this repository.
2.  Download the `FNote.exe` file.
3.  Run `FNote.exe` to start the application. You can create a shortcut to this file on your desktop for easy access.

That's it! No further installation is required.

### For Developers (Running from Source)

If you want to run the application directly from the Python source code, follow these steps.

#### Prerequisites

1.  **Python 3.7+:** Make sure you have Python installed and added to your system's PATH. You can get it from [python.org](https://www.python.org/).
2.  **VLC Media Player:** The application relies on the VLC engine for audio playback. **You must have the 64-bit version of VLC Media Player installed on your system.** You can download it from the [official VideoLAN website](https://www.videolan.org/vlc/).

#### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repository.git
    cd your-repository
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python FNote.py
    ```

## 🚀 How to Use

1.  **Create a Playlist:** On first launch, you'll be in the "default" playlist. You can create a new one using the `+` button.
2.  **Add Music:** Click the `Add Music` button to select audio files from your computer. They will be copied into the current playlist's dedicated folder. You can also add music by importing an existing FNote playlist `.zip` file.
3.  **Play:** Double-click a song in the list to start playing.
4.  **Control:** Use the playback controls at the bottom of the window.
5.  **Reorder:** Click and drag a song to a new position in the playlist.
6.  **Configure:** Click the gear icon (`⚙️`) in the top right to access settings like "Run on Startup", "Hide to Tray", and the audio detection ignore list.

## 📦 Dependencies

The application relies on the following Python libraries:

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

## ⚙️ Configuration

FNote saves its configuration and playlists automatically in the same directory where it is run:
-   `FConf.json`: Stores user settings like volume, current playlist, and system integration options.
-   `FMem.json`: Stores the playlist data and paths to the music files.
-   `playlists/`: A directory containing sub-folders for each playlist, where the actual music files are stored.

This makes your entire FNote setup, including music and settings, fully portable.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
