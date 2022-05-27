from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import BotBlocked
from aiogram.utils.callback_data import CallbackData
from utils import *
from pixela import *
import json


token = '5381219717:AAGmW2vYBGKaqnOpH3ng3iGC_o9Bff4KvsQ'
base_url = 'https://api.telegram.org/bot' + token

bot = Bot(token)
dp = Dispatcher(bot)

# TODO implement bot behaviour
USER_CREATION_STATE = ('new user', 'user creation', 'user done')
USER_DELETION_STATE = ('deletion confirmed',)
GRAPH_CREATION_STATE = ('choosing name', 'choosing unit', 'choosing type', 'choosing color', 'graph confirmation')
USERS = dict()
COMMANDS = ['start', 'select', 'create', 'delete']
cb = CallbackData('post', 'graph', 'action')


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
        text='Добавить точку',
        callback_data=cb.new(callback_data['graph'], 'add'))
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


@dp.callback_query_handler(cb.filter(action=['del_graph']))
async def edit_handler(query: types.CallbackQuery, callback_data: dict):
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
async def edit_handler(query: types.CallbackQuery, callback_data: dict):
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


async def graph_creation_unit(message: types.Message, user: User):
    if message.text:
        user.graph['name'] = message.text
        if user.editting:
            try:
                id = update_graph(user.pixela_token, user.pixela_name, **user.graph)
                if user.graph['id'] == id:
                    await message.answer('Таблица успешно обновлена!')
                    user.editting = False
            except PixelaDataException as exc:
                await message.reply(f'Произошла ошибка {exc}.')
        else:
            if not user.graph['unit']:
                await message.reply('Выберите единицы измерения таблицы:')
                user.state = GRAPH_CREATION_STATE[1]
            else:
                await message.answer(f'Создаем таблицу с именем {user.graph["name"]} '
                                     f'в единицах {user.graph["unit"]} и с цветом {user.graph["color"].name}. Все верно?')
                user.state = GRAPH_CREATION_STATE[4]
        save_user(user.id)
    else:
        await message.reply('Не понимаю.')


async def graph_creation_type(message: types.Message, user: User):
    if message.text:
        user.graph['unit'] = message.text
        if user.editting:
            try:
                id = update_graph(user.pixela_token, user.pixela_name, **user.graph)
                if user.graph['id'] == id:
                    await message.answer('Таблица успешно обновлена!')
                    user.editting = False
            except PixelaDataException as exc:
                await message.reply(f'Произошла ошибка {exc}.')
        else:
            if not user.graph['type']:
                await type_selection(message)
                user.state = GRAPH_CREATION_STATE[2]
            else:
                await message.answer(f'Создаем таблицу с именем {user.graph["name"]} '
                                     f'в единицах {user.graph["unit"]} и с цветом {user.graph["color"].name}. Все верно?')
                user.state = GRAPH_CREATION_STATE[4]
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
            try:
                id = update_graph(user.pixela_token, user.pixela_name, **user.graph)
                if user.graph['id'] == id:
                    await message.answer('Таблица успешно обновлена!')
                    user.editting = False
            except PixelaDataException as exc:
                await message.reply(f'Произошла ошибка {exc}.')
        else:
            if not user.graph['color']:
                await color_selection(message)
                user.state = GRAPH_CREATION_STATE[3]
            else:
                await message.answer(f'Создаем таблицу с именем {user.graph["name"]} '
                                     f'в единицах {user.graph["unit"]} и с цветом {user.graph["color"].name}. Все верно?')
                user.state = GRAPH_CREATION_STATE[4]
        save_user(user.id)
    elif message.text.lower() == 'дробные':
        user.graph['type'] = 'float'
        if user.editting:
            try:
                id = update_graph(user.pixela_token, user.pixela_name, **user.graph)
                if user.graph['id'] == id:
                    await message.answer('Таблица успешно обновлена!')
                    user.editting = False
            except PixelaDataException as exc:
                await message.reply(f'Произошла ошибка {exc}.')
        else:
            if not user.graph['color']:
                await color_selection(message)
                user.state = GRAPH_CREATION_STATE[3]
            else:
                await message.answer(f'Создаем таблицу с именем {user.graph["name"]} '
                                     f'в единицах {user.graph["unit"]} и с цветом {user.graph["color"].name}. Все верно?')
                user.state = GRAPH_CREATION_STATE[4]
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
            try:
                id = update_graph(user.pixela_token, user.pixela_name, **user.graph)
                if user.graph['id'] == id:
                    await message.answer('Таблица успешно обновлена!')
                    user.editting = False
            except PixelaDataException as exc:
                await message.reply(f'Произошла ошибка {exc}.')
        else:
            await message.answer(f'Создаем таблицу с именем {user.graph["name"]} '
                                 f'в единицах {user.graph["unit"]} и с цветом {user.graph["color"].name}. Все верно?')
            user.state = GRAPH_CREATION_STATE[4]
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


executor.start_polling(dp, skip_updates=True)
