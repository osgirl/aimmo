from logging import getLogger
import time
from abc import ABCMeta, abstractmethod

import requests
from eventlet.greenpool import GreenPool
from game_data_manager import GameDataManager

LOGGER = getLogger(__name__)


class GameManager(object):
    """Methods of this class must be thread safe unless explicitly stated"""
    __metaclass__ = ABCMeta
    daemon = True

    def __init__(self, games_url):
        self._data = GameDataManager()
        self.games_url = games_url
        self._pool = GreenPool(size=3)
        super(GameManager, self).__init__()

    @abstractmethod
    def create_game(self, game_id, game_data):
        """Creates a new game"""

        raise NotImplemented

    @abstractmethod
    def delete_game(self, game_id):
        """Deletes the given game"""

        raise NotImplemented

    def recreate_game(self, game_id, game_data):
        """Deletes and recreates the given game"""
        LOGGER.info("Deleting game {}".format(game_data["name"]))
        try:
            self.delete_game(game_id)
        except Exception as ex:
            LOGGER.error("Failed to delete game {}".format(game_data["name"]))
            LOGGER.exception(ex)

        LOGGER.info("Recreating game {}".format(game_data["name"]))
        try:
            game_data["GAME_API_URL"] = "{}{}/".format(self.games_url, game_id)
            self.create_game(game_id, game_data)
        except Exception as ex:
            LOGGER.error("Failed to create game {}".format(game_data["name"]))
            LOGGER.exception(ex)

    def update(self):
        try:
            LOGGER.info("Waking up")
            games = requests.get(self.games_url).json()
        except (requests.RequestException, ValueError) as ex:
            LOGGER.error("Failed to obtain game data")
            LOGGER.exception(ex)
        else:
            games_to_add = {
                id: games[id]
                for id in self._data.add_new_games(games.keys())
            }
            LOGGER.debug("Need to add games: {}".format(games_to_add))

            # Add missing games
            self._parallel_map(self.recreate_game, games_to_add.keys(), games_to_add.values())

            # Delete extra games
            known_games = set(games.keys())
            removed_game_ids = self._data.remove_unknown_games(known_games)
            LOGGER.debug("Removing games: {}".format(removed_game_ids))
            self._parallel_map(self.delete_game, removed_game_ids)

    def get_persistent_state(self, player_id):
        """Get the persistent state of a game"""

        return None

    def run(self):
        while True:
            self.update()
            LOGGER.info("Sleeping")
            time.sleep(10)

    def _parallel_map(self, func, *iterable_args):
        list(self._pool.imap(func, *iterable_args))
