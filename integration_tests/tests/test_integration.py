import logging
import unittest

import psutil
import requests

from aimmo_runner import runner
import connection_api


logging.basicConfig(level=logging.WARNING)


class TestIntegration(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestIntegration, self).__init__(*args, **kwargs)
        self.processes = []

    def tearDown(self):
        """
        Kills the process and its children peacefully.
        """

        for process in self.processes:
            try:
                parent = psutil.Process(process.pid)
            except psutil.NoSuchProcess:
                for child in process.children(recursive=True):
                    print(child.name)
                    child.kill()
            else:
                children = parent.children(recursive=True)
                for child in children:
                    print(child.name)
                    child.kill()
            finally:
                process.kill()

    def test_superuser_authentication(self):
        """
        A test that will run on a clean & empty database, create all migrations, new
        browser session and passes a CSRF token with the POST input request.

        """
        host_name = 'http://localhost:8000'
        login_url = host_name + '/aimmo/accounts/login/'

        connection_api.delete_old_database()
        self.processes = runner.run(use_minikube=False, server_wait=False)

        self.assertTrue(connection_api.server_is_healthy(host_name))
        session = requests.Session()
        response = session.get(login_url)
        self.assertEquals(response.status_code, 200)

        login_info = {
            'username': 'admin',
            'password': 'admin',
            'csrfmiddlewaretoken': session.cookies['csrftoken'],
        }

        response = session.post(login_url, login_info)
        self.assertEquals(response.status_code, 200)
        self.assertTrue('sessionid' in session.cookies.keys(), 'Failed to log in successfully')

