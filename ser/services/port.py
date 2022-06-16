from typing import List
from pydantic import BaseModel, Field
from ser.docker import DockerService
from ser.factories import ServiceFactory

from ser.setup import Setup
from ser.utils import create_config_mount, create_dev_mount
from .common import PostgresConfig, LokConfig, ServerConfig, RedisConfig



class PortService(BaseModel):
    postgres: PostgresConfig = Field(default_factory=lambda: PostgresConfig(db_name="fluss_db"))
    lok: LokConfig = Field(default_factory=lambda: LokConfig())
    server: ServerConfig
    redis: RedisConfig = Field(default_factory=lambda: RedisConfig())
    port: int = 8050

class PortFakt(BaseModel):
    healthz: str
    endpoint_url: str
    secure: bool
    ws_endpoint_url: str

class PortServiceFactory(ServiceFactory):

    def __init__(self, setup: Setup) -> None:
        super().__init__(setup)
        self.c =  PortService(server=ServerConfig.from_setup(self.setup), postgres=PostgresConfig.from_setup(self.setup, db_name="port_db"))

    def create_config(self) -> BaseModel:
        return self.c

    def create_fakt(self, host):
        f = PortFakt(
            endpoint_url=f"http://{host}:{self.c.port}/graphql",
            healthz=f"http://{host}:{self.c.port}/ht",
            secure=False,
            ws_endpoint_url=f"ws://{host}:{self.c.port}/graphql"
        )

        return f

    def create_docker_services(self) -> List[DockerService]:
        return [DockerService(name="port", image="jhnnsrs/port:prod", ports=["8050:8050"], volumes=[create_dev_mount("port", self.setup),create_config_mount("port"), ],  depends_on=["redis","daten"])]
