# --------------------------------------------------------------------------------
#  NovusMusic © 2026
#  Developed by Bad Munda 
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

from typing import Union

from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.types import CallbackQuery, Message

from NovusMusic.utils.db import get_music_permissions, is_music_user_authed

import config

TRUSTED_IDS: set[int] = {777000, *config.SUDO_USERS}


async def is_user_authorized(obj: Union[Message, CallbackQuery]) -> bool:
    """
    Returns True if the user is:
    - Bot owner or Telegram system account (777000)
    - A group admin or owner
    """
    if isinstance(obj, CallbackQuery):
        message = obj.message
        user    = obj.from_user
    elif isinstance(obj, Message):
        message = obj
        user    = obj.from_user
    else:
        return False

    if not user:
        return False

    if user.id in TRUSTED_IDS:
        return True

    if message.chat.type not in (ChatType.SUPERGROUP, ChatType.GROUP, ChatType.CHANNEL):
        return False

    try:
        member = await message._client.get_chat_member(message.chat.id, user.id)
        return member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)
    except Exception:
        return False



async def is_music_command_authorized(obj: Union[Message, CallbackQuery], command: str) -> bool:
    """Permission gate for configurable playback commands."""
    if isinstance(obj, CallbackQuery):
        message = obj.message
        user = obj.from_user
    elif isinstance(obj, Message):
        message = obj
        user = obj.from_user
    else:
        return False

    if not user:
        return False
    if user.id in TRUSTED_IDS:
        return True
    if message.chat.type not in (ChatType.SUPERGROUP, ChatType.GROUP):
        return False

    settings = get_music_permissions(message.chat.id)
    mode = settings.get(command) or (settings.get("play") if command == "vplay" else "admin")
    if mode == "member":
        return True

    try:
        member = await message._client.get_chat_member(message.chat.id, user.id)
        is_admin = member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)
    except Exception:
        is_admin = False

    if is_admin:
        return True
    if mode == "auth":
        return is_music_user_authed(message.chat.id, user.id)
    return False
