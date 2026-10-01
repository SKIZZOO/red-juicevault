import asyncio
import os
import tempfile
import time
import urllib.request

SOUNDBOARD_CACHE_DIR = os.path.join(tempfile.gettempdir(), 'juicevault_soundboard')
os.makedirs(SOUNDBOARD_CACHE_DIR, exist_ok=True)

SOUNDBOARD_SOUNDS = [
    {
        "id": "sb_01",
        "name": "Are You Out of Your Mind",
        "color": "#eb2f96",
        "url": "https://www.myinstants.com/media/sounds/are-you-out-of-your-mind-greenscreen-change-quality-and-end-wont-cut-off_2.mp3"
    },
    {
        "id": "sb_02",
        "name": "FAAAH",
        "color": "#722ed1",
        "url": "https://www.myinstants.com/media/sounds/faaah.mp3"
    },
    {
        "id": "sb_03",
        "name": "Sad Violin",
        "color": "#1890ff",
        "url": "https://www.myinstants.com/media/sounds/tf_nemesis.mp3"
    },
    {
        "id": "sb_04",
        "name": "Among Us Reveal",
        "color": "#13c2c2",
        "url": "https://www.myinstants.com/media/sounds/among-us-role-reveal-sound.mp3"
    },
    {
        "id": "sb_05",
        "name": "Windows Error",
        "color": "#52c41a",
        "url": "https://www.myinstants.com/media/sounds/error_CDOxCYm.mp3"
    },
    {
        "id": "sb_06",
        "name": "Baby Laugh",
        "color": "#faad14",
        "url": "https://www.myinstants.com/media/sounds/baby-laughing-meme.mp3"
    },
    {
        "id": "sb_07",
        "name": "Punch Impact",
        "color": "#fa541c",
        "url": "https://www.myinstants.com/media/sounds/punch-gaming-sound-effect-hd_RzlG1GE.mp3"
    },
    {
        "id": "sb_08",
        "name": "Spiderman Theme",
        "color": "#f5222d",
        "url": "https://www.myinstants.com/media/sounds/spiderman-meme-song.mp3"
    },
    {
        "id": "sb_09",
        "name": "Vine Boom",
        "color": "#2f54eb",
        "url": "https://www.myinstants.com/media/sounds/vine-boom-sound-effect_KT89XIq.mp3"
    },
    {
        "id": "sb_10",
        "name": "Shocked Sound",
        "color": "#fa8c16",
        "url": "https://www.myinstants.com/media/sounds/shocked-sound-effect.mp3"
    },
    {
        "id": "sb_11",
        "name": "Dun Dun Dun",
        "color": "#a0d911",
        "url": "https://www.myinstants.com/media/sounds/dun-dun-dun-sound-effect-brass_8nFBccR.mp3"
    },
    {
        "id": "sb_12",
        "name": "Camera Shutter",
        "color": "#13c2c2",
        "url": "https://www.myinstants.com/media/sounds/zvuk-fotoapparata.mp3"
    },
    {
        "id": "sb_13",
        "name": "Fortnite Knocked",
        "color": "#eb2f96",
        "url": "https://www.myinstants.com/media/sounds/tmp_7901-951678082.mp3"
    },
    {
        "id": "sb_14",
        "name": "Emotional Damage",
        "color": "#722ed1",
        "url": "https://www.myinstants.com/media/sounds/emotional-damage-meme.mp3"
    },
    {
        "id": "sb_15",
        "name": "Cat Laugh",
        "color": "#1890ff",
        "url": "https://www.myinstants.com/media/sounds/cat-laugh-meme-1.mp3"
    },
    {
        "id": "sb_16",
        "name": "Shooting Stars",
        "color": "#13c2c2",
        "url": "https://www.myinstants.com/media/sounds/galaxy-meme.mp3"
    },
    {
        "id": "sb_17",
        "name": "Fart Reverb",
        "color": "#52c41a",
        "url": "https://www.myinstants.com/media/sounds/fart-meme-sound.mp3"
    },
    {
        "id": "sb_18",
        "name": "Final Credits",
        "color": "#faad14",
        "url": "https://www.myinstants.com/media/sounds/meme-de-creditos-finales.mp3"
    },
    {
        "id": "sb_19",
        "name": "Run AWOLNATION",
        "color": "#fa541c",
        "url": "https://www.myinstants.com/media/sounds/run-vine-sound-effect.mp3"
    },
    {
        "id": "sb_20",
        "name": "Mutahar Laugh",
        "color": "#f5222d",
        "url": "https://www.myinstants.com/media/sounds/ny-video-online-audio-converter.mp3"
    },
    {
        "id": "sb_21",
        "name": "Dexter Surprise",
        "color": "#2f54eb",
        "url": "https://www.myinstants.com/media/sounds/dexter-meme.mp3"
    },
    {
        "id": "sb_22",
        "name": "-999 Social Credit",
        "color": "#fa8c16",
        "url": "https://www.myinstants.com/media/sounds/999-social-credit-siren.mp3"
    },
    {
        "id": "sb_23",
        "name": "Huh?",
        "color": "#a0d911",
        "url": "https://www.myinstants.com/media/sounds/huh_37bAoRo.mp3"
    },
    {
        "id": "sb_24",
        "name": "Cartoon Snore",
        "color": "#13c2c2",
        "url": "https://www.myinstants.com/media/sounds/snore-mimimimimimi.mp3"
    },
    {
        "id": "sb_25",
        "name": "Xenogenesis Outro",
        "color": "#eb2f96",
        "url": "https://www.myinstants.com/media/sounds/outro-song_oqu8zAg.mp3"
    },
    {
        "id": "sb_26",
        "name": "Brain Fart",
        "color": "#722ed1",
        "url": "https://www.myinstants.com/media/sounds/long-brain-fart.mp3"
    },
    {
        "id": "sb_27",
        "name": "Oh My God",
        "color": "#1890ff",
        "url": "https://www.myinstants.com/media/sounds/oh-my-god-meme.mp3"
    },
    {
        "id": "sb_28",
        "name": "Wide Putin",
        "color": "#13c2c2",
        "url": "https://www.myinstants.com/media/sounds/my-movie-6_0RlWMvM.mp3"
    },
    {
        "id": "sb_29",
        "name": "German Motivation",
        "color": "#52c41a",
        "url": "https://www.myinstants.com/media/sounds/du-bist-gut-genug.mp3"
    },
    {
        "id": "sb_30",
        "name": "What Da Dog Doin",
        "color": "#faad14",
        "url": "https://www.myinstants.com/media/sounds/yt1s_wU4BGgD.mp3"
    },
    {
        "id": "sb_31",
        "name": "Spanish Credits",
        "color": "#fa541c",
        "url": "https://www.myinstants.com/media/sounds/meme-de-creditos-finales_qHtIjyQ.mp3"
    },
    {
        "id": "sb_32",
        "name": "Anime Wow",
        "color": "#f5222d",
        "url": "https://www.myinstants.com/media/sounds/anime-wow-sound-effect-mp3cut.mp3"
    },
    {
        "id": "sb_33",
        "name": "French Accordion",
        "color": "#2f54eb",
        "url": "https://www.myinstants.com/media/sounds/french-meme-song.mp3"
    },
    {
        "id": "sb_34",
        "name": "Mega Fart",
        "color": "#fa8c16",
        "url": "https://www.myinstants.com/media/sounds/fartmeme.mp3"
    },
    {
        "id": "sb_35",
        "name": "Sanctuary Guardian",
        "color": "#a0d911",
        "url": "https://www.myinstants.com/media/sounds/what-bottom-text-meme-sanctuary-guardian-sound-effect-hd.mp3"
    },
    {
        "id": "sb_36",
        "name": "Deja Vu Initial D",
        "color": "#13c2c2",
        "url": "https://www.myinstants.com/media/sounds/deja-vu.mp3"
    },
    {
        "id": "sb_37",
        "name": "Screaming Fighter",
        "color": "#eb2f96",
        "url": "https://www.myinstants.com/media/sounds/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-e-lutador.mp3"
    },
    {
        "id": "sb_38",
        "name": "Aayein Baingan",
        "color": "#722ed1",
        "url": "https://www.myinstants.com/media/sounds/aayein-meme.mp3"
    },
    {
        "id": "sb_39",
        "name": "Directed by Robert Weide",
        "color": "#1890ff",
        "url": "https://www.myinstants.com/media/sounds/directed-by-robert-b_voI2Z4T.mp3"
    },
    {
        "id": "sb_40",
        "name": "Squeaky Duck",
        "color": "#13c2c2",
        "url": "https://www.myinstants.com/media/sounds/duck-toy-sound.mp3"
    },
    {
        "id": "sb_41",
        "name": "Red Alert Alarm",
        "color": "#52c41a",
        "url": "https://www.myinstants.com/media/sounds/danger-alarm-sound-effect-meme.mp3"
    },
    {
        "id": "sb_42",
        "name": "You Have To Say Fine",
        "color": "#faad14",
        "url": "https://www.myinstants.com/media/sounds/they-ask-you-how-you-are-and-you-just-have-to-say-that-youre-fine-sound-effect_IgYM1CV.mp3"
    },
    {
        "id": "sb_43",
        "name": "FBI Open Up",
        "color": "#fa541c",
        "url": "https://www.myinstants.com/media/sounds/fbi-open-up_dwLhIFf.mp3"
    },
    {
        "id": "sb_44",
        "name": "Bruh",
        "color": "#f5222d",
        "url": "https://www.myinstants.com/media/sounds/movie_1_C2K5NH0.mp3"
    },
    {
        "id": "sb_45",
        "name": "AUUGHHH",
        "color": "#2f54eb",
        "url": "https://www.myinstants.com/media/sounds/auughhh.mp3"
    },
    {
        "id": "sb_46",
        "name": "Camera Shutter",
        "color": "#fa8c16",
        "url": "https://www.myinstants.com/media/sounds/dobroe-utro-moia-devochka.mp3"
    },
    {
        "id": "sb_47",
        "name": "Oi Oi Cat",
        "color": "#a0d911",
        "url": "https://www.myinstants.com/media/sounds/oi-oi-oe-oi-a-eye-eye.mp3"
    },
    {
        "id": "sb_48",
        "name": "Lobotomy Corporation",
        "color": "#13c2c2",
        "url": "https://www.myinstants.com/media/sounds/lobotomy-sound-effect.mp3"
    },
    {
        "id": "sb_49",
        "name": "Buffering Ring",
        "color": "#eb2f96",
        "url": "https://www.myinstants.com/media/sounds/loading-lost-connection-green-screen-with-sound-effect-2_K8HORkT.mp3"
    },
    {
        "id": "sb_50",
        "name": "Heavy Punch",
        "color": "#722ed1",
        "url": "https://www.myinstants.com/media/sounds/punch-sound-effect-meme.mp3"
    }
]


def get_soundboard_sounds():
    return SOUNDBOARD_SOUNDS


def get_sound_by_id(sound_id):
    clean = str(sound_id or '').strip().lower()
    for s in SOUNDBOARD_SOUNDS:
        if s['id'].lower() == clean or s['name'].lower() == clean:
            return s
    return None


def _download_file(url, target_path):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'audio/mpeg,audio/*;q=0.9,*/*;q=0.8',
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = resp.read()
    temp_target = target_path + '.tmp'
    with open(temp_target, 'wb') as f:
        f.write(data)
    if os.path.isfile(target_path):
        try:
            os.remove(target_path)
        except OSError:
            pass
    os.replace(temp_target, target_path)
    return target_path


async def get_sound_file(sound):
    sound_id = sound['id']
    target_path = os.path.join(SOUNDBOARD_CACHE_DIR, f"{sound_id}.mp3")
    if os.path.isfile(target_path) and os.path.getsize(target_path) > 1024:
        return target_path

    return await asyncio.to_thread(_download_file, sound['url'], target_path)


async def play_soundboard_in_guild(main_cog, guild_id, sound_id):
    guild = main_cog.bot.get_guild(guild_id)
    if not guild:
        return False, "Guild not found."

    voice = guild.voice_client
    if not voice or not voice.is_connected():
        return False, "Bot is not in a voice channel. Start playback with 4jv start first."

    sound = get_sound_by_id(sound_id)
    if not sound:
        return False, f"Sound not found: {sound_id}"

    try:
        sound_path = await get_sound_file(sound)
    except Exception as exc:
        return False, f"Failed to download sound: {exc}"

    if not hasattr(main_cog, '_preserved_files'):
        main_cog._preserved_files = set()

    gid = guild_id
    current = main_cog.current.get(gid)
    was_playing = bool(voice.is_playing() and not voice.is_paused())
    current_pos = 0.0
    local_path = main_cog.current_files.get(gid)

    # 1. If currently playing a track (and not already a soundboard sound), save resume state
    if current and not current.get('_is_soundboard'):
        base = float(main_cog.play_positions.get(gid, 0.0))
        started = getattr(voice, '_jv_started_at', None)
        if started is not None and was_playing:
            base += max(0.0, time.monotonic() - started)
        current_pos = base

        if local_path and os.path.isfile(local_path):
            main_cog._preserved_files.add(local_path)

        resume_track = dict(
            current,
            _jv_seek_copy=True,
            _cached_file=local_path,
            _resume_position=current_pos,
            _resume_was_playing=was_playing,
        )
        main_cog.manual_queues.setdefault(gid, []).insert(0, resume_track)

    # 2. Build soundboard track entry
    sb_track = {
        'id': f"soundboard:{sound['id']}",
        'title': sound['name'],
        'artist': 'Soundboard',
        'length': '0:05',
        'file_name': f"soundboard_{sound['id']}.mp3",
        '_cached_file': sound_path,
        '_is_soundboard': True,
        '_sound_id': sound['id'],
        '_sound_color': sound.get('color', '#eb2f96'),
        'url': sound['url'],
    }

    # 3. Insert soundboard track at the very front of requested queue
    main_cog.manual_queues.setdefault(gid, []).insert(0, sb_track)

    # 4. Set play offset to 0 for the sound effect
    main_cog.play_positions[gid] = 0.0
    if not hasattr(main_cog, 'pause_after_seek'):
        main_cog.pause_after_seek = {}
    main_cog.pause_after_seek[gid] = False

    # 5. Stop voice playback so _player loop immediately triggers and plays the soundboard sound
    if voice.is_playing() or voice.is_paused():
        voice.stop()
    else:
        skip_evt = main_cog.skip_events.get(gid)
        if skip_evt:
            skip_evt.set()

    return True, f"Playing sound: {sound['name']}"


async def stop_soundboard_in_guild(main_cog, guild_id):
    guild = main_cog.bot.get_guild(guild_id)
    if not guild:
        return False, "Guild not found."

    voice = guild.voice_client
    current = main_cog.current.get(guild_id)
    if not current or not current.get('_is_soundboard'):
        return False, "No soundboard sound is currently playing."

    if voice and (voice.is_playing() or voice.is_paused()):
        voice.stop()
        return True, "Stopped soundboard sound."

    return False, "Voice is not active."
