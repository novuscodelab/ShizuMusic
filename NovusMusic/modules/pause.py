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

from NovusMusic import bot, call_py
from NovusMusic.modules.block import group_allowed, user_allowed
from NovusMusic.utils.permissions import is_music_command_authorized


@bot.on_message(
    filters.group
    & filters.command("pause")
    & group_allowed
    & user_allowed
)
async def pause_cmd(_, message: Message) -> None:

    if not await is_music_command_authorized(message, "pause"):
        await message.reply(
            "<b> ᴀᴅᴍɪɴ ᴏɴʟʏ</b>\n"
            "<b> ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪs ғᴏʀ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴs.</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        await call_py.pause(message.chat.id)
        await message.reply(
            "<b> sᴛʀᴇᴀᴍ ᴘᴀᴜsᴇᴅ</b>\n"
            "<b> ᴍᴜsɪᴄ ᴘʟᴀʏʙᴀᴄᴋ ᴛᴇᴍᴘᴏʀᴀʀɪʟʏ sᴛᴏᴘᴘᴇᴅ.</b>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await message.reply(
            f"<b> ᴘᴀᴜsᴇ ғᴀɪʟᴇᴅ</b>\n<code>{e}</code>",
            parse_mode=ParseMode.HTML,
        )
