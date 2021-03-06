"""Helper functions for handling sticker sets."""
import io
import re
import logging
from PIL import Image
from pytesseract import image_to_string
from telegram.error import BadRequest, TimedOut

from stickerfinder.config import config
from stickerfinder.logic.tag import add_original_emojis
from stickerfinder.models import Sticker, Chat
from stickerfinder.sentry import sentry
from stickerfinder.telegram.keyboard import get_tag_this_set_keyboard


def refresh_stickers(session, sticker_set, bot, refresh_ocr=False, chat=None):
    """Refresh stickers and set data from telegram."""
    # Get sticker set from telegram and create new a Sticker for each sticker
    stickers = []
    try:
        tg_sticker_set = bot.get_sticker_set(sticker_set.name)
    except BadRequest as e:
        if (
            e.message == "Stickerset_invalid"
            or e.message == "Requested data is inaccessible"
        ):
            # The sticker set has been deleted.
            # Mark it as such and auto review the task
            sticker_set.deleted = True
            sticker_set.completed = True
            if len(sticker_set.tasks) > 0 and sticker_set.tasks[0].type == "scan_set":
                sticker_set.tasks[0].reviewed = True
            return

        raise e

    sticker_set.animated = tg_sticker_set.is_animated

    for tg_sticker in tg_sticker_set.stickers:
        # Ignore already existing stickers if we don't need to rescan images
        sticker = session.query(Sticker).get(tg_sticker.file_unique_id)
        text = None
        if not tg_sticker.is_animated and (sticker is None or refresh_ocr):
            text = extract_text(tg_sticker)

        # Create new Sticker.
        if sticker is None:
            sticker = Sticker(tg_sticker.file_id, tg_sticker.file_unique_id)

        # Only set text, if we got some text from the ocr recognition
        if text is not None:
            sticker.text = text

        sticker.animated = tg_sticker.is_animated
        add_original_emojis(session, sticker, tg_sticker.emoji)
        stickers.append(sticker)
        session.commit()

    sticker_set.name = tg_sticker_set.name.lower()

    sticker_set.title = tg_sticker_set.title.lower()
    sticker_set.stickers = stickers
    sticker_set.complete = True

    review_task = None
    if len(sticker_set.tasks) > 0 and sticker_set.tasks[0].type == "scan_set":
        review_task = sticker_set.tasks[0]

    # Auto accept everything if the config says so
    if review_task and config["mode"]["auto_accept_set"] and not review_task.reviewed:
        sticker_set.reviewed = True
        review_task.reviewed = True

        keyboard = get_tag_this_set_keyboard(sticker_set, review_task.user)
        message = f"Stickerset {sticker_set.name} has been added."
        bot.send_message(review_task.chat.id, message, reply_markup=keyboard)

        newsfeed_chats = session.query(Chat).filter(Chat.is_newsfeed.is_(True)).all()
        for chat in newsfeed_chats:
            bot.send_sticker(chat.id, sticker_set.stickers[0].file_id)

    session.commit()


def merge_sticker(session, sticker, new_sticker):
    """Merge two identical stickers with different file ids."""
    # Merge new tags into old sticker
    for tag in new_sticker.tags:
        if tag not in sticker.tags:
            sticker.tags.append(tag)

    # Merge usages
    for new_usage in new_sticker.usages:
        # Check if we find a usage from the old sticker
        found_equivalent = False
        for usage in sticker.usages:
            if usage.user == new_usage.user:
                usage.usage_count += new_usage.usage_count
                found_equivalent = True
                break

        # Point usage to old sticker before we update the file id.
        # Otherwise it would be deleted by cascade or there would
        # be a unique constraint violation
        if not found_equivalent:
            new_usage.sticker_file_unique_id = sticker.file_unique_id
            session.commit()

    session.delete(new_sticker)
    session.commit()


def extract_text(tg_sticker):
    """Extract the text from a telegram sticker."""
    text = None
    logger = logging.getLogger()
    try:
        # Get Image and preprocess it
        tg_file = tg_sticker.get_file()
        image_bytes = tg_file.download_as_bytearray()
        with Image.open(io.BytesIO(image_bytes)).convert("RGB") as image:
            # Extract text
            text = image_to_string(image).strip().lower()

        # Only allow chars and remove multiple spaces to single spaces
        text = re.sub("[^a-zA-Z\ ]+", "", text)
        text = re.sub(" +", " ", text)
        text = text.strip()
        if text == "":
            text = None

    except TimedOut:
        logger.info(f"Finally failed on file {tg_sticker.file_unique_id}")
        pass
    except BadRequest:
        logger.info(f"Failed to get image of {tg_sticker.file_unique_id}")
        pass
    except OSError:
        logger.info(f"Failed to open image {tg_sticker.file_unique_id}")
        pass
    except:
        sentry.capture_exception(tags={"context": "text_extraction"})
        pass

    return text
