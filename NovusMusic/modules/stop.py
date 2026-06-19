# --------------------------------------------------------------------------------
#  NovusMusic © 2026
#  Developed by Bad Munda 
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from NovusMusic import bot
from NovusMusic.core.call import leave_vc
from NovusMusic.core.queue import clear_queue, queue_size
from NovusMusic.modules.block import group_allowed, user_allowed
from NovusMusic.utils.permissions import is_music_command_authorized


# ── /stop & /end ──────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.command(["stop", "end"])
    & group_allowed
    & user_allowed
)
async def stop_cmd(_, message: Message) -> None:

    if not await is_music_command_authorized(message, "stop"):
        await message.reply(
            "<b> ᴀᴅᴍɪɴ ᴏɴʟʏ</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    await leave_vc(message.chat.id)

    await message.reply(
        "<b> ᴘʟᴀʏʙᴀᴄᴋ ꜱᴛᴏᴘᴘᴇᴅ</b>\n"
        "<b> Qᴜᴇᴜᴇ ᴄʟᴇᴀʀᴇᴅ</b>\n"
        "<b> ʟᴇꜰᴛ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ</b>",
        parse_mode=ParseMode.HTML,
    )


# ── /clear ─────────────────────────────────────────────────────────────────────

@bot.on_message(
    filters.group
    & filters.command("clear")
    & group_allowed
    & user_allowed
)
async def clear_cmd(_, message: Message) -> None:

    if not await is_music_command_authorized(message, "stop"):
        await message.reply(
            "<b> ᴀᴅᴍɪɴ ᴏɴʟʏ</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    chat_id = message.chat.id

    try:
        from NovusMusic.core.autoplay import stop_autoplay
        stop_autoplay(chat_id)
    except Exception:
        pass

    if not queue_size(chat_id):
        await message.reply(
            "<b> Qᴜᴇᴜᴇ ɪꜱ ᴇᴍᴘᴛʏ</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    clear_queue(chat_id)
    await message.reply(
        "<b> Qᴜᴇᴜᴇ ᴄʟᴇᴀʀᴇᴅ</b>\n"
        "<b> ᴀʟʟ ꜱᴏɴɢꜱ ʀᴇᴍᴏᴠᴇᴅ</b>",
        parse_mode=ParseMode.HTML,
    )


# ── /reboot ────────────────────────────────────────────────────────────────────

@bot.on_message(
    filters.command("reboot")
    & group_allowed
    & user_allowed
)
async def reboot_cmd(_, message: Message) -> None:
    await leave_vc(message.chat.id)
    await message.reply(
        "<b> ᴄʜᴀᴛ ʀᴇʙᴏᴏᴛᴇᴅ</b>\n"
        "<b> ᴀʟʟ ꜱᴛᴀᴛᴇꜱ ʀᴇꜱᴇᴛ</b>",
        parse_mode=ParseMode.HTML,
    )
