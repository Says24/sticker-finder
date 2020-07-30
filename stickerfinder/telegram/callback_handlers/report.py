from stickerfinder.models import Task
from stickerfinder.logic.maintenance import check_maintenance_chat
from stickerfinder.helper.callback import CallbackResult
from stickerfinder.telegram.wrapper import call_tg_func
from stickerfinder.telegram.keyboard import get_report_keyboard


def handle_report_ban(session, context):
    """Handle the ban button of voting tasks in maintenance channels."""
    task = session.query(Task).get(context.payload)
    if CallbackResult(context.action).name == "ban":
        task.sticker_set.banned = True
        call_tg_func(context.query, "answer", ["Set tagged as nsfw"])
    else:
        task.sticker_set.banned = False
        call_tg_func(context.query, "answer", ["Set no longer tagged as nsfw"])

    session.commit()

    keyboard = get_report_keyboard(task)
    call_tg_func(
        context.query.message, "edit_reply_markup", [], {"reply_markup": keyboard}
    )


def handle_report_nsfw(session, context):
    """Handle the nsfw button of voting tasks in maintenance channels."""
    task = session.query(Task).get(context.payload)
    if CallbackResult(context.action).name == "ban":
        task.sticker_set.nsfw = True
        call_tg_func(context.query, "answer", ["Set banned"])
    else:
        task.sticker_set.nsfw = False
        call_tg_func(context.query, "answer", ["Set unbanned"])

    session.commit()

    keyboard = get_report_keyboard(task)
    call_tg_func(
        context.query.message, "edit_reply_markup", [], {"reply_markup": keyboard}
    )


def handle_report_furry(session, context):
    """Handle the furry button of voting tasks in maintenance channels."""
    task = session.query(Task).get(context.payload)
    if CallbackResult(context.action).name == "ban":
        task.sticker_set.furry = True
        call_tg_func(context.query, "answer", ["Set tagged as furry"])
    else:
        task.sticker_set.furry = False
        call_tg_func(context.query, "answer", ["Set tagged as furry"])

    session.commit()

    keyboard = get_report_keyboard(task)
    call_tg_func(
        context.query.message, "edit_reply_markup", [], {"reply_markup": keyboard}
    )


def handle_report_next(session, context):
    """Handle the nextbutton of voting tasks in maintenance channels."""
    task = session.query(Task).get(context.payload)

    if not task.reviewed:
        task.reviewed = True
        check_maintenance_chat(session, context.tg_chat, context.chat)

    try:
        keyboard = get_report_keyboard(task)
        call_tg_func(
            context.query.message, "edit_reply_markup", [], {"reply_markup": keyboard}
        )
    except:  # noqa
        return
