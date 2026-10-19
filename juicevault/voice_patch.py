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
    supported, _ = is_voice_recognition_supported()
    vc_enabled = await is_voice_commands_enabled_for_guild(self, guild.id)

    if voice and voice.is_connected():
        # If voice recognition is supported & enabled, but current voice_client cannot receive audio, upgrade:
        if supported and vc_enabled and not hasattr(voice, "listen"):
            try:
                ch = voice.channel
                print(f"[JuiceVault Voice] Upgrading voice connection in '{guild.name}' to VoiceRecvClient for voice commands...")
                await voice.disconnect(force=True)
                await asyncio.sleep(0.5)
                voice_cls = get_voice_client_cls()
                voice = await ch.connect(reconnect=True, timeout=15, cls=voice_cls)
            except Exception as exc:
                print(f"[JuiceVault Voice] Failed upgrading voice client: {exc}")

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

    connected_voice = None
    voice_cls = get_voice_client_cls() if (vc_enabled and supported) else discord.VoiceClient
    if voice_cls is not discord.VoiceClient:
        try:
            connected_voice = await channel.connect(reconnect=True, timeout=15, cls=voice_cls)
        except Exception as exc:
            err_msg = str(exc) or type(exc).__name__
            print(f"[JuiceVault Voice] VoiceRecvClient connection error ({type(exc).__name__}): {err_msg}")
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
