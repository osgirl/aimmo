#!/usr/bin/env python
import os

from game_manager import GAME_MANAGERS
from log_setup import configure_logger
LOGGER = None


def main():
    game_manager_class = GAME_MANAGERS[os.environ.get('GAME_MANAGER', 'local')]
    game_manager = game_manager_class(os.environ.get('GAME_API_URL',
                                                     'http://localhost:8000/aimmo/api/games/'))
    game_manager.run()


if __name__ == '__main__':
    configure_logger()
    main()
