from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from ShizuMusic import bot


async def _block_middleware(_, message: Message) -> None:
    """
    Global middleware handler registered at group=-1.
    Runs before every other handler. If the chat or user is blocked,
    it calls message.stop_propagation() so no plugin ever sees the message.
    """
    try:
        from ShizuMusic.plugins.block import is_group_blocked, is_user_blocked
    except ImportError:
        return  # block plugin not loaded yet — let it pass

    chat_id = message.chat.id if message.chat else None
    user_id = message.from_user.id if message.from_user else None

    if chat_id and is_group_blocked(chat_id):
        message.stop_propagation()
        return

    if user_id and is_user_blocked(user_id):
        message.stop_propagation()
        return


def register_block_middleware() -> None:
    """
    Call this once during bot startup (before plugins load).
    Example in __main__.py:

        from ShizuMusic.middleware import register_block_middleware
        register_block_middleware()
    """
    bot.add_handler(
        MessageHandler(
            _block_middleware,
            filters=filters.all,
        ),
        group=-1,   # runs before all other handlers (group 0, 1, 2 ...)
    )
