
import os
import secrets
from typing import List
from pydantic import BaseModel, Field
from ser.docker import DockerService, DockerVolume
from ser.factories import ServiceFactory
from ser.secrets import alphabet

from ser.setup import Setup
from ser.utils import create_config_mount, create_dev_mount
from .common import PostgresConfig, LokConfig, ServerConfig, RedisConfig



class MinioConfig(BaseModel):
    host: str = "minio"
    protocol: str = "http"
    port: int = 9000
    access_key: str = Field(default_factory= lambda:''.join(secrets.choice(alphabet) for i in range(20)) ) 
    secret_key: str = Field(default_factory= lambda:''.join(secrets.choice(alphabet) for i in range(20)) ) 
    buckets: List[str] = ["zarr", "media"]


class MikroService(BaseModel):
    postgres: PostgresConfig = Field(default_factory=lambda: PostgresConfig(db_name="mikro_db"))
    lok: LokConfig = Field(default_factory=lambda: LokConfig())
    server: ServerConfig
    redis: RedisConfig = Field(default_factory=lambda: RedisConfig())
    minio: MinioConfig = Field(default_factory=lambda: MinioConfig())
    port: int = 8080


class Datalayer(BaseModel):
    endpoint_url: str
    secure:bool = False

class MikroFakt(BaseModel):
    healthz: str
    endpoint_url: str
    secure: bool
    ws_endpoint_url: str
    datalayer: Datalayer



class MikroServiceFactory(ServiceFactory):

    def __init__(self, setup: Setup) -> None:
        super().__init__(setup)

        os.makedirs("init/data/zarr", exist_ok=True)
        os.makedirs("init/data/parquet", exist_ok=True)
        os.makedirs("init/data/media", exist_ok=True)

        self.c = MikroService(server=ServerConfig.from_setup(setup), postgres=PostgresConfig.from_setup(setup, db_name="mikro_db"))

    def create_config(self) -> BaseModel:
        return self.c

    def create_fakt(self, host):

        f = MikroFakt(
            endpoint_url=f"http://{host}:{self.c.port}/graphql",
            healthz=f"http://{host}:{self.c.port}/ht",
            secure=False,
            ws_endpoint_url=f"ws://{host}:{self.c.port}/graphql",
            datalayer=Datalayer(
                endpoint_url=f"http://{host}:9000/ht" if host != "mikro" else "http://minio:9000",
            )
        )

        return f

    def create_docker_services(self) -> List[DockerService]:
        return  [DockerService(name="mikro", image="jhnnsrs/mikro:prod", ports=["8080:8080"] , volumes=[create_dev_mount("mikro", self.setup),create_config_mount("mikro"), ],  depends_on=["redis","daten","minio"]), DockerService(name="minio", image="minio/minio", ports=["9000:9000"], volumes=["data:/data"], environment={"MINIO_ACCESS_KEY": self.c.minio.access_key, "MINIO_SECRET_KEY": self.c.minio.secret_key})]

    def create_docker_volumes(self):
        return [DockerVolume.from_local(name="data", path="data")]
