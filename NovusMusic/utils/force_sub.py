# --------------------------------------------------------------------------------
#  NovusMusic © 2026
#  Developed by Bad Munda
# --------------------------------------------------------------------------------

from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config

_FORCE_SUB_PROMPTS: dict[int, tuple[int, int]] = {}

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


async def _delete_join_prompt(client, user_id: int) -> None:
    """Delete the stored force-sub prompt for a user when it is no longer needed."""
    prompt = _FORCE_SUB_PROMPTS.pop(user_id, None)
    if not prompt:
        return

    chat_id, message_id = prompt
    try:
        await client.delete_messages(chat_id, message_id)
    except Exception:
        pass


async def require_force_sub(client, message: Message) -> bool:
    """Send the join prompt and return False if user has not joined yet."""
    if not message.from_user:
        return True

    user_id = message.from_user.id
    if await is_joined(client, user_id):
        await _delete_join_prompt(client, user_id)
        return True

    await _delete_join_prompt(client, user_id)

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
    prompt = await message.reply_photo(
        config.FORCE_SUB_IMAGE,
        caption=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )
    _FORCE_SUB_PROMPTS[user_id] = (prompt.chat.id, prompt.id)
    return False
