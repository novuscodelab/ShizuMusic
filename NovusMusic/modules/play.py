# --------------------------------------------------------------------------------
#  NovusMusic © 2026
#  Developed by Bad Munda 
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio
import re
import time

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import config
from NovusMusic import bot
from NovusMusic.core.player import play_song
from NovusMusic.core.queue import add_to_queue, peek_current, queue_size
from NovusMusic.modules.block import group_allowed, user_allowed
from NovusMusic.utils.assistant import is_assistant_in, try_join_assistant
from NovusMusic.utils.db import add_served_chat, add_served_user
from NovusMusic.utils.force_sub import require_force_sub
from NovusMusic.utils.formatters import fmt_time, iso_to_human, iso_to_sec, short
from NovusMusic.utils.permissions import is_music_command_authorized
from NovusMusic.utils.youtube import search_yt

# ── Blocked words ──────────────────────────────────────────────────────────────
BLOCKED_WORDS = [
    "porn", "xxx", "xnxx", "xvideos",
    "sex", "fuck", "lund",
    "drug", "cocaine", "weed", "charas",
]

# ── Per-chat state ─────────────────────────────────────────────────────────────
_last_cmd: dict[int, float] = {}
_pending:  dict[int, tuple] = {}


def _max_duration_text() -> str:
    return fmt_time(config.MAX_DURATION_SECONDS)


# ── DB helper ──────────────────────────────────────────────────────────────────

def _db_track(chat_id: int, user_id: int) -> None:
    try:
        add_served_chat(chat_id)
        if user_id:
            add_served_user(user_id)
    except Exception:
        pass


# ── Cooldown handler ───────────────────────────────────────────────────────────

async def _run_pending(chat_id: int, delay: int) -> None:
    await asyncio.sleep(delay)
    if chat_id in _pending:
        msg, reply = _pending.pop(chat_id)
        try:
            await reply.delete()
        except Exception:
            pass
        await play_handler(bot, msg)


# ── /play & /vplay command ─────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.regex(r"^/(?P<cmd>v?play)(?:@\w+)?(?:\s+(?P<q>.+))?$")
    & group_allowed
    & user_allowed
)
async def play_handler(_, message: Message) -> None:

    if not await require_force_sub(bot, message):
        return

    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0
    match = message.matches[0]
    cmd = (match.group("cmd") or "play").strip().lower()

    if not await is_music_command_authorized(message, cmd):
        await message.reply(f"<b> Kamu tidak punya izin untuk memakai /{cmd} di grup ini.</b>", parse_mode=ParseMode.HTML)
        return

    _db_track(chat_id, user_id)

    # ── Replied audio / video ──────────────────────────────────────────────────
    if message.reply_to_message and (
        message.reply_to_message.audio or message.reply_to_message.video
    ):
        pm = await message.reply(
            "<b> ᴘʀᴏᴄᴇssɪɴɢ ᴍᴇᴅɪᴀ...</b>",
            parse_mode=ParseMode.HTML,
        )

        orig  = message.reply_to_message
        fresh = await bot.get_messages(orig.chat.id, orig.id)
        media = fresh.video or fresh.audio

        if fresh.audio and getattr(fresh.audio, "file_size", 0) > 100 * 1024 * 1024:
            await pm.edit_text(
                "<b> ғɪʟᴇ ᴛᴏᴏ ʟᴀʀɢᴇ</b>\n"
                "<b> ᴍᴀx :</b> <code>100 MB</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        await pm.edit_text(
            "<b> ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴍᴇᴅɪᴀ...</b>",
            parse_mode=ParseMode.HTML,
        )

        try:
            fp = await bot.download_media(media)
        except Exception as e:
            await pm.edit_text(
                f"<b> ᴅᴏᴡɴʟᴏᴀᴅ ғᴀɪʟᴇᴅ</b>\n<code>{e}</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        thumb = None
        try:
            thumbs = (fresh.video or fresh.audio).thumbs
            if thumbs:
                thumb = await bot.download_media(thumbs[0])
        except Exception:
            pass

        duration_seconds = media.duration or 0
        if duration_seconds > config.MAX_DURATION_SECONDS:
            await pm.edit_text(
                f"<b> ᴍᴇᴅɪᴀ ᴛᴏᴏ ʟᴏɴɢ</b>\n"
                f"<b> ᴅᴜʀ :</b> <code>{fmt_time(duration_seconds)}</code>\n"
                f"<b> ᴍᴀx :</b> <code>{_max_duration_text()}</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        song = {
            "url":              fp,
            "title":            getattr(media, "file_name", "Video" if cmd == "vplay" else "Audio"),
            "duration":         fmt_time(duration_seconds),
            "duration_seconds": duration_seconds,
            "requester":        message.from_user.first_name if message.from_user else "Unknown",
            "requester_id":     user_id,
            "thumbnail":        thumb,
            "video":            cmd == "vplay" and bool(fresh.video),
        }

        add_to_queue(chat_id, song)
        await play_song(chat_id, pm, song)
        return

    # ── Text query ─────────────────────────────────────────────────────────────
    query = (match.group("q") or "").strip()

    try:
        await message.delete()
    except Exception:
        pass

    # Blocked words check
    if any(x in query.lower() for x in BLOCKED_WORDS):
        await bot.send_message(
            chat_id,
            "<b> ᴛʜɪs sᴏɴɢ ɪs ʙʟᴏᴄᴋᴇᴅ</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    # Cooldown check
    now = time.time()
    if chat_id in _last_cmd and (now - _last_cmd[chat_id]) < config.COOLDOWN:
        rem = int(config.COOLDOWN - (now - _last_cmd[chat_id]))
        if chat_id not in _pending:
            rep = await bot.send_message(
                chat_id,
                f"<b> ᴄᴏᴏʟᴅᴏᴡɴ ᴀᴄᴛɪᴠᴇ</b>\n"
                f"<b> ᴘʀᴏᴄᴇssɪɴɢ ɪɴ :</b> <code>{rem}s</code>",
                parse_mode=ParseMode.HTML,
            )
            _pending[chat_id] = (message, rep)
            asyncio.create_task(_run_pending(chat_id, rem))
        return

    _last_cmd[chat_id] = now

    if not query:
        await bot.send_message(
            chat_id,
            "<b> ᴜsᴀɢᴇ :</b> <code>/play song name</code>\n"
            "<b> ᴏʀ :</b> <code>/play youtube url</code>\n"
            f"<b> ᴠɪᴅᴇᴏ :</b> <code>/vplay song name</code>\n"
            f"<b> ᴍᴀx ᴅᴜʀᴀsɪ :</b> <code>{_max_duration_text()}</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    await _process_play(message, query, video=(cmd == "vplay"))


# ── Process play ───────────────────────────────────────────────────────────────

async def _process_play(message: Message, query: str, video: bool = False) -> None:
    chat_id = message.chat.id

    pm = await message.reply(
        "<b> ᴘʀᴏᴄᴇssɪɴɢ...</b>",
        parse_mode=ParseMode.HTML,
    )

    # Assistant check — uses utils/assistant.py
    status = await is_assistant_in(chat_id)

    if status == "banned":
        await pm.edit_text(
            "<b> ᴀssɪsᴛᴀɴᴛ ʙᴀɴɴᴇᴅ</b>\n"
            "<b> ᴘʟᴇᴀsᴇ ᴜɴʙᴀɴ ᴀssɪsᴛᴀɴᴛ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    if not status:
        await pm.edit_text(
            "<b> ᴀssɪsᴛᴀɴᴛ ɪs ᴊᴏɪɴɪɴɢ ᴛʜᴇ ɢʀᴏᴜᴘ...</b>",
            parse_mode=ParseMode.HTML,
        )
        ok = await try_join_assistant(chat_id, pm)
        if not ok:
            return
        await pm.edit_text(
            "<b> ᴀssɪsᴛᴀɴᴛ ʜᴀs ᴊᴏɪɴᴇᴅ </b>\n"
            "<b> ᴘʀᴏᴄᴇssɪɴɢ...</b>",
            parse_mode=ParseMode.HTML,
        )

    # Normalise short YouTube URL
    if "youtu.be" in query:
        m = re.search(r"youtu\.be/([^?&]+)", query)
        if m:
            query = f"https://www.youtube.com/watch?v={m.group(1)}"

    # Search YouTube
    try:
        result = await search_yt(query)
    except Exception as e:
        await pm.edit_text(
            f"<b> sᴇᴀʀᴄʜ ғᴀɪʟᴇᴅ</b>\n<code>{e}</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    # Playlist
    if isinstance(result, dict) and "playlist" in result:
        items = result["playlist"]
        if not items:
            await pm.edit_text("<b> ᴘʟᴀʏʟɪsᴛ ᴇᴍᴩᴛʏ</b>", parse_mode=ParseMode.HTML)
            return

        req    = message.from_user.first_name if message.from_user else "Unknown"
        req_id = message.from_user.id         if message.from_user else 0

        first_was_empty = queue_size(chat_id) == 0

        added_count = 0
        skipped_count = 0
        added_titles = []

        for item in items:
            duration_seconds = iso_to_sec(item["duration"])
            if duration_seconds > config.MAX_DURATION_SECONDS:
                skipped_count += 1
                continue

            add_to_queue(chat_id, {
                "url":              item["link"],
                "title":            item["title"],
                "duration":         iso_to_human(item["duration"]),
                "duration_seconds": duration_seconds,
                "requester":        req,
                "requester_id":     req_id,
                "thumbnail":        item["thumbnail"],
                "video":            video,
            })
            added_titles.append(item["title"])
            added_count += 1

        if added_count == 0:
            await pm.edit_text(
                f"<b> ɴᴏ ᴘʟᴀʏʟɪsᴛ sᴏɴɢs ᴜɴᴅᴇʀ ᴍᴀx ᴅᴜʀᴀsɪ</b>\n"
                f"<b> ᴍᴀx :</b> <code>{_max_duration_text()}</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        text = (
            f"<b> ᴘʟᴀʏʟɪsᴛ ᴀᴅᴅᴇᴅ</b>\n"
            f"<b> sᴏɴɢs :</b> <code>{added_count}</code>\n"
            f"<b> ғɪʀsᴛ :</b> <code>{short(added_titles[0])}</code>"
        )
        if skipped_count:
            text += f"\n<b> sᴋɪᴘᴘᴇᴅ :</b> <code>{skipped_count}</code> (> {_max_duration_text()})"

        await message.reply(text, parse_mode=ParseMode.HTML)

        if first_was_empty:
            first_song = peek_current(chat_id)
            if first_song:
                await play_song(chat_id, pm, first_song)
        else:
            await pm.delete()
        return

    # Single track
    url, title, dur_iso, thumb = result

    if not url:
        await pm.edit_text("<b> sᴏɴɢ ɴᴏᴛ ғᴏᴜɴᴅ</b>", parse_mode=ParseMode.HTML)
        return

    secs = iso_to_sec(dur_iso)

    if secs > config.MAX_DURATION_SECONDS:
        await pm.edit_text(
            f"<b> sᴏɴɢ ᴛᴏᴏ ʟᴏɴɢ</b>\n"
            f"<b> ᴅᴜʀ :</b> <code>{iso_to_human(dur_iso)}</code>\n"
            f"<b> ᴍᴀx :</b> <code>{_max_duration_text()}</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    req    = message.from_user.first_name if message.from_user else "Unknown"
    req_id = message.from_user.id         if message.from_user else 0

    song = {
        "url":              url,
        "title":            title,
        "duration":         iso_to_human(dur_iso),
        "duration_seconds": secs,
        "requester":        req,
        "requester_id":     req_id,
        "thumbnail":        thumb,
        "video":            video,
    }

    pos = add_to_queue(chat_id, song)

    if pos == 1:
        await play_song(chat_id, pm, song)
    else:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("⌯ sᴋɪᴩ ⌯",  callback_data="skip"),
            InlineKeyboardButton("⌯ ᴄʟᴇᴀʀ ⌯", callback_data="clear"),
        ]])
        await message.reply(
            f"<b> ᴀᴅᴅᴇᴅ ᴛᴏ ǫᴜᴇᴜᴇ</b>\n"
            f"<b> ᴛɪᴛʟᴇ :</b> <code>{short(title)}</code>\n"
            f"<b> ᴅᴜʀ :</b> <code>{iso_to_human(dur_iso)}</code>\n"
            f"<b> ʙʏ :</b> <code>{req}</code>\n"
            f"<b> ᴩᴏs :</b> <code>#{pos - 1}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        await pm.delete()
