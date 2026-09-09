# Red JuiceVault

24/7 JuiceVault music player for Red-DiscordBot.

## Install

Install FFmpeg on the host running Red, then:

```text
[p]repo add juicevault https://github.com/SKIZZOO/red-juicevault
[p]cog install juicevault juicevault
[p]load juicevault
```

Start it from the desired voice channel:

```text
[p]jv start
```

Other commands:

```text
[p]jv stop
[p]jv skip
[p]jv refresh
[p]jv status
```

The cog remembers the enabled voice channel and restores playback after a Red restart. The archive is reloaded when the queue reaches the end.

## FFmpeg

Ubuntu/Debian:

```bash
sudo apt update
sudo apt install ffmpeg
```

## JuiceVault

The cog reads `https://juicevault.xyz/files?path=Music` and supports common JSON, HTML, and plain-text directory responses. If JuiceVault requires authentication, signed URLs, or a different API response, the parser must be adapted.
