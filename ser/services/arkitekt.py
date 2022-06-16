



from ast import Str
from typing import List
from pydantic import BaseModel, Field
from ser.docker import DockerService
from ser.factories import ServiceFactory

from ser.setup import Setup
from ser.utils import create_config_mount, create_dev_mount
from .common import PostgresConfig, LokConfig, ServerConfig, RedisConfig

class RabbitConfig(BaseModel):
    username: str = "guest"
    password: int = "guest"
    v_host: str = ""
    host: str = "mister"
    port: int = 5672

class ArkitektService(BaseModel):
    postgres: PostgresConfig = Field(default_factory=lambda: PostgresConfig(db_name="arkitekt_db"))
    lok: LokConfig = Field(default_factory=lambda: LokConfig())
    server: ServerConfig
    redis: RedisConfig = Field(default_factory=lambda: RedisConfig())
    rabbit: RabbitConfig = Field(default_factory=lambda: RabbitConfig())
    port: int = 8090



class AgentFakt(BaseModel):
    endpoint_url: str

class PostmanFakt(BaseModel):
    endpoint_url: str

class ArkitektFakt(BaseModel):
    healthz: str
    agent: AgentFakt
    endpoint_url: str
    postman: PostmanFakt
    secure: bool
    ws_endpoint_url: str


class ArkitektServiceFactory(ServiceFactory):

    def __init__(self, setup: Setup) -> None:
        super().__init__(setup)

        self.c = ArkitektService(server=ServerConfig.from_setup(self.setup), postgres=PostgresConfig.from_setup(self.setup, db_name="arkitekt_db"))
    def create_fakt(self, host):

        a = ArkitektFakt(
            agent=AgentFakt(endpoint_url=f"ws://{host}:{self.c.port}/agi/"),
            endpoint_url=f"http://{host}:{self.c.port}/graphql",
            healthz=f"http://{host}:{self.c.port}/ht",
            postman=PostmanFakt(endpoint_url=f"ws://{host}:{self.c.port}/watchi/"),
            secure=False,
            ws_endpoint_url=f"ws://{host}:{self.c.port}/graphql"
        )

        return a

    def create_config(self) -> BaseModel:
        return self.c

    def create_docker_services(self) -> List[DockerService]:
        return [DockerService(name="arkitekt", image="jhnnsrs/arkitekt:prod",  ports=[f"{self.c.port}:{self.c.port}"], volumes=[ create_dev_mount("arkitekt", self.setup), create_config_mount("arkitekt"),], depends_on=["redis","mister","daten"]), DockerService(name="mister", image="jhnnsrs/mister:fancy")]