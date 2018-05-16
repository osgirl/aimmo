from logging import getLogger
import os
import subprocess

from game_manager import GameManager

LOGGER = getLogger(__name__)

class LocalGameManager(GameManager):
    """Manages games running on local host"""

    host = "127.0.0.1"
    game_directory = os.path.join(
        os.path.dirname(__file__),
        "../aimmo-game/",
    )
    game_service_path = os.path.join(game_directory, "service.py")
    logger = getLogger(__name__)

    def __init__(self, *args, **kwargs):
        self.games = {}
        super(LocalGameManager, self).__init__(*args, **kwargs)

    def create_game(self, game_id, game_data):
        assert(game_id not in self.games)
        port = str(6001 + int(game_id) * 1000)
        process_args = [
            "python",
            self.game_service_path,
            self.host,
            port,
        ]
        env = os.environ.copy()
        game_data = {str(k): str(v) for k, v in game_data.items()}
        env.update(game_data)
        self.games[game_id] = subprocess.Popen(process_args, cwd=self.game_directory, env=env)
        game_url = "http://{}:{}".format(self.host, port)
        LOGGER.info("Game started - {}, listening at {}".format(game_id, game_url))

    def delete_game(self, game_id):
        if game_id in self.games:
            self.games[game_id].kill()
            del self.games[game_id]