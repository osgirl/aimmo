from logging import getLogger
import os
import kubernetes

import pykube
from game_manager import GameManager

LOGGER = getLogger(__name__)


class KubernetesGameManager(GameManager):
    """Manages games running on Kubernetes cluster"""

    def __init__(self, *args, **kwargs):
        self._api = pykube.HTTPClient(pykube.KubeConfig.from_service_account())
        kubernetes.config.load_incluster_config()
        self._api_instance = kubernetes.client.ExtensionsV1beta1Api()
        super(KubernetesGameManager, self).__init__(*args, **kwargs)
        self._create_ingress_paths_for_existing_games()

    def _create_ingress_paths_for_existing_games(self):
        games = self._data.get_games()
        for game_id in games:
            self._add_path_to_ingress(game_id)

    def _create_game_rc(self, id, environment_variables):
        environment_variables["SOCKETIO_RESOURCE"] = "game-{}".format(id)
        environment_variables["GAME_ID"] = id
        environment_variables["GAME_URL"] = "http://game-{}".format(id)
        environment_variables["PYKUBE_KUBERNETES_SERVICE_HOST"] = "kubernetes"
        environment_variables["IMAGE_SUFFIX"] = os.environ.get("IMAGE_SUFFIX", "latest")
        rc = pykube.ReplicationController(
            self._api,
            {
                "kind": "ReplicationController",
                "apiVersion": "v1",
                "metadata": {
                    "name": "game-{}".format(id),
                    "namespace": "default",
                    "labels": {
                        "app": "aimmo-game",
                        "game_id": id,
                    },
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "app": "aimmo-game",
                        "game_id": id,
                    },
                    "template": {
                        "metadata": {
                            "labels": {
                                "app": "aimmo-game",
                                "game_id": id,
                            },
                        },
                        "spec": {
                            "containers": [
                                {
                                    "env": [
                                        {
                                            "name": env_name,
                                            "value": env_value,
                                        } for env_name, env_value in environment_variables.items()
                                    ],
                                    "image": "ocadotechnology/aimmo-game:{}".format(os.environ.get("IMAGE_SUFFIX", "latest")),
                                    "ports": [
                                        {
                                            "containerPort": 5000,
                                        },
                                    ],
                                    "name": "aimmo-game",
                                    "resources": {
                                        "limits": {
                                            "cpu": "1000m",
                                            "memory": "128Mi",
                                        },
                                        "requests": {
                                            "cpu": "100m",
                                            "memory": "64Mi",
                                        },
                                    },
                                },
                            ],
                        },
                    },
                },
            },
        )
        rc.create()

    def _create_game_service(self, id, _config):
        service = pykube.Service(
            self._api,
            {
                "kind": "Service",
                "apiVersion": "v1",
                "metadata": {
                    "name": "game-{}".format(id),
                    "labels": {
                        "app": "aimmo-game",
                        "game_id": id,
                    },
                },
                "spec": {
                    "selector": {
                        "app": "aimmo-game",
                        "game_id": id,
                    },
                    "ports": [
                        {
                            "protocol": "TCP",
                            "port": 80,
                            "targetPort": 5000,
                        },
                    ],
                    "type": "NodePort",
                },
            },
        )
        service.create()

    def _add_path_to_ingress(self, game_id):
        backend = kubernetes.client.V1beta1IngressBackend("game-{}".format(game_id, 80))
        path = kubernetes.client.V1beta1HTTPIngressPath(backend, "/game-{}".format(game_id))

        patch = [
            {
                "op": "add",
                "path": "/spec/rules/0/http/paths/-",
                "value": path
            }
        ]

        self._api_instance.patch_namespaced_ingress("aimmo-ingress", "default", patch)

    def _remove_path_from_ingress(self, game_id):
        backend = kubernetes.client.V1beta1IngressBackend("game-{}".format(game_id), 80)
        path = kubernetes.client.V1beta1HTTPIngressPath(backend, "/game-{}".format(game_id))
        ingress = self._api_instance.list_namespaced_ingress("default").items[0]
        paths = ingress.spec.rules[0].http.paths
        try:
            index_to_delete = paths.index(path)
        except ValueError:
            return

        patch = [
            {
                "op": "remove",
                "path": "/spec/rules/0/http/paths/{}".format(index_to_delete)
            }
        ]

        self._api_instance.patch_namespaced_ingress("aimmo-ingress", "default", patch)

    def create_game(self, game_id, game_data):
        try:
            self._create_game_service(game_id, game_data)
        except pykube.exceptions.HTTPError as err:
            if "already exists" in err.message:
                LOGGER.warning("Service for game {} already existed".format(game_id))
            else:
                raise
        self._create_game_rc(game_id, game_data)
        self._add_path_to_ingress(game_id)
        LOGGER.info("Game started - {}".format(game_id))

    def delete_game(self, game_id):
        self._remove_path_from_ingress(game_id)
        for object_type in (pykube.ReplicationController, pykube.Service, pykube.Pod):
            for game in object_type.objects(self._api). \
                    filter(selector={"app": "aimmo-game",
                                     "game_id": game_id}):
                LOGGER.info("Removing {}: {}".format(object_type.__name__, game.name))
                game.delete()
