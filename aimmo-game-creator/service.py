#!/usr/bin/env python
import logging
import os

from local_game_manager import LocalGameManager


def main():
    logging.basicConfig(level=logging.DEBUG)
    game_manager = LocalGameManager(os.environ.get('GAME_API_URL', 'http://localhost:8000/players/api/games/'))
    game_manager.run()


if __name__ == '__main__':
    main()
