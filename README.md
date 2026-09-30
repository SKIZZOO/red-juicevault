# Red JuiceVault

A polished 24/7 JuiceVault music player for [Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot).

## UI Preview

The JuiceVault control panel provides a live Now Playing display with playback status, voice channel, category, queue information, Lyrics, EQ, and interactive playback controls.

![JuiceVault UI Preview](docs/ui-preview.png)

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
- 📱 **Mobile Web Remote & PWA** — control playback, queues, and audio EQ directly from any mobile phone browser or install it as a standalone home-screen app.
- 📷 **Instant QR Code pairing** — scan a QR code from Discord with your phone camera to connect immediately with secure token authentication.
- 🔒 **Phone Lock Screen Media Controls** — MediaSession API integration allows skipping, pausing, and seeking directly from your phone's lock screen, dynamic island, or notification center.
- ⚡ **REST API & iOS Shortcuts** — pre-built HTTP endpoints to control playback with Siri, Apple Shortcuts, Android widgets, or Tasker.
- 🎶 **Lyrics button** — opens a Genius search for the currently playing artist and track.
- 🎨 **Discord control panel** — interactive buttons for playback, search, categories, EQ, shuffle, repeat, 10-second seeking, and 📱 Remote.
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

### Mobile Remote & REST API

```text
[p]jv remote                     # Displays mobile URL, auth token, and scannable QR Code
[p]jv remote port <port>         # Change web server port (default: 8088)
[p]jv remote token [tok]         # View or set secret auth token
[p]jv remote url [url]           # Set custom domain / tunnel URL (e.g. Cloudflare / reverse proxy)
[p]jv remote ssl <cert> <key>    # Enable direct HTTPS with SSL certificate and key
[p]jv remote restart             # Restart the web remote server
[p]jv remote toggle              # Enable / disable the web remote server
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

The panel provides interactive controls for Category, Search, Refresh, Lyrics, EQ, Play/Stop, Pause/Resume, Previous, Next, Repeat, Shuffle, 10-second seeking, and a private **📱 Remote** button.

## Mobile Phone Control (Web Remote & PWA)

JuiceVault includes a built-in mobile web app and REST API powered by `aiohttp`:

1. Run `[p]jv remote` in Discord (or click **📱 Remote** on the `[p]jvpanel`).
2. Scan the QR code with your phone camera or click the link.
3. **Kinetics & OriginKit UI**: Engineered with tactile spring physics, soundwave visualizer bars, zero emojis (pure custom SVGs), and responsive layouts for both mobile phones and desktop displays.
4. **HTTPS Support**:
   - **Cloudflare Tunnel (Easiest)**: Run `cloudflared tunnel --url http://localhost:8088` and set `[p]jv remote url https://your-tunnel.trycloudflare.com` for instant free SSL.
   - **Direct SSL**: Provide your SSL cert and private key with `[p]jv remote ssl <cert_path> <key_path>`.
5. **Add to Home Screen**: In Safari (iOS) or Chrome (Android), tap Share / Menu -> *Add to Home Screen* to use it as a fullscreen app!
6. **Lock Screen Controls**: Tap *Enable* in the remote banner to activate background audio sync — now you can pause, skip, and see what's playing from your phone's lock screen and Apple Watch / Bluetooth controls.
7. **iOS Shortcuts / Siri**: In the *Shortcuts* tab of the web app, copy one-tap webhook URLs into the Apple Shortcuts app ("Get Contents of URL") to control music with Siri or widgets!

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
