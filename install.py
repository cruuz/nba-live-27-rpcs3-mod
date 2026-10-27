#!/usr/bin/env python3
"""NBA LIVE 27 (NBA Live 10 PS3 mod) installer for RPCS3.

Works on Windows, Linux (native, AppImage, Flatpak), macOS and Steam Deck.
Needs only Python 3.8+ (standard library). It never touches the base game
beyond the files the mod replaces, and it backs up everything it overwrites.

Examples
  python install.py                       find RPCS3, download the mod, install it
  python install.py --parts-dir ./parts   use parts you already downloaded
  python install.py --preset low          lighter RPCS3 settings for weaker PCs
  python install.py --dry-run             show what would happen, change nothing
  python install.py --uninstall           put the original files back
"""
import argparse
import datetime
import hashlib
import json
import os
import platform
import re
import shutil
import sys
import tempfile
import urllib.request
import zipfile

TITLE_ID = "BLUS30393"
REPO = "cruuz/nba-live-27-rpcs3-mod"
RELEASE_TAG = "v1.0"
BASE_URL = "https://github.com/%s/releases/download/%s/" % (REPO, RELEASE_TAG)
BACKUP_DIRNAME = "nba_live_27_backup"
STATE_NAME = "install_state.json"

# Partial custom config. RPCS3 fills every key not listed here from your global settings,
# so this stays valid across RPCS3 versions and never pins a GPU or audio device.
PRESETS = {
    "low":      dict(scale=100, aniso=4,  msaa="Disabled"),
    "balanced": dict(scale=200, aniso=8,  msaa="Disabled"),
    "high":     dict(scale=300, aniso=16, msaa="Auto"),
}
CONFIG_TEMPLATE = """\
# NBA LIVE 27 preset "{preset}" written by install.py. Edit freely, or delete this file
# to fall back to your global RPCS3 settings.
Core:
  PPU Decoder: Recompiler (LLVM)
  SPU Decoder: Recompiler (LLVM)
  SPU Block Size: Safe
  SPU XFloat Accuracy: Approximate
  LLVM Precompilation: true
Video:
  Renderer: Vulkan
  Resolution Scale: {scale}
  Anisotropic Filter Override: {aniso}
  MSAA: {msaa}
  Multithreaded RSX: true
  Relaxed ZCULL Sync: true
  Accurate ZCULL stats: false
  Vulkan:
    Asynchronous Texture Streaming: true
"""


def say(msg=""):
    print(msg, flush=True)


def die(msg):
    say("\nERROR: " + msg)
    sys.exit(1)


# ---------------------------------------------------------------- locating RPCS3

def candidate_rpcs3_dirs():
    home = os.path.expanduser("~")
    c = []
    if platform.system() == "Windows":
        c += [os.getcwd(), os.path.dirname(os.path.abspath(__file__)),
              os.path.join(os.environ.get("APPDATA", ""), "rpcs3"),
              os.path.join(os.environ.get("LOCALAPPDATA", ""), "rpcs3")]
        for drive in "CDEFG":
            c += [drive + ":\\rpcs3", drive + ":\\Emulators\\rpcs3", drive + ":\\Games\\rpcs3"]
    elif platform.system() == "Darwin":
        c += [os.path.join(home, "Library/Application Support/rpcs3"),
              os.path.join(home, ".config/rpcs3")]
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
        c += [os.path.join(xdg, "rpcs3"),
              os.path.join(home, ".var/app/net.rpcs3.RPCS3/config/rpcs3"),
              os.path.join(home, ".local/share/rpcs3"),
              os.path.join(home, "rpcs3")]
    return [p for p in c if p]


def is_rpcs3_dir(p):
    return os.path.isdir(os.path.join(p, "dev_hdd0")) and (
        os.path.isfile(os.path.join(p, "config.yml")) or os.path.isfile(os.path.join(p, "config", "config.yml"))
        or os.path.isdir(os.path.join(p, "dev_flash")))


def find_rpcs3_dir(arg):
    if arg:
        arg = os.path.abspath(os.path.expanduser(arg))
        if not os.path.isdir(os.path.join(arg, "dev_hdd0")):
            die("%s has no dev_hdd0 folder. Point --rpcs3-dir at the folder that holds dev_hdd0 "
                "(next to rpcs3.exe on Windows)." % arg)
        return arg
    for p in candidate_rpcs3_dirs():
        if is_rpcs3_dir(p):
            return p
    die("Could not find your RPCS3 folder. Run again with --rpcs3-dir \"<folder that contains dev_hdd0>\".")


def find_game_folder(rpcs3_dir, arg):
    """Folder that contains PS3_GAME for the disc copy of the game, or None."""
    def norm(p):
        p = os.path.abspath(os.path.expanduser(p))
        if os.path.basename(p) == "PS3_GAME":
            p = os.path.dirname(p)
        return p if os.path.isdir(os.path.join(p, "PS3_GAME")) else None
    if arg:
        g = norm(arg)
        if not g:
            die("%s does not contain a PS3_GAME folder." % arg)
        return g
    games_yml = os.path.join(rpcs3_dir, "games.yml")
    if os.path.isfile(games_yml):
        with open(games_yml, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.match(r"^%s:\s*(.+?)\s*$" % TITLE_ID, line)
                if m:
                    return norm(m.group(1).strip("\"'"))
    return None


# ---------------------------------------------------------------- getting the parts

def load_manifest(parts_dir):
    local = os.path.join(parts_dir, "manifest.json") if parts_dir else None
    if local and os.path.isfile(local):
        with open(local) as f:
            return json.load(f)
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest.json")
    if os.path.isfile(here):
        with open(here) as f:
            return json.load(f)
    say("Fetching manifest ...")
    with urllib.request.urlopen(BASE_URL + "manifest.json") as r:
        return json.load(r)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def download(url, dest, total):
    req = urllib.request.Request(url, headers={"User-Agent": "nba-live-27-installer"})
    done = 0
    with urllib.request.urlopen(req) as r, open(dest, "wb") as out:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            out.write(b)
            done += len(b)
            if total:
                print("\r  %s  %d / %d MB" % (os.path.basename(dest), done >> 20, total >> 20),
                      end="", flush=True)
    print()


def fetch_part(part, parts_dir, cache):
    name = part["file"]
    for d in (parts_dir, cache):
        if d and os.path.isfile(os.path.join(d, name)):
            p = os.path.join(d, name)
            if sha256(p) == part["sha256"]:
                return p
            say("  %s is corrupt or incomplete, fetching again" % name)
    os.makedirs(cache, exist_ok=True)
    dest = os.path.join(cache, name)
    download(BASE_URL + name, dest, part.get("bytes"))
    if sha256(dest) != part["sha256"]:
        os.remove(dest)
        die("Checksum mismatch on %s. Download it again." % name)
    return dest


# ---------------------------------------------------------------- applying files

def safe_target(root, rel):
    target = os.path.normpath(os.path.join(root, rel))
    if os.path.commonpath([os.path.abspath(root), os.path.abspath(target)]) != os.path.abspath(root):
        die("Refusing to write outside the target folder: %s" % rel)
    return target


def apply_zip(zpath, root, label, backup_root, state, dry):
    n_new = n_over = 0
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            rel = info.filename
            target = safe_target(root, rel)
            key = label + "/" + rel
            if os.path.exists(target):
                n_over += 1
                if key not in state["backed_up"] and not dry:
                    b = os.path.join(backup_root, label, rel)
                    os.makedirs(os.path.dirname(b), exist_ok=True)
                    shutil.copy2(target, b)
                    state["backed_up"].append(key)
            else:
                n_new += 1
                if key not in state["created"] and not dry:
                    state["created"].append(key)
            if not dry:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with z.open(info) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst, 1 << 20)
    return n_new, n_over


def config_path(rpcs3_dir):
    """Windows keeps settings in <rpcs3>/config, Linux and macOS keep them in the folder itself."""
    if os.path.isfile(os.path.join(rpcs3_dir, "config.yml")) or os.path.isdir(os.path.join(rpcs3_dir, "custom_configs")):
        base = rpcs3_dir
    elif os.path.isdir(os.path.join(rpcs3_dir, "config")):
        base = os.path.join(rpcs3_dir, "config")
    else:
        base = rpcs3_dir
    return os.path.join(base, "custom_configs", "config_%s.yml" % TITLE_ID)


def write_config(rpcs3_dir, preset, backup_root, dry):
    path = config_path(rpcs3_dir)
    cfg_dir = os.path.dirname(path)
    if dry:
        say("  would write %s (preset %s)" % (path, preset))
        return
    os.makedirs(cfg_dir, exist_ok=True)
    if os.path.exists(path):
        os.makedirs(backup_root, exist_ok=True)
        shutil.copy2(path, os.path.join(backup_root, "config_%s.yml.before" % TITLE_ID))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(CONFIG_TEMPLATE.format(preset=preset, **PRESETS[preset]))
    say("  wrote %s (preset %s)" % (path, preset))


# ---------------------------------------------------------------- uninstall

def uninstall(rpcs3_dir, game_dir):
    backup_root = os.path.join(rpcs3_dir, BACKUP_DIRNAME)
    sp = os.path.join(backup_root, STATE_NAME)
    if not os.path.isfile(sp):
        die("No install record found in %s. Nothing to undo." % backup_root)
    with open(sp) as f:
        state = json.load(f)
    roots = {"hdd0": os.path.join(rpcs3_dir, "dev_hdd0"), "disc": state.get("game_dir") or game_dir}
    for key in state["created"]:
        label, rel = key.split("/", 1)
        if roots.get(label):
            t = os.path.join(roots[label], rel)
            if os.path.isfile(t):
                os.remove(t)
    for key in state["backed_up"]:
        label, rel = key.split("/", 1)
        if roots.get(label):
            t = os.path.join(roots[label], rel)
            os.makedirs(os.path.dirname(t), exist_ok=True)
            shutil.copy2(os.path.join(backup_root, label, rel), t)
    before = os.path.join(backup_root, "config_%s.yml.before" % TITLE_ID)
    cfg = config_path(rpcs3_dir)
    if os.path.isfile(before):
        shutil.copy2(before, cfg)
    elif state.get("wrote_config") and os.path.isfile(cfg):
        os.remove(cfg)
    os.remove(sp)
    say("Original files restored. Backup copies are still in %s if you want to delete them." % backup_root)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rpcs3-dir", help="folder that contains dev_hdd0 (next to rpcs3.exe on Windows)")
    ap.add_argument("--game-dir", help="folder that contains PS3_GAME, only if you run the game from a disc dump")
    ap.add_argument("--parts-dir", help="folder with already-downloaded mod parts (zips + manifest.json)")
    ap.add_argument("--preset", choices=sorted(PRESETS), default="balanced", help="RPCS3 settings preset")
    ap.add_argument("--no-config", action="store_true", help="do not write an RPCS3 settings file")
    ap.add_argument("--reshade", action="store_true", help="also unpack the optional ReShade files next to --exe-dir")
    ap.add_argument("--exe-dir", help="folder that holds the RPCS3 executable (only for --reshade)")
    ap.add_argument("--dry-run", action="store_true", help="show what would change, change nothing")
    ap.add_argument("--uninstall", action="store_true", help="restore the original files")
    a = ap.parse_args()

    rpcs3_dir = find_rpcs3_dir(a.rpcs3_dir)
    game_dir = find_game_folder(rpcs3_dir, a.game_dir)
    say("RPCS3 folder : " + rpcs3_dir)
    say("Disc folder  : " + (game_dir or "(none found, skipping the disc overlay)"))

    if a.uninstall:
        uninstall(rpcs3_dir, game_dir)
        return

    installed = os.path.join(rpcs3_dir, "dev_hdd0", "game", TITLE_ID, "USRDIR")
    if not os.path.isdir(installed):
        die("NBA Live 10 (%s) has not installed its data yet.\n"
            "Boot the game once in RPCS3 until it reaches the title screen, close RPCS3, then run this again."
            % TITLE_ID)

    manifest = load_manifest(a.parts_dir)
    cache = os.path.join(tempfile.gettempdir(), "nba_live_27_parts")
    backup_root = os.path.join(rpcs3_dir, BACKUP_DIRNAME)
    sp = os.path.join(backup_root, STATE_NAME)
    state = {"created": [], "backed_up": [], "game_dir": game_dir, "wrote_config": False,
             "installed": datetime.datetime.now().isoformat(timespec="seconds"),
             "version": manifest.get("version")}
    if os.path.isfile(sp):  # re-running keeps the first backups, which are the true originals
        with open(sp) as f:
            state.update({k: v for k, v in json.load(f).items() if k in ("created", "backed_up")})

    free = shutil.disk_usage(rpcs3_dir).free
    need = sum(p["bytes"] for p in manifest["parts"] if p["kind"] in ("hdd0", "disc")) * 1.15
    if free < need and not a.dry_run:
        die("Not enough free space: about %d GB needed, %d GB free." % (need >> 30, free >> 30))

    for part in manifest["parts"]:
        kind = part["kind"]
        if kind == "disc" and not game_dir:
            continue
        if kind == "reshade" and not a.reshade:
            continue
        if kind == "reshade":
            if not a.exe_dir:
                die("--reshade needs --exe-dir (the folder that holds the RPCS3 executable).")
            root, label = os.path.abspath(a.exe_dir), "reshade"
        elif kind == "hdd0":
            root, label = os.path.join(rpcs3_dir, "dev_hdd0"), "hdd0"
        else:
            root, label = game_dir, "disc"
        say("\n%s" % part["file"])
        zp = fetch_part(part, a.parts_dir, cache)
        n_new, n_over = apply_zip(zp, root, label, backup_root, state, a.dry_run)
        say("  %d new files, %d replaced%s" % (n_new, n_over, " (dry run)" if a.dry_run else ""))

    if not a.no_config:
        say("\nRPCS3 settings")
        write_config(rpcs3_dir, a.preset, backup_root, a.dry_run)
        state["wrote_config"] = True

    if not a.dry_run:
        os.makedirs(backup_root, exist_ok=True)
        with open(sp, "w") as f:
            json.dump(state, f, indent=1)
    say("\nDone. Start a NEW franchise or save so the updated rosters load (old saves keep old rosters).")
    say("To undo everything later: python install.py --uninstall")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nCancelled.")
