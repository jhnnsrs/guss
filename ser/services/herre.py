



from typing import Dict, List
from pydantic import BaseModel, Field, root_validator
from tomlkit import value
from ser.docker import DockerService
from ser.factories import ServiceFactory
from ser.secrets import private_key, public_key
from ser.services.auth import App, User
import os

from ser.setup import Setup
from ser.utils import create_config_mount, create_dev_mount, create_fakts_mount
from .common import PostgresConfig, LokConfig, ServerConfig, RedisConfig



DEFAULT_SCOPES = {
    "read": "Reading all of your Data",
  "read_starred": "Reading all of your shared Data",
  "provider": "Can act as a provider",
  "introspection": "Introspect the Token scope",
  "can_provide": "Can Provide Nodes",
  "can_assign": "Can Assign Nodes",
  "can_template": "Can Template Nodes",
  "can_create": "Can Create Nodes",
  "can_forward_bounce": "Can reserve and assign to Nodes mimicking other Users (only backend and admin)",
  "can_create_identifier": "Can create new identifier for the platform"
}





class HerreService(BaseModel):
    postgres: PostgresConfig = Field(default_factory=lambda: PostgresConfig(db_name="herre_db"))
    activation_days: int = 7
    token_expire_seconds: int = 60 * 60 * 24 * 7
    scopes: Dict[str, str] = Field(default_factory=lambda: {**DEFAULT_SCOPES})
    public_key: str = Field(default_factory=lambda: public_key)
    private_key: str = Field(default_factory=lambda: private_key)
    server: ServerConfig
    redis: RedisConfig = Field(default_factory=lambda: RedisConfig())
    loks: List[User] = Field(default_factory=list)
    apps: List[App] = Field(default_factory=list)
    advertised_hosts: List[str] =Field(default_factory=list)
    port: int = 8000




class HerreFakt(BaseModel):
    healthz: str
    endpoint_url: str
    base_url: str
    secure: bool
    ws_endpoint_url: str



class HerreServiceFactory(ServiceFactory):

    def __init__(self, setup: Setup) -> None:
        super().__init__(setup)

        self.c =  HerreService(server=ServerConfig.from_setup(self.setup), postgres=PostgresConfig.from_setup(self.setup, db_name="herre_db"), apps=setup.apps, loks=setup.loks)


    def create_fakt(self, host):
        f = HerreFakt(
            base_url=f"http://{host}:{self.c.port}/o",
            endpoint_url=f"http://{host}:{self.c.port}/graphql",
            healthz=f"http://{host}:{self.c.port}/ht",
            secure=False,
            ws_endpoint_url=f"ws://{host}:{self.c.port}/graphql"
        )

        return f

    def create_config(self) -> BaseModel:
        return self.c

    def create_docker_services(self) -> List[DockerService]:

        return  [DockerService(name="herre", image="jhnnsrs/herre:prod", ports=[f"{self.c.port}:{self.c.port}"], volumes=[create_dev_mount("herre", self.setup),create_config_mount("herre"), create_fakts_mount()],  depends_on=["daten"])]



