# --------------------------------------------------------------------------------
#  NovusMusic © 2026
#  Developed by Bad Munda 
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio
import random

from pyrogram import filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from NovusMusic import bot
from config import START_ANIMATIONS
from NovusMusic.modules.block import user_allowed
from NovusMusic.utils.db import add_broadcast_chat, add_served_chat, add_served_user

# ── Message effect IDs (Telegram premium effects) ─────────────────────────────
EFFECT_ID = [
    5046509860389126442,
    5107584321108051014,
    5104841245755180586,
    5159385139981059251,
]

# ── /start ────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("start") & user_allowed)
async def start_handler(_, message: Message) -> None:

    uid       = message.from_user.id
    name      = message.from_user.first_name or "User"
    chat_id   = message.chat.id
    chat_type = message.chat.type
    animation = random.choice(START_ANIMATIONS)

    # ── Delete the user's /start command message ──────────────────────────────
    try:
        await message.delete()
    except Exception:
        pass

    try:
        add_served_user(uid)
        add_served_chat(chat_id)
    except Exception:
        pass

    # ── Private ───────────────────────────────────────────────────────────────
    if chat_type == ChatType.PRIVATE:

        caption = (
            "<b>╭────────────────────▣</b>\n"
            f"<b>│ Hai</b> <a href='tg://user?id={uid}'>{name}</a>,\n"
            f"<b>│ ini {config.BOT_NAME}!</b>\n"
            "<b>├────────────────────▣</b>\n"
            "<b>│ Bot musik Telegram yang cepat</b>\n"
            "<b>│ dan gampang dipakai buat VC.</b>\n"
            "<b>│ Fiturnya lengkap, tinggal pakai.</b>\n"
            "<b>├────────────────────▣</b>\n"
            "<b>│ Klik bantuan buat lihat semua perintah.</b>\n"
            "<b>├────────────────────▣</b>\n"
            f"<b>│ Didukung oleh » "
            f"<a href='https://t.me/NovusSociety'>NovusMusic™</a></b>\n"
            "<b>╰────────────────────▣</b>"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Tambah ke grup",
                                  url=f"{config.BOT_LINK}?startgroup=true")],
            [
                InlineKeyboardButton("Support", url=config.SUPPORT_GROUP),
                InlineKeyboardButton("Update",  url=config.UPDATES_CHANNEL),
            ],
            [InlineKeyboardButton("Bantuan & Perintah",
                                  callback_data="show_help")],
            [
                InlineKeyboardButton("Owner",
                                     url=f"tg://user?id={config.OWNER_ID}"),
                InlineKeyboardButton("Source",
                                     url="https://github.com/Badmunda05/NovusMusic/fork"),
            ],
        ])

        sent = await message.reply_animation(
            animation,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
            message_effect_id=random.choice(EFFECT_ID),
        )

        try:
            add_broadcast_chat(chat_id, "private")
        except Exception:
            pass

        if config.LOGGER_ID:
            try:
                await bot.send_message(
                    config.LOGGER_ID,
                    "<b>#ɴᴇᴡᴜsᴇʀ sᴛᴀʀᴛᴇᴅ</b>\n\n"
                    f"<b> ɴᴀᴍᴇ     :</b> <a href='tg://user?id={uid}'>{name}</a>\n"
                    f"<b> ɪᴅ       :</b> <code>{uid}</code>\n"
                    f"<b> ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username or 'N/A'}",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass

    # ── Group ─────────────────────────────────────────────────────────────────
    else:
        chat_title = message.chat.title or "ᴛʜɪs ᴄʜᴀᴛ"
        caption = (
            f"Hai <a href='tg://user?id={uid}'>{name}</a>,\n"
            f"ini <b>{config.BOT_NAME}</b>.\n\n"
            f"Makasih sudah nambahin aku ke <b>{chat_title}</b>.\n"
            f"Sekarang {name} bisa putar lagu di sini."
        )
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Tambah ke grup",
                                     url=f"{config.BOT_LINK}?startgroup=true"),
                InlineKeyboardButton("Support", url=config.SUPPORT_GROUP),
            ],
            [InlineKeyboardButton("Bantuan & Perintah",
                                  callback_data="show_help")],
        ])

        sent = await message.reply_animation(
            animation,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )

        admin_msg = (
            "<b>╭──────────────────────▣</b>\n"
            "<b>│ Makasih sudah nambahin aku!</b>\n"
            "<b>├──────────────────────▣</b>\n"
            "<b>│ Tolong jadiin aku admin</b>\n"
            "<b>│ dengan izin ini:</b>\n"
            "<b>├──────────────────────▣</b>\n"
            "<b>│ Hapus pesan</b>\n"
            "<b>│ Kelola video chat</b>\n"
            "<b>│ Undang pengguna</b>\n"
            "<b>├──────────────────────▣</b>\n"
            "<b>│ Kalau belum admin,</b>\n"
            "<b>│ beberapa fitur nggak bakal jalan.</b>\n"
            "<b>╰──────────────────────▣</b>"
        )
        admin_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "Jadikan admin",
                url=f"tg://user?id={(await bot.get_me()).id}",
            )
        ]])
        try:
            admin_sent = await message.reply_text(
                admin_msg,
                parse_mode=ParseMode.HTML,
                reply_markup=admin_kb,
            )
        except Exception:
            pass

        try:
            add_broadcast_chat(chat_id, "group")
        except Exception:
            pass


# ── /help ─────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("help") & user_allowed)
async def help_handler(_, message: Message) -> None:

    uid  = message.from_user.id
    name = message.from_user.first_name or "User"

    # ── Delete the user's /help command message ───────────────────────────────
    try:
        await message.delete()
    except Exception:
        pass

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ᴧᴅᴍɪɴ",    callback_data="help_admin"),
            InlineKeyboardButton("ᴧ-ᴘʟᴀʏ",   callback_data="help_autoplay"),
            InlineKeyboardButton("ɢ-ᴄᴧsᴛ",   callback_data="help_gcast"),
        ],
        [
            InlineKeyboardButton("ʙʟ-ᴄʜᴧᴛ",  callback_data="help_blchat"),
            InlineKeyboardButton("ʙʟ-ᴜsᴇʀs", callback_data="help_blusers"),
            InlineKeyboardButton("ᴘɪɴɢ",     callback_data="help_ping"),
        ],
        [
            InlineKeyboardButton("ᴘʟᴀʏ",     callback_data="help_play"),
            InlineKeyboardButton("sᴘᴇᴇᴅ",    callback_data="help_speed"),
            InlineKeyboardButton("ɪɴғᴏ",     callback_data="help_info"),
        ],
        [
            InlineKeyboardButton("⌯ ᴄʟᴏsᴇ ⌯", callback_data="close_help"),
        ],
    ])

    animation = random.choice(START_ANIMATIONS)

    sent = await message.reply_animation(
        animation,
        caption=(
            "<b>╭────────────────────▣</b>\n"
            f"<b>│ Hai</b> <a href='tg://user?id={uid}'>{name}</a>,\n"
            "<b>├────────────────────▣</b>\n"
            "<b>│ Pilih kategori yang kamu butuhin:</b>\n"
            "<b>├────────────────────▣</b>\n"
            f"<b>│ Didukung oleh » "
            f"<a href='https://t.me/NovusSociety'>NovusMusic™</a></b>\n"
            "<b>╰────────────────────▣</b>"
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )
