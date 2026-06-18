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
from NovusMusic.utils.permissions import is_user_authorized


@bot.on_message(
    filters.group
    & filters.command("resume")
    & group_allowed
    & user_allowed
)
async def resume_cmd(_, message: Message) -> None:

    if not await is_user_authorized(message):
        await message.reply(
            "<b> ᴀᴅᴍɪɴ ᴏɴʟʏ</b>\n"
            "<b> ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪs ғᴏʀ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴs.</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        await call_py.resume(message.chat.id)
        await message.reply(
            "<b> sᴛʀᴇᴀᴍ ʀᴇsᴜᴍᴇᴅ</b>\n"
            "<b> ᴍᴜsɪᴄ ᴘʟᴀʏʙᴀᴄᴋ ᴄᴏɴᴛɪɴᴜᴇᴅ.</b>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await message.reply(
            f"<b> ʀᴇsᴜᴍᴇ ғᴀɪʟᴇᴅ</b>\n<code>{e}</code>",
            parse_mode=ParseMode.HTML,
        )
