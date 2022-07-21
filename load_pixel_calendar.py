"""
Module to display created pixels as dates inside calendar, which is shown as inline keyboard.
"""

from datetime import date
from typing import Optional, List
from aiogram import types
from aiogram.utils.callback_data import CallbackData
from utils import User, str_to_date, get_user, date_to_str
from pixela import Pixels

ROW_WIDTH = 4

cb_calendar = CallbackData('calendar', 'date', 'action', 'direction')
cb_pixel = CallbackData('pixels', 'pixel', 'action')
ignore_callback = cb_calendar.new('', '', 'ignore')


async def load_pixels(pixels: List[Pixels], user: User,
                      action: str) -> Optional[types.InlineKeyboardMarkup]:
    """
    Sorts pixels and loads those corresponding to the current month.
    Displays dates as inline buttons and adds button for dates of previous month if such exist.
    :param pixels: list of all available pixels
    :param user:
    :param action: whether edit or delete
    :return: markup with buttons for dates or none
    """
    if len(pixels) > 0:
        pixels_sorted = convert_pixel_str_to_date(pixels)
        pixels_sorted = sorted(pixels_sorted, key=lambda pix: pix['date'], reverse=True)
        ini_date = pixels_sorted[0]['date']
        last_date = date(year=ini_date.year, month=ini_date.month, day=1)
        month = last_date.strftime('%B')
        markup = types.InlineKeyboardMarkup(row_width=ROW_WIDTH)
        markup.row()
        buttons = []
        for pixel_fmt in pixels_sorted:
            if last_date <= pixel_fmt['date'] <= ini_date:
                btn = create_inline_btn_for_date(pixel_fmt['date'], pixel_fmt["quantity"],
                                                 user.graph["unit"], action)
                buttons.append(btn)
            else:
                markup.insert(create_inline_btn_for_direction(last_date, 'prev', action))
                break
        markup.insert(types.InlineKeyboardButton(text=month, callback_data=ignore_callback))
        buttons = buttons[::-1]
        return order_buttons(buttons, markup)
    return None


async def load_pixel_prev(query: types.CallbackQuery, callback_data: dict, users: dict):
    """
    Displays dates as inline buttons for previous month.
    We're using higher order function to define local storage and
    be able to use inner function for query handler in main bot script.
    :param callback_data:
    :param query:
    :param users: local storage
    :return: inner function
    """
    action = callback_data['action']
    cur_month = str_to_date(callback_data['date'])
    user = await get_user(query.from_user.id, users)
    pixels_sorted = convert_pixel_str_to_date(user.pixels)
    pixels_sorted = sorted([pix for pix in pixels_sorted if pix['date'] < cur_month],
                           key=lambda pix: pix['date'], reverse=True)
    ini_date = pixels_sorted[0]['date']
    last_date = date(year=ini_date.year, month=ini_date.month, day=1)
    month = last_date.strftime('%B')
    markup = types.InlineKeyboardMarkup(row_width=ROW_WIDTH)
    markup.row()
    buttons = []
    dir_btn = []
    if last_date.month != 12:
        dir_btn.append(create_inline_btn_for_direction(
            date(year=last_date.year, month=last_date.month + 1, day=1), 'next', action))
    else:
        dir_btn.append(create_inline_btn_for_direction(
            date(year=last_date.year + 1, month=1, day=1), 'next', action))
    dir_btn.append(types.InlineKeyboardButton(text=month, callback_data=ignore_callback))
    for pixel_fmt in pixels_sorted:
        if last_date <= pixel_fmt['date'] <= ini_date:
            btn = create_inline_btn_for_date(pixel_fmt['date'], pixel_fmt["quantity"],
                                             user.graph["unit"], action)
            buttons.append(btn)
        else:
            dir_btn.append(create_inline_btn_for_direction(last_date, 'prev', action))
            break
    buttons = buttons[::-1]
    dir_btn = dir_btn[::-1]
    for o_btn in dir_btn:
        markup.insert(o_btn)
    markup = order_buttons(buttons, markup)
    await query.message.edit_reply_markup(reply_markup=markup)


async def load_pixel_next(query: types.CallbackQuery, callback_data: dict, users: dict):
    """
    Displays dates as inline buttons for next month.
    We're using higher order function to define local storage and
    be able to use inner function for query handler in main bot script.
    :param callback_data:
    :param query:
    :param users: local storage
    :return: inner function
    """
    action = callback_data['action']
    cur_month = str_to_date(callback_data['date'])
    user = await get_user(query.from_user.id, users)
    pixels_sorted = convert_pixel_str_to_date(user.pixels)
    pixels_sorted = sorted([pix for pix in pixels_sorted if pix['date'] >= cur_month],
                           key=lambda pix: pix['date'])
    ini_date = pixels_sorted[0]['date']
    if ini_date.month != 12:
        last_date = date(year=ini_date.year, month=ini_date.month + 1, day=1)
    else:
        last_date = date(year=ini_date.year + 1, month=1, day=1)
    month = ini_date.strftime('%B')
    markup = types.InlineKeyboardMarkup(row_width=ROW_WIDTH)
    markup.row()
    buttons = []
    markup.insert(create_inline_btn_for_direction(
        date(year=ini_date.year, month=ini_date.month, day=1), 'prev', action))
    markup.insert(types.InlineKeyboardButton(text=month, callback_data=ignore_callback))
    for pixel_fmt in pixels_sorted:
        if ini_date <= pixel_fmt['date'] < last_date:
            btn = create_inline_btn_for_date(pixel_fmt['date'], pixel_fmt["quantity"],
                                             user.graph["unit"], action)
            buttons.append(btn)
        else:
            if ini_date.month != 12:
                markup.insert(create_inline_btn_for_direction(
                    date(year=ini_date.year, month=ini_date.month + 1, day=1), 'next', action))
            else:
                markup.insert(create_inline_btn_for_direction(
                    date(year=ini_date.year + 1, month=1, day=1), 'next', action))
            break
    markup = order_buttons(buttons, markup)
    await query.message.edit_reply_markup(reply_markup=markup)


def convert_pixel_str_to_date(pixels: List[Pixels]) -> List:
    """
    Turns dates in str format to date format inside pixel's dict.
    :param pixels:
    :return:
    """
    return [{'date': str_to_date(pixel['date']), 'quantity': pixel['quantity']}
            for pixel in pixels]


def create_inline_btn_for_direction(date_: date, direction: str,
                                    action: str) -> types.InlineKeyboardButton:
    """
    Creates inline button for direction towards next or previous month.
    :param date_: date to pass as callback data
    :param direction: next or prev
    :param action: edit or delete
    :return: inline button
    """
    if direction == 'next':
        return types.InlineKeyboardButton(text='>',
                                          callback_data=cb_calendar.new(date_to_str(date_),
                                                                        action, 'next'))
    elif direction == 'prev':
        return types.InlineKeyboardButton(text='<',
                                          callback_data=cb_calendar.new(date_to_str(date_),
                                                                        action, 'prev'))


def create_inline_btn_for_date(date_: date, quantity: str, unit: str,
                               action: str) -> types.InlineKeyboardButton:
    """
    Creates inline button for existing date.
    :param date_: date
    :param quantity: quantity of pixel
    :param unit: unit of graph
    :param action: edit or delete
    :return: inline button
    """
    return types.InlineKeyboardButton(text=str(date_.day) + f' - {quantity} {unit}',
                                      callback_data=cb_pixel.new(date_to_str(date_), action))


def order_buttons(buttons: List[types.InlineKeyboardButton],
                  markup: types.InlineKeyboardMarkup) -> types.InlineKeyboardMarkup:
    """
    Inserts buttons in rows in markup.
    :param buttons: list of inline buttons for available dates
    :param markup: markup with direction buttons
    :return: markup with all buttons
    """
    for i, btn in enumerate(buttons):
        if i % ROW_WIDTH == 0:
            markup.row()
        markup.insert(btn)
    return markup
