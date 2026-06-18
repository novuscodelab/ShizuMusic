# --------------------------------------------------------------------------------
#  NovusMusic © 2026
#  Developed by Bad Munda 
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio
import html
import json
import os

import aiohttp
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

import config
from NovusMusic import bot, LOGGER
from NovusMusic.modules.block import user_allowed
from NovusMusic.utils.db import (
    is_nsfw_enabled,
    set_nsfw_enabled,
    is_badword_enabled,
    set_badword_enabled,
    is_link_filter_enabled,
    set_link_filter_enabled,
    is_document_filter_enabled,
    set_document_filter_enabled,
    get_mod_settings,
    approve_nsfw_user,
    disapprove_nsfw_user,
    is_nsfw_approved,
    get_nsfw_approved_users,
)
from NovusMusic.utils.permissions import is_user_authorized

DOWNLOAD_DIR = "downloads/nsfw"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

REPORT_AUTO_DELETE = 20   # seconds — scan report message auto-deletes after this


# ── Filters ──────────────────────────────────────────────────────────────────

def _is_plain_text(_, __, message: Message) -> bool:
    """Text messages that are NOT commands."""
    return bool(message.text) and not message.text.startswith("/")


not_command = filters.create(_is_plain_text)

MEDIA_FILTER = (
    filters.photo
    | filters.video
    | filters.animation
    | filters.sticker
    | filters.document
)


# ── API Helpers ──────────────────────────────────────────────────────────────

async def _scan_file(path: str, content_type: str) -> dict | None:
    """Upload local media file to the moderation API for scanning."""
    try:
        async with aiohttp.ClientSession() as session:
            with open(path, "rb") as f:
                data = aiohttp.FormData()
                data.add_field(
                    "file", f,
                    filename=os.path.basename(path),
                    content_type=content_type,
                )
                # Custom NSFW thresholds — config.NSFW_THRESHOLDS
                data.add_field("thresholds", json.dumps(config.NSFW_THRESHOLDS))
                headers = {"x-api-key": config.NSFW_API_KEY}
                async with session.post(
                    f"{config.NSFW_API_URL}/detect/upload",
                    data=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    if resp.status != 200:
                        LOGGER.warning(f"[nsfw] API status {resp.status}")
                        return None
                    return await resp.json()
    except Exception as e:
        LOGGER.error(f"[nsfw] scan_file failed: {e}")
        return None


async def _scan_text(text: str) -> dict | None:
    """Send plain text to the moderation API for bad-word + link checking."""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"text": text, "x_api_key": config.NSFW_API_KEY}
            async with session.post(
                f"{config.NSFW_API_URL}/text/check",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()
    except Exception as e:
        LOGGER.error(f"[nsfw] scan_text failed: {e}")
        return None


async def _check_document_api(filename: str) -> dict | None:
    """
    Ask the moderation API whether this filename is blocked. Filename only —
    no upload needed. Mainly useful for custom extensions an admin added at
    runtime via /blockedext/add on the API, beyond the local default list.
    """
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"filename": filename, "x_api_key": config.NSFW_API_KEY}
            async with session.post(
                f"{config.NSFW_API_URL}/document/check",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()
    except Exception as e:
        LOGGER.error(f"[nsfw] check_document_api failed: {e}")
        return None


# ── Media Helpers ────────────────────────────────────────────────────────────

def _media_content_type(message: Message) -> str | None:
    """Return a content-type string for the message's media, or None if unsupported."""
    if message.photo:
        return "image/jpeg"
    if message.video:
        return "video/mp4"
    if message.animation:
        return "video/mp4"
    if message.sticker:
        mime = message.sticker.mime_type or ""
        if "tgsticker" in mime:
            return "application/x-tgsticker"
        if "webm" in mime:
            return "video/webm"
        return "image/webp"
    if message.document:
        mime = message.document.mime_type or ""
        if mime.startswith("image/") or mime.startswith("video/") or "tgsticker" in mime:
            return mime
        return None
    return None


async def _auto_delete(message: Message, delay: int) -> None:
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass


# ── Blocked File Extensions ──────────────────────────────────────────────────

def _blocked_extension(filename: str) -> str | None:
    """Instant local check against config.BLOCKED_EXTENSIONS — no API call."""
    if not filename:
        return None
    name = filename.lower()
    for ext in config.BLOCKED_EXTENSIONS:
        if name.endswith(ext):
            return ext
    return None


def _build_blocked_file_report(filename: str, ext: str) -> str:
    return (
        "<b> File Deleted</b>\n\n"
        f"<b> Reason:</b> Blocked file type (<code>{html.escape(ext)}</code>)\n"
        f"<b> File:</b> <code>{html.escape(filename)}</code>\n\n"
        f"<b> Not allowed:</b> {', '.join(config.BLOCKED_EXTENSIONS)}"
    )


# ── Links ─────────────────────────────────────────────────────────────────

def _build_link_report(links: list[str]) -> str:
    shown = links[:5]
    lines = "\n".join(f"• <code>{html.escape(l)}</code>" for l in shown)
    more = f"\n<i>+{len(links) - 5} more</i>" if len(links) > 5 else ""
    return (
        "<b> Message Deleted</b>\n\n"
        f"<b> Reason:</b> Link detected\n"
        f"<b> Found:</b>\n{lines}{more}"
    )


async def _extract_user(client, message: Message, args: list):
    """
    Find the target user:
      1. The sender of the replied-to message
      2. /nsfwapprove <user_id|@username>

    Returns None if nothing matches.
    """
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user

    if args:
        target = args[0]
        try:
            if target.lstrip("-").isdigit():
                return await client.get_users(int(target))
            return await client.get_users(target)
        except Exception:
            return None

    return None


# ── Report Builder ───────────────────────────────────────────────────────────

def _build_report(result: dict) -> tuple[str, bool]:
    """Returns (report_text, should_delete)."""
    nsfw          = result.get("nsfw", {}) or {}
    triggered     = result.get("triggered")
    has_weapon    = result.get("has_weapon", False)
    has_drugs     = result.get("has_drugs", False)
    should_delete = result.get("should_delete", False)
    thresholds    = result.get("thresholds_used", {}) or {}

    threshold_line = ""
    if triggered:
        category   = triggered.capitalize()
        confidence = nsfw.get(triggered, 0) * 100
        thr        = thresholds.get(triggered)
        if thr is not None:
            threshold_line = f"<b> Threshold:</b> {thr * 100:.0f}%\n"
    elif has_weapon:
        category   = "Weapon"
        confs      = [d["confidence"] for d in result.get("detections", []) if d["type"] == "weapon"]
        confidence = (max(confs) * 100) if confs else 0
    elif has_drugs:
        category   = "Drugs"
        confs      = [d["confidence"] for d in result.get("detections", []) if d["type"] == "drug"]
        confidence = (max(confs) * 100) if confs else 0
    else:
        category   = "Clean"
        confidence = nsfw.get("neutral", 0) * 100

    status      = "NSFW Detected " if should_delete else "Safe "
    action      = "Delete " if should_delete else "None"
    weapon_str  = "Detected " if has_weapon else "Not Detected "
    drugs_str   = "Detected " if has_drugs else "Not Detected "

    text = (
        "<b> NSFW Scan Result</b>\n\n"
        f"<b> Status:</b> {status}\n"
        f"<b> Category:</b> {category}\n"
        f"<b> Confidence:</b> {confidence:.1f}%\n"
        f"{threshold_line}\n"
        f"<b> Recommended Action:</b> {action}\n\n"
        f"<b> Weapon:</b> {weapon_str}\n"
        f"<b> Drugs:</b> {drugs_str}"
    )
    return text, should_delete


# ── Filter Toggle Commands (nsfw / badword / linkfilter / docfilter) ─────────

async def _toggle_filter_cmd(message: Message, name: str, getter, setter, label: str) -> None:
    args = message.command[1:]

    if not args:
        status = "ON " if getter(message.chat.id) else "OFF "
        await message.reply(
            f"<b> {label} is currently:</b> {status}\n"
            f"<b> Usage:</b> <code>/{name} on</code> | <code>/{name} off</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    if not await is_user_authorized(message):
        await message.reply(
            "<b> Only admins can change this setting.</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    arg = args[0].lower()
    if arg == "on":
        setter(message.chat.id, True)
        await message.reply(f"<b> {label} Enabled </b>", parse_mode=ParseMode.HTML)
    elif arg == "off":
        setter(message.chat.id, False)
        await message.reply(f"<b> {label} Disabled </b>", parse_mode=ParseMode.HTML)
    else:
        await message.reply(
            f"<b> Usage:</b> <code>/{name} on</code> | <code>/{name} off</code>",
            parse_mode=ParseMode.HTML,
        )


@bot.on_message(filters.command("nsfw") & filters.group & user_allowed)
async def nsfw_toggle_cmd(_, message: Message) -> None:
    await _toggle_filter_cmd(message, "nsfw", is_nsfw_enabled, set_nsfw_enabled, "NSFW Filter")


@bot.on_message(filters.command("badword") & filters.group & user_allowed)
async def badword_toggle_cmd(_, message: Message) -> None:
    await _toggle_filter_cmd(message, "badword", is_badword_enabled, set_badword_enabled, "Bad-Word Filter")


@bot.on_message(filters.command(["linkfilter", "link"]) & filters.group & user_allowed)
async def link_toggle_cmd(_, message: Message) -> None:
    await _toggle_filter_cmd(message, "linkfilter", is_link_filter_enabled, set_link_filter_enabled, "Link Filter")


@bot.on_message(filters.command(["docfilter", "filefilter"]) & filters.group & user_allowed)
async def doc_toggle_cmd(_, message: Message) -> None:
    await _toggle_filter_cmd(message, "docfilter", is_document_filter_enabled, set_document_filter_enabled, "Document Filter")


@bot.on_message(filters.command("filters") & filters.group & user_allowed)
async def filters_status_cmd(_, message: Message) -> None:
    s = get_mod_settings(message.chat.id)

    def mark(v: bool) -> str:
        return "ON " if v else "OFF "

    text = (
        "<b> Moderation Filters</b>\n\n"
        f"<b> NSFW (media):</b> {mark(s['nsfw'])}\n"
        f"<b> Bad Words:</b> {mark(s['badword'])}\n"
        f"<b> Links:</b> {mark(s['link'])}\n"
        f"<b> Blocked Files:</b> {mark(s['document'])}\n\n"
        "<b> Toggle individually:</b>\n"
        "• <code>/nsfw on|off</code>\n"
        "• <code>/badword on|off</code>\n"
        "• <code>/linkfilter on|off</code>\n"
        "• <code>/docfilter on|off</code>"
    )
    await message.reply(text, parse_mode=ParseMode.HTML)


# ── /nsfwapprove ──────────────────────────────────────────────────────────────
@bot.on_message(filters.command("nsfwapprove") & filters.group & user_allowed)
async def nsfw_approve_cmd(client, message: Message) -> None:
    if not await is_user_authorized(message):
        await message.reply(
            "<b> Only admins can use this command.</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    args = message.command[1:]

    # /nsfwapprove list
    if args and args[0].lower() == "list":
        users = get_nsfw_approved_users(message.chat.id)
        if not users:
            await message.reply(
                "<b> No NSFW-approved users in this chat.</b>",
                parse_mode=ParseMode.HTML,
            )
            return
        lines = "\n".join(f"• <code>{uid}</code>" for uid in users)
        await message.reply(
            f"<b> NSFW-Approved Users:</b>\n{lines}",
            parse_mode=ParseMode.HTML,
        )
        return

    # /nsfwapprove off
    remove = bool(args) and args[-1].lower() in ("off", "remove", "-")
    target_args = args[:-1] if remove else args

    target = await _extract_user(client, message, target_args)
    if target is None:
        await message.reply(
            "<b> Reply to a user's message</b> (or provide their ID/username) "
            "<b>along with</b> <code>/nsfwapprove</code> <b>to whitelist them from the NSFW filter.</b>\n\n"
            "<b> Usage:</b>\n"
            "• <code>/nsfwapprove</code> — reply to approve\n"
            "• <code>/nsfwapprove off</code> — reply to remove approval\n"
            "• <code>/nsfwapprove list</code> — view approved users",
            parse_mode=ParseMode.HTML,
        )
        return

    if remove:
        disapprove_nsfw_user(message.chat.id, target.id)
        await message.reply(
            f"<b></b> {target.mention} <b>removed from the approved list </b>\n"
            f"<b>Their media/text/files/links will now be checked again.</b>",
            parse_mode=ParseMode.HTML,
        )
    else:
        approve_nsfw_user(message.chat.id, target.id)
        await message.reply(
            f"<b></b> {target.mention} <b>Approved </b>\n"
            f"<b>Their media/text/files/links will bypass all moderation filters.</b>",
            parse_mode=ParseMode.HTML,
        )


# ── Media Scanner — photo / video / gif / sticker / animation ───────────────

@bot.on_message(MEDIA_FILTER & filters.group & user_allowed)
async def nsfw_media_scan(client, message: Message) -> None:
    chat_id = message.chat.id
    bypass = bool(message.from_user) and is_nsfw_approved(chat_id, message.from_user.id)

    # ── 1. Blocked file-extension check — independent toggle, runs first ───
    if message.document and not bypass and is_document_filter_enabled(chat_id):
        filename = message.document.file_name or ""
        ext = _blocked_extension(filename)               # instant local check
        if not ext:
            api_result = await _check_document_api(filename)  # custom list on API
            if api_result and api_result.get("blocked"):
                ext = api_result.get("extension") or os.path.splitext(filename.lower())[1]

        if ext:
            try:
                await message.delete()
            except Exception as e:
                LOGGER.warning(f"[nsfw] could not delete blocked file: {e}")

            user = message.from_user
            header = f"<b> User:</b> {user.mention}\n\n" if user else ""
            sent = await client.send_message(
                chat_id,
                header + _build_blocked_file_report(filename, ext),
                parse_mode=ParseMode.HTML,
            )
            asyncio.create_task(_auto_delete(sent, REPORT_AUTO_DELETE))
            return  # already handled — skip the NSFW scan below

    # ── 2. NSFW image/video scan ─────────────────────────────────────────
    if not is_nsfw_enabled(chat_id) or bypass:
        return

    content_type = _media_content_type(message)
    if content_type is None:
        return

    path = None
    try:
        path = await message.download(file_name=f"{DOWNLOAD_DIR}/")
    except Exception as e:
        LOGGER.error(f"[nsfw] download failed: {e}")
        return

    try:
        result = await _scan_file(path, content_type)
    finally:
        try:
            os.remove(path)
        except Exception:
            pass

    if not result:
        return  # API unreachable — fail silently, don't block the chat

    report_text, should_delete = _build_report(result)
    if not should_delete:
        return

    try:
        await message.delete()
    except Exception as e:
        LOGGER.warning(f"[nsfw] could not delete message: {e}")

    user   = message.from_user
    header = f"<b> User:</b> {user.mention}\n\n" if user else ""
    sent = await client.send_message(
        chat_id,
        header + report_text,
        parse_mode=ParseMode.HTML,
    )
    asyncio.create_task(_auto_delete(sent, REPORT_AUTO_DELETE))


# ── Text Scanner — bad words ─────────────────────────────────────────────────

@bot.on_message(filters.text & filters.group & not_command & user_allowed)
async def nsfw_text_scan(client, message: Message) -> None:
    chat_id = message.chat.id

    if message.from_user and is_nsfw_approved(chat_id, message.from_user.id):
        return

    link_on    = is_link_filter_enabled(chat_id)
    badword_on = is_badword_enabled(chat_id)
    if not link_on and not badword_on:
        return

    if len(message.text.strip()) < 2:
        return

    # Single API call covers both checks — /text/check returns has_link/links
    # alongside has_bad_words/toxicity_score.
    result = await _scan_text(message.text)
    if not result:
        return  # API unreachable — fail silently, don't block the chat

    # ── 1. Link filter ───────────────────────────────────────────────────
    if link_on and result.get("has_link"):
        try:
            await message.delete()
        except Exception as e:
            LOGGER.warning(f"[nsfw] could not delete link message: {e}")

        user   = message.from_user
        header = f"<b> User:</b> {user.mention}\n\n" if user else ""
        sent = await client.send_message(
            chat_id,
            header + _build_link_report(result.get("links", [])),
            parse_mode=ParseMode.HTML,
        )
        asyncio.create_task(_auto_delete(sent, REPORT_AUTO_DELETE))
        return  # message already gone — no point bad-word checking it too

    # ── 2. Bad-word filter ───────────────────────────────────────────────
    if not badword_on or not result.get("has_bad_words"):
        return

    try:
        await message.delete()
    except Exception as e:
        LOGGER.warning(f"[nsfw] could not delete text message: {e}")

    user      = message.from_user
    mention   = user.mention if user else "Someone"
    toxicity  = result.get("toxicity_score", 0) * 100

    warn_text = (
        "<b> Message Deleted</b>\n\n"
        f"<b> User:</b> {mention}\n"
        f"<b> Reason:</b> Bad word(s) detected\n"
        f"<b> Toxicity:</b> {toxicity:.0f}%"
    )
    sent = await client.send_message(
        chat_id,
        warn_text,
        parse_mode=ParseMode.HTML,
    )
    asyncio.create_task(_auto_delete(sent, REPORT_AUTO_DELETE))
