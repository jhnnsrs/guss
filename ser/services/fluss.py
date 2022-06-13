



from typing import List
from pydantic import BaseModel, Field
from ser.docker import DockerService
from ser.factories import ServiceFactory

from ser.setup import Setup
from ser.utils import create_config_mount, create_dev_mount
from .common import PostgresConfig, LokConfig, ServerConfig, RedisConfig



class FlussService(BaseModel):
    postgres: PostgresConfig = Field(default_factory=lambda: PostgresConfig(db_name="fluss_db"))
    lok: LokConfig = Field(default_factory=lambda: LokConfig())
    server: ServerConfig
    redis: RedisConfig = Field(default_factory=lambda: RedisConfig())
    port: int = 8070


class FlussFakt(BaseModel):
    healthz: str
    endpoint_url: str
    secure: bool
    ws_endpoint_url: str

class FlussServiceFactory(ServiceFactory):

    def __init__(self, setup: Setup) -> None:
        super().__init__(setup)

        self.c =  FlussService(server=ServerConfig.from_setup(self.setup), postgres=PostgresConfig.from_setup(self.setup, db_name="fluss_db"))

    def create_fakt(self, host):
        f = FlussFakt(
            endpoint_url=f"http://{host}:{self.c.port}/graphql",
            healthz=f"http://{host}:{self.c.port}/ht",
            secure=False,
            ws_endpoint_url=f"ws://{host}:{self.c.port}/graphql"
        )

        return f


    def create_config(self) -> BaseModel:
        return self.c

    def create_docker_services(self) -> List[DockerService]:
        return [DockerService(name="fluss", image="jhnnsrs/fluss:prod",  ports=[f"{self.c.port}:{self.c.port}"], volumes=[create_dev_mount("fluss", self.setup),create_config_mount("fluss")],  depends_on=["redis","daten"])]
