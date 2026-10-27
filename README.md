# NBA LIVE 27 (NBA Live 10 mod for RPCS3)

A roster, look and feel overhaul for NBA Live 10 on PS3, played in the RPCS3 emulator.

What the mod changes:

- Rosters brought up to the end of the 2010-11 season
- Elite 11 faces and jerseys
- Sharpened textures
- Kobe intro videos, a Press Start screen and new menu art
- NBA LIVE 27 title and icon
- Crowd audio and arena haze
- Optional ReShade lighting setup (Windows)

The base game is not included. You need your own copy of NBA Live 10 for PS3 (USA, title ID `BLUS30393`).

The mod was made by Instagram user [@drewskiiie247](https://www.instagram.com/drewskiiie247/) and is shared here with their permission. The installer, packaging and these docs were put together with Claude.

## Quick install (Windows, Linux, macOS, Steam Deck)

1. Install RPCS3 and get NBA Live 10 (`BLUS30393`) running. Boot it once until you reach the title screen so RPCS3 installs the game data, then close RPCS3.
2. Install Python 3.8 or newer if you do not have it (python.org on Windows and macOS, already there on most Linux).
3. Download `install.py` from this repo (green Code button, or the raw file).
4. Run it:

```
python install.py
```

It finds your RPCS3 folder, downloads the mod parts from the Releases page, checks them, backs up every file it replaces, installs the mod and writes a graphics preset for the game.

If it cannot find RPCS3, or you keep RPCS3 somewhere unusual, tell it:

```
python install.py --rpcs3-dir "D:\Emulators\rpcs3"
```

That folder is the one that contains `dev_hdd0` (on Windows it sits next to `rpcs3.exe`). On Linux it is usually `~/.config/rpcs3`, or `~/.var/app/net.rpcs3.RPCS3/config/rpcs3` for the Flatpak.

Useful options:

| Option | What it does |
| --- | --- |
| `--preset low` / `balanced` / `high` | Picks the graphics preset. `balanced` is the default. |
| `--parts-dir <folder>` | Use mod zips you already downloaded from Releases instead of downloading. |
| `--game-dir <folder>` | Folder that holds `PS3_GAME`, if you run the game from a disc dump and the installer does not find it. |
| `--no-config` | Do not write a settings file, keep your own RPCS3 settings. |
| `--dry-run` | Show what would change, change nothing. |
| `--uninstall` | Put the original files back. |

Then start a **new** franchise or save. Old saves keep their old rosters.

## Manual install

Use this if you do not want to run the script.

1. Boot the game once in RPCS3, then close it.
2. From the latest Release, download every `nba-live-27-hdd0-part*.zip` and extract them into your RPCS3 `dev_hdd0` folder, so you end up with `dev_hdd0/game/BLUS30393/USRDIR/...`. Say yes to replacing files.
3. Disc dump only: download every `nba-live-27-disc-part*.zip` and extract it into the folder that contains `PS3_GAME`. This changes the title and icon to NBA LIVE 27 and swaps the crowd audio. Back that folder up first.
4. Optional: copy a settings file from this repo's `configs` folder to `custom_configs/config_BLUS30393.yml` inside your RPCS3 config folder, or set the options yourself using [SETTINGS.md](SETTINGS.md).

Backing up the files you replace is up to you here. The installer does it automatically.

## Controller

Any controller RPCS3 supports works. In RPCS3 open Configure, then Pads, pick your controller, and set up the buttons. To keep this game separate from your others, right-click NBA LIVE 27 in the game list, choose Change Custom Pad Configuration, and set it there. More in [SETTINGS.md](SETTINGS.md).

## Settings, performance and problems

See [SETTINGS.md](SETTINGS.md). The short version: the biggest lag cause is a high Resolution Scale. If it stutters, use `--preset low`, or lower Resolution Scale in RPCS3 under GPU. The first few minutes always stutter a little while RPCS3 builds its shader cache.

## Uninstall

```
python install.py --uninstall
```

The installer keeps the original files it replaced in a `nba_live_27_backup` folder inside your RPCS3 folder, and puts them back.

## Legal

No game files are included, only the mod's changes. You need your own legitimate copy of NBA Live 10. This is an unofficial fan project and is not affiliated with or endorsed by EA or the NBA.
