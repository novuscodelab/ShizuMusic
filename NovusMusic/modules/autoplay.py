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

from NovusMusic import bot
from NovusMusic.core.autoplay import (
    get_autoplay_query,
    is_autoplay,
    start_autoplay,
    stop_autoplay,
)
from NovusMusic.core.call import leave_vc
from NovusMusic.core.player import play_song
from NovusMusic.core.queue import peek_current, queue_size
from NovusMusic.modules.block import group_allowed, user_allowed
from NovusMusic.utils.formatters import short
from NovusMusic.utils.permissions import is_user_authorized


@bot.on_message(
    filters.group
    & filters.regex(r"^/autoplay(?:@\w+)?(?:\s+(?P<q>.+))?$")
    & group_allowed
    & user_allowed
)
async def autoplay_cmd(_, message: Message) -> None:

    chat_id = message.chat.id
    user    = message.from_user

    if not await is_user_authorized(message):
        await message.reply(
            "<b> ᴀᴅᴍɪɴ ᴏɴʟʏ</b>\n"
            "<b> ᴏɴʟʏ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ /autoplay</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    match = message.matches[0]
    query = (match.group("q") or "").strip()

    if not query:
        current_q = get_autoplay_query(chat_id)
        if is_autoplay(chat_id) and current_q:
            await message.reply(
                f"<b> ᴀᴜᴛᴏᴘʟᴀʏ ɪꜱ ᴀʟʀᴇᴀᴅʏ ʀᴜɴɴɪɴɢ</b>\n"
                f"<b> Qᴜᴇʀʏ :</b> <code>{current_q}</code>\n"
                f"<b> ᴜꜱᴇ /end ᴛᴏ ꜱᴛᴏᴘ ᴀᴜᴛᴏᴘʟᴀʏ ꜰɪʀꜱᴛ</b>",
                parse_mode=ParseMode.HTML,
            )
        else:
            await message.reply(
                "<b> ᴜꜱᴀɢᴇ :</b> <code>/autoplay sidhu moose wala</code>\n"
                "<b> ᴛʜɪꜱ ᴡɪʟʟ ᴄᴏɴᴛɪɴᴜᴏᴜꜱʟʏ ᴘʟᴀʏ ꜱᴏɴɢꜱ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ</b>",
                parse_mode=ParseMode.HTML,
            )
        return

    pm = await message.reply(
        f"<b> ꜱᴇᴛᴛɪɴɢ ᴜᴘ ᴀᴜᴛᴏᴘʟᴀʏ...</b>\n"
        f"<b> Qᴜᴇʀʏ :</b> <code>{query}</code>",
        parse_mode=ParseMode.HTML,
    )

    req    = user.first_name if user else "AutoPlay"
    req_id = user.id         if user else 0

    was_playing = queue_size(chat_id) > 0
    count       = await start_autoplay(chat_id, query, req, req_id)

    if count == 0:
        stop_autoplay(chat_id)
        await pm.edit_text(
            "<b> ᴀᴜᴛᴏᴘʟᴀʏ ꜰᴀɪʟᴇᴅ</b>\n"
            "<b> ɴᴏ ꜱᴏɴɢꜱ ᴡᴇʀᴇ ꜰᴏᴜɴᴅ, ᴘʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    first = peek_current(chat_id)

    await pm.edit_text(
        f"<b> ᴀᴜᴛᴏᴘʟᴀʏ ꜱᴛᴀʀᴛᴇᴅ</b>\n"
        f"<b> Qᴜᴇʀʏ :</b> <code>{query}</code>\n"
        f"<b> {count} ꜱᴏɴɢꜱ ᴀᴅᴅᴇᴅ ᴛᴏ Qᴜᴇᴜᴇ</b>\n"
        f"<b> ᴜꜱᴇ /end ᴛᴏ ꜱᴛᴏᴘ ᴀᴜᴛᴏᴘʟᴀʏ</b>",
        parse_mode=ParseMode.HTML,
    )

    if not was_playing and first:
        dm = await bot.send_message(
            chat_id,
            f"<b> ɴᴏᴡ ᴘʟᴀʏɪɴɢ :</b> <code>{short(first['title'])}</code>",
            parse_mode=ParseMode.HTML,
        )
        await play_song(chat_id, dm, first)

    try:
        await message.delete()
    except Exception:
        pass
