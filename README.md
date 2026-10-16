# music Player v2 🎵

A fast, keyboard-driven terminal music player for **Termux** (Android) and Linux, built with Python + curses + mpv.

![Platform](https://img.shields.io/badge/platform-Termux%20%7C%20Linux-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

- 🎨 **28 color themes** (ocean, dracula, cyberpunk, matrix, gruvbox, nord, ...)
- 🎛️ **17 equalizer presets** (bass, vocal, rock, jazz, EDM, hiphop, ...)
- 📚 **Library browser** — Folders, Recent, Playlists, Favorites, Queue, Stats
- 🔍 **Instant search** across filename / title / artist / album
- ⏸️ **Fade in/out** on play/pause, next/prev — smooth transitions
- 🌙 **Sleep timer** (15/30/60 min or custom)
- 💾 **Session restore** — queue and position persist across runs
- ♥️ **Favorites** — heart your favorite tracks
- 📝 **Lyrics** support (`.lrc` files) with synced highlight
- 🎯 **Resume playback** — remembers last position per track
- ⚡ **Background library scan** with JSON cache
- 🖥️ **Clean TUI** with Nerd Font icons

## 📦 Installation

### Termux (Android)

```bash
pkg install python mpv
pip install python-mpv mutagen

git clone https://https://github.com/Musadddiqshah/music-am.git
cd music-am

python music-am.py
