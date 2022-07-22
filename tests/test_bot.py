"""
Tests handlers of our bot to provide proper answers for given inputs
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
import pytest
from pixela import *
from utils import *
from habit_bot import *


TODAY = datetime.today().date()
API_RETURNS = [
    ('my-md-token', 'md-habit-test-max'),
    True,
    'gtest_graph_id',
    [{'id': 'gtest_graph_id', 'name': 'gtest', 'unit': 'min', 'type': 'int', 'color': 'shibafu'}],
    'some_url',
    'gtest_graph_id',
    True,
    [{'date': date_to_str(TODAY), 'quantity': '10'}, {'date': '20200101', 'quantity': '20'}],
    'date',
    'gtest_graph_id',
    True,
    {'id': 'gtest_graph_id', 'name': 'gtest', 'unit': 'min', 'type': 'int', 'color': 'shibafu'},
]
INPUTS = ['test', '/start', "да", 'test-max', '/create', 'gtest', 'min', 'целые', 'зеленый', 'да',
          '/select', None, None, None, None, None, '10', None, None, None, '20', None,
          None, None, '5', None, None, None, None, None, None, None, None, 'qtest',
          None, None, None, None, None, None, '/delete', 'да', ]
EXPECTED_ANSWERS = [
    'Здравствуйте, Max! Это бот для составления диаграмм привычек.',
    'Здравствуйте, Max! Профиль Pixela не найден. Желаете создать?',
    'Выберите имя для своего профиля, допустимо использовать латинские буквы и/или цифры.',
    'Профиль успешно создан! Ваше имя профиля md-habit-test-max, токен my-md-token.',
    'Создаем таблицу!',
    'Выберите единицы измерения таблицы:',
    'Выберите тип единиц измерения таблицы:',
    'Выберите цвет таблицы:',
    'Создаем таблицу с именем gtest в единицах min и с цветом зеленый. Все верно?',
    'Успешно создана таблица с id gtest_graph_id!',
    'Ваши таблицы:',
    None,
    'Ссылка на таблицу:\nsome_url',
    'Выберите действие с точкой:',
    'Выберите дату для добавления точки:',
    f'Вы выбрали {TODAY.strftime("%d/%m/%Y")}.',
    'Точка успешно добавлена!',
    None,
    'Выберите дату для добавления точки:',
    'Вы выбрали 01/01/2020.',
    'Точка успешно добавлена!',
    None,
    'Выберите точку для изменения:',
    'Выберите новое значение точки:',
    'Точка успешно обновлена!',
    None,
    'Выберите точку для удаления:',
    None,
    None,
    'Точка успешно удалена!',
    None,
    'Редактировать:',
    'Выберите новое имя:',
    'Таблица успешно обновлена!',
    None,
    'Редактировать:',
    'Невозможно поменять тип единиц в таблице с уже существующими точками.',
    None,
    'Вы уверены?',
    'Таблица успешно удалена!',
    'Вы уверены?',
    'Профиль успешно удален!',
]
REPLY_TYPES = [
    'answer',
    'answer',
    'answer',
    'answer',
    'answer',
    'reply',
    'reply',
    'reply',
    'answer',
    'answer',
    'answer',
    'edit_reply_markup',
    'edit_text',
    'edit_text',
    'edit_text',
    'edit_text',
    'answer',
    'edit_reply_markup',
    'edit_text',
    'edit_text',
    'answer',
    'edit_reply_markup',
    'edit_text',
    'answer',
    'answer',
    'edit_reply_markup',
    'edit_text',
    'edit_reply_markup',
    'edit_reply_markup',
    'answer',
    'edit_reply_markup',
    'edit_text',
    'edit_text',
    'answer',
    'edit_reply_markup',
    'edit_text',
    'answer',
    'edit_reply_markup',
    'edit_text',
    'answer',
    'reply',
    'answer',
]
USER_STATES = [
    None,
    USER_CREATION_STATE[0],
    USER_CREATION_STATE[1],
    USER_DEFAULT_STATE[0],
    GRAPH_CREATION_STATE[0],
    GRAPH_CREATION_STATE[1],
    GRAPH_CREATION_STATE[2],
    GRAPH_CREATION_STATE[3],
    GRAPH_CREATION_STATE[4],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    PIXEL_ADD_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    PIXEL_ADD_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    PIXEL_EDIT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    GRAPH_CREATION_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DEFAULT_STATE[0],
    USER_DELETION_STATE[0],
    None,
]
IF_INLINE_QUERY = [
    False,
    False,
    False,
    False,
    False,
    False,
    False,
    False,
    False,
    False,
    False,
    True,
    True,
    True,
    True,
    True,
    False,
    True,
    True,
    True,
    False,
    True,
    True,
    True,
    False,
    True,
    True,
    True,
    True,
    True,
    True,
    True,
    True,
    False,
    True,
    True,
    True,
    True,
    True,
    True,
    False,
    False,
]
INLINE_HANDLERS = [
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    inline_graph_handler,
    view_graph,
    inline_pixel_handler,
    add_pixel_handler,
    add_pixel_date_simple,
    None,
    inline_graph_handler,
    add_pixel_date_other,
    process_simple_calendar,
    None,
    inline_graph_handler,
    edit_pixel,
    pixel_edit_ask_quantity,
    None,
    inline_graph_handler,
    del_pixel,
    partial(load_pixel_prev, users=USERS),
    partial(load_pixel_next, users=USERS),
    pixel_delete_confirm,
    inline_graph_handler,
    edit_handler,
    edit_name_handler,
    None,
    inline_graph_handler,
    edit_handler,
    edit_type_handler,
    inline_graph_handler,
    delete_graph_ask_confirm,
    delete_graph_confirm,
    None,
    None,
]
CALLBACK_DATAS = [
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    {'graph': 'gtest_graph_id', 'action': 'list'},
    {'graph': 'gtest_graph_id', 'action': 'view'},
    {'graph': 'gtest_graph_id', 'action': 'pixel'},
    {'graph': 'gtest_graph_id', 'action': 'add'},
    {'graph': 'gtest_graph_id', 'action': 'add_today'},
    None,
    {'graph': 'gtest_graph_id', 'action': 'list'},
    {'graph': 'gtest_graph_id', 'action': 'add_other'},
    {'year': 2020, 'month': 1, 'day': 1, 'act': 'DAY'},
    None,
    {'graph': 'gtest_graph_id', 'action': 'list'},
    {'graph': 'gtest_graph_id', 'action': 'edit_pixel'},
    {'pixel': '20200101', 'action': 'edit'},
    None,
    {'graph': 'gtest_graph_id', 'action': 'list'},
    {'graph': 'gtest_graph_id', 'action': 'del_pixel'},
    {'date': date_to_str(date(year=TODAY.year, month=TODAY.month, day=1)),
     'action': 'delete', 'direction': 'prev'},
    {'date': '20200201', 'action': 'delete', 'direction': 'next'},
    {'pixel': '20200101', 'action': 'delete'},
    {'graph': 'gtest_graph_id', 'action': 'list'},
    {'graph': 'gtest_graph_id', 'action': 'edit'},
    {'graph': 'gtest_graph_id', 'action': 'edit_name'},
    None,
    {'graph': 'gtest_graph_id', 'action': 'list'},
    {'graph': 'gtest_graph_id', 'action': 'edit'},
    {'graph': 'gtest_graph_id', 'action': 'edit_type'},
    {'graph': 'gtest_graph_id', 'action': 'list'},
    {'graph': 'gtest_graph_id', 'action': 'del_graph'},
    {'graph': 'gtest_graph_id', 'action': 'del_graph_confirm'},
    None,
    None,
]
user_mock = Mock()
user_mock.graph = {'unit': 'min'}


def create_custom_markup(date_: date, dir_: str, quant: str) -> types.InlineKeyboardMarkup:
    custom_markup = types.InlineKeyboardMarkup(row_width=4)
    custom_markup.row()
    ord_btn = []
    new_month = date_.month + 1 if dir_ == 'next' else date_.month
    ord_btn.append(create_inline_btn_for_direction(date(
        year=date_.year, month=new_month, day=1
    ), dir_, 'delete'))
    ord_btn.append(types.InlineKeyboardButton(text=date_.strftime('%B'),
                                              callback_data=ignore_callback))
    if dir_ == 'next':
        ord_btn.reverse()
    for o_btn in ord_btn:
        custom_markup.insert(o_btn)
    custom_markup.row()
    custom_markup.insert(create_inline_btn_for_date(date_, quant, 'min', 'delete'))
    return custom_markup


custom_markup = create_custom_markup(TODAY, 'prev', '10')
prev_markup = create_custom_markup(date(year=2020, month=1, day=1), 'next', '20')
next_markup = create_custom_markup(TODAY, 'prev', '10')


async def reply_kwarg():
    return [
            {},
            {},
            {},
            {},
            {},
            {},
            {'reply_markup': type_selection()},
            {'reply_markup': color_selection()},
            {},
            {},
            {'reply_markup': graphs_info_inline(API_RETURNS[3])},
            {'reply_markup': create_markup_list_graphs(API_RETURNS[2])},
            {},
            {'reply_markup': create_inline_markup_pixel_action(API_RETURNS[2])},
            {'reply_markup': create_markup_add_pixel(API_RETURNS[2])},
            {},
            {},
            {'reply_markup': create_markup_list_graphs(API_RETURNS[2])},
            {'reply_markup': await SimpleCalendar().start_calendar()},
            {},
            {},
            {'reply_markup': create_markup_list_graphs(API_RETURNS[2])},
            {'reply_markup': await load_pixels(API_RETURNS[7], user_mock, action='edit')},
            {},
            {},
            {'reply_markup': create_markup_list_graphs(API_RETURNS[2])},
            {'reply_markup': custom_markup},
            {'reply_markup': prev_markup},
            {'reply_markup': next_markup},
            {},
            {'reply_markup': create_markup_list_graphs(API_RETURNS[2])},
            {'reply_markup': await edit_graph_inline(API_RETURNS[2])},
            {},
            {},
            {'reply_markup': create_markup_list_graphs(API_RETURNS[2])},
            {'reply_markup': await edit_graph_inline(API_RETURNS[2])},
            {},
            {'reply_markup': create_markup_list_graphs(API_RETURNS[2])},
            {'reply_markup': create_markup_for_graph_delete(API_RETURNS[2])},
            {},
            {},
            {},
        ]


@pytest.mark.asyncio
async def test_main_handler():
    user = User(id=10, first_name='Max', state=USER_CREATION_STATE[0])
    user_none = None
    initial_mess_mock = AsyncMock(text=INPUTS[0], from_user=user)

    patchers = []
    patchers.append(patch('habit_bot.create_db_user', AsyncMock()))
    patchers.append(patch('habit_bot.save_user', AsyncMock()))
    patchers.append(patch('habit_bot.bot.pin_chat_message', AsyncMock()))

    patchers.append(patch('habit_bot.create_user', AsyncMock(return_value=API_RETURNS[0])))
    patchers.append(patch('habit_bot.delete_user', AsyncMock(return_value=API_RETURNS[1])))
    patchers.append(patch('habit_bot.create_graph', AsyncMock(return_value=API_RETURNS[2])))
    patchers.append(patch('habit_bot.get_graphs', AsyncMock(return_value=API_RETURNS[3])))
    patchers.append(patch('habit_bot.show_graph', AsyncMock(return_value=API_RETURNS[4])))
    patchers.append(patch('habit_bot.update_graph', AsyncMock(return_value=API_RETURNS[5])))
    patchers.append(patch('habit_bot.delete_graph', AsyncMock(return_value=API_RETURNS[6])))
    patchers.append(patch('habit_bot.get_pixels', AsyncMock(return_value=API_RETURNS[7])))
    patchers.append(patch('habit_bot.post_pixel', AsyncMock(return_value=API_RETURNS[8])))
    patchers.append(patch('habit_bot.update_pixel', AsyncMock(return_value=API_RETURNS[9])))
    patchers.append(patch('habit_bot.delete_pixel', AsyncMock(return_value=API_RETURNS[10])))
    patchers.append(patch('habit_bot.get_graph', AsyncMock(return_value=API_RETURNS[11])))

    for patcher in patchers:
        patcher.start()

    # We need to patch first call to get user from USERS, because it goes to db
    # Afterwards we just check USERS dictionary, therefore no patch needed
    with patch('habit_bot.get_user', AsyncMock(return_value=user_none)):
        await main_handler(message=initial_mess_mock)
        initial_mess_mock.answer.assert_any_call(EXPECTED_ANSWERS[0])

    counter = 0
    for answer, input_, reply_type, kwarg, state, inline, inline_handler, c_back in zip(
            EXPECTED_ANSWERS, INPUTS, REPLY_TYPES, await reply_kwarg(), USER_STATES,
            IF_INLINE_QUERY, INLINE_HANDLERS, CALLBACK_DATAS):
        counter += 1
        if answer == EXPECTED_ANSWERS[0]:
            continue
        mock = AsyncMock(text=input_, from_user=user)
        if inline:
            mock = AsyncMock(message=mock, from_user=user)
        if not inline:
            handle = command_handler if input_.startswith('/') else main_handler
            await handle(message=mock)
            send_type = getattr(mock, reply_type)
        else:
            await inline_handler(query=mock, callback_data=c_back)
            send_type = getattr(mock.message, reply_type)
        if not answer:
            send_type.assert_any_call(**kwarg)
        else:
            send_type.assert_any_call(answer, **kwarg)
        m_user = await get_user(user.id, USERS)
        assert m_user.state == state

    # print(counter)
    for patcher in patchers:
        patcher.stop()
