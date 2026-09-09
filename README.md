# Red JuiceVault

A polished 24/7 JuiceVault music player for [Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot).

## Features

- 🎵 **24/7 JuiceVault playback** — continuously plays tracks from the JuiceVault archive.
- 🔄 **Automatic queue refill** — reloads the archive when the normal queue reaches the end.
- 🎚️ **Categories** — browse JuiceVault collections such as All Music, Instrumentals, Remasters, Stems, Released, and Cut Files.
- 🔎 **JuiceVault Search** — search the archive and add results directly to Requested.
- 🌐 **External Search** — search online sources supported by `yt-dlp`, with automatic fallback to JuiceVault when external playback is exhausted or fails.
- 📥 **Requested queue** — manually requested tracks are played before the normal archive queue.
- ⏮️ **Previous / Next** — move through playback history and the queue.
- ⏩ **10-second seek** — jump backward or forward by 10 seconds.
- 🔀 **Shuffle** — randomize the normal queue.
- 🔁 **Repeat** — keep the current playback flow repeating.
- 🎚️ **Audio effects / EQ** — Flat, Bass Boost, 8D Audio, Nightcore, Slowed, Echo, Wide, and Virtual Bass.
- 🎶 **Lyrics button** — opens a Genius search for the currently playing artist and track.
- 🎨 **Discord control panel** — interactive buttons for playback, search, categories, EQ, shuffle, repeat, and seeking.
- 🔊 **Voice channel awareness** — shows the current voice channel and does not force the bot back when it is manually moved to another channel.
- 🖼️ **Album artwork** — displays JuiceVault artwork when available; external tracks do not attempt JuiceVault cover lookups.
- 🔗 **Direct track links** — the currently playing JuiceVault track links directly to its archive page.
- 👤 **Creator link** — the panel credits SKIZZOO with a link to the creator page.
- 💾 **Playback recovery** — restores the configured playback setup after a Red restart.

## Commands

The examples below use the default Red prefix `[p]`.

### Player

```text
[p]jv start
[p]jv stop
[p]jv skip
[p]jv next
[p]jv skip10
[p]jv shuffle
[p]jv status
```

### Library & search

```text
[p]jv categories
[p]jv category <name>
[p]jv search <query>
[p]jv play <query or number>
[p]jv refresh
```

### Control panel

```text
[p]jvpanel
```

The panel provides interactive controls for Category, Search, Refresh, Lyrics, EQ, Play/Stop, Pause/Resume, Previous, Next, Repeat, Shuffle, and 10-second seeking.

## Installation

Install FFmpeg on the host running Red, then add and install the repository:

```text
[p]repo add juicevault https://github.com/SKIZZOO/red-juicevault
[p]cog install juicevault juicevault
[p]load juicevault
```

Join the desired voice channel and start playback:

```text
[p]jv start
```

## Requirements

The cog uses:

- **Red-DiscordBot** — cog framework and Discord bot integration.
- **discord.py** — Discord API and voice integration through Red.
- **FFmpeg** — audio decoding and playback.
- **aiohttp** — HTTP/API requests.
- **PyNaCl** — Discord voice encryption support.
- **imageio-ffmpeg** — FFmpeg helper support.
- **yt-dlp** — external online audio search/download support.
- **davey** — Discord voice protocol support.

Python dependencies are listed in [`requirements.txt`](requirements.txt).

## JuiceVault API

The cog uses the public JuiceVault archive/API to retrieve music metadata and streamable tracks.

JuiceVault collections currently used by the cog include:

- All Music
- Instrumentals
- Remasters
- Stems
- Released
- Cut Files

## External Sources

External search uses `yt-dlp` for supported online sources. External tracks are placed into the Requested queue so they can play next, and the player returns to the JuiceVault archive when the external queue is finished.

## Credits / Thanks

### Thanks to

- 🧃 **JuiceVault** — for the music archive and API.
- 🤖 **Red-DiscordBot** — for the cog framework.
- 💬 **discord.py** — for Discord integration and voice playback support.
- 🎬 **yt-dlp** — for external source extraction and downloading.
- ⚙️ **FFmpeg** — for reliable audio processing and playback.

### Made by

**SKIZZOO**

- GitHub: [SKIZZOO](https://github.com/SKIZZOO)
- Website: [guns.lol/skizzoo](https://guns.lol/skizzoo)

## License

See the repository for the current project license and source code.
