from typing import List
from pydantic import BaseModel, Field
from ser.docker import DockerService
from ser.factories import ServiceFactory

from ser.setup import Setup
from ser.utils import create_config_mount, create_docker_mount
from .common import PostgresConfig, LokConfig, ServerConfig, RedisConfig



class HubService(BaseModel):
    lok: LokConfig = Field(default_factory=lambda: LokConfig())
    redis: RedisConfig = Field(default_factory=lambda: RedisConfig())
    port: int = 8040



class HubServiceFactory(ServiceFactory):

    def __init__(self, setup: Setup) -> None:
        super().__init__(setup)

        self.c = HubService()


    def create_config(self) -> BaseModel:
        return self.c

    def create_docker_services(self) -> List[DockerService]:
        return [DockerService(name="hub", image="jhnnsrs/hub:latest",ports=[f"{self.c.port}:{self.c.port}","8081:8018"], volumes=[create_docker_mount(), "./configs/hub.yaml:/srv/jupyterhub/config.yaml"], environment={"DOCKER_NETWORK_NAME": "hub"}, depends_on=["herre"])]
