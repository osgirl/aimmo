import logging
import unittest
import time
import subprocess

import kubernetes.client
import psutil

from aimmo_runner import runner
import connection_api

LOGGER = logging.getLogger(__name__)


class TestKubernetes(unittest.TestCase):
    def setUp(self):
        """
        Sets a clean database for each test before running
        starting starting the run script again. Sleeps 60 second
        between each test to ensure stable state and loads the
        api instance from the kubernetes client.
        """

        time.sleep(30)
        connection_api.delete_old_database()

        # Clear any k8s resources that are still hanging around so that we can precisely test ours
        subprocess.call(['kubectl', 'delete', 'rc', '--all'])
        subprocess.call(['kubectl', 'delete', 'pods', '--all'])
        subprocess.call(['kubectl', 'delete', 'ingress', '--all'])

        self.processes = runner.run(use_minikube=True, server_wait=False, capture_output=False)
        kubernetes.config.load_kube_config(context='minikube')
        self.api_instance = kubernetes.client.CoreV1Api()
        self.api_extension_instance = kubernetes.client.ExtensionsV1beta1Api()

    def tearDown(self):
        """
        Kills the process and its children peacefully.
        """
        for process in self.processes:
            try:
                parent = psutil.Process(process.pid)
            except psutil.NoSuchProcess:
                LOGGER.info('No such process')
                for child in process.children(recursive=True):
                    child.kill()
            else:
                children = parent.children(recursive=True)
                for child in children:
                    child.kill()
            finally:
                process.kill()

    @staticmethod
    def _eventually_true(f, timeout, **f_args):
        for _ in range(timeout):
            if f(**f_args):
                return True
            time.sleep(1)
        return False

    @staticmethod
    def _resource_check(namespace_f):
        api_response = namespace_f("default")
        return len(api_response.items) == 1

    def test_clean_starting_state_of_cluster(self):
        """
        The purpose of this test is to check the correct number
        of pods, replication controllers and services are created.
        All components created by the game will be in the "default"
        namespace.
        """

        # PODS
        have_pod = self._eventually_true(self._resource_check, 60, namespace_f=self.api_instance.list_namespaced_pod)
        self.assertTrue(have_pod)

        api_response = self.api_instance.list_namespaced_pod("default")
        pod_item = api_response.items[0]
        self.assertTrue(pod_item.metadata.name.startswith("aimmo-game-creator-"))
        self.assertEqual(len(pod_item.metadata.owner_references), 1)
        self.assertEqual(pod_item.metadata.owner_references[0].kind, "ReplicationController")

        # REPLICATION CONTROLLERS
        have_rc = self._eventually_true(self._resource_check, 60,
                                        namespace_f=self.api_instance.list_namespaced_replication_controller)
        self.assertTrue(have_rc)

        api_response = self.api_instance.list_namespaced_replication_controller("default")
        rc_item = api_response.items[0]
        self.assertTrue(rc_item.metadata.name.startswith("aimmo-game-creator"))

        # SERVICES
        have_service = self._eventually_true(self._resource_check, 60, namespace_f=self.api_instance.list_namespaced_service)
        self.assertTrue(have_service)

        api_response = self.api_instance.list_namespaced_service("default")
        service_item = api_response.items[0]
        self.assertEqual(service_item.metadata.name, "kubernetes")

    def test_correct_initial_ingress_yaml(self):
        """
        This test will ensure that the initial yaml created on a
        fresh state of the cluster. It assumes: ingress name, no backend
        and only one specific rule, with only one path specified!
        """

        have_ingress = self._eventually_true(self._resource_check, 60,
                                             namespace_f=self.api_extension_instance.list_namespaced_ingress)
        self.assertTrue(have_ingress)
        api_response = self.api_extension_instance.list_namespaced_ingress("default")

        # NAME
        self.assertEqual(api_response.items[0].metadata.name, "aimmo-ingress")

        # NO BACKEND
        self.assertEqual(api_response.items[0].spec.backend, None)

        # RULES
        rule = api_response.items[0].spec.rules[0]
        self.assertEqual(len(api_response.items[0].spec.rules), 1)
        self.assertEqual(rule.host,
                         "local.aimmo.codeforlife.education")

        # PATHS
        path = rule.http.paths[0]
        self.assertEqual(len(rule.http.paths), 1)
        self.assertEqual(path.backend.service_name, "default-http-backend")
        self.assertEqual(path.path, None)

    def test_adding_custom_game_sets_cluster_correctly(self):
        """
        Log into the server as admin (superuser) and create a game
        with the name "testGame", using the default settings provided.
        """

        def check_cluster_ready():
            temp_response = self.api_instance.list_namespaced_pod("default")
            print(temp_response.items)
            worker_ready = any([item.metadata.name.startswith("aimmo-1-worker") for item in temp_response.items])
            game_ready = any([item.metadata.name.startswith("game-1") for item in temp_response.items])

            return worker_ready and game_ready

        def find_path(target):
            api_response = self.api_extension_instance.list_ingress_for_all_namespaces()

            for item in api_response.items:
                for rule in item.spec.rules:
                    for path in rule.http.paths:
                        if path.path == target:
                            return True
            return False

        request_response, session = connection_api.create_custom_game_default_settings(name="testGame")
        self.assertEqual(request_response.status_code, 200)
        self.assertTrue('sessionid' in session.cookies.keys(), 'Failed to log in successfully')

        # Trigger the creation of the worker pod
        code_response = session.get('http://localhost:8000/aimmo/api/code/1/')
        self.assertEqual(code_response.status_code, 200)

        # WORKER
        cluster_ready = self._eventually_true(check_cluster_ready, 180 * 2)
        print('logs: ')
        time.sleep(20)
        subprocess.call(['kubectl', 'logs', '-l', 'app=aimmo-game'])
        self.assertTrue(cluster_ready, "Cluster not created!")

        # SERVICE
        api_response = self.api_instance.list_namespaced_service("default")

        service_names = [service.metadata.name for service in api_response.items]
        if "game-1" not in service_names:
            self.fail("Service not created!")

        # REPLICATION CONTROLLERS
        api_response = self.api_instance.list_namespaced_replication_controller("default")

        rc_names = [rc.metadata.name for rc in api_response.items]
        if "game-1" not in rc_names:
            self.fail("Replication controller not created!")

        # INGRESS
        have_ingress = self._eventually_true(find_path, 180, target='/game-1')
        self.assertTrue(have_ingress, "Ingress not added." + str(self.api_instance.list_namespaced_pod("default")))



