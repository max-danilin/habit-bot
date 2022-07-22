"""
Module for managing storing and retrieving data about users.
"""

import json
from datetime import datetime, date
from typing import Union
import asyncpg
import os


HEROKU = os.getenv('HEROKU', False)
if HEROKU:
    DATABASE_URL = os.environ['DATABASE_URL']
else:
    from config import DATABASE_USER, DATABASE_PASSWORD, DATABASE_NAME, DATABASE_URL


class Database:
    """
    Class to manipulate with connection to database.
    """

    def __init__(self, url: str, name: str = '', user: str = '', pwd: str = ''):
        self.url = url
        self.name = name
        self.user = user
        self.pwd = pwd
        self.conn: asyncpg.connection.Connection = None

    async def connect(self):
        """
        Making connection.
        """
        if not HEROKU:
            self.conn = await asyncpg.connect(user=self.user, password=self.pwd,
                                              database=self.name, host=self.url)
        else:
            self.conn = await asyncpg.connect(self.url)

    async def close(self):
        """
        Close connection.
        """
        await self.conn.close()


if not HEROKU:
    database = Database(url=DATABASE_URL, name=DATABASE_NAME, pwd=DATABASE_PASSWORD, user=DATABASE_USER)
else:
    database = Database(DATABASE_URL)


class User:
    """
    Class to save user's state and various user-related data.
    """

    def __init__(self, id: int, first_name: str, pixela_token: str = None,
                 pixela_name: str = None, state: str = None):
        """
        :param id: telegram id
        :param first_name: telegram first name
        :param pixela_token: pixela token
        :param pixela_name: pixela username
        :param state: current user's state
        graph: current chosen graph
        pixel: current chosen pixel
        pixels: list of all available pixels (storing them for calendar implementation)
        editting: whether the graph is being edited or created
        """
        self.id = id
        self.first_name = first_name
        self.pixela_token = pixela_token
        self.pixela_name = pixela_name
        self.state = state
        self.graph = {'id': None, 'name': None, 'unit': None, 'type': None, 'color': None}
        self.pixel = {'date': None, 'quantity': None}
        self.pixels = None
        self.editting = False
        self.session = None

    def __str__(self):
        return (f'User {self.first_name} with id {self.id} in state {self.state}. ' +
                f'Pixela name {self.pixela_name}, token {self.pixela_token}. ' +
                f'Current graph {self.graph}. Current pixel {self.pixel}.')

    def reset_graph(self):
        """
        Resetting graph to initial state.
        """
        self.graph = {'id': None, 'name': None, 'unit': None, 'type': None, 'color': None}

    def reset_pixel(self):
        """
        Resetting pixel to initial state.
        """
        self.pixel = {'date': None, 'quantity': None}

    def reset(self):
        """
        Resetting user to state without pixela profile.
        """
        self.pixela_name = None
        self.pixela_token = None
        self.state = None
        self.editting = False
        self.graph = {'id': None, 'name': None, 'unit': None, 'type': None, 'color': None}
        self.pixel = {'date': None, 'quantity': None}
        self.pixels = None
        self.session = None


async def get_user(id: int, container: dict) -> User:
    """
    Gets user data first from local container. If container is empty, retrieves data from database.
    Creates user object from received data.
    :param id: user id
    :param container: local storage
    :return: user object
    """
    if not container.keys():
        users = await database.conn.fetch('SELECT * FROM users')
        for item in users:
            user = User(
                id=item['telegram_id'],
                first_name=item['username'],
                pixela_token=item['pixela_token'],
                pixela_name=item['pixela_name'],
                state=item['user_state']
            )
            if item['graph'] and item['graph'] != 'null':
                user.graph = json.loads(item['graph'])
            else:
                user.reset_graph()
            if item['pixel'] and item['pixel'] != 'null':
                user.pixel = json.loads(item['pixel'])
            else:
                user.reset_pixel()
            user.pixels = json.loads(item['pixels']) if item['pixels'] and item['pixels'] != 'null' \
                else None
            user.editting = item['editting']
            container.update({user.id: user})
    return container.get(id)


async def save_user(user: User):
    """
    Updates user's data inside database.
    :param user: user object
    :return:
    """
    query = '''
    UPDATE users 
    SET (pixela_token, pixela_name, 
    user_state, graph, pixel, pixels, editting) =
    ($1, $2, $3, $4, $5, $6, $7)
    WHERE telegram_id = $8 AND username = $9;
    '''
    await database.conn.execute(query, user.pixela_token, user.pixela_name, user.state,
                                json.dumps(user.graph), json.dumps(user.pixel),
                                json.dumps(user.pixels), user.editting, user.id, user.first_name)


async def create_db_user(user: User):
    """
    Creates record inside database for given user.
    :param user: user object
    :return:
    """
    query = '''
    INSERT INTO users (telegram_id, username, user_state, editting) VALUES ($1, $2, $3, $4);
    '''
    await database.conn.execute(query, user.id, user.first_name, user.state, False)


def date_to_str(date_: Union[date, datetime]) -> str:
    return date_.strftime("%Y%m%d")


def str_to_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y%m%d").date()
