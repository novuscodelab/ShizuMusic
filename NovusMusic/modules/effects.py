# --------------------------------------------------------------------------------
#  NovusMusic © 2026
#  Developed by Bad Munda 
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio
import os

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from NovusMusic import LOGGER, bot, call_py
from NovusMusic.core.queue import peek_current
from NovusMusic.modules.block import group_allowed, user_allowed
from NovusMusic.utils.formatters import short

# ── DB helpers using utils.db ──────────────────────────────────────────────────

def _db_save(chat_id: int) -> None:
    try:
        from NovusMusic.utils.db import save_chat_effects
        s = _get(chat_id)
        save_chat_effects(chat_id, s["speed"], s["bass"], s["enabled"])
    except Exception as e:
        LOGGER.warning(f"[Effects] DB save failed: {e}")


def _db_load(chat_id: int) -> dict:
    try:
        from NovusMusic.utils.db import load_chat_effects
        return load_chat_effects(chat_id)
    except Exception:
        return {"speed": 1.0, "bass": 0, "enabled": False}


# ── In-memory cache ────────────────────────────────────────────────────────────
_cache: dict[int, dict] = {}

SPEED_DEFAULT = 1.0
BASS_DEFAULT  = 0


def _get(chat_id: int) -> dict:
    if chat_id not in _cache:
        _cache[chat_id] = _db_load(chat_id)
    return _cache[chat_id]


def get_effects(chat_id: int) -> dict:
    return _get(chat_id).copy()


def set_speed(chat_id: int, speed: float) -> None:
    _get(chat_id)["speed"] = speed
    _db_save(chat_id)


def set_bass(chat_id: int, bass: int) -> None:
    _get(chat_id)["bass"] = bass
    _db_save(chat_id)


def set_enabled(chat_id: int, val: bool) -> None:
    _get(chat_id)["enabled"] = val
    _db_save(chat_id)


def is_effects_on(chat_id: int) -> bool:
    return _get(chat_id).get("enabled", False)


def clear_effects(chat_id: int) -> None:
    _cache.pop(chat_id, None)
    try:
        from NovusMusic.utils.db import delete_chat_effects
        delete_chat_effects(chat_id)
    except Exception:
        pass


# ── ffmpeg filter builder ──────────────────────────────────────────────────────

def _build_af(speed: float, bass: int) -> str | None:
    parts = []

    if bass and bass > 0:
        parts.append(f"equalizer=f=80:t=h:width=200:g={min(bass, 20)}")

    if speed and speed != 1.0:
        speed = round(max(0.25, min(speed, 4.0)), 2)
        if 0.5 <= speed <= 2.0:
            parts.append(f"atempo={speed}")
        elif speed < 0.5:
            parts.append("atempo=0.5,atempo=0.5")
        else:
            chain = []
            rem   = speed
            while rem > 2.0:
                chain.append("atempo=2.0")
                rem /= 2.0
            chain.append(f"atempo={round(rem, 2)}")
            parts.append(",".join(chain))

    return ",".join(parts) if parts else None


# ── Process file with ffmpeg ───────────────────────────────────────────────────

async def _process_file(src: str, speed: float, bass: int) -> str:
    af = _build_af(speed, bass)
    if not af:
        return src

    os.makedirs("downloads/effects", exist_ok=True)
    base = os.path.splitext(os.path.basename(src))[0]
    tag  = f"s{str(speed).replace('.', '')}_b{bass}"
    out  = f"downloads/effects/{base}_{tag}.mp3"

    if os.path.exists(out) and os.path.getsize(out) > 0:
        return out

    cmd = [
        "ffmpeg", "-y", "-i", src,
        "-af", af,
        "-vn", "-acodec", "libmp3lame", "-b:a", "192k",
        out,
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await asyncio.wait_for(proc.communicate(), timeout=120)

    if proc.returncode != 0 or not os.path.exists(out):
        raise Exception("ffmpeg processing failed")

    return out


# ── Stream helper ──────────────────────────────────────────────────────────────

async def _stream_from(chat_id: int, file_path: str, seek_sec: int = 0) -> None:
    from pytgcalls.types import AudioQuality, MediaStream

    ms_kwargs = dict(
        audio_parameters=AudioQuality.HIGH,
        video_flags=MediaStream.Flags.IGNORE,
    )
    if seek_sec > 0:
        ms_kwargs["ffmpeg_parameters"] = f"-ss {seek_sec}"

    try:
        await call_py.change_stream(chat_id, MediaStream(file_path, **ms_kwargs))
    except Exception:
        await call_py.play(chat_id, MediaStream(file_path, **ms_kwargs))


# ── Apply effects to current song ─────────────────────────────────────────────

async def apply_effects_now(chat_id: int, message: Message, *, seek_sec: int = -1) -> None:
    from NovusMusic.utils.youtube import resolve_stream
    from NovusMusic.modules.seek import get_current_position, set_seek_state

    song = peek_current(chat_id)
    if not song:
        await message.reply("<b> No song is currently playing.</b>", parse_mode=ParseMode.HTML)
        return

    state = _get(chat_id)
    speed = state["speed"]
    bass  = state["bass"]

    pm = await message.reply("<b> Applying effects, please wait...</b>", parse_mode=ParseMode.HTML)

    try:
        src = await resolve_stream(song["url"])
    except Exception as e:
        await pm.edit_text(f"<b> Stream resolve failed.</b>\n<code>{e}</code>", parse_mode=ParseMode.HTML)
        return

    try:
        processed = await _process_file(src, speed, bass)
    except Exception as e:
        await pm.edit_text(f"<b> ffmpeg error:</b> <code>{e}</code>", parse_mode=ParseMode.HTML)
        return

    pos = get_current_position(chat_id) if seek_sec == -1 else seek_sec

    try:
        await _stream_from(chat_id, processed, seek_sec=pos)
    except Exception as e:
        await pm.edit_text(f"<b> Playback failed:</b> <code>{e}</code>", parse_mode=ParseMode.HTML)
        return

    set_seek_state(chat_id, pos)

    speed_label = f"{speed}x" if speed != 1.0 else "Normal (1.0x)"
    bass_label  = f"{bass} dB boost" if bass > 0 else "Off"
    pos_label   = f"{pos // 60}:{pos % 60:02d}"

    await pm.edit_text(
        f"<b> Effects Applied </b>\n\n"
        f"<b> Song     :</b> {short(song['title'])}\n"
        f"<b> Position :</b> <code>{pos_label}</code>\n"
        f"<b> Speed    :</b> <code>{speed_label}</code>\n"
        f"<b> Bass     :</b> <code>{bass_label}</code>",
        parse_mode=ParseMode.HTML,
    )


# ── Auto-apply effects (called from player.py) ────────────────────────────────

async def maybe_apply_effects(chat_id: int, file_path: str) -> str:
    state = _get(chat_id)
    if not state.get("enabled", False):
        return file_path
    speed = state["speed"]
    bass  = state["bass"]
    if speed == 1.0 and bass == 0:
        return file_path
    try:
        return await _process_file(file_path, speed, bass)
    except Exception as e:
        LOGGER.warning(f"[Effects] Auto-apply failed for {chat_id}: {e}")
        return file_path


# ══════════════════════════════════════════════════════════════════════════════
# COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@bot.on_message(
    filters.group
    & filters.regex(r"^/speed(?:@\w+)?\s+(?P<val>[\d.]+)$")
    & group_allowed & user_allowed
)
async def speed_cmd(_, message: Message) -> None:
    chat_id = message.chat.id
    try:
        val = round(float(message.matches[0].group("val")), 2)
    except ValueError:
        await message.reply(
            "<b> Invalid value.</b>\n<b> Usage :</b> <code>/speed 1.5</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    if not (0.25 <= val <= 4.0):
        await message.reply(
            "<b> Speed must be between</b> <code>0.25</code> <b>and</b> <code>4.0</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    set_speed(chat_id, val)
    try:
        await message.delete()
    except Exception:
        pass
    await apply_effects_now(chat_id, message)


@bot.on_message(
    filters.group
    & filters.regex(r"^/speedreset(?:@\w+)?$")
    & group_allowed & user_allowed
)
async def speedreset_cmd(_, message: Message) -> None:
    chat_id = message.chat.id
    set_speed(chat_id, SPEED_DEFAULT)
    try:
        await message.delete()
    except Exception:
        pass
    await apply_effects_now(chat_id, message)


@bot.on_message(
    filters.group
    & filters.regex(r"^/bass(?:@\w+)?\s+(?P<val>\d+)$")
    & group_allowed & user_allowed
)
async def bass_cmd(_, message: Message) -> None:
    chat_id = message.chat.id
    try:
        val = int(message.matches[0].group("val"))
    except ValueError:
        await message.reply(
            "<b> Invalid value.</b>\n<b> Usage :</b> <code>/bass 10</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    if not (1 <= val <= 20):
        await message.reply(
            "<b> Bass must be between</b> <code>1</code> <b>and</b> <code>20</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    set_bass(chat_id, val)
    try:
        await message.delete()
    except Exception:
        pass
    await apply_effects_now(chat_id, message)


@bot.on_message(
    filters.group
    & filters.regex(r"^/bassoff(?:@\w+)?$")
    & group_allowed & user_allowed
)
async def bassoff_cmd(_, message: Message) -> None:
    chat_id = message.chat.id
    set_bass(chat_id, BASS_DEFAULT)
    try:
        await message.delete()
    except Exception:
        pass
    await apply_effects_now(chat_id, message)


@bot.on_message(
    filters.group
    & filters.regex(r"^/effecton(?:@\w+)?$")
    & group_allowed & user_allowed
)
async def effecton_cmd(_, message: Message) -> None:
    chat_id = message.chat.id
    set_enabled(chat_id, True)
    state       = _get(chat_id)
    speed_label = f"{state['speed']}x" if state['speed'] != 1.0 else "Normal (1.0x)"
    bass_label  = f"{state['bass']} dB" if state['bass'] > 0 else "Off"
    await message.reply(
        "<b> Effects Enabled </b>\n\n"
        "<b> All songs in this group will now play with effects.</b>\n\n"
        f"<b> Speed  :</b> <code>{speed_label}</code>\n"
        f"<b> Bass   :</b> <code>{bass_label}</code>\n\n"
        "<i>Use /effectoff to disable. Settings are saved across restarts.</i>",
        parse_mode=ParseMode.HTML,
    )


@bot.on_message(
    filters.group
    & filters.regex(r"^/effectoff(?:@\w+)?$")
    & group_allowed & user_allowed
)
async def effectoff_cmd(_, message: Message) -> None:
    set_enabled(message.chat.id, False)
    await message.reply(
        "<b> Effects Disabled </b>\n\n"
        "<b> Songs will now play normally in this group.</b>\n\n"
        "<i>Speed + bass settings are kept — use /effecton to re-enable.</i>",
        parse_mode=ParseMode.HTML,
    )


@bot.on_message(
    filters.group
    & filters.regex(r"^/effects(?:@\w+)?$")
    & group_allowed & user_allowed
)
async def effects_status_cmd(_, message: Message) -> None:
    chat_id     = message.chat.id
    state       = _get(chat_id)
    speed       = state["speed"]
    bass        = state["bass"]
    enabled     = state["enabled"]

    speed_label = f"{speed}x" if speed != 1.0 else "Normal (1.0x)"
    bass_label  = f"{bass} dB boost" if bass > 0 else "Off"
    mode_label  = "ON — All songs affected " if enabled else "OFF — Manual per song "

    song        = peek_current(chat_id)
    song_label  = short(song["title"]) if song else "Nothing playing"

    await message.reply(
        f"<b> Effects Status — {message.chat.title}</b>\n\n"
        f"<b> Now Playing  :</b> {song_label}\n"
        f"<b> Mode         :</b> <code>{mode_label}</code>\n"
        f"<b> Speed        :</b> <code>{speed_label}</code>\n"
        f"<b> Bass Boost   :</b> <code>{bass_label}</code>\n\n"
        "<b> Commands :</b>\n"
        "<code>/speed 1.5</code>    → set speed (0.25–4.0)\n"
        "<code>/speedreset</code>   → back to normal speed\n"
        "<code>/bass 10</code>      → bass boost (1–20 dB)\n"
        "<code>/bassoff</code>      → remove bass boost\n"
        "<code>/effecton</code>     → all songs get effects\n"
        "<code>/effectoff</code>    → manual mode only",
        parse_mode=ParseMode.HTML,
    )
