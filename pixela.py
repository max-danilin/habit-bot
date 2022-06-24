"""
Module for working with external Pixela API.
"""

import enum
import json
from datetime import datetime
import re
from typing import Tuple, Union, List, Optional, Literal, TypedDict
import requests


PIXELA_BASE_URL = 'https://pixe.la/v1/'
TOKEN_PIXELA = 'my-md-token'
NAME_PREFIX = 'md-habit-'


class Pixels(TypedDict):
    """
    Class for type hints for pixels.
    """
    date: str
    quantity: str


class PixelaDataException(Exception):
    """
    Custom expression for Pixela API.
    """


class Color(enum.Enum):
    """
    Class representing available colors as enumerations.
    """
    shibafu = "зеленый"
    momiji = "красный"
    sora = "синий"
    ichou = "желтый"
    ajisai = "фиолетовый"
    kuro = "черный"


def generate_name(name: str) -> str:
    """
    Generates pixela username.
    :param name:
    :return:
    """
    return NAME_PREFIX + name.lower()


def create_user(token: str, name: str) -> Tuple[str, str]:
    """
    Creates user of pixela
    :param token: user token
    :param name: username
    :return: token and name if successful or None
    """
    url = PIXELA_BASE_URL + 'users'
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
    url = PIXELA_BASE_URL + 'users/' + username
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
                 color: str
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
    if color not in [e.name for e in Color]:
        raise PixelaDataException('Choose correct color.')
    if type not in ('int', 'float'):
        raise PixelaDataException('Choose correct data type.')
    url = PIXELA_BASE_URL + 'users/' + username + '/graphs'
    id = re.sub(r'[\W_]', '-', name.lower())
    headers = {'X-USER-TOKEN': token}
    payload = {
        'id': id,
        'name': name,
        'unit': unit,
        'type': type,
        'color': color
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload)).json()
    if response.get('isSuccess'):
        return id
    else:
        raise PixelaDataException(response.get('message'))


def get_graph(token: str, username: str, graph_id: str) -> dict:
    """
    Gets single graph definitions.
    :param token:
    :param username:
    :param graph_id:
    :return:
    """
    url = (PIXELA_BASE_URL + 'users/' + username + '/graphs/'
           + graph_id + '/graph-def')
    headers = {'X-USER-TOKEN': token}
    response = requests.get(url, headers=headers).json()
    if response.get('id') is not None:
        graph = {'id': response['id'], 'name': response['name'], 'unit': response['unit'],
                 'type': response['type'], 'color': Color[response['color']].name}
        return graph
    else:
        raise PixelaDataException(response.status_code)


def get_graphs(token: str, username: str) -> List[dict]:
    """
    Gets all existing graphs for given user.
    :param token: user token
    :param username:
    :return: list of graphs names and units
    """
    url = PIXELA_BASE_URL + 'users/' + username + '/graphs'
    headers = {'X-USER-TOKEN': token}
    response = requests.get(url, headers=headers).json()
    if response.get('graphs') is not None:
        graphs = []
        for item in response.get('graphs'):
            graphs.append({'id': item['id'], 'name': item['name'], 'unit': item['unit'],
                           'type': item['type'], 'color': Color[item['color']].name})
        return graphs
    else:
        raise PixelaDataException(response.get('message'))


def show_graph(username: str, graph_id: str) -> Optional[str]:
    """
    Gets url for certain graph.
    :param username:
    :param graph_id:
    :return: url
    """
    url = PIXELA_BASE_URL + 'users/' + username + '/graphs/' + graph_id + '.html?mode=simple'
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
                 color: str) -> str:
    """
    Updates certain graph.
    :param token: user token
    :param username:
    :param id: graph_id
    :param name: graph_name
    :param unit:
    :param type: type of given types
    :param color: color of given colors
    :return: graph id
    """
    if color not in [e.name for e in Color]:
        raise PixelaDataException('Choose correct color.')
    if type not in ('int', 'float'):
        raise PixelaDataException('Choose correct data type.')
    url = PIXELA_BASE_URL + 'users/' + username + '/graphs/' + id
    headers = {'X-USER-TOKEN': token}
    payload = {
        'name': name,
        'unit': unit,
        'type': type,
        'color': color
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
    Deletes certain graph.
    :param token: user token
    :param username:
    :param graph_id:
    :return: graph id
    """
    url = PIXELA_BASE_URL + 'users/' + username + '/graphs/' + graph_id
    headers = {'X-USER-TOKEN': token}
    response = requests.delete(url, headers=headers).json()
    if response.get('isSuccess'):
        return True
    else:
        raise PixelaDataException(response.get('message'))


def get_pixels(token: str,
               username: str,
               graph_id: str
               ) -> List[Pixels]:
    """
    Get list of pixels for certain graph.
    :param token: user token
    :param username:
    :param graph_id:
    :return: list of pixels
    """
    url = PIXELA_BASE_URL + 'users/' + username + '/graphs/' + graph_id + '/pixels?withBody=true'
    headers = {'X-USER-TOKEN': token}
    response = requests.get(url, headers=headers).json()
    pixels = response.get('pixels')
    if pixels:
        return [{'date': pixel['date'], 'quantity': pixel['quantity']} for pixel in pixels]
    else:
        raise PixelaDataException(response.get('message'))


def post_pixel(token: str,
               username: str,
               graph_id: str,
               date_: str,
               quantity: Union[int, float]
               ) -> str:
    """
    Posts pixel for certain date inside given graph
    :param token: user token
    :param username:
    :param graph_id:
    :param quantity:
    :param date_:
    :return: graph id
    """
    if type(quantity) not in (int, float):
        raise PixelaDataException('Wrong data type of quantity.')
    try:
        datetime.strptime(date_, "%Y%m%d")
    except ValueError as exc:
        raise PixelaDataException('Wrong data format of date.') from exc
    url = PIXELA_BASE_URL + 'users/' + username + '/graphs/' + graph_id
    headers = {'X-USER-TOKEN': token}
    payload = {
        'date': date_,
        'quantity': str(quantity)
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload)).json()
    if response.get('isSuccess'):
        return date_
    else:
        raise PixelaDataException(response.get('message'))


def update_pixel(token: str,
                 username: str,
                 graph_id: str,
                 date_: str,
                 quantity: Union[int, float] = 0
                 ) -> str:
    """
    Updates pixel
    :param token: user token
    :param username:
    :param graph_id:
    :param date_:
    :param quantity:
    :return: graph id
    """
    if type(quantity) not in (int, float):
        raise PixelaDataException('Wrong data type of quantity.')
    try:
        datetime.strptime(date_, "%Y%m%d")
    except ValueError as exc:
        raise PixelaDataException('Wrong data format of date.') from exc
    url = PIXELA_BASE_URL + 'users/' + username + '/graphs/' + graph_id + '/' + date_
    headers = {'X-USER-TOKEN': token}
    payload = {
        'quantity': str(quantity)
    }
    response = requests.put(url, headers=headers, data=json.dumps(payload)).json()
    if response.get('isSuccess'):
        return date_
    else:
        raise PixelaDataException(response.get('message'))


def delete_pixel(token: str,
                 username: str,
                 graph_id: str,
                 date_: str
                 ) -> bool:
    """
    Delete pixel from a graph
    :param token: user token
    :param username:
    :param graph_id:
    :param date_:
    :return: graph id
    """
    url = PIXELA_BASE_URL + 'users/' + username + '/graphs/' + graph_id + '/' + date_
    headers = {'X-USER-TOKEN': token}
    response = requests.delete(url, headers=headers).json()
    if response.get('isSuccess'):
        return True
    else:
        raise PixelaDataException(response.get('message'))


# delete_user(TOKEN_PIXELA, NAME_PREFIX+'madmax')
# print(Color.green, type(Color.green), Color.green.value, Color.green.name)
# for color in Color:
#     print(color.name, type(color.name), color.value, type(color.value))
