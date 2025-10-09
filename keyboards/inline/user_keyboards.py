from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import data_store

def create_user_buttons() -> InlineKeyboardMarkup:
    """Creates the main keyboard for regular users."""
    cfg = data_store.bot_data['ui_config']
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text=cfg['date_button_label'], callback_data="show_date"),
        InlineKeyboardButton(text=cfg['time_button_label'], callback_data="show_time"),
        InlineKeyboardButton(text=cfg['reminder_button_label'], callback_data="show_reminder")
    )
    return keyboard
