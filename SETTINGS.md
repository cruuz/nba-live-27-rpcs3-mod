# Settings guide

All of these are per game. In RPCS3, right-click NBA LIVE 27 and choose Change Custom Configuration. The installer writes a starting point for you, and you can change anything afterwards.

## Pick a preset

Low-end means a 4 to 6 core CPU, a laptop, a Steam Deck or an older or entry graphics card. High-end means an 8 core or better CPU from the last few years and something like an RTX 3070 or RX 6800 or better.

| RPCS3 setting | low | balanced (default) | high |
| --- | --- | --- | --- |
| GPU, Renderer | Vulkan | Vulkan | Vulkan |
| GPU, Resolution Scale | 100% | 200% | 300% |
| GPU, Anisotropic Filter | 4x | 8x | 16x |
| GPU, Anti-Aliasing (MSAA) | Disabled | Disabled | Auto |
| GPU, Shader Mode | Async | Async | Async |
| CPU, PPU and SPU Decoder | Recompiler (LLVM) | Recompiler (LLVM) | Recompiler (LLVM) |
| CPU, SPU Block Size | Safe | Safe | Safe |
| Advanced, Frame Limit | Auto | Auto | Auto |

Resolution Scale is the setting that matters most. 100% is 720p, 200% is about 1440p, 300% is about 2160p. A previous version of this mod shipped at 425%, which only a very strong GPU can run. If you see slow motion, lower it first.

macOS uses Vulkan through MoltenVK, so start from the low preset there. On Linux, use the Vulkan driver for your GPU (Mesa RADV for AMD, the proprietary driver for NVIDIA).

## Controller

- Configure, Pads, choose your controller in the Device list, map the buttons. Xbox style pads work best with the SDL or XInput handler, PlayStation pads with DualShock 3 or DualSense, 8BitDo and similar with SDL.
- For a profile used only by this game: right-click the game, Change Custom Pad Configuration.
- If the game ignores the pad, check that the Player 1 handler is not set to the keyboard and that the controller is awake.

## ReShade lighting (optional, Windows)

The Releases page has `nba-live-27-reshade-extras.zip`. It holds the preset files and shaders. Install ReShade from reshade.me, pick `rpcs3.exe` and the Vulkan option, skip the effect downloads, then unpack the extras zip next to `rpcs3.exe` and replace files. Press Home in game to open the menu. Use `ReShadePreset_Live10_Low.ini` on weaker PCs.

| Effect | What it does | High-end | Low-end |
| --- | --- | --- | --- |
| MXAO | soft shadows and light bounce | on | off |
| SSR | floor reflections | off | off |
| StandsHaze | dark haze over the crowd | on | on |
| ShadowLift | brightens dark areas a little | on | on |

SSR can leave ghost trails behind fast players, so only turn it on if you do not see any.

## Common problems

| Problem | Fix |
| --- | --- |
| Ghost trails behind players | Turn SSR off in the ReShade menu. |
| Stutter or slow motion | Lower Resolution Scale, then turn MXAO off. |
| Screen tearing | Turn VSync on. |
| Too dark or too bright | ReShade menu, MXAO, Indirect Lighting Amount, or StandsHaze, Strength. |
| Court looks foggy | StandsHaze, raise Start distance. |
| Black bars on a wide monitor | Normal, the game is 16:9. |
| First minutes stutter | Normal, RPCS3 is building its shader cache. |
| New rosters not showing | Start a new season or franchise. Old saves keep their old rosters. |
| Installer says the game data is missing | Boot NBA Live 10 once in RPCS3 first. |
| Installer cannot find RPCS3 | Pass `--rpcs3-dir` with the folder that contains `dev_hdd0`. |
