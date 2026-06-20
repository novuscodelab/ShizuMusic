# --------------------------------------------------------------------------------
#  NovusMusic © 2026
#  Developed by Bad Munda
# --------------------------------------------------------------------------------

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from NovusMusic import bot
from NovusMusic.modules.block import group_allowed, user_allowed
from NovusMusic.utils.db import (
    auth_music_user,
    get_music_permissions,
    set_music_permission,
)

_COMMANDS = {"play", "vplay", "skip", "pause", "resume", "stop"}
_MODES = {"member", "admin", "auth"}


async def _is_admin_or_sudo(message: Message) -> bool:
    user = message.from_user
    if not user:
        return False
    if user.id in config.SUDO_USERS:
        return True
    try:
        member = await message._client.get_chat_member(message.chat.id, user.id)
        return member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)
    except Exception:
        return False


def _settings_text(chat_id: int) -> str:
    settings = get_music_permissions(chat_id)
    return (
        "<b>Pengaturan izin music command</b>\n\n"
        f"<b>/play:</b> <code>{settings['play']}</code>\n"
        f"<b>/vplay:</b> <code>{settings['vplay']}</code>\n"
        f"<b>/skip:</b> <code>{settings['skip']}</code>\n"
        f"<b>/pause:</b> <code>{settings['pause']}</code>\n"
        f"<b>/resume:</b> <code>{settings['resume']}</code>\n"
        f"<b>/stop:</b> <code>{settings['stop']}</code>\n\n"
        "<b>Pilih tombol di bawah untuk mengatur atau merubah izinnya.</b>\n"
        "<b>Mode:</b> member = semua member, admin = admin grup, auth = admin + user yang di-/auth"
    )


def _settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("/play", callback_data="settings_menu:play"),
            InlineKeyboardButton("/vplay", callback_data="settings_menu:vplay"),
        ],
        [
            InlineKeyboardButton("/skip", callback_data="settings_menu:skip"),
            InlineKeyboardButton("/pause", callback_data="settings_menu:pause"),
        ],
        [
            InlineKeyboardButton("/resume", callback_data="settings_menu:resume"),
            InlineKeyboardButton("/stop", callback_data="settings_menu:stop"),
        ],
    ])


@bot.on_message(filters.group & filters.command("settings") & group_allowed & user_allowed)
async def settings_cmd(_, message: Message) -> None:
    if not await _is_admin_or_sudo(message):
        await message.reply("<b> Hanya admin grup yang bisa mengubah settings.</b>", parse_mode=ParseMode.HTML)
        return

    args = message.command[1:]
    chat_id = message.chat.id

    if len(args) >= 2:
        command = args[0].lower().lstrip("/")
        mode = args[1].lower()
        if command not in _COMMANDS or mode not in _MODES:
            await message.reply(
                "<b>Format salah.</b>\n"
                "<code>/settings play member</code>\n"
                "<code>/settings vplay member</code>\n"
                "<code>/settings skip member</code>\n"
                "<code>/settings stop admin</code>\n"
                "<code>/settings pause auth</code>",
                parse_mode=ParseMode.HTML,
            )
            return
        set_music_permission(chat_id, command, mode)
        await message.reply(
            f"<b>Settings diperbarui.</b>\n<code>/{command}</code> sekarang: <code>{mode}</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    await message.reply(
        _settings_text(chat_id),
        parse_mode=ParseMode.HTML,
        reply_markup=_settings_keyboard(),
    )


@bot.on_message(filters.group & filters.command("auth") & group_allowed & user_allowed)
async def auth_cmd(_, message: Message) -> None:
    if not await _is_admin_or_sudo(message):
        await message.reply("<b> Hanya admin, owner, atau developer yang bisa menjalankan /auth.</b>", parse_mode=ParseMode.HTML)
        return

    user_id = None
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        try:
            user_id = int(message.command[1])
        except ValueError:
            user_id = None

    if not user_id:
        await message.reply("<b>Usage:</b> <code>/auth user_id</code> atau reply pesan user dengan <code>/auth</code>", parse_mode=ParseMode.HTML)
        return

    auth_music_user(message.chat.id, user_id)
    await message.reply(
        f"<b>User diizinkan memakai command dengan mode auth.</b>\n<b>ID:</b> <code>{user_id}</code>",
        parse_mode=ParseMode.HTML,
    )
