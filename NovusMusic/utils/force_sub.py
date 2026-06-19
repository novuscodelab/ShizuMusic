# --------------------------------------------------------------------------------
#  NovusMusic © 2026
#  Developed by Bad Munda
# --------------------------------------------------------------------------------

from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config

_JOIN_STATUSES = {
    ChatMemberStatus.OWNER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.MEMBER,
}


async def is_joined(client, user_id: int) -> bool:
    """Return True when a user has joined the required update channel."""
    if user_id in config.SUDO_USERS:
        return True
    try:
        member = await client.get_chat_member(config.FORCE_SUB_CHANNEL, user_id)
        return member.status in _JOIN_STATUSES
    except Exception:
        return False


async def require_force_sub(client, message: Message) -> bool:
    """Send the join prompt and return False if user has not joined yet."""
    if not message.from_user:
        return True
    if await is_joined(client, message.from_user.id):
        return True

    caption = (
        "<b>╭────────────────────▣</b>\n"
        "<b>│ Kamu belum bergabung ke channel</b>\n"
        "<b>│ Novus Society.</b>\n"
        "<b>├────────────────────▣</b>\n"
        "<b>│ Silakan join terlebih dahulu</b>\n"
        "<b>│ agar bisa memulai dan memakai bot.</b>\n"
        "<b>╰────────────────────▣</b>"
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("Join", url=config.FORCE_SUB_URL),
    ]])
    await message.reply_photo(
        config.FORCE_SUB_IMAGE,
        caption=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )
    return False
