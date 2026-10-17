#!/data/data/com.termux/files/usr/bin/python
# music-am v11 : Termux music player (curses + mpv)
# Config : ~/.config/music-am/config.toml
# State  : ~/.config/music-am/state.json
# Cache  : ~/.cache/music-am/library.json

import os, sys, re, copy, json, time, math, random, curses, threading, textwrap
import atexit, signal

os.environ.setdefault("ESCDELAY", "25")

try:
    import tomllib
except ImportError:
    import tomli as tomllib

try:
    import mpv
except ImportError:
    sys.exit("python-mpv was not found. Install it with: pip install python-mpv")

try:
    from mutagen import File as MutagenFile
except ImportError:
    MutagenFile = None

META_ON = MutagenFile is not None

CONFIG_PATH = os.path.expanduser("~/.config/music-am/config.toml")
STATE_PATH = os.path.expanduser("~/.config/music-am/state.json")
CACHE_DIR = os.path.expanduser("~/.cache/music-am")
INDEX_PATH = os.path.join(CACHE_DIR, "library.json")

FADE_SECONDS = 0.4
HISTORY_MAX = 200
RESUME_MIN = 10
RESUME_NEAR_END = 30

# ---------- themes (28) ----------
THEMES = {
    "ocean":    {"fg": 252, "on_accent": 16, "accent": 45,  "accent2": 75,  "accent3": 117, "sel_fg": 16, "sel_bg": 81,  "dim": 244, "warn": 215},
    "neon":     {"fg": 255, "on_accent": 16, "accent": 201, "accent2": 118, "accent3": 213, "sel_fg": 16, "sel_bg": 201, "dim": 240, "warn": 226},
    "sunset":   {"fg": 230, "on_accent": 16, "accent": 208, "accent2": 220, "accent3": 203, "sel_fg": 16, "sel_bg": 214, "dim": 242, "warn": 196},
    "nord":     {"fg": 153, "on_accent": 16, "accent": 110, "accent2": 109, "accent3": 180, "sel_fg": 16, "sel_bg": 152, "dim": 245, "warn": 174},
    "forest":   {"fg": 194, "on_accent": 16, "accent": 114, "accent2": 149, "accent3": 221, "sel_fg": 16, "sel_bg": 114, "dim": 242, "warn": 167},
    "rose":     {"fg": 225, "on_accent": 16, "accent": 211, "accent2": 183, "accent3": 218, "sel_fg": 16, "sel_bg": 211, "dim": 242, "warn": 203},
    "dracula":  {"fg": 255, "on_accent": 16, "accent": 141, "accent2": 117, "accent3": 212, "sel_fg": 16, "sel_bg": 141, "dim": 245, "warn": 210},
    "gold":     {"fg": 223, "on_accent": 16, "accent": 220, "accent2": 180, "accent3": 215, "sel_fg": 16, "sel_bg": 220, "dim": 242, "warn": 196},
    "mono":     {"fg": 252, "on_accent": 16, "accent": 250, "accent2": 245, "accent3": 255, "sel_fg": 16, "sel_bg": 255, "dim": 240, "warn": 203},
    "cyberpunk": {"fg": 255, "on_accent": 16, "accent": 202, "accent2": 51,  "accent3": 201, "sel_fg": 16, "sel_bg": 51,  "dim": 240, "warn": 196},
    "matrix":    {"fg": 46,  "on_accent": 16, "accent": 46,  "accent2": 40,  "accent3": 82,  "sel_fg": 16, "sel_bg": 40,  "dim": 28,  "warn": 196},
    "sakura":    {"fg": 225, "on_accent": 16, "accent": 218, "accent2": 224, "accent3": 211, "sel_fg": 16, "sel_bg": 224, "dim": 245, "warn": 203},
    "midnight":  {"fg": 189, "on_accent": 16, "accent": 63,  "accent2": 105, "accent3": 147, "sel_fg": 16, "sel_bg": 63,  "dim": 240, "warn": 210},
    "ember":     {"fg": 224, "on_accent": 16, "accent": 202, "accent2": 214, "accent3": 166, "sel_fg": 16, "sel_bg": 202, "dim": 240, "warn": 196},
    "aurora":    {"fg": 195, "on_accent": 16, "accent": 122, "accent2": 213, "accent3": 87,  "sel_fg": 16, "sel_bg": 122, "dim": 244, "warn": 210},
    "magma":     {"fg": 230, "on_accent": 16, "accent": 196, "accent2": 208, "accent3": 202, "sel_fg": 16, "sel_bg": 196, "dim": 240, "warn": 226},
    "ice":       {"fg": 195, "on_accent": 16, "accent": 159, "accent2": 195, "accent3": 117, "sel_fg": 16, "sel_bg": 159, "dim": 245, "warn": 210},
    "crimson":   {"fg": 224, "on_accent": 16, "accent": 160, "accent2": 196, "accent3": 203, "sel_fg": 16, "sel_bg": 160, "dim": 240, "warn": 226},
    "royal":     {"fg": 189, "on_accent": 16, "accent": 99,  "accent2": 141, "accent3": 177, "sel_fg": 16, "sel_bg": 99,  "dim": 245, "warn": 210},
    "mint":      {"fg": 194, "on_accent": 16, "accent": 121, "accent2": 157, "accent3": 85,  "sel_fg": 16, "sel_bg": 121, "dim": 244, "warn": 203},
    "lavender":  {"fg": 189, "on_accent": 16, "accent": 183, "accent2": 189, "accent3": 141, "sel_fg": 16, "sel_bg": 183, "dim": 245, "warn": 210},
    "coffee":    {"fg": 223, "on_accent": 16, "accent": 137, "accent2": 180, "accent3": 173, "sel_fg": 16, "sel_bg": 137, "dim": 240, "warn": 196},
    "copper":    {"fg": 223, "on_accent": 16, "accent": 173, "accent2": 180, "accent3": 209, "sel_fg": 16, "sel_bg": 173, "dim": 240, "warn": 196},
    "arctic":    {"fg": 195, "on_accent": 16, "accent": 117, "accent2": 153, "accent3": 159, "sel_fg": 16, "sel_bg": 117, "dim": 245, "warn": 210},
    "vaporwave": {"fg": 225, "on_accent": 16, "accent": 213, "accent2": 51,  "accent3": 219, "sel_fg": 16, "sel_bg": 213, "dim": 245, "warn": 203},
    "hacker":    {"fg": 46,  "on_accent": 16, "accent": 46,  "accent2": 118, "accent3": 154, "sel_fg": 16, "sel_bg": 46,  "dim": 28,  "warn": 196},
    "solarized": {"fg": 145, "on_accent": 16, "accent": 136, "accent2": 33,  "accent3": 166, "sel_fg": 16, "sel_bg": 136, "dim": 240, "warn": 160},
    "gruvbox":   {"fg": 223, "on_accent": 16, "accent": 172, "accent2": 142, "accent3": 109, "sel_fg": 16, "sel_bg": 172, "dim": 245, "warn": 167},
}
FALLBACK = {
    "fg": curses.COLOR_WHITE, "on_accent": curses.COLOR_BLACK, "accent": curses.COLOR_CYAN,
    "accent2": curses.COLOR_YELLOW, "accent3": curses.COLOR_MAGENTA,
    "sel_fg": curses.COLOR_BLACK, "sel_bg": curses.COLOR_CYAN,
    "dim": curses.COLOR_WHITE, "warn": curses.COLOR_RED,
}
REPEAT_MODES = ["off", "one", "all"]
SLEEP_STEPS = [0, 15, 30, 60]
TABS = ["All", "Library", "Settings"]

EQ_PRESETS = {
    # ============ BASIC ============
    "flat":       "",
    "treble":     "equalizer=f=8000:t=q:w=1:g=6",
    "vocal":      "equalizer=f=3000:t=q:w=1:g=4,equalizer=f=200:t=q:w=1:g=-3",

    # ============ 3D SPATIAL (HEADPHONES) ============
    "3d":         "haas,stereowiden=delay=20:feedback=0.3:crossfeed=0.35:drymix=0.75",
    "3d-hall":    "haas,stereowiden=delay=30:feedback=0.4:crossfeed=0.45:drymix=0.65,aecho=0.9:0.85:150:0.35",

    # ============ 8D ROTATION (HEADPHONES) ============
    "8d":         "apulsator=hz=0.1:mode=triangle:amount=1:offset_r=0.25,haas,stereowiden=delay=20:feedback=0.35:crossfeed=0.35:drymix=0.65,aecho=0.8:0.7:100:0.3",
    "8d-cinema":  "apulsator=hz=0.12:mode=triangle:amount=1:offset_r=0.3,haas,stereowiden=delay=35:feedback=0.45:crossfeed=0.55:drymix=0.45,aecho=0.9:0.8:200:0.35,aecho=0.8:0.7:120:0.25,aecho=0.7:0.6:60:0.15",
    "8d-vocal":   "apulsator=hz=0.08:mode=triangle:amount=0.8:offset_r=0.2,haas,equalizer=f=2500:t=q:w=1:g=3,equalizer=f=4000:t=q:w=1:g=2,stereowiden=delay=18:feedback=0.3:crossfeed=0.3:drymix=0.7",

    # ============ LO-FI ============
    "lofi":       "equalizer=f=60:t=q:w=1:g=4,equalizer=f=250:t=q:w=1:g=2,equalizer=f=3000:t=q:w=1:g=-3,equalizer=f=8000:t=q:w=1:g=-4",
    "lofi-vinyl": "equalizer=f=60:t=q:w=1:g=5,equalizer=f=250:t=q:w=1:g=2,equalizer=f=3000:t=q:w=1:g=-3,equalizer=f=9000:t=q:w=1:g=-5,lowpass=f=9000,aecho=0.8:0.75:50:0.3",
    "lofi-sleep": "equalizer=f=40:t=q:w=1:g=5,equalizer=f=150:t=q:w=1:g=3,equalizer=f=1000:t=q:w=1:g=-2,equalizer=f=3000:t=q:w=1:g=-5,equalizer=f=8000:t=q:w=1:g=-6,lowpass=f=7000,aecho=0.9:0.85:100:0.5",
    "lofi-8d":    "apulsator=hz=0.08:mode=sine:amount=0.9:offset_r=0.25,haas,equalizer=f=60:t=q:w=1:g=4,equalizer=f=250:t=q:w=1:g=2,equalizer=f=3000:t=q:w=1:g=-3,equalizer=f=8000:t=q:w=1:g=-4,stereowiden=delay=25:feedback=0.35:crossfeed=0.4:drymix=0.65,aecho=0.85:0.8:100:0.35,lowpass=f=10000",
}


SETTING_SPEC = [
    ("theme", "Theme", "choice", list(THEMES.keys())),
    ("volume_step", "Volume step", "int", (1, 20, 1)),
    ("seek_step", "Seek step (sec)", "int", (1, 30, 1)),
    ("shuffle", "Shuffle default", "bool", None),
    ("repeat", "Repeat default", "choice", REPEAT_MODES),
    ("eq", "Equalizer preset", "choice", list(EQ_PRESETS.keys())),
    ("show_folders", "Show folders (Library)", "bool", None),
    ("show_count", "Header: song count", "bool", None),
    ("show_total", "Header: total time", "bool", None),
    ("show_counts", "Folder song counts", "bool", None),
    ("show_meta", "Artist / title tags", "bool", None),
    ("resume", "Resume last position", "bool", None),
]

DEFAULTS = {
    "general": {
        "root": "/sdcard",
        "extensions": [".mp3", ".m4a", ".flac", ".opus", ".wav", ".aac", ".ogg"],
        "skip_dirs": [".thumbnails", "Android/data", "Android/obb", ".cache",
                      "WhatsApp/.Statuses", ".trash", "LOST.DIR"],
        "max_scan_depth": 6,
    },
    "player": {
        "volume_start": 100,
        "volume_max": 150,
        "volume_step": 5,
        "seek_step": 5,
        "shuffle": False,
        "repeat": "off",
        "eq": "flat",
        "extra_flags": ["--no-video", "--idle=yes", "--no-resume-playback"],
    },
    "ui": {
        "theme": "ocean",
        "show_folders": True,
        "show_count": False,
        "show_total": False,
        "show_counts": True,
        "show_meta": True,
        "resume": True,
    },
    "keys": {
        "search": "/", "play_all": "a", "shuffle": "s", "repeat": "r",
        "prev": "p", "next": "n", "jump_playing": "g", "write_playlist": "w",
        "bookmarks": "b", "help": "?", "mute": "m", "slower": "[", "faster": "]",
        "speed_reset": "0", "sleep": "t",
    },
}


def load_config():
    cfg = copy.deepcopy(DEFAULTS)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "rb") as f:
                user = tomllib.load(f)
            for sec, opts in user.items():
                if isinstance(opts, dict):
                    cfg.setdefault(sec, {}).update(opts)
        except Exception as e:
            print(f"config error: {e}", file=sys.stderr)
    return cfg


def load_state():
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_state(state):
    try:
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass


CFG = load_config()
STATE = load_state()


def build_settings():
    ui, pl = CFG["ui"], CFG["player"]
    s = {
        "theme": ui["theme"],
        "volume_step": int(pl["volume_step"]),
        "seek_step": int(pl["seek_step"]),
        "shuffle": bool(pl["shuffle"]),
        "repeat": pl["repeat"],
        "eq": pl.get("eq", "flat"),
        "show_folders": bool(ui["show_folders"]),
        "show_count": bool(ui["show_count"]),
        "show_total": bool(ui["show_total"]),
        "show_counts": bool(ui["show_counts"]),
        "show_meta": bool(ui["show_meta"]),
        "resume": bool(ui.get("resume", True)),
    }
    for k, v in STATE.get("settings", {}).items():
        if k in s:
            s[k] = v
    if s["theme"] not in THEMES:
        s["theme"] = "ocean"
    if s["repeat"] not in REPEAT_MODES:
        s["repeat"] = "off"
    if s["eq"] not in EQ_PRESETS:
        s["eq"] = "flat"
    return s


SET = build_settings()

ROOT = os.path.normpath(os.path.expanduser(CFG["general"]["root"]))
EXTS = tuple(e.lower() for e in CFG["general"]["extensions"])
SKIP_DIRS = list(CFG["general"]["skip_dirs"])
MAX_DEPTH = int(CFG["general"]["max_scan_depth"])

PL_VOL_START = int(CFG["player"]["volume_start"])
VOL_MAX = int(CFG["player"]["volume_max"])
EXTRA_FLAGS = list(CFG["player"]["extra_flags"])
K = CFG["keys"]

START_DIR = STATE.get("last_dir", ROOT)
if not (START_DIR == ROOT or START_DIR.startswith(ROOT + os.sep)) or not os.path.isdir(START_DIR):
    START_DIR = ROOT


def build_mpv_opts(flags):
    opts = {}
    for flag in flags:
        if not flag.startswith("--"):
            continue
        body = flag[2:]
        if body.startswith("no-"):
            key, val = body[3:], "no"
        elif "=" in body:
            key, val = body.split("=", 1)
        else:
            key, val = body, "yes"
        opts[key.replace("-", "_")] = val
    opts.setdefault("ytdl", "no")
    opts.setdefault("video", "no")
    opts.setdefault("idle", "yes")
    opts.setdefault("resume_playback", "no")
    opts.setdefault("volume_max", str(VOL_MAX))
    return opts


# ---------- file helpers ----------
def is_music(name):
    return name.lower().endswith(EXTS)


def is_playlist(name):
    return name.lower().endswith(".m3u")


def is_skipped(path):
    return any(s in path for s in SKIP_DIRS)


def read_m3u(path):
    songs = []
    base = os.path.dirname(path)
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if not os.path.isabs(line):
                    line = os.path.join(base, line)
                if os.path.exists(line):
                    songs.append(line)
    except Exception:
        pass
    return songs


def _tag(m, key):
    try:
        v = m.get(key)
        return str(v[0]).strip() if v else ""
    except Exception:
        return ""


def read_meta(path):
    info = {"t": "", "a": "", "al": "", "l": 0.0, "s": 0}
    try:
        info["s"] = os.path.getsize(path)
    except OSError:
        pass
    if META_ON:
        try:
            m = MutagenFile(path, easy=True)
            if m:
                info["t"] = _tag(m, "title")
                info["a"] = _tag(m, "artist")
                info["al"] = _tag(m, "album")
                length = getattr(getattr(m, "info", None), "length", None)
                if length:
                    info["l"] = float(length)
        except Exception:
            pass
    return info


def read_lrc(path):
    lrc_path = os.path.splitext(path)[0] + ".lrc"
    if not os.path.exists(lrc_path):
        return []
    out = []
    pat = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]")
    try:
        with open(lrc_path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.rstrip("\n")
                times = pat.findall(line)
                if not times:
                    continue
                text = pat.sub("", line).strip()
                for mm, ss in times:
                    t = int(mm) * 60 + float(ss)
                    out.append((t, text))
    except Exception:
        pass
    out.sort(key=lambda x: x[0])
    return out


def build_view(tracks, playlists):
    root = ROOT
    children, files, under, cnt, length, pls = {}, {}, {}, {}, {}, {}
    for path, info in tracks.items():
        d = os.path.dirname(path)
        files.setdefault(d, []).append(path)
        sec = float(info.get("l", 0) or 0)
        cur = d
        while True:
            under.setdefault(cur, []).append(path)
            cnt[cur] = cnt.get(cur, 0) + 1
            length[cur] = length.get(cur, 0.0) + sec
            if cur == root:
                break
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            children.setdefault(parent, set()).add(cur)
            cur = parent
    for p in playlists:
        pls.setdefault(os.path.dirname(p), []).append(p)

    def by_name(xs):
        return sorted(xs, key=lambda x: os.path.basename(x).lower())

    return {
        "children": {k: by_name(v) for k, v in children.items()},
        "files": {k: by_name(v) for k, v in files.items()},
        "pls": {k: by_name(v) for k, v in pls.items()},
        "under": under,
        "cnt": cnt,
        "len": length,
        "all_dirs": sorted((d for d in cnt if d != root), key=str.lower),
    }


class Library:
    def __init__(self):
        self.tracks = {}
        self.playlists = {}
        self.view = None
        self.version = 0
        self.scanning = False
        self.found = 0
        self.all_paths = []

    def _set(self, tracks, playlists):
        self.tracks = tracks
        self.playlists = playlists
        self.view = build_view(tracks, playlists)
        self.all_paths = sorted(tracks.keys(),
                                key=lambda p: list_label(p).lower())
        self.version += 1

    def load(self):
        try:
            with open(INDEX_PATH, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("root") != ROOT:
                return False
            self._set(data.get("tracks", {}), data.get("playlists", {}))
            return True
        except Exception:
            return False

    def save(self, tracks, playlists):
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            tmp = INDEX_PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"root": ROOT, "built": time.time(),
                           "tracks": tracks, "playlists": playlists}, f)
            os.replace(tmp, INDEX_PATH)
        except Exception:
            pass

    def start_scan(self):
        if self.scanning:
            return
        self.scanning = True
        self.found = 0
        threading.Thread(target=self._scan, daemon=True).start()

    def _scan(self):
        tracks, playlists = {}, {}
        try:
            for base, dirs, files in os.walk(ROOT):
                rel = os.path.relpath(base, ROOT)
                depth = 0 if rel == "." else rel.count(os.sep) + 1
                if depth >= MAX_DEPTH:
                    dirs[:] = []
                else:
                    dirs[:] = [d for d in dirs if not d.startswith(".")
                               and not is_skipped(os.path.join(base, d))]
                for f in files:
                    full = os.path.join(base, f)
                    if is_playlist(f):
                        playlists[full] = len(read_m3u(full))
                    elif is_music(f):
                        tracks[full] = read_meta(full)
                        self.found = len(tracks)
        except Exception:
            pass
        finally:
            self._set(tracks, playlists)
            self.save(tracks, playlists)
            self.scanning = False


LIB = Library()


def track_title(path):
    info = LIB.tracks.get(path, {})
    if SET["show_meta"] and info.get("t"):
        return info["t"]
    fname = os.path.splitext(os.path.basename(path))[0]
    return re.sub(r"^\s*\d{1,3}\s*[-._)]+\s*", "", fname).strip() or fname


def list_label(path):
    info = LIB.tracks.get(path, {})
    title = track_title(path)
    if SET["show_meta"] and info.get("a"):
        return f"{info['a']} - {title}"
    return title


def search_tracks(query):
    q = query.strip().lower()
    hits = []
    for path, info in list(LIB.tracks.items()):
        if q:
            hay = " ".join((os.path.basename(path), info.get("t", ""),
                            info.get("a", ""), info.get("al", ""))).lower()
            if q not in hay:
                continue
        hits.append(path)
    hits.sort(key=lambda p: (not list_label(p).lower().startswith(q), list_label(p).lower()))
    return hits


def fmt_time(t):
    if not t or t != t:
        return "00:00"
    t = int(t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def fmt_size(n):
    n = float(n or 0)
    for unit in ("B", "KB", "MB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


def info_rows(path):
    info = LIB.tracks.get(path, {})
    length = info.get("l", 0)
    return [
        ("Full name", os.path.basename(path)),
        ("Title", info.get("t") or track_title(path)),
        ("Artist", info.get("a") or "—"),
        ("Album", info.get("al") or "—"),
        ("Length", fmt_time(length) if length else "—"),
        ("Format", os.path.splitext(path)[1].lstrip(".").upper() or "—"),
        ("Size", fmt_size(info.get("s", 0))),
        ("Full path", path),
    ]


def safe(scr, y, x, s, attr=0):
    h, w = scr.getmaxyx()
    if y < 0 or y >= h or x < 0 or x >= w:
        return
    try:
        scr.addstr(y, x, s[:max(0, w - x - 1)], attr)
    except curses.error:
        pass


def init_theme(name):
    if not curses.has_colors():
        return
    t = THEMES.get(name, THEMES["ocean"]) if curses.COLORS >= 256 else FALLBACK
    pairs = {
        1: (t["on_accent"], t["accent"]),
        2: (t["accent"], -1),
        3: (t["sel_fg"], t["sel_bg"]),
        4: (t["accent2"], -1),
        5: (t["accent3"], -1),
        6: (t["dim"], -1),
        7: (t["accent"], -1),
        8: (t["dim"], -1),
        9: (t["on_accent"], t["accent2"]),
        10: (t["warn"], -1),
        11: (t["fg"], -1),
    }
    for pid, (fg, bg) in pairs.items():
        try:
            curses.init_pair(pid, fg, bg)
        except curses.error:
            pass


def read_key(scr):
    try:
        k = scr.get_wch()
    except curses.error:
        return None, ""
    if isinstance(k, str):
        return ord(k), k
    return k, ""


HELP = [
    " KEYS",
    " Tab / 1-3    All · Library · Settings",
    " ↑ ↓          move          PgUp/PgDn   jump 10",
    " g / G        top / bottom",
    " ENTER        open / play / change setting",
    " o            open folder in All (Library → Folders)",
    " ← / BKSP     back (Library) / decrease setting",
    " → / J / L    seek +5 / -30 / +30 sec",
    " SPACE        pause / play (with fade effect)",
    " n / p        next / prev (with fade effect)",
    " + / -        volume       m    mute",
    " [ / ] / 0    speed slower / faster / reset",
    " E            equalizer menu (popup)",
    " e            equalizer preset cycle",
    " t / T        sleep timer cycle / custom",
    " a            play visible list / current folder",
    " s / r        shuffle · repeat",
    " /            search         Esc = close",
    " i            track info     L    lyrics (.lrc)",
    " N            now-playing popup",
    " R            library rescan",
    " w / b        save .m3u · bookmarks",
    " d / c        queue: remove / clear",
    " x            delete track from disk (confirm)",
    " f            toggle favorite (current track)",
    " q            quit",
    "",
    " Press any key to close",
]


class App:
    def __init__(self, scr, player):
        self.scr = scr
        self.p = player
        self.tab = 0
        self.lib_view = 0
        self.folder_filter = None
        self.cur_dir = START_DIR
        self.idx = 0
        self.scroll = 0
        self.status = "Ready" if LIB.view else "Scanning library..."
        self.queue = []
        self.q_idx = -1
        self.current_path = ""
        self.user_vol = min(VOL_MAX, int(STATE.get("volume", PL_VOL_START)))
        self.shuffle = SET["shuffle"]
        self.repeat = SET["repeat"]
        self.eq = SET["eq"]
        self.sleep_i = 0
        self.sleep_until = 0.0
        self.last_play = 0.0
        self.fade = {"phase": None, "t0": 0.0, "dur": FADE_SECONDS, "action": None}
        self.bookmarks = list(STATE.get("bookmarks", []))
        self.favorites = set(STATE.get("favorites", []))
        self.help_open = False
        self.info_path = None
        self.lyrics_path = None
        self.lyrics_data = []
        self.lyrics_scroll = 0
        self.now_playing_open = False
        self.eq_menu_open = False
        self.eq_menu_idx = 0
        self.theme_menu_open = False
        self.theme_menu_idx = 0
        self.search_on = False
        self.focus = "input"
        self.query = ""
        self.s_hits = []
        self.s_ver = 0
        self.saved_pos = (0, 0)
        self._rkey = None
        self._rows = []
        self._was_scanning = False

        self.history = list(STATE.get("history", []))[:HISTORY_MAX]
        self.play_count = dict(STATE.get("play_count", {}))
        self.positions = dict(STATE.get("positions", {}))

        # Visualizer state
        self.viz_bars = 8
        self.viz_phase = 0.0
        self.viz_heights = [0.0] * self.viz_bars

        sess = STATE.get("session") or {}
        if sess.get("queue") and all(os.path.exists(p) for p in sess["queue"]):
            self.queue = list(sess["queue"])
            self.q_idx = min(int(sess.get("q_idx", 0)), len(self.queue) - 1)
            self.current_path = self.queue[self.q_idx]
            self.status = "Session restored"
        self._session_save_t = 0.0

    # ---------- mpv helpers ----------
    def gp(self, name, default=None):
        try:
            v = getattr(self.p, name)
            return default if v is None else v
        except Exception:
            return default

    def _safe_set(self, name, value):
        try:
            setattr(self.p, name, value)
        except Exception:
            pass

    def seek(self, secs):
        if not self.current_path:
            return
        try:
            self.p.command("seek", secs, "relative")
        except Exception:
            pass

    def apply_eq(self):
        try:
            f = EQ_PRESETS.get(self.eq, "")
            if f:
                self.p.command("af", "set", f)
            else:
                self.p.command("af", "clr")
        except Exception:
            pass

    def persist(self):
        STATE["volume"] = self.user_vol
        STATE["bookmarks"] = self.bookmarks
        STATE["favorites"] = list(self.favorites)
        STATE["last_dir"] = self.cur_dir
        STATE["settings"] = dict(SET)
        STATE["history"] = self.history[:HISTORY_MAX]
        STATE["play_count"] = self.play_count
        STATE["positions"] = self.positions
        save_state(STATE)

    def save_session(self):
        try:
            STATE["session"] = {
                "queue": self.queue,
                "q_idx": self.q_idx,
                "position": self.gp("time_pos", 0) or 0,
            }
            save_state(STATE)
        except Exception:
            pass

    def remember_position(self, path):
        if not path or not SET["resume"]:
            return
        try:
            pos = self.gp("time_pos", 0) or 0
            dur = self.gp("duration", 0) or 0
            if pos >= RESUME_MIN and (not dur or pos < dur - RESUME_NEAR_END):
                self.positions[path] = float(pos)
        except Exception:
            pass

    def add_history(self, path):
        if not path:
            return
        self.history.insert(0, {"p": path, "t": time.time()})
        self.history = self.history[:HISTORY_MAX]
        self.play_count[path] = self.play_count.get(path, 0) + 1

    # ---------- visualizer ----------
    def tick_viz(self):
        """Animate the bar visualizer (only when playing)."""
        if not self.is_active():
            for i in range(self.viz_bars):
                self.viz_heights[i] *= 0.7
            return
        pos = self.gp("time_pos", 0) or 0
        vol = max(1, self.user_vol)
        base = (vol / VOL_MAX) * 0.85
        self.viz_phase = (time.monotonic() * 4.0) % (2 * math.pi)
        for i in range(self.viz_bars):
            ph = self.viz_phase + i * 0.7 + (pos * 0.4)
            s1 = 0.5 + 0.5 * math.sin(ph)
            s2 = 0.5 + 0.5 * math.sin(ph * 1.7 + 1.3)
            s3 = random.random() * 0.15
            target = base * (0.35 + 0.55 * ((s1 + s2) / 2) + s3)
            self.viz_heights[i] = self.viz_heights[i] * 0.6 + target * 0.4
            if self.viz_heights[i] > 1.0:
                self.viz_heights[i] = 1.0

    def draw_viz(self, h, w, right_x):
        """Draw small bars near the right side of the chips row."""
        if not self.current_path:
            return
        blocks = " ▁▂▃▄▅▆▇█"
        bar_x = max(2, right_x)
        y = h - 2
        for i in range(self.viz_bars):
            hgt = self.viz_heights[i]
            idx = int(round(hgt * (len(blocks) - 1)))
            ch = blocks[idx] if idx < len(blocks) else "█"
            if bar_x + i >= w - 1:
                break
            color = 5 if hgt > 0.6 else (7 if hgt > 0.35 else 4)
            safe(self.scr, y, bar_x + i, ch, curses.color_pair(color) | curses.A_BOLD)

    # ---------- playback ----------
    def is_active(self):
        return (bool(self.current_path)
                and not self.gp("idle_active", True)
                and not self.gp("pause", False))

    def play_now(self, path):
        try:
            if self.current_path and self.current_path != path:
                self.remember_position(self.current_path)
            self.p.play(path)
            self.p.pause = False
            self.current_path = path
            self.last_play = time.monotonic()
            self.status = "PLAYING"
            self.apply_eq()
            self.add_history(path)
            if SET["resume"]:
                pos = self.positions.get(path)
                if pos and pos > RESUME_MIN:
                    try:
                        self.p.command("seek", pos, "absolute")
                    except Exception:
                        pass
        except Exception as e:
            self.status = f"ERROR: {str(e)[:40]}"

    def start_fade_in(self):
        self.fade.update(phase="in", t0=time.monotonic(), dur=FADE_SECONDS, action=None)

    def run_action(self, action):
        self.fade.update(phase=None, action=None)
        if action[0] == "play":
            self._safe_set("volume", 0)
            self.play_now(action[1])
            self.start_fade_in()
        else:
            self._safe_set("pause", True)
            self._safe_set("volume", self.user_vol)
            self.status = action[1]

    def start_fade_out(self, action):
        # If already fading out with same action, don't restart
        if (self.fade["phase"] == "out" and self.fade.get("action") == action):
            return
        # If not playing, just execute the action immediately
        if not self.is_active():
            self.run_action(action)
            return
        # Start fade-out with new action
        self.fade.update(
            phase="out",
            t0=time.monotonic(),
            dur=FADE_SECONDS,
            action=action
        )

    def start_track(self, path):
        self.start_fade_out(("play", path))

    def tick_fade(self):
        f = self.fade
        if f["phase"] is None:
            return
        p = min(1.0, (time.monotonic() - f["t0"]) / f["dur"])
        e = 0.5 - 0.5 * math.cos(math.pi * p)
        if f["phase"] == "out":
            self._safe_set("volume", int(round(self.user_vol * (1 - e))))
            if p >= 1.0:
                self.run_action(f["action"])
        else:
            self._safe_set("volume", int(round(self.user_vol * e)))
            if p >= 1.0:
                f["phase"] = None
                self._safe_set("volume", self.user_vol)

    def tick_sleep(self):
        if self.sleep_until and time.monotonic() >= self.sleep_until:
            self.sleep_until = 0.0
            self.sleep_i = 0
            self.start_fade_out(("pause", "Sleep: paused"))

    def tick_library(self):
        if self._was_scanning and not LIB.scanning:
            self.status = f"Library ready: {len(LIB.tracks)} songs"
        self._was_scanning = LIB.scanning

    def tick_session(self):
        t = time.monotonic()
        if t - self._session_save_t > 10:
            self._session_save_t = t
            self.save_session()

    def maybe_autonext(self):
        # Only trigger auto-next when not in fade transition
        if (self.queue
                and self.fade["phase"] is None
                and self.status == "PLAYING"
                and not self.gp("pause", False)
                and self.gp("idle_active", False)
                and time.monotonic() - self.last_play > 1.5):
            self.next_track(auto=True)

    def set_queue(self, paths, start=0):
        if not paths:
            return
        start = max(0, min(start, len(paths) - 1))
        if self.shuffle:
            first = paths[start]
            rest = paths[:start] + paths[start + 1:]
            random.shuffle(rest)
            paths = [first] + rest
            start = 0
        self.queue = list(paths)
        self.q_idx = start
        self.start_track(self.queue[self.q_idx])

    def next_track(self, step=1, auto=False):
        if not self.queue:
            return
        # Repeat-ONE: restart current track with fade
        if auto and self.repeat == "one" and self.q_idx >= 0:
            self.start_fade_out(("play", self.queue[self.q_idx]))
            return
        n = self.q_idx + step
        if n >= len(self.queue) or n < 0:
            if self.repeat == "all":
                n %= len(self.queue)
            elif step > 0:
                self.status = "END"
                return
            else:
                n = 0
        self.q_idx = n
        self.start_fade_out(("play", self.queue[n]))

    def toggle_pause(self):
        if not self.current_path:
            return
        f = self.fade
        if f["phase"] == "out" and f["action"] and f["action"][0] == "pause":
            f.update(phase=None, action=None)
            self._safe_set("volume", self.user_vol)
            self.status = "PLAYING"
            return
        if self.gp("pause", False):
            self._safe_set("volume", 0)
            self._safe_set("pause", False)
            self.status = "PLAYING"
            self.start_fade_in()
        else:
            self.start_fade_out(("pause", "PAUSED"))

    def change_volume(self, delta):
        self.user_vol = max(0, min(VOL_MAX, self.user_vol + delta))
        if self.fade["phase"] is None:
            self._safe_set("volume", self.user_vol)
        self.persist()

    def set_speed(self, s):
        self._safe_set("speed", round(max(0.5, min(2.0, s)), 2))

    def cycle_sleep(self):
        self.sleep_i = (self.sleep_i + 1) % len(SLEEP_STEPS)
        mins = SLEEP_STEPS[self.sleep_i]
        self.sleep_until = time.monotonic() + mins * 60 if mins else 0.0
        self.status = f"Sleep timer {mins} min" if mins else "Sleep timer OFF"

    def set_sleep_minutes(self, mins):
        if mins <= 0:
            self.sleep_until = 0.0
            self.status = "Sleep timer OFF"
        else:
            self.sleep_until = time.monotonic() + mins * 60
            self.status = f"Sleep timer {mins} min"

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        SET["shuffle"] = self.shuffle
        if self.shuffle and self.queue and self.q_idx >= 0:
            cur = self.queue[self.q_idx]
            rest = [x for i, x in enumerate(self.queue) if i != self.q_idx]
            random.shuffle(rest)
            self.queue = [cur] + rest
            self.q_idx = 0
        self.persist()

    def cycle_eq(self):
        keys = list(EQ_PRESETS.keys())
        i = keys.index(self.eq) if self.eq in keys else 0
        self.eq = keys[(i + 1) % len(keys)]
        SET["eq"] = self.eq
        self.apply_eq()
        self.status = f"EQ: {self.eq}"
        self.persist()

    def toggle_favorite(self, path=None):
        path = path or self.current_path
        if not path:
            self.status = "No track selected"
            return
        if path in self.favorites:
            self.favorites.discard(path)
            self.status = f" Removed: {os.path.basename(path)[:40]}"
        else:
            self.favorites.add(path)
            self.status = f" Added: {os.path.basename(path)[:40]}"
        self.persist()

    def play_folder(self, folder):
        V = LIB.view
        if not V:
            return
        paths = sorted(V["under"].get(folder, []))
        if paths:
            self.set_queue(paths, 0)
            self.status = f"Folder: {os.path.basename(folder)} ({len(paths)})"
        else:
            self.status = "Nothing in this folder"

    # ---------- navigation ----------
    def switch_tab(self, t):
        if t == 0:
            self.folder_filter = None
        self.tab = t
        self.idx = 0
        self.scroll = 0
        if t == 1:
            self.lib_view = 0

    def switch_lib_view(self, v):
        if v == 1:
            # Going to Folders — start at ROOT
            self.cur_dir = ROOT
        self.lib_view = v
        self.idx = 0
        self.scroll = 0

    # ---------- rows ----------
    def build_all(self):
        if self.folder_filter and LIB.view:
            paths = sorted(LIB.view["under"].get(self.folder_filter, []))
            return [("file", list_label(p), p) for p in paths]
        return [("file", list_label(p), p) for p in LIB.all_paths]

    def build_library_menu(self):
        V = LIB.view
        rows = []
        cnt = len(V["all_dirs"]) if V else 0
        rows.append(("menu", f"  Folders  ({cnt})", "Folders"))
        rows.append(("menu", f"  Recent  ({len(self.history)})", "Recent"))
        rows.append(("menu", f"  Playlists  ({len(LIB.playlists)})", "Playlists"))
        rows.append(("menu", f"  Favorite  ({len(self.favorites)})", "Favorite"))
        rows.append(("menu", f"󰎌  Queue  ({len(self.queue)})", "Queue"))
        rows.append(("menu", f"󱕎  Stats", "Stats"))
        return rows

    def build_folders(self):
        """Show immediate subfolders of cur_dir + files + parent link."""
        V = LIB.view
        if not V:
            return []
        rows = []
        # Back to parent
        if self.cur_dir != ROOT:
            rows.append(("fdir_up", ".. (up one level)", os.path.dirname(self.cur_dir)))
        # Immediate subfolders
        for d in V["children"].get(self.cur_dir, []):
            label = f"▸ {os.path.basename(d)}  ({V['cnt'].get(d, 0)})"
            rows.append(("fdir", label, d))
        # Files in this folder
        for p in V["files"].get(self.cur_dir, []):
            rows.append(("file", list_label(p), p))
        # Playlists in this folder
        for p in V["pls"].get(self.cur_dir, []):
            rows.append(("pl", f" {os.path.basename(p)}  ({LIB.playlists.get(p, 0)})", p))
        return rows

    def build_playlists(self):
        items = sorted(LIB.playlists.items(), key=lambda x: os.path.basename(x[0]).lower())
        return [("pl", f"≡ {os.path.basename(p)}  ({n})", p) for p, n in items]

    def build_recent(self):
        seen = set()
        rows = []
        for entry in self.history:
            p = entry.get("p")
            if not p or p in seen or not os.path.exists(p):
                continue
            seen.add(p)
            cnt = self.play_count.get(p, 0)
            rows.append(("file", f"[{cnt}×] {list_label(p)}", p))
        return rows

    def build_favorite(self):
        rows = []
        for p in sorted(self.favorites, key=lambda x: list_label(x).lower()):
            if os.path.exists(p):
                rows.append(("file", f" {list_label(p)}", p))
        return rows

    def build_queue(self):
        rows = []
        for i, p in enumerate(self.queue):
            marker = "▶" if i == self.q_idx else " "
            rows.append(("qitem", f"{marker} {i+1:>3}. {list_label(p)}", p))
        return rows

    def build_stats(self):
        total_tracks = len(LIB.tracks)
        total_sec = sum(float(v.get("l", 0) or 0) for v in LIB.tracks.values())
        total_size = sum(int(v.get("s", 0) or 0) for v in LIB.tracks.values())
        total_plays = sum(self.play_count.values())
        artist_sec = {}
        for p, info in LIB.tracks.items():
            a = info.get("a") or "—"
            artist_sec[a] = artist_sec.get(a, 0.0) + float(info.get("l", 0) or 0)
        top_artist = max(artist_sec.items(), key=lambda x: x[1])[0] if artist_sec else "—"
        top_track = "—"
        if self.play_count:
            tp = max(self.play_count.items(), key=lambda x: x[1])[0]
            if os.path.exists(tp):
                top_track = track_title(tp)
        lines = [
            ("Tracks", f"{total_tracks}"),
            ("Total time", fmt_time(total_sec)),
            ("Total size", fmt_size(total_size)),
            ("Total plays", f"{total_plays}"),
            ("Top artist", top_artist),
            ("Top track", top_track),
            ("Favorites", f"{len(self.favorites)}"),
            ("History entries", f"{len(self.history)}"),
        ]
        return [("stat", f"{k:<16} {v}", None) for k, v in lines]

    def build_settings(self):
        out = []
        for key, label, kind, _ in SETTING_SPEC:
            v = SET[key]
            shown = ("ON" if v else "OFF") if kind == "bool" else str(v)
            out.append(("set", f"{label:<26} {shown}", key))
        return out

    def rows(self):
        if self.search_on:
            key = ("s", self.s_ver, SET["show_meta"])
            build = lambda: [("file", list_label(p), p) for p in self.s_hits]
        elif self.tab == 0:
            key = ("all", LIB.version, SET["show_meta"], self.folder_filter)
            build = self.build_all
        elif self.tab == 2:
            return self.build_settings()
        else:
            lv = self.lib_view
            if lv == 0:
                key = ("libmenu", LIB.version, len(self.history),
                       len(LIB.playlists), len(self.favorites), len(self.queue))
                build = self.build_library_menu
            elif lv == 1:
                key = ("folders", self.cur_dir, LIB.version)
                build = self.build_folders
            elif lv == 2:
                return self.build_recent()
            elif lv == 3:
                return self.build_playlists()
            elif lv == 4:
                return self.build_favorite()
            elif lv == 5:
                return self.build_queue()
            elif lv == 6:
                return self.build_stats()
            else:
                return []
        if key != self._rkey:
            self._rkey = key
            self._rows = build()
        return self._rows

    def stats_bar(self):
        if self.search_on:
            return len(self.s_hits), sum(LIB.tracks.get(p, {}).get("l", 0) for p in self.s_hits)
        if self.tab == 0:
            if self.folder_filter:
                paths = LIB.view["under"].get(self.folder_filter, []) if LIB.view else []
                total_sec = sum(LIB.tracks.get(p, {}).get("l", 0) for p in paths)
                return len(paths), total_sec
            total_sec = sum(float(v.get("l", 0) or 0) for v in LIB.tracks.values())
            return len(LIB.all_paths), total_sec
        if self.tab == 1 and LIB.view:
            lv = self.lib_view
            if lv == 1:
                return len(LIB.view["all_dirs"]), None
            if lv == 2:
                return len(self.history), None
            if lv == 3:
                return len(LIB.playlists), None
            if lv == 4:
                return len(self.favorites), None
            if lv == 5:
                return len(self.queue), None
        return None, None

    # ---------- actions ----------
    def enter_dir(self, path):
        self.cur_dir = path
        self.idx = 0
        self.scroll = 0
        self.persist()

    def go_up(self):
        """Backspace in Folders: go up one level."""
        if self.tab == 1 and self.lib_view == 1:
            if self.cur_dir != ROOT:
                parent = os.path.dirname(self.cur_dir)
                if parent == ROOT or parent.startswith(ROOT + os.sep):
                    self.enter_dir(parent)
                    return
            # At ROOT, go to Library menu
            self.switch_lib_view(0)
            return
        if self.tab == 1 and self.lib_view != 0:
            self.switch_lib_view(0)
            return

    def activate(self, row):
        """Enter on a row. NEVER changes tab."""
        kind, _, payload = row
        if kind == "menu":
            m = {"Folders": 1, "Recent": 2, "Playlists": 3,
                 "Favorite": 4, "Queue": 5, "Stats": 6}
            if payload in m:
                self.switch_lib_view(m[payload])
        elif kind == "dir":
            self.enter_dir(payload)
        elif kind == "fdir_up":
            self.enter_dir(payload)
        elif kind == "fdir":
            # Enter on folder in Folders view → drill into it
            self.enter_dir(payload)
        elif kind == "file":
            files = [r[2] for r in self.rows() if r[0] in ("file", "qitem")]
            if payload in files:
                self.set_queue(files, files.index(payload))
        elif kind == "qitem":
            if payload in self.queue:
                self.q_idx = self.queue.index(payload)
                self.start_track(payload)
        elif kind == "pl":
            songs = read_m3u(payload)
            if songs:
                self.set_queue(songs, 0)
                self.status = f"Playlist: {os.path.basename(payload)}"
            else:
                self.status = "Playlist is empty or files are missing"
        elif kind == "set":
            self.adjust_setting(payload, +1)

    def jump_to_playing(self):
        if not self.current_path:
            return
        for i, r in enumerate(self.rows()):
            if r[0] in ("file", "qitem") and r[2] == self.current_path:
                self.idx = i
                return
        self.status = "This track is not in the current list"

    def adjust_setting(self, key, d):
        _, _, kind, opts = next(s for s in SETTING_SPEC if s[0] == key)
        v = SET[key]
        if kind == "bool":
            v = not v
        elif kind == "choice":
            v = opts[(opts.index(v) + d) % len(opts)]
        elif kind == "int":
            lo, hi, step = opts
            v = max(lo, min(hi, v + d * step))
        SET[key] = v
        if key == "theme":
            init_theme(v)
        elif key == "repeat":
            self.repeat = v
        elif key == "shuffle":
            self.shuffle = v
        elif key == "eq":
            self.eq = v
            self.apply_eq()
        self.persist()

    # ---------- search ----------
    def refresh_hits(self):
        self.s_hits = search_tracks(self.query)
        self.s_ver += 1
        self.idx = 0
        self.scroll = 0

    def open_search(self):
        self.search_on = True
        self.focus = "input"
        self.query = ""
        self.saved_pos = (self.idx, self.scroll)
        self.refresh_hits()

    def close_search(self):
        self.search_on = False
        self.focus = "input"
        self.query = ""
        self.s_hits = []
        self.s_ver += 1
        self.idx, self.scroll = self.saved_pos

    def handle_search(self, code, ch):
        if code == 27:
            self.close_search()
            return True
        if code == 9:
            self.focus = "list" if self.focus == "input" else "input"
            return True
        if code in (10, 13):
            if self.focus == "input":
                if self.s_hits:
                    self.focus = "list"
                    self.idx = 0
                    self.scroll = 0
                else:
                    self.status = "NO RESULTS"
            else:
                rows = self.rows()
                if rows:
                    self.activate(rows[min(self.idx, len(rows) - 1)])
            return True
        if code == curses.KEY_DOWN:
            if self.focus == "input":
                if self.s_hits:
                    self.focus = "list"
                    self.idx = 0
            else:
                self.idx = min(len(self.s_hits) - 1, self.idx + 1)
            return True
        if code == curses.KEY_UP:
            if self.focus == "list":
                if self.idx == 0:
                    self.focus = "input"
                else:
                    self.idx -= 1
            return True
        if code in (curses.KEY_BACKSPACE, 127, 8):
            self.focus = "input"
            self.query = self.query[:-1]
            self.refresh_hits()
            return True
        if ch and ch.isprintable() and code >= 32:
            self.focus = "input"
            self.query += ch
            self.refresh_hits()
        return True

    # ---------- EQ / Theme popup ----------
    def open_eq_menu(self):
        self.eq_menu_open = True
        keys = list(EQ_PRESETS.keys())
        self.eq_menu_idx = keys.index(self.eq) if self.eq in keys else 0
        self.eq_menu_scroll = 0

    def handle_eq_menu(self, code, ch):
        keys = list(EQ_PRESETS.keys())
        if code == 27:
            self.eq_menu_open = False
            return True
        if code == curses.KEY_UP or ch == "k":
            self.eq_menu_idx = max(0, self.eq_menu_idx - 1)
            return True
        if code == curses.KEY_DOWN or ch == "j":
            self.eq_menu_idx = min(len(keys) - 1, self.eq_menu_idx + 1)
            return True
        if code == curses.KEY_PPAGE:
            self.eq_menu_idx = max(0, self.eq_menu_idx - 10)
            return True
        if code == curses.KEY_NPAGE:
            self.eq_menu_idx = min(len(keys) - 1, self.eq_menu_idx + 10)
            return True
        if ch == "g":
            self.eq_menu_idx = 0
            return True
        if ch == "G":
            self.eq_menu_idx = len(keys) - 1
            return True
        if code in (10, 13, ord(" ")):
            self.eq = keys[self.eq_menu_idx]
            SET["eq"] = self.eq
            self.apply_eq()
            self.persist()
            self.eq_menu_open = False
            self.status = f"EQ: {self.eq}"
            return True
        return True

    def open_theme_menu(self):
        self.theme_menu_open = True
        keys = list(THEMES.keys())
        self.theme_menu_idx = keys.index(SET["theme"]) if SET["theme"] in keys else 0

    def handle_theme_menu(self, code, ch):
        keys = list(THEMES.keys())
        if code == 27:
            self.theme_menu_open = False
            return True
        if code == curses.KEY_UP:
            self.theme_menu_idx = max(0, self.theme_menu_idx - 1)
            init_theme(keys[self.theme_menu_idx])
            return True
        if code == curses.KEY_DOWN:
            self.theme_menu_idx = min(len(keys) - 1, self.theme_menu_idx + 1)
            init_theme(keys[self.theme_menu_idx])
            return True
        if code in (10, 13, ord(" ")):
            SET["theme"] = keys[self.theme_menu_idx]
            init_theme(SET["theme"])
            self.persist()
            self.theme_menu_open = False
            self.status = f"Theme: {SET['theme']}"
            return True
        return True

    # ---------- prompts / actions ----------
    def prompt(self, label):
        h, w = self.scr.getmaxyx()
        s = ""
        curses.echo()
        curses.curs_set(1)
        self.scr.nodelay(False)
        self.scr.timeout(-1)
        try:
            self.scr.move(h - 1, 0)
            self.scr.clrtoeol()
            self.scr.addstr(h - 1, 0, label[:w - 1], curses.A_BOLD)
            self.scr.refresh()
            s = self.scr.getstr(h - 1, min(len(label), w - 2), 200).decode("utf-8", "ignore")
        except Exception:
            s = ""
        finally:
            curses.noecho()
            curses.curs_set(0)
            self.scr.nodelay(True)
            self.scr.timeout(40)
        return s.strip()

    def save_playlist(self):
        files = [r[2] for r in self.rows() if r[0] == "file"]
        if not files:
            return
        out = os.path.join(self.cur_dir, "playlist.m3u")
        try:
            with open(out, "w", encoding="utf-8") as fp:
                fp.write("#EXTM3U\n")
                for f in files:
                    fp.write(f + "\n")
            self.status = f"SAVED: {out}"
        except Exception as e:
            self.status = f"ERR: {str(e)[:40]}"

    def do_bookmarks(self):
        bm = self.prompt(" Bookmark name (blank = list): ")
        if not bm:
            if not self.bookmarks:
                self.status = "NO BOOKMARKS"
                return
            pick = self.prompt(" Jump to # : ")
            try:
                j = int(pick) - 1
                if 0 <= j < len(self.bookmarks):
                    self.enter_dir(self.bookmarks[j])
                    self.tab = 0
            except ValueError:
                pass
        else:
            if self.cur_dir not in self.bookmarks:
                self.bookmarks.append(self.cur_dir)
                self.persist()
                self.status = f"BOOKMARKED: {bm}"
            else:
                self.status = "Already bookmarked"

    def delete_current(self, path):
        name = os.path.basename(path)
        ans = self.prompt(f" Delete {name[:40]}? (y/N): ")
        if ans.lower() != "y":
            self.status = "Cancelled"
            return
        try:
            os.remove(path)
            self.status = f"Deleted: {name[:40]}"
            if path == self.current_path:
                self._safe_set("stop", True)
                self.current_path = ""
            if path in self.queue:
                i = self.queue.index(path)
                self.queue.pop(i)
                if self.q_idx > i:
                    self.q_idx -= 1
                elif self.q_idx == i and self.queue:
                    self.q_idx = min(self.q_idx, len(self.queue) - 1)
            self.favorites.discard(path)
        except Exception as e:
            self.status = f"ERR: {str(e)[:40]}"

    def clear_queue(self):
        self.queue = []
        self.q_idx = -1
        self._safe_set("stop", True)
        self.current_path = ""
        self.status = "Queue cleared"

    def remove_from_queue(self):
        if not self.queue or self.q_idx < 0:
            return
        self.queue.pop(self.q_idx)
        if not self.queue:
            self.clear_queue()
            return
        self.q_idx = min(self.q_idx, len(self.queue) - 1)
        self.start_track(self.queue[self.q_idx])

    def open_lyrics(self):
        if not self.current_path:
            self.status = "No track is currently playing"
            return
        data = read_lrc(self.current_path)
        if not data:
            self.status = "Lyrics (.lrc) not found"
            return
        self.lyrics_path = self.current_path
        self.lyrics_data = data
        self.lyrics_scroll = 0

    def open_now_playing(self):
        if not self.current_path:
            self.status = "No track is currently playing"
            return
        self.now_playing_open = True

    # ---------- drawing ----------
    def draw_header(self, w):
        """Header: left = status, right = only VOLUME (no song count/total time)."""
        # Only show volume or scanning indicator on the right
        if LIB.scanning:
            right = f"⟳ scanning {LIB.found}  "
        else:
            right = f"vol {self.user_vol}  "
        left = f"  music-am  ·  {self.status}"
        width = max(0, w - len(right) - 1)
        line = left[:width].ljust(width) + right
        safe(self.scr, 0, 0, line, curses.color_pair(1) | curses.A_BOLD)

    def draw_tabs(self, w):
        x = 1
        for i, name in enumerate(TABS):
            label = f" {i + 1} {name} "
            attr = (curses.color_pair(9) | curses.A_BOLD) if i == self.tab else curses.color_pair(6)
            safe(self.scr, 1, x, label, attr)
            x += len(label) + 1

        if self.tab == 1 and self.lib_view != 0:
            names = {1: "Folders", 2: "Recent", 3: "Playlists",
                     4: "Favorite", 5: "Queue", 6: "Stats"}
            x += 2
            crumb = f"▸ Library / {names.get(self.lib_view, '')}  ( BKSP = back)"
            safe(self.scr, 1, x, crumb, curses.color_pair(4) | curses.A_BOLD)

        if self.search_on:
            cursor = "▌" if self.focus == "input" else ""
            sub = (f" / {self.query}{cursor}   {len(self.s_hits)} results   "
                   f"↑↓ move · ⏎ play · Esc close")
        elif self.tab == 0:
            if self.folder_filter:
                sub = f"   {os.path.basename(self.folder_filter)} · 1 = All"
            else:
                sub = " All songs  ·  alphabetical"
        elif self.tab == 1:
            lv = self.lib_view
            if lv == 0:
                sub = " Library menu  · ENTER = open · ← / Backspace = return"
            elif lv == 1:
                rel = os.path.relpath(self.cur_dir, ROOT) if self.cur_dir != ROOT else "."
                sub = f"   {rel}  ·  ⏎ = enter  ·  ⌫ = up  ·  a = play all  ·  o = All view"
            elif lv == 2:
                sub = " Recently played (latest first)"
            elif lv == 3:
                sub = " Playlists (.m3u)"
            elif lv == 4:
                sub = " Favorite tracks  ·  f = toggle favorite"
            elif lv == 5:
                sub = " Current queue  ·  d = remove · c = clear"
            elif lv == 6:
                sub = " Library statistics"
        else:
            sub = " ENTER / Right = change"
        safe(self.scr, 2, 0, sub, curses.color_pair(2))
        safe(self.scr, 3, 0, "─" * (w - 1), curses.color_pair(6))

    def empty_msg(self):
        if LIB.scanning:
            return "Scanning the library. Please wait..."
        if LIB.view is None:
            return "The library is empty. Press R to start scanning"
        if self.search_on:
            return "No results found"
        if self.tab == 0:
            return "The library is empty (press R to scan)"
        if self.tab == 2:
            return ""
        lv = self.lib_view
        return {
            0: "",
            1: "Nothing in this folder",
            2: "Nothing played yet",
            3: "No playlists (.m3u) found",
            4: "No favorites yet (press f on a track)",
            5: "Queue is empty",
            6: "",
        }.get(lv, "")

    def draw_list(self, rows, h, w):
        top, bot = 4, h - 5
        vis = bot - top
        if vis < 1:
            return
        n = len(rows)
        if n == 0:
            safe(self.scr, top, 3, self.empty_msg(), curses.color_pair(6))
            return
        self.idx = max(0, min(self.idx, n - 1))
        if self.idx < self.scroll:
            self.scroll = self.idx
        elif self.idx >= self.scroll + vis:
            self.scroll = self.idx - vis + 1
        for i in range(vis):
            r = self.scroll + i
            if r >= n:
                break
            kind, label, payload = rows[r]
            y = top + i
            if r == self.idx:
                safe(self.scr, y, 0, ("  " + label).ljust(w - 1),
                     curses.color_pair(3) | curses.A_BOLD)
            else:
                playing = kind in ("file", "qitem") and payload == self.current_path
                prefix = " ▶ " if playing else "   "
                cp = 5 if playing else {
                    "menu": 4, "dir": 4, "fdir": 4, "fdir_up": 2,
                    "pl": 2, "stat": 2,
                }.get(kind, 11)
                attr = curses.color_pair(cp) | (
                    curses.A_BOLD if (playing or kind == "menu") else 0
                )
                safe(self.scr, y, 0, prefix + label, attr)

    def draw_info(self, h, w):
        top, bot = 4, h - 5
        for y in range(top, bot):
            safe(self.scr, y, 0, " " * (w - 1))
        safe(self.scr, top, 2, "Track info   (any key = close)",
             curses.color_pair(2) | curses.A_BOLD)
        y = top + 2
        vw = max(10, w - 22)
        for k, v in info_rows(self.info_path):
            for i, line in enumerate(textwrap.wrap(str(v), vw) or ["—"]):
                if y >= bot:
                    return
                label = f"{k:<10}" if i == 0 else " " * 10
                safe(self.scr, y, 2, f"{label}  {line}",
                     curses.color_pair(5 if i == 0 else 11))
                y += 1

    def draw_lyrics(self, h, w):
        top, bot = 4, h - 5
        for y in range(top, bot):
            safe(self.scr, y, 0, " " * (w - 1))
        safe(self.scr, top, 2, "Lyrics   (↑↓ scroll · any key = close)",
             curses.color_pair(2) | curses.A_BOLD)
        pos = self.gp("time_pos", 0) or 0
        active = -1
        for i, (t, _) in enumerate(self.lyrics_data):
            if t <= pos:
                active = i
            else:
                break
        if active >= 0:
            self.lyrics_scroll = max(0, active - (bot - top - 4) // 2)
        y = top + 2
        for i in range(self.lyrics_scroll, len(self.lyrics_data)):
            if y >= bot:
                break
            t, text = self.lyrics_data[i]
            line = f"[{fmt_time(t)}] {text}" if text else ""
            if i == active:
                safe(self.scr, y, 2, line[:w - 3],
                     curses.color_pair(3) | curses.A_BOLD)
            else:
                safe(self.scr, y, 2, line[:w - 3], curses.color_pair(6))
            y += 1

    def draw_now_playing(self, h, w):
        for y in range(4, h - 5):
            safe(self.scr, y, 0, " " * (w - 1))
        if not self.current_path:
            safe(self.scr, 6, 4, "Nothing playing", curses.color_pair(6))
            return
        title = track_title(self.current_path)
        info = LIB.tracks.get(self.current_path, {})
        artist = info.get("a") or ""
        album = info.get("al") or ""
        safe(self.scr, 5, 2, "╭" + "─" * (w - 6) + "╮", curses.color_pair(2))
        y = 6
        for ln in textwrap.wrap(title, w - 8)[:2]:
            safe(self.scr, y, 4, f"   {ln}", curses.color_pair(5) | curses.A_BOLD)
            y += 1
        y += 1
        if artist:
            safe(self.scr, y, 4, f"    {artist}", curses.color_pair(11))
            y += 1
        if album:
            safe(self.scr, y, 4, f"    {album}", curses.color_pair(6))
            y += 1
        y += 1
        pos = self.gp("time_pos", 0) or 0
        dur = self.gp("duration", 0) or 0
        if dur > 0:
            bar_w = max(10, w - 24)
            filled = min(bar_w, int(bar_w * pos / dur))
            pct = int(100 * pos / dur)
            x = 4
            safe(self.scr, y, x, fmt_time(pos) + " ", curses.color_pair(11))
            x += len(fmt_time(pos)) + 1
            safe(self.scr, y, x, "█" * filled, curses.color_pair(7) | curses.A_BOLD)
            x += filled
            safe(self.scr, y, x, "░" * (bar_w - filled), curses.color_pair(8))
            x += bar_w - filled
            safe(self.scr, y, x, f" {fmt_time(dur)} {pct:3d}%", curses.color_pair(11))
            y += 2
        chips = []
        if self.queue:
            chips.append(f"[{self.q_idx + 1}/{len(self.queue)}]")
        if self.shuffle:
            chips.append("SHUF")
        if self.repeat != "off":
            chips.append(f"REP:{self.repeat}")
        chips.append(f"EQ:{self.eq}")
        safe(self.scr, y, 4, "  ".join(chips), curses.color_pair(2))
        y += 2
        safe(self.scr, y, 4, "Press any key to close", curses.color_pair(6))
        safe(self.scr, min(h - 6, y + 2), 2, "╰" + "─" * (w - 6) + "╯", curses.color_pair(2))

    def draw_eq_menu(self, h, w):
        for y in range(4, h - 5):
            safe(self.scr, y, 0, " " * (w - 1))

        safe(self.scr, 4, 2, " Equalizer Presets  (Up/Down scroll | Enter apply | Esc cancel)",
             curses.color_pair(2) | curses.A_BOLD)
        safe(self.scr, 5, 2, "-" * (w - 5), curses.color_pair(6))

        keys = list(EQ_PRESETS.keys())
        total = len(keys)
        if total == 0:
            return

        top = 6
        bot = h - 5
        visible = max(1, bot - top)

        if getattr(self, "eq_menu_scroll", 0) is None:
            self.eq_menu_scroll = 0
        if self.eq_menu_idx < self.eq_menu_scroll:
            self.eq_menu_scroll = self.eq_menu_idx
        elif self.eq_menu_idx >= self.eq_menu_scroll + visible:
            self.eq_menu_scroll = self.eq_menu_idx - visible + 1

        max_scroll = max(0, total - visible)
        self.eq_menu_scroll = max(0, min(self.eq_menu_scroll, max_scroll))

        end = min(total, self.eq_menu_scroll + visible)
        y = top
        for i in range(self.eq_menu_scroll, end):
            k = keys[i]
            if i == self.eq_menu_idx:
                prefix = " > "
                current = " (active)" if k == self.eq else ""
                line = (prefix + k + current).ljust(w - 2)
                safe(self.scr, y, 0, line,
                     curses.color_pair(3) | curses.A_BOLD)
            else:
                current = " (active)" if k == self.eq else ""
                safe(self.scr, y, 2, f"   {k}{current}", curses.color_pair(11))
            y += 1

        if self.eq_menu_scroll > 0:
            safe(self.scr, top - 1, max(2, w - 12), " ^ more ",
                 curses.color_pair(4) | curses.A_BOLD)
        if end < total:
            safe(self.scr, bot, max(2, w - 12), " v more ",
                 curses.color_pair(4) | curses.A_BOLD)

        pos_text = f" {self.eq_menu_idx + 1}/{total} "
        safe(self.scr, bot, max(2, w - 20), pos_text, curses.color_pair(2))

    def draw_theme_menu(self, h, w):
        for y in range(4, h - 5):
            safe(self.scr, y, 0, " " * (w - 1))
        safe(self.scr, 4, 2, " Themes  (↑↓ = preview · ⏎ = apply · Esc = cancel)",
             curses.color_pair(2) | curses.A_BOLD)
        safe(self.scr, 5, 2, "─" * (w - 5), curses.color_pair(6))
        keys = list(THEMES.keys())
        y = 6
        for i, k in enumerate(keys):
            if y >= h - 5:
                break
            marker = "  " if i == self.theme_menu_idx else "   "
            current = " ●" if k == SET["theme"] else ""
            attr = (curses.color_pair(3) | curses.A_BOLD) if i == self.theme_menu_idx else curses.color_pair(11)
            safe(self.scr, y, 2, f"{marker}{k}{current}", attr)
            y += 1

    def draw_player(self, h, w):
        safe(self.scr, h - 5, 0, "─" * (w - 1), curses.color_pair(6))
        if self.current_path:
            title = track_title(self.current_path)[:max(20, w - 6)]
            fav = " " if self.current_path in self.favorites else ""
            safe(self.scr, h - 4, 0, f"   {fav}{title}",
                 curses.color_pair(5) | curses.A_BOLD)
        else:
            safe(self.scr, h - 4, 0, "  Nothing playing, ENTER dabao", curses.color_pair(6))

        pos = self.gp("time_pos", 0) or 0
        dur = self.gp("duration", 0) or 0
        if self.current_path and dur > 0:
            tpos = fmt_time(pos)
            tdur = fmt_time(dur)
            pct = int(100 * pos / dur)
            right_len = len(tdur) + len(f" {pct:3d}%") + 2
            bar_w = max(6, w - len(tpos) - right_len - 6)
            filled = min(bar_w, int(bar_w * pos / dur))
            y, x = h - 3, 2
            safe(self.scr, y, x, tpos + " ", curses.color_pair(11))
            x += len(tpos) + 1
            safe(self.scr, y, x, "█" * filled, curses.color_pair(7) | curses.A_BOLD)
            x += filled
            safe(self.scr, y, x, "░" * (bar_w - filled), curses.color_pair(8))
            x += bar_w - filled
            safe(self.scr, y, x, f" {tdur} {pct:3d}%", curses.color_pair(11))

        chips = []
        if self.queue:
            chips.append(f"[{self.q_idx + 1}/{len(self.queue)}]")
        if self.shuffle:
            chips.append("SHUF")
        if self.repeat != "off":
            chips.append(f"R:{self.repeat}")
        if self.eq != "flat":
            chips.append(f"EQ:{self.eq}")
        sp = self.gp("speed", 1.0) or 1.0
        if abs(sp - 1.0) > 0.01:
            chips.append(f"{sp:.2f}x")
        if self.gp("mute", False):
            chips.append("MUTE")
        if self.sleep_until:
            rem = max(0, int(self.sleep_until - time.monotonic()))
            chips.append(f"zz{rem // 60:02d}:{rem % 60:02d}")
        chip_text = " ".join(chips)
        safe(self.scr, h - 2, 1, chip_text, curses.color_pair(2))

        # Small bar visualizer, right side of chips row
        if self.current_path:
            viz_x = min(w - self.viz_bars - 2, len(chip_text) + 3)
            self.draw_viz(h, w, viz_x)

        if w >= 70:
            hint = " 1-3 tabs  ↑↓  ⏎  ␣  n/p  E=EQ  e=change  /  ?  q"
        else:
            hint = " E=EQ • e=Change • ? help"
        safe(self.scr, h - 1, 0, hint, curses.color_pair(6))

    def draw_help(self, h, w):
        for i, line in enumerate(HELP):
            y = 4 + i
            if y >= h - 1:
                break
            safe(self.scr, y, 0, " " * (w - 1))
            attr = (curses.color_pair(2) | curses.A_BOLD) if i == 0 else curses.color_pair(11)
            safe(self.scr, y, 0, line[:w - 1], attr)

    def draw(self):
        scr = self.scr
        scr.erase()
        h, w = scr.getmaxyx()
        if h < 12 or w < 30:
            safe(scr, 0, 0, "Terminal is too small. Enlarge it")
            scr.refresh()
            return
        self.draw_header(w)
        self.draw_tabs(w)
        if self.help_open:
            self.draw_help(h, w)
        elif self.eq_menu_open:
            self.draw_eq_menu(h, w)
        elif self.theme_menu_open:
            self.draw_theme_menu(h, w)
        elif self.now_playing_open:
            self.draw_now_playing(h, w)
        elif self.lyrics_path:
            self.draw_lyrics(h, w)
        elif self.info_path:
            self.draw_info(h, w)
        else:
            self.draw_list(self.rows(), h, w)
        self.draw_player(h, w)
        scr.refresh()

    # ---------- input ----------
    def handle_normal(self, code, ch):
        rows = self.rows()
        last = max(0, len(rows) - 1)
        cur = rows[min(self.idx, last)] if rows else None

        if ch == "q":
            return False
        if ch in ("1", "2", "3"):
            self.switch_tab(int(ch) - 1)
        elif code == 9:
            self.switch_tab((self.tab + 1) % len(TABS))
        elif code == curses.KEY_UP:
            self.idx = max(0, self.idx - 1)
        elif code == curses.KEY_DOWN:
            self.idx = min(last, self.idx + 1)
        elif code == curses.KEY_PPAGE:
            self.idx = max(0, self.idx - 10)
        elif code == curses.KEY_NPAGE:
            self.idx = min(last, self.idx + 10)
        elif ch == "g":
            self.idx = 0
        elif ch == "G":
            self.idx = last
        elif code in (curses.KEY_LEFT, curses.KEY_BACKSPACE, 127, 8):
            if self.tab == 2 and cur:
                self.adjust_setting(cur[2], -1)
            elif self.tab == 1:
                self.go_up()
        elif code == curses.KEY_RIGHT:
            if self.tab == 2 and cur:
                self.adjust_setting(cur[2], +1)
            else:
                self.seek(SET["seek_step"])
        elif code in (10, 13):
            if cur:
                self.activate(cur)
        elif ch == " ":
            self.toggle_pause()
        elif ch == K["next"]:
            self.next_track()
        elif ch == K["prev"]:
            self.next_track(step=-1)
        elif ch in ("+", "="):
            self.change_volume(SET["volume_step"])
        elif ch == "-":
            self.change_volume(-SET["volume_step"])
        elif ch == K["mute"]:
            self._safe_set("mute", not self.gp("mute", False))
        elif ch == K["slower"]:
            self.set_speed((self.gp("speed", 1.0) or 1.0) - 0.25)
        elif ch == K["faster"]:
            self.set_speed((self.gp("speed", 1.0) or 1.0) + 0.25)
        elif ch == K["speed_reset"]:
            self.set_speed(1.0)
        elif ch == K["sleep"]:
            self.cycle_sleep()
        elif ch == "T":
            ans = self.prompt(" Sleep minutes (0 = off): ")
            try:
                self.set_sleep_minutes(int(ans))
            except ValueError:
                pass
        elif ch == "L":
            self.open_lyrics()
        elif ch == "N":
            self.open_now_playing()
        elif ch == "J":
            self.seek(-30)
        elif ch == "E":
            self.open_eq_menu()
        elif ch == "e":
            self.cycle_eq()
        elif ch == K["play_all"]:
            if self.tab == 1 and self.lib_view == 1:
                V = LIB.view
                if V:
                    paths = sorted(V["under"].get(self.cur_dir, []))
                    if paths:
                        self.set_queue(paths, 0)
                        self.status = f" Folder: {os.path.basename(self.cur_dir)} ({len(paths)})"
                    else:
                        self.status = "Nothing in this folder"
            else:
                files = [r[2] for r in rows if r[0] in ("file", "qitem")]
                if files:
                    self.set_queue(files, 0)
                    self.status = f"Playing {len(files)} tracks"
        elif ch == K["shuffle"]:
            self.toggle_shuffle()
        elif ch == K["repeat"]:
            i = REPEAT_MODES.index(self.repeat)
            self.repeat = REPEAT_MODES[(i + 1) % len(REPEAT_MODES)]
            SET["repeat"] = self.repeat
            self.persist()
        elif ch == K["search"]:
            self.open_search()
        elif ch == "i":
            if cur and cur[0] in ("file", "qitem"):
                self.info_path = cur[2]
            else:
                self.status = "Track info is only available for music tracks"
        elif ch == "f":
            if cur and cur[0] in ("file", "qitem"):
                self.toggle_favorite(cur[2])
            elif self.current_path:
                self.toggle_favorite(self.current_path)
        elif ch == "R":
            if LIB.scanning:
                self.status = "A scan is already in progress"
            else:
                LIB.start_scan()
                self.status = "Scanning library..."
        elif ch == K["jump_playing"]:
            self.jump_to_playing()
        elif ch == K["write_playlist"]:
            self.save_playlist()
        elif ch == K["bookmarks"]:
            self.do_bookmarks()
        elif ch == "d":
            if self.tab == 1 and self.lib_view == 5:
                self.remove_from_queue()
            else:
                self.status = "d only works in Queue view"
        elif ch == "c":
            if self.tab == 1 and self.lib_view == 5:
                self.clear_queue()
        elif ch == "x":
            if cur and cur[0] in ("file", "qitem"):
                self.delete_current(cur[2])
        elif ch == "o":
            if self.tab == 1 and self.lib_view == 1 and cur and cur[0] in ("fdir", "fdir_up"):
                folder = cur[2]
                self.tab = 0
                self.folder_filter = folder
                self.idx = 0
                self.scroll = 0
                self.status = f"  {os.path.basename(folder)}  ·  1 = poora All"
            else:
                self.status = "o only works on folders in Library / Folders"
        elif ch == K["help"]:
            self.help_open = True
        return True

    def handle(self, code, ch):
        if self.search_on:
            return self.handle_search(code, ch)
        return self.handle_normal(code, ch)

    def run(self):
        self.scr.nodelay(True)
        self.scr.timeout(40)
        self._safe_set("volume", self.user_vol)
        self.apply_eq()
        try:
            while True:
                self.tick_fade()
                self.tick_sleep()
                self.tick_library()
                self.tick_session()
                self.tick_viz()
                self.maybe_autonext()
                self.draw()
                code, ch = read_key(self.scr)
                if code is None:
                    continue
                if self.help_open:
                    self.help_open = False
                    continue
                if self.eq_menu_open:
                    self.handle_eq_menu(code, ch)
                    continue
                if self.theme_menu_open:
                    self.handle_theme_menu(code, ch)
                    continue
                if self.now_playing_open:
                    self.now_playing_open = False
                    continue
                if self.lyrics_path:
                    if code == curses.KEY_UP:
                        self.lyrics_scroll = max(0, self.lyrics_scroll - 1)
                    elif code == curses.KEY_DOWN:
                        self.lyrics_scroll += 1
                    else:
                        self.lyrics_path = None
                    continue
                if self.info_path:
                    self.info_path = None
                    continue
                if not self.handle(code, ch):
                    break
        finally:
            try:
                self._safe_set("pause", True)
            except Exception:
                pass
            self.remember_position(self.current_path)
            self.save_session()
            self.persist()


def main(stdscr, player):
    try:
        curses.start_color()
        curses.use_default_colors()
    except curses.error:
        pass
    curses.curs_set(0)
    init_theme(SET["theme"])
    App(stdscr, player).run()


def _cleanup_player(player):
    if player is None:
        return
    try:
        player.terminate()
    except Exception:
        pass
    try:
        pid = player.process.pid if hasattr(player, "process") else None
        if pid:
            time.sleep(0.15)
            os.kill(pid, signal.SIGKILL)
    except Exception:
        pass


def _install_signal_handlers(player):
    def handler(signum, frame):
        _cleanup_player(player)
        os._exit(0)
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        try:
            signal.signal(sig, handler)
        except Exception:
            pass


if __name__ == "__main__":
    if not LIB.load():
        LIB.start_scan()
    _player = None
    try:
        _player = mpv.MPV(**build_mpv_opts(EXTRA_FLAGS))
    except Exception as e:
        sys.exit(f"Could not start mpv: {e}\nCheck: mpv --list-options | grep <flag>")
    atexit.register(_cleanup_player, _player)
    _install_signal_handlers(_player)
    try:
        curses.wrapper(main, _player)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Crash: {e}", file=sys.stderr)
    finally:
        _cleanup_player(_player)
        os._exit(0)
