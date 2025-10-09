from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_user_buttons() -> InlineKeyboardMarkup:
    """Creates the main keyboard for regular users."""
    # This keyboard is now static, but could be made dynamic from DB if needed.
    return InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton("📅 التاريخ الهجري", callback_data="show_date"),
        InlineKeyboardButton("⏰ الوقت الآن", callback_data="show_time"),
        InlineKeyboardButton("💡 تذكير", callback_data="show_reminder")
    )
