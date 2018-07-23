import logging
import unittest
import time
import subprocess

import kubernetes.client
import psutil

from aimmo_runner import runner
from connection_api import (delete_old_database, create_custom_game_default_settings, _log_in_as_a_superuser)

logging.basicConfig(level=logging.WARNING)


class TestKubernetes(unittest.TestCase):
    def setUp(self):
        """
        Sets a clean database for each test before running
        starting starting the run script again. Sleeps 60 second
        between each test to ensure stable state and loads the
        api instance from the kubernetes client.
        """
        delete_old_database()

        # Clear any k8s resources that are still hanging around so that we can precisely test ours
        subprocess.call(['kubectl', 'delete', 'rc', '--all'])
        subprocess.call(['kubectl', 'delete', 'pods', '--all'])
        self.processes = runner.run(use_minikube=True, server_wait=False, capture_output=False)
        time.sleep(10)
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
                return

            children = parent.children(recursive=True)

            for child in children:
                child.terminate()

    def test_clean_starting_state_of_cluster(self):
        """
        The purpose of this test is to check the correct number
        of pods, replication controllers and services are created.
        All components created by the game will be in the "default"
        namespace.
        """

        # PODS
        api_response = self.api_instance.list_namespaced_pod("default")
        self.assertEqual(len(api_response.items), 1, str([item.metadata.name for item in api_response.items]))
        pod_item = api_response.items[0]
        self.assertTrue(pod_item.metadata.name.startswith("aimmo-game-creator-"))
        self.assertEqual(len(pod_item.metadata.owner_references), 1)
        self.assertEqual(pod_item.metadata.owner_references[0].kind, "ReplicationController")

        # REPLICATION CONTROLLERS
        api_response = self.api_instance.list_namespaced_replication_controller("default")
        self.assertEqual(len(api_response.items), 1)
        pod_item = api_response.items[0]
        self.assertTrue(pod_item.metadata.name.startswith("aimmo-game-creator"))

        # SERVICES
        api_response = self.api_instance.list_namespaced_service("default")
        self.assertEqual(len(api_response.items), 1)
        pod_item = api_response.items[0]
        self.assertEqual(pod_item.metadata.name, "kubernetes")

    def test_correct_initial_ingress_yaml(self):
        """
        This test will ensure that the initial yaml created on a
        fresh state of the cluster. It assumes: ingress name, no backend
        and only one specific rule, with only one path specified!
        """
        api_response = self.api_extension_instance.list_namespaced_ingress("default")

        self.assertEquals(len(api_response.items), 1)

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

        def check_cluster_ready(api_instance):
            temp_response = api_instance.list_namespaced_pod("default")
            print('Items: ' + str([item.metadata.name for item in temp_response.items]))
            worker_ready = any([item.metadata.name.startswith("aimmo-1-worker") for item in temp_response.items])
            game_ready = any([item.metadata.name.startswith("game-1") for item in temp_response.items])

            return worker_ready and game_ready

        request_response, session = create_custom_game_default_settings(name="testGame")
        self.assertEqual(request_response.status_code, 200)

        # Trigger the creation of the worker pod
        code_response = session.get('http://localhost:8000/aimmo/api/code/1/')
        self.assertEqual(code_response.status_code, 200)

        # WORKER
        cluster_ready = False
        for _ in range(200):
            if check_cluster_ready(self.api_instance):
                cluster_ready = True
                break
            time.sleep(1)

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

    @unittest.skip("Not Implemented.")
    def test_adding_game_appends_path_to_ingress(self):
        """
        Adding a game (level), will append the correct path to the ingress at /game-1.
        """
        pass

    @unittest.skip("Not Implemented.")
    def test_remove_old_ingress_paths_on_startup(self):
        """
        A game is created in the minikube instance and ingress path is appended. The
        cluster is then stopped and started again with a fresh database. When this happens,
        we check that the ingress paths are returned to default again.
        """
        pass
