import logging

from eventlet.greenpool import GreenPool

LOGGER = logging.getLogger(__name__)


class WorkerManager(object):
    def __init__(self, worker_class, port=5000):
        self._pool = GreenPool(size=3)
        self.player_id_to_worker = {}
        self.port = port
        self.worker_class = worker_class

    def get_code(self, player_id):
        return self.player_id_to_worker[player_id].code

    def update_code(self, player):
        self.player_id_to_worker[player['id']].code = player['code']

    def fetch_all_worker_data(self, player_id_to_game_state):
        for player_id, worker in self.player_id_to_worker.iteritems():
            worker.fetch_data(player_id_to_game_state[player_id])

    def get_player_id_to_serialised_actions(self):
        return {player_id: self.player_id_to_worker[player_id].serialised_action
                for player_id in self.player_id_to_worker}

    def clear_logs(self):
        for worker in self.player_id_to_worker.values():
            worker.log = None

    def add_new_worker(self, player_id):
        self.player_id_to_worker[player_id] = self.worker_class(player_id, self.port)

    def _parallel_map(self, func, iterable_args):
        return list(self._pool.imap(func, iterable_args))

    def add_workers(self, users_to_add):
        self._parallel_map(self.add_new_worker, users_to_add)

    def delete_workers(self, players_to_delete):
        self._parallel_map(self.delete_worker, players_to_delete)

    def delete_worker(self, player_id):
        self.player_id_to_worker[player_id].remove_worker(player_id)
        del self.player_id_to_worker[player_id]

    def update_worker_codes(self, players):
        map(self.update_code, players)
