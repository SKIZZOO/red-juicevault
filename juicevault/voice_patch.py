import asyncio
import time
import discord

from .juicevault import JuiceVault
from .voice_recognition import (
    is_voice_recognition_supported,
    is_voice_commands_enabled_for_guild,
    get_voice_client_cls,
    attach_voice_command_sink,
)


async def stay_in_current_voice(self, guild, channel):
    """Respect manual Discord voice moves; only use channel as a reconnect fallback."""
    voice = guild.voice_client
    if voice and voice.is_connected():
        # The user may have moved the bot to another VC. Never force it back
        # to the channel where the 24/7 player was originally started.
        if not hasattr(voice, "_jv_connected_at"):
            voice._jv_connected_at = time.time()
        attach_voice_command_sink(self, guild)
        return voice

    # Clean up any stale or half-closed voice client to clear gateway handshake collisions
    if voice is not None:
        try:
            await voice.disconnect(force=True)
        except Exception:
            pass
        await asyncio.sleep(0.5)

    # Check if in-Discord voice commands are explicitly enabled and supported
    vc_enabled = await is_voice_commands_enabled_for_guild(self, guild.id)
    supported, _ = is_voice_recognition_supported()

    connected_voice = None
    if vc_enabled and supported:
        voice_cls = get_voice_client_cls()
        if voice_cls is not discord.VoiceClient:
            try:
                connected_voice = await channel.connect(reconnect=True, timeout=12, cls=voice_cls)
            except Exception:
                # Fallback to standard discord.VoiceClient so music playback NEVER fails!
                if guild.voice_client:
                    try:
                        await guild.voice_client.disconnect(force=True)
                    except Exception:
                        pass
                    await asyncio.sleep(0.5)
                connected_voice = None

    if connected_voice is None:
        try:
            connected_voice = await channel.connect(reconnect=True, timeout=30)
        except Exception:
            # Emergency retry after gateway cleanup
            if guild.voice_client:
                try:
                    await guild.voice_client.disconnect(force=True)
                except Exception:
                    pass
                await asyncio.sleep(1)
            connected_voice = await channel.connect(reconnect=True, timeout=35)

    if not hasattr(connected_voice, "_jv_connected_at"):
        connected_voice._jv_connected_at = time.time()

    attach_voice_command_sink(self, guild)
    return connected_voice


def patch_voice_location():
    JuiceVault._connect = stay_in_current_voice
