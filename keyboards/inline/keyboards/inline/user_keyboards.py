from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import data_store

def create_user_buttons() -> InlineKeyboardMarkup:
    """Creates the main keyboard for regular users."""
    cfg = data_store.bot_data.get('ui_config', {})
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text=cfg.get('date_button_label', '📅 التاريخ'), callback_data="show_date"),
        InlineKeyboardButton(text=cfg.get('time_button_label', '⏰ الساعة الان'), callback_data="show_time"),
        InlineKeyboardButton(text=cfg.get('reminder_button_label', '💡 تذكير يومي'), callback_data="show_reminder")
    )
    
