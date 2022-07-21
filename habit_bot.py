"""
Creates behaviour for telegram habit bot.
"""
from datetime import timedelta
import logging
from sys import stdout
import os
from typing import List
from functools import partial

import aiohttp
from aiohttp import web
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.executor import start_webhook
from aiogram.utils.exceptions import BotBlocked
from aiogram.utils.callback_data import CallbackData
from aiogram_calendar import simple_cal_callback, SimpleCalendar
from pixela import *
from load_pixel_calendar import *
from utils import get_user, save_user, User, create_db_user, database


TOKEN = '5381219717:AAGmW2vYBGKaqnOpH3ng3iGC_o9Bff4KvsQ'
BASE_URL = 'https://api.telegram.org/bot' + TOKEN

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=stdout)
logger.addHandler(handler)

bot = Bot(TOKEN)
dp = Dispatcher(bot)

app = web.Application()

HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')

# webhook settings
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

# webserver settings
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.getenv('PORT', default=8000)


# TODO Add webhooks
USER_CREATION_STATE = ('new user', 'user creation',)
USER_DELETION_STATE = ('deletion confirmed',)
USER_DEFAULT_STATE = ('default',)
PIXEL_ADD_STATE = ('date chosen',)
PIXEL_EDIT_STATE = ('getting quantity',)
GRAPH_CREATION_STATE = ('choosing name', 'choosing unit', 'choosing type',
                        'choosing color', 'graph confirmation')
USERS = {}
cb = CallbackData('post', 'graph', 'action')

# Commands for bot
COMMANDS = ['start', 'select', 'create', 'delete']
BOT_COMMANDS = [
    types.BotCommand('start', 'Найти или создать профиль.'),
    types.BotCommand('select', 'Вывести список таблиц.'),
    types.BotCommand('create', 'Создать новую таблицу.'),
    types.BotCommand('delete', 'Удалить профиль.'),
    # types.BotCommand('exit', 'Выход.')
]


@dp.errors_handler(exception=BotBlocked)
async def error_bot_blocked(update: types.Update, exception: BotBlocked) -> bool:
    """
    Show statement if bot was added to a blacklist.
    :param update:
    :param exception:
    :return:
    """
    logger.warning('Меня заблокировали!\nСообщение: %s\nОшибка: %s', update, exception)
    return True


def graphs_info_inline(graphs: List[dict]) -> types.InlineKeyboardMarkup:
    """
    Displays available graphics as inline buttons.
    :param graphs: graphs from user object
    """
    markup = types.InlineKeyboardMarkup()
    buttons = []
    for item in graphs:
        btn = types.InlineKeyboardButton(
            text=f'{item["name"]} в единицах {item["unit"]}.',
            callback_data=cb.new(graph=item['id'], action='list'))
        buttons.append(btn)
    markup.add(*buttons)
    return markup


def create_markup_list_graphs(graph: str) -> types.InlineKeyboardMarkup:
    """
    Creates markup for listing actions for specific graph.
    :param graph: graph id
    :return: markup
    """
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(
        text='Просмотреть',
        callback_data=cb.new(graph, 'view'))
    btn3 = types.InlineKeyboardButton(
        text='Редактировать',
        callback_data=cb.new(graph, 'edit'))
    btn2 = types.InlineKeyboardButton(
        text='Работа с точками',
        callback_data=cb.new(graph, 'pixel'))
    btn4 = types.InlineKeyboardButton(
        text='Удалить',
        callback_data=cb.new(graph, 'del_graph'))
    btn5 = types.InlineKeyboardButton(
        text='Назад',
        callback_data=cb.new(graph, 'back'))
    buttons = [btn1, btn2, btn3, btn4, btn5]
    markup.add(*buttons)
    return markup


@dp.callback_query_handler(cb.filter(action=['list']))
async def inline_graph_handler(query: types.CallbackQuery, callback_data: dict):
    """
    Displays available actions for graph as inline buttons and set chosen graph as user.graph.
    :param query:
    :param callback_data: contains graph id and action to filter by.
    """
    user = await get_user(query.from_user.id, USERS)
    user.graph = await set_graph(query.message, callback_data['graph'], user)
    markup = create_markup_list_graphs(callback_data['graph'])
    await save_user(user)
    await query.message.edit_reply_markup(reply_markup=markup)


@dp.callback_query_handler(cb.filter(action=['view']))
async def view_graph(query: types.CallbackQuery, callback_data: dict):
    """
    Displays url for given graph.
    :param query:
    :param callback_data: contains graph id and action to filter by.
    """
    graph_id = callback_data['graph']
    user = await get_user(query.from_user.id, USERS)
    logger.info('Показываем таблицу %s пользователю %d.', graph_id, user.id)
    try:
        url = await show_graph(user.session, user.pixela_name, graph_id)
        await query.message.edit_text(f'Ссылка на таблицу:\n{url}')
    except PixelaDataException as exc:
        logger.error('Произошла ошибка %s.', exc)
        await query.message.answer(f'Произошла ошибка {exc}.')


@dp.callback_query_handler(cb.filter(action=['back']))
async def back_to_list(query: types.CallbackQuery):
    """
    Returns to showing graphs.
    """
    user = await get_user(query.from_user.id, USERS)
    logger.info('Возвращаемся к таблицам пользователя %d.', user.id)
    await pixela_graphs_lookup(query.message, user)


async def pixela_graphs_lookup(message: types.Message, user: User):
    """
    Get graphs from user's pixela profile and add them to user object.
    Then call handler to display graphs.
    """
    await message.reply('Ищем ваши таблицы...')
    logger.info('Ищем таблицы пользователя %d.', user.id)
    try:
        graphs = await get_graphs(user.session, user.pixela_token, user.pixela_name)
        if len(graphs) != 0:
            markup = graphs_info_inline(graphs)
            await message.answer('Ваши таблицы:', reply_markup=markup)
        else:
            await message.answer('Таблиц не найдено.')
    except PixelaDataException as exc:
        logger.error('Произошла ошибка %s.', exc)
        await message.reply(f'Произошла ошибка {exc}.')


def create_inline_markup_pixel_action(graph: str) -> types.InlineKeyboardMarkup:
    """
    Creates inline markup for actions with pixels for given graph.
    :param graph: graph id
    :return: inline markup
    """
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(
        text='Добавить',
        callback_data=cb.new(graph, 'add'))
    btn2 = types.InlineKeyboardButton(
        text='Редактировать',
        callback_data=cb.new(graph, 'edit_pixel'))
    btn3 = types.InlineKeyboardButton(
        text='Удалить',
        callback_data=cb.new(graph, 'del_pixel'))
    btn4 = types.InlineKeyboardButton(
        text='Назад',
        callback_data=cb.new(graph, 'list'))
    buttons = [btn1, btn2, btn3, btn4]
    markup.add(*buttons)
    return markup


@dp.callback_query_handler(cb.filter(action=['pixel']))
async def inline_pixel_handler(query: types.CallbackQuery, callback_data: dict):
    """
    Displays inline keyboard for operations with pixels.
    """
    markup = create_inline_markup_pixel_action(callback_data['graph'])
    await query.message.edit_text('Выберите действие с точкой:', reply_markup=markup)


@dp.message_handler(commands=COMMANDS)
async def command_handler(message: types.Message):
    """
    Handler for bot basic commands.
    """
    user = await get_user(message.from_user.id, USERS)
    logger.info('User details: %s', user)
    if not user:
        await ask_to_create_user(message)
    elif message.text == '/start':
        if user.pixela_name:
            await message.answer(f'Здравствуйте, {user.first_name}! '
                                 f'Ваш профиль {user.pixela_name} найден.')
            await pixela_graphs_lookup(message, user)
        else:
            await message.answer(f'Здравствуйте, {user.first_name}! '
                                 f'Профиль Pixela не найден. Желаете создать?')
            user.state = USER_CREATION_STATE[0]
            await save_user(user)
    elif message.text == '/select':
        if not user.pixela_name:
            await message.answer('Сначала создайте профиль.')
        else:
            await pixela_graphs_lookup(message, user)
    elif message.text == '/create':
        if not user.pixela_name:
            await message.answer('Сначала создайте профиль.')
        else:
            await graph_creation_name(message, user)
    elif message.text == '/delete':
        if not user.pixela_name:
            await message.answer('Профиль уже удален.')
        else:
            await message.reply('Вы уверены?')
            user.state = USER_DELETION_STATE[0]
            await save_user(user)


@dp.message_handler()
async def main_handler(message: types.Message):
    """
    Main bot handler for various user states.
    """
    user = await get_user(message.from_user.id, USERS)
    logger.info('User details: %s', user)
    if not user:
        await ask_to_create_user(message)
    elif user.state == USER_CREATION_STATE[0]:
        await user_creation_agreement(message, user)
    elif user.state == USER_CREATION_STATE[1]:
        await user_name_selection(message, user)
    elif user.state == GRAPH_CREATION_STATE[0]:
        await graph_creation_unit(message, user)
    elif user.state == GRAPH_CREATION_STATE[1]:
        await graph_creation_type(message, user)
    elif user.state == GRAPH_CREATION_STATE[2]:
        await graph_creation_color(message, user)
    elif user.state == GRAPH_CREATION_STATE[3]:
        await graph_creation_confirm(message, user)
    elif user.state == GRAPH_CREATION_STATE[4]:
        await graph_creation_finish(message, user)
    elif user.state == USER_DELETION_STATE[0]:
        await user_delete_handler(message, user)
    elif user.state == PIXEL_ADD_STATE[0]:
        await pixel_quantity_selection(message, user)
    elif user.state == PIXEL_EDIT_STATE[0]:
        await edit_pixel_confirm(message, user)


# ---------------- Create user ---------------


async def ask_to_create_user(message: types.Message):
    """
    Method for creating in memory user telegram profile.
    """
    user_id = message.from_user.id
    name = message.from_user.first_name
    user = User(id=user_id, first_name=name, state=USER_DEFAULT_STATE[0])
    logger.info('User with id %d and name %s is created.', user_id, name)
    pinned = await message.answer(f'Здравствуйте, {name}! Это бот для составления диаграмм привычек.')
    await bot.pin_chat_message(message.chat.id, pinned.message_id)
    await default_message(message)
    USERS.update({user_id: user})
    await create_db_user(user)


async def user_creation_agreement(message: types.Message, user: User):
    """
    Awaits for user agreement on creating pixela profile and proceeds with it.
    """
    if message.text.lower() == 'да':
        await message.reply('Отлично!')
        await message.answer('Выберите имя для своего профиля, '
                             'допустимо использовать латинские буквы и/или цифры.')
        user.state = USER_CREATION_STATE[1]
        await save_user(user)
    elif message.text.lower() == 'нет':
        await message.reply('Воля ваша.')
        user.state = USER_DEFAULT_STATE[0]
        await default_message(message)
        await save_user(user)
    else:
        await message.reply('Не понимаю.')


async def default_message(message: types.Message):
    """
    Message with available commands for operating with bot.
    """
    await message.answer('Выберите команду:\n'
                         '/start - Начать работу с ботом.\n'
                         '/create - Создать новую таблицу.\n'
                         '/select - Просмотреть доступные таблицы.\n'
                         '/delete - Удалить профиль.\n'
                         '/exit   - Выйти.')


async def user_name_selection(message: types.Message, user: User):
    """
    Checks if user's chosen name conform with permitted pattern.
    """
    pattern = re.compile('[a-z][a-z0-9-]{1,32}')
    if pattern.match(message.text):
        await message.reply('Проверим...')
        try:
            user.session = aiohttp.ClientSession()
            token, username = await create_user(user.session, TOKEN_PIXELA, message.text.lower())
            await message.answer(f'Профиль успешно создан! Ваше имя профиля {username},'
                                 f' токен {token}.')
            logger.info('Pixela profile for user with id %d with username %s created.',
                        user.id, username)
            await default_message(message)
            user.pixela_token = token
            user.pixela_name = username
            user.state = USER_DEFAULT_STATE[0]
            await save_user(user)
        except PixelaDataException as exc:
            logger.error('Произошла ошибка %s.', exc)
            await message.reply(f'Произошла ошибка {exc}.')
            await message.answer('Попробуйте другое имя.')
    else:
        await message.reply('Введите корректное имя.')


# --------------Delete user ---------------


async def user_delete_handler(message: types.Message, user: User):
    """
    Method for processing user deletion.
    """
    if message.text.lower() == 'да':
        try:
            await delete_user(user.session, user.pixela_token, user.pixela_name)
            await message.answer('Профиль успешно удален!')
            logger.info('Pixela profile deleted for user with id %d.', user.id)
            await user.session.close()
            user.reset()
            await save_user(user)
        except PixelaDataException as exc:
            logger.error('Произошла ошибка %s.', exc)
            await message.answer(f'Произошла ошибка {exc}.')
    elif message.text.lower() == 'нет':
        await pixela_graphs_lookup(message, user)
    else:
        await message.reply('Не понимаю.')


# --------------- Create graph -----------------


async def graph_creation_name(message: types.Message, user: User):
    """
    Asks for new graph name and creates an empty template for one.
    """
    await message.answer('Создаем таблицу!')
    await message.reply('Выберите название таблицы:')
    logger.info('User with id %d creating new graph.', user.id)
    user.reset_graph()
    user.state = GRAPH_CREATION_STATE[0]
    await save_user(user)


async def graph_creation_unit(message: types.Message, user: User):
    """
    Gets graph name and asks for unit name.
    """
    if message.text:
        user.graph['name'] = message.text
        if user.editting:
            await updating_graph(message, user)
        else:
            if not user.graph['unit']:
                await message.reply('Выберите единицы измерения таблицы:')
                user.state = GRAPH_CREATION_STATE[1]
            else:
                await creation_graph_confirm(message, user)
        await save_user(user)
    else:
        await message.reply('Не понимаю.')


async def graph_creation_type(message: types.Message, user: User):
    """
    Gets graph unit name and asks for type of unit.
    """
    if message.text:
        user.graph['unit'] = message.text
        if user.editting:
            await updating_graph(message, user)
        else:
            if not user.graph['type']:
                markup = type_selection()
                await message.reply('Выберите тип единиц измерения таблицы:', reply_markup=markup)
                user.state = GRAPH_CREATION_STATE[2]
            else:
                await creation_graph_confirm(message, user)
        await save_user(user)
    else:
        await message.reply('Не понимаю.')


def type_selection() -> types.ReplyKeyboardMarkup:
    """
    Helper function for getting type of unit as keyboard buttons.
    :return: markup
    """
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    buttons = []
    for unit in 'Целые', 'Дробные':
        btn = types.KeyboardButton(unit)
        buttons.append(btn)
    markup.add(*buttons)
    return markup


async def graph_type_processing(message: types.Message, user: User, type_: str):
    """
    Helper method for checking if graph type is float or int.
    :param message:
    :param user:
    :param type_: float or int
    """
    user.graph['type'] = type_
    if user.editting:
        await updating_graph(message, user)
    else:
        if not user.graph['color']:
            markup = color_selection()
            await message.reply('Выберите цвет таблицы:', reply_markup=markup)
            user.state = GRAPH_CREATION_STATE[3]
        else:
            await creation_graph_confirm(message, user)
    await save_user(user)


async def graph_creation_color(message: types.Message, user: User):
    """
    Gets type of unit and asks for graph color.
    """
    if message.text.lower() == "целые":
        await graph_type_processing(message, user, 'int')
    elif message.text.lower() == 'дробные':
        await graph_type_processing(message, user, 'float')
    else:
        await message.reply('Не понимаю.')


def color_selection() -> types.ReplyKeyboardMarkup:
    """
    Helper function for displaying available colors as keyboard buttons.
    :return: markup
    """
    markup = types.ReplyKeyboardMarkup(row_width=3, one_time_keyboard=True)
    buttons = []
    for color in Color:
        btn = types.KeyboardButton(color.value)
        buttons.append(btn)
    markup.add(*buttons)
    return markup


async def graph_creation_confirm(message: types.Message, user: User):
    """
    Gets graph color and proceeds to confirming graph creation.
    """
    if message.text in [e.value for e in Color]:
        user.graph['color'] = Color(message.text).name
    else:
        user.graph['color'] = None
    if user.graph["color"]:
        if user.editting:
            await updating_graph(message, user)
        else:
            await creation_graph_confirm(message, user)
        await save_user(user)
    else:
        await message.reply('Не понимаю.')


async def creation_graph_confirm(message: types.Message, user: User):
    """
    Asks if graph was setted correctly or user wants to change anything.
    """
    await message.answer(f'Создаем таблицу с именем {user.graph["name"]} '
                         f'в единицах {user.graph["unit"]} и с цветом {Color[user.graph["color"]].value}. '
                         f'Все верно?')
    user.state = GRAPH_CREATION_STATE[4]
    await save_user(user)


async def graph_creation_finish(message: types.Message, user: User):
    """
    Creates graph.
    """
    if message.text.lower() == 'да':
        await message.reply('Создаем таблицу...')
        try:
            # Pop id to be able to unpack user.graph
            user.graph.pop('id')
            id = await create_graph(
                 user.session,
                 user.pixela_token,
                 user.pixela_name,
                 **user.graph)
            user.graph['id'] = id
            await message.answer(f'Успешно создана таблица с id {id}!')
            logger.info('Created graph with id %s for user with id %d.', id, user.id)
            user.state = USER_DEFAULT_STATE[0]
            user.reset_graph()
            await save_user(user)
            await default_message(message)
        except PixelaDataException as exc:
            logger.error('Произошла ошибка %s.', exc)
            await message.reply(f'Произошла ошибка {exc}.')
        finally:
            if not user.graph.get('id'):
                user.graph['id'] = None
    elif message.text.lower() == 'нет':
        markup = await edit_graph_inline(None)
        await message.reply('Выберите что изменить:', reply_markup=markup)
    else:
        await message.reply('Не понимаю.')


# ------------- Edit graph ------------------


async def updating_graph(message: types.Message, user: User):
    """
    Updates graph with new parameters.
    """
    try:
        id = await update_graph(user.session, user.pixela_token, user.pixela_name, **user.graph)
        if user.graph['id'] == id:
            await message.answer('Таблица успешно обновлена!')
            logger.info('Таблица с id %s пользователя с id %d обновлена.', id, user.id)
        else:
            await message.answer('Произошла внутренняя ошибка, просим прощения. '
                                 'Попробуйте еще раз чуть позже.')
            logger.error('Ошибка в обновлении таблицы. Исходный id %d не совпадает с id %d, полученным от API.',
                         user.graph['id'], id)
        user.editting = False
        user.state = USER_DEFAULT_STATE[0]
        user.reset_graph()
        await save_user(user)
        await default_message(message)
    except PixelaDataException as exc:
        logger.error('Произошла ошибка %s.', exc)
        await message.reply(f'Произошла ошибка {exc}.')


async def edit_graph_inline(graph: Optional[str]) -> types.InlineKeyboardMarkup:
    """
    Helper function for displaying options for editing graph as inline buttons.
    :param graph:
    :return: markup with buttons
    """
    markup = types.InlineKeyboardMarkup()
    buttons = []
    if not graph:
        graph = 'null'
    for item, c_back in (
            ('Имя', cb.new(graph=graph, action='edit_name')),
            ("Ед. Изм.", cb.new(graph=graph, action='edit_unit')),
            ("Тип единиц", cb.new(graph=graph, action='edit_type')),
            ("Цвет", cb.new(graph=graph, action='edit_color'))):
        btn = types.InlineKeyboardButton(text=item, callback_data=c_back)
        buttons.append(btn)
    if graph != 'null':
        buttons.append(types.InlineKeyboardButton(text="Назад", callback_data=cb.new(graph=graph, action='list')))
    markup.add(*buttons)
    return markup


@dp.callback_query_handler(cb.filter(action=['edit']))
async def edit_handler(query: types.CallbackQuery, callback_data: dict):
    """
    Process inline button for editing graph.
    """
    graph = callback_data['graph']
    markup = await edit_graph_inline(graph)
    await query.message.edit_text('Редактировать:', reply_markup=markup)


async def set_graph(message: types.Message, graph_id: str, user: User):
    """
    Helper function to set graph for updating/viewing.
    """
    try:
        return await get_graph(user.session, user.pixela_token, user.pixela_name, graph_id)
    except PixelaDataException as exc:
        logger.error('Произошла ошибка %s.', exc)
        await message.reply(f'Произошла ошибка {exc}.')


@dp.callback_query_handler(cb.filter(action=['edit_name']))
async def edit_name_handler(query: types.CallbackQuery, callback_data: dict):
    """
    Asks for new name of graph.
    """
    graph = callback_data['graph']
    user = await get_user(query.from_user.id, USERS)
    await query.message.edit_text('Выберите новое имя:')
    if graph != 'null':
        user.editting = True
    user.state = GRAPH_CREATION_STATE[0]
    await save_user(user)


@dp.callback_query_handler(cb.filter(action=['edit_unit']))
async def edit_unit_handler(query: types.CallbackQuery, callback_data: dict):
    """
    Asks for new unit name for graph.
    """
    graph = callback_data['graph']
    user = await get_user(query.from_user.id, USERS)
    await query.message.edit_text('Выберите новые единицы измерения:')
    if graph != 'null':
        user.editting = True
    user.state = GRAPH_CREATION_STATE[1]
    await save_user(user)


@dp.callback_query_handler(cb.filter(action=['edit_type']))
async def edit_type_handler(query: types.CallbackQuery, callback_data: dict):
    """
    Asks for new unit type for graph. Action is permitted only if there are none
    already existing pixels in current graph.
    """
    graph = callback_data['graph']
    user = await get_user(query.from_user.id, USERS)
    try:
        pixels = await get_pixels(user.session, user.pixela_token, user.pixela_name, graph)
        if pixels == []:
            markup = type_selection()
            await query.message.reply('Выберите тип единиц измерения таблицы:', reply_markup=markup)
            if graph != 'null':
                user.editting = True
            user.state = GRAPH_CREATION_STATE[2]
            await save_user(user)
        else:
            await query.message.answer('Невозможно поменять тип единиц в таблице с уже существующими точками.')
    except PixelaDataException as exc:
        logger.error('Произошла ошибка %s.', exc)
        await query.message.answer(f'Произошла ошибка {exc}.')


@dp.callback_query_handler(cb.filter(action=['edit_color']))
async def edit_color_handler(query: types.CallbackQuery, callback_data: dict):
    """
    Asks for new color for graph.
    """
    graph = callback_data['graph']
    user = await get_user(query.from_user.id, USERS)
    markup = color_selection()
    await query.message.reply('Выберите цвет таблицы:', reply_markup=markup)
    if graph != 'null':
        user.editting = True
    user.state = GRAPH_CREATION_STATE[3]
    await save_user(user)


# ------------ Delete graph ---------------


def create_markup_for_graph_delete(graph: str) -> types.InlineKeyboardMarkup:
    """
    Creates markup with buttons 'yes' and 'no' to confirm graph deletion.
    """
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(
        text='Да',
        callback_data=cb.new(graph, 'del_graph_confirm'))
    btn2 = types.InlineKeyboardButton(
        text='Нет',
        callback_data=cb.new(graph, 'list'))
    buttons = [btn1, btn2]
    markup.add(*buttons)
    return markup


@dp.callback_query_handler(cb.filter(action=['del_graph']))
async def delete_graph_ask_confirm(query: types.CallbackQuery, callback_data: dict):
    """
    Helper function to ask confirmation for deletion of the graph as keyboard buttons.
    """
    markup = create_markup_for_graph_delete(callback_data['graph'])
    await query.message.edit_text('Вы уверены?', reply_markup=markup)


@dp.callback_query_handler(cb.filter(action=['del_graph_confirm']))
async def delete_graph_confirm(query: types.CallbackQuery, callback_data: dict):
    """
    Processes graph deletion.
    """
    graph = callback_data['graph']
    user = await get_user(query.from_user.id, USERS)
    await query.message.edit_text('Удаляем таблицу...')
    try:
        await delete_graph(user.session, user.pixela_token, user.pixela_name, graph)
        await query.message.answer('Таблица успешно удалена!')
        logger.info('Таблица с id %s пользователя с id %d удалена.', graph, user.id)
        user.state = USER_DEFAULT_STATE[0]
        user.reset_graph()
        await save_user(user)
        await default_message(query.message)
    except PixelaDataException as exc:
        logger.error('Произошла ошибка %s.', exc)
        await query.message.answer(f'Произошла ошибка {exc}.')


# -------------Post pixel ------------

def create_markup_add_pixel(graph: str) -> types.InlineKeyboardMarkup:
    """
    Create inline markup for adding pixels to given graph.
    :param graph: graph id
    :return: markup
    """
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(
        text='Сегодня',
        callback_data=cb.new(graph, 'add_today'))
    btn2 = types.InlineKeyboardButton(
        text='Вчера',
        callback_data=cb.new(graph, 'add_yest'))
    btn3 = types.InlineKeyboardButton(
        text='Другой день',
        callback_data=cb.new(graph, 'add_other'))
    buttons = [btn1, btn2, btn3]
    markup.add(*buttons)
    return markup


@dp.callback_query_handler(cb.filter(action=['add']))
async def add_pixel_handler(query: types.CallbackQuery, callback_data: dict):
    """
    Processes inline button for adding pixel, asks for date of pixel.
    """
    markup = create_markup_add_pixel(callback_data['graph'])
    await query.message.edit_text('Выберите дату для добавления точки:', reply_markup=markup)


@dp.callback_query_handler(cb.filter(action=['add_today', 'add_yest']))
async def add_pixel_date_simple(query: types.CallbackQuery, callback_data: dict):
    """
    Processes pixel date for today and yesterday.
    """
    if callback_data['action'] == 'add_today':
        await add_pixel_process_date(query.message, query.from_user.id, datetime.today())
    else:
        await add_pixel_process_date(query.message, query.from_user.id,
                                     datetime.today() - timedelta(days=1))


@dp.callback_query_handler(cb.filter(action=['add_other']))
async def add_pixel_date_other(query: types.CallbackQuery, callback_data: dict):
    """
    Calls external calendar for choosing pixel date other than today and yesterday.
    """
    await query.message.edit_text('Выберите дату для добавления точки:',
                                  reply_markup=await SimpleCalendar().start_calendar())


async def add_pixel_process_date(message: types.Message, user_id: int, date_: datetime):
    """
    Processes chosen date, saves it in user object and asks for quantity.
    """
    user = await get_user(user_id, USERS)
    date_str = date_to_str(date_)
    user.pixel['date'] = date_str
    await message.edit_text(f'Вы выбрали {date_.strftime("%d/%m/%Y")}.')
    await message.answer(f'Выберите количество {user.graph["unit"]}:')
    user.state = PIXEL_ADD_STATE[0]
    await save_user(user)


async def pixel_post_type(message: types.Message, user: User, type_: str):
    """
    Checks pixel data type and creates pixel.
    """
    if user.graph['type'] == type_:
        try:
            await post_pixel(user.session, user.pixela_token, user.pixela_name, user.graph['id'],
                       user.pixel['date'], user.pixel['quantity'])
            await message.answer('Точка успешно добавлена!')
            logger.info('Добавлена точка с датой %s на график с id %s для пользователя с id %d.',
                        user.pixel['date'], user.graph['id'], user.id)
            user.state = USER_DEFAULT_STATE[0]
            user.reset_pixel()
            user.reset_graph()
            await save_user(user)
            await default_message(message)
        except PixelaDataException as exc:
            logger.error('Произошла ошибка %s.', exc)
            await message.answer(f'Произошла ошибка {exc}.')
    else:
        await message.reply(f'Выберите верный тип данных {user.graph["type"]}.')


async def pixel_quantity_selection(message: types.Message, user: User):
    """
    Gets pixel quantity and checks its type.
    """
    try:
        quantity = int(message.text)
        user.pixel['quantity'] = quantity
        await pixel_post_type(message, user, 'int')
    except ValueError:
        try:
            quantity = float(message.text)
            user.pixel['quantity'] = quantity
            await pixel_post_type(message, user, 'float')
        except ValueError:
            await message.reply('Не понимаю.')


@dp.callback_query_handler(simple_cal_callback.filter())
async def process_simple_calendar(query: types.CallbackQuery, callback_data: CallbackData):
    """
    Helper function to process external calendar.
    """
    selected, date_ = await SimpleCalendar().process_selection(query, callback_data)
    if selected:
        await add_pixel_process_date(query.message, query.from_user.id, date_)


# ----------- Edit pixel --------------------


@dp.callback_query_handler(cb.filter(action='edit_pixel'))
async def edit_pixel(query: types.CallbackQuery, callback_data: dict):
    """
    Allows to choose active pixel to edit.
    """
    graph = callback_data['graph']
    user = await get_user(query.from_user.id, USERS)
    try:
        pixels = await get_pixels(user.session, user.pixela_token, user.pixela_name, graph)
        user.pixels = pixels
        markup = await load_pixels(pixels, user, action='edit')
        if not markup:
            await query.message.edit_text('Нет доступных точек.')
        else:
            await query.message.edit_text('Выберите точку для изменения:', reply_markup=markup)
        await save_user(user)
    except PixelaDataException as exc:
        logger.error('Произошла ошибка %s.', exc)
        await query.message.answer(f'Произошла ошибка {exc}.')


@dp.callback_query_handler(cb_pixel.filter(action='edit'))
async def pixel_edit_ask_quantity(query: types.CallbackQuery, callback_data: dict):
    """
    Gets pixel date for editing, asks for new quantity.
    """
    pixel = callback_data['pixel']
    user = await get_user(query.from_user.id, USERS)
    user.pixel['date'] = pixel
    user.state = PIXEL_EDIT_STATE[0]
    await save_user(user)
    await query.message.answer('Выберите новое значение точки:')


async def edit_pixel_helper(message: types.Message, user: User,
                            type_: str, quantity: Union[int, float]):
    """
    Updates pixel.
    """
    if user.graph['type'] == type_:
        try:
            await update_pixel(user.session, user.pixela_token, user.pixela_name,
                         user.graph['id'], user.pixel['date'], quantity)
            await message.answer('Точка успешно обновлена!')
            user.state = USER_DEFAULT_STATE[0]
            logger.info('Точка с датой %s таблицы с id %s пользователя с id %d обновлена.',
                        user.pixel['date'], user.graph['id'], user.id)
            user.reset_pixel()
            user.reset_graph()
            await save_user(user)
            await default_message(message)
        except PixelaDataException as exc:
            logger.error('Произошла ошибка %s.', exc)
            await message.answer(f'Произошла ошибка {exc}.')
    else:
        await message.reply(f'Выберите верный тип данных {user.graph["type"]}.')


async def edit_pixel_confirm(message: types.Message, user: User):
    """
    Prepares pixel for update depending on pixel's data type.
    """
    try:
        quantity = int(message.text)
        await edit_pixel_helper(message, user, 'int', quantity)
    except ValueError:
        try:
            quantity = float(message.text)
            await edit_pixel_helper(message, user, 'float', quantity)
        except ValueError:
            await message.reply('Не понимаю.')


# ------------- Delete pixel -------------


@dp.callback_query_handler(cb.filter(action='del_pixel'))
async def del_pixel(query: types.CallbackQuery, callback_data: dict):
    """
    Gets list of available pixels to prepare for deletion.
    """
    graph = callback_data['graph']
    user = await get_user(query.from_user.id, USERS)
    try:
        pixels = await get_pixels(user.session, user.pixela_token, user.pixela_name, graph)
        user.pixels = pixels
        markup = await load_pixels(pixels, user, action='delete')
        if not markup:
            await query.message.edit_text('Нет доступных точек.')
        else:
            await query.message.edit_text('Выберите точку для удаления:', reply_markup=markup)
        await save_user(user)
    except PixelaDataException as exc:
        logger.error('Произошла ошибка %s.', exc)
        await query.message.answer(f'Произошла ошибка {exc}.')


@dp.callback_query_handler(cb_pixel.filter(action='delete'))
async def pixel_delete_confirm(query: types.CallbackQuery, callback_data: dict):
    """
    Deletes chosen pixel.
    """
    pixel = callback_data['pixel']
    user = await get_user(query.from_user.id, USERS)
    try:
        await delete_pixel(user.session, user.pixela_token, user.pixela_name, user.graph['id'], pixel)
        await query.message.answer('Точка успешно удалена!')
        logger.info('Точка с датой %s таблицы с id %s пользователя с id %d удалена.',
                    pixel, user.graph['id'], user.id)
        user.state = USER_DEFAULT_STATE[0]
        user.reset_pixel()
        user.reset_graph()
        await save_user(user)
        await default_message(query.message)
    except PixelaDataException as exc:
        logger.error('Произошла ошибка %s.', exc)
        await query.message.answer(f'Произошла ошибка {exc}.')


async def on_startup(dispatcher):
    """
    Function on bot startup.
    :param dispatcher:
    :return:
    """
    # loop = asyncio.get_running_loop()
    # web.run_app(app, loop=loop, host=WEBAPP_HOST, port=WEBAPP_PORT)
    # runner = aiohttp.web.AppRunner(app)
    # await runner.setup()
    # site = aiohttp.web.TCPSite(runner, host=WEBAPP_HOST, port=WEBAPP_PORT)
    # await site.start()
    # print('server running')
    # await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    await bot.set_my_commands(BOT_COMMANDS)
    menu_button = types.MenuButtonCommands()
    await bot.set_chat_menu_button(menu_button=menu_button)
    await database.connect()


async def on_shutdown(dispatcher):
    """
    Function upon shutting bot down.
    :param dispatcher:
    :return:
    """
    await database.close()
    for user in USERS.values():
        if user.session:
            await user.session.close()
    # await bot.delete_webhook()


if __name__ == '__main__':
    dp.register_callback_query_handler(partial(load_pixel_prev, users=USERS),
                                       cb_calendar.filter(direction='prev'))
    dp.register_callback_query_handler(partial(load_pixel_next, users=USERS),
                                       cb_calendar.filter(direction='next'))
    executor.start_polling(dp, skip_updates=True,
                           on_startup=on_startup, on_shutdown=on_shutdown)
    # start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH, skip_updates=True,
    #               on_startup=on_startup, on_shutdown=on_shutdown,
    #               host=WEBAPP_HOST, port=WEBAPP_PORT)
