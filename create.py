from ctypes import Union
import itertools
from typing import Dict, List, Optional, Type
from pydantic import BaseModel, Field, SecretStr
import yaml
from jwcrypto import jwk
import secrets
import string

key = jwk.JWK.generate(kty='RSA', size=2048, alg='RSA-OAEP-256', use='enc', kid='12345')
public_key = key.export_public()
private_key = key.export_private()


alphabet = string.ascii_letters + string.digits

def remove_none(obj):
  if isinstance(obj, (list, tuple, set)):
    return type(obj)(remove_none(x) for x in obj if x)
  elif isinstance(obj, dict):
    return type(obj)((remove_none(k), remove_none(v))
      for k, v in obj.items() if k and v)
  else:
    return obj



class DockerService(BaseModel):
    name: str
    image: str
    ports: Optional[List[str]]
    volumes: Optional[List[str]]
    environment: Optional[dict]


class DockerVolume(BaseModel):
    name: str


class User(BaseModel):
    username: str
    email: str
    password: str
    groups: List[str]

class AdminUser(BaseModel):
    username: str
    email: str
    password: str



class DockerCompose(BaseModel):
    version: str = "3.7"
    services: Optional[Dict]
    volumes: Optional[Dict]
    networks: Optional[Dict]
    secrets: Optional[Dict]



class Setup(BaseModel):
    services: List[str]



class ServiceFactory:
    name: str = "U"

    def __init__(self, setup: Setup) -> None:
        self.setup = setup

    def create_dirs(self):
        pass
    
    def create_config(self) -> BaseModel:
        raise NotImplementedError()

    def create_docker_services(self) -> List[DockerService]:
        return []

    def create_docker_volumes(self) -> List[DockerVolume]:
        return []


class PostgresConfig(BaseModel):
    host: str = "daten"
    port: int = 5432
    user: str = "hello_django"
    password: str = "hello_django"
    db_name: str


class RedisConfig(BaseModel):
    host: str = "redis"
    port: int = 6379

class RabbitConfig(BaseModel):
    username: str = "guest"
    password: int = "guest"
    v_host: str = ""
    host: str = "mister"
    port: int = 5672

class ServerConfig(BaseModel):
    debug: bool = False
    hosts: List[str] = ["*"]
    admin: AdminUser 
    secret_key: str

    @classmethod
    def from_setup(cls, setup: Setup):
        return ServerConfig(admin=AdminUser(username="admin", email="johannes", password="osinosinosine"), secret_key="oinsoin")


class LokConfig(BaseModel):
    public_key: str = Field(default_factory=lambda: public_key)
    key_type: str = "RSA256"
    issuer: str = "herre"


class MinioConfig(BaseModel):
    host: str = "minio"
    protocol: str = "http"
    port: int = 9000
    access_key: str = Field(default_factory= lambda:''.join(secrets.choice(alphabet) for i in range(20)) ) 
    secret_key: str = Field(default_factory= lambda:''.join(secrets.choice(alphabet) for i in range(20)) ) 
    buckets: List[str] = ["zarr, media"]



class ArkitektService(BaseModel):
    postgres: PostgresConfig = Field(default_factory=lambda: PostgresConfig(db_name="arkitekt_db"))
    lok: LokConfig = Field(default_factory=lambda: LokConfig())
    server: ServerConfig
    redis: RedisConfig = Field(default_factory=lambda: RedisConfig())
    rabbit: RabbitConfig = Field(default_factory=lambda: RabbitConfig())

    @classmethod
    def from_setup(cls, setup: Setup):
        return ArkitektService(server=ServerConfig.from_setup(setup))

    def create_docker_services(self) -> List[DockerService]:
        return [
            DockerService(name="mikro", image="mikro", ports=["8080:8080"], volumes=["data/zarr:/data/zarr", "data/parquet:/data/parquet", "data/media:/data/media"]),]

class MikroService(BaseModel):
    postgres: PostgresConfig = Field(default_factory=lambda: PostgresConfig(db_name="mikro_db"))
    lok: LokConfig = Field(default_factory=lambda: LokConfig())
    server: ServerConfig
    redis: RedisConfig = Field(default_factory=lambda: RedisConfig())
    minio: MinioConfig = Field(default_factory=lambda: MinioConfig())

    @classmethod
    def crea(cls, setup: Setup):

        os.makedirs("data/zarr", exist_ok=True)
        os.makedirs("data/parquet", exist_ok=True)
        os.makedirs("data/media", exist_ok=True)

        return MikroService(server=ServerConfig.from_setup(setup))

    def create_docker_services(self) -> List[DockerService]:
        return [
            DockerService(name="mikro", image="mikro", ports=["8080:8080"], volumes=["data/zarr:/data/zarr", "data/parquet:/data/parquet", "data/media:/data/media"]),
            DockerService(name="minio", image="minio/minio", ports=["9000:9000"], volumes=["/data/minio:/data"], environment={"MINIO_ACCESS_KEY": self.minio.access_key, "MINIO_SECRET_KEY": self.minio.secret_key})]



class FlussService(BaseModel):
    postgres: PostgresConfig = Field(default_factory=lambda: PostgresConfig(db_name="fluss_db"))
    lok: LokConfig = Field(default_factory=lambda: LokConfig())
    server: ServerConfig
    redis: RedisConfig = Field(default_factory=lambda: RedisConfig())

    @classmethod
    def from_setup(cls, setup: Setup):
        return FlussService(server=ServerConfig.from_setup(setup))

    def create_docker_services(self) -> List[DockerService]:
        return [DockerService(name="fluss", image="fluss", ports=["8080:8080"])]

class HerreService(BaseModel):
    postgres: PostgresConfig = Field(default_factory=lambda: PostgresConfig(db_name="herre_db"))
    activation_days: int = 7
    token_expire_seconds: int = 60 * 60 * 24 * 7
    scopes: Dict[str, str] = Field(default_factory=lambda: {"read": "read", "write": "write"})
    private_key: str = Field(default_factory=lambda: private_key)
    server: ServerConfig
    redis: RedisConfig = Field(default_factory=lambda: RedisConfig())
    rabbit: RabbitConfig = Field(default_factory=lambda: RabbitConfig())





class HerreServiceFactory(ServiceFactory):

    def create_config(self) -> BaseModel:
        return HerreService(server=ServerConfig.from_setup(setup))

    def create_docker_services(self) -> List[DockerService]:
        return  [DockerService(name="herre", image="jhnnsrs/herre:prod", ports=["8000:8000"])]


class FlussServiceFactory(ServiceFactory):

    def create_config(self) -> BaseModel:
        return FlussService(server=ServerConfig.from_setup(setup))

    def create_docker_services(self) -> List[DockerService]:
        return [DockerService(name="fluss", image="jhnnsrs/fluss:prod", ports=["8070:8070"])]

class MikroServiceFactory(ServiceFactory):

    def __init__(self, setup: Setup) -> None:
        self.config = MikroService(server=ServerConfig.from_setup(setup))

    def create_config(self) -> BaseModel:
        return self.config

    def create_docker_services(self) -> List[DockerService]:
        return  [DockerService(name="mikro", image="jhnnsrs/mikro:prod", ports=["8080:8080"]), DockerService(name="minio", image="minio/minio", ports=["9000:9000"], volumes=["/data/minio:/data"], environment={"MINIO_ACCESS_KEY": self.config.minio.access_key, "MINIO_SECRET_KEY": self.config.minio.secret_key})]

    def create_docker_volumes(self):
        return [DockerVolume(name="data", host_path="data", container_path="/data")]


class ArkitektServiceFactory(ServiceFactory):

    def create_config(self) -> BaseModel:
        return ArkitektService(server=ServerConfig.from_setup(setup))

    def create_docker_services(self) -> List[DockerService]:
        return [DockerService(name="arkitekt", image="jhnnsrs/arkitekt:prod", ports=["8090:8090"])]



import os


def make_dirs(setup: Setup):

    if "mikro" in setup.services:
        os.makedirs("data/zarr", exist_ok=True)
        os.makedirs("data/parquet", exist_ok=True)
        os.makedirs("data/media", exist_ok=True)

    os.makedirs("configs", exist_ok=True)


class Baker:

    def __init__(self):
        self.factoryClasses = {}

    def register_factory(self, name, service: Type[ServiceFactory]):
        self.factoryClasses[name] = service

    def init(self, setup: Setup):
        self.factories = {name: factory(setup) for name, factory in self.factoryClasses.items() if name in setup.services}

    def generate_configs(self):
        os.makedirs("configs", exist_ok=True)

        for service_name, factory in self.factories.items():
            config = factory.create_config()

            with open(f"configs/{service_name}.yaml", "w") as f:
                yaml.dump(remove_none(config.dict()), f)

    def generate_dirs(self):
        os.makedirs("data", exist_ok=True)

        for service_name, factory in self.factories.items():
            config = factory.create_dirs()


    def create_docker_services(self) -> Dict :
        return {d.name: d.dict(exclude={"name"}) for d in itertools.chain(*(service.create_docker_services() for service in self.factories.values()))}

    def create_docker_volumes(self) -> Dict:
        return {d.name: d.dict(exclude={"name"}) for d in itertools.chain(*(service.create_docker_volumes() for service in self.factories.values()))}

    def bake(self):

        self.generate_dirs()
        self.generate_configs()

        docker_compose = DockerCompose(services=self.create_docker_services(), volumes=self.create_docker_volumes(), networks={}, secrets={})

        with open("docker-compose.yaml", "w") as f:
            yaml.dump(remove_none(docker_compose.dict()), f)



        return self.create_docker_services(), self.create_docker_volumes()


    
if __name__ == "__main__":

    



    with open("setup.yaml", "r") as f:
        extended_config = yaml.load(f, yaml.BaseLoader)


    setup = Setup(**extended_config)

    baker = Baker()
    baker.register_factory("mikro", MikroServiceFactory)
    baker.register_factory("arkitekt", ArkitektServiceFactory)
    baker.register_factory("fluss", FlussServiceFactory)
    baker.register_factory("core", HerreServiceFactory)
    baker.init(setup)

    baker.bake()



