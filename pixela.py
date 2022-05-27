import requests
import json
from typing import Tuple, Union, List, Optional, Literal
from datetime import datetime
import re
import enum


pixela_base_url = 'https://pixe.la/v1/'
TOKEN_PIXELA = 'my-md-token'
NAME_PREFIX = 'md-habit-'


class PixelaDataException(Exception):
    pass


class Color(enum.Enum):
    green = 'shibafu'
    red = 'momiji'
    blue = 'sora'
    yellow = 'ichou'
    purple = 'ajisai'
    black = 'kuro'


def generate_name(name: str) -> str:
    return NAME_PREFIX + name.lower()


def create_user(token: str, name: str) -> Tuple[str, str]:
    """
    Creates user of pixela
    :param token: user token
    :param name: username
    :return: token and name if successful or None
    """
    url = pixela_base_url + 'users'
    username = generate_name(name)
    payload = {
        "token": token,
        'username': username,
        'agreeTermsOfService': 'yes',
        'notMinor': 'yes'
    }
    response = requests.post(url, data=json.dumps(payload)).json()
    if response.get('isSuccess'):
        return token, username
    else:
        raise PixelaDataException(response.get('message'))


def delete_user(token: str, username: str) -> bool:
    """
    Deletes user of pixela
    :param token: user token
    :param username: username
    :return: token and name if successful or None
    """
    url = pixela_base_url + 'users/' + username
    headers = {'X-USER-TOKEN': token}
    response = requests.delete(url, headers=headers).json()
    if response.get('isSuccess'):
        return True
    else:
        raise PixelaDataException(response.get('message'))


def create_graph(token: str,
                 username: str,
                 name: str,
                 unit: str,
                 type: Literal['int', 'float'],
                 color: Color
                 ) -> str:
    """
    Creates graph with given data
    :param token: user token
    :param username:
    :param graph_name:
    :param unit: unit of measurement
    :param type: int or float
    :param color: str with predefined color
    :return: graph id
    """
    if color not in Color:
        raise PixelaDataException('Choose correct color.')
    if type not in ('int', 'float'):
        raise PixelaDataException('Choose correct data type.')
    url = pixela_base_url + 'users/' + username + '/graphs'
    id = re.sub(r'[\W_]', '-', name.lower())
    headers = {'X-USER-TOKEN': token}
    payload = {
        'id': id,
        'name': name,
        'unit': unit,
        'type': type,
        'color': color.value
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload)).json()
    if response.get('isSuccess'):
        return id
    else:
        raise PixelaDataException(response.get('message'))


def get_graphs(token: str, username: str) -> List[dict]:
    """
    Gets all of user existing graphs
    :param token: user token
    :param username:
    :return: list of graphs names and units
    """
    url = pixela_base_url + 'users/' + username + '/graphs'
    headers = {'X-USER-TOKEN': token}
    response = requests.get(url, headers=headers).json()
    if response.get('graphs') is not None:
        graphs = []
        for item in response.get('graphs'):
            graphs.append({'id': item['id'], 'name': item['name'], 'unit': item['unit'],
                           'type': item['type'], 'color': item['color']})
        return graphs
    else:
        raise PixelaDataException(response.get('message'))


def show_graph(username: str, graph_id: str) -> Optional[str]:
    """
    Gets url for certain graph
    :param username:
    :param graph_id:
    :return: url
    """
    url = pixela_base_url + 'users/' + username + '/graphs/' + graph_id + '.html?mode=simple'
    response = requests.get(url)
    if response.ok:
        return url
    else:
        raise PixelaDataException(response.status_code)


def update_graph(token: str,
                 username: str,
                 id: str,
                 name: str,
                 unit: str,
                 type: Literal['int', 'float'],
                 color: Color) -> str:
    """
    Updates certain graph
    :param token: user token
    :param username:
    :param graph_id:
    :param graph_name:
    :param unit:
    :param type: type of given types
    :param color: color of given colors
    :return: graph id
    """
    if color not in Color:
        raise PixelaDataException('Choose correct color.')
    if type not in ('int', 'float'):
        raise PixelaDataException('Choose correct data type.')
    url = pixela_base_url + 'users/' + username + '/graphs/' + id
    headers = {'X-USER-TOKEN': token}
    payload = {
        'name': name,
        'unit': unit,
        'type': type,
        'color': color.value
    }
    response = requests.put(url, headers=headers, data=json.dumps(payload)).json()
    if response.get('isSuccess'):
        return id
    else:
        raise PixelaDataException(response.get('message'))


def delete_graph(token: str,
                 username: str,
                 graph_id: str) -> bool:
    """
    Deletes certain graph
    :param token: user token
    :param username:
    :param graph_id:
    :return: graph id
    """
    url = pixela_base_url + 'users/' + username + '/graphs/' + graph_id
    headers = {'X-USER-TOKEN': token}
    response = requests.delete(url, headers=headers).json()
    if response.get('isSuccess'):
        return True
    else:
        raise PixelaDataException(response.get('message'))


def post_pixel(token: str,
               username: str,
               graph_id: str,
               quantity: Union[int, float],
               date: datetime = datetime.today()
               ) -> str:
    """
    Posts pixel for certain date inside given graph
    :param token: user token
    :param username:
    :param graph_id:
    :param quantity:
    :param date:
    :return: graph id
    """
    if type(quantity) not in (int, float):
        raise PixelaDataException('Wrong data type of quantity.')
    if not issubclass(type(date), datetime):
        raise PixelaDataException('Wrong data type of date.')
    url = pixela_base_url + 'users/' + username + '/graphs/' + graph_id
    headers = {'X-USER-TOKEN': token}
    payload = {
        'date': parse_date(date),
        'quantity': str(quantity)
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload)).json()
    print(response)
    if response.get('isSuccess'):
        return parse_date(date)
    else:
        raise PixelaDataException(response.get('message'))


def update_pixel(token: str,
                 username: str,
                 graph_id: str,
                 quantity: Union[int, float] = 0,
                 date: datetime = datetime.today(),
                 ) -> str:
    """
    Updates pixel
    :param token: user token
    :param username:
    :param graph_id:
    :param date:
    :param quantity:
    :return: graph id
    """
    if type(quantity) not in (int, float):
        raise PixelaDataException('Wrong data type of quantity.')
    if not issubclass(type(date), datetime):
        raise PixelaDataException('Wrong data type of date.')
    url = pixela_base_url + 'users/' + username + '/graphs/' + graph_id + '/' + parse_date(date)
    headers = {'X-USER-TOKEN': token}
    payload = {
        'quantity': str(quantity)
    }
    response = requests.put(url, headers=headers, data=json.dumps(payload)).json()
    print(response)
    if response.get('isSuccess'):
        return parse_date(date)
    else:
        raise PixelaDataException(response.get('message'))


def delete_pixel(token: str,
                 username: str,
                 graph_id: str,
                 date: datetime = datetime.today()
                 ) -> bool:
    """
    Delete pixel from a graph
    :param token: user token
    :param username:
    :param graph_id:
    :param date:
    :return: graph id
    """
    url = pixela_base_url + 'users/' + username + '/graphs/' + graph_id + '/' + parse_date(date)
    headers = {'X-USER-TOKEN': token}
    response = requests.delete(url, headers=headers).json()
    print(response)
    if response.get('isSuccess'):
        return True
    else:
        raise PixelaDataException(response.get('message'))


def parse_date(date: datetime) -> str:
    return date.strftime("%Y%m%d")

# create_user('my-md-token', 'maxx')
# id_ = create_graph(TOKEN, NAME, 'test1', 'hour', 'int', "shibafu")
# id_ = 'test1'
# show_graph(NAME, id_)
# update_graph(TOKEN, NAME, id_, graph_name='Test one')
# get_graphs(TOKEN, NAME)
# post_pixel(TOKEN, NAME, id_, '20220509', 4)
# update_pixel(TOKEN, NAME, id_, '20220510', 10)
# delete_pixel(TOKEN, NAME, id_, '20220509')
# delete_user(TOKEN_PIXELA, NAME_PREFIX+'madmax')
# create_graph(TOKEN_PIXELA, NAME_PREFIX+'madmax', 'test1', 'hour', 'int', "shibafu")
# print(Color.green, type(Color.green), Color.green.value, Color.green.name)