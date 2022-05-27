class User:
    def __init__(self, id: int, first_name: str, pixela_token: str = None, pixela_name: str = None, state: str = None):
        self.id = id
        self.first_name = first_name
        self.pixela_token = pixela_token
        self.pixela_name = pixela_name
        self.state = state
        self.graph = {'id': None, 'name': None, 'unit': None, 'type': None, 'color': None}
        self.graphs = []
        self.editting = False

    def __str__(self):
        return (f'User {self.first_name} with id {self.id} in state {self.state}. ' +
                f'Pixela name {self.pixela_name}, token {self.pixela_token}.' +
                f'Current graph {self.graph}.')

    def reset(self):
        self.pixela_name = None
        self.pixela_token = None
        self.state = None
        self.editting = False
        self.graph = {'id': None, 'name': None, 'unit': None, 'type': None, 'color': None}
        self.graphs = []

    def set_graph(self, graph_id: str):
        self.graph = [graph for graph in self.graphs if graph_id == graph['id']][0]


def get_user(id: int, container: dict) -> User:
    return container.get(id)


def save_user(id):
    pass
