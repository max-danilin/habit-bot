import requests
import json
from typing import Tuple, Union, List
from datetime import datetime

pixela_base_url = 'https://pixe.la/v1/'
TOKEN_PIXELA = 'my-md-token'
NAME_PREFIX = 'md-habit-'


def generate_name(name: str) -> str:
    return NAME_PREFIX + name


def create_user(token: str, name: str) -> Union[Tuple[str, str], None]:
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


def create_graph(token: str,
                 username: str,
                 graph_name: str,
                 unit: str,
                 type: str,
                 color: str
                 ) -> Union[str, None]:
    url = pixela_base_url + 'users/' + username + '/graphs'
    id = graph_name.lower().replace(' ', '-')
    headers = {'X-USER-TOKEN': token}
    payload = {
        'id': id,
        'name': graph_name,
        'unit': unit,
        'type': type,
        'color': color
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload)).json()
    if response.get('isSuccess'):
        return id


def get_graphs(token: str, username: str) -> List[Tuple[str, str]]:
    url = pixela_base_url + 'users/' + username + '/graphs'
    headers = {'X-USER-TOKEN': token}
    response = requests.get(url, headers=headers).json()
    if response.get('graphs'):
        graphs = []
        for item in response.get('graphs'):
            graphs.append((item['name'], item['unit']))
        return graphs


def show_graph(username: str, graph_id: str) -> Union[str, None]:
    url = pixela_base_url + 'users/' + username + '/graphs/' + graph_id + '.html?mode=simple'
    response = requests.get(url)
    if response.ok:
        return url


def update_graph(token: str,
                 username: str,
                 graph_id: str,
                 graph_name: str = None,
                 unit: str = None,
                 type: str = None,
                 color: str = None) -> Union[str, None]:
    url = pixela_base_url + 'users/' + username + '/graphs/' + graph_id
    headers = {'X-USER-TOKEN': token}
    payload = {
        'name': graph_name,
        'unit': unit,
        'type': type,
        'color': color
    }
    response = requests.put(url, headers=headers, data=json.dumps(payload)).json()
    if response.get('isSuccess'):
        return graph_id


def post_pixel(token: str,
               username: str,
               graph_id: str,
               quantity: Union[int, float],
               date: datetime = datetime.today()
               ) -> Union[str, None]:
    url = pixela_base_url + 'users/' + username + '/graphs/' + graph_id
    headers = {'X-USER-TOKEN': token}
    payload = {
        'date': parse_date(date),
        'quantity': str(quantity)
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload)).json()
    if response.get('isSuccess'):
        return graph_id


def update_pixel(token: str,
                 username: str,
                 graph_id: str,
                 date: datetime = datetime.today(),
                 quantity: Union[int, float] = None
                 ) -> Union[str, None]:
    url = pixela_base_url + 'users/' + username + '/graphs/' + graph_id + '/' + parse_date(date)
    headers = {'X-USER-TOKEN': token}
    payload = {
        'quantity': str(quantity)
    }
    response = requests.put(url, headers=headers, data=json.dumps(payload)).json()
    if response.get('isSuccess'):
        return graph_id


def delete_pixel(token: str,
                 username: str,
                 graph_id: str,
                 date: datetime = datetime.today()
                 ) -> Union[str, None]:
    url = pixela_base_url + 'users/' + username + '/graphs/' + graph_id + '/' + parse_date(date)
    headers = {'X-USER-TOKEN': token}
    response = requests.delete(url, headers=headers).json()
    if response.get('isSuccess'):
        return graph_id


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
