"""
Tests API to provide expected answers to given requests.
"""

from datetime import datetime
import pytest
import pytest_asyncio
import aiohttp
import asyncio
from pixela import *
from utils import *


user_name1 = 'vasya'
user_name2 = 'MaSha-99'
user_data1 = (TOKEN_PIXELA, NAME_PREFIX + 'vasya')
user_data2 = (TOKEN_PIXELA, NAME_PREFIX + 'masha-99')
graph_data1 = ('Test graph', 'kilo', 'int', Color.shibafu.name, 'test-graph')
graph_data2 = ('tEst @_mygraph', 'kilo', 'float', Color.momiji.name, 'test---mygraph')
pixel_data1 = (date_to_str(datetime.today()), 5, date_to_str(datetime.today()))
pixel_data2 = (date_to_str(datetime(year=2020, month=3, day=4)), 2.3, '20200304')


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope='session')
async def session(event_loop):
    cl_ses = aiohttp.ClientSession()
    print("Session ", cl_ses, id(cl_ses))
    yield cl_ses
    await cl_ses.close()


@pytest_asyncio.fixture()
async def create_delete_user(session):
    token, username = await create_user(session, TOKEN_PIXELA, user_name1)
    yield (token, username)
    await delete_user(session, token, username)


@pytest.fixture()
def cleanup_user(session):
    async def do_cleanup(token, username):
        await delete_user(session, token, username)
    return do_cleanup


@pytest_asyncio.fixture()
async def create_delete_graph(session):
    id = await create_graph(session, *user_data1, *graph_data1[:-1])
    yield id
    await delete_graph(session, *user_data1, id)


@pytest.fixture()
def cleanup_graph(session):
    async def do_cleanup(id):
        await delete_graph(session, *user_data1, id)
    return do_cleanup


@pytest_asyncio.fixture()
async def create_delete_pixel(session):
    id = await post_pixel(session, *user_data1, graph_data1[-1], *pixel_data1[:-1])
    yield id
    await delete_pixel(session, *user_data1, graph_data1[-1], pixel_data1[-1])


@pytest.fixture()
def cleanup_pixel(session):
    async def do_cleanup(date, graph_data=graph_data1):
        await delete_pixel(session, *user_data1, graph_data[-1], date)
    return do_cleanup


@pytest.mark.asyncio
class TestCreateUser:
    @pytest.mark.parametrize('token, name, output', [
        (TOKEN_PIXELA, user_name1, user_data1),
        (TOKEN_PIXELA, user_name2, user_data2),
    ])
    async def test_success(self, session, cleanup_user, token, name, output):
        assert await create_user(session, token, name) == output
        await cleanup_user(*output)

    @pytest.mark.parametrize('token, name', [
        (TOKEN_PIXELA, '_vasya@'),
        (TOKEN_PIXELA, 'вася')
    ])
    async def test_incorrect_name(self, session, token, name):
        with pytest.raises(PixelaDataException):
            await create_user(session, token, name)

    async def test_already_exists(self, session, cleanup_user):
        output = await create_user(session, TOKEN_PIXELA, user_name1)
        with pytest.raises(PixelaDataException):
            await create_user(session, TOKEN_PIXELA, user_name1)
        await cleanup_user(*output)


@pytest.mark.asyncio
class TestDeleteUser:
    async def test_duplicate(self, session):
        output = await create_user(session, TOKEN_PIXELA, user_name1)
        assert await delete_user(session, *output) is True
        with pytest.raises(PixelaDataException):
            await delete_user(session, *output)


@pytest.mark.asyncio
class TestCreateGraph:
    @pytest.mark.parametrize('graph_name, unit, type, color, output', [
        graph_data1,
        graph_data2
    ])
    async def test_success(self, session, create_delete_user, cleanup_graph, graph_name, unit, type, color, output):
        token, username = create_delete_user
        assert await create_graph(session, token, username, graph_name, unit, type, color) == output
        await cleanup_graph(output)

    @pytest.mark.parametrize('graph_name, unit, type, color', [
        ('Test graph', 'kilo', 'text', Color.shibafu.name),
        ('Test graph', 'kilo', int, Color.shibafu.name),
        ('Test graph', 'kilo', 'int', 'green'),
    ])
    async def test_wrong_data(self, session, create_delete_user, graph_name, unit, type, color):
        token, username = create_delete_user
        with pytest.raises(PixelaDataException):
            await create_graph(session, token, username, graph_name, unit, type, color)

    async def test_already_exists(self, session, create_delete_user, cleanup_graph):
        token, username = create_delete_user
        id = await create_graph(session, token, username, *graph_data1[:-1])
        with pytest.raises(PixelaDataException):
            await create_graph(session, token, username, *graph_data1[:-1])
        await cleanup_graph(id)


@pytest.mark.asyncio
class TestDeleteGraph:
    async def test_duplicate(self, session, create_delete_user):
        id = await create_graph(session, *create_delete_user, *graph_data1[:-1])
        assert await delete_graph(session, *create_delete_user, id) is True
        with pytest.raises(PixelaDataException):
            await delete_graph(session, *create_delete_user, id)


@pytest.mark.asyncio
class TestUpdateGraph:
    @pytest.mark.parametrize('graph_name, unit, type, color', [
        ('Test graph', 'kilo', 'float', Color.shibafu.name),
        ('Test graph', 'kilos', 'float', Color.shibafu.name),
        ('Test1 graph', 'kilo', 'int', Color.shibafu.name),
        ('Test1 graph', 'kilo', 'int', Color.momiji.name),
    ])
    async def test_success(self, session, create_delete_user, create_delete_graph, graph_name, unit, type, color):
        token, username = create_delete_user
        id = create_delete_graph
        assert await update_graph(session, token, username, id, graph_name, unit, type, color) == id

    @pytest.mark.parametrize('graph_name, unit, type, color', [
        ('Test graph', 'kilo', 'text', Color.shibafu.name),
        ('Test graph', 'kilo', int, Color.shibafu.name),
        ('Test graph', 'kilo', 'int', 'green'),
    ])
    async def test_wrong_data(self, session, create_delete_user, graph_name, unit, type, color):
        token, username = create_delete_user
        id = create_delete_graph
        with pytest.raises(PixelaDataException):
            await update_graph(session, token, username, id, graph_name, unit, type, color)

    async def test_graph_doesnt_exist(self, session, create_delete_user):
        token, username = create_delete_user
        with pytest.raises(PixelaDataException):
            await update_graph(session, token, username, graph_data1[-1], *graph_data1[:-1])


@pytest.mark.asyncio
class TestGetAndShowGraphs:
    async def test_get_single_graph_success(self, session, create_delete_user, create_delete_graph):
        assert await get_graph(session, *create_delete_user, create_delete_graph) == {
            'id': 'test-graph', 'name': 'Test graph', 'unit': 'kilo',
            'type': 'int', 'color': Color.shibafu.name
        }

    async def test_get_single_graph_no_graph(self, session, create_delete_user):
        with pytest.raises(PixelaDataException):
            await get_graph(session, *create_delete_user, graph_data1[-1])

    async def test_get_single_graph_no_user(self, session):
        with pytest.raises(PixelaDataException):
            await get_graph(session, *user_data1, graph_data1[-1])

    async def test_get_success(self, session, create_delete_user, create_delete_graph):
        assert await get_graphs(session, *create_delete_user) == [{'id': 'test-graph', 'name': 'Test graph',
                                                                   'unit': 'kilo', 'type': 'int', 'color': 'shibafu'}]

    async def test_get_success_zero(self, session, create_delete_user):
        assert len(await get_graphs(session, *create_delete_user)) == 0

    async def test_user_doesnt_exist(self, session):
        with pytest.raises(PixelaDataException):
            await get_graphs(session, *user_data1)

    async def test_show_success(self, session, create_delete_user, create_delete_graph):
        token, username = create_delete_user
        id = create_delete_graph
        assert await show_graph(session, username, id) == \
               'https://pixe.la/v1/users/' + username + '/graphs/' + id + '.html?mode=simple'

    async def test_show_graph_doesnt_exist(self, session, create_delete_user):
        token, username = create_delete_user
        with pytest.raises(PixelaDataException):
            await show_graph(session, username, graph_data1[-1])

    async def test_show_user_doesnt_exist(self, session):
        with pytest.raises(PixelaDataException):
            await show_graph(session, user_data1[-1], graph_data1[-1])


@pytest.mark.asyncio
class TestPostPixel:
    @pytest.mark.parametrize('graph_data, date, quantity, output', [
        (graph_data1, *pixel_data1),
        (graph_data2, *pixel_data2)
    ])
    async def test_success(self, session, create_delete_user, cleanup_graph, cleanup_pixel, graph_data, quantity, date, output):
        id = await create_graph(session, *user_data1, *graph_data[:-1])
        assert await post_pixel(session, *create_delete_user, id, date, quantity) == output
        await cleanup_pixel(date, graph_data=graph_data)
        await cleanup_graph(id)

    @pytest.mark.parametrize('quantity, date', [
        ('5', date_to_str(datetime.today())),
        (5, 20200503),
        (5, datetime.today()),
    ])
    async def test_wrong_data(self, session, create_delete_user, create_delete_graph, quantity, date):
        with pytest.raises(PixelaDataException):
            await post_pixel(session, *create_delete_user, create_delete_graph, date, quantity)

    async def test_graph_doesnt_exist(self, session, create_delete_user):
        with pytest.raises(PixelaDataException):
            await post_pixel(session, *create_delete_user, graph_data1[-1], *pixel_data1[:-1])

    async def test_user_doesnt_exist(self, session):
        with pytest.raises(PixelaDataException):
            await post_pixel(session, *user_data1, graph_data1[-1], *pixel_data1[:-1])


@pytest.mark.asyncio
class TestDeletePixel:
    async def test_duplicate(self, session, create_delete_user, create_delete_graph):
        await post_pixel(session, *create_delete_user, create_delete_graph, *pixel_data1[:-1])
        assert await delete_pixel(session, *create_delete_user, create_delete_graph, pixel_data1[0]) is True
        with pytest.raises(PixelaDataException):
            await delete_pixel(session, *create_delete_user, create_delete_graph, pixel_data1[0])


@pytest.mark.asyncio
class TestUpdatePixel:
    @pytest.mark.parametrize('graph_data, quantity, date, output', [
        (graph_data1, 15, date_to_str(datetime.today()), date_to_str(datetime.today())),
        (graph_data1, 15, date_to_str(datetime(year=2022, month=10, day=1)), '20221001'),
        (graph_data2, 3.3, date_to_str(datetime(year=2020, month=3, day=4)), '20200304'),
        (graph_data2, 3.3, date_to_str(datetime.today()), date_to_str(datetime.today()))
    ])
    async def test_success(self, session, create_delete_user, cleanup_graph, cleanup_pixel, graph_data, quantity, date, output):
        id = await create_graph(session, *user_data1, *graph_data[:-1])
        await post_pixel(session, *create_delete_user, id, *pixel_data1[:-1])
        assert await update_pixel(session, *create_delete_user, id, date, quantity) == output
        await cleanup_pixel(date, graph_data=graph_data)
        await cleanup_graph(id)

    @pytest.mark.parametrize('graph_data, quantity, date', [
        (graph_data1, '15', pixel_data1[0]),
        (graph_data1, 15.1, pixel_data1[0]),
        (graph_data2, '3.3', pixel_data1[0])
    ])
    async def test_wrong_data(self, session, create_delete_user, cleanup_graph, cleanup_pixel, graph_data, quantity, date):
        id = await create_graph(session, *user_data1, *graph_data[:-1])
        await post_pixel(session, *create_delete_user, id, *pixel_data1[:-1])
        with pytest.raises(PixelaDataException):
            await update_pixel(session, *create_delete_user, id, date, quantity)
        await cleanup_pixel(date, graph_data=graph_data)
        await cleanup_graph(id)

    async def test_graph_doesnt_exist(self, session, create_delete_user):
        with pytest.raises(PixelaDataException):
            await update_pixel(session, *create_delete_user, graph_data1[-1], *pixel_data1[:-1])

    async def test_user_doesnt_exist(self, session):
        with pytest.raises(PixelaDataException):
            await update_pixel(session, *user_data1, graph_data1[-1], *pixel_data1[:-1])


@pytest.mark.asyncio
class TestGetPixel:
    async def test_get_pixels_success(self, session, create_delete_user, create_delete_graph, create_delete_pixel):
        assert await get_pixels(session, *create_delete_user, create_delete_graph) == [
            {'date': pixel_data1[0], 'quantity': str(pixel_data1[1])}
        ]

    async def test_get_pixels_no_pixels(self, session, create_delete_user, create_delete_graph):
        assert await get_pixels(session, *create_delete_user, create_delete_graph) == []

    async def test_get_pixels_no_graph(self, session, create_delete_user):
        with pytest.raises(PixelaDataException):
            await get_pixels(session, *create_delete_user, graph_data1[-1])

    async def test_get_pixels_no_user(self, session):
        with pytest.raises(PixelaDataException):
            await get_pixels(session, *user_data1, graph_data1[-1])


