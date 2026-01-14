import json
import logging
import os
import sys
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler

import discord


def configure_logging() -> logging.Logger:
    """Configure persistent file logging to catch crashes."""
    os.makedirs('/tmp/bot_logs', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            RotatingFileHandler(
                '/tmp/bot_logs/bot_crash.log',
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=3,
            ),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


logger = configure_logging()


def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Catch ALL uncaught exceptions and log them before the bot dies."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical("UNCAUGHT EXCEPTION - Bot is crashing!", exc_info=(exc_type, exc_value, exc_traceback))
    with open('/tmp/bot_logs/bot_crash.log', 'a') as f:
        f.write(f"\n{'=' * 60}\n")
        f.write(f"FATAL CRASH at {datetime.now()}\n")
        f.write(f"{'=' * 60}\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        f.write(f"\n{'=' * 60}\n\n")


def asyncio_exception_handler(loop, context):
    """Catch uncaught asyncio exceptions."""
    exception = context.get('exception')
    if exception:
        logger.critical(f"ASYNCIO EXCEPTION: {context['message']}", exc_info=exception)
        with open('/tmp/bot_logs/bot_crash.log', 'a') as f:
            f.write(f"\n{'=' * 60}\n")
            f.write(f"ASYNCIO CRASH at {datetime.now()}\n")
            f.write(f"{'=' * 60}\n")
            f.write(f"Message: {context['message']}\n")
            if exception:
                traceback.print_exception(type(exception), exception, exception.__traceback__, file=f)
            f.write(f"\n{'=' * 60}\n\n")
    else:
        logger.error(f"ASYNCIO ERROR: {context}")


def install_exception_handlers() -> None:
    """Install global exception handlers."""
    sys.excepthook = global_exception_handler


def log_panel_error(panel_name: str, error: Exception, extra_context: dict = None):
    """Log panel/dashboard errors with full stack trace for debugging."""
    try:
        with open('/tmp/bot_logs/panel_errors.log', 'a') as f:
            f.write(f"\n{'=' * 80}\n")
            f.write(f"{panel_name.upper()} ERROR at {datetime.now()}\n")
            f.write(f"Error Type: {type(error).__name__}\n")
            f.write(f"Error Message: {str(error)}\n")
            if extra_context:
                f.write(f"Context: {json.dumps(extra_context, indent=2)}\n")
            f.write(f"{'=' * 80}\n")
            traceback.print_exception(type(error), error, error.__traceback__, file=f)
            f.write(f"\n{'=' * 80}\n\n")
        logger.error(f"[{panel_name}] {type(error).__name__}: {error}")
    except Exception:
        pass  # Don't let logging failures crash the bot


def safe_interaction(func):
    """Decorator to catch exceptions in Discord interactions and keep bot alive."""

    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        try:
            return await func(self, interaction, *args, **kwargs)
        except Exception as e:
            logger.critical(f"INTERACTION ERROR in {func.__name__}", exc_info=e)
            with open('/tmp/bot_logs/bot_crash.log', 'a') as f:
                f.write(f"\n{'=' * 60}\n")
                f.write(f"INTERACTION CRASH at {datetime.now()}\n")
                f.write(f"Function: {func.__name__}\n")
                f.write(f"Button: {getattr(self, 'custom_id', 'unknown')}\n")
                f.write(f"User: {interaction.user}\n")
                f.write(f"Guild: {interaction.guild}\n")
                f.write(f"{'=' * 60}\n")
                traceback.print_exception(type(e), e, e.__traceback__, file=f)
                f.write(f"\n{'=' * 60}\n\n")

            # Try to respond to user
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
                else:
                    await interaction.edit_original_response(content=f"❌ Error: {str(e)}")
            except Exception:
                pass  # If we can't respond, at least we logged it

    return wrapper
