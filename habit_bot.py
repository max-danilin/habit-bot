from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import BotBlocked
from aiogram.utils.callback_data import CallbackData
from aiogram_calendar import simple_cal_callback, SimpleCalendar
from utils import *
from pixela import *
from datetime import datetime, timedelta, date
import json


token = '5381219717:AAGmW2vYBGKaqnOpH3ng3iGC_o9Bff4KvsQ'
base_url = 'https://api.telegram.org/bot' + token

bot = Bot(token)
dp = Dispatcher(bot)

# TODO implement bot behaviour
# TODO Test get_pixels endpoint
USER_CREATION_STATE = ('new user', 'user creation', 'user done')
USER_DELETION_STATE = ('deletion confirmed',)
PIXEL_ADD_STATE = ('date chosen',)
PIXEL_EDIT_STATE = ('getting quantity',)
GRAPH_CREATION_STATE = ('choosing name', 'choosing unit', 'choosing type', 'choosing color', 'graph confirmation')
USERS = dict()
COMMANDS = ['start', 'select', 'create', 'delete']
cb = CallbackData('post', 'graph', 'action')
cb_calendar = CallbackData('calendar', 'date', 'action', 'direction')
cb_pixel = CallbackData('pixels', 'pixel', 'action')
ignore_callback = cb_calendar.new('', '', 'ignore')


@dp.errors_handler(exception=BotBlocked)
async def error_bot_blocked(update: types.Update, exception: BotBlocked):
    print(f'Меня заблокировали!\nСообщение: {update}\nОшибка: {exception}')
    return True


async def tables_inline(message: types.Message, graphs: List[dict]):
    if len(graphs) != 0:
        markup = types.InlineKeyboardMarkup()
        buttons = []
        for item in graphs:
            btn = types.InlineKeyboardButton(
                text=f'Таблица {item["name"]} в единицах {item["unit"]}.',
                callback_data=cb.new(graph=item['id'], action='list'))
            buttons.append(btn)
        markup.add(*buttons)
        await message.answer('Ваши таблицы:', reply_markup=markup)
    else:
        await message.answer('Таблиц не найдено.')


async def edit_graph_inline(graph: Optional[str]) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    buttons = []
    for item, cback in (
            ('Имя', cb.new(graph=graph, action='edit_name')),
            ("Ед. Изм.", cb.new(graph=graph, action='edit_unit')),
            ("Тип единиц", cb.new(graph=graph, action='edit_type')),
            ("Цвет", cb.new(graph=graph, action='edit_color')),
            ("Назад", cb.new(graph=graph, action='list'))):
        btn = types.InlineKeyboardButton(text=item, callback_data=cback)
        buttons.append(btn)
    markup.add(*buttons)
    return markup


@dp.callback_query_handler(cb.filter(action=['list']))
async def inline_list_handler(query: types.CallbackQuery, callback_data: dict):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(
        text='Просмотреть',
        callback_data=cb.new(callback_data['graph'], 'view'))
    btn3 = types.InlineKeyboardButton(
        text='Редактировать',
        callback_data=cb.new(callback_data['graph'], 'edit'))
    btn2 = types.InlineKeyboardButton(
        text='Работа с точками',
        callback_data=cb.new(callback_data['graph'], 'pixel'))
    btn4 = types.InlineKeyboardButton(
        text='Удалить',
        callback_data=cb.new(callback_data['graph'], 'del_graph'))
    btn5 = types.InlineKeyboardButton(
        text='Назад',
        callback_data=cb.new(callback_data['graph'], 'back'))
    buttons = [btn1, btn2, btn3, btn4, btn5]
    markup.add(*buttons)
    await query.message.edit_reply_markup(reply_markup=markup)


@dp.callback_query_handler(cb.filter(action=['view']))
async def view_graph(query: types.CallbackQuery, callback_data: dict):
    graph_id = callback_data['graph']
    user = get_user(query.from_user.id, USERS)
    try:
        url = show_graph(user.pixela_name, graph_id)
        await query.message.edit_text(f'Ссылка на таблицу:\n{url}')
    except PixelaDataException as exc:
        await query.message.answer(f'Произошла ошибка {exc}.')


@dp.callback_query_handler(cb.filter(action=['back']))
async def back_to_list(query: types.CallbackQuery):
    user = get_user(query.from_user.id, USERS)
    await pixela_tables_lookup(query.message, user)


@dp.callback_query_handler(cb.filter(action=['edit']))
async def edit_handler(query: types.CallbackQuery, callback_data: dict):
    graph = callback_data['graph']
    markup = await edit_graph_inline(graph)
    await query.message.edit_text('Редактировать:', reply_markup=markup)


@dp.callback_query_handler(cb.filter(action=['edit_name']))
async def edit_name_handler(query: types.CallbackQuery, callback_data: dict):
    graph = callback_data['graph']
    user = get_user(query.from_user.id, USERS)
    await query.message.edit_text('Выберите новое имя:')
    if graph:
        user.set_graph(graph)
        user.editting = True
    user.state = GRAPH_CREATION_STATE[0]
    save_user(user.id)


@dp.callback_query_handler(cb.filter(action=['edit_unit']))
async def edit_unit_handler(query: types.CallbackQuery, callback_data: dict):
    graph = callback_data['graph']
    user = get_user(query.from_user.id, USERS)
    await query.message.edit_text('Выберите новые единицы измерения:')
    if graph:
        user.set_graph(graph)
        user.editting = True
    user.state = GRAPH_CREATION_STATE[1]
    save_user(user.id)


@dp.callback_query_handler(cb.filter(action=['edit_type']))
async def edit_type_handler(query: types.CallbackQuery, callback_data: dict):
    graph = callback_data['graph']
    user = get_user(query.from_user.id, USERS)
    await type_selection(query.message)
    if graph:
        user.set_graph(graph)
        user.editting = True
    user.state = GRAPH_CREATION_STATE[2]
    save_user(user.id)


@dp.callback_query_handler(cb.filter(action=['edit_color']))
async def edit_color_handler(query: types.CallbackQuery, callback_data: dict):
    graph = callback_data['graph']
    user = get_user(query.from_user.id, USERS)
    await color_selection(query.message)
    if graph:
        user.set_graph(graph)
        user.editting = True
    user.state = GRAPH_CREATION_STATE[3]
    save_user(user.id)


@dp.callback_query_handler(cb.filter(action=['pixel']))
async def inline_list_handler(query: types.CallbackQuery, callback_data: dict):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(
        text='Добавить',
        callback_data=cb.new(callback_data['graph'], 'add'))
    btn2 = types.InlineKeyboardButton(
        text='Редактировать',
        callback_data=cb.new(callback_data['graph'], 'edit_pixel'))
    btn3 = types.InlineKeyboardButton(
        text='Удалить',
        callback_data=cb.new(callback_data['graph'], 'del_pixel'))
    btn4 = types.InlineKeyboardButton(
        text='Назад',
        callback_data=cb.new(callback_data['graph'], 'list'))
    buttons = [btn1, btn2, btn3, btn4]
    markup.add(*buttons)
    await query.message.edit_text(text='Выберите действие с точкой:', reply_markup=markup)


@dp.callback_query_handler(cb.filter(action=['add']))
async def add_pixel_handler(query: types.CallbackQuery, callback_data: dict):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(
        text='Сегодня',
        callback_data=cb.new(callback_data['graph'], 'add_today'))
    btn2 = types.InlineKeyboardButton(
        text='Вчера',
        callback_data=cb.new(callback_data['graph'], 'add_yest'))
    btn3 = types.InlineKeyboardButton(
        text='Другой день',
        callback_data=cb.new(callback_data['graph'], 'add_other'))
    buttons = [btn1, btn2, btn3]
    markup.add(*buttons)
    await query.message.edit_text('Выберите дату для добавления точки:', reply_markup=markup)


@dp.callback_query_handler(cb.filter(action=['add_today', 'add_yest']))
async def add_pixel_date_simple(query: types.CallbackQuery, callback_data: dict):
    if callback_data['action'] == 'add_today':
        await add_pixel_process_date(query.message, query.from_user.id, datetime.today())
    else:
        await add_pixel_process_date(query.message, query.from_user.id, datetime.today() - timedelta(days=1))


@dp.callback_query_handler(cb.filter(action=['add_other']))
async def add_pixel_date_other(query: types.CallbackQuery):
    await query.message.edit_text('Выберите дату для добавления точки:',
                                  reply_markup=await SimpleCalendar().start_calendar())


async def add_pixel_process_date(message: types.Message, user_id: int, date: datetime):
    user = get_user(user_id, USERS)
    user.pixel['date'] = date
    await message.edit_text(f'Вы выбрали {date.strftime("%d/%m/%Y")}.')
    await message.answer(f'Выберите количество {user.graph["unit"]}:')
    user.state = PIXEL_ADD_STATE[0]
    save_user(user.id)


@dp.callback_query_handler(simple_cal_callback.filter())
async def process_simple_calendar(query: types.CallbackQuery, callback_data: dict):
    selected, date = await SimpleCalendar().process_selection(query, callback_data)
    if selected:
        await add_pixel_process_date(query.message, query.from_user.id, date)


async def load_pixels(pixels: List, user: User, action: str) -> Optional[types.InlineKeyboardMarkup]:
    if len(pixels) > 0:
        pixels_sorted = sorted(pixels, key=lambda pix: pix['date'], reverse=True)
        ini_date = pixels_sorted[0]['date']
        last_date = date(year=ini_date.year, month=ini_date.month, day=1)
        month = last_date.strftime('%B')
        markup = types.InlineKeyboardMarkup(row_width=4)
        markup.row()
        buttons = list()
        for pp in pixels_sorted:
            if last_date <= pp['date'] <= ini_date:
                btn = types.InlineKeyboardButton(text=str(pp['date'].day)+f' - {pp["quantity"]} {user.graph["unit"]}',
                                                 callback_data=cb_pixel.new(pp["date"].strftime("%Y%m%d"), action))
                buttons.append(btn)
            else:
                markup.insert(types.InlineKeyboardButton(
                    text='<',
                    callback_data=cb_calendar.new(last_date.strftime("%Y%m%d"), action, 'prev')))
                break
        markup.insert(types.InlineKeyboardButton(text=month, callback_data=ignore_callback))
        buttons = buttons[::-1]
        for i, bt in enumerate(buttons):
            if i % 4 == 0:
                markup.row()
            markup.insert(bt)
        return markup
    else:
        return None


@dp.callback_query_handler(cb_calendar.filter(direction='prev'))
async def load_pixel_prev(query: types.CallbackQuery, callback_data: dict):
    action = callback_data['action']
    cur_month = datetime.strptime(callback_data['date'], "%Y%m%d").date()
    user = get_user(query.from_user.id, USERS)
    pixels_sorted = sorted(user.pixels, key=lambda pix: pix['date'], reverse=True)
    pixels_sorted = [pix for pix in pixels_sorted if pix['date'] < cur_month]
    ini_date = pixels_sorted[0]['date']
    last_date = date(year=ini_date.year, month=ini_date.month, day=1)
    month = last_date.strftime('%B')
    markup = types.InlineKeyboardMarkup(row_width=4)
    markup.row()
    buttons = list()
    order_btn = list()
    if last_date.month != 12:
        order_btn.append(types.InlineKeyboardButton(
            text='>',
            callback_data=cb_calendar.new(date(year=last_date.year, month=last_date.month+1, day=1).strftime("%Y%m%d"),
                                          action, 'next')))
    else:
        order_btn.append(types.InlineKeyboardButton(
            text='>',
            callback_data=cb_calendar.new(
                date(year=last_date.year+1, month=1, day=1).strftime("%Y%m%d"), action, 'next')))
    order_btn.append(types.InlineKeyboardButton(text=month, callback_data=ignore_callback))
    for pp in pixels_sorted:
        if last_date <= pp['date'] <= ini_date:
            btn = types.InlineKeyboardButton(text=str(pp['date'].day) + f' - {pp["quantity"]} {user.graph["unit"]}',
                                             callback_data=cb_pixel.new(pp["date"].strftime("%Y%m%d"), action))
            buttons.append(btn)
        else:
            order_btn.append(types.InlineKeyboardButton(
                text='<',
                callback_data=cb_calendar.new(last_date.strftime("%Y%m%d"), action, 'prev')))
            break
    buttons = buttons[::-1]
    order_btn = order_btn[::-1]
    for obtn in order_btn:
        markup.insert(obtn)
    for i, bt in enumerate(buttons):
        if i % 4 == 0:
            markup.row()
        markup.insert(bt)
    await query.message.edit_reply_markup(reply_markup=markup)


@dp.callback_query_handler(cb_calendar.filter(action='next'))
async def load_pixel_next(query: types.CallbackQuery, callback_data: dict):
    action = callback_data['action']
    cur_month = datetime.strptime(callback_data['date'], "%Y%m%d").date()
    user = get_user(query.from_user.id, USERS)
    pixels_sorted = sorted(user.pixels, key=lambda pix: pix['date'])
    pixels_sorted = [pix for pix in pixels_sorted if pix['date'] > cur_month]
    ini_date = pixels_sorted[0]['date']
    if ini_date.month != 12:
        last_date = date(year=ini_date.year, month=ini_date.month+1, day=1)
    else:
        last_date = date(year=ini_date.year+1, month=1, day=1)
    month = ini_date.strftime('%B')
    markup = types.InlineKeyboardMarkup(row_width=4)
    markup.row()
    buttons = list()
    markup.insert(types.InlineKeyboardButton(
        text='<',
        callback_data=cb_calendar.new(date(year=ini_date.year, month=ini_date.month, day=1).strftime("%Y%m%d"),
                                      action, 'prev')))
    markup.insert(types.InlineKeyboardButton(text=month, callback_data=ignore_callback))
    for pp in pixels_sorted:
        if ini_date <= pp['date'] < last_date:
            btn = types.InlineKeyboardButton(text=str(pp['date'].day) + f' - {pp["quantity"]} {user.graph["unit"]}',
                                             callback_data=cb_pixel.new(pp["date"].strftime("%Y%m%d"), action))
            buttons.append(btn)
        else:
            if ini_date.month != 12:
                markup.insert(types.InlineKeyboardButton(
                    text='>',
                    callback_data=cb_calendar.new(
                        date(year=ini_date.year, month=ini_date.month + 1, day=1).strftime("%Y%m%d"), action, 'next')))
            else:
                markup.insert(types.InlineKeyboardButton(
                    text='>',
                    callback_data=cb_calendar.new(
                        date(year=ini_date.year + 1, month=1, day=1).strftime("%Y%m%d"), action, 'next')))
            break
    for i, bt in enumerate(buttons):
        if i % 4 == 0:
            markup.row()
        markup.insert(bt)
    await query.message.edit_reply_markup(reply_markup=markup)


@dp.callback_query_handler(cb.filter(action='edit_pixel'))
async def edit_pixel(query: types.CallbackQuery, callback_data: dict):
    graph = callback_data['graph']
    user = get_user(query.from_user.id, USERS)
    try:
        pixels = get_pixels(user.pixela_token, user.pixela_name, graph)
        for pixel in pixels:
            pixel['date'] = datetime.strptime(pixel['date'], "%Y%m%d").date()
        user.pixels = pixels
        markup = await load_pixels(pixels, user, action='edit')
        await query.message.edit_text(text='Выберите точку для изменения:', reply_markup=markup)
        save_user(user.id)
    except PixelaDataException as exc:
        await query.message.answer(f'Произошла ошибка {exc}.')


@dp.callback_query_handler(cb.filter(action='del_pixel'))
async def del_pixel(query: types.CallbackQuery, callback_data: dict):
    graph = callback_data['graph']
    user = get_user(query.from_user.id, USERS)
    try:
        pixels = get_pixels(user.pixela_token, user.pixela_name, graph)
        for pixel in pixels:
            pixel['date'] = datetime.strptime(pixel['date'], "%Y%m%d").date()
        user.pixels = pixels
        markup = await load_pixels(pixels, user, action='delete')
        await query.message.edit_text(text='Выберите точку для удаления:', reply_markup=markup)
        save_user(user.id)
    except PixelaDataException as exc:
        await query.message.answer(f'Произошла ошибка {exc}.')


@dp.callback_query_handler(cb_pixel.filter(action='edit'))
async def pixel_edit_ask_quantity(query: types.CallbackQuery, callback_data: dict):
    pixel = callback_data['pixel']
    user = get_user(query.from_user.id, USERS)
    user.pixel_date = pixel
    user.state = PIXEL_EDIT_STATE[0]
    save_user(user.id)
    await query.message.answer('Выберите новое значение точки:')


@dp.callback_query_handler(cb_pixel.filter(action='delete'))
async def pixel_delete_confirm(query: types.CallbackQuery, callback_data: dict):
    pixel = callback_data['pixel']
    user = get_user(query.from_user.id, USERS)
    try:
        delete_pixel(user.pixela_token, user.pixela_name, user.graph['id'], pixel)
        await query.message.answer('Точка успешно обновлена!')
    except PixelaDataException as exc:
        await query.message.answer(f'Произошла ошибка {exc}.')


@dp.callback_query_handler(cb.filter(action=['del_graph']))
async def delete_graph_ask_confirm(query: types.CallbackQuery, callback_data: dict):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(
        text='Да',
        callback_data=cb.new(callback_data['graph'], 'del_graph_confirm'))
    btn2 = types.InlineKeyboardButton(
        text='Нет',
        callback_data=cb.new(callback_data['graph'], 'list'))
    buttons = [btn1, btn2]
    markup.add(*buttons)
    await query.message.edit_text('Вы уверены?', reply_markup=markup)


@dp.callback_query_handler(cb.filter(action=['del_graph_confirm']))
async def delete_graph_confirmr(query: types.CallbackQuery, callback_data: dict):
    graph = callback_data['graph']
    user = get_user(query.from_user.id, USERS)
    await query.message.edit_text('Удаляем график...')
    try:
        delete_graph(user.pixela_token, user.pixela_name, graph)
        await query.message.answer('Таблица успешно удалена!')
    except PixelaDataException as exc:
        await query.message.answer(f'Произошла ошибка {exc}.')


@dp.message_handler(commands=COMMANDS)
async def command_handler(message: types.Message):
    user = get_user(message.from_user.id, USERS)
    if not user:
        user = await ask_to_create_user(message)
    if message.text == '/start':
        await message.answer(f'Здравствуйте, {user.first_name}! Ваш профиль {user.pixela_name} найден.')
        await pixela_tables_lookup(message, user)
    elif message.text == '/select':
        await pixela_tables_lookup(message, user)
    elif message.text == '/create':
        await graph_creation_name(message, user)
    elif message.text == '/delete':
        await message.reply('Вы уверены?')
        user.state = USER_DELETION_STATE[0]
        save_user(user.id)


@dp.message_handler()
async def main_handler(message: types.Message):
    user = get_user(message.from_user.id, USERS)
    print(user)
    if not user:
        user = await ask_to_create_user(message)
    if user.state == USER_CREATION_STATE[0]:
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


async def ask_to_create_user(message: types.Message) -> User:
    user_id = message.from_user.id
    name = message.from_user.first_name
    user = User(id=user_id, first_name=name, state=USER_CREATION_STATE[0])
    await message.answer(f'Здравствуйте, {name}! Это бот для составления диаграмм привычек. '
                         f'Желаете создать новый профиль?')
    USERS.update({user_id: user})
    save_user(user_id)
    return user


async def user_creation_agreement(message: types.Message, user: User):
    if message.text.lower() == 'да':
        await message.reply('Отлично!')
        await message.answer('Выберите имя для своего профиля, допустимо использовать латинские буквы и/или цифры.')
        user.state = USER_CREATION_STATE[1]
        save_user(user.id)
    elif message.text.lower() == 'нет':
        await message.reply('Воля ваша.')
        user.state = USER_CREATION_STATE[0]
        save_user(user.id)
    else:
        await message.reply('Не понимаю.')


async def user_name_selection(message: types.Message, user: User):
    if message.text.isalnum():
        await message.reply('Проверим...')
        try:
            token, username = create_user(TOKEN_PIXELA, message.text.lower())
            await message.answer(f'Профиль успешно создан! Ваше имя профиля {username}, токен {token}.')
            await message.answer('Выберите команду:\n'
                                 '/create - Создать новую таблицу.\n'
                                 '/select - Просмотреть доступные таблицы.\n'
                                 '/delete - Удалить профиль.\n'
                                 '/exit   - Выйти.')
            user.pixela_token = token
            user.pixela_name = username
            user.state = USER_CREATION_STATE[2]
            save_user(user.id)
        except PixelaDataException as exc:
            await message.reply(f'Произошла ошибка {exc}.')
            await message.answer('Попробуйте другое имя.')
    else:
        await message.reply('Введите корректное имя.')


async def pixela_tables_lookup(message: types.Message, user: User):
    await message.reply('Ищем ваши таблицы...')
    try:
        graphs = get_graphs(user.pixela_token, user.pixela_name)
        user.graphs = graphs
        save_user(user.id)
        await tables_inline(message, graphs)
    except PixelaDataException as exc:
        await message.reply(f'Произошла ошибка {exc}.')


async def graph_creation_name(message: types.Message, user: User):
    await message.answer('Создаем таблицу!')
    await message.reply('Выберите название таблицы:')
    user.graph = {'id': None, 'name': None, 'unit': None, 'type': None, 'color': None}
    user.state = GRAPH_CREATION_STATE[0]
    save_user(user.id)


async def creation_graph_confirm(message: types.Message, user: User):
    await message.answer(f'Создаем таблицу с именем {user.graph["name"]} '
                         f'в единицах {user.graph["unit"]} и с цветом {user.graph["color"].name}. Все верно?')
    user.state = GRAPH_CREATION_STATE[4]


async def updating_graph(message: types.Message, user: User):
    try:
        id = update_graph(user.pixela_token, user.pixela_name, **user.graph)
        if user.graph['id'] == id:
            await message.answer('Таблица успешно обновлена!')
            user.editting = False
    except PixelaDataException as exc:
        await message.reply(f'Произошла ошибка {exc}.')


async def graph_creation_unit(message: types.Message, user: User):
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
        save_user(user.id)
    else:
        await message.reply('Не понимаю.')


async def graph_creation_type(message: types.Message, user: User):
    if message.text:
        user.graph['unit'] = message.text
        if user.editting:
            await updating_graph(message, user)
        else:
            if not user.graph['type']:
                await type_selection(message)
                user.state = GRAPH_CREATION_STATE[2]
            else:
                await creation_graph_confirm(message, user)
        save_user(user.id)
    else:
        await message.reply('Не понимаю.')


async def type_selection(message: types.Message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    buttons = []
    for unit in 'Целые', 'Дробные':
        btn = types.KeyboardButton(unit)
        buttons.append(btn)
    markup.add(*buttons)
    await message.reply('Выберите тип единиц измерения таблицы:', reply_markup=markup)


async def graph_creation_color(message: types.Message, user: User):
    if message.text.lower() == "целые":
        user.graph['type'] = 'int'
        if user.editting:
            await updating_graph(message, user)
        else:
            if not user.graph['color']:
                await color_selection(message)
                user.state = GRAPH_CREATION_STATE[3]
            else:
                await creation_graph_confirm(message, user)
        save_user(user.id)
    elif message.text.lower() == 'дробные':
        user.graph['type'] = 'float'
        if user.editting:
            await updating_graph(message, user)
        else:
            if not user.graph['color']:
                await color_selection(message)
                user.state = GRAPH_CREATION_STATE[3]
            else:
                await creation_graph_confirm(message, user)
        save_user(user.id)
    else:
        await message.reply('Не понимаю.')


async def color_selection(message: types.Message):
    markup = types.ReplyKeyboardMarkup(row_width=3, one_time_keyboard=True)
    buttons = []
    for color in ('зеленый', "красный", "желтый", "синий", "черный", "фиолетовый"):
        btn = types.KeyboardButton(color)
        buttons.append(btn)
    markup.add(*buttons)
    await message.reply('Выберите цвет таблицы:', reply_markup=markup)


async def graph_creation_confirm(message: types.Message, user: User):
    match message.text:
        case 'зеленый':
            user.graph['color'] = Color.green
        case "красный":
            user.graph['color'] = Color.red
        case "желтый":
            user.graph['color'] = Color.yellow
        case "синий":
            user.graph['color'] = Color.blue
        case "черный":
            user.graph['color'] = Color.black
        case "фиолетовый":
            user.graph['color'] = Color.purple
        case _:
            user.graph['color'] = None
    if user.graph["color"]:
        if user.editting:
            await updating_graph(message, user)
        else:
            await creation_graph_confirm(message, user)
        save_user(user.id)
    else:
        await message.reply('Не понимаю.')


async def graph_creation_finish(message: types.Message, user: User):
    if message.text.lower() == 'да':
        await message.reply('Создаем таблицу...')
        try:
            user.graph.pop('id')
            id = create_graph(
                 user.pixela_token,
                 user.pixela_name,
                 **user.graph)
            user.graph['id'] = id
            await message.answer(f'Успешно создана таблица с id {id}!')
        except PixelaDataException as exc:
            await message.reply(f'Произошла ошибка {exc}.')
    elif message.text.lower() == 'нет':
        markup = await edit_graph_inline(None)
        await message.reply('Выберите что изменить:', reply_markup=markup)
    else:
        await message.reply('Не понимаю.')


async def user_delete_handler(message: types.Message, user: User):
    if message.text.lower() == 'да':
        try:
            delete_user(user.pixela_token, user.pixela_name)
            await message.answer('Профиль успешно удален!')
            user.reset()
        except PixelaDataException as exc:
            await message.answer(f'Произошла ошибка {exc}.')
    elif message.text.lower() == 'нет':
        await pixela_tables_lookup(message, user)
    else:
        await message.reply('Не понимаю.')


async def pixel_post_type(message: types.Message, user: User, type: str):
    if user.graph['type'] == type:
        try:
            post_pixel(user.pixela_token, user.pixela_name, user.graph['id'], user.pixel['quantity'], user.pixel['date'])
            await message.answer('Точка успешно добавлена!')
        except PixelaDataException as exc:
            await message.answer(f'Произошла ошибка {exc}.')
    else:
        await message.reply(f'Выберите верный тип данных {user.graph["type"]}.')


async def pixel_quantity_selection(message: types.Message, user: User):
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


async def edit_pixel_confirm(message: types.Message, user: User):
    try:
        quantity = int(message.text)
        if user.graph['type'] == 'int':
            try:
                update_pixel(user.pixela_token, user.pixela_name, user.graph['id'], quantity, user.pixel_date)
                await message.answer('Точка успешно обновлена!')
            except PixelaDataException as exc:
                await message.answer(f'Произошла ошибка {exc}.')
        else:
            await message.reply(f'Выберите верный тип данных {user.graph["type"]}.')
    except ValueError:
        try:
            quantity = float(message.text)
            if user.graph['type'] == 'float':
                try:
                    update_pixel(user.pixela_token, user.pixela_name, user.graph['id'], quantity, user.pixel_date)
                    await message.answer('Точка успешно обновлена!')
                except PixelaDataException as exc:
                    await message.answer(f'Произошла ошибка {exc}.')
            else:
                await message.reply(f'Выберите верный тип данных {user.graph["type"]}.')
        except ValueError:
            await message.reply('Не понимаю.')


executor.start_polling(dp, skip_updates=True)
