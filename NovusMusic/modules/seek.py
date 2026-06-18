# --------------------------------------------------------------------------------
#  NovusMusic © 2026
#  Developed by Bad Munda 
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import time

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from NovusMusic import bot, call_py, LOGGER
from NovusMusic.core.queue import peek_current
from NovusMusic.modules.block import group_allowed, user_allowed
from NovusMusic.utils.formatters import fmt_time, parse_dur, progress_bar, short
from NovusMusic.utils.youtube import resolve_stream

# ── Seek state tracker ─────────────────────────────────────────────────────────
_seek_state: dict[int, dict] = {}


def set_seek_state(chat_id: int, offset: int) -> None:
    _seek_state[chat_id] = {"start_ts": time.time(), "offset": offset}


def get_current_position(chat_id: int) -> int:
    state = _seek_state.get(chat_id)
    if not state:
        return 0
    return state["offset"] + int(time.time() - state["start_ts"])


def clear_seek_state(chat_id: int) -> None:
    _seek_state.pop(chat_id, None)


# ── Internal seek ──────────────────────────────────────────────────────────────

async def _seek_to(chat_id: int, target_sec: int, message: Message) -> None:
    from pytgcalls.types import AudioQuality, MediaStream

    song = peek_current(chat_id)
    if not song:
        await message.reply("<b> Nothing is playing right now.</b>", parse_mode=ParseMode.HTML)
        return

    total_sec  = parse_dur(song.get("duration", "0:00"))
    target_sec = max(0, min(target_sec, total_sec - 1))

    pm = await message.reply(
        f"<b> Seeking to</b> <code>{fmt_time(target_sec)}</code><b>...</b>",
        parse_mode=ParseMode.HTML,
    )

    try:
        media_path = await resolve_stream(song["url"])
    except Exception as e:
        await pm.edit_text(
            f"<b> Seek failed — could not resolve stream.</b>\n<code>{e}</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        await call_py.change_stream(
            chat_id,
            MediaStream(
                media_path,
                audio_parameters=AudioQuality.HIGH,
                video_flags=MediaStream.Flags.IGNORE,
                ffmpeg_parameters=f"-ss {target_sec}",
            ),
        )
    except Exception as e:
        try:
            await call_py.play(
                chat_id,
                MediaStream(
                    media_path,
                    audio_parameters=AudioQuality.HIGH,
                    video_flags=MediaStream.Flags.IGNORE,
                    ffmpeg_parameters=f"-ss {target_sec}",
                ),
            )
        except Exception as e2:
            await pm.edit_text(
                f"<b> Seek failed.</b>\n<code>{e2}</code>",
                parse_mode=ParseMode.HTML,
            )
            return

    set_seek_state(chat_id, target_sec)

    caption = (
        "<blockquote>"
        "<b> Novus Music</b>\n\n"
        f"<b> Title :</b> {short(song['title'])}\n"
        f"<b> Duration :</b> {song.get('duration', '?')}\n"
        f"<b> By :</b> {song['requester']}\n"
        f"<b> Seeked to :</b> <code>{fmt_time(target_sec)}</code>"
        "</blockquote>"
    )
    btns = [
        InlineKeyboardButton("▷",   callback_data="resume"),
        InlineKeyboardButton("II",  callback_data="pause"),
        InlineKeyboardButton("‣‣I", callback_data="skip"),
        InlineKeyboardButton("▢",   callback_data="stop"),
    ]
    bar = progress_bar(target_sec, total_sec)
    kb  = InlineKeyboardMarkup([
        [InlineKeyboardButton(bar, callback_data="noop")],
        btns,
    ])
    await pm.edit_text(caption, reply_markup=kb, parse_mode=ParseMode.HTML)


# ── /seek ──────────────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.regex(r"^/seek(?:@\w+)?\s+(?P<sec>\d+)$")
    & group_allowed
    & user_allowed
)
async def seek_cmd(_, message: Message) -> None:
    chat_id = message.chat.id
    song    = peek_current(chat_id)

    if not song:
        await message.reply("<b> No song is currently playing.</b>", parse_mode=ParseMode.HTML)
        return

    sec = int(message.matches[0].group("sec"))
    if sec < 1:
        await message.reply(
            "<b> Please provide a number of seconds greater than 0.</b>\n"
            "<b> Usage :</b> <code>/seek 30</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    current_pos = get_current_position(chat_id)
    target      = current_pos + sec
    total_sec   = parse_dur(song.get("duration", "0:00"))

    if current_pos >= total_sec - 1:
        await message.reply("<b> Song is almost finished. Cannot seek forward.</b>", parse_mode=ParseMode.HTML)
        return

    if target >= total_sec:
        await message.reply(
            f"<b> Cannot seek that far forward.</b>\n"
            f"<b> Current position :</b> <code>{fmt_time(current_pos)}</code>\n"
            f"<b> Song duration :</b> <code>{fmt_time(total_sec)}</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        await message.delete()
    except Exception:
        pass

    await _seek_to(chat_id, target, message)


# ── /seekback ──────────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.regex(r"^/seekback(?:@\w+)?\s+(?P<sec>\d+)$")
    & group_allowed
    & user_allowed
)
async def seekback_cmd(_, message: Message) -> None:
    chat_id = message.chat.id
    song    = peek_current(chat_id)

    if not song:
        await message.reply("<b> No song is currently playing.</b>", parse_mode=ParseMode.HTML)
        return

    sec = int(message.matches[0].group("sec"))
    if sec < 1:
        await message.reply(
            "<b> Please provide a number of seconds greater than 0.</b>\n"
            "<b> Usage :</b> <code>/seekback 30</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    target = max(0, get_current_position(chat_id) - sec)

    try:
        await message.delete()
    except Exception:
        pass

    await _seek_to(chat_id, target, message)


# ── /seek (no args) ────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.regex(r"^/seek(?:@\w+)?$")
    & group_allowed
    & user_allowed
)
async def seek_usage(_, message: Message) -> None:
    chat_id = message.chat.id
    song    = peek_current(chat_id)

    if song:
        pos       = get_current_position(chat_id)
        total_sec = parse_dur(song.get("duration", "0:00"))
        await message.reply(
            f"<b> Current position :</b> <code>{fmt_time(pos)}</code> / <code>{fmt_time(total_sec)}</code>\n\n"
            f"<b> Usage :</b>\n"
            f"<code>/seek 30</code>     → forward 30 seconds\n"
            f"<code>/seekback 30</code> → backward 30 seconds",
            parse_mode=ParseMode.HTML,
        )
    else:
        await message.reply(
            "<b> Usage :</b>\n"
            "<code>/seek 30</code>     → forward 30 seconds\n"
            "<code>/seekback 30</code> → backward 30 seconds",
            parse_mode=ParseMode.HTML,
        )
