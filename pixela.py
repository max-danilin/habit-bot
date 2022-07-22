"""
Module for working with external Pixela API.
"""

import enum
import json
from datetime import datetime
import re
import os
from typing import Tuple, Union, List, Optional, Literal, TypedDict
import requests
import aiohttp

PIXELA_BASE_URL = 'https://pixe.la/v1/'
HEROKU = os.getenv('HEROKU', False)
if HEROKU:
    TOKEN_PIXELA = os.getenv('TOKEN_PIXELA')
    NAME_PREFIX = os.getenv('NAME_PREFIX')
else:
    from config import TOKEN_PIXELA, NAME_PREFIX


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


async def create_user(session: aiohttp.ClientSession, token: str, name: str) -> Tuple[str, str]:
    """
    Creates user of pixela
    :param session:
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
    async with session.post(url, data=json.dumps(payload)) as resp:
        response = await resp.json()
        # response = requests.post(url, data=json.dumps(payload)).json()
        if response.get('isSuccess'):
            return token, username
        else:
            raise PixelaDataException(response.get('message'))


async def delete_user(session: aiohttp.ClientSession, token: str, username: str) -> bool:
    """
    Deletes user of pixela
    :param session:
    :param token: user token
    :param username: username
    :return: token and name if successful or None
    """
    url = PIXELA_BASE_URL + 'users/' + username
    headers = {'X-USER-TOKEN': token}
    async with session.delete(url, headers=headers) as resp:
        response = await resp.json()
    # response = requests.delete(url, headers=headers).json()
        if response.get('isSuccess'):
            return True
        else:
            raise PixelaDataException(response.get('message'))


async def create_graph(session: aiohttp.ClientSession,
                       token: str,
                       username: str,
                       name: str,
                       unit: str,
                       type: Literal['int', 'float'],
                       color: str) -> str:
    """
    Creates graph with given data
    :param session:
    :param token: user token
    :param username:
    :param name:
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
    async with session.post(url, headers=headers, data=json.dumps(payload)) as resp:
        response = await resp.json()
    # response = requests.post(url, headers=headers, data=json.dumps(payload)).json()
        if response.get('isSuccess'):
            return id
        else:
            raise PixelaDataException(response.get('message'))


async def get_graph(session: aiohttp.ClientSession, token: str, username: str, graph_id: str) -> dict:
    """
    Gets single graph definitions.
    :param session:
    :param token:
    :param username:
    :param graph_id:
    :return:
    """
    url = (PIXELA_BASE_URL + 'users/' + username + '/graphs/'
           + graph_id + '/graph-def')
    headers = {'X-USER-TOKEN': token}
    async with session.get(url, headers=headers) as resp:
        response = await resp.json()
    # response = requests.get(url, headers=headers).json()
        if response.get('id'):
            graph = {'id': response['id'], 'name': response['name'], 'unit': response['unit'],
                     'type': response['type'], 'color': Color[response['color']].name}
            return graph
        else:
            raise PixelaDataException(response.get('message'))


async def get_graphs(session: aiohttp.ClientSession, token: str, username: str) -> List[dict]:
    """
    Gets all existing graphs for given user.
    :param session:
    :param token: user token
    :param username:
    :return: list of graphs names and units
    """
    url = PIXELA_BASE_URL + 'users/' + username + '/graphs'
    headers = {'X-USER-TOKEN': token}
    async with session.get(url, headers=headers) as resp:
        response = await resp.json()
    # response = requests.get(url, headers=headers).json()
        if response.get('graphs') is not None:
            graphs = []
            for item in response.get('graphs'):
                graphs.append({'id': item['id'], 'name': item['name'], 'unit': item['unit'],
                               'type': item['type'], 'color': Color[item['color']].name})
            return graphs
        else:
            raise PixelaDataException(response.get('message'))


async def show_graph(session: aiohttp.ClientSession, username: str, graph_id: str) -> Optional[str]:
    """
    Gets url for certain graph.
    :param session:
    :param username:
    :param graph_id:
    :return: url
    """
    url = PIXELA_BASE_URL + 'users/' + username + '/graphs/' + graph_id + '.html?mode=simple'
    async with session.get(url) as response:
    # response = requests.get(url)
        if response.ok:
            return url
        else:
            raise PixelaDataException(response.status)


async def update_graph(session: aiohttp.ClientSession,
                       token: str,
                       username: str,
                       id: str,
                       name: str,
                       unit: str,
                       type: Literal['int', 'float'],
                       color: str) -> str:
    """
    Updates certain graph.
    :param session:
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
    async with session.put(url, headers=headers, data=json.dumps(payload)) as resp:
        response = await resp.json()
    # response = requests.put(url, headers=headers, data=json.dumps(payload)).json()
        if response.get('isSuccess'):
            return id
        else:
            raise PixelaDataException(response.get('message'))


async def delete_graph(session: aiohttp.ClientSession,
                       token: str,
                       username: str,
                       graph_id: str) -> bool:
    """
    Deletes certain graph.
    :param session:
    :param token: user token
    :param username:
    :param graph_id:
    :return: graph id
    """
    url = PIXELA_BASE_URL + 'users/' + username + '/graphs/' + graph_id
    headers = {'X-USER-TOKEN': token}
    async with session.delete(url, headers=headers) as resp:
        response = await resp.json()
    # response = requests.delete(url, headers=headers).json()
        if response.get('isSuccess'):
            return True
        else:
            raise PixelaDataException(response.get('message'))


async def get_pixels(session: aiohttp.ClientSession,
                     token: str,
                     username: str,
                     graph_id: str) -> List[Pixels]:
    """
    Get list of pixels for certain graph.
    :param session:
    :param token: user token
    :param username:
    :param graph_id:
    :return: list of pixels
    """
    url = PIXELA_BASE_URL + 'users/' + username + '/graphs/' + graph_id + '/pixels?withBody=true'
    headers = {'X-USER-TOKEN': token}
    async with session.get(url, headers=headers) as resp:
        response = await resp.json()
    # response = requests.get(url, headers=headers).json()
        pixels = response.get('pixels')
        if pixels:
            return [{'date': pixel['date'], 'quantity': pixel['quantity']} for pixel in pixels]
        elif pixels == []:
            return []
        else:
            raise PixelaDataException(response.get('message'))


async def post_pixel(session: aiohttp.ClientSession,
                     token: str,
                     username: str,
                     graph_id: str,
                     date_: str,
                     quantity: Union[int, float]) -> str:
    """
    Posts pixel for certain date inside given graph
    :param session:
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
    except TypeError as exc:
        raise PixelaDataException('Wrong data type of date.') from exc
    url = PIXELA_BASE_URL + 'users/' + username + '/graphs/' + graph_id
    headers = {'X-USER-TOKEN': token}
    payload = {
        'date': date_,
        'quantity': str(quantity)
    }
    async with session.post(url, headers=headers, data=json.dumps(payload)) as resp:
        response = await resp.json()
    # response = requests.post(url, headers=headers, data=json.dumps(payload)).json()
        if response.get('isSuccess'):
            return date_
        else:
            raise PixelaDataException(response.get('message'))


async def update_pixel(session: aiohttp.ClientSession,
                       token: str,
                       username: str,
                       graph_id: str,
                       date_: str,
                       quantity: Union[int, float] = 0) -> str:
    """
    Updates pixel
    :param session:
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
    async with session.put(url, headers=headers, data=json.dumps(payload)) as resp:
        response = await resp.json()
    # response = requests.put(url, headers=headers, data=json.dumps(payload)).json()
        if response.get('isSuccess'):
            return date_
        else:
            raise PixelaDataException(response.get('message'))


async def delete_pixel(session: aiohttp.ClientSession,
                       token: str,
                       username: str,
                       graph_id: str,
                       date_: str) -> bool:
    """
    Delete pixel from a graph
    :param session:
    :param token: user token
    :param username:
    :param graph_id:
    :param date_:
    :return: graph id
    """
    url = PIXELA_BASE_URL + 'users/' + username + '/graphs/' + graph_id + '/' + date_
    headers = {'X-USER-TOKEN': token}
    async with session.delete(url, headers=headers) as resp:
        response = await resp.json()
    # response = requests.delete(url, headers=headers).json()
        if response.get('isSuccess'):
            return True
        else:
            raise PixelaDataException(response.get('message'))

