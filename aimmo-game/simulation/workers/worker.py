import logging
from abc import ABCMeta, abstractmethod

import requests

LOGGER = logging.getLogger(__name__)


class Worker(object):
    __metaclass__ = ABCMeta

    def __init__(self, player_id):
        self.url = '{}/turn/'.format(self.create_worker(player_id))
        self.log = None
        self.serialised_action = None
        self.has_code_updated = False
        self.code = None

    @abstractmethod
    def create_worker(self, player_id):
        pass

    def _set_defaults(self):
        self.log = None
        self.serialised_action = None
        self.has_code_updated = False

    def fetch_data(self, state_view):
        try:
            response = requests.post(self.url, json=state_view)
            response.raise_for_status()
            data = response.json()
            self.serialised_action = data['action']
            self.log = data['log']
            self.has_code_updated = data['avatar_updated']
        except requests.exceptions.ConnectionError:
            LOGGER.info('Could not connect to worker, probably not ready yet')
            self._set_defaults()
        except KeyError as e:
            LOGGER.error('Missing key in data from worker: {}'.format(e))
            self._set_defaults()
        except Exception as e:
            LOGGER.exception('Unknown error while fetching turn data.')
            LOGGER.exception(e)
            self._set_defaults()
