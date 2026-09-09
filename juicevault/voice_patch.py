import discord

from .juicevault import JuiceVault


async def stay_in_current_voice(self, guild, channel):
    """Respect manual Discord voice moves; only use channel as a reconnect fallback."""
    voice = guild.voice_client
    if voice and voice.is_connected():
        # The user may have moved the bot to another VC. Never force it back
        # to the channel where the 24/7 player was originally started.
        return voice
    return await channel.connect(reconnect=True, timeout=30)


def patch_voice_location():
    JuiceVault._connect = stay_in_current_voice
