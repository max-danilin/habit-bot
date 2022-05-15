import pytest
from pixela import *
from datetime import datetime


user_name1 = 'vasya'
user_name2 = 'MaSha-99'
user_data1 = (TOKEN_PIXELA, NAME_PREFIX + 'vasya')
user_data2 = (TOKEN_PIXELA, NAME_PREFIX + 'masha-99')
graph_data1 = ('Test graph', 'kilo', 'int', Color.green.value, 'test-graph')
graph_data2 = ('tEst @_mygraph', 'kilo', 'float', Color.red.value, 'test---mygraph')
pixel_data1 = (5, datetime.today(), parse_date(datetime.today()))
pixel_data2 = (2.3, datetime(year=2020, month=3, day=4), '20200304')


@pytest.fixture()
def create_delete_user():
    token, username = create_user(TOKEN_PIXELA, user_name1)
    yield (token, username)
    delete_user(token, username)


@pytest.fixture()
def cleanup_user():
    def do_cleanup(token, username):
        delete_user(token, username)
    return do_cleanup


@pytest.fixture()
def create_delete_graph():
    id = create_graph(*user_data1, *graph_data1[:-1])
    yield id
    delete_graph(*user_data1, id)


@pytest.fixture()
def cleanup_graph():
    def do_cleanup(id):
        delete_graph(*user_data1, id)
    return do_cleanup


@pytest.fixture()
def create_delete_pixel():
    id = post_pixel(*user_data1, graph_data1[-1], *pixel_data1[:-1])
    yield id
    delete_pixel(*user_data1, graph_data1[-1])


@pytest.fixture()
def cleanup_pixel():
    def do_cleanup(date, graph_data=graph_data1):
        delete_pixel(*user_data1, graph_data[-1], date)
    return do_cleanup


class TestCreateUser:
    @pytest.mark.parametrize('token, name, output', [
        (TOKEN_PIXELA, user_name1, user_data1),
        (TOKEN_PIXELA, user_name2, user_data2),
    ])
    def test_success(self, cleanup_user, token, name, output):
        assert create_user(token, name) == output
        cleanup_user(*output)

    @pytest.mark.parametrize('token, name', [
        (TOKEN_PIXELA, '_vasya@'),
        (TOKEN_PIXELA, 'вася')
    ])
    def test_incorrect_name(self, token, name):
        with pytest.raises(PixelaDataException):
            create_user(token, name)

    def test_already_exists(self, cleanup_user):
        output = create_user(TOKEN_PIXELA, user_name1)
        with pytest.raises(PixelaDataException):
            create_user(TOKEN_PIXELA, user_name1)
        cleanup_user(*output)


class TestDeleteUser:
    def test_duplicate(self):
        output = create_user(TOKEN_PIXELA, user_name1)
        assert delete_user(*output) is True
        with pytest.raises(PixelaDataException):
            delete_user(*output)


class TestCreateGraph:
    @pytest.mark.parametrize('graph_name, unit, type, color, output', [
        graph_data1,
        graph_data2
    ])
    def test_success(self, create_delete_user, cleanup_graph, graph_name, unit, type, color, output):
        token, username = create_delete_user
        assert create_graph(token, username, graph_name, unit, type, color) == output
        cleanup_graph(output)

    @pytest.mark.parametrize('graph_name, unit, type, color', [
        ('Test graph', 'kilo', 'text', Color.green.value),
        ('Test graph', 'kilo', int, Color.green.value),
        ('Test graph', 'kilo', 'int', 'green'),
    ])
    def test_wrong_data(self, create_delete_user, graph_name, unit, type, color):
        token, username = create_delete_user
        with pytest.raises(PixelaDataException):
            create_graph(token, username, graph_name, unit, type, color)

    def test_already_exists(self, create_delete_user, cleanup_graph):
        token, username = create_delete_user
        id = create_graph(token, username, *graph_data1[:-1])
        with pytest.raises(PixelaDataException):
            create_graph(token, username, *graph_data1[:-1])
        cleanup_graph(id)


class TestDeleteGraph:
    def test_duplicate(self, create_delete_user):
        id = create_graph(*create_delete_user, *graph_data1[:-1])
        assert delete_graph(*create_delete_user, id) is True
        with pytest.raises(PixelaDataException):
            delete_graph(*create_delete_user, id)


class TestUpdateGraph:
    @pytest.mark.parametrize('graph_name, unit, type, color', [
        ('Test graph', 'kilo', 'float', Color.green.value),
        ('Test graph', 'kilos', 'float', Color.green.value),
        ('Test1 graph', 'kilo', 'int', Color.green.value),
        ('Test1 graph', 'kilo', 'int', Color.red.value),
    ])
    def test_success(self, create_delete_user, create_delete_graph, graph_name, unit, type, color):
        token, username = create_delete_user
        id = create_delete_graph
        assert update_graph(token, username, id, graph_name, unit, type, color) == id

    @pytest.mark.parametrize('graph_name, unit, type, color', [
        ('Test graph', 'kilo', 'text', Color.green.value),
        ('Test graph', 'kilo', int, Color.green.value),
        ('Test graph', 'kilo', 'int', 'green'),
    ])
    def test_wrong_data(self, create_delete_user, graph_name, unit, type, color):
        token, username = create_delete_user
        id = create_delete_graph
        with pytest.raises(PixelaDataException):
            update_graph(token, username, id, graph_name, unit, type, color)

    def test_graph_doesnt_exist(self, create_delete_user):
        token, username = create_delete_user
        with pytest.raises(PixelaDataException):
            update_graph(token, username, graph_data1[-1], *graph_data1[:-1])


class TestGetAndShowGraphs:
    def test_get_success(self, create_delete_user, create_delete_graph):
        assert get_graphs(*create_delete_user) == [('test-graph', 'Test graph', 'kilo')]

    def test_get_success_zero(self, create_delete_user):
        assert len(get_graphs(*create_delete_user)) == 0

    def test_user_doesnt_exist(self):
        with pytest.raises(PixelaDataException):
            get_graphs(*user_data1)

    def test_show_success(self, create_delete_user, create_delete_graph):
        token, username = create_delete_user
        id = create_delete_graph
        assert show_graph(username, id) == \
               'https://pixe.la/v1/users/' + username + '/graphs/' + id + '.html?mode=simple'

    def test_show_graph_doesnt_exist(self, create_delete_user):
        token, username = create_delete_user
        with pytest.raises(PixelaDataException):
            show_graph(username, graph_data1[-1])

    def test_show_user_doesnt_exist(self):
        with pytest.raises(PixelaDataException):
            show_graph(user_data1[-1], graph_data1[-1])


class TestPostPixel:
    @pytest.mark.parametrize('graph_data, quantity, date, output', [
        (graph_data1, *pixel_data1),
        (graph_data2, *pixel_data2)
    ])
    def test_success(self, create_delete_user, cleanup_graph, cleanup_pixel, graph_data, quantity, date, output):
        id = create_graph(*user_data1, *graph_data[:-1])
        assert post_pixel(*create_delete_user, id, quantity, date) == output
        cleanup_pixel(date, graph_data=graph_data)
        cleanup_graph(id)

    @pytest.mark.parametrize('quantity, date', [
        ('5', datetime.today()),
        (5, 20200503),
        (5, '20200503'),
    ])
    def test_wrong_data(self, create_delete_user, create_delete_graph, quantity, date):
        with pytest.raises(PixelaDataException):
            post_pixel(*create_delete_user, create_delete_graph, quantity, date)

    def test_graph_doesnt_exist(self, create_delete_user):
        with pytest.raises(PixelaDataException):
            post_pixel(*create_delete_user, graph_data1[-1], *pixel_data1[:-1])

    def test_user_doesnt_exist(self):
        with pytest.raises(PixelaDataException):
            post_pixel(*user_data1, graph_data1[-1], *pixel_data1[:-1])


class TestDeletePixel:
    def test_duplicate(self, create_delete_user, create_delete_graph):
        post_pixel(*create_delete_user, create_delete_graph, *pixel_data1[:-1])
        assert delete_pixel(*create_delete_user, create_delete_graph, pixel_data1[1]) is True
        with pytest.raises(PixelaDataException):
            delete_pixel(*create_delete_user, create_delete_graph, pixel_data1[1])


class TestUpdatePixel:
    @pytest.mark.parametrize('graph_data, quantity, date, output', [
        (graph_data1, 15, datetime.today(), parse_date(datetime.today())),
        (graph_data1, 15, datetime(year=2022, month=10, day=1), '20221001'),
        (graph_data2, 3.3, datetime(year=2020, month=3, day=4), '20200304'),
        (graph_data2, 3.3, datetime.today(), parse_date(datetime.today()))
    ])
    def test_success(self, create_delete_user, cleanup_graph, cleanup_pixel, graph_data, quantity, date, output):
        id = create_graph(*user_data1, *graph_data[:-1])
        post_pixel(*create_delete_user, id, *pixel_data1[:-1])
        assert update_pixel(*create_delete_user, id, quantity, date) == output
        cleanup_pixel(date, graph_data=graph_data)
        cleanup_graph(id)

    @pytest.mark.parametrize('graph_data, quantity, date', [
        (graph_data1, '15', pixel_data1[1]),
        (graph_data1, 15.1, pixel_data1[1]),
        (graph_data2, '3.3', pixel_data1[1])
    ])
    def test_wrong_data(self, create_delete_user, cleanup_graph, cleanup_pixel, graph_data, quantity, date):
        id = create_graph(*user_data1, *graph_data[:-1])
        post_pixel(*create_delete_user, id, *pixel_data1[:-1])
        with pytest.raises(PixelaDataException):
            update_pixel(*create_delete_user, id, quantity, date)
        cleanup_pixel(date, graph_data=graph_data)
        cleanup_graph(id)

    def test_graph_doesnt_exist(self, create_delete_user):
        with pytest.raises(PixelaDataException):
            update_pixel(*create_delete_user, graph_data1[-1], *pixel_data1[:-1])

    def test_user_doesnt_exist(self):
        with pytest.raises(PixelaDataException):
            update_pixel(*user_data1, graph_data1[-1], *pixel_data1[:-1])



