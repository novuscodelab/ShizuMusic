# --------------------------------------------------------------------------------
#  NovusMusic © 2026
#  Developed by Bad Munda 
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from NovusMusic import bot, call_py
from NovusMusic.core.player import play_song
from NovusMusic.core.queue import peek_current, pop_current, queue_size
from NovusMusic.modules.block import group_allowed, user_allowed
from NovusMusic.utils.formatters import short
from NovusMusic.utils.helpers import delete_file
from NovusMusic.utils.permissions import is_music_command_authorized


@bot.on_message(
    filters.group
    & filters.command("skip")
    & group_allowed
    & user_allowed
)
async def skip_cmd(_, message: Message) -> None:

    chat_id = message.chat.id

    if not await is_music_command_authorized(message, "skip"):
        await message.reply(
            "<b> Kamu tidak punya izin untuk memakai /skip di grup ini.</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    if not queue_size(chat_id):
        await message.reply(
            "<b> ǫᴜᴇᴜᴇ ɪs ᴇᴍᴘᴛʏ</b>\n"
            "<b> ɴᴏ sᴏɴɢs ᴛᴏ sᴋɪᴘ.</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    sm = await message.reply(
        "<b> sᴋɪᴘᴘɪɴɢ ᴄᴜʀʀᴇɴᴛ ᴛʀᴀᴄᴋ...</b>",
        parse_mode=ParseMode.HTML,
    )

    skipped = pop_current(chat_id)

    try:
        await call_py.leave_call(chat_id)
    except Exception:
        pass

    await asyncio.sleep(2)

    try:
        delete_file(skipped.get("file_path", ""))
    except Exception:
        pass

    nxt = peek_current(chat_id)

    if nxt:
        await sm.edit_text(
            f"<b> sᴋɪᴘᴘᴇᴅ ᴛʀᴀᴄᴋ :</b> <code>{short(skipped['title'])}</code>\n"
            f"<b> ɴᴏᴡ ᴘʟᴀʏɪɴɢ :</b>\n<code>{nxt['title']}</code>",
            parse_mode=ParseMode.HTML,
        )
        dm = await bot.send_message(
            chat_id,
            f"<b> ɴᴇxᴛ ᴛʀᴀᴄᴋ :</b> <code>{nxt['title']}</code>",
            parse_mode=ParseMode.HTML,
        )
        await play_song(chat_id, dm, nxt)
    else:
        await sm.edit_text(
            f"<b> sᴋɪᴘᴘᴇᴅ ᴛʀᴀᴄᴋ :</b> <code>{short(skipped['title'])}</code>\n"
            "<b> ǫᴜᴇᴜᴇ ɪs ɴᴏᴡ ᴇᴍᴘᴛʏ</b>",
            parse_mode=ParseMode.HTML,
        )
