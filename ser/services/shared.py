from typing import List
from pydantic import BaseModel, Field
from ser.docker import DockerService
from ser.factories import ServiceFactory

from ser.setup import Setup
from ser.utils import create_config_mount
from .common import PostgresConfig, LokConfig, ServerConfig, RedisConfig






class SharedServiceFactory(ServiceFactory):

    def create_config(self) -> BaseModel:
        return None

    def create_docker_services(self) -> List[DockerService]: 

        s = []
        if self.setup.common_db:
            s += [DockerService(name="daten", image="jhnnsrs/daten:prod", environment={"POSTGRES_MULTIPLE_DATABASES": "herredb,arkitektdb,elementsdb,mikrodb,portdb,flussdb,faktsdb,nextfaktsdb",
                "POSTGRES_PASSWORD": self.setup.postgres_password,
                "POSTGRES_USER": self.setup.postgres_user
            })]

        if self.setup.common_redis:
            s += [DockerService(name="redis", image="redis:latest")]

        
        return s


