# --------------------------------------------------------------------------------
#  NovusMusic © 2026
#  Developed by Bad Munda 
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import random

from pyrogram import filters
from pyrogram.errors import ChatAdminRequired
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from NovusMusic import bot
from NovusMusic.utils.db import (
    add_broadcast_chat,
    add_served_chat,
    remove_broadcast_chat,
    remove_served_chat,
)

LEFT_PHOTOS = [
    "https://telegra.ph/file/1949480f01355b4e87d26.jpg",
    "https://telegra.ph/file/3ef2cc0ad2bc548bafb30.jpg",
    "https://telegra.ph/file/a7d663cd2de689b811729.jpg",
    "https://telegra.ph/file/6f19dc23847f5b005e922.jpg",
    "https://telegra.ph/file/2973150dd62fd27a3a6ba.jpg",
]


# ── Bot added to group ─────────────────────────────────────────────────────────

@bot.on_message(filters.new_chat_members, group=-10)
async def bot_added_watcher(_, message: Message) -> None:
    try:
        chat    = message.chat
        chat_id = chat.id
        me      = await bot.get_me()

        for member in message.new_chat_members:
            if member.id != me.id:
                continue

            add_served_chat(chat_id)
            add_broadcast_chat(chat_id, "group")

            added_by         = message.from_user
            added_by_mention = added_by.mention if added_by else "ᴜɴᴋɴᴏᴡɴ"

            admin_request_text = (
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
                InlineKeyboardButton("Jadikan admin", url=f"tg://user?id={me.id}")
            ]])
            try:
                await message.reply_text(admin_request_text, parse_mode=ParseMode.HTML, reply_markup=admin_kb)
            except Exception:
                pass

            if not config.LOGGER_ID:
                return

            try:
                invite_link = await bot.export_chat_invite_link(chat_id)
                link_text   = f"<a href='{invite_link}'>ɢᴇᴛ ʟɪɴᴋ</a>"
            except (ChatAdminRequired, Exception):
                link_text = "ɴᴏ ʟɪɴᴋ"

            try:
                count = await bot.get_chat_members_count(chat_id)
            except Exception:
                count = "N/A"

            username   = f"@{chat.username}" if chat.username else "ᴘʀɪᴠᴀᴛᴇ ɢʀᴏᴜᴘ"
            chat_photo = None
            try:
                if chat.photo:
                    chat_photo = await bot.download_media(
                        chat.photo.big_file_id,
                        file_name=f"grppp_{chat_id}.png",
                    )
            except Exception:
                chat_photo = None

            log_text = (
                "<b> #ɴᴇᴡɢʀᴏᴜᴘ — ʙᴏᴛ ᴀᴅᴅᴇᴅ!</b>\n\n"
                f"<b> ᴄʜᴀᴛ ɴᴀᴍᴇ  :</b> {chat.title}\n"
                f"<b> ᴄʜᴀᴛ ɪᴅ    :</b> <code>{chat_id}</code>\n"
                f"<b> ᴜsᴇʀɴᴀᴍᴇ   :</b> {username}\n"
                f"<b> ɢʀᴏᴜᴘ ʟɪɴᴋ  :</b> {link_text}\n"
                f"<b> ᴍᴇᴍʙᴇʀs    :</b> {count}\n"
                f"<b> ᴀᴅᴅᴇᴅ ʙʏ   :</b> {added_by_mention}"
            )
            log_kb = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    f" {added_by.first_name if added_by else 'ᴜsᴇʀ'}",
                    user_id=added_by.id if added_by else config.OWNER_ID,
                )
            ]]) if added_by else None

            try:
                if chat_photo:
                    await bot.send_photo(
                        config.LOGGER_ID, photo=chat_photo,
                        caption=log_text, parse_mode=ParseMode.HTML, reply_markup=log_kb,
                    )
                else:
                    await bot.send_message(
                        config.LOGGER_ID, log_text,
                        parse_mode=ParseMode.HTML, reply_markup=log_kb,
                        disable_web_page_preview=True,
                    )
            except Exception:
                pass

    except Exception as e:
        print(f"[watcher] bot_added_watcher error: {e}")


# ── Bot left / removed ─────────────────────────────────────────────────────────

@bot.on_message(filters.left_chat_member, group=-12)
async def bot_left_watcher(_, message: Message) -> None:
    try:
        left_member = message.left_chat_member
        if not left_member:
            return

        me = await bot.get_me()
        if left_member.id != me.id:
            return

        chat    = message.chat
        chat_id = chat.id

        remove_served_chat(chat_id)
        remove_broadcast_chat(chat_id)

        removed_by         = message.from_user
        removed_by_mention = removed_by.mention if removed_by else "ᴜɴᴋɴᴏᴡɴ ᴜsᴇʀ"
        username           = f"@{chat.username}" if chat.username else "ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ"

        if not config.LOGGER_ID:
            return

        left_text = (
            "<b> #ʟᴇғᴛɢʀᴏᴜᴘ </b>\n\n"
            f"<b> ᴄʜᴀᴛ ᴛɪᴛʟᴇ   :</b> {chat.title}\n"
            f"<b> ᴄʜᴀᴛ ɪᴅ     :</b> <code>{chat_id}</code>\n"
            f"<b> ᴜsᴇʀɴᴀᴍᴇ    :</b> {username}\n"
            f"<b> ʀᴇᴍᴏᴠᴇᴅ ʙʏ  :</b> {removed_by_mention}\n"
            f"<b> ʙᴏᴛ          :</b> @{me.username}"
        )

        try:
            await bot.send_photo(
                config.LOGGER_ID,
                photo=random.choice(LEFT_PHOTOS),
                caption=left_text,
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            try:
                await bot.send_message(config.LOGGER_ID, left_text, parse_mode=ParseMode.HTML)
            except Exception:
                pass

    except Exception as e:
        print(f"[watcher] bot_left_watcher error: {e}")
