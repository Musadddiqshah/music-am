#!/data/data/com.termux/files/usr/bin/bash
# music-am quick installer for Termux
set -e

echo "🎵 music-am installer"
echo "────────────────────"

echo "📦 Installing system packages..."
pkg install -y python mpv

echo "🐍 Installing Python packages..."
pip install --upgrade pip
pip install python-mpv mutagen

echo "📁 Creating config directory..."
mkdir -p ~/.config/music-am

if [ ! -f ~/.config/music-am/config.toml ]; then
    if [ -f config.toml.example ]; then
        cp config.toml.example ~/.config/music-am/config.toml
    else
        cat > ~/.config/music-am/config.toml <<'EOF'
[general]
root = "/sdcard/Music"

[player]
volume_start = 100

[ui]
theme = "dracula"
EOF
    fi
    echo "✅ Config created: ~/.config/music-am/config.toml"
    echo "   Edit the 'root' to match your music folder."
fi

echo ""
echo "✅ Done!"
echo ""
echo "Run the player with:"
echo "  python music-am.py"
