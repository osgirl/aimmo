#!/usr/bin/env python
import logging
import sys
import flask

from simulation.avatar_state import AvatarState
from simulation.world_map import WorldMap
from avatar_runner import AvatarRunner
from log_setup import configure_logger

app = flask.Flask(__name__)

avatar_runner = None


@app.route('/turn/', methods=['POST'])
def process_turn():
    LOGGER.info('Calculating action')
    data = flask.request.get_json()

    world_map = WorldMap(**data['world_map'])
    avatar_state = AvatarState(**data['avatar_state'])

    action, logs = avatar_runner.process_avatar_turn(world_map, avatar_state)

    return flask.jsonify(action=action, logs=logs)


def run(host, port):
    logging.basicConfig(level=logging.INFO)
    global avatar_runner
    avatar_runner = AvatarRunner()
    app.config['DEBUG'] = False
    app.run(host, port)


if __name__ == '__main__':
    configure_logger()
    LOGGER = logging.getLogger(__name__)  # Has to be after configure_logger()
    run(host=sys.argv[1], port=int(sys.argv[2]))
